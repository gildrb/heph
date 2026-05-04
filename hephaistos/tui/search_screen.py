# pylint: disable=duplicate-code
# pyright: reportMissingImports=false, reportUnknownArgumentType=false, reportUnknownMemberType=false
# pyright: reportUntypedBaseClass=false, reportGeneralTypeIssues=false
# pyright: reportUnknownVariableType=false, reportInvalidTypeArguments=false
# pyright: reportOptionalCall=false, reportUnknownParameterType=false
"""Cross-armory search screen for the TUI."""

from __future__ import annotations

import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import ClassVar

from hephaistos.search_index import CrossArmoryIndex, SearchResult, load_known_armories
from hephaistos.terminal import ThemePalette, current_palette

try:
    from textual import events
    from textual.app import ComposeResult
    from textual.binding import Binding
    from textual.containers import Vertical
    from textual.screen import ModalScreen
    from textual.widgets import Input, OptionList, Static
except ImportError:
    events = None  # type: ignore[assignment]
    ComposeResult = None  # type: ignore[assignment,misc]
    Binding = None  # type: ignore[assignment,misc]
    Vertical = None  # type: ignore[assignment,misc]
    ModalScreen = object  # type: ignore[assignment, misc]
    Input = None  # type: ignore[assignment]
    OptionList = None  # type: ignore[assignment]
    Static = None  # type: ignore[assignment]


def _open_file_at_system(path: Path) -> None:
    """Open a file with the system default application."""
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])  # nosec B603
    elif sys.platform == "linux":
        subprocess.Popen(["xdg-open", str(path)])  # nosec B603
    else:
        subprocess.Popen(["start", str(path)])  # nosec B603


def _search_screen_css(p: ThemePalette) -> str:
    """Generate CSS from the active theme palette."""
    bg = "transparent" if p.is_transparent else p.background
    border_color = p.stone
    text_color = p.text
    dim_color = p.dim

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
    """Format a search result for display in the option list."""
    preview = result.chunk_text.replace("\n", " ").strip()
    if len(preview) > 80:
        preview = preview[:77] + "..."
    score_pct = f"{result.score:.0%}"
    return f"  [{result.armory_name}]  {result.source_rel}  ({score_pct})\n    {preview}"


class SearchScreen(ModalScreen[SearchResult | None]):  # type: ignore[misc]
    """Modal search screen that searches across all indexed armories."""

    BINDINGS: ClassVar[list[Binding]] = [  # type: ignore[assignment]
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "select", "Select"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._results: list[SearchResult] = []
        self._index = CrossArmoryIndex()
        self._built = False
        self.CSS = _search_screen_css(current_palette())

    def compose(self) -> ComposeResult:  # type: ignore[override,reportInvalidTypeForm]
        p = current_palette()
        title = f"[bold {p.ember}]\u2301 Search[/bold {p.ember}]"
        with Vertical(id="search-dialog"):
            yield Static(title, id="search-title", markup=True)
            yield Input(placeholder="Search across armories...", id="search-input")
            yield OptionList(id="search-results")
            yield Static("", id="search-preview")

    def on_mount(self) -> None:
        search_input = self.query_one("#search-input", Input)
        search_input.focus()
        armories = load_known_armories()
        if armories:
            self._index.build(armories)
            self._built = True

    def on_key(self, event: events.Key) -> None:  # type: ignore[override]
        if event.key == "o":
            self._open_selected_source()
            event.prevent_default()
            event.stop()
            return

    def on_input_changed(self, event: Input.Changed) -> None:  # type: ignore[override]
        if event.input.id == "search-input":
            self._run_search(event.value)

    def on_option_list_option_selected(  # type: ignore[override]
        self,
        event: OptionList.OptionSelected,  # type: ignore[reportInvalidTypeForm]
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
            f"[bold {p.ember}]Source:[/bold {p.ember}] {result.source_rel}",
            f"[bold {p.ember}]Armory:[/bold {p.ember}] {result.armory_name}",
            "",
            result.chunk_text[:300],
        ]
        if result.source_path.suffix.lower() == ".pdf":
            lines.append("")
            lines.append(f"[bold {p.ember}]Press 'o' to open PDF[/bold {p.ember}]")
        preview.update("\n".join(lines))

    def _open_selected_source(self) -> None:
        results_list = self.query_one("#search-results", OptionList)
        idx = results_list.highlighted
        if idx is None or idx >= len(self._results):
            return
        result = self._results[idx]
        source_path = result.source_path
        if source_path.exists():
            _open_file_at_system(source_path)

    def action_select(self) -> None:
        results_list = self.query_one("#search-results", OptionList)
        idx = results_list.highlighted
        if idx is not None and idx < len(self._results):
            self.dismiss(self._results[idx])
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)
