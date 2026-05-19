from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, overload

from hephaistos.armory.search import add_known_armory, set_last_armory
from hephaistos.armory.storage import ArmoryError, initialize
from hephaistos.armory.storage import validate as _validate_armory
from hephaistos.terminal import current_palette
from hephaistos.tui.armory_browser import (
    _creation_parent_error,
    _DirEntry,
    _is_within_armory_home,
    armory_detail,
    build_entries,
    default_armory_home,
    new_armory_path,
)
from hephaistos.tui.textual_compat import (
    ClassableWidget as _ClassableWidget,
)
from hephaistos.tui.textual_compat import (
    Input,
    OptionList,
    RichLog,
    Static,
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
    from textual.widget import Widget

    from hephaistos.chat.session import ChatSession


class _ArmoryHost(Protocol):
    _armory_inline_active: bool
    _armory_current: Path
    _armory_filter: str
    _armory_mode: str
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

    def _refresh_status(self, state: str) -> None: ...

    def _sync_busy_to_current_session(self, *, idle_status: str = "ready") -> None: ...

    def _replace_transcript_from_session(self) -> None: ...

    def _update_info_panel(self) -> None: ...

    def _open_armory_inline(self, mode: str) -> None: ...

    def _close_armory_inline(self) -> None: ...

    def _refresh_armory_inline(self, *, mode: str = "manage") -> None: ...

    def _render_armory_options(self, highlighted: int | None = None) -> None: ...

    def _armory_selection_key(self) -> tuple[str, str] | None: ...

    def _armory_index_for_key(self, key: tuple[str, str] | None) -> int | None: ...

    def _first_selectable_armory_index(self) -> int | None: ...

    def _armory_highlighted_entry(self) -> _DirEntry | None: ...

    def _update_armory_preview(self) -> None: ...

    def _move_armory_highlight(self, offset: int) -> None: ...

    def _start_inline_create(self) -> None: ...

    def _open_selected_armory(self, path: Path) -> None: ...


def _armory_command_mode(value: str) -> str | None:
    """Return the TUI armory browser mode, or None for invalid usage."""
    parts = value.strip().lower().split()
    command = tuple(parts)
    if command in (("/armory",), ("/armory", "menu")):
        return "manage"
    if command == ("/armory", "open"):
        return "open"
    if command in (("/armory", "create"), ("/armory", "new")):
        return "create"
    return None


def _armory_usage_message() -> str:
    return "Usage: /armory [open|create]\nBrowse, open, or create a local document armory."


def _display_path(path: Path) -> str:
    """Return a compact path label that keeps home-relative paths readable."""
    try:
        return f"~/{path.relative_to(Path.home())}"
    except ValueError:
        return str(path)


def _sidebar_text(content: str) -> str:
    return "\n".join(f"  {line}" if line else "" for line in content.splitlines())


_ACTIVE_TURN_BADGE = "  working"


def _armory_entry_text(entry: _DirEntry, *, selected: bool, active: bool = False) -> str | Text:
    if _RichText is None:
        return f"{entry.label}{_ACTIVE_TURN_BADGE if active else ''}"
    if not entry.label:
        return ""

    palette = current_palette()
    text = _RichText()
    leading = entry.label[: len(entry.label) - len(entry.label.lstrip())]
    label = entry.label.strip()
    text.append(leading, style=palette.text_muted)
    if entry.is_section:
        text.append(label, style=f"dim {palette.text_muted}")
    elif entry.is_create:
        style = f"bold {palette.brand_primary}" if selected else palette.text_primary
        text.append(label, style=style)
    elif entry.is_missing:
        style = f"bold {palette.status_error_text}" if selected else palette.status_error_text
        text.append(label, style=style)
    else:
        style = f"bold {palette.brand_primary}" if selected else palette.text_primary
        text.append(label, style=style)
    if active:
        badge_style = f"bold {palette.brand_primary}" if selected else palette.brand_primary
        text.append(_ACTIVE_TURN_BADGE, style=badge_style)
    return text


class TuiArmoryMixin:
    def _handle_armory_browser(self: _ArmoryHost, value: str) -> None:
        mode = _armory_command_mode(value)
        composer = self.query_one("#composer", Input)
        if mode is None:
            self._append_error(_armory_usage_message())
            composer.focus()
            return
        self._open_armory_inline(mode)

    def _open_armory_inline(self: _ArmoryHost, mode: str) -> None:
        self._armory_inline_active = True
        self._armory_current = default_armory_home()
        self._armory_filter = ""
        self._armory_mode = mode
        self._armory_creating = mode == "create"
        self.query_one("#transcript", RichLog).add_class("hidden-for-armory")
        self.query_one("#transcript-spacer", Static).add_class("hidden-for-armory")
        self.query_one("#armory-inline").add_class("active")
        self._set_sidebar_visible(self._sidebar_width_visible)
        composer = self.query_one("#composer", Input)
        composer.value = ""
        composer.placeholder = (
            "Module or topic name..." if self._armory_creating else "Filter armory paths..."
        )
        self._hide_completions()
        self._refresh_armory_inline(mode=mode)
        self._refresh_footer_hints()
        composer.focus()
        self.set_focus(composer)

    def _close_armory_inline(self: _ArmoryHost) -> None:
        self._armory_inline_active = False
        self._armory_filter = ""
        self._armory_creating = False
        self._armory_mode = "manage"
        self.query_one("#transcript", RichLog).remove_class("hidden-for-armory")
        self.query_one("#transcript-spacer", Static).remove_class("hidden-for-armory")
        self.query_one("#armory-inline").remove_class("active")
        self._set_sidebar_visible(self._sidebar_width_visible)
        self._update_info_panel()
        self._schedule_transcript_reflow()
        composer = self.query_one("#composer", Input)
        composer.value = ""
        composer.placeholder = 'Ask anything... "Summarize the risks in this document set"'
        self._refresh_footer_hints()
        composer.focus()
        self.set_focus(composer)

    def _refresh_armory_inline(self: _ArmoryHost, *, mode: str = "manage") -> None:
        if not _is_within_armory_home(self._armory_current):
            self._armory_current = default_armory_home()
        previous_key = self._armory_selection_key()
        self._armory_entries = build_entries(
            self._armory_current,
            allow_create=self._armory_mode in ("manage", "create"),
            filter_query=self._armory_filter,
            show_places=False,
        )
        header = self.query_one("#armory-header", Static)
        breadcrumbs = self.query_one("#armory-breadcrumbs", Static)
        mode_hint = self.query_one("#armory-mode-hint", Static)
        pane_hint = self.query_one("#armory-pane-hint", Static)

        location = _display_path(self._armory_current)
        filter_hint = f"  {self._armory_filter}" if self._armory_filter else ""
        selectable_count = sum(
            1 for entry in self._armory_entries if entry.path is not None or entry.is_create
        )
        count_hint = f"  {selectable_count} item(s)"
        header.update(f"armory  {location}{filter_hint}{count_hint}")
        breadcrumbs.update("")

        if self._armory_creating:
            mode_hint.update("enter create  esc cancel")
        else:
            mode_hint.update("enter open  n new  esc close")

        pane_hint.update("")
        self.query_one("#armory-count-hint", Static).update("")

        highlighted = self._armory_index_for_key(previous_key)
        if highlighted is not None:
            entry = self._armory_entries[highlighted]
            if entry.path is None and not entry.is_create:
                highlighted = None
        if highlighted is None:
            highlighted = self._first_selectable_armory_index()
        self._render_armory_options(highlighted)
        self._update_armory_preview()

    def _render_armory_options(
        self: _ArmoryHost,
        highlighted: int | None = None,
    ) -> None:
        current = self.query_one("#armory-current-inline", OptionList)
        if highlighted is None:
            highlighted = current.highlighted
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
        if entry is None:
            if self._armory_filter:
                content = f"No matches\n\nFilter: {self._armory_filter}\n\nEsc clears the filter."
            else:
                content = "No selection"
        elif entry.path is None:
            content = entry.label or ""
        else:
            content = armory_detail(entry.path)
            if self._turn_key_for_armory_path(entry.path) in self._active_turn_sessions:
                content = f"{content}\n\nassistant working"
        preview.update(content)
        sidebar.update(_sidebar_text(content))

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
        self._armory_mode = "create"
        composer = self.query_one("#composer", Input)
        composer.value = ""
        composer.placeholder = "Module or topic name..."
        self._refresh_armory_inline()
        self._refresh_footer_hints()
        composer.focus()

    def _create_inline_armory(self: _ArmoryHost, name: str) -> None:
        if not name:
            self._armory_creating = False
            self.query_one("#composer", Input).placeholder = "Filter armory paths..."
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
        add_known_armory(armory_path)
        self._close_armory_inline()
        self._append_notice(f"Created armory '{armory_path.name}' at {armory_path}")
        display_root = _display_path(armory_path.parent)
        self._append_notice(f"Add documents to {display_root}/{armory_path.name}/materials/")

    def _open_selected_armory(self: _ArmoryHost, path: Path) -> None:
        if not _is_within_armory_home(path):
            self.query_one("#armory-error-inline", Static).update(
                f"Cannot open an armory outside armory home: {path}"
            )
            return
        try:
            _validate_armory(path)
        except OSError as exc:
            self.query_one("#armory-error-inline", Static).update(f"Could not read armory: {exc}")
            return
        except ArmoryError as exc:
            self.query_one("#armory-error-inline", Static).update(f"Not a valid armory: {exc}")
            return
        previous = self.session
        tui_module = sys.modules["hephaistos.tui"]
        turn_key = self._turn_key_for_armory_path(path)
        reusable_session = self._active_turn_sessions.get(turn_key) or self._turn_sessions.get(
            turn_key
        )
        if reusable_session is None:
            self.session = tui_module.start_fresh_session(self.session, path)
        else:
            self.session = reusable_session
        if self.session is previous:
            self.query_one("#armory-error-inline", Static).update(f"Could not open armory: {path}")
            return
        set_last_armory(path)
        self._turn_sessions[turn_key] = self.session
        self._close_armory_inline()
        self._focused_msg_index = None
        self._replace_transcript_from_session()
        self._sync_busy_to_current_session()
        self._update_info_panel()
        self._append_notice(f"Using armory {path}")
        src_count = self.session.source_file_count or 0
        if src_count:
            self._append_notice(f"Loaded {src_count} file(s).")

    def _handle_armory_key(self: _ArmoryHost, event: events.Key) -> bool:
        composer = self.query_one("#composer", Input)
        if event.key == "escape":
            if self._armory_creating:
                self._armory_creating = False
                composer.value = ""
                composer.placeholder = "Filter armory paths..."
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
        if event.key == "n" and self._armory_mode != "open":
            self._start_inline_create()
            event.prevent_default()
            event.stop()
            return True
        return False
