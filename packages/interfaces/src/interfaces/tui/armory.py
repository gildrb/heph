from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, overload

from hephaion.armory.search import remember_armory, set_last_armory
from hephaion.armory.storage import ArmoryError, initialize
from hephaion.armory.storage import validate as _validate_armory

from hephaion.materials import count_material_files
from interfaces.terminal import current_palette
from interfaces.tui.armory_browser import (
    _creation_parent_error,
    _DirEntry,
    _is_armory,
    _is_within_armory_home,
    build_entries,
    default_armory_home,
    new_armory_path,
)
from interfaces.tui.cell_text import cell_width as _cell_width
from interfaces.tui.cell_text import pad_cell_right as _pad_cell_right
from interfaces.tui.cell_text import truncate_with_ellipsis as _truncate_with_ellipsis
from interfaces.tui.display_text import COMPOSER_PLACEHOLDER, label_value_line
from interfaces.tui.inline_menu import _inline_selection_prefix
from interfaces.tui.textual_compat import (
    ClassableWidget as _ClassableWidget,
)
from interfaces.tui.textual_compat import (
    Input,
    OptionList,
    RichLog,
    Static,
    sidebar_content_width,
    sidebar_text,
)
from interfaces.tui.textual_compat import (
    RichText as _RichText,
)
from interfaces.tui.textual_compat import (
    WidgetT as _WidgetT,
)

if TYPE_CHECKING:
    from hephaion.chat.session import ChatSession
    from rich.text import Text
    from textual import events
    from textual.widget import Widget


class _ArmoryHost(Protocol):
    _armory_inline_active: bool
    _armory_current: Path
    _armory_filter: str
    _armory_flow: str
    _armory_creating: bool
    _armory_entries: list[_DirEntry]
    _active_turn_sessions: dict[str, ChatSession]
    _turn_sessions: dict[str, ChatSession]
    _sidebar_width_visible: bool
    _focused_msg_index: int | None
    session: ChatSession

    @property
    def focused(self) -> object | None: ...

    @overload
    def query_one(self, selector: str) -> _ClassableWidget: ...

    @overload
    def query_one(self, selector: str, expect_type: type[_WidgetT]) -> _WidgetT: ...

    def set_focus(self, widget: Widget | None) -> None: ...

    def _append_error(self, text: str) -> None: ...

    def _append_notice(self, text: str) -> None: ...

    def _set_sidebar_visible(self, visible: bool) -> None: ...

    def _turn_key_for_armory_path(self, armory_path: Path) -> str: ...

    def _hide_completions(self) -> None: ...

    def _refresh_footer_hints(self) -> None: ...

    def _schedule_transcript_reflow(self) -> None: ...

    def _refresh_status(self) -> None: ...

    def _sync_busy_to_current_session(self) -> None: ...

    def _replace_transcript_from_session(self) -> None: ...

    def _update_info_panel(self) -> None: ...

    def _open_armory_inline(self, flow: str) -> None: ...

    def _close_armory_inline(self) -> None: ...

    def _record_history(self, value: str) -> None: ...

    def _refresh_armory_inline(self) -> None: ...

    def _refresh_armory_header(self) -> None: ...

    def _refreshed_armory_highlight(self, previous_key: tuple[str, str] | None) -> int | None: ...

    def _armory_entry_selectable(self, index: int) -> bool: ...

    def _render_armory_options(self, highlighted: int | None = None) -> None: ...

    def _armory_selection_key(self) -> tuple[str, str] | None: ...

    def _current_armory_index(self) -> int | None: ...

    def _armory_index_for_key(self, key: tuple[str, str] | None) -> int | None: ...

    def _first_selectable_armory_index(self) -> int | None: ...

    def _armory_highlighted_entry(self) -> _DirEntry | None: ...

    def _update_armory_preview(self) -> None: ...

    def _move_armory_highlight(self, offset: int) -> None: ...

    def _start_inline_create(self) -> None: ...

    def _open_selected_armory(self, path: Path) -> None: ...

    def _append_hidden_armory_error(self, text: str) -> None: ...


def _armory_command_flow(value: str) -> str | None:
    flows: dict[tuple[str, ...], str] = {
        ("/armory",): "manage",
        ("/armory", "menu"): "manage",
        ("/armory", "open"): "open",
        ("/armory", "create"): "create",
        ("/armory", "new"): "create",
    }
    return flows.get(tuple(value.strip().lower().split()))


_ARMORY_USAGE_MESSAGE = (
    "Usage: /armory [open|create]\nBrowse, open, or create a local document armory."
)
_ARMORY_CREATE_PLACEHOLDER = "CREATE armory name"
_ARMORY_FILTER_PLACEHOLDER = "FILTER armory paths"
_ARMORY_ROW_LEFT_PADDING = len(_inline_selection_prefix(False))
_ARMORY_TRUNCATION_MARKER = "..."


def _display_path(path: Path) -> str:
    try:
        return f"~/{path.relative_to(Path.home())}"
    except ValueError:
        return str(path)


def _armory_reference_tokens(value: str) -> tuple[str, ...]:
    stripped = value.strip()
    if not stripped:
        return ()
    return (stripped,)


def _candidate_path_from_reference(reference: str) -> Path:
    candidate = Path(reference).expanduser()
    if candidate.is_absolute():
        return candidate.resolve(strict=False)
    return (default_armory_home() / candidate).resolve(strict=False)


def _known_armory_paths_by_name() -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for entry in build_entries(allow_create=False, show_places=False):
        if (
            entry.path is None
            or not _is_armory(entry.path)
            or not _is_within_armory_home(entry.path)
        ):
            continue
        paths.setdefault(entry.path.name, entry.path.resolve(strict=False))
    return paths


def _resolve_armory_reference(value: str) -> Path | None:
    known_paths = _known_armory_paths_by_name()
    matched_paths: set[Path] = set()
    for token in _armory_reference_tokens(value):
        if path := known_paths.get(token):
            matched_paths.add(path)
            continue
        candidate = _candidate_path_from_reference(token)
        if _is_within_armory_home(candidate) and _is_armory(candidate):
            matched_paths.add(candidate)
    if len(matched_paths) != 1:
        return None
    return next(iter(matched_paths))


_ARMORY_DESCRIPTION_GAP = 4


def _armory_selectable_count(entries: list[_DirEntry]) -> int:
    return sum(1 for entry in entries if entry.path is not None or entry.is_create)


def _armory_header_text(
    *,
    current_path: Path,
    filter_query: str,
    entries: list[_DirEntry],
    label_width: int = 0,
) -> str:
    del current_path, filter_query
    count_label = label_value_line("items", _armory_selectable_count(entries))
    label_width = max(label_width, _cell_width(count_label) + 2 - _ARMORY_DESCRIPTION_GAP)
    return f"{' ' * _ARMORY_ROW_LEFT_PADDING}{_pad_cell_right(count_label, label_width)}"


def _armory_flow_hint(*, creating: bool) -> str:
    del creating
    return ""


def _armory_entry_label(entry: _DirEntry) -> str:
    return entry.label.strip()


def _armory_entry_description(entry: _DirEntry, *, active: bool = False) -> str:
    if entry.is_section or not entry.label:
        return ""
    if entry.is_create:
        return ""
    state = _armory_entry_state(entry.path, active=active)
    file_count = _armory_entry_file_column(entry.path)
    if not state:
        return label_value_line("files", file_count)
    return f"{label_value_line('files', file_count)}  {label_value_line('state', state)}"


def _armory_entry_file_column(path: Path | None) -> str:
    if path is None or not path.exists() or not _is_armory(path):
        return "-"
    return str(count_material_files(path))


def _armory_entry_state(path: Path | None, *, active: bool = False) -> str:
    if active:
        return "working"
    if path is None:
        return ""
    if not path.exists():
        return "missing"
    if not _is_armory(path):
        return "folder"
    if count_material_files(path) == 0:
        return "empty"
    return ""


def _armory_sidebar_text(entry: _DirEntry | None, *, active: bool = False) -> str:
    if entry is None:
        return label_value_line("state", "none")
    label = _armory_entry_label(entry).strip()
    if entry.is_create:
        return "\n".join(
            (
                label_value_line("action", "create"),
                label_value_line("scope", "local armory"),
                label_value_line("materials", "add files in materials/"),
            )
        )
    if entry.path is None:
        return label_value_line("section", label)
    state = _armory_entry_state(entry.path, active=active)
    if state == "missing":
        return "\n".join(
            (
                label_value_line("state", "missing"),
                label_value_line("detail", "recent entry no longer exists"),
            )
        )
    if state == "folder":
        return "\n".join(
            (
                label_value_line("state", "folder"),
                label_value_line("action", "initialize before using"),
            )
        )
    if state == "empty":
        return "\n".join(
            (
                label_value_line("state", "empty"),
                label_value_line("materials", "add files in materials/"),
            )
        )
    if state == "working":
        return "\n".join(
            (
                label_value_line("state", "working"),
                label_value_line("detail", "turn running"),
            )
        )
    return "\n".join(
        (
            label_value_line("state", "ready"),
            label_value_line("materials", "available"),
            label_value_line("memory", "armory scoped"),
        )
    )


def _armory_preview_text(entry: _DirEntry | None, *, filter_query: str, active: bool) -> str:
    if entry is None:
        if filter_query:
            return "\n".join(
                (
                    label_value_line("state", "no matches"),
                    label_value_line("filter", filter_query),
                    label_value_line("action", "esc clears"),
                )
            )
        return label_value_line("state", "none")
    content = _armory_sidebar_text(entry, active=active)
    if active:
        return content
    return content


def _armory_visible_entries(
    entries: list[_DirEntry],
    *,
    highlighted: int | None,
    rendered_height: int,
) -> list[_DirEntry]:
    if not entries:
        return []
    visible_rows = rendered_height if rendered_height > 0 else len(entries)
    visible_rows = max(1, min(len(entries), visible_rows))
    highlighted_index = highlighted if highlighted is not None else 0
    max_scroll_y = max(0, len(entries) - visible_rows)
    scroll_y = min(max(highlighted_index - (visible_rows // 2), 0), max_scroll_y)
    return entries[scroll_y : scroll_y + visible_rows]


def _armory_label_width(
    entries: list[_DirEntry],
    *,
    highlighted: int | None,
    rendered_height: int,
) -> int:
    return max(
        (
            _cell_width(_armory_entry_label(entry))
            for entry in _armory_visible_entries(
                entries,
                highlighted=highlighted,
                rendered_height=rendered_height,
            )
            if _armory_entry_label(entry)
        ),
        default=0,
    )


def _armory_row_width(widget: _ClassableWidget, host: object) -> int:
    if widget.size.width > 0:
        return widget.size.width
    host_size = getattr(host, "size", None)
    host_width = getattr(host_size, "width", 0)
    return host_width if isinstance(host_width, int) else 0


def _armory_description_width(entries: list[_DirEntry]) -> int:
    return max((_cell_width(_armory_entry_description(entry)) for entry in entries), default=0)


def _armory_layout_label_width(
    label_width: int,
    count_label: str,
    *,
    entries: list[_DirEntry],
    row_width: int,
) -> int:
    label_width = max(label_width, _cell_width(count_label) + 2 - _ARMORY_DESCRIPTION_GAP)
    if row_width <= 0:
        return label_width
    description_width = max(
        _armory_description_width(entries),
        _cell_width(label_value_line("files", "-")),
    )
    available = row_width - _ARMORY_ROW_LEFT_PADDING - _ARMORY_DESCRIPTION_GAP
    available -= description_width
    if available <= 0:
        return min(label_width, max(1, row_width - _ARMORY_ROW_LEFT_PADDING))
    return min(label_width, max(1, available))


def _clip_armory_label(label: str, width: int) -> str:
    return _truncate_with_ellipsis(label, width)


def _armory_entry_text(
    entry: _DirEntry,
    *,
    selected: bool,
    active: bool = False,
    label_width: int = 0,
) -> str | Text:
    label = _armory_entry_label(entry)
    description = _armory_entry_description(entry, active=active)
    if _RichText is None:
        prefix = _inline_selection_prefix(selected)
        if description:
            label = _clip_armory_label(label, label_width)
            return (
                f"{prefix}{_pad_cell_right(label, label_width)}"
                f"{' ' * _ARMORY_DESCRIPTION_GAP}{description}"
            )
        return f"{prefix}{label}"
    if not label:
        return ""

    palette = current_palette()
    text = _RichText()
    prefix = _inline_selection_prefix(selected)
    prefix_style = palette.brand_primary if selected else palette.text_muted
    text.append(prefix, style=prefix_style)
    if entry.is_section:
        text.append(label, style=f"dim {palette.text_muted}")
        return text
    label_style = palette.brand_primary if selected else palette.text_primary
    description_style = palette.text_muted
    padded_width = max(label_width, _cell_width(label))
    if description:
        label = _clip_armory_label(label, label_width)
        padded_width = label_width
    text.append(_pad_cell_right(label, padded_width) if description else label, style=label_style)
    if description:
        text.append(" " * _ARMORY_DESCRIPTION_GAP, style=description_style)
        text.append(description, style=description_style)
    return text


class TuiArmoryMixin:
    def _open_armory_reference_from_input(self: _ArmoryHost, value: str) -> bool:
        if self.session.armory_path is not None:
            return False
        armory_path = _resolve_armory_reference(value)
        if armory_path is None:
            return False
        self._record_history(value)
        self._open_selected_armory(armory_path)
        return True

    def _handle_armory_browser(self: _ArmoryHost, value: str) -> None:
        flow = _armory_command_flow(value)
        composer = self.query_one("#composer", Input)
        if flow is None:
            self._append_error(_ARMORY_USAGE_MESSAGE)
            composer.focus()
            return
        self._open_armory_inline(flow)

    def _open_armory_inline(self: _ArmoryHost, flow: str) -> None:
        self._armory_inline_active = True
        self._armory_current = default_armory_home()
        self._armory_filter = ""
        self._armory_flow = flow
        self._armory_creating = flow == "create"
        self.query_one("#transcript", RichLog).add_class("hidden-for-armory")
        self.query_one("#transcript-spacer", Static).add_class("hidden-for-armory")
        self.query_one("#armory-inline").add_class("active")
        self._set_sidebar_visible(self._sidebar_width_visible)
        composer = self.query_one("#composer", Input)
        composer.value = ""
        composer.placeholder = (
            _ARMORY_CREATE_PLACEHOLDER if self._armory_creating else _ARMORY_FILTER_PLACEHOLDER
        )
        self._hide_completions()
        self._armory_entries = []
        current = self.query_one("#armory-current-inline", OptionList)
        current.clear_options()
        current.highlighted = None
        self._refresh_armory_inline()
        self._refresh_status()
        self._refresh_footer_hints()
        composer.focus()
        self.set_focus(composer)

    def _close_armory_inline(self: _ArmoryHost) -> None:
        self._armory_inline_active = False
        self._armory_filter = ""
        self._armory_creating = False
        self._armory_flow = "manage"
        self.query_one("#transcript", RichLog).remove_class("hidden-for-armory")
        self.query_one("#transcript-spacer", Static).remove_class("hidden-for-armory")
        self.query_one("#armory-inline").remove_class("active")
        self._set_sidebar_visible(self._sidebar_width_visible)
        self._update_info_panel()
        self._schedule_transcript_reflow()
        composer = self.query_one("#composer", Input)
        composer.value = ""
        composer.placeholder = COMPOSER_PLACEHOLDER
        self._refresh_status()
        self._refresh_footer_hints()
        composer.focus()
        self.set_focus(composer)

    def _refresh_armory_inline(self: _ArmoryHost) -> None:
        if not _is_within_armory_home(self._armory_current):
            self._armory_current = default_armory_home()
        previous_key = self._armory_selection_key()
        self._armory_entries = build_entries(
            allow_create=self._armory_flow in ("manage", "create"),
            filter_query=self._armory_filter,
            show_places=False,
        )
        self._refresh_armory_header()
        highlighted = self._refreshed_armory_highlight(previous_key)
        self._render_armory_options(highlighted)
        self._update_armory_preview()

    def _refresh_armory_header(self: _ArmoryHost) -> None:
        current = self.query_one("#armory-current-inline", OptionList)
        label_width = _armory_label_width(
            self._armory_entries,
            highlighted=current.highlighted,
            rendered_height=current.size.height,
        )
        label_width = _armory_layout_label_width(
            label_width,
            label_value_line("items", _armory_selectable_count(self._armory_entries)),
            entries=self._armory_entries,
            row_width=_armory_row_width(current, self),
        )
        self.query_one("#armory-header", Static).update(
            _armory_header_text(
                current_path=self._armory_current,
                filter_query=self._armory_filter,
                entries=self._armory_entries,
                label_width=label_width,
            )
        )
        self.query_one("#armory-breadcrumbs", Static).update("")
        self.query_one("#armory-flow-hint", Static).update(
            _armory_flow_hint(creating=self._armory_creating)
        )
        self.query_one("#armory-pane-hint", Static).update("")
        self.query_one("#armory-count-hint", Static).update("")

    def _refreshed_armory_highlight(
        self: _ArmoryHost,
        previous_key: tuple[str, str] | None,
    ) -> int | None:
        highlighted = self._armory_index_for_key(previous_key)
        if highlighted is not None and self._armory_entry_selectable(highlighted):
            return highlighted
        if previous_key is None:
            current_index = self._current_armory_index()
            if current_index is not None:
                return current_index
        return self._first_selectable_armory_index()

    def _current_armory_index(self: _ArmoryHost) -> int | None:
        if self._armory_creating or self.session.armory_path is None:
            return None
        try:
            current_path = self.session.armory_path.resolve(strict=False)
        except OSError:
            return None
        for index, entry in enumerate(self._armory_entries):
            if entry.path is None or not self._armory_entry_selectable(index):
                continue
            try:
                entry_path = entry.path.resolve(strict=False)
            except OSError:
                continue
            if entry_path == current_path:
                return index
        return None

    def _armory_entry_selectable(self: _ArmoryHost, index: int) -> bool:
        if index < 0 or index >= len(self._armory_entries):
            return False
        entry = self._armory_entries[index]
        return entry.path is not None or entry.is_create

    def _render_armory_options(
        self: _ArmoryHost,
        highlighted: int | None = None,
    ) -> None:
        current = self.query_one("#armory-current-inline", OptionList)
        if highlighted is None:
            highlighted = current.highlighted
        label_width = _armory_label_width(
            self._armory_entries,
            highlighted=highlighted,
            rendered_height=current.size.height,
        )
        count_label = label_value_line("items", _armory_selectable_count(self._armory_entries))
        label_width = _armory_layout_label_width(
            label_width,
            count_label,
            entries=self._armory_entries,
            row_width=_armory_row_width(current, self),
        )
        self.query_one("#armory-header", Static).update(
            _armory_header_text(
                current_path=self._armory_current,
                filter_query=self._armory_filter,
                entries=self._armory_entries,
                label_width=label_width,
            )
        )
        current.set_options(
            [
                _armory_entry_text(
                    entry,
                    selected=index == highlighted,
                    active=(
                        entry.path is not None
                        and self._turn_key_for_armory_path(entry.path)
                        in self._active_turn_sessions
                    ),
                    label_width=label_width,
                )
                for index, entry in enumerate(self._armory_entries)
            ]
        )
        current.highlighted = highlighted

    def _armory_focus_name(self: _ArmoryHost) -> str:
        """Return which pane is focused for explicit navigation feedback."""
        focused = self.focused
        if focused is None:
            return "none"
        widget_id = getattr(focused, "id", None)
        if widget_id == "armory-current-inline":
            return "armories"
        if widget_id == "composer":
            return "input"
        return "preview"

    def _armory_selection_key(self: _ArmoryHost) -> tuple[str, str] | None:
        entry = self._armory_highlighted_entry()
        if entry is None:
            return None
        if entry.path is not None:
            return ("path", str(entry.path))
        if entry.is_create:
            return ("create", entry.label)
        return ("label", entry.label)

    def _armory_index_for_key(self: _ArmoryHost, key: tuple[str, str] | None) -> int | None:
        if key is None:
            return None
        for index, entry in enumerate(self._armory_entries):
            if entry.path is not None and key == ("path", str(entry.path)):
                return index
            if entry.path is None and key == ("label", entry.label):
                return index
            if entry.is_create and key == ("create", entry.label):
                return index
        return None

    def _first_selectable_armory_index(self: _ArmoryHost) -> int | None:
        for index, entry in enumerate(self._armory_entries):
            if entry.path is not None or entry.is_create:
                return index
        return None

    def _armory_highlighted_entry(self: _ArmoryHost) -> _DirEntry | None:
        current = self.query_one("#armory-current-inline", OptionList)
        idx = current.highlighted
        if idx is None or idx < 0 or idx >= len(self._armory_entries):
            return None
        return self._armory_entries[idx]

    def _update_armory_preview(self: _ArmoryHost) -> None:
        preview = self.query_one("#armory-preview-inline", Static)
        sidebar = self.query_one("#info-panel", Static)
        entry = self._armory_highlighted_entry()
        active = (
            entry is not None
            and entry.path is not None
            and self._turn_key_for_armory_path(entry.path) in self._active_turn_sessions
        )
        content = _armory_preview_text(entry, filter_query=self._armory_filter, active=active)
        preview.update(content)
        sidebar.update(sidebar_text(content, width=sidebar_content_width(sidebar)))

    def _move_armory_highlight(self: _ArmoryHost, offset: int) -> None:
        if not self._armory_entries:
            return
        current = self.query_one("#armory-current-inline", OptionList)
        highlighted = current.highlighted
        if highlighted is None:
            highlighted = -1 if offset > 0 else 0
        for step in range(1, len(self._armory_entries) + 1):
            index = (highlighted + (offset * step)) % len(self._armory_entries)
            entry = self._armory_entries[index]
            if entry.path is not None or entry.is_create:
                current.highlighted = index
                break
        self._render_armory_options()
        self._update_armory_preview()

    def _armory_open_highlighted(self: _ArmoryHost) -> None:
        entry = self._armory_highlighted_entry()
        if entry is None or not entry.label:
            return
        if entry.is_create:
            self._start_inline_create()
            return
        if entry.is_section:
            return
        if entry.path is not None:
            if not _is_within_armory_home(entry.path):
                self.query_one("#armory-error-inline", Static).update(
                    f"Cannot navigate outside armory home: {entry.path}"
                )
                return
            self._open_selected_armory(entry.path)

    def _start_inline_create(self: _ArmoryHost) -> None:
        self._armory_creating = True
        self._armory_flow = "create"
        composer = self.query_one("#composer", Input)
        composer.value = ""
        composer.placeholder = _ARMORY_CREATE_PLACEHOLDER
        self._refresh_armory_inline()
        self._refresh_footer_hints()
        composer.focus()

    def _create_inline_armory(self: _ArmoryHost, name: str) -> None:
        if not name:
            self._armory_creating = False
            self.query_one("#composer", Input).placeholder = _ARMORY_FILTER_PLACEHOLDER
            self._refresh_armory_inline()
            self._refresh_footer_hints()
            return
        parent_error = _creation_parent_error(self._armory_current)
        if parent_error is not None:
            self.query_one("#armory-error-inline", Static).update(parent_error)
            return
        armory_path, name_error = new_armory_path(self._armory_current, name)
        if name_error is not None or armory_path is None:
            self.query_one("#armory-error-inline", Static).update(
                name_error or "Invalid armory name."
            )
            return
        try:
            initialize(armory_path)
        except (ArmoryError, OSError) as exc:
            self.query_one("#armory-error-inline", Static).update(
                f"Could not create armory: {exc}"
            )
            return
        remember_armory(armory_path)
        self._close_armory_inline()
        self._append_notice(f"Created armory '{armory_path.name}' at {armory_path}")
        display_root = _display_path(armory_path.parent)
        self._append_notice(f"Add documents to {display_root}/{armory_path.name}/materials/")

    def _open_selected_armory(self: _ArmoryHost, path: Path) -> None:
        if not _is_within_armory_home(path):
            self._append_hidden_armory_error(f"Cannot open an armory outside armory home: {path}")
            return
        try:
            _validate_armory(path)
        except OSError as exc:
            self._append_hidden_armory_error(f"Could not read armory: {exc}")
            return
        except ArmoryError as exc:
            self._append_hidden_armory_error(f"Not a valid armory: {exc}")
            return
        previous = self.session
        tui_module = sys.modules["interfaces.tui"]
        turn_key = self._turn_key_for_armory_path(path)
        reusable_session = self._active_turn_sessions.get(turn_key) or self._turn_sessions.get(
            turn_key
        )
        if reusable_session is None:
            self.session = tui_module.start_fresh_session(self.session, path)
        else:
            self.session = reusable_session
        if self.session is previous:
            self._append_hidden_armory_error(f"Could not open armory: {path}")
            return
        set_last_armory(path)
        self._turn_sessions[turn_key] = self.session
        self._close_armory_inline()
        self._focused_msg_index = None
        self._replace_transcript_from_session()
        self._sync_busy_to_current_session()
        self._update_info_panel()
        self._append_notice(f"Using armory {path.name}")
        src_count = self.session.source_file_count or 0
        if src_count:
            self._append_notice(f"Loaded {src_count} file(s).")

    def _append_hidden_armory_error(self: _ArmoryHost, text: str) -> None:
        self.query_one("#armory-error-inline", Static).update(text)
        if not self._armory_inline_active:
            self._append_error(text)

    def _handle_armory_key(self: _ArmoryHost, event: events.Key) -> bool:
        composer = self.query_one("#composer", Input)
        if event.key == "escape":
            if self._armory_creating:
                self._armory_creating = False
                composer.value = ""
                composer.placeholder = _ARMORY_FILTER_PLACEHOLDER
                self._refresh_armory_inline()
                self._refresh_footer_hints()
            elif composer.value:
                composer.value = ""
                self._armory_filter = ""
                self._refresh_armory_inline()
                self._refresh_footer_hints()
            else:
                self._close_armory_inline()
            event.prevent_default()
            event.stop()
            return True
        if event.key in ("up", "k"):
            self._move_armory_highlight(-1)
            event.prevent_default()
            event.stop()
            return True
        if event.key in ("down", "j"):
            self._move_armory_highlight(1)
            event.prevent_default()
            event.stop()
            return True
        return False
