# pylint: disable=duplicate-code
"""Cross-armory search screen for the TUI."""

from __future__ import annotations

import subprocess  # nosec B404
import sys
from typing import ClassVar

from hephaistos.armory.search import CrossArmoryIndex, SearchResult
from hephaistos.shell.startup_discovery import discover_available_armories
from hephaistos.terminal import Theme, current_palette

try:
    from textual import events
    from textual.app import ComposeResult
    from textual.binding import Binding
    from textual.containers import Vertical
    from textual.screen import ModalScreen
    from textual.widgets import Input, OptionList, Static
except ImportError:
    events = None  # ty:ignore[invalid-assignment]
    ComposeResult = None  # ty:ignore[invalid-assignment]
    Binding = None  # ty:ignore[invalid-assignment]
    Vertical = None  # ty:ignore[invalid-assignment]
    ModalScreen = object  # ty:ignore[invalid-assignment]
    Input = None  # ty:ignore[invalid-assignment]
    OptionList = None  # ty:ignore[invalid-assignment]
    Static = None  # ty:ignore[invalid-assignment]


def _search_screen_css(p: Theme) -> str:
    bg = p.bg_surface
    border_color = p.bg_app
    text_color = p.text_primary
    dim_color = p.text_muted

    return f"""
    SearchScreen {{
        align: center middle;
    }}
    #search-dialog {{
        width: 80;
        height: 24;
        border: round {border_color};
        background: {bg};
        padding: 1 2;
        color: {text_color};
    }}
    #search-title {{
        text-style: bold;
        color: {dim_color};
        width: 100%;
        margin-bottom: 0;
    }}
    #search-input {{
        width: 100%;
        margin-bottom: 1;
    }}
    #search-results {{
        width: 100%;
        height: 1fr;
    }}
    #search-preview {{
        width: 100%;
        height: 8;
        border-top: solid {border_color};
        padding-top: 1;
        color: {dim_color};
    }}
    """


def _format_result(result: SearchResult) -> str:
    preview = result.chunk_text.replace("\n", " ").strip()
    if len(preview) > 80:
        preview = preview[:77] + "..."
    score_pct = f"{result.score:.0%}"
    return f"  [{result.armory_name}]  {result.source_rel}  ({score_pct})\n    {preview}"


class SearchScreen(ModalScreen[SearchResult | None]):
    BINDINGS: ClassVar[list[Binding]] = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "select", "Select"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._results: list[SearchResult] = []
        self._index = CrossArmoryIndex()
        self._built = False
        self.CSS = _search_screen_css(current_palette())  # ty:ignore[invalid-attribute-access]

    def compose(self) -> ComposeResult:
        p = current_palette()
        title = f"[bold {p.text_primary}]\u2301 Search[/bold {p.text_primary}]"
        with Vertical(id="search-dialog"):
            yield Static(title, id="search-title", markup=True)
            yield Input(placeholder="Search across armories...", id="search-input")
            yield OptionList(id="search-results")
            yield Static("", id="search-preview")

    def on_mount(self) -> None:
        search_input = self.query_one("#search-input", Input)
        search_input.focus()
        armories = discover_available_armories()
        if armories:
            self._index.build(armories)
            self._built = True

    def on_key(self, event: events.Key) -> None:
        if event.key == "o":
            self._open_selected_source()
            event.prevent_default()
            event.stop()
            return

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-input":
            self._run_search(event.value)

    def on_option_list_option_selected(
        self,
        event: OptionList.OptionSelected,
    ) -> None:
        if event.option_list.id == "search-results":
            self.action_select()

    def _run_search(self, query: str) -> None:
        if not self._built:
            return
        self._results = self._index.search(query, limit=20)
        results_list = self.query_one("#search-results", OptionList)
        if not self._results:
            results_list.clear_options()
            return
        formatted = [_format_result(r) for r in self._results]
        results_list.clear_options()
        for f in formatted:
            results_list.add_option(f)
        results_list.highlighted = 0
        self._update_preview()

    def _update_preview(self) -> None:
        p = current_palette()
        results_list = self.query_one("#search-results", OptionList)
        preview = self.query_one("#search-preview", Static)
        idx = results_list.highlighted
        if idx is None or idx >= len(self._results):
            preview.update("")
            return
        result = self._results[idx]
        lines = [
            f"[bold {p.text_primary}]Source:[/bold {p.text_primary}] {result.source_rel}",
            f"[bold {p.text_primary}]Armory:[/bold {p.text_primary}] {result.armory_name}",
            "",
            result.chunk_text[:300],
        ]
        if result.source_path.suffix.lower() == ".pdf":
            lines.append("")
            lines.append(f"[bold {p.text_primary}]Press 'o' to open PDF[/bold {p.text_primary}]")
        preview.update("\n".join(lines))

    def _open_selected_source(self) -> None:
        results_list = self.query_one("#search-results", OptionList)
        idx = results_list.highlighted
        if idx is None or idx >= len(self._results):
            return
        result = self._results[idx]
        source_path = result.source_path
        if source_path.exists():
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            if sys.platform not in {"darwin", "linux"}:
                opener = "start"
            subprocess.Popen([opener, str(source_path)])  # nosec B603 B607

    def action_select(self) -> None:
        results_list = self.query_one("#search-results", OptionList)
        idx = results_list.highlighted
        if idx is not None and idx < len(self._results):
            self.dismiss(self._results[idx])
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)
