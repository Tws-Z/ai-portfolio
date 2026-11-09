# 学科智能问答助手 v1.0

## 功能

- 使用 W2 的学科助教人设和回答边界。
- 通过 W6 `LLM.ask()` 统一调用本地 Ollama 与云端 DeepSeek。
- 通过 W7 `retrieve()` + Chroma 从 `data/等级标准节选.txt` 检索资料。
- `use_rag=True/False` 一键切换“基于资料回答”和“纯对话”。
- `prefer="local"/"api"` 选择首选引擎，任一引擎失败会自动切换另一侧。
- 答案附资料编号和来源；运行异常会显示原因，不直接崩溃。

## 怎么装

### 1. 准备 Python 环境

```powershell
python --version
python -m pip install -r requirements.txt
```

要求 Python 3.10 以上；本项目使用 `openai`、`requests`、`python-dotenv`、LangChain、Chroma 等依赖。

### 2. 安装并启动 Ollama

使用课程提供的 Ollama Windows 便携包，程序和模型放在 E 盘：

```powershell
$env:OLLAMA_MODELS = "E:\Project\Logs2\W3\ollama_models"
$env:OLLAMA_HOST = "127.0.0.1:11434"
E:\Project\Logs2\W3\tools\ollama\ollama.exe serve
```

另开一个终端，拉取本地模型和嵌入模型：

```powershell
ollama pull qwen2.5:0.5b
ollama pull nomic-embed-text
```

如果 Ollama 已安装为桌面版，也可以直接保持羊驼服务运行。

### 3. 配置云端密钥

复制 `.env.example` 为 `.env`，在本机填写：

```text
DEEPSEEK_API_KEY=你的真实密钥
```

`.env` 已经在 `.gitignore` 中，不提交；不要把密钥发到聊天或截图。

### 4. 首次建库

首次运行 `use_rag=True` 时，W7 会自动读取资料、分块、调用 `nomic-embed-text` 并创建 `chroma_db/`。如果更换了资料，需要重建：

```powershell
python -c "import sys; sys.path.insert(0, '.'); import weekpath; from rag_qa import get_retriever; get_retriever(k=3, rebuild=True)"
```

## 怎么用

### 命令行

```powershell
# 默认：RAG + 本地优先
python week08_助手v1.0/assistant_v1.py "HSK4 累计需要掌握多少词汇？"

# 关闭 RAG，纯对话
python week08_助手v1.0/assistant_v1.py "解释什么是把字句" --no-rag

# 指定云端引擎
python week08_助手v1.0/assistant_v1.py "对比 HSK4 和 HSK5 的词汇要求" --prefer api

# 指定检索片段数
python week08_助手v1.0/assistant_v1.py "HSK5 语法点要求" --k 3
```

### Python 调用

```python
from assistant_v1 import answer

print(answer(
    "按照 2021 标准，四级累计需要掌握多少词汇？",
    use_rag=True,
    prefer="api",
))
```

### 推荐选择

- 学生作文、成绩、未公开教案：`use_rag=True, prefer="local"`，优先保护隐私。
- 标准数字、等级规则、教材原文：`use_rag=True, prefer="api"`，并要求人工核对来源。
- 通用写作和头脑风暴：可以 `use_rag=False, prefer="api"`。
- 断网课堂演示：使用 `prefer="local"`，但要接受小模型质量限制。

## 已知问题

1. 本地 `qwen2.5:0.5b` 只有 0.5B 参数，遇到 HSK 数字和表格时可能串列；本地 RAG 也可能把 3245 误读成 972 或其他数字。
2. 2021 标准中的“四级累计词汇 3245”与旧版 HSK4 的“1200 词”不是同一口径，回答时必须说明采用哪个标准。
3. `chroma_db/` 是本地生成物，不提交；修改 `data/等级标准节选.txt` 后必须使用 `rebuild=True` 重建，否则检索还是旧资料。
4. Ollama 未启动、`nomic-embed-text` 未拉取或系统代理拦截 localhost 时，RAG 会失败；本程序会显示失败原因，不会静默返回空字符串。
5. 云端密钥缺失或余额不足时，云端调用可能失败；程序会尝试切换到本地引擎，但本地答案仍需人工复核。