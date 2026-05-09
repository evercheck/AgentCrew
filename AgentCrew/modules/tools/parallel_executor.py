from dataclasses import dataclass
from typing import Any, Awaitable, Callable
import asyncio


SEQUENTIAL_TOOLS = frozenset({"transfer", "ask"})
SEQUENTIAL_PREFIXES = ("browser_",)


def is_sequential_tool(tool_name: str) -> bool:
    if tool_name in SEQUENTIAL_TOOLS:
        return True
    return any(tool_name.startswith(prefix) for prefix in SEQUENTIAL_PREFIXES)


@dataclass
class ToolResult:
    tool_use: dict[str, Any]
    result: Any
    is_error: bool = False


async def execute_tools_in_parallel(
    tool_uses: list[dict[str, Any]],
    executor: Callable[[str, dict], Awaitable[Any]],
) -> list[ToolResult]:
    if len(tool_uses) == 1:
        return [await _safe_execute(executor, tool_uses[0])]

    tasks = [_safe_execute(executor, tu) for tu in tool_uses]
    return list(await asyncio.gather(*tasks))


async def _safe_execute(
    executor: Callable[[str, dict], Awaitable[Any]],
    tool_use: dict[str, Any],
) -> ToolResult:
    try:
        result = await executor(tool_use["name"], tool_use["input"])
        return ToolResult(tool_use=tool_use, result=result, is_error=False)
    except Exception as e:
        return ToolResult(tool_use=tool_use, result=str(e), is_error=True)
