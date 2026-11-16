# W8 B 路径改造说明：返回出处开关

## 改造点

在原有 RAG 回答的基础上增加 `with_sources` 开关：

- `assistant_v1.answer(..., with_sources=True/False)`
- `rag_qa.retrieve(..., include_sources=True/False)`
- `rag_qa.format_context(..., include_sources=True/False)`
- `rag_qa.build_prompt(..., require_sources=True/False)`
- 命令行新增 `--no-sources`

默认值为 `True`，保持原有 W8 行为不变；设为 `False` 时，模型仍使用检索资料回答，但提示词不要求资料编号，回答不会追加“参考来源”列表。

## 代码位置

- `week08_助手v1.0/assistant_v1.py`
- `week07_RAG/rag_qa.py`

## 实测命令

```powershell
python week08_助手v1.0/assistant_v1.py "按照 2021 标准，四级（对应 HSK4）累计需要掌握多少词汇？" --prefer api
python week08_助手v1.0/assistant_v1.py "按照 2021 标准，四级（对应 HSK4）累计需要掌握多少词汇？" --prefer api --no-sources
```

## 实测结果

- `with_sources=True`：回答 3245 个词汇，并列出“资料 2”。
- `with_sources=False`：同样回答 3245 个词汇，但不输出资料编号。

完整输出见 `b_path_run_output.txt`，运行截图见 `b_path_run.png`，原始结果见 `b_path_results.json`。