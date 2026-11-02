# W7 RAG 入门：加载 -> 分块 -> 向量化 -> 检索 + 生成
# 依赖：pip install langchain langchain-community langchain-text-splitters
#       pip install langchain-ollama langchain-chroma chromadb
# 运行：python week07_RAG/rag_qa.py "HSK4 需要掌握多少词汇？"
import os
import sys

# 代码包根目录：week07_RAG 的上一级。
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import weekpath  # noqa: E402

weekpath.load_env()

from langchain_community.document_loaders import TextLoader  # noqa: E402
from langchain_text_splitters import RecursiveCharacterTextSplitter  # noqa: E402
from langchain_ollama import OllamaEmbeddings  # noqa: E402
from langchain_chroma import Chroma  # noqa: E402

from llm import LLM  # noqa: E402

CORPUS = weekpath.data_path("等级标准节选.txt")
PERSIST = weekpath.root_path("chroma_db")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
DEFAULT_QUESTION = "HSK4 需要掌握多少词汇？"


def get_embeddings():
    """使用本地 Ollama 嵌入模型，数据不出本机。"""
    return OllamaEmbeddings(model=EMBED_MODEL)


def _build_vectorstore(embeddings):
    """加载学科文本，按 500 字、重叠 50 字切块，并写入 Chroma。"""
    if not os.path.exists(CORPUS):
        raise FileNotFoundError("找不到学科文本：%s" % CORPUS)

    documents = TextLoader(CORPUS, encoding="utf-8").load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        add_start_index=True,
    )
    splits = splitter.split_documents(documents)

    # 给每个片段写入可读的来源，方便答案附出处。
    source_name = os.path.basename(CORPUS)
    for index, doc in enumerate(splits, 1):
        text = doc.page_content.strip()
        # 表格片段缺少“HSK/词汇/汉字/语法点”等自然语言关键词，
        # 直接向量化时容易被具体问题漏检；补一行表头语义提高召回率。
        if "音节" in text and "汉字" in text and "词汇" in text and "语法点" in text:
            text = (
                "《国际中文教育中文水平等级标准》HSK等级语言量化指标总表。"
                "列依次为：等次、级别、音节、汉字、词汇、语法点；"
                "表格中的 a/b 表示 a 为本级新增、b 为累计数量。\n" + text
            )
            doc.metadata["section"] = "language_metrics_table"
        elif "对应 HSK" in text or "对应HSK" in text:
            text = "国际中文教育中文水平等级标准与 HSK 等级的对应关系。\n" + text
            doc.metadata["section"] = "hsk_mapping"
        doc.page_content = text
        doc.metadata["source_name"] = source_name
        doc.metadata["chunk_id"] = index

    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=PERSIST,
    )
    # 兼容不同版本：新版会自动持久化，旧版可能需要显式 persist。
    if hasattr(vectorstore, "persist"):
        vectorstore.persist()
    return vectorstore


def get_retriever(k=3, rebuild=False):
    """获取检索器；已有 chroma_db 时直接复用，避免每次重复建库。"""
    embeddings = get_embeddings()
    if not rebuild and os.path.isdir(PERSIST) and os.listdir(PERSIST):
        vectorstore = Chroma(
            persist_directory=PERSIST,
            embedding_function=embeddings,
        )
    else:
        vectorstore = _build_vectorstore(embeddings)
    return vectorstore.as_retriever(search_kwargs={"k": k})


def retrieve_documents(question, k=3, rebuild=False):
    """返回检索到的文档对象，保留来源和片段内容。"""
    retriever = get_retriever(k=k, rebuild=rebuild)
    return retriever.invoke(question)


def format_context(documents):
    """把检索片段拼成带来源编号的上下文。"""
    blocks = []
    for index, doc in enumerate(documents, 1):
        source = doc.metadata.get("source_name", "未知资料")
        chunk_id = doc.metadata.get("chunk_id", "?")
        blocks.append(
            "【资料 %d｜来源：%s｜片段 %s】\n%s"
            % (index, source, chunk_id, doc.page_content.strip())
        )
    return "\n\n".join(blocks)


def retrieve(question, k=3, rebuild=False):
    """兼容课程接口：返回拼接后的检索文本。"""
    return format_context(retrieve_documents(question, k=k, rebuild=rebuild))


def build_prompt(question, context):
    """把检索结果放进强约束提示词，要求模型只依据资料回答。"""
    return (
        "你是国际中文教育学科助手。请严格根据下面的资料回答问题。\n"
        "资料中没有的内容必须如实回答「资料中未提及」，不得凭记忆补充数字或规则。\n如果资料包含表格，请严格按表头逐列对应，注意区分音节、汉字、词汇和语法点，不要混用相邻列。\n\n"
        "资料：\n%s\n\n问题：%s\n\n"
        "请先给出简洁答案，再列出你使用的资料编号。"
        % (context, question)
    )


def rag_qa(question, prefer="local", k=3, rebuild=False, with_sources=True):
    """执行完整 RAG：检索 -> 构造提示词 -> 调用 W6 统一入口。"""
    documents = retrieve_documents(question, k=k, rebuild=rebuild)
    if not documents:
        return "资料中未提及。"
    context = format_context(documents)
    answer = LLM().ask(build_prompt(question, context), prefer=prefer)

    if with_sources:
        source_lines = []
        for index, doc in enumerate(documents, 1):
            source = doc.metadata.get("source_name", "未知资料")
            chunk_id = doc.metadata.get("chunk_id", "?")
            source_lines.append("- 资料 %d：%s（片段 %s）" % (index, source, chunk_id))
        return answer.rstrip() + "\n\n参考来源：\n" + "\n".join(source_lines)
    return answer


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]).strip() or DEFAULT_QUESTION
    prefer = os.getenv("RAG_PREFER", "local")
    print(rag_qa(question, prefer=prefer))