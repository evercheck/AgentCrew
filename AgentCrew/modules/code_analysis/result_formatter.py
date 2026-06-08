from typing import Any, Set

from .text_map_formatter import TextMapFormatter
from .file_tree_formatter import FileTreeFormatter


class ResultFormatter:
    """Formats code analysis results into structured text reports."""

    def __init__(
        self,
        text_map_formatter: TextMapFormatter,
        file_tree_formatter: FileTreeFormatter,
        class_types: Set[str],
        function_types: Set[str],
        max_files_to_analyze: int,
    ):
        self._text_map_formatter = text_map_formatter
        self._file_tree_formatter = file_tree_formatter
        self._class_types = class_types
        self._function_types = function_types
        self._max_files_to_analyze = max_files_to_analyze

    @staticmethod
    def _count_nodes(structure: dict[str, Any], node_types: Set[str]) -> int:
        """Recursively count nodes of specific types in the tree structure."""
        count = 0

        if structure.get("type") in node_types:
            count += 1

        for child in structure.get("children", []):
            count += ResultFormatter._count_nodes(child, node_types)

        return count

    def format_analysis_results(
        self,
        analysis_results: list[dict[str, Any]],
        analyzed_files: list[str],
        errors: list[dict[str, str]],
        non_analyzed_files: list[str] = [],
        total_supported_files: int = 0,
    ) -> str:
        """Format the analysis results into a clear text format.

        Args:
            analysis_results: list of analysis results for each file
            analyzed_files: list of files that were analyzed
            errors: list of errors encountered during analysis
            non_analyzed_files: list of files that were skipped due to file limit
            total_supported_files: Total number of supported files in the repository
        """

        total_files = len(analyzed_files)
        classes = sum(
            self._count_nodes(f["structure"], self._class_types)
            for f in analysis_results
        )
        functions = sum(
            self._count_nodes(f["structure"], self._function_types)
            for f in analysis_results
        )
        decorated_functions = sum(
            self._count_nodes(f["structure"], {"decorated_definition"})
            for f in analysis_results
        )
        error_count = len(errors)
        non_analyzed_count = len(non_analyzed_files)

        sections = []

        sections.append(
            f"files: {total_files} classes: {classes} funcs: {functions} decorated: {decorated_functions} errors: {error_count}"
        )
        if non_analyzed_count > 0:
            sections.append(
                f"skipped: {non_analyzed_count} supported: {total_supported_files}"
            )

        if errors:
            sections.append("errors:")
            for error in errors:
                error_first_line = error["error"].split("\n")[0]
                sections.append(f"{error['path']}: {error_first_line}")

        sections.append(self._text_map_formatter.generate_text_map(analysis_results))

        if non_analyzed_files:
            sections.append("skipped analyzed files:")
            max_non_analyzed_to_show = int(self._max_files_to_analyze / 2)
            non_analyzed_tree = self._file_tree_formatter.build_file_tree(
                sorted(non_analyzed_files)[:max_non_analyzed_to_show]
            )
            non_analyzed_tree_lines = self._file_tree_formatter.format_file_tree(
                non_analyzed_tree
            )
            sections.extend(non_analyzed_tree_lines)
            if len(non_analyzed_files) > max_non_analyzed_to_show:
                sections.append(
                    f"...and {len(non_analyzed_files) - max_non_analyzed_to_show} more files."
                )

        return "\n".join(sections)
