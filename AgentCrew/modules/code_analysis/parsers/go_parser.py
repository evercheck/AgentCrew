"""
Go language parser for code analysis.
"""

from typing import Any

from .base import BaseLanguageParser


class GoParser(BaseLanguageParser):
    """Parser for Go source code."""

    @property
    def language_name(self) -> str:
        return "go"

    def process_node(
        self, node, source_code: bytes, process_children_callback
    ) -> dict[str, Any] | None:
        result = self._create_base_result(node)

        if node.type == "type_declaration":
            return self._handle_type_declaration(
                node, source_code, result, process_children_callback
            )

        elif node.type in ["function_declaration", "method_declaration"]:
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

        elif node.type == "interface_declaration":
            for child in node.children:
                if child.type == "identifier":
                    result["name"] = self.extract_node_text(child, source_code)
                    return result
            return result

        elif node.type in ["var_declaration", "const_declaration"]:
            return self._handle_var_declaration(node, source_code, result)

        elif node.type == "field_declaration":
            return self._handle_field_declaration(node, source_code, result)

        children = []
        for child in node.children:
            child_result = process_children_callback(child)
            if child_result and self._is_significant_node(child_result):
                children.append(child_result)

        if children:
            result["children"] = children

        return result

    def _handle_type_declaration(
        self,
        node,
        source_code: bytes,
        result: dict[str, Any],
        process_children_callback,
    ) -> dict[str, Any]:
        for child in node.children:
            if child.type == "type_spec":
                for spec_child in child.children:
                    if spec_child.type == "type_identifier":
                        result["name"] = self.extract_node_text(spec_child, source_code)
                        result["type"] = "type_declaration"
                    elif spec_child.type == "struct_type":
                        result["type"] = "struct_declaration"
                        for struct_child in spec_child.children:
                            if struct_child.type == "field_declaration_list":
                                children = []
                                for field in struct_child.children:
                                    field_result = process_children_callback(field)
                                    if field_result and self._is_significant_node(
                                        field_result
                                    ):
                                        children.append(field_result)
                                if children:
                                    result["children"] = children
                    elif spec_child.type == "interface_type":
                        result["type"] = "interface_declaration"

        return result

    def _handle_var_declaration(
        self, node, source_code: bytes, result: dict[str, Any]
    ) -> dict[str, Any]:
        var_name = None
        var_type = None

        for child in node.children:
            if child.type in ["var_spec", "const_spec"]:
                for subchild in child.children:
                    if subchild.type == "identifier" and var_name is None:
                        var_name = self.extract_node_text(subchild, source_code)
                    elif subchild.type in [
                        "type_identifier",
                        "pointer_type",
                        "array_type",
                        "slice_type",
                        "map_type",
                        "channel_type",
                        "qualified_type",
                    ]:
                        var_type = self.extract_node_text(subchild, source_code)

        if var_name:
            result["type"] = "variable_declaration"
            if var_type:
                result["name"] = f"{var_name} {var_type}"
            else:
                result["name"] = var_name

        return result

    def _handle_field_declaration(
        self, node, source_code: bytes, result: dict[str, Any]
    ) -> dict[str, Any]:
        field_name = None
        field_type = None

        for child in node.children:
            if child.type == "field_identifier":
                field_name = self.extract_node_text(child, source_code)
            elif child.type in [
                "type_identifier",
                "pointer_type",
                "array_type",
                "slice_type",
                "map_type",
                "channel_type",
                "qualified_type",
                "struct_type",
                "interface_type",
            ]:
                field_type = self.extract_node_text(child, source_code)

        if field_name:
            result["type"] = "field_declaration"
            if field_type:
                result["name"] = f"{field_name} {field_type}"
            else:
                result["name"] = field_name

        return result
