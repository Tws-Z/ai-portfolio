# W4 命令行学科问答机器人（API 版）
# 依赖：pip install openai python-dotenv
# 单次：python week04_API/week4_api_bot.py "把字句的教学难点有哪些"
# 多轮：python week04_API/week4_api_bot.py --chat
# 批量：python week04_API/week4_api_bot.py --batch week04_API/w4_questions.txt
import argparse
import csv
import os
import sys
from datetime import datetime

# 定位代码包根目录，保证从任意目录运行都能加载 weekpath 和 .env。
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import weekpath  # noqa: E402

weekpath.load_env()

try:
    import openai
except ImportError:
    openai = None

PROVIDERS = {
    "deepseek": {
        "key_env": "DEEPSEEK_API_KEY",
        "base_url_env": "DEEPSEEK_BASE_URL",
        "base_url": "https://api.deepseek.com/v1",
        "model_env": "DEEPSEEK_MODEL",
        "model": "deepseek-chat",
        "input_price_env": "DEEPSEEK_INPUT_PRICE_PER_MILLION",
        "output_price_env": "DEEPSEEK_OUTPUT_PRICE_PER_MILLION",
    },
    "dashscope": {
        "key_env": "DASHSCOPE_API_KEY",
        "base_url_env": "DASHSCOPE_BASE_URL",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model_env": "DASHSCOPE_MODEL",
        "model": "qwen-plus",
        "input_price_env": "DASHSCOPE_INPUT_PRICE_PER_MILLION",
        "output_price_env": "DASHSCOPE_OUTPUT_PRICE_PER_MILLION",
    },
}

DEFAULT_QUESTION = "把字句的教学难点有哪些"
CHAT_LOG = weekpath.root_path("chat_log.txt")
USAGE_CSV = weekpath.root_path("w4_usage.csv")


def get_provider_config(provider=None):
    """按 .env 中实际配置的密钥选择平台；换平台只改 base_url 和 model。"""
    names = [provider] if provider else ["deepseek", "dashscope"]
    for name in names:
        if name not in PROVIDERS:
            raise RuntimeError("不支持的平台：%s" % name)
        config = PROVIDERS[name]
        key = (os.getenv(config["key_env"]) or "").strip()
        if key and not key.startswith("your_"):
            return {
                "name": name,
                "key": key,
                "base_url": os.getenv(config["base_url_env"], config["base_url"]),
                "model": os.getenv(config["model_env"], config["model"]),
                "input_price_env": config["input_price_env"],
                "output_price_env": config["output_price_env"],
            }
    raise RuntimeError("未配置 API 密钥，请复制 .env.example 为 .env 并填写 KEY。")


def build_client(config, timeout=60.0):
    """按需创建客户端，避免没有密钥时在 import 阶段就崩溃。"""
    if openai is None:
        raise RuntimeError("未安装 openai，请先运行：pip install openai python-dotenv")
    return openai.OpenAI(
        base_url=config["base_url"],
        api_key=config["key"],
        timeout=timeout,
    )


def ask(question, temperature=0.7, max_tokens=800, history=None,
        provider=None, timeout=60.0):
    """调用一次问答接口，返回答案、token 用量和更新后的对话历史。"""
    config = get_provider_config(provider)
    messages = list(history or [])
    messages.append({"role": "user", "content": question})
    response = build_client(config, timeout).chat.completions.create(
        model=config["model"],
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    answer = response.choices[0].message.content
    usage = getattr(response, "usage", None)
    token_info = {
        "prompt_tokens": getattr(usage, "prompt_tokens", None),
        "completion_tokens": getattr(usage, "completion_tokens", None),
        "total_tokens": getattr(usage, "total_tokens", None),
    }
    messages.append({"role": "assistant", "content": answer})
    return answer, token_info, messages, config


def estimate_cost(config, token_info):
    """只有配置了每百万 token 单价时才计算费用，避免写死会变动的价格。"""
    in_price = os.getenv(config["input_price_env"], "").strip()
    out_price = os.getenv(config["output_price_env"], "").strip()
    if not in_price or not out_price:
        return None
    try:
        prompt_tokens = token_info.get("prompt_tokens") or 0
        completion_tokens = token_info.get("completion_tokens") or 0
        return (prompt_tokens * float(in_price) +
                completion_tokens * float(out_price)) / 1000000.0
    except ValueError:
        return None


def append_chat_log(question, answer, token_info, config, temperature,
                    max_tokens, mode):
    """追加问答日志；日志只记录问题和答案，不记录 API 密钥。"""
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(CHAT_LOG, "a", encoding="utf-8") as f:
        f.write("===== %s =====\n" % stamp)
        f.write("mode: %s\n" % mode)
        f.write("provider: %s | model: %s | temperature: %s | max_tokens: %s\n"
                % (config["name"], config["model"], temperature, max_tokens))
        f.write("prompt_tokens: %s | completion_tokens: %s | total_tokens: %s\n"
                % (token_info["prompt_tokens"], token_info["completion_tokens"],
                   token_info["total_tokens"]))
        f.write("Q: %s\nA: %s\n\n" % (question, answer))


def append_usage_csv(question, token_info, config, temperature, max_tokens):
    """把每次调用的 token 数据追加到 CSV，方便做 10 次费用统计。"""
    is_new = not os.path.exists(USAGE_CSV)
    with open(USAGE_CSV, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["time", "provider", "model", "temperature", "max_tokens",
                        "question", "prompt_tokens", "completion_tokens",
                        "total_tokens", "estimated_cost"],
        )
        if is_new:
            writer.writeheader()
        writer.writerow({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "provider": config["name"],
            "model": config["model"],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "question": question,
            "prompt_tokens": token_info["prompt_tokens"],
            "completion_tokens": token_info["completion_tokens"],
            "total_tokens": token_info["total_tokens"],
            "estimated_cost": estimate_cost(config, token_info),
        })


def format_usage(token_info, config):
    """格式化 token 与可选费用信息。"""
    text = "prompt_tokens=%s completion_tokens=%s total_tokens=%s" % (
        token_info["prompt_tokens"], token_info["completion_tokens"],
        token_info["total_tokens"])
    cost = estimate_cost(config, token_info)
    if cost is not None:
        text += " estimated_cost=%.6f" % cost
    return text


def load_questions(path):
    """读取批量问题文件，每个非空行是一道独立问题。"""
    questions = []
    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            text = line.strip()
            if text and not text.startswith("#"):
                questions.append(text)
    return questions


def run_one(question, args):
    """执行一次独立问答。"""
    answer, token_info, _history, config = ask(
        question,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        provider=args.provider,
        timeout=args.timeout,
    )
    print(answer)
    print("\n[usage] %s" % format_usage(token_info, config))
    append_chat_log(question, answer, token_info, config, args.temperature,
                    args.max_tokens, "single")
    append_usage_csv(question, token_info, config, args.temperature,
                     args.max_tokens)
    return token_info


def run_batch(path, args):
    """批量运行多道独立问题，并输出平均 token 与平均费用。"""
    questions = load_questions(path)
    if not questions:
        print("批量问题文件为空：%s" % path)
        return 1
    rows = []
    for index, question in enumerate(questions, 1):
        print("\n[%d/%d] %s" % (index, len(questions), question))
        token_info = run_one(question, args)
        rows.append(token_info)
    total = sum((row.get("total_tokens") or 0) for row in rows)
    average = total / len(rows) if rows else 0
    print("\n[summary] calls=%d total_tokens=%s average_tokens=%.1f"
          % (len(rows), total, average))
    return 0


def run_chat(args):
    """多轮追问模式：把每轮问答都追加到 messages 历史中。"""
    history = [{"role": "system", "content": "你是一个国际中文教育学科助手。"}]
    print("进入多轮追问模式。输入 /exit 退出。")
    while True:
        try:
            question = input("\n你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出。")
            return 0
        if not question:
            continue
        if question.lower() in ("/exit", "exit", "quit"):
            print("已退出。")
            return 0
        try:
            answer, token_info, history, config = ask(
                question,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                history=history,
                provider=args.provider,
                timeout=args.timeout,
            )
        except Exception as exc:
            print("调用失败：%s" % friendly_error(exc))
            return 1
        print("\nAI：%s" % answer)
        print("[usage] %s" % format_usage(token_info, config))
        append_chat_log(question, answer, token_info, config, args.temperature,
                        args.max_tokens, "chat")
        append_usage_csv(question, token_info, config, args.temperature,
                         args.max_tokens)


def friendly_error(exc):
    """把常见 SDK 异常翻译成可行动的中文提示。"""
    if openai is not None:
        if isinstance(exc, openai.AuthenticationError):
            return "401 鉴权失败：检查密钥是否正确、是否失效或带空格。"
        if isinstance(exc, openai.APITimeoutError):
            return "请求超时：检查网络，或把 --timeout / max_tokens 调小。"
        if isinstance(exc, openai.APIConnectionError):
            return "连接失败：检查网络、base_url 和代理设置。"
        if isinstance(exc, openai.APIStatusError):
            return "API 返回错误（状态码 %s），请查看服务端说明。" % exc.status_code
    return str(exc)


def build_parser():
    parser = argparse.ArgumentParser(description="命令行学科问答机器人（API 版）")
    parser.add_argument("question", nargs="*", help="要提问的学科问题")
    parser.add_argument("--chat", action="store_true", help="进入多轮追问模式")
    parser.add_argument("--batch", metavar="FILE", help="批量读取问题文件")
    parser.add_argument("--provider", choices=sorted(PROVIDERS), default=None,
                        help="指定平台；默认按 .env 中存在的密钥自动选择")
    parser.add_argument("--temperature", type=float, default=0.7,
                        help="随机性，0.0 更稳定，1.5 更发散")
    parser.add_argument("--max-tokens", type=int, default=800,
                        help="输出长度上限")
    parser.add_argument("--timeout", type=float, default=60.0,
                        help="单次请求超时秒数")
    return parser


def main():
    args = build_parser().parse_args()
    try:
        if args.batch:
            return run_batch(args.batch, args)
        if args.chat:
            return run_chat(args)
        question = " ".join(args.question).strip() or DEFAULT_QUESTION
        run_one(question, args)
        return 0
    except Exception as exc:
        print("调用失败：%s" % friendly_error(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())