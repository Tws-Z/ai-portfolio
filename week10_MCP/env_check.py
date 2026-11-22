# W10 预习环境自检
import importlib.metadata
import importlib.util
import platform
import sys
from pathlib import Path

print("当前解释器：", sys.executable, platform.python_version())

import mcp
print("mcp 包路径：", Path(mcp.__file__).resolve())

try:
    from mcp.server.fastmcp import FastMCP  # noqa: F401
    print("MCP 导入路径：1.x FastMCP OK")
except Exception:
    try:
        from mcp.server import MCPServer  # noqa: F401
        print("MCP 导入路径：2.x MCPServer OK")
    except Exception as exc:
        print("MCP 导入失败：", exc)

try:
    print("mcp 版本：", importlib.metadata.version("mcp"))
except Exception:
    print("mcp 版本：无法读取")

root = Path(__file__).resolve().parent.parent
checks = {
    "W9 tool_agent.py": root / "week09_工具调用" / "tool_agent.py",
    "生词表.csv": root / "data" / "生词表.csv",
    "等级标准节选.txt": root / "data" / "等级标准节选.txt",
    "weekpath.py": root / "weekpath.py",
}
for label, path in checks.items():
    print(("%s：%s" % (label, "存在" if path.exists() else "缺失")))

ok = all(path.exists() for path in checks.values())
print("结论：W10 MCP 预习环境可运行" if ok else "结论：仍有缺失项，请按提示补齐")