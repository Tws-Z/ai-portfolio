# 学科智能问答助手 v1.0

## 功能

- 统一调用本地 Ollama 与云端 DeepSeek，任一侧失败自动切换。
- `use_rag=True/False` 切换知识库检索和纯对话。
- 基于 `data/等级标准节选.txt` 的 Chroma 知识库回答，并附来源。
- 支持 `prefer="local"` 和 `prefer="api"`。
- 运行失败时显示原因，不静默返回空字符串。

## 安装

1. 安装 Python 依赖：`python -m pip install -r requirements.txt`
2. 启动 Ollama，并拉取 `qwen2.5:0.5b`、`nomic-embed-text`
3. 复制 `.env.example` 为 `.env`，填写 `DEEPSEEK_API_KEY`
4. 首次 RAG 运行会自动创建 `chroma_db/`

## 用法

```powershell
python week08_助手v1.0/assistant_v1.py "HSK4 累计需要掌握多少词汇？"
python week08_助手v1.0/assistant_v1.py "解释什么是把字句" --no-rag
python week08_助手v1.0/assistant_v1.py "HSK5 语法点要求" --prefer api
```

## 已知问题

本地 0.5b 对专业数字和表格仍可能出错；2021 标准与旧版 HSK 的口径不能混用。知识库改动后必须用 `rebuild=True` 重建 Chroma。详细说明见 `week08_助手v1.0/README.md`。