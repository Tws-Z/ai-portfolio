# W8 阶段项目互评记录

## 1. 评阅信息

- 评阅人：赵诗雯
- 评阅对象：陈龙SERNLONG
- 对象仓库：https://gitee.com/vongsanti-sernlong/ai-protfolio
- 复现日期：2026-11-09
- 复现环境：Windows + Git for Windows 2.55.0；仓库为 Gitee 公开仓库
- 说明：以下只记录实际看到的操作现象和可执行修改建议，不打分、不评价个人。未复制对方代码到自己的仓库。

## 2. 四个维度的现象

### 维度 1：能不能跑

我执行的复现命令：

```powershell
git clone --depth 1 https://gitee.com/vongsanti-sernlong/ai-protfolio.git
python assistant_v1.py
```

实际现象：

1. `git clone` 下载对象后，工作区检出失败，终端原文包含：

```text
error: invalid path 'week07_RAG /hallucination_shturl.md'
fatal: unable to checkout working tree
```

2. 远端 HEAD 的文件树中没有找到 `assistant_v1.py`，也没有可执行的 W8 助手代码；找到的是：
   - `week07_RAG /week08_preview.md`
   - `week1/README.md`
   - `prompt_iteration_log.md/ai-portfolio/README.md`
3. 因此没有可运行的 `assistant_v1.py`，无法执行三问三答验证。

### 维度 2：README 能复现吗

- 仓库根目录没有找到 `README.md`。
- 没有找到 W8 项目的四段式 README（功能、怎么装、怎么用、已知问题）。
- `week07_RAG /week08_preview.md` 是一份计划列表，列出了 `week08_assistant/` 下计划包含的 `main.py`、`rag_qa.py`、`llm.py`、`data/`、`chroma_db/`、`README.md`，但没有安装命令、启动命令或复现步骤。
- 由于工作区无法检出，我无法按照 README 完整走通“怎么装 / 怎么用”。

### 维度 3：Release 发了吗

通过 Gitee 公开 API 查询：

```text
GET https://gitee.com/api/v5/repos/vongsanti-sernlong/ai-protfolio/tags
GET https://gitee.com/api/v5/repos/vongsanti-sernlong/ai-protfolio/releases
```

实际结果：

- 标签接口返回空列表：`tag_count = 0`
- Release 接口返回空列表：`release_count = 0`
- 当前没有 `v1.0` 标签，也没有可打开的 W8 Release 页面。

### 维度 4：有没有已知限制

- 没找到 W8 的 README，因此没有看到“已知问题 / 已知限制”章节。
- `week08_preview.md` 只列了“需要补齐实现的功能”，例如来源引用、多轮追问、双引擎回退和交互循环；这些仍是计划项，不是已经完成并记录的限制说明。

## 3. 可执行的修改建议

1. 将 `week07_RAG /hallucination_shturl.md` 中的目录名改为不含尾部空格的合法目录名，例如 `week07_RAG/hallucination_log.md`，然后重新提交并验证 Windows 上可正常 `git clone`。
2. 补齐真正的 `assistant_v1.py`，至少包含 `answer()`、`use_rag` 开关、`prefer` 和异常提示，并在根目录运行三问三答。
3. 增加 W8 的 `README.md`，按“功能 / 怎么装 / 怎么用 / 已知问题”四段写，安装步骤要能从空环境复现。
4. 增加 `requirements.txt`、`answer_log.md` 和 `peer_review` 所需的项目材料。
5. 完成并推送 `v1.0` 标签，再在 Gitee 网页端发布包含功能、安装、用法说明的 Release。