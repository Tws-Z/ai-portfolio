# 第 8 周开源项目拆解阅读笔记

1. **2-Step RAG 是什么**：先在知识库中检索相关资料，再把检索结果和问题一起交给大模型生成答案；这个流程简单、可预测，适合 FAQ 和课程文档问答。
2. **C3 做了什么**：C3 讲词向量和向量知识库，包括 Embedding API、文档读取/清洗/切片、向量数据库的建立与使用，对应我们 W7 的 Chroma + nomic-embed-text。
3. **C4 做了什么**：C4 把大模型接入 LangChain，构建检索问答链，并用 Streamlit 部署知识库助手；对应 W8 的 assistant_v1.py 和后续 W15 的部署计划。

## 引用来源

- LangChain 官方 Retrieval / 2-Step RAG 文档：https://docs.langchain.com/oss/python/langchain/rag
- Datawhale llm-universe C3/C4：https://datawhalechina.github.io/llm-universe/

说明：llm-universe 仓库未附 LICENSE，本文只记录阅读到的思路和章节对应，没有复制其代码。