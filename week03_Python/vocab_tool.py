# W3 生词表 CSV -> 自动生成 HSK4 练习题
# 运行：python week03_Python/vocab_tool.py
import csv
import os
import sys
from collections import Counter

# 把代码包根目录加入模块搜索路径，保证从任意目录运行都能导入 weekpath。
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import weekpath  # noqa: E402

DEFAULT_INPUT = weekpath.data_path("生词表.csv")
DEFAULT_OUTPUT = weekpath.root_path("练习.txt")
REQUIRED_COLUMNS = ("词汇", "HSK等级", "词性", "释义")


def _clean(value):
    """清理 CSV 单元格中的空格和空值。"""
    return str(value or "").strip()


def load_words(path=None):
    """读取生词表，并检查必需字段是否存在。"""
    path = path or DEFAULT_INPUT
    if not os.path.exists(path):
        raise FileNotFoundError("找不到生词表：%s" % path)

    # utf-8-sig 同时兼容带 BOM 和不带 BOM 的 UTF-8 文件。
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        missing = [name for name in REQUIRED_COLUMNS if name not in fieldnames]
        if missing:
            raise ValueError(
                "生词表缺少字段：%s；实际字段：%s"
                % ("、".join(missing), "、".join(fieldnames))
            )

        words = []
        for row in reader:
            if any(_clean(value) for value in row.values()):
                words.append({key: _clean(value) for key, value in row.items()})
    return words


def filter_by_level(words, level="4"):
    """按 HSK 等级筛选词汇。"""
    target = _clean(level).upper().replace("HSK", "").strip()
    result = []
    for word in words:
        current = _clean(word.get("HSK等级")).upper().replace("HSK", "").strip()
        if current == target:
            result.append(word)
    return result


def count_by_pos(words):
    """统计词性分布，返回按数量从多到少的列表。"""
    counter = Counter(_clean(word.get("词性")) or "未标注" for word in words)
    return counter.most_common()


def gen_exercises(words, out=None):
    """按词性分组生成练习题，默认写到代码包根目录。"""
    out = out or DEFAULT_OUTPUT
    out_dir = os.path.dirname(os.path.abspath(out))
    os.makedirs(out_dir, exist_ok=True)

    counts = count_by_pos(words)
    lines = [
        "# HSK4 词汇造句练习",
        "",
        "共 %d 个词；词性分布：%s"
        % (
            len(words),
            "，".join("%s %d 个" % (pos, count) for pos, count in counts) or "无",
        ),
    ]

    for pos, _count in counts:
        group = [word for word in words if (_clean(word.get("词性")) or "未标注") == pos]
        lines.extend(["", "## %s" % pos, ""])
        for index, word in enumerate(group, 1):
            lines.append(
                "%d. 用“%s”造一个句子。（释义：%s）"
                % (index, _clean(word.get("词汇")), _clean(word.get("释义")) or "未提供")
            )

    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    return out


def main():
    """执行读取、筛选、统计和生成练习题的完整流程。"""
    try:
        words = load_words()
        level_four = filter_by_level(words, "4")
        if not level_four:
            print("没有找到 HSK4 词汇，请检查 data/生词表.csv 的“HSK等级”列。")
            return 1

        output = gen_exercises(level_four)
        print(
            "总词汇 %d 个，其中 HSK4 词汇 %d 个，词性分布：%s"
            % (len(words), len(level_four), dict(count_by_pos(level_four)))
        )
        print("已生成：%s" % output)
        return 0
    except (FileNotFoundError, ValueError) as exc:
        print("运行失败：%s" % exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())