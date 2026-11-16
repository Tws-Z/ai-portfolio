# W9 工具调用：智能体原理

## 功能

- `tool_agent.py` 手写最小工具调用循环，不依赖智能体框架。
- 工具一：`get_time`，查询当前时间。
- 工具二：`calc`，使用白名单 AST 做安全四则运算，绝不使用裸 `eval`。
- 工具三：`hsk_level`，从 `data/生词表.csv` 查 HSK 等级。
- 工具四：`lesson_difficulty`，评估课文相对目标等级的覆盖率、超纲词和未收录片段。
- 模型输出 JSON → `parse_calls` 容错解析 → 程序执行工具 → 结果回喂 → 模型生成最终答案。

## 安装

```powershell
python -m pip install openai python-dotenv
```

在项目根目录的 `.env` 中配置：

```text
DEEPSEEK_API_KEY=你的真实密钥
```

`.env` 不提交。默认使用 DeepSeek 云端；如果要切换到本地 Ollama，可设置：

```powershell
$env:DEEPSEEK_BASE_URL = "http://127.0.0.1:11434/v1"
$env:DEEPSEEK_MODEL = "qwen2.5:0.5b"
```

## 用法

```powershell
# 复合问句：查 HSK 等级 + 当前时间
python week09_工具调用/tool_agent.py "请依次查询两件事：1. '把'字的 HSK 等级是多少？2. 现在的时间是多少？"

# 安全计算
python week09_工具调用/tool_agent.py "请用计算器计算 35*24 等于多少。"

# 第四个工具：课文难度评估
python week09_工具调用/tool_agent.py "请评估这段课文相对 HSK4 的难度：愚公移山讲述了愚公带领子孙挖山的故事。"
```

`run()` 支持传入 `trace` 列表，测试脚本可以从 trace 中读取模型原始输出、解析出的工具调用和工具返回值。

## 已知限制

- 本地 0.5b 在复合问句中可能选错工具或参数；高质量工具选择建议使用云端模型或更大本地模型。
- `lesson_difficulty` 使用 `data/生词表.csv` 的样例词典，覆盖率只能作为演示，不能直接作为正式教材难度结论。
- 模型可能输出代码围栏或前后说明；`parse_calls` 会尽量提取 JSON，无法解析时按普通回答处理。
- 工具执行异常会回喂给模型；达到最大轮数仍无自然语言答案时，需要人工重试并查看 `tool_trace_log.md` 中的原始输出。