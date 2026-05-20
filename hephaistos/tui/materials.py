from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, overload

from hephaistos.materials import material_display_name
from hephaistos.terminal import current_palette
from hephaistos.tui.textual_compat import (
    ClassableWidget as _ClassableWidget,
)
from hephaistos.tui.textual_compat import (
    Input,
    OptionList,
    RichLog,
    Static,
    sidebar_text,
)
from hephaistos.tui.textual_compat import (
    RichText as _RichText,
)
from hephaistos.tui.textual_compat import (
    WidgetT as _WidgetT,
)

if TYPE_CHECKING:
    from rich.text import Text
    from textual import events
    from textual.geometry import Size
    from textual.widget import Widget

    from hephaistos.chat.session import ChatSession

_MATERIALS_LIST_IDS = ("materials-list", "materials-list-right")
_MATERIALS_MIN_TWO_COLUMN_WIDTH = 72


class _MaterialsHost(Protocol):
    _materials_inline_active: bool
    _materials_filter: str
    _materials_entries: list[str]
    _materials_columns: tuple[list[str], list[str]]
    _materials_highlighted_index: int | None
    _materials_mode: str
    _sidebar_width_visible: bool
    session: ChatSession
    size: Size

    @property
    def focused(self) -> Widget | None: ...

    @overload
    def query_one(self, selector: str) -> _ClassableWidget: ...

    @overload
    def query_one(self, selector: str, expect_type: type[_WidgetT]) -> _WidgetT: ...

    def set_focus(self, widget: Widget | None) -> None: ...

    def _set_sidebar_visible(self, visible: bool) -> None: ...

    def _hide_completions(self) -> None: ...

    def _refresh_footer_hints(self) -> None: ...

    def _schedule_transcript_reflow(self) -> None: ...

    def _refresh_status(self) -> None: ...

    def _sync_busy_to_current_session(self) -> None: ...

    def _update_info_panel(self) -> None: ...

    def _open_materials_inline(self, value: str = "", *, mode: str = "toggle") -> None: ...

    def _close_materials_inline(self) -> None: ...

    def _refresh_materials_inline(self) -> None: ...

    def _materials_footer_text(self) -> str: ...

    def _update_materials_sidebar(self) -> None: ...

    def _format_material_option(self, file: str, *, selected: bool) -> str | Text: ...

    def _material_columns_for_entries(self) -> tuple[list[str], list[str]]: ...

    def _materials_should_use_two_columns(self) -> bool: ...

    def _materials_visible_rows(self) -> int: ...

    def _materials_local_index(
        self,
        list_id: str,
        global_index: int | None,
    ) -> int | None: ...

    def _materials_global_index(self, list_id: str, index: int) -> int | None: ...

    def _materials_list_for_index(self, index: int) -> OptionList: ...

    def _focus_materials_highlighted_list(self) -> None: ...

    def _refresh_materials_highlight_class(self) -> None: ...

    def _handle_materials_option_selected(self, list_id: str, index: int) -> None: ...

    def _handle_materials_option_highlighted(self, list_id: str, index: int) -> None: ...

    def _toggle_highlighted_material(self) -> None: ...

    def _move_material_highlight(self, offset: int) -> None: ...

    def _set_material_enabled(self, file: str, enabled: bool) -> None: ...

    def _handle_materials_key(self, event: events.Key) -> bool: ...


def _active_material_count(host: _MaterialsHost) -> int:
    return sum(
        1 for file in host.session.source_files if file not in host.session.disabled_source_files
    )


class TuiMaterialsMixin:
    def _open_materials_inline(
        self: _MaterialsHost,
        value: str = "",
        *,
        mode: str = "toggle",
    ) -> None:
        _, _, args = value.partition(" ")
        self._materials_filter = args.strip()
        self._materials_mode = mode
        self._materials_inline_active = True
        self.query_one("#transcript", RichLog).add_class("hidden-for-armory")
        self.query_one("#transcript-spacer", Static).add_class("hidden-for-armory")
        self.query_one("#materials-inline").add_class("active")
        self._set_sidebar_visible(False)
        composer = self.query_one("#composer", Input)
        composer.value = self._materials_filter
        composer.placeholder = "Filter materials..."
        self._hide_completions()
        self._refresh_materials_inline()
        self._refresh_footer_hints()
        material_list = self.query_one("#materials-list", OptionList)
        material_list.focus()
        self.set_focus(material_list)

    def _close_materials_inline(self: _MaterialsHost) -> None:
        self._materials_inline_active = False
        self._materials_filter = ""
        self._materials_mode = "toggle"
        self._materials_highlighted_index = None
        self.query_one("#transcript", RichLog).remove_class("hidden-for-armory")
        self.query_one("#transcript-spacer", Static).remove_class("hidden-for-armory")
        self.query_one("#materials-inline").remove_class("active")
        self._set_sidebar_visible(self._sidebar_width_visible)
        self._schedule_transcript_reflow()
        composer = self.query_one("#composer", Input)
        composer.value = ""
        composer.placeholder = 'Ask anything... "Summarize the risks in this document set"'
        self._sync_busy_to_current_session()
        self._update_info_panel()
        composer.focus()
        self.set_focus(composer)

    def _refresh_materials_inline(self: _MaterialsHost) -> None:
        query = self._materials_filter.strip().lower()
        files = list(self.session.source_files)
        if query:
            files = [file for file in files if query in file.lower()]
        self._materials_entries = files
        total = len(self.session.source_files)
        enabled = _active_material_count(self)
        header = (
            f"materials  {enabled}/{total} active"
            if self._materials_mode == "toggle"
            else f"sources  {enabled}/{total} active"
        )
        if query:
            header = f"{header}  {len(self._materials_entries)} shown"
        self.query_one("#materials-header", Static).update(header)

        previous = self._materials_highlighted_index
        if not self._materials_entries:
            highlighted = None
        elif previous is None:
            highlighted = 0
        else:
            highlighted = min(max(previous, 0), len(self._materials_entries) - 1)
        self._materials_highlighted_index = highlighted

        left_entries, right_entries = self._material_columns_for_entries()
        self._materials_columns = (left_entries, right_entries)
        columns = self.query_one("#materials-columns")
        if right_entries:
            columns.add_class("two-column")
        else:
            columns.remove_class("two-column")

        left = self.query_one("#materials-list", OptionList)
        right = self.query_one("#materials-list-right", OptionList)
        for list_id, material_list, entries in (
            ("materials-list", left, left_entries),
            ("materials-list-right", right, right_entries),
        ):
            material_list.clear_options()
            start = len(left_entries) if list_id == "materials-list-right" else 0
            for local_index, file in enumerate(entries):
                global_index = start + local_index
                material_list.add_option(
                    self._format_material_option(file, selected=global_index == highlighted)
                )
            material_list.highlighted = self._materials_local_index(list_id, highlighted)
        if self._materials_entries:
            self._focus_materials_highlighted_list()
        self._refresh_materials_highlight_class()
        footer = self.query_one("#materials-footer", Static)
        if not self.session.source_files:
            footer.update("No materials attached.")
        elif query and not self._materials_entries:
            footer.update(f"No materials match: {self._materials_filter}")
        else:
            footer.update(self._materials_footer_text())
        self._update_materials_sidebar()

    def _materials_footer_text(self: _MaterialsHost) -> str:
        if self._materials_mode == "toggle":
            return "type to filter  space or enter toggle  esc close"
        return "type to filter  enter or esc close"

    def _update_materials_sidebar(self: _MaterialsHost) -> None:
        sidebar = self.query_one("#info-panel", Static)
        idx = self._materials_highlighted_index
        total = len(self.session.source_files)
        enabled = _active_material_count(self)
        title = "Materials" if self._materials_mode == "toggle" else "Sources"
        if idx is None or idx < 0 or idx >= len(self._materials_entries):
            if self._materials_filter:
                content = (
                    f"{title}\n\n"
                    f"{enabled}/{total} active\n"
                    f"No matches\n\n"
                    f"Filter: {self._materials_filter}"
                )
            else:
                content = f"{title}\n\n{enabled}/{total} active\nNo material selected"
        else:
            file = self._materials_entries[idx]
            label = material_display_name(file)
            state = "active" if file not in self.session.disabled_source_files else "disabled"
            content = f"{title}\n\n@{label}\n{state}\n\n{file}"
        sidebar.update(sidebar_text(content))

    def _format_material_option(
        self: _MaterialsHost,
        file: str,
        *,
        selected: bool,
    ) -> str | Text:
        _ = selected
        palette = current_palette()
        enabled_file = file not in self.session.disabled_source_files
        label = material_display_name(file)
        state_color = palette.action_primary_bg if enabled_file else palette.status_error_text
        if _RichText is None:
            return f"@{label}"
        text = _RichText()
        text.append("@", style=palette.text_muted)
        text.append(label, style=state_color)
        return text

    def _material_columns_for_entries(self: _MaterialsHost) -> tuple[list[str], list[str]]:
        entries = list(self._materials_entries)
        if not self._materials_should_use_two_columns():
            return entries, []
        split_at = (len(entries) + 1) // 2
        return entries[:split_at], entries[split_at:]

    def _materials_should_use_two_columns(self: _MaterialsHost) -> bool:
        return (
            len(self._materials_entries) > 1
            and self.size.width >= _MATERIALS_MIN_TWO_COLUMN_WIDTH
            and len(self._materials_entries) > self._materials_visible_rows()
        )

    def _materials_visible_rows(self: _MaterialsHost) -> int:
        columns = self.query_one("#materials-columns")
        height = columns.size.height
        if height <= 0:
            height = max(1, self.size.height - 8)
        return max(1, height)

    def _materials_local_index(
        self: _MaterialsHost,
        list_id: str,
        global_index: int | None,
    ) -> int | None:
        if global_index is None:
            return None
        column = 1 if list_id == "materials-list-right" else 0
        start = len(self._materials_columns[0]) if column == 1 else 0
        local_index = global_index - start
        if 0 <= local_index < len(self._materials_columns[column]):
            return local_index
        return None

    def _materials_global_index(self: _MaterialsHost, list_id: str, index: int) -> int | None:
        column = 1 if list_id == "materials-list-right" else 0
        entries = self._materials_columns[column]
        if index < 0 or index >= len(entries):
            return None
        start = len(self._materials_columns[0]) if column == 1 else 0
        return start + index

    def _materials_list_for_index(self: _MaterialsHost, index: int) -> OptionList:
        right_start = len(self._materials_columns[0])
        list_id = "materials-list-right" if index >= right_start else "materials-list"
        return self.query_one(f"#{list_id}", OptionList)

    def _focus_materials_highlighted_list(self: _MaterialsHost) -> None:
        if self._materials_highlighted_index is None:
            return
        focused_id = getattr(self.focused, "id", None)
        if focused_id not in _MATERIALS_LIST_IDS:
            return
        target = self._materials_list_for_index(self._materials_highlighted_index)
        target.focus()
        self.set_focus(target)

    def _refresh_materials_highlight_class(self: _MaterialsHost) -> None:
        left = self.query_one("#materials-list", OptionList)
        right = self.query_one("#materials-list-right", OptionList)
        left.remove_class("material-enabled", "material-disabled")
        right.remove_class("material-enabled", "material-disabled")
        idx = self._materials_highlighted_index
        if idx is None or idx < 0 or idx >= len(self._materials_entries):
            return
        file = self._materials_entries[idx]
        class_name = (
            "material-disabled"
            if file in self.session.disabled_source_files
            else "material-enabled"
        )
        self._materials_list_for_index(idx).add_class(class_name)

    def _handle_materials_option_selected(
        self: _MaterialsHost,
        list_id: str,
        index: int,
    ) -> None:
        global_index = self._materials_global_index(list_id, index)
        if global_index is None:
            return
        self._materials_highlighted_index = global_index
        if self._materials_mode == "toggle":
            self._toggle_highlighted_material()
        else:
            self._close_materials_inline()

    def _handle_materials_option_highlighted(
        self: _MaterialsHost,
        list_id: str,
        index: int,
    ) -> None:
        global_index = self._materials_global_index(list_id, index)
        if global_index is None:
            return
        if self._materials_highlighted_index == global_index:
            self._refresh_materials_highlight_class()
            return
        self._materials_highlighted_index = global_index
        self._refresh_materials_inline()

    def _toggle_highlighted_material(self: _MaterialsHost) -> None:
        idx = self._materials_highlighted_index
        if idx is None or idx < 0 or idx >= len(self._materials_entries):
            return
        file = self._materials_entries[idx]
        self._set_material_enabled(file, file in self.session.disabled_source_files)
        self._refresh_materials_inline()

    def _move_material_highlight(self: _MaterialsHost, offset: int) -> None:
        if not self._materials_entries:
            return
        highlighted = self._materials_highlighted_index
        if highlighted is None:
            highlighted = 0
        self._materials_highlighted_index = (highlighted + offset) % len(self._materials_entries)
        self._refresh_materials_inline()

    def _set_material_enabled(
        self: _MaterialsHost,
        file: str,
        enabled: bool,
    ) -> None:
        disabled = self.session.disabled_source_files
        if enabled:
            if file not in disabled:
                return
            disabled.remove(file)
        else:
            if file in disabled:
                return
            disabled.add(file)
        self.session.dirty = True

    def _handle_materials_key(self: _MaterialsHost, event: events.Key) -> bool:
        if event.key == "escape":
            self._close_materials_inline()
            event.prevent_default()
            event.stop()
            return True
        if event.key == "enter":
            if self._materials_mode == "toggle":
                self._toggle_highlighted_material()
            else:
                self._close_materials_inline()
            event.prevent_default()
            event.stop()
            return True
        if event.key in ("up", "k"):
            self._move_material_highlight(-1)
            event.prevent_default()
            event.stop()
            return True
        if event.key in ("down", "j"):
            self._move_material_highlight(1)
            event.prevent_default()
            event.stop()
            return True
        if event.key == "space" or event.character == " ":
            if self._materials_mode == "toggle":
                self._toggle_highlighted_material()
            event.prevent_default()
            event.stop()
            return True
        return False
