"""Visual mode viewer for raw message content."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from rich.console import Console
from rich.text import Text

from .viewer_ui import VisualModeUI
from .viewer_input_handler import VisualModeInputHandler
from ..constants import RICH_STYLE_YELLOW

if TYPE_CHECKING:
    pass


class VisualModeViewer:
    """Main class for visual mode viewing of raw message content."""

    def __init__(
        self,
        console: Console,
        on_copy: Callable[[str], None] | None = None,
    ):
        self._console = console
        self._on_copy = on_copy
        self._ui = VisualModeUI(console)
        self._input_handler = VisualModeInputHandler(self._ui, on_copy=on_copy)

    def set_messages(self, messages: list[dict[str, Any]]):
        self._ui.set_messages(messages)

    def show(self):
        if not self._ui._messages:
            self._console.print(
                Text("No messages to display in visual mode.", style=RICH_STYLE_YELLOW)
            )
            return

        self._input_handler.run()
