# 官方 RAG 流水线 ↔ 我的 rag_qa.py 映射表

| # | 官方 RAG 流水线步骤 | 我的实现 | 说明 |
| --- | --- | --- | --- |
| 1 | 加载文档（Load） | `TextLoader(CORPUS, encoding="utf-8").load()` | 读取 `data/等级标准节选.txt`，路径由 `weekpath.data_path()` 解析。 |
| 2 | 切分文本（Split） | `RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)` | 控制片段长度并保留相邻上下文。 |
| 3 | 向量化（Embed） | `OllamaEmbeddings(model="nomic-embed-text")` | 使用本地嵌入模型，数据不离开本机。 |
| 4 | 存入向量库（Store） | `Chroma.from_documents(..., persist_directory=PERSIST)` | 持久化到 `chroma_db/`，下次直接复用。 |
| 5 | 检索并生成（Retrieve + Generate） | `retriever.invoke(question)` → `format_context()` → `LLM.ask()` | 把 top-k 资料加入提示词，再走 W6 的本地/云端统一入口，并附来源。 |

## 与官方最小示例的差异

- 额外给表格片段补充“音节、汉字、词汇、语法点”等表头语义，解决表格内容难以被向量检索命中。
- 给每个片段记录 `source_name` 和 `chunk_id`，答案附来源。
- 生成层复用 W6 的 `LLM.ask()`，继承 `prefer` 参数和双向回退。
- 保留本地嵌入方案，适合隐私优先和离线课堂。