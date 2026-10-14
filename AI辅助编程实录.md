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
---

# W4：第一次 API 调用（AI 结对编程实录）

## 1. 任务与提示词

### 要做什么

制作一个命令行学科问答机器人 `week4_api_bot.py`：接收问题、调用大模型 API、在终端打印答案，并把问答追加到代码包根目录的 `chat_log.txt`。

### 我写给 AI 的提示词

```text
你是一位 Python 结对编程助教。请帮我把 week4_api_bot.py 扩展成一个适合国际中文教育学生使用的命令行 API 机器人。

要求：
1. 密钥必须从 .env 和 os.getenv 读取，绝不写进代码。
2. 支持 DeepSeek 和通义兼容模式，切换平台时主要改 base_url 和 model。
3. 单次问答要把 Q/A 追加到 chat_log.txt。
4. 支持 --chat 多轮追问，messages 中保留历史。
5. 支持 --batch 批量 10 个学科问题，并记录 prompt_tokens、completion_tokens、total_tokens。
6. 对缺少密钥、401、超时、连接失败给出中文可行动提示。
7. 记录 token 数据到 w4_usage.csv，方便计算平均备课成本。
```

## 2. AI 初版代码

AI 先给出的初版只能单次提问，缺少多轮追问和 token 记录：

```python
import os
import sys
import openai

BASE_URL = "https://api.deepseek.com/v1"
MODEL = "deepseek-chat"


def ask(question):
    client = openai.OpenAI(
        base_url=BASE_URL,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": question}],
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "把字句的教学难点有哪些"
    print(ask(question))
```

初版能完成“问一句、答一句”，但无法保留上下文，也没有记录 token 和费用，还不能应对缺失密钥和网络错误。

## 3. 我的修改点（5 条）

### 修改 1：让客户端按需创建，并把错误变成人话

`get_client()` 或 `build_client()` 只在真正调用时检查密钥。缺少密钥时输出“请复制 .env.example 为 .env”，而不是在 import 阶段抛出长堆栈。

### 修改 2：增加多轮追问 `--chat`

把每轮 `user` 和 `assistant` 消息追加到 `messages`，下一次请求继续使用这个历史，从而让机器人记住上一轮内容。

### 修改 3：增加批量模式和 token 记录

`--batch` 读取 `w4_questions.txt`，每道题独立调用，并记录：

```text
prompt_tokens, completion_tokens, total_tokens
```

数据写入 `w4_usage.csv`，用于作业中的 10 次费用统计。

### 修改 4：增加参数选项

支持：

```bash
--temperature 0.0/1.5
--max-tokens 15/800
--timeout 60
```

这样可以在不修改代码的情况下完成参数对比实验。

### 修改 5：增加平台切换与费用估算

通过 `.env` 中的 `DEEPSEEK_*` 或 `DASHSCOPE_*` 配置选择平台。费用单价由 `.env` 提供，没有写死价格，因为平台价格会调整。

## 4. 最终版与初版差异说明

| 对比项 | AI 初版 | 最终版 | 为什么这样改 |
| --- | --- | --- | --- |
| 密钥检查 | 直接创建客户端 | 调用前检查并给出中文提示 | 缺密钥时失败得可行动 |
| 对话能力 | 单轮 | `--chat` 多轮历史 | 完成课后“多轮追问”作业 |
| 批量调用 | 无 | `--batch` | 方便完成 10 次费用统计 |
| token 统计 | 无 | 记录并写入 CSV | 费用必须从 usage 里计算 |
| 平台切换 | 改代码或固定 DeepSeek | `.env` 配置自动选择 | 只改 base_url 和 model |
| 错误处理 | 原始异常 | 401、超时、连接失败分别提示 | 能判断是密钥、网络还是代码问题 |
| 参数体验 | 无参数入口 | temperature / max_tokens / timeout | 完成课堂参数体验表 |

## 5. 官方 API 文档精读记录

阅读平台文档后，用自己的话记录：

- `temperature`：控制回答的随机性。值越低，输出越稳定；值越高，措辞越多样，但也更容易跑偏。教学材料建议使用 0.2–0.7。
- `max_tokens`：限制本次回答最多生成多少 token。设置太小会出现半句截断，设置太大则提高费用上限。
- `timeout`：规定客户端等待服务器响应的最长时间。超时通常先检查网络、域名和服务器负载，再考虑放大超时时间。
- 平台计费：输入 token 和输出 token 分开计价，单价会变化，因此不能把价格写死在程序里。

## 6. 费用判断

实际调用 10 次后，根据 `w4_usage.csv` 汇总：

- 总输入 token：待运行后填写
- 总输出 token：待运行后填写
- 总费用：待运行后填写
- 一次备课问答平均成本：待运行后填写
- 我的判断：待运行后填写

## 7. 失败实验实测

- 缺密钥：输出“调用失败：未配置 API 密钥，请复制 .env.example 为 .env 并填写 KEY”，退出码 1。
- 错误域名：输出“调用失败：连接失败：检查网络、base_url 和代理设置”，退出码 1。
- 不可达端口：输出“调用失败：请求超时：检查网络，或把 --timeout / max_tokens 调小”，退出码 1。

结论：脚本能把“密钥问题”和“网络问题”分开提示，符合课程要求中“失败也要失败得清楚”。

## 8. 密钥安全

完整自查见根目录的 `密钥安全自查表.md`。核心原则：

1. 密钥只在本机 `.env`。
2. 代码只使用 `os.getenv()`。
3. 日志不写入密钥。
4. 截图不显示完整密钥。
5. 一旦泄露，先到平台后台吊销，再生成新密钥。
