# W10 最小 MCP 客户端：启动服务端、发现工具、调用工具
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = Path(__file__).resolve().parent
SERVER = StdioServerParameters(
    command=sys.executable,
    args=[str(HERE / "hsk_mcp_server.py")],
    cwd=str(HERE),
)


def result_text(result):
    """提取 MCP 工具调用返回的文本内容。"""
    pieces = []
    for item in getattr(result, "content", None) or []:
        text = getattr(item, "text", None)
        if text is not None:
            pieces.append(str(text))
    if not pieces:
        structured = getattr(result, "structuredContent", None)
        if structured is not None:
            pieces.append(json.dumps(structured, ensure_ascii=False))
    return "\n".join(pieces) if pieces else str(result)


async def main():
    async with stdio_client(SERVER, errlog=sys.stderr) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("MCP client connected")
            tools = await session.list_tools()
            print("Discovered tools:")
            for tool in tools.tools:
                desc = (tool.description or "").replace("\n", " ")
                print("- %s: %s" % (tool.name, desc))
            for name, arguments in [
                ("hsk_level", {"word": "把"}),
                ("count_by_level", {"level": "4"}),
                ("list_by_level", {"level": "3"}),
            ]:
                result = await session.call_tool(name, arguments=arguments)
                print('CALL %s %s -> %s' % (name, arguments, result_text(result)))


if __name__ == "__main__":
    asyncio.run(main())