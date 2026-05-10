from __future__ import annotations

from typing import Any


def message_content_to_text(content: Any) -> str:
    """Convert message content (str, list, or None) to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "thinking":
                    parts.append(str(block.get("thinking", "")))
                else:
                    parts.append(str(block.get("text", "")))
            else:
                parts.append(str(block))
        return " ".join(part for part in parts if part)
    if content is None:
        return ""
    return str(content)


def extract_thinking_text(message: dict[str, Any]) -> str:
    """Extract thinking/reasoning text from a message."""
    content = message.get("content", "")
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "thinking":
                parts.append(str(block.get("thinking", "")))
        return " ".join(part for part in parts if part)
    if message.get("role") == "thinking":
        return message_content_to_text(content)
    return ""


def extract_assistant_text(message: dict[str, Any]) -> str:
    """Extract assistant text from a message, excluding thinking blocks."""
    if message.get("role") == "thinking":
        return ""
    content = message.get("content", "")
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "thinking":
                    continue
                parts.append(str(block.get("text", "")))
            else:
                parts.append(str(block))
        return " ".join(part for part in parts if part)
    return message_content_to_text(content)


def extract_tool_calls(message: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract tool call entries from a message."""
    tool_calls = message.get("tool_calls")
    if not isinstance(tool_calls, list):
        return []
    extracted = []
    for tool_call in tool_calls:
        if not isinstance(tool_call, dict):
            continue
        tool_call_id = tool_call.get("id")
        tool_name = tool_call.get("name")
        if not isinstance(tool_call_id, str) or not isinstance(tool_name, str):
            continue
        extracted.append(
            {
                "id": tool_call_id,
                "name": tool_name,
                "input": tool_call.get("arguments", tool_call.get("input", {})),
                "type": tool_call.get("type", "tool_call"),
            }
        )
    return extracted


def prompt_to_text(prompt: list[Any]) -> str:
    """Convert an ACP prompt (list of content blocks) to plain text."""
    chunks: list[str] = []
    for block in prompt:
        block_type = getattr(block, "type", None)
        if block_type == "text":
            chunks.append(getattr(block, "text", ""))
        elif block_type == "resource_link":
            chunks.append(resource_link_to_text(block))
        elif block_type == "resource":
            chunks.append(embedded_resource_to_text(block))
        else:
            chunks.append(f"[Unsupported ACP content block: {block_type}]")
    return "\n\n".join(chunk for chunk in chunks if chunk)


def resource_link_to_text(block: Any) -> str:
    """Convert an ACP resource link block to a text representation."""
    uri = getattr(block, "uri", "")
    name = getattr(block, "name", "resource")
    return f"[ACP resource link: {name}]({uri})"


def embedded_resource_to_text(block: Any) -> str:
    """Convert an ACP embedded resource block to a text representation."""
    resource = getattr(block, "resource", None)
    if resource is None:
        return ""
    text = getattr(resource, "text", None)
    uri = getattr(resource, "uri", "embedded-resource")
    if text is not None:
        return f"[ACP embedded resource: {uri}]\n{text}"
    return f"[ACP embedded binary resource: {uri}]"
