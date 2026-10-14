# AI Portfolio

这是我的个人作品集仓库，会用于记录本学期在学习过程中完成的练习、作业与项目。

## 仓库内容

- `README.md`：仓库说明文件
- `hello.py`：Python 环境配置验证脚本
- `ai任务单.md`：使用 AI 对话工具完成学科任务的过程与结果记录

## 运行 Python 验证脚本

在 VS Code 中打开本仓库后，运行：

```bash
python hello.py
```

运行成功后会看到：

```text
Hello, AI Portfolio!
Python 环境配置成功！
```

## 学习目标

1. 熟悉 GitHub 仓库的基本创建和文件提交方法。
2. 完成 VS Code 与 Python 运行环境配置。
3. 学习使用 AI 对话工具辅助完成学习任务，并如实记录过程与结果。

## 第 2 周：提示词模板库

本仓库的 `prompt-library/` 文件夹用于保存数学与线性代数学习场景的提示词模板。

每个模板包含：

- 提示词：角色、任务、约束和输出格式四件套。
- 适用说明：说明该模板适合解决什么任务。
- 最佳示例：保存实际测试后效果较好的一次输出。

目前包含 6 个线性代数主题的 v2 模板。v2 使用 XML 风格分隔符区分固定指令和用户输入，并增加输入校验门与生成后自检，以减少信息缺失时的猜测和输出漂移。

同时使用 `prompt_iteration_log.md` 记录提示词的迭代、比较和改进结果。

## 第 3 周：Python 生词表练习题生成器

本仓库增加了 Python 读取 CSV 并生成练习题的基础工具。

- `week03_Python/vocab_tool.py`：读取生词表、筛选 HSK4 词汇、按词性分组生成练习题。
- `weekpath.py`：统一解析代码包根目录和 `data/` 路径。
- `data/生词表.csv`：示例词汇数据。
- `AI辅助编程实录.md`：记录 AI 初版代码、我的修改原因和最终差异。

运行命令：

```bash
python week03_Python/vocab_tool.py
```

运行后会在仓库根目录生成 `练习.txt`。该文件是自动生成物，已由 `.gitignore` 忽略，不提交到仓库。

## 第 4 周：第一次 API 调用

本仓库增加命令行学科问答机器人，用 API 让程序直接调用大模型回答教学问题。

- `week04_API/week4_api_bot.py`：单次问答、多轮追问、批量调用、token 记录和错误提示。
- `.env.example`：API 平台和密钥配置模板；真实密钥只写本机 `.env`，不提交。
- `week04_API/w4_questions.txt`：10 个国际中文教育学科问题，用于费用统计。
- `W4_API调用记录.md`：参数体验、费用统计和失败实验记录。
- `密钥安全自查表.md`：提交前的密钥安全逐项检查。
- `AI辅助编程实录.md`：已追加 W4 的 AI 初版代码、修改原因和最终差异。
- `chat_log.txt`：真实 API 问答日志，包含 3 个学科问题、参数实验、多轮追问和 10 次批量调用。
- `w4_usage.csv`：每次调用的 prompt、completion、total tokens 与估算费用。

运行示例：

```bash
python week04_API/week4_api_bot.py "把字句的教学难点有哪些"
python week04_API/week4_api_bot.py --chat
python week04_API/week4_api_bot.py --batch week04_API/w4_questions.txt
```
