# pylint: disable=duplicate-code
"""Cross-armory search screen for the TUI."""

from __future__ import annotations

import subprocess  # nosec B404
import sys
from typing import ClassVar

from harness.armory.search import CrossArmoryIndex, SearchResult

from interfaces.terminal import Theme, current_palette
from interfaces.tui.cell_text import cell_width as _cell_width
from interfaces.tui.cell_text import pad_cell_right as _pad_to_cell_width
from interfaces.tui.display_text import label_value_line, menu_label_value
from interfaces.tui.shortcut_hints import ShortcutHint, shortcut_hint_line
from interfaces.tui.slash_completion import changed_highlight_indices
from interfaces.tui.startup_discovery import discover_available_armories

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


_SEARCH_SELECTED_PREFIX = "→ "
_SEARCH_UNSELECTED_PREFIX = "  "
_SEARCH_DESCRIPTION_GAP = 4
_SEARCH_TITLE_HINTS = shortcut_hint_line(
    (
        ShortcutHint("Filter", "type"),
        ShortcutHint("Open", "o"),
        ShortcutHint("Select", "enter"),
        ShortcutHint("Close", "esc"),
    )
)


def _result_armory_name_width(results: list[SearchResult]) -> int:
    return max((_cell_width(result.armory_name) for result in results), default=0)


def _result_source_rel_width(results: list[SearchResult]) -> int:
    return max((_cell_width(result.source_rel.strip()) for result in results), default=0)


def _padded_label_value(label: str, value: str, *, value_width: int) -> str:
    rendered = label_value_line(label, value)
    value_text = value.strip()
    if not value_text:
        return rendered
    label_width = _cell_width(label.strip().upper())
    column_width = label_width + 1 + max(value_width, _cell_width(value_text))
    return _pad_to_cell_width(rendered, column_width)


def _empty_result_parts(query: str) -> list[str]:
    parts = [menu_label_value("state", "no matches")]
    if query.strip():
        parts.append(menu_label_value("filter", query))
    return parts


def _format_empty_result(query: str) -> str:
    return "  ".join(_empty_result_parts(query))


def _search_title_text() -> str:
    return f"Search  {menu_label_value('scope', 'armories')}  {_SEARCH_TITLE_HINTS}"


def _format_result(
    result: SearchResult,
    *,
    selected: bool = False,
    armory_width: int = 0,
    source_width: int = 0,
) -> str:
    preview = result.chunk_text.replace("\n", " ").strip()
    if len(preview) > 80:
        preview = preview[:77] + "..."
    score_pct = f"{result.score:.0%}"
    prefix = _SEARCH_SELECTED_PREFIX if selected else _SEARCH_UNSELECTED_PREFIX
    armory_name = _pad_to_cell_width(
        result.armory_name,
        max(armory_width, _cell_width(result.armory_name)),
    )
    source = _padded_label_value("source", result.source_rel, value_width=source_width)
    metadata = f"{source}  {label_value_line('score', score_pct)}"
    return f"{prefix}{armory_name}{' ' * _SEARCH_DESCRIPTION_GAP}{metadata}\n    {preview}"


class SearchScreen(ModalScreen[SearchResult | None]):
    BINDINGS: ClassVar[list[Binding]] = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "select", "Select"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._results: list[SearchResult] = []
        self._highlighted_result_index: int | None = None
        self._query = ""
        self._index = CrossArmoryIndex()
        self._built = False
        self.CSS = _search_screen_css(current_palette())  # ty:ignore[invalid-attribute-access]

    def compose(self) -> ComposeResult:
        with Vertical(id="search-dialog"):
            yield Static(_search_title_text(), id="search-title")
            yield Input(placeholder="FILTER armories", id="search-input")
            yield OptionList(id="search-results")
            yield Static("", id="search-preview")

    def on_mount(self) -> None:
        search_input = self.query_one("#search-input", Input)
        search_input.focus()
        self.run_worker(self._build_index_worker, thread=True)

    def _build_index_worker(self) -> None:
        armories = discover_available_armories()
        index = CrossArmoryIndex()
        if armories:
            index.build(armories)
        self.app.call_from_thread(self._finish_index_build, index)

    def _finish_index_build(self, index: CrossArmoryIndex) -> None:
        self._index = index
        self._built = True
        if self._query:
            self._run_search(self._query)

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

    def on_option_list_option_highlighted(
        self,
        event: OptionList.OptionHighlighted,
    ) -> None:
        if event.option_list.id != "search-results":
            return
        previous = self._highlighted_result_index
        self._highlighted_result_index = event.option_index
        self._refresh_result_selection(previous, event.option_index)
        self._update_preview()

    def _run_search(self, query: str) -> None:
        self._query = query
        if not self._built:
            self._update_indexing_result(query)
            return
        self._results = self._index.search(query, limit=20)
        results_list = self.query_one("#search-results", OptionList)
        if not self._results:
            results_list.clear_options()
            results_list.add_option(_format_empty_result(query))
            self._highlighted_result_index = None
            results_list.highlighted = None
            self._update_empty_preview(query)
            return
        armory_width = _result_armory_name_width(self._results)
        source_width = _result_source_rel_width(self._results)
        formatted = [
            _format_result(
                result,
                selected=index == 0,
                armory_width=armory_width,
                source_width=source_width,
            )
            for index, result in enumerate(self._results)
        ]
        results_list.clear_options()
        for f in formatted:
            results_list.add_option(f)
        self._highlighted_result_index = 0
        results_list.highlighted = 0
        self._update_preview()

    def _update_indexing_result(self, query: str) -> None:
        results_list = self.query_one("#search-results", OptionList)
        results_list.clear_options()
        parts = [menu_label_value("state", "indexing")]
        if query.strip():
            parts.append(menu_label_value("filter", query))
        results_list.add_option("  ".join(parts))
        self._highlighted_result_index = None
        results_list.highlighted = None
        preview = self.query_one("#search-preview", Static)
        preview.update("\n".join(parts))

    def _update_empty_preview(self, query: str) -> None:
        preview = self.query_one("#search-preview", Static)
        preview.update("\n".join(_empty_result_parts(query)))

    def _refresh_result_selection(self, previous: int | None, highlighted: int) -> None:
        results_list = self.query_one("#search-results", OptionList)
        armory_width = _result_armory_name_width(self._results)
        source_width = _result_source_rel_width(self._results)
        for index in changed_highlight_indices(previous, highlighted, len(self._results)):
            results_list.replace_option_prompt_at_index(
                index,
                _format_result(
                    self._results[index],
                    selected=index == highlighted,
                    armory_width=armory_width,
                    source_width=source_width,
                ),
            )

    def _update_preview(self) -> None:
        results_list = self.query_one("#search-results", OptionList)
        preview = self.query_one("#search-preview", Static)
        idx = results_list.highlighted
        if idx is None or idx >= len(self._results):
            preview.update("")
            return
        result = self._results[idx]
        lines = [
            label_value_line("source", result.source_rel),
            label_value_line("armory", result.armory_name),
            "",
            result.chunk_text[:300],
        ]
        if result.source_path.suffix.lower() == ".pdf":
            lines.append("")
            lines.append(label_value_line("open", "o"))
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
