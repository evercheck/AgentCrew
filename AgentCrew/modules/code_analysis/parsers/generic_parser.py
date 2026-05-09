"""
Generic language parser for code analysis (fallback for unsupported languages).
"""

from typing import Any

from .base import BaseLanguageParser


class GenericParser(BaseLanguageParser):
    """Generic parser for languages without specific implementation."""

    def __init__(self, language: str = "unknown"):
        self._language = language

    @property
    def language_name(self) -> str:
        return self._language

    def process_node(
        self, node, source_code: bytes, process_children_callback
    ) -> dict[str, Any] | None:
        result = self._create_base_result(node)

        if node.type in [
            "type_declaration",
            "function_declaration",
            "method_declaration",
            "interface_declaration",
        ]:
            for child in node.children:
                if child.type in ["identifier", "field_identifier"]:
                    result["name"] = self.extract_node_text(child, source_code)
                    result["first_line"] = (
                        self.extract_node_text(node, source_code)
                        .split("\n")[0]
                        .strip("{")
                    )
                    return result
            return result

        elif node.type in ["var_declaration", "const_declaration"]:
            for child in node.children:
                if child.type in ["var_spec", "const_spec"]:
                    for subchild in child.children:
                        if subchild.type == "identifier":
                            result["type"] = "variable_declaration"
                            result["name"] = self.extract_node_text(
                                subchild, source_code
                            )
                            return result
            return result

        children = []
        for child in node.children:
            child_result = process_children_callback(child)
            if child_result and self._is_significant_node(child_result):
                children.append(child_result)

        if children:
            result["children"] = children

        return result
