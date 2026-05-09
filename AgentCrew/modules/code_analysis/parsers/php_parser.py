"""
PHP language parser for code analysis.
"""

from typing import Any

from .base import BaseLanguageParser


class PhpParser(BaseLanguageParser):
    """Parser for PHP source code."""

    @property
    def language_name(self) -> str:
        return "php"

    def process_node(
        self, node, source_code: bytes, process_children_callback
    ) -> dict[str, Any] | None:
        result = self._create_base_result(node)

        if node.type in [
            "class_declaration",
            "interface_declaration",
            "trait_declaration",
        ]:
            for child in node.children:
                if child.type == "name":
                    result["name"] = self.extract_node_text(child, source_code)
                elif child.type == "declaration_list":
                    children = []
                    for body_child in child.children:
                        child_result = process_children_callback(body_child)
                        if child_result and self._is_significant_node(child_result):
                            children.append(child_result)
                    if children:
                        result["children"] = children
            return result

        elif node.type in ["method_declaration", "function_definition"]:
            for child in node.children:
                if child.type == "name":
                    result["name"] = self.extract_node_text(child, source_code)
                    return result
            return result

        elif node.type == "property_declaration":
            return self._handle_property_declaration(node, source_code, result)

        elif node.type == "const_declaration":
            return self._handle_const_declaration(node, source_code, result)

        children = []
        for child in node.children:
            child_result = process_children_callback(child)
            if child_result and self._is_significant_node(child_result):
                children.append(child_result)

        if children:
            result["children"] = children

        return result

    def _handle_property_declaration(
        self, node, source_code: bytes, result: dict[str, Any]
    ) -> dict[str, Any]:
        prop_name = None
        prop_type = None

        for child in node.children:
            if child.type in [
                "primitive_type",
                "named_type",
                "optional_type",
                "union_type",
            ]:
                prop_type = self.extract_node_text(child, source_code)
            elif child.type == "property_element":
                for subchild in child.children:
                    if subchild.type == "variable_name":
                        prop_name = self.extract_node_text(subchild, source_code)

        if prop_name:
            result["type"] = "property_declaration"
            if prop_type:
                result["name"] = f"{prop_type} {prop_name}"
            else:
                result["name"] = prop_name

        return result

    def _handle_const_declaration(
        self, node, source_code: bytes, result: dict[str, Any]
    ) -> dict[str, Any]:
        const_name = None

        for child in node.children:
            if child.type == "const_element":
                for subchild in child.children:
                    if subchild.type == "name":
                        const_name = self.extract_node_text(subchild, source_code)

        if const_name:
            result["type"] = "const_declaration"
            result["name"] = const_name

        return result
