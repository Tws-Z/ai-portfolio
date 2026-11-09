# W8 阶段项目一：学科智能问答助手 v1.0
# 组装 = W2 提示词库 + W6 双引擎 + W7 知识库问答
import argparse
import os
import sys

# 代码包根目录：week08_助手v1.0 的上一级。
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import weekpath  # noqa: E402

weekpath.load_env()

from llm import LLM  # noqa: E402
from rag_qa import retrieve, build_prompt  # noqa: E402

# W2 的角色与话术约束：明确身份、受众和回答边界。
SYSTEM_HINT = (
    "你是国际中文教育学科助手，面向 HSK3–4 学习者。"
    "回答要准确、简洁、可核验；资料不足时必须明确说明，不能猜测数字或规则。"
)

llm = LLM()


def answer(question, use_rag=True, prefer="local", k=3):
    """统一问答入口：use_rag 控制是否检索资料，prefer 控制引擎偏好。"""
    if prefer not in ("local", "api"):
        raise ValueError("prefer 只能是 'local' 或 'api'")
    try:
        if use_rag:
            context = retrieve(question, k=k)
            prompt = SYSTEM_HINT + "\n" + build_prompt(question, context)
        else:
            # 纯对话模式：只给系统人设，不附加知识库资料。
            prompt = SYSTEM_HINT + "\n问题：" + question
        return llm.ask(prompt, prefer=prefer, temperature=0.3, max_tokens=600)
    except Exception as exc:
        # 课堂演示不能因为 Ollama 未启动或云端超时而直接退出。
        return "运行失败：%s: %s" % (type(exc).__name__, exc)


def build_parser():
    parser = argparse.ArgumentParser(description="学科智能问答助手 v1.0")
    parser.add_argument("question", nargs="*", help="要提问的学科问题")
    parser.add_argument("--no-rag", action="store_true", help="关闭知识库检索，使用纯对话")
    parser.add_argument("--prefer", choices=("local", "api"), default="local",
                        help="首选引擎：local 本地，api 云端")
    parser.add_argument("--k", type=int, default=3, help="RAG 检索片段数")
    return parser


def main():
    args = build_parser().parse_args()
    question = " ".join(args.question).strip()
    if not question:
        question = "HSK4（四级）累计需要掌握多少词汇？"
    print(answer(question, use_rag=not args.no_rag, prefer=args.prefer, k=args.k))


if __name__ == "__main__":
    main()