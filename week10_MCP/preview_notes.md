# W10 MCP 预习记录

## 1. 环境检查

运行：

```powershell
python week10_MCP/env_check.py
```

本机检查结果：

- Python 解释器：`D:\软件\python3.13.12\python.exe`，Python 3.13.12
- `mcp` 版本：2.3.0
- MCP 导入路径：`from mcp.server import MCPServer` 可用（2.x）
- `week09_工具调用/tool_agent.py`、`data/生词表.csv`、`data/等级标准节选.txt`、`weekpath.py` 均存在

## 2. MCP 服务端

启动方式：

```powershell
cd week10_MCP
python hsk_mcp_server.py
```

现象：进程启动后停在等待客户端连接的状态，不退出、不报错；这是 stdio MCP 服务端的正常状态，按 Ctrl+C 退出。

服务端提供两个工具：

- `hsk_level(word: str) -> str`：查询一个词的 HSK 等级。
- `list_by_level(level: str) -> str`：列出某个 HSK 等级的全部词汇。

类型注解就是客户端发现参数结构的依据：客户端从 `word: str` 知道 `hsk_level` 需要一个字符串参数。

## 3. 三者辨析三句话

1. **Function Calling** 是模型侧机制：模型决定“要不要调用工具、调用哪个、参数是什么”，但不亲自执行工具。
2. **MCP** 是工具侧协议：规定工具如何被发现、描述和调用，解决外部工具与模型客户端之间的标准接口问题。
3. **普通 API 调用** 是程序直接请求一个预先写死的接口，调用哪个接口由程序员决定，模型不参与选择。

## 4. W11 多步规划预习

本次预习的必做项已经完成。W11 的 planner 预览属于选做：本机为 8GB 内存且无独立显卡，文档建议低配机使用云端模式；下周上课前可再运行并补截图。

## 5. 截图清单

- `env_check_output.png`：Python/mcp/依赖检查输出
- `mcp_import_output.png`：mcp 导入路径验证
- `mcp_server_start.png`：MCP stdio 服务端启动状态
## 6. 直接工具验证

除 stdio 服务端启动外，我还直接调用两个被 `@mcp.tool()` 装饰的函数确认行为：

```text
hsk_level("把") = 把 -> 3 级
list_by_level("3") = 把、决定
```

这说明工具从 CSV 读取数据，而不是让语言模型凭记忆回答 HSK 等级。