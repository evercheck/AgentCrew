"""
C++ language parser for code analysis.
"""

from typing import Any

from .base import BaseLanguageParser


class CppParser(BaseLanguageParser):
    """Parser for C++ source code."""

    @property
    def language_name(self) -> str:
        return "cpp"

    def process_node(
        self, node, source_code: bytes, process_children_callback
    ) -> dict[str, Any] | None:
        result = self._create_base_result(node)

        if node.type in ["class_specifier", "struct_specifier"]:
            for child in node.children:
                if child.type in ["identifier", "type_identifier"]:
                    result["name"] = self.extract_node_text(child, source_code)
                elif child.type == "field_declaration_list":
                    children = []
                    for body_child in child.children:
                        child_result = process_children_callback(body_child)
                        if child_result and self._is_significant_node(child_result):
                            children.append(child_result)
                    if children:
                        result["children"] = children
            return result

        elif node.type == "function_definition":
            for child in node.children:
                if child.type in ["identifier", "field_identifier"]:
                    result["name"] = self.extract_node_text(child, source_code)
                    return result
                elif child.type == "function_declarator":
                    for subchild in child.children:
                        if subchild.type in ["identifier", "field_identifier"]:
                            result["name"] = self.extract_node_text(
                                subchild, source_code
                            )
                            return result
            return result

        elif node.type == "field_declaration":
            return self._handle_field_declaration(node, source_code, result)

        elif node.type in ["declaration", "variable_declaration"]:
            return self._handle_declaration(node, source_code, result)

        children = []
        for child in node.children:
            child_result = process_children_callback(child)
            if child_result and self._is_significant_node(child_result):
                children.append(child_result)

        if children:
            result["children"] = children

        return result

    def _handle_field_declaration(
        self, node, source_code: bytes, result: dict[str, Any]
    ) -> dict[str, Any]:
        field_name = None
        field_type = None

        for child in node.children:
            if child.type in [
                "primitive_type",
                "type_identifier",
                "qualified_identifier",
                "template_type",
            ]:
                field_type = self.extract_node_text(child, source_code)
            elif child.type == "field_identifier":
                field_name = self.extract_node_text(child, source_code)

        if field_name:
            result["type"] = "field_declaration"
            if field_type:
                result["name"] = f"{field_type} {field_name}"
            else:
                result["name"] = field_name

        return result

    def _handle_declaration(
        self, node, source_code: bytes, result: dict[str, Any]
    ) -> dict[str, Any]:
        var_name = None
        var_type = None

        for child in node.children:
            if child.type in [
                "primitive_type",
                "type_identifier",
                "qualified_identifier",
                "template_type",
            ]:
                var_type = self.extract_node_text(child, source_code)
            elif child.type in ["init_declarator", "declarator"]:
                for subchild in child.children:
                    if subchild.type == "identifier":
                        var_name = self.extract_node_text(subchild, source_code)
                        break
                    elif subchild.type == "pointer_declarator":
                        for ptr_child in subchild.children:
                            if ptr_child.type == "identifier":
                                var_name = self.extract_node_text(
                                    ptr_child, source_code
                                )
                                break

        if var_name:
            result["type"] = "variable_declaration"
            if var_type:
                result["name"] = f"{var_type} {var_name}"
            else:
                result["name"] = var_name

        return result
