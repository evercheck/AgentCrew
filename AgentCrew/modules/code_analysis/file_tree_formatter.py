from typing import Any


class FileTreeFormatter:
    """Builds and formats hierarchical file tree representations."""

    def build_file_tree(self, file_paths: list[str]) -> dict[str, Any]:
        """Build a hierarchical tree structure from flat file paths.

        Args:
            file_paths: list of relative file paths

        Returns:
            Nested dictionary representing the file tree
        """
        tree: dict[str, Any] = {}
        for path in sorted(file_paths):
            parts = path.replace("\\", "/").split("/")
            current = tree
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    current[part] = None
                else:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
        return tree

    def format_file_tree(self, tree: dict[str, Any], indent: str = "") -> list[str]:
        """Format a file tree dictionary into indented lines.

        Args:
            tree: Nested dictionary representing file tree
            indent: Current indentation string

        Returns:
            list of formatted lines
        """
        lines = []
        items = sorted(tree.keys())
        for name in items:
            subtree = tree[name]
            if subtree is None:
                lines.append(f"{indent}{name}")
            else:
                lines.append(f"{indent}{name}/")
                child_lines = self.format_file_tree(subtree, indent + "  ")
                lines.extend(child_lines)
        return lines
