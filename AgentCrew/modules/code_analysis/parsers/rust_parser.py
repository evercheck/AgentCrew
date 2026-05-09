"""
Rust language parser for code analysis.
"""

from typing import Any

from .base import BaseLanguageParser


class RustParser(BaseLanguageParser):
    """Parser for Rust source code."""

    @property
    def language_name(self) -> str:
        return "rust"

    def process_node(
        self, node, source_code: bytes, process_children_callback
    ) -> dict[str, Any] | None:
        result = self._create_base_result(node)

        if node.type in ["struct_item", "impl_item", "fn_item", "trait_item"]:
            for child in node.children:
                if child.type == "identifier":
                    result["name"] = self.extract_node_text(child, source_code)
                    return result
            return result

        elif node.type in ["static_item", "const_item", "let_declaration"]:
            return self._handle_variable_declaration(node, source_code, result)

        children = []
        for child in node.children:
            child_result = process_children_callback(child)
            if child_result and self._is_significant_node(child_result):
                children.append(child_result)

        if children:
            result["children"] = children

        return result

    def _handle_variable_declaration(
        self, node, source_code: bytes, result: dict[str, Any]
    ) -> dict[str, Any]:
        var_name = None
        var_type = None

        for child in node.children:
            if child.type == "identifier" and var_name is None:
                var_name = self.extract_node_text(child, source_code)
            elif child.type == "pattern":
                if child.children:
                    var_name = self.extract_node_text(child.children[0], source_code)
            elif child.type in [
                "type_identifier",
                "generic_type",
                "reference_type",
                "pointer_type",
                "array_type",
                "primitive_type",
            ]:
                var_type = self.extract_node_text(child, source_code)

        if var_name:
            result["type"] = "variable_declaration"
            if var_type:
                result["name"] = f"{var_name}: {var_type}"
            else:
                result["name"] = var_name

        return result
