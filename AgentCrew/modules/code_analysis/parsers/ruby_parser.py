"""
Ruby language parser for code analysis.
"""

from typing import Any

from .base import BaseLanguageParser


class RubyParser(BaseLanguageParser):
    """Parser for Ruby source code."""

    @property
    def language_name(self) -> str:
        return "ruby"

    def process_node(
        self, node, source_code: bytes, process_children_callback
    ) -> dict[str, Any] | None:
        result = self._create_base_result(node)

        if node.type in ["class", "method", "singleton_method", "module"]:
            for child in node.children:
                if child.type == "identifier":
                    result["name"] = self.extract_node_text(child, source_code)
                    return result
            return result

        elif node.type in ["assignment", "global_variable"]:
            for child in node.children:
                if child.type in ["identifier", "global_variable"]:
                    result["type"] = "variable_declaration"
                    result["name"] = self.extract_node_text(child, source_code)
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
