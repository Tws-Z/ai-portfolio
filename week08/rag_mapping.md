# 第 8 周 RAG 流水线映射表

| 官方流水线 | llm-universe 对应章节 | 我自己的代码（第三列） |
| --- | --- | --- |
| Load + Split | C3「数据处理：读取、清洗与切片」 | `TextLoader(CORPUS, encoding="utf-8")` 读取 `data/等级标准节选.txt`；`RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)` 切分。 |
| Embed + Store | C3「词向量及向量知识库」「搭建并使用向量数据库」 | `OllamaEmbeddings(model="nomic-embed-text")` 向量化；`Chroma.from_documents(..., persist_directory=PERSIST)` 持久化到 `chroma_db/`。 |
| Retrieve | C4「基于 LangChain 搭建检索问答链」 | `retrieve()` / `retrieve_documents()` 取 `k=3` 的片段；`assistant_v1.answer(use_rag=True)` 先 `retrieve()`，再生成。 |
| Prompt + Generate | C4「将 LLM 接入 LangChain」 | `build_prompt(question, context, require_sources=...)` 拼系统提示、检索片段和问题；最后调用 W6 的 `LLM().ask(..., prefer="local"/"api")`。 |
| Deploy + Evaluate | C4 Streamlit 部署；C5 评估与优化 | W7 的 `hallucination_log.md` 和 `w7_hallucination_results.json` 是最朴素的幻觉评估；W15 计划用 Streamlit 发布助手。 |