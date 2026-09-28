# AI 辅助编程实录

## 1. 任务与提示词

### 要做什么

把 `data/生词表.csv` 读入 Python，筛选出 HSK4 词汇，在代码包根目录生成 `练习.txt`。要求从任意目录运行都能找到数据，并且输出文件始终落在代码包根目录。

### 我写给 AI 的提示词

```text
你是我的 Python 结对编程助教。我是刚开始学习 Python 的汉语国际教育专业学生，请一步一步帮助我完成下面任务。

任务：
读取代码包 data/生词表.csv 中的词条，筛选出 HSK4 词汇，并为每个词生成一道造句练习题，最终写入代码包根目录的 练习.txt。

硬性要求：
1. 使用 csv.DictReader 读取 CSV，字段名必须以真实 CSV 为准。
2. 文件和程序都使用 UTF-8，避免中文乱码。
3. 无论从哪个目录运行，都能找到 data/生词表.csv。
4. 无论从哪个目录运行，练习.txt 都必须生成在代码包根目录。
5. 代码要加中文注释，便于我理解。
6. 请先给出最基础的完整初版，不要一次堆太多高级写法。
```

### AI 的回答思路

AI 先给出一个能读取 CSV、筛选 HSK4 并写入文件的最小版本。它的结构清楚，但默认数据和输出都在当前工作目录，而且使用了 CSV 中不存在的字段名“等级”。这两个问题会导致从其他目录运行时失败。

## 2. AI 初版代码

```python
import csv


def main():
    with open("data/生词表.csv", encoding="utf-8") as f:
        words = list(csv.DictReader(f))

    hsk4 = [word for word in words if word["等级"] == "4"]

    with open("练习.txt", "w", encoding="utf-8") as f:
        for word in hsk4:
            f.write("用“%s”造一个句子。（%s）\n" % (word["词汇"], word["词性"]))

    print("已生成 练习.txt")


if __name__ == "__main__":
    main()
```

初版代码运行时的实际问题：

1. 从 `week03_Python` 目录运行时，程序找不到 `data/生词表.csv`。
2. CSV 的真实字段名是 `HSK等级`，不是 `等级`，因此筛选会报错。
3. `练习.txt` 会落在启动程序时所在的目录，不符合“代码包根目录”的要求。
4. 找到 HSK4 词汇后没有统计词性分布，输出也比较简略。

## 3. 我的修改点（5 条）

### 修改 1：把字段名改成真实 CSV 中的“HSK等级”

**改法：**

```python
current = _clean(word.get("HSK等级")).upper().replace("HSK", "").strip()
if current == target:
    result.append(word)
```

**为什么：**  
我先打开 CSV 检查了表头，确认实际字段是 `词汇,HSK等级,词性,释义,备注`。直接使用 AI 初版里的“等级”会触发 `KeyError`，所以字段名必须和真实数据完全一致。同时把外层空格和 `HSK` 前缀清理掉，兼容 `4`、`HSK4` 等写法。

### 修改 2：统一使用 UTF-8，并兼容带 BOM 的文件

**改法：**

```python
with open(path, "r", encoding="utf-8-sig", newline="") as f:
```

**为什么：**  
CSV 中可能有中文和 BOM。`utf-8-sig` 既能读取普通 UTF-8，也能兼容带 BOM 的 UTF-8，避免第一列出现奇怪的 `\ufeff`。写入 `练习.txt` 时也明确使用 `encoding="utf-8"`，保证中文不会乱码。

### 修改 3：用 `weekpath.data_path()` 找数据，不再依赖当前目录

**改法：**

```python
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
import weekpath

DEFAULT_INPUT = weekpath.data_path("生词表.csv")
```

**为什么：**  
AI 初版使用相对路径 `data/生词表.csv`，在哪里启动程序就会到哪里找数据。课程代码包已经提供了 `weekpath.data_path()`，它根据脚本本身的位置定位 `data/`，所以无论我是在 VS Code、PowerShell 还是其他目录运行，都能找到同一个 CSV。

### 修改 4：用 `weekpath.root_path()` 固定练习题输出位置

**改法：**

```python
DEFAULT_OUTPUT = weekpath.root_path("练习.txt")
out = out or DEFAULT_OUTPUT
```

**为什么：**  
初版把 `练习.txt` 写在当前目录，可能落在 `week03_Python` 或其他文件夹里。老师要求产物必须落在代码包根目录，所以统一通过 `weekpath.root_path()` 生成路径。这样既满足目录规范，也方便我从任意位置运行脚本后检查结果。

### 修改 5：增加词性分组、统计和输入检查

**改法：**

```python
counts = count_by_pos(words)
for pos, _count in counts:
    group = [word for word in words if (_clean(word.get("词性")) or "未标注") == pos]
    lines.extend(["", "## %s" % pos, ""])
    for index, word in enumerate(group, 1):
        lines.append("%d. 用“%s”造一个句子。（释义：%s）" % (...))
```

同时增加缺列和空谓词检查：

```python
missing = [name for name in REQUIRED_COLUMNS if name not in fieldnames]
if missing:
    raise ValueError("生词表缺少字段：%s" % "、".join(missing))
```

**为什么：**  
初版只能输出一长串句子，很难看出词汇类别。增加词性分组和统计后，练习题更有教学结构，也方便我检查筛选结果。增加字段检查后，如果以后换 CSV 或表头写错，程序会直接说明缺少哪一列，而不是抛出难以理解的错误。

## 4. 最终版 vs 初版差异说明

| 对比项 | AI 初版 | 我的最终版 | 为什么这样改 |
| --- | --- | --- | --- |
| CSV 字段 | `word["等级"]` | `word.get("HSK等级")` | 与真实 CSV 表头一致，避免 `KeyError` |
| 中文编码 | 读取时使用 `utf-8` | 读取使用 `utf-8-sig`，写入使用 `utf-8` | 兼容 BOM，避免首列和中文乱码 |
| 数据路径 | `data/生词表.csv` | `weekpath.data_path("生词表.csv")` | 从任意目录运行都能找到数据 |
| 输出路径 | 当前目录下的 `练习.txt` | `weekpath.root_path("练习.txt")` | 满足作业要求，产物固定在代码包根目录 |
| 文件检查 | 没有检查 | 检查必需字段和空行 | 出问题时给出清晰提示 |
| 练习结构 | 所有词顺序输出 | 按词性分组并统计数量 | 输出更像可用的教学练习材料 |
| 运行结果 | 依赖当前目录，容易失败 | 可从任意目录运行 | 符合课程“路径统一定位”的要求 |

## 5. 实际运行结果

我在代码包外的目录执行：

```bash
python week03_Python/vocab_tool.py
```

程序输出：

```text
总词汇 13 个，其中 HSK4 词汇 4 个，词性分布：{'动词': 3, '名词': 1}
已生成：C:\...\ai-portfolio\练习.txt
```

生成的 `练习.txt` 包含：

- 题目总数和词性分布说明
- “动词”分组下的 3 个 HSK4 词汇
- “名词”分组下的 1 个 HSK4 词汇
- 每个词的释义和造句要求

这说明程序已经能够稳定读取数据、按 HSK4 筛选，并把产物写到代码包根目录。