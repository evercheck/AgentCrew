"""Shared formatting utilities for fork conversation display."""

from typing import Any


def format_fork_title(title: str, metadata: dict[str, Any]) -> str:
    """Build a display title with fork indentation, prefix, and children count.

    Args:
        title: The raw conversation title / preview text.
        metadata: Conversation dict containing ``indent_level``,
                  ``is_fork``, and ``fork_children`` keys.

    Returns:
        A formatted string ready for display in any UI.
    """
    indent_level: int = metadata.get("indent_level", 0)
    is_fork: bool = metadata.get("is_fork", False)
    fork_children: list[dict[str, Any]] = metadata.get("fork_children", [])

    indent = "  " * indent_level
    prefix = "\u21b3 " if is_fork else ""
    suffix = f" [{len(fork_children)}]" if fork_children else ""
    return f"{indent}{prefix}{title}{suffix}"
