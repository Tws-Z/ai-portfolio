# smolagents 工具调用与手写 tool_agent.py 的 5 行映射

参考：Hugging Face smolagents（Apache-2.0）ToolCallingAgent 与手写 W9 工具循环。

| # | 我的 tool_agent.py | smolagents 里对应什么 | 说明 |
| --- | --- | --- | --- |
| 1 | `TOOLS` 字典：工具名 → 函数 | `@tool` 装饰器把带类型注解和 Args 文档的函数变成 Tool，交给 `ToolCallingAgent(tools=[...])` | 手写版自己维护工具注册表，框架版自动生成工具描述。 |
| 2 | `SYS` 提示词要求输出 JSON | 模型原生 tool calling；提示模板在 `prompts/toolcalling_agent.yaml` | 手写版用文字约束模型，框架版把工具协议交给模型接口。 |
| 3 | `parse_calls` 剥围栏、提取 JSON | 框架内部解析 `ChatMessageToolCall` | 手写版需要自己容错处理代码围栏、自然语言和多个 JSON。 |
| 4 | `TOOLS[name](*args)` 执行并捕获异常 | 框架按 `Tool.inputs` 校验参数，再把结果送回多步消息 | 手写版需要自己写 `validate_args` 和异常兜底。 |
| 5 | `run()` 手动回喂 + `max_calls` 收口 | `MultiStepAgent` 管理多步循环、步数和停止条件 | 框架省去了循环管理，但也隐藏了一部分控制权。 |

## 对照结论

手写循环让我们看清 Function Calling 的四步接力：模型提出调用、程序解析、程序执行、结果回喂。smolagents 把解析、参数校验和循环封装起来，适合快速构建；手写版更适合理解原理和控制安全边界。