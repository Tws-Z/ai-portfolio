# W9 手写最小工具调用循环（不用框架）
# 依赖：pip install openai python-dotenv
import os
import csv
import sys
import ast
import json
import re
import operator
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import weekpath  # noqa: E402  数据路径 + 加载 .env

weekpath.load_env()

import openai  # noqa: E402

VOCAB = weekpath.data_path("生词表.csv")

# 默认走 DeepSeek 云端；教师机演示可通过环境变量切到本机 Ollama
# （OpenAI 兼容端点），例如 DEEPSEEK_BASE_URL=http://localhost:11434/v1
# DEEPSEEK_MODEL=llama3.1:8b-local。不设置时行为与云端口径完全一致。
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

_client = None


def get_client():
    global _client
    if _client is None:
        key = os.getenv("DEEPSEEK_API_KEY")
        if not key:
            raise RuntimeError("未配置 DEEPSEEK_API_KEY，请先在 .env 中填写")
        base = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        _client = openai.OpenAI(base_url=base, api_key=key)
    return _client


def get_time():
    return str(datetime.datetime.now())


# ---- 安全计算：白名单 AST，绝不使用裸 eval ----
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def _eval_node(node):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("只允许数字与 + - * / ** % 运算")


def calc(expr):
    """教学演示用：只做四则运算。为什么不用 eval？
    因为 eval 会执行任意 Python 代码，是典型的安全反模式（本课程伦理红线之一）。"""
    try:
        return str(_eval_node(ast.parse(str(expr), mode="eval")))
    except ZeroDivisionError:
        return "错误：除数为 0"
    except Exception as e:
        return "拒绝计算：%s" % e


def hsk_level(word):
    with open(VOCAB, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["词汇"].strip() == str(word).strip():
                return "%s 是 %s 级" % (word, row["HSK等级"])
    return "未找到 %s" % word


def lesson_difficulty(text, target_level="4"):
    """评估一段课文相对目标 HSK 等级的生词覆盖率和超纲词。

    输入：课文文本、目标等级（如 "4" 或 "HSK4"）
    输出：JSON 字符串，包含覆盖率、超纲词和未收录片段。
    说明：以 data/生词表.csv 的词汇表为词典，未收录片段仍需教师人工复核。
    """
    source = str(text or "").strip()
    if not source:
        return "评估失败：课文为空"
    level_text = str(target_level).upper().replace("HSK", "").strip()
    try:
        target = int(level_text)
    except ValueError:
        return "评估失败：目标等级必须是 1–6 的数字"

    vocab = {}
    with open(VOCAB, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            word = (row.get("词汇") or "").strip()
            level = (row.get("HSK等级") or "").strip()
            if word and level.isdigit():
                vocab[word] = int(level)
    words = sorted(vocab, key=len, reverse=True)

    matched = []
    out_of_level = []
    unlisted = []
    i = 0
    while i < len(source):
        ch = source[i]
        if "\u4e00" <= ch <= "\u9fff":
            found = None
            for word in words:
                if source.startswith(word, i):
                    found = word
                    break
            if found:
                matched.append(found)
                if vocab[found] > target:
                    out_of_level.append(found)
                i += len(found)
            else:
                start = i
                i += 1
                while i < len(source) and "\u4e00" <= source[i] <= "\u9fff":
                    if any(source.startswith(word, i) for word in words):
                        break
                    i += 1
                unlisted.append(source[start:i])
        else:
            i += 1

    in_level = [word for word in matched if vocab[word] <= target]
    total_units = len(matched) + sum(len(segment) for segment in unlisted)
    coverage = len(in_level) / total_units if total_units else 0.0
    return json.dumps({
        "target_level": target,
        "total_units": total_units,
        "in_level_count": len(in_level),
        "out_of_level_count": len(out_of_level),
        "unknown_char_count": sum(len(segment) for segment in unlisted),
        "coverage_rate": round(coverage, 4),
        "out_of_level_words": sorted(set(out_of_level)),
        "unlisted_segments": unlisted,
        "note": "基于 data/生词表.csv 的样例词典，结果需人工复核",
    }, ensure_ascii=False)

TOOLS = {"get_time": get_time, "calc": calc, "hsk_level": hsk_level, "lesson_difficulty": lesson_difficulty}
TOOL_ARGS = {
    "get_time": 0,
    "calc": 1,
    "hsk_level": 1,
    "lesson_difficulty": 2,
}


def validate_args(tool_name, args):
    """校验每个工具的参数数量和基本类型，避免把错误参数直接执行。"""
    expected = TOOL_ARGS.get(tool_name)
    if expected is None:
        return "未知工具：%s" % tool_name
    if len(args) != expected:
        return "工具参数数量错误：%s 需要 %d 个参数，实际收到 %d 个" % (
            tool_name, expected, len(args))
    if tool_name in ("calc", "hsk_level") and not isinstance(args[0], str):
        return "工具参数类型错误：%s 的第一个参数必须是字符串" % tool_name
    if tool_name == "lesson_difficulty":
        if not isinstance(args[0], str):
            return "工具参数类型错误：lesson_difficulty 的课文必须是字符串"
        if isinstance(args[1], bool) or not isinstance(args[1], (str, int)):
            return "工具参数类型错误：lesson_difficulty 的目标等级必须是字符串或整数"
    return None

SYS = ("你是国际中文助教。可用工具只有这 4 个：get_time（查当前时间，无参数）、"
       "calc（四则运算，如 calc('35*24')）、hsk_level（查生词 HSK 等级，如 hsk_level('把')）、"
       "lesson_difficulty（评估课文难度，输入课文文本和目标等级，如 lesson_difficulty('课文文本', '4')）。"
       '重要规则：只要用户询问当前时间、数学计算、HSK 等级或课文难度，必须先调用对应工具，'
       '不得凭记忆直接回答；工具结果返回前不要给出答案。'
       '需要调用时只输出一行 JSON，格式：{"tool": "工具名", "args": [参数]}；'
       "一次只调用一个工具，绝不编造不存在的工具名；无需工具时直接回答。")


def parse_calls(txt):
    """容错解析：剥掉 ```json 围栏与前后客套话，返回全部工具调用（0/1/多个）。

    模型不一定老实输出一个 JSON：可能带围栏、可能一段自然语言里夹着 JSON、
    也可能把多个工具调用并列输出成多行——这里全部兜住。"""
    s = (txt or "").strip()
    s = s.replace("```json", "").replace("```", "").strip()
    try:
        obj = json.loads(s)
        return [obj] if isinstance(obj, dict) else []
    except Exception:
        m = re.search(r"\{.*\}", s, re.S)  # re.S：跨行也能匹配到 JSON 块
        if m:
            try:
                obj = json.loads(m.group())
                if isinstance(obj, dict):
                    return [obj]
            except Exception:
                pass
        # 多个工具调用并列输出（小模型常态）：逐块全部解析，一轮依次执行
        calls = []
        for blk in re.findall(r"\{[^{}]*\}", s):
            try:
                obj = json.loads(blk)
            except Exception:
                continue
            if isinstance(obj, dict):
                calls.append(obj)
        return calls


def run(user_msg, max_calls=2, trace=None):
    msgs = [{"role": "system", "content": SYS}, {"role": "user", "content": user_msg}]
    for _ in range(max_calls):
        txt = get_client().chat.completions.create(
            model=MODEL, messages=msgs).choices[0].message.content
        calls = [c for c in parse_calls(txt)
                 if isinstance(c.get("tool"), str) and c.get("tool") in TOOLS]
        if not calls:
            if trace is not None:
                trace.append({"round": _ + 1, "model_output": txt, "calls": [], "tool_results": []})
            return txt                                   # 没调用工具 → 直接回答
        # 一轮内依次执行模型请求的全部工具，结果合并回喂
        results = []
        for call in calls:
            args = call.get("args") or []
            if not isinstance(args, list):
                results.append("工具参数格式错误：%r" % (args,))
                continue
            arg_error = validate_args(call["tool"], args)
            if arg_error:
                results.append(arg_error)
                continue
            try:
                results.append("%s%r → %s" % (call["tool"], args, TOOLS[call["tool"]](*args)))
            except Exception as e:
                results.append("工具执行失败：%s" % e)
        if trace is not None:
            trace.append({"round": _ + 1, "model_output": txt, "calls": calls, "tool_results": results})
        msgs += [{"role": "assistant", "content": txt},
                 {"role": "user", "content": "工具返回：%s。请据此作答。" % "；".join(results)}]
    # 达到上限后强制收口，避免无限循环烧 token；若模型还在请求工具，不能把裸 JSON 当答案。
    final = get_client().chat.completions.create(
        model=MODEL, messages=msgs).choices[0].message.content
    final_calls = parse_calls(final)
    if final_calls:
        if trace is not None:
            trace.append({"round": max_calls + 1, "model_output": final,
                          "calls": final_calls, "tool_results": ["达到最大工具调用轮数"]})
        return "工具调用未完成：模型在达到调用上限后仍在请求工具。请重试或改用云端模型。"
    return final


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "请依次查询两件事：1. '把'字的 HSK 等级是多少？2. 现在的时间是多少？"
    print("用户输入：", q)
    print("助手：", run(q))
