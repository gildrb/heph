# ty: ignore
from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from hephaistos.armory.search import add_known_armory
from hephaistos.armory.storage import ArmoryError, initialize
from hephaistos.armory.storage import validate as _validate_armory
from hephaistos.tui.armory_browser import (
    _creation_parent_error,
    _DirEntry,
    armory_detail,
    build_entries,
    build_parent_entries,
    file_detail,
    new_armory_path,
)

try:
    from textual.widgets import Input, OptionList, RichLog, Static
except ImportError:
    Input = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]
    OptionList = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]
    RichLog = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]
    Static = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]

if TYPE_CHECKING:
    from textual import events


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
    return "Usage: /armory [open|create]\nBrowse, open, or create a local study armory."


class TuiArmoryMixin:
    def _handle_armory_browser(self, value: str) -> None:
        mode = _armory_command_mode(value)
        composer = self.query_one("#composer", Input)
        if mode is None:
            self._append_error(_armory_usage_message())
            composer.focus()
            return
        self._open_armory_inline(mode)

    def _open_armory_inline(self, mode: str) -> None:
        self._armory_inline_active = True
        if self.session.armory_path is not None:
            self._armory_current = self.session.armory_path
        self._armory_filter = ""
        self._armory_mode = mode
        self._armory_creating = mode == "create"
        self.query_one("#transcript", RichLog).add_class("hidden-for-armory")
        self.query_one("#armory-inline").add_class("active")
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

    def _close_armory_inline(self) -> None:
        self._armory_inline_active = False
        self._armory_filter = ""
        self._armory_creating = False
        self._armory_mode = "manage"
        self.query_one("#transcript", RichLog).remove_class("hidden-for-armory")
        self.query_one("#armory-inline").remove_class("active")
        composer = self.query_one("#composer", Input)
        composer.value = ""
        composer.placeholder = 'Ask anything... "What do I need to study next?"'
        self._refresh_footer_hints()
        composer.focus()
        self.set_focus(composer)

    def _refresh_armory_inline(self, *, mode: str = "manage") -> None:
        current = self.query_one("#armory-current-inline", OptionList)
        previous_key = self._armory_selection_key()
        self._armory_entries = build_entries(
            self._armory_current,
            allow_create=self._armory_mode in ("manage", "create"),
            filter_query=self._armory_filter,
            show_places=True,
        )
        self._armory_parent_entries = build_parent_entries(self._armory_current)
        header = self.query_one("#armory-header", Static)
        mode_hint = (
            "new armory · enter create · esc cancel"
            if self._armory_creating
            else "arrows navigate · enter/right open · c choose · n new · esc close"
        )
        filter_hint = f" · filter: {self._armory_filter}" if self._armory_filter else ""
        count_hint = f" · {len(self._armory_entries)} item(s)"
        header.update(f"armory · {self._armory_current}{filter_hint}{count_hint}\n{mode_hint}")
        parent = self.query_one("#armory-parent-inline", OptionList)
        parent.clear_options()
        for label, _path in self._armory_parent_entries:
            parent.add_option(label)
        current.clear_options()
        for entry in self._armory_entries:
            current.add_option(entry.label)
        current.highlighted = self._armory_index_for_key(previous_key)
        if current.highlighted is None and self._armory_entries:
            current.highlighted = 0
        self._update_armory_preview()

    def _armory_selection_key(self) -> tuple[str, str] | None:
        entry = self._armory_highlighted_entry()
        if entry is None:
            return None
        if entry.path is not None:
            return ("path", str(entry.path))
        if entry.is_parent:
            return ("parent", entry.label)
        if entry.is_create:
            return ("create", entry.label)
        return ("label", entry.label)

    def _armory_index_for_key(self, key: tuple[str, str] | None) -> int | None:
        if key is None:
            return None
        for index, entry in enumerate(self._armory_entries):
            if entry.path is not None and key == ("path", str(entry.path)):
                return index
            if entry.path is None and key == ("label", entry.label):
                return index
            if entry.is_parent and key == ("parent", entry.label):
                return index
            if entry.is_create and key == ("create", entry.label):
                return index
        return None

    def _armory_highlighted_entry(self) -> _DirEntry | None:
        current = self.query_one("#armory-current-inline", OptionList)
        idx = current.highlighted
        if idx is None or idx < 0 or idx >= len(self._armory_entries):
            return None
        return self._armory_entries[idx]

    def _update_armory_preview(self) -> None:
        preview = self.query_one("#armory-preview-inline", Static)
        entry = self._armory_highlighted_entry()
        if entry is None:
            if self._armory_filter:
                preview.update(
                    f"No matches\n\nFilter: {self._armory_filter}\n\nEsc clears the filter."
                )
            else:
                preview.update("No selection")
            return
        if entry.path is None:
            preview.update(entry.label or "")
            return
        if entry.is_file:
            preview.update(file_detail(entry.path))
        else:
            preview.update(armory_detail(entry.path))

    def _move_armory_highlight(self, offset: int) -> None:
        if not self._armory_entries:
            return
        current = self.query_one("#armory-current-inline", OptionList)
        highlighted = current.highlighted or 0
        current.highlighted = (highlighted + offset) % len(self._armory_entries)
        self._update_armory_preview()

    def _armory_open_highlighted(self) -> None:
        entry = self._armory_highlighted_entry()
        if entry is None or not entry.label:
            return
        if entry.is_create:
            self._start_inline_create()
            return
        if entry.is_parent:
            parent = self._armory_current.parent
            if parent != self._armory_current:
                self._armory_current = parent
            return
        if entry.path is not None and entry.path.is_dir() and not entry.is_recent:
            self._armory_current = entry.path
            return
        if entry.path is not None:
            self._open_selected_armory(entry.path)

    def _start_inline_create(self) -> None:
        self._armory_creating = True
        self._armory_mode = "create"
        composer = self.query_one("#composer", Input)
        composer.value = ""
        composer.placeholder = "Module or topic name..."
        self._refresh_armory_inline()
        self._refresh_footer_hints()
        composer.focus()

    def _create_inline_armory(self, name: str) -> None:
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
        self._append_notice(f"Add study files to ~/.armories/{armory_path.name}/materials/")

    def _open_selected_armory(self, path: Path) -> None:
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
        self.session = tui_module.start_fresh_session(self.session, path)
        if self.session is previous:
            self.query_one("#armory-error-inline", Static).update(f"Could not open armory: {path}")
            return
        self._close_armory_inline()
        self._refresh_status("ready")
        self._focused_msg_index = None
        self._update_info_panel()
        self._append_notice(f"Using armory {path}")
        src_count = self.session.source_file_count or 0
        if src_count:
            self._append_notice(f"Loaded {src_count} file(s).")

    def _handle_armory_key(self, event: events.Key) -> bool:
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
        if event.key in ("left", "h"):
            parent = self._armory_current.parent
            if parent != self._armory_current:
                self._armory_current = parent
                self._armory_filter = ""
                composer.value = ""
                self._refresh_armory_inline()
            event.prevent_default()
            event.stop()
            return True
        if event.key in ("right", "l"):
            if self._armory_creating:
                return False
            composer.value = ""
            self._armory_filter = ""
            self._armory_open_highlighted()
            self._refresh_armory_inline()
            event.prevent_default()
            event.stop()
            return True
        if event.key == "c":
            self._open_selected_armory(self._armory_current)
            event.prevent_default()
            event.stop()
            return True
        if event.key == "n" and self._armory_mode != "open":
            self._start_inline_create()
            event.prevent_default()
            event.stop()
            return True
        return False
