# M1 会话协议草案

## 1. 事件类型与字段

建议所有事件使用统一信封：

```json
{
  "session_id": "会话唯一标识",
  "seq": 0,
  "ts": "ISO-8601 时间戳",
  "type": "事件类型",
  "payload": {}
}
```

事件类型建议：

- `client_message`：用户输入。
- `ack`：服务端确认收到，携带服务端分配的 `seq`。
- `assistant_delta`：助手回复的增量片段。
- `tool_call`：模型请求调用工具。
- `tool_result`：工具执行结果。
- `done`：本轮回答结束。
- `error`：可恢复或不可恢复错误。
- `interrupt`：用户打断当前生成或工具执行。

`payload` 按事件类型定义；服务端事件必须带单调递增的 `seq`。

## 2. 状态机

```text
idle
  -> listening        收到 client_message
  -> thinking         开始生成
  -> tool_calling     需要调用工具
  -> thinking         工具结果回喂
  -> speaking         输出最终回复
  -> idle             本轮完成

thinking/speaking/tool_calling
  -> listening        用户打断（interrupt）
```

打断规则：

1. 客户端发送 `interrupt`，并带上最后收到的 `seq`。
2. 服务端停止尚未完成的生成或工具调用，丢弃未发送的增量。
3. 服务端发送 `done` 或 `error` 收口，然后回到 `listening`。
4. 已经完成的工具结果可以保留，但不能继续向用户发送旧回复。

## 3. 权威与幂等

- **服务端唯一权威**：服务端分配 `session_id` 和 `seq`，客户端只发送输入和确认，不自行生成权威序号。
- 客户端消息应携带自己的 `message_id`；服务端用 `(session_id, message_id)` 去重，重复提交只返回第一次的结果。
- 客户端收到重复 `seq` 时忽略；发现缺口时请求补发。
- 所有工具调用和结果都要写入会话事件，便于重连和审计。

## 4. 断线语义

1. 客户端重连时发送 `session_id` 和 `last_seq`。
2. 服务端从 `last_seq + 1` 开始补发未确认事件。
3. 如果会话仍在内存中，恢复后继续原来的状态机。
4. 如果会话已过期，返回明确错误，客户端创建一个新的 `session_id`，不能假装旧上下文仍然存在。
5. 断线期间不重复执行已经成功的工具调用；依靠 `message_id` 和 `seq` 去重。

## 5. 最小验收

- 能说明每个事件由谁产生、包含哪些字段。
- 能画出正常路径和用户打断后的回退路径。
- 能解释服务端为什么是唯一权威，以及重复消息如何处理。
- 能描述重连时按 `last_seq` 补发，而不是从头重复执行。