# pylint: disable=duplicate-code
"""Inline Textual armory selector screen.

A ModalScreen that lists recent armories and all available armories under the
configured armory home.  The current column shows selectable armory entries and
the preview pane shows metadata.

All interaction is keyboard-first: arrows or j/k move, enter opens the selected
armory, n creates a new armory, / focuses the fuzzy filter, and escape/q
cancels.

All Textual imports are guarded so the module can be imported safely in
environments where Textual is not installed.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import ClassVar

from hephaion.armory.search import (
    MAX_RECENT_ARMORIES,
    KnownArmory,
    load_known_armory_entries,
    load_recent_armory_entries,
)
from hephaion.armory.storage import MARKER_FILE, ArmoryError, initialize
from hephaion.matching import ranked_matches
from hephaion.materials import count_material_files
from hephaion.terminal import Theme, current_palette
from hephaion.tui.startup_discovery import discover_available_armories
from hephaion.tui.transparent import transparent_strip

try:
    from textual import events
    from textual.app import ComposeResult
    from textual.binding import Binding
    from textual.containers import Horizontal, Vertical
    from textual.screen import ModalScreen
    from textual.strip import Strip
    from textual.widgets import Input, OptionList, Static
except ImportError:
    events = None  # ty:ignore[invalid-assignment]
    ComposeResult = None  # ty:ignore[invalid-assignment]
    Binding = None  # ty:ignore[invalid-assignment]
    Horizontal = None  # ty:ignore[invalid-assignment]
    Vertical = None  # ty:ignore[invalid-assignment]
    ModalScreen = object  # ty:ignore[invalid-assignment]
    Strip = None  # ty:ignore[invalid-assignment]
    Input = None  # ty:ignore[invalid-assignment]
    OptionList = None  # ty:ignore[invalid-assignment]
    Static = None  # ty:ignore[invalid-assignment]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_NEW_ARMORY_LABEL = "+ new"
_DIR_PREFIX = "  "
_ARMORY_BADGE = ""
_RECENT_PREFIX = "  "
_RECENT_HEADING = "recent"
_ALL_HEADING = "all"
_EMPTY_RECENT_LABEL = "  no recent items"
_EMPTY_ALL_LABEL = "  none found"
_PREVIEW_COLUMN_WIDTH = 38
_DEFAULT_ARMORY_HOME_ENV = "HEPHAION_ARMORY_HOME"
_BROWSER_HINT = "arrows navigate  enter open  n new  / filter  esc cancel"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _list_entries(path: Path) -> list[Path]:
    try:
        entries = sorted(path.iterdir())
    except OSError:
        return []
    result: list[Path] = []
    for e in entries:
        if e.name.startswith("."):
            continue
        if e.is_dir():
            result.append(e)
    return result


def _is_armory(path: Path) -> bool:
    try:
        return (path / MARKER_FILE).is_file()
    except OSError:
        return False


def _is_writable_directory(path: Path) -> bool:
    return path.exists() and path.is_dir() and os.access(path, os.W_OK | os.X_OK)


def default_armory_home() -> Path:
    configured = os.environ.get(_DEFAULT_ARMORY_HOME_ENV, "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / ".armories").resolve()


def _is_within_armory_home(path: Path) -> bool:
    try:
        path.expanduser().resolve(strict=False).relative_to(default_armory_home())
    except (OSError, RuntimeError, ValueError):
        return False
    return True


def _resolved_armory_home_child(path: Path) -> Path | None:
    resolved = path.expanduser().resolve(strict=False)
    return resolved if _is_within_armory_home(resolved) else None


def _existing_armory_home_dir(path: Path) -> Path | None:
    resolved = _resolved_armory_home_child(path)
    if resolved is None or not resolved.exists() or not resolved.is_dir():
        return None
    return resolved


def _creation_parent_error(path: Path) -> str | None:
    if not _is_within_armory_home(path):
        return (
            f"Armories can only be created in the armories directory ({default_armory_home()}). "
            f"Current location: {path}"
        )

    if path.exists():
        return _existing_creation_target_error(path)
    if not _has_writable_parent(path):
        return f"Cannot create an armory here because this folder is not writable: {path}"
    return None


def _existing_creation_target_error(path: Path) -> str | None:
    if not path.is_dir():
        return f"Cannot create an armory here because this is not a folder: {path}"
    if not _is_writable_directory(path):
        return f"Cannot create an armory in a read-only folder: {path}"
    return None


def _has_writable_parent(path: Path) -> bool:
    return path.parent != path and _is_writable_directory(path.parent)


def new_armory_path(parent: Path, name: str) -> tuple[Path | None, str | None]:
    candidate = Path(name)
    if error := _new_armory_name_error(candidate):
        return None, error
    path = parent / candidate.name
    if path.exists():
        return None, f"A folder named '{candidate.name}' already exists. Choose another name."
    return path, None


def _new_armory_name_error(candidate: Path) -> str:
    if candidate.is_absolute() or ".." in candidate.parts:
        return "Armory name must stay inside the selected folder."
    if len(candidate.parts) != 1:
        return "Armory name must be a single folder name."
    if not candidate.name:
        return "Armory name is required."
    return ""


def _default_start_path(start: Path | None) -> Path:
    if start is not None and _is_within_armory_home(start):
        return start.expanduser().resolve(strict=False)
    return default_armory_home()


# ---------------------------------------------------------------------------
# Entry wrapper
# ---------------------------------------------------------------------------


class _DirEntry:
    __slots__ = (
        "is_create",
        "is_place",
        "is_recent",
        "is_section",
        "label",
        "path",
    )

    def __init__(
        self,
        label: str,
        path: Path | None = None,
        *,
        is_create: bool = False,
        is_recent: bool = False,
        is_place: bool = False,
        is_section: bool = False,
    ) -> None:
        self.label = label
        self.path = path
        self.is_create = is_create
        self.is_recent = is_recent
        self.is_place = is_place
        self.is_section = is_section


def _place_entries() -> list[_DirEntry]:
    candidates = (
        ("armories", default_armory_home()),
        ("cwd", Path.cwd()),
        ("desktop", Path.home() / "Desktop"),
        ("documents", Path.home() / "Documents"),
        ("downloads", Path.home() / "Downloads"),
    )
    entries: list[_DirEntry] = []
    seen: set[Path] = set()
    for label, path in candidates:
        resolved = _existing_armory_home_dir(path)
        if resolved is None or resolved in seen:
            continue
        seen.add(resolved)
        entries.append(_DirEntry(f"{label}  {resolved}", path=resolved, is_place=True))
    return entries


def _recent_entries() -> list[_DirEntry]:
    discover_available_armories()
    entries: list[_DirEntry] = []
    recent = load_recent_armory_entries()
    if not recent:
        recent = load_known_armory_entries()
    for known in recent:
        if len(entries) >= MAX_RECENT_ARMORIES:
            break
        if entry := _recent_entry(known):
            entries.append(entry)
    return entries


def _recent_entry(known: KnownArmory) -> _DirEntry | None:
    path = _resolved_armory_home_child(known.path)
    if not known.valid or path is None:
        return None
    return _DirEntry(
        f"{_RECENT_PREFIX}{path.name}{_ARMORY_BADGE}",
        path=path,
        is_recent=True,
    )


def _available_armory_entries() -> list[_DirEntry]:
    armories = discover_available_armories()
    child_entries = _discovered_armory_entries(armories)
    if child_entries:
        return child_entries
    return _armory_home_child_entries()


def _discovered_armory_entries(armories: list[Path]) -> list[_DirEntry]:
    return [
        _DirEntry(f"{_DIR_PREFIX}{path.name}{_ARMORY_BADGE}", path=path)
        for raw_path in armories
        if (path := _resolved_armory_home_child(raw_path)) is not None
    ]


def _armory_home_child_entries() -> list[_DirEntry]:
    return [
        _DirEntry(
            f"{_DIR_PREFIX}{child.name}{_ARMORY_BADGE if _is_armory(child) else ''}",
            path=child,
        )
        for child in _list_entries(default_armory_home())
        if _is_within_armory_home(child)
    ]


def build_entries(
    allow_create: bool,
    *,
    filter_query: str = "",
    show_places: bool = False,
) -> list[_DirEntry]:
    place_entries = _place_entries() if show_places and not filter_query.strip() else []
    recent_entries = _recent_entries()
    child_entries = _available_armory_entries()

    if filter_query.strip():
        return _filtered_entries(
            filter_query,
            _deduped_path_entries([*child_entries, *recent_entries]),
        )

    recent_entries, child_entries = _dedupe_recent_from_all_entries(
        recent_entries,
        child_entries,
    )

    return _sectioned_entries(
        place_entries,
        recent_entries,
        child_entries,
        allow_create=allow_create,
    )


def _filtered_entries(filter_query: str, entries: list[_DirEntry]) -> list[_DirEntry]:
    matches = ranked_matches(
        filter_query,
        entries,
        key=lambda entry: entry.label.strip(),
        limit=50,
        min_score=30.0,
    )
    return [match.value for match in matches]


def _dedupe_recent_from_all_entries(
    recent_entries: list[_DirEntry],
    child_entries: list[_DirEntry],
) -> tuple[list[_DirEntry], list[_DirEntry]]:
    recent_path_keys: set[Path] = set()
    for entry in recent_entries:
        if entry.path is None:
            continue
        path_key = _entry_path_key(entry.path)
        if path_key is not None:
            recent_path_keys.add(path_key)
    child_entries = [
        entry
        for entry in child_entries
        if entry.path is None or _entry_path_key(entry.path) not in recent_path_keys
    ]
    return recent_entries, child_entries


def _deduped_path_entries(entries: list[_DirEntry]) -> list[_DirEntry]:
    deduped: list[_DirEntry] = []
    seen: set[Path] = set()
    for entry in entries:
        if entry.path is None:
            deduped.append(entry)
            continue
        path_key = _entry_path_key(entry.path)
        if path_key is None or path_key in seen:
            continue
        seen.add(path_key)
        deduped.append(entry)
    return deduped


def _entry_path_key(path: Path) -> Path | None:
    try:
        return path.expanduser().resolve(strict=False)
    except (OSError, RuntimeError):
        return None


def _sectioned_entries(
    place_entries: list[_DirEntry],
    recent_entries: list[_DirEntry],
    child_entries: list[_DirEntry],
    *,
    allow_create: bool,
) -> list[_DirEntry]:
    entries: list[_DirEntry] = []
    entries.extend(place_entries)
    if entries:
        entries.append(_DirEntry(""))
    entries.extend(_entry_section(_RECENT_HEADING, recent_entries, _EMPTY_RECENT_LABEL))
    if entries:
        entries.append(_DirEntry(""))
    entries.extend(
        _entry_section(
            _ALL_HEADING,
            [_DirEntry(_NEW_ARMORY_LABEL, is_create=True), *child_entries]
            if allow_create
            else child_entries,
            _EMPTY_ALL_LABEL,
        )
    )
    return entries


def _entry_section(
    heading: str,
    entries: list[_DirEntry],
    empty_label: str,
) -> list[_DirEntry]:
    if entries:
        return [_DirEntry(heading, is_section=True), *entries]
    return [_DirEntry(heading, is_section=True), _DirEntry(empty_label, is_section=True)]


def armory_detail(path: Path) -> str:
    if not path.exists():
        return (
            f"{path.name}\n\n"
            "missing recent armory\n"
            "locate it with open/create or remove later\n\n"
            f"{path}"
        )
    if not _is_armory(path):
        return f"{path.name}\n\nfolder\nchoose only if initialized\n\n{path}"
    material_count = count_material_files(path)
    return (
        f"{path.name}\n\n"
        "valid armory\n"
        f"{material_count} material file{'s' if material_count != 1 else ''}\n\n"
        "User files: materials/\n"
        "Internal state: .hephaion/\n\n"
        f"{path}"
    )


def _entry_preview(entry: _DirEntry | None) -> str:
    if entry is None:
        return "No selection"
    preview = _entry_preview_renderer(entry)
    return preview(entry) if preview is not None else ""


def _entry_preview_renderer(entry: _DirEntry) -> Callable[[_DirEntry], str] | None:
    if not entry.label:
        return None
    if entry.is_place:
        return _place_entry_preview
    if entry.is_create:
        return _new_armory_entry_preview
    if entry.path is not None:
        return _armory_entry_preview
    return None


def _place_entry_preview(entry: _DirEntry) -> str:
    return f"Place\n\nJump to:\n{entry.path}"


def _new_armory_entry_preview(_entry: _DirEntry) -> str:
    return (
        "New armory\n\n"
        "What document set are you working on?\n"
        "Type the name to create an armory.\n\n"
        "Armories are saved locally in ~/.armories/\n"
        "Add documents to ~/.armories/<name>/materials/"
    )


def _armory_entry_preview(entry: _DirEntry) -> str:
    if entry.path is None:
        return ""
    return armory_detail(entry.path)


def _selectable_entry(entry: _DirEntry) -> bool:
    return entry.path is not None or entry.is_create


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------


def _armory_browser_css(p: Theme) -> str:
    """Generate CSS from the active theme palette."""
    bg = p.bg_surface
    border_color = p.border_subtle
    text_color = p.text_primary
    dim_color = p.text_muted
    emphasis_color = p.text_primary
    return f"""
ArmoryBrowserScreen {{
    align: center middle;
    background: {p.bg_app};
    background-tint: {p.bg_app};
}}
#armory-dialog {{
    width: 112;
    max-width: 96%;
    height: 34;
    max-height: 88%;
    padding: 1 2;
    background: {bg};
    background-tint: {p.bg_app};
    border: none;
    color: {text_color};
}}
#armory-title {{
    text-style: bold;
    color: {emphasis_color};
    width: 100%;
    margin-bottom: 0;
}}
#armory-path {{
    color: {dim_color};
    width: 100%;
    margin-bottom: 1;
}}
#armory-filter-container {{
    height: auto;
    width: 100%;
    margin-bottom: 0;
    display: none;
    background: {bg};
}}
#armory-filter-container.active {{
    display: block;
}}
#armory-filter {{
    height: 1;
    width: 100%;
    background: {bg};
    color: {text_color};
    border: none;
}}
#armory-columns {{
    layout: horizontal;
    height: 1fr;
    width: 100%;
}}
#armory-current-col {{
    width: 1fr;
    height: 100%;
    background: {bg};
    border: none;
    padding: 0 1;
    color: {text_color};
    scrollbar-size: 0 0;
}}
#armory-current-col > .option-list--option {{
    background: {bg};
    color: {text_color};
    padding: 0;
}}
#armory-current-col > .option-list--option-highlighted {{
    background: {bg};
    color: {text_color};
    padding: 0;
}}
#armory-current-col:focus > .option-list--option-highlighted {{
    background: {bg};
    color: {text_color};
    padding: 0;
}}
#armory-preview {{
    width: {_PREVIEW_COLUMN_WIDTH};
    height: 100%;
    padding: 0 1;
    border-left: solid {border_color};
    color: {dim_color};
}}
#armory-error {{
    color: {p.status_error_text};
    width: 100%;
    margin-top: 0;
}}
#armory-hint {{
    color: {dim_color};
    width: 100%;
    margin-top: 0;
}}
#armory-new-input-container {{
    height: auto;
    width: 100%;
    padding: 0 1;
    display: none;
    background: {bg};
}}
#armory-new-input-container.active {{
    display: block;
}}
#armory-new-input {{
    height: 1;
    width: 100%;
    background: {bg};
    color: {text_color};
    border: none;
}}
"""


# ---------------------------------------------------------------------------
# Screen
# ---------------------------------------------------------------------------


class ArmoryBrowserScreen(ModalScreen[Path | None]):
    """Modal armory selector.

    Lists recent armories and all available armories. Keyboard-first interaction
    uses an OptionList widget. Returns the chosen *Path* when the user picks an
    armory, or *None* when cancelled.
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("escape", "cancel", "Cancel"),
        Binding("q", "cancel", "Cancel", show=False),
        Binding("n", "new_armory", "New"),
        Binding("slash", "start_filter", "Filter", show=False),
        Binding("enter", "activate", "Open", show=False),
    ]

    def __init__(
        self,
        start: Path | None = None,
        *,
        allow_create: bool = True,
        title: str = "Armory",
    ) -> None:
        super().__init__()
        self._current = _default_start_path(start)
        self._allow_create = allow_create
        self._title = title
        self._creating = False
        self._filtering = False
        self._filter_query = ""
        self._entries: list[_DirEntry] = []
        self.CSS = _armory_browser_css(current_palette())  # ty:ignore[invalid-attribute-access]

    # -----------------------------------------------------------------------
    # Compose
    # -----------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        p = current_palette()
        title = f"[bold {p.text_primary}]{self._title}[/bold {p.text_primary}]"
        with Vertical(id="armory-dialog"):
            yield Static(title, id="armory-title", markup=True)
            yield Static("", id="armory-path")
            with Vertical(id="armory-filter-container"):
                yield Input(
                    placeholder="Filter entries...",
                    id="armory-filter",
                )
            with Horizontal(id="armory-columns"):
                yield OptionList(id="armory-current-col")
                yield Static("", id="armory-preview")
            with Vertical(id="armory-new-input-container"):
                yield Input(
                    placeholder="Armory name...",
                    id="armory-new-input",
                )
            yield Static("", id="armory-error")
            yield Static(_BROWSER_HINT, id="armory-hint")

    def on_mount(self) -> None:
        self._refresh()
        self._focus_current_col()

    def render_line(self, y: int) -> Strip:
        return transparent_strip(super().render_line(y), self.size.width)

    def on_app_focus(self, event: events.AppFocus) -> None:
        self._focus_current_col()
        event.stop()

    def on_click(self, event: events.Click) -> None:
        self._focus_current_col()
        event.stop()

    # -----------------------------------------------------------------------
    # Focus helpers
    # -----------------------------------------------------------------------

    def _focus_current_col(self) -> None:
        ol = self.query_one("#armory-current-col", OptionList)
        ol.focus()

    # -----------------------------------------------------------------------
    # Refresh / rendering
    # -----------------------------------------------------------------------

    def _refresh(self) -> None:
        self._set_error("")
        if not _is_within_armory_home(self._current):
            self._current = default_armory_home()
        self._entries = build_entries(
            self._allow_create,
            filter_query=self._filter_query,
            show_places=True,
        )

        path_widget = self.query_one("#armory-path", Static)
        path_widget.update(str(self._current))

        cur_ol = self.query_one("#armory-current-col", OptionList)
        cur_ol.clear_options()
        for entry in self._entries:
            cur_ol.add_option(entry.label)
        cur_ol.highlighted = self._first_selectable_index()

        self._update_preview()

    def _set_error(self, message: str) -> None:
        error = self.query_one("#armory-error", Static)
        error.update(message)

    def _set_hint(self, message: str) -> None:
        hint = self.query_one("#armory-hint", Static)
        hint.update(message)

    def _set_input_panel_active(self, container_id: str, *, active: bool) -> None:
        container = self.query_one(container_id, Vertical)
        if active:
            container.add_class("active")
        else:
            container.remove_class("active")

    def _update_preview(self) -> None:
        preview = self.query_one("#armory-preview", Static)
        preview.update(_entry_preview(self._highlighted_entry()))

    def _first_selectable_index(self) -> int | None:
        for index, entry in enumerate(self._entries):
            if _selectable_entry(entry):
                return index
        return None

    # -----------------------------------------------------------------------
    # Entry access
    # -----------------------------------------------------------------------

    def _highlighted_entry(self) -> _DirEntry | None:
        ol = self.query_one("#armory-current-col", OptionList)
        idx = ol.highlighted
        if idx is None or idx < 0 or idx >= len(self._entries):
            return None
        return self._entries[idx]

    # -----------------------------------------------------------------------
    # Navigation
    # -----------------------------------------------------------------------

    def _navigate_into(self, entry: _DirEntry) -> None:
        if not entry.label:
            return
        if entry.is_create:
            self._start_new_armory()
            return
        if entry.path is not None:
            self._open_entry_path(entry.path)

    def _open_entry_path(self, path: Path) -> None:
        if not _is_within_armory_home(path):
            self._set_error(f"Cannot navigate outside armory home: {path}")
            return
        if not path.exists():
            self._set_error(f"Missing armory: {path}")
            return
        self.dismiss(path)

    def _move_highlight(self, offset: int) -> None:
        if not self._entries:
            return
        ol = self.query_one("#armory-current-col", OptionList)
        current = ol.highlighted
        if current is None:
            current = -1 if offset > 0 else 0
        if (index := self._next_selectable_index(current, offset)) is not None:
            ol.highlighted = index
        self._update_preview()

    def _next_selectable_index(self, current: int, offset: int) -> int | None:
        for step in range(1, len(self._entries) + 1):
            index = (current + (offset * step)) % len(self._entries)
            if _selectable_entry(self._entries[index]):
                return index
        return None

    # -----------------------------------------------------------------------
    # Actions (bound keys)
    # -----------------------------------------------------------------------

    def action_activate(self) -> None:
        if self._creating or self._filtering:
            return
        entry = self._highlighted_entry()
        if entry is not None:
            self._navigate_into(entry)

    def action_cancel(self) -> None:
        if self._filtering:
            self._stop_filter()
            return
        if self._creating:
            self._stop_new_armory()
            return
        self.dismiss(None)

    def action_new_armory(self) -> None:
        if self._creating or self._filtering:
            return
        if self._allow_create:
            self._start_new_armory()

    def action_start_filter(self) -> None:
        if self._creating or self._filtering:
            return
        self._start_filter()

    # -----------------------------------------------------------------------
    # Filter
    # -----------------------------------------------------------------------

    def _start_filter(self) -> None:
        self._filtering = True
        self._set_input_panel_active("#armory-filter-container", active=True)
        inp = self.query_one("#armory-filter", Input)
        inp.value = self._filter_query
        inp.focus()
        self._set_hint("type to filter  enter accept  esc cancel")

    def _stop_filter(self) -> None:
        self._filtering = False
        self._set_input_panel_active("#armory-filter-container", active=False)
        self._set_hint(_BROWSER_HINT)
        self._focus_current_col()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "armory-filter":
            self._filter_query = event.value
            self._refresh()
            return
        if event.input.id == "armory-new-input":
            return

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "armory-filter":
            event.stop()
            self._stop_filter()
            return
        if event.input.id != "armory-new-input":
            return
        event.stop()
        self._submit_new_armory(event.value)

    def _submit_new_armory(self, value: str) -> None:
        name = value.strip()
        if not name:
            self._stop_new_armory()
            return
        if armory_path := self._validated_new_armory_path(name):
            self._create_new_armory(armory_path)

    def _validated_new_armory_path(self, name: str) -> Path | None:
        if parent_error := _creation_parent_error(self._current):
            self._set_error(parent_error)
            return None
        armory_path, name_error = new_armory_path(self._current, name)
        if name_error is not None or armory_path is None:
            self._set_error(name_error or "Invalid armory name.")
            return None
        return armory_path

    def _create_new_armory(self, armory_path: Path) -> None:
        try:
            initialize(armory_path)
        except (ArmoryError, OSError) as exc:
            self._set_error(f"Could not create armory: {exc}")
            return
        self.dismiss(armory_path)

    # -----------------------------------------------------------------------
    # New armory creation
    # -----------------------------------------------------------------------

    def _start_new_armory(self) -> None:
        self._creating = True
        self._set_input_panel_active("#armory-new-input-container", active=True)
        inp = self.query_one("#armory-new-input", Input)
        inp.value = ""
        inp.focus()
        self._set_hint("enter confirm  esc cancel")

    def _stop_new_armory(self) -> None:
        self._creating = False
        self._set_input_panel_active("#armory-new-input-container", active=False)
        self._set_hint(_BROWSER_HINT)
        self._focus_current_col()

    # -----------------------------------------------------------------------
    # OptionList events
    # -----------------------------------------------------------------------

    def on_option_list_option_selected(
        self,
        event: OptionList.OptionSelected,
    ) -> None:
        if event.option_list.id == "armory-current-col":
            event.stop()
            idx = event.option_list.highlighted
            if idx is not None and 0 <= idx < len(self._entries):
                self._navigate_into(self._entries[idx])
            return

    # -----------------------------------------------------------------------
    # Key handling
    # -----------------------------------------------------------------------

    def on_key(self, event: events.Key) -> None:
        if self._handle_active_input_key(event):
            return
        if callback := self._key_callback(event.key):
            self._handled_key(event, callback)

    def _key_callback(self, key: str) -> Callable[[], None] | None:
        if key in ("up", "k"):
            return lambda: self._move_highlight(-1)
        if key in ("down", "j"):
            return lambda: self._move_highlight(1)
        return {
            "n": self.action_new_armory,
            "/": self.action_start_filter,
            "escape": self.action_cancel,
            "q": self.action_cancel,
        }.get(key)

    def _handle_active_input_key(self, event: events.Key) -> bool:
        if self._creating:
            if event.key == "escape":
                self._handled_key(event, self._stop_new_armory)
            return True
        if self._filtering:
            if event.key == "escape":
                self._handled_key(event, self._stop_filter)
            return True
        return False

    @staticmethod
    def _handled_key(event: events.Key, callback: Callable[[], None]) -> None:
        callback()
        event.prevent_default()
        event.stop()
