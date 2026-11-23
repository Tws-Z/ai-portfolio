# MCP 实验 3：服务端、客户端与工具调用

## 1. 配置记录

### 实际客户端

客户端脚本：`week10_MCP/mcp_client_demo.py`

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = StdioServerParameters(
    command=sys.executable,
    args=["hsk_mcp_server.py"],
    cwd=week10_MCP目录,
)
```

### 等价的 MCP 客户端 JSON 配置

```json
{
  "mcpServers": {
    "hsk-tools": {
      "command": "python",
      "args": ["hsk_mcp_server.py"]
    }
  }
}
```

- 使用的 MCP 版本：2.3.0
- 服务端启动方式：stdio，客户端把 `hsk_mcp_server.py` 作为子进程启动
- 服务端文件：`week10_MCP/hsk_mcp_server.py`
- 数据：`data/生词表.csv`

## 2. 调用证据

客户端实际输出：

```text
MCP client connected
Discovered tools:
- hsk_level: 查询某个词属于 HSK 几级。
- list_by_level: 列出某一 HSK 等级的全部词汇。
- count_by_level: 统计某个 HSK 等级收录的词汇数量。
CALL hsk_level {'word': '把'} -> 把 -> 3 级
CALL count_by_level {'level': '4'} -> HSK4 共有 4 个词汇
CALL list_by_level {'level': '3'} -> 把、决定
```

运行截图：[mcp_client_output.png](mcp_client_output.png)

结论：客户端成功列出了 `hsk_level`、`list_by_level`、`count_by_level` 三个工具，并成功调用了 `hsk_level("把")`。

## 3. 三者辨析

| 概念 | 在哪一侧 | 解决什么 |
| --- | --- | --- |
| Function Calling | 模型侧机制 | 模型决定“要不要调用工具、调用哪个、参数是什么”；工具由应用程序执行。 |
| MCP | 工具侧协议 | 规定工具如何被发现、描述和调用，让客户端与外部工具使用统一接口。 |
| 普通 API 调用 | 程序侧直连 | 程序员直接请求一个确定的 API，调用哪个接口由程序写死，模型不参与选择。 |

一句话：**Function Calling 决定“模型想调用什么”，MCP 规定“工具如何被调用”，普通 API 调用是程序直接请求服务。**

## 4. 第 3 个工具：count_by_level

- 工具名：`count_by_level`
- 输入：`level: str`，HSK 等级，例如 `"4"`
- 输出：该等级收录的词汇数量，例如 `HSK4 共有 4 个词汇`
- 实现位置：`week10_MCP/hsk_mcp_server.py`
- 验证方式：客户端工具列表中出现该工具，并成功调用 `count_by_level("4")`

## 5. 安全说明

- 服务端只读取本地 `data/生词表.csv`，不访问网络、不读取 `.env`。
- `.env` 和密钥没有进入仓库。
- 第三方 MCP 服务端在本机运行前，应先检查它读取哪些文件和网络资源。