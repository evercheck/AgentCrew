"""
JavaScript/TypeScript language parser for code analysis.
"""

from typing import Any

from .base import BaseLanguageParser


class JavaScriptParser(BaseLanguageParser):
    """Parser for JavaScript and TypeScript source code."""

    @property
    def language_name(self) -> str:
        return "javascript"

    def process_node(
        self, node, source_code: bytes, process_children_callback
    ) -> dict[str, Any] | None:
        result = self._create_base_result(node)

        if node.type in [
            "class_declaration",
            "method_definition",
            "class",
            "method_declaration",
            "function_declaration",
            "interface_declaration",
            "export_statement",
            "arrow_function",
            "lexical_declaration",
        ]:
            if node.type == "export_statement":
                return self._handle_export_statement(
                    node, source_code, process_children_callback
                )
            elif node.type == "arrow_function":
                return self._handle_arrow_function(
                    node, source_code, result, process_children_callback
                )
            elif node.type == "lexical_declaration":
                return self._handle_lexical_declaration(
                    node, source_code, result, process_children_callback
                )
            else:
                self._handle_regular_declaration(node, source_code, result)

        elif node.type in ["property_declaration", "public_field_definition"]:
            return self._handle_property_declaration(node, source_code, result)

        elif node.type in ["variable_statement", "variable_declaration"]:
            return self._handle_variable_statement(
                node, source_code, result, process_children_callback
            )

        children = []
        for child in node.children:
            child_result = process_children_callback(child)
            if child_result and self._is_significant_node(child_result):
                children.append(child_result)

        if children:
            result["children"] = children

        return result

    def _handle_export_statement(
        self, node, source_code: bytes, process_children_callback
    ) -> dict[str, Any] | None:
        for child in node.children:
            if child.type in [
                "class_declaration",
                "function_declaration",
                "interface_declaration",
                "variable_statement",
                "lexical_declaration",
                "method_definition",
            ]:
                exported_result = process_children_callback(child)
                if exported_result:
                    exported_result["exported"] = True
                    return exported_result
        return None

    def _handle_arrow_function(
        self,
        node,
        source_code: bytes,
        result: dict[str, Any],
        process_children_callback,
    ) -> dict[str, Any]:
        parent = node.parent
        if parent and parent.type == "variable_declarator":
            for sibling in parent.children:
                if sibling.type == "identifier":
                    result["type"] = "arrow_function"
                    result["name"] = self.extract_node_text(sibling, source_code)

        for child in node.children:
            if child.type == "formal_parameters":
                params = self._extract_parameters(child, source_code)
                if params:
                    result["parameters"] = params

        return result

    def _handle_lexical_declaration(
        self,
        node,
        source_code: bytes,
        result: dict[str, Any],
        process_children_callback,
    ) -> dict[str, Any]:
        for child in node.children:
            if child.type == "variable_declarator":
                var_name = None
                has_arrow_function = False

                for declarator_child in child.children:
                    if declarator_child.type == "identifier":
                        var_name = self.extract_node_text(declarator_child, source_code)
                    elif declarator_child.type == "arrow_function":
                        has_arrow_function = True

                if var_name and has_arrow_function:
                    result["type"] = "arrow_function"
                    result["name"] = var_name
                    for declarator_child in child.children:
                        if declarator_child.type == "arrow_function":
                            arrow_result = process_children_callback(declarator_child)
                            if arrow_result and "parameters" in arrow_result:
                                result["parameters"] = arrow_result["parameters"]
                else:
                    result["type"] = "variable_declaration"
                    result["name"] = var_name
                    result["first_line"] = (
                        self.extract_node_text(node, source_code)
                        .split("\n")[0]
                        .strip("{")
                    )

        return result

    def _handle_regular_declaration(
        self, node, source_code: bytes, result: dict[str, Any]
    ) -> None:
        for child in node.children:
            if child.type in ["identifier", "type_identifier", "property_identifier"]:
                result["name"] = self.extract_node_text(child, source_code)
            elif child.type == "formal_parameters" and node.type in [
                "function_declaration",
                "method_declaration",
                "method_definition",
            ]:
                params = self._extract_parameters_with_types(child, source_code)
                if params:
                    result["parameters"] = params

    def _handle_variable_statement(
        self,
        node,
        source_code: bytes,
        result: dict[str, Any],
        process_children_callback,
    ) -> dict[str, Any]:
        for child in node.children:
            if child.type == "variable_declaration_list":
                for declarator in child.children:
                    if declarator.type == "variable_declarator":
                        var_name = None
                        has_arrow_function = False

                        for declarator_child in declarator.children:
                            if declarator_child.type == "identifier":
                                var_name = self.extract_node_text(
                                    declarator_child, source_code
                                )
                            elif declarator_child.type == "arrow_function":
                                has_arrow_function = True

                        if var_name:
                            if has_arrow_function:
                                result["type"] = "arrow_function"
                                result["name"] = var_name
                                for declarator_child in declarator.children:
                                    if declarator_child.type == "arrow_function":
                                        arrow_result = process_children_callback(
                                            declarator_child
                                        )
                                        if (
                                            arrow_result
                                            and "parameters" in arrow_result
                                        ):
                                            result["parameters"] = arrow_result[
                                                "parameters"
                                            ]
                            else:
                                result["type"] = "variable_declaration"
                                result["name"] = var_name
                            return result

            elif child.type == "identifier":
                result["type"] = "variable_declaration"
                result["name"] = self.extract_node_text(child, source_code)
                return result

        return result

    def _handle_property_declaration(
        self, node, source_code: bytes, result: dict[str, Any]
    ) -> dict[str, Any]:
        prop_name = None
        prop_type = None

        for child in node.children:
            if child.type in ["property_identifier", "identifier"]:
                prop_name = self.extract_node_text(child, source_code)
            elif child.type == "type_annotation":
                for type_child in child.children:
                    if type_child.type != ":":
                        prop_type = self.extract_node_text(type_child, source_code)

        if prop_name:
            result["type"] = "property_declaration"
            if prop_type:
                result["name"] = f"{prop_name}: {prop_type}"
            else:
                result["name"] = prop_name

        return result

    def _extract_parameters(self, params_node, source_code: bytes) -> list:
        params = []
        for param in params_node.children:
            if param.type in ["required_parameter", "optional_parameter", "identifier"]:
                param_text = self.extract_node_text(param, source_code)
                params.append(param_text)
        return params

    def _extract_parameters_with_types(self, params_node, source_code: bytes) -> list:
        params = []
        for param in params_node.children:
            if param.type in ["required_parameter", "optional_parameter", "identifier"]:
                param_name = None
                param_type = None

                if param.type == "identifier":
                    param_name = self.extract_node_text(param, source_code)
                    params.append(param_name)
                    continue

                for param_child in param.children:
                    if param_child.type in ["identifier", "object_pattern"]:
                        param_name = self.extract_node_text(param_child, source_code)
                    elif param_child.type == "type_annotation":
                        for type_child in param_child.children:
                            if type_child.type != ":":
                                param_type = self.extract_node_text(
                                    type_child, source_code
                                )

                if param_name:
                    if param_type:
                        params.append(f"{param_name}: {param_type}")
                    else:
                        params.append(param_name)

        return params
