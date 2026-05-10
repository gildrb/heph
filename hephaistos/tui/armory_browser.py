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
import stat
import time
from pathlib import Path
from typing import ClassVar

from hephaistos.armory.search import (
    MAX_RECENT_ARMORIES,
    load_known_armory_entries,
    load_recent_armory_entries,
)
from hephaistos.armory.storage import MARKER_FILE, ArmoryError, initialize
from hephaistos.matching import ranked_matches
from hephaistos.materials import count_material_files
from hephaistos.shell.startup_discovery import discover_available_armories
from hephaistos.terminal import ThemePalette, current_palette
from hephaistos.tui.transparent import transparent_strip

try:
    from textual import events
    from textual.app import ComposeResult
    from textual.binding import Binding
    from textual.containers import Horizontal, Vertical
    from textual.screen import ModalScreen
    from textual.strip import Strip
    from textual.widgets import Input, OptionList, Static
except ImportError:
    events = None  # type: ignore[assignment]  # ty:ignore[invalid-assignment]
    ComposeResult = None  # type: ignore[assignment,misc]  # ty:ignore[invalid-assignment]
    Binding = None  # type: ignore[assignment,misc]  # ty:ignore[invalid-assignment]
    Horizontal = None  # type: ignore[assignment,misc]  # ty:ignore[invalid-assignment]
    Vertical = None  # type: ignore[assignment,misc]  # ty:ignore[invalid-assignment]
    ModalScreen = object  # type: ignore[assignment,misc]  # ty:ignore[invalid-assignment]
    Strip = None  # type: ignore[assignment,misc]  # ty:ignore[invalid-assignment]
    Input = None  # type: ignore[assignment,misc]  # ty:ignore[invalid-assignment]
    OptionList = None  # type: ignore[assignment,misc]  # ty:ignore[invalid-assignment]
    Static = None  # type: ignore[assignment,misc]  # ty:ignore[invalid-assignment]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PARENT_LABEL = "all armories"
_NEW_ARMORY_LABEL = "+ new armory"
_DIR_PREFIX = "  "
_FILE_PREFIX = "  "
_ARMORY_BADGE = "  armory"
_RECENT_PREFIX = "  "
_MISSING_BADGE = "  missing"
_RECENT_HEADING = "recent armories"
_ALL_HEADING = "all armories"
_EMPTY_RECENT_LABEL = "  no recent armories"
_EMPTY_ALL_LABEL = "  no armories found"
_PARENT_COLUMN_WIDTH = 0
_PREVIEW_COLUMN_WIDTH = 38
_DEFAULT_ARMORY_HOME_ENV = "HEPHAISTOS_ARMORY_HOME"

_TEXT_PREVIEW_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".txt",
        ".md",
        ".py",
        ".js",
        ".ts",
        ".java",
        ".go",
        ".rs",
        ".c",
        ".h",
        ".cpp",
        ".toml",
        ".yaml",
        ".yml",
        ".json",
        ".csv",
        ".html",
        ".css",
        ".sh",
        ".bash",
        ".zsh",
        ".fish",
        ".r",
        ".rb",
        ".pl",
        ".lua",
        ".vim",
        ".tex",
        ".bib",
        ".rst",
        ".ini",
        ".cfg",
        ".conf",
        ".log",
        ".sql",
        ".xml",
        ".svg",
        ".tcl",
        ".m",
        ".mat",
    }
)
_PREVIEW_MAX_CHARS = 2048
_PREVIEW_MAX_LINES = 30


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _list_entries(path: Path, *, show_files: bool = False) -> list[Path]:
    """Return sorted child entries (dirs, and optionally files), skipping hidden."""
    try:
        entries = sorted(path.iterdir())
    except OSError:
        return []
    result: list[Path] = []
    for e in entries:
        if e.name.startswith("."):
            continue
        if e.is_dir() or (show_files and e.is_file()):
            result.append(e)
    return result


def _list_child_dirs(path: Path) -> list[Path]:  # ty: ignore
    """Return sorted child directories, skipping hidden ones.

    Backward-compatible wrapper kept for existing tests.
    """
    return [e for e in _list_entries(path) if e.is_dir()]


def _is_armory(path: Path) -> bool:
    try:
        return (path / MARKER_FILE).is_file()
    except OSError:
        return False


def _armory_root_from(path: Path) -> Path | None:
    """Return the armory root containing *path*, or None."""
    current = path
    for _ in range(32):
        if _is_armory(current):
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def _format_size(size: int) -> str:
    """Human-readable file size."""
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def _is_writable_directory(path: Path) -> bool:
    """Return True when *path* is a directory Hephaistos may create inside."""
    return path.exists() and path.is_dir() and os.access(path, os.W_OK | os.X_OK)


def default_armory_home() -> Path:
    """Return the default parent directory used when creating new armories."""
    configured = os.environ.get(_DEFAULT_ARMORY_HOME_ENV, "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / ".armories").resolve()


def _is_within_armory_home(path: Path) -> bool:
    """Return True when *path* resolves to the armory home or one of its descendants."""
    try:
        path.expanduser().resolve(strict=False).relative_to(default_armory_home())
    except (OSError, RuntimeError, ValueError):
        return False
    return True


def _creation_parent_error(path: Path) -> str | None:
    """Return a user-facing create error for *path*, or None when writable."""
    armory_home = default_armory_home()

    if not _is_within_armory_home(path):
        return (
            f"Armories can only be created in the armories directory ({armory_home}). "
            f"Current location: {path}"
        )

    if path.exists():
        if not path.is_dir():
            return f"Cannot create an armory here because this is not a folder: {path}"
        if not _is_writable_directory(path):
            return f"Cannot create an armory in a read-only folder: {path}"
        return None
    parent = path.parent
    if parent == path or not _is_writable_directory(parent):
        return f"Cannot create an armory here because this folder is not writable: {path}"
    return None


def new_armory_path(parent: Path, name: str) -> tuple[Path | None, str | None]:
    """Return a safe child path for a new armory name, or a user-facing error."""
    candidate = Path(name)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None, "Armory name must stay inside the selected folder."
    if len(candidate.parts) != 1:
        return None, "Armory name must be a single folder name."
    if not candidate.name:
        return None, "Armory name is required."
    path = parent / candidate.name
    if path.exists():
        return None, f"A folder named '{candidate.name}' already exists. Choose another name."
    return path, None


def _default_start_path(start: Path | None) -> Path:
    """Return a safe initial browser location."""
    if start is not None and _is_within_armory_home(start):
        return start.expanduser().resolve(strict=False)
    return default_armory_home()


def _file_preview_text(path: Path) -> str:
    """Return a short text preview for a file, or empty string."""
    suffix = path.suffix.lower()
    if suffix not in _TEXT_PREVIEW_EXTENSIONS:
        return ""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    lines = content.splitlines()
    if len(lines) > _PREVIEW_MAX_LINES:
        lines = lines[:_PREVIEW_MAX_LINES]
        lines.append("...")
    text = "\n".join(lines)
    if len(text) > _PREVIEW_MAX_CHARS:
        text = text[:_PREVIEW_MAX_CHARS] + "\n..."
    return text


# ---------------------------------------------------------------------------
# Entry wrapper
# ---------------------------------------------------------------------------


class _DirEntry:
    """Lightweight wrapper pairing a display label with a Path or action."""

    __slots__ = (
        "is_create",
        "is_file",
        "is_missing",
        "is_parent",
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
        is_parent: bool = False,
        is_create: bool = False,
        is_recent: bool = False,
        is_missing: bool = False,
        is_file: bool = False,
        is_place: bool = False,
        is_section: bool = False,
    ) -> None:
        self.label = label
        self.path = path
        self.is_parent = is_parent
        self.is_create = is_create
        self.is_recent = is_recent
        self.is_missing = is_missing
        self.is_file = is_file
        self.is_place = is_place
        self.is_section = is_section


def _place_entries() -> list[_DirEntry]:
    """Return quick navigation entries for common user locations."""
    armory_home = default_armory_home()
    candidates = (
        ("armories", armory_home),
        ("cwd", Path.cwd()),
        ("desktop", Path.home() / "Desktop"),
        ("documents", Path.home() / "Documents"),
        ("downloads", Path.home() / "Downloads"),
    )
    entries: list[_DirEntry] = []
    seen: set[Path] = set()
    for label, path in candidates:
        resolved = path.expanduser().resolve(strict=False)
        if not _is_within_armory_home(resolved):
            continue
        if resolved in seen or not resolved.exists() or not resolved.is_dir():
            continue
        seen.add(resolved)
        entries.append(_DirEntry(f"place   {label:<9} {resolved}", path=resolved, is_place=True))
    return entries


def _recent_entries() -> list[_DirEntry]:
    """Return recent armories as quick-open entries."""
    discover_available_armories()
    entries: list[_DirEntry] = []
    recent = load_recent_armory_entries()
    if not recent:
        recent = load_known_armory_entries()
    for known in recent:
        if len(entries) >= MAX_RECENT_ARMORIES:
            break
        if not known.valid:
            continue
        if not _is_within_armory_home(known.path):
            continue
        entries.append(
            _DirEntry(
                f"{_RECENT_PREFIX}{known.path.name}{_ARMORY_BADGE}",
                path=known.path,
                is_recent=True,
            )
        )
    return entries


def _available_armory_entries() -> list[_DirEntry]:
    """Return all valid armories under the configured armory home."""
    armories = discover_available_armories()
    child_entries = [
        _DirEntry(f"{_DIR_PREFIX}{path.name}{_ARMORY_BADGE}", path=path)
        for path in armories
        if _is_within_armory_home(path)
    ]
    if child_entries:
        return child_entries
    current = default_armory_home()
    children = _list_entries(current)
    return [
        _DirEntry(
            f"{_DIR_PREFIX}{child.name}{_ARMORY_BADGE if _is_armory(child) else ''}",
            path=child,
        )
        for child in children
        if _is_within_armory_home(child)
    ]


def build_entries(
    current: Path,
    allow_create: bool,
    *,
    show_files: bool = False,
    filter_query: str = "",
    show_places: bool = False,
) -> list[_DirEntry]:
    """Build the ordered armory selector entries for the current column."""
    place_entries = _place_entries() if show_places and not filter_query.strip() else []
    recent_entries = _recent_entries()
    entries: list[_DirEntry] = []
    child_entries = _available_armory_entries()

    if filter_query.strip():
        searchable = [*recent_entries, *child_entries]
        matches = ranked_matches(
            filter_query,
            searchable,
            key=lambda e: e.label.strip(),
            limit=50,
            min_score=30.0,
        )
        return [m.value for m in matches]

    entries.extend(place_entries)
    if entries:
        entries.append(_DirEntry(""))
    entries.append(_DirEntry(_RECENT_HEADING, is_section=True))
    entries.extend(recent_entries)
    if not recent_entries:
        entries.append(_DirEntry(_EMPTY_RECENT_LABEL, is_section=True))
    if entries:
        entries.append(_DirEntry(""))
    if allow_create:
        entries.append(_DirEntry(_NEW_ARMORY_LABEL, is_create=True))
    entries.append(_DirEntry(_ALL_HEADING, is_section=True))
    entries.extend(child_entries)
    if not child_entries:
        entries.append(_DirEntry(_EMPTY_ALL_LABEL, is_section=True))
    return entries


def _format_entry(entry: _DirEntry) -> str:
    """Return the display string for an OptionList option."""
    return entry.label


def build_parent_entries(current: Path) -> list[tuple[str, Path]]:
    """Build entries for the parent (left) column: siblings of *current*."""
    parent = current.parent

    if parent == current or not parent.exists():
        return []
    if not _is_within_armory_home(parent):
        return []

    try:
        siblings = sorted(parent.iterdir())
    except PermissionError:
        return []
    result: list[tuple[str, Path]] = []
    for s in siblings:
        if s.name.startswith(".") or not s.is_dir():
            continue
        if not _is_within_armory_home(s):
            continue
        badge = _ARMORY_BADGE if _is_armory(s) else ""
        marker = " > " if s == current else "   "
        result.append((f"{marker}{s.name}{badge}", s))
    return result


def armory_detail(path: Path) -> str:
    """Return the detail panel text for a directory entry."""
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
        "Internal state: .hephaistos/\n\n"
        f"{path}"
    )


def file_detail(path: Path) -> str:
    """Return the preview panel text for a file entry."""
    if not path.exists():
        return f"{path.name}\n\nfile not found\n\n{path}"
    try:
        st = path.stat()
    except OSError:
        return f"{path.name}\n\ncannot stat file\n\n{path}"

    lines: list[str] = [path.name, ""]
    lines.append(f"Size: {_format_size(st.st_size)}")

    # Permissions
    mode = stat.filemode(st.st_mode)
    lines.append(f"Mode: {mode}")

    mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime))
    lines.append(f"Modified: {mtime}")

    # Extension hint
    suffix = path.suffix.lower()
    if suffix:
        lines.append(f"Type: {suffix}")

    lines.append("")
    lines.append(str(path))

    # Text preview
    preview = _file_preview_text(path)
    if preview:
        lines.append("")
        lines.append("--- preview ---")
        lines.append(preview)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------


def _armory_browser_css(p: ThemePalette) -> str:
    """Generate CSS from the active theme palette."""
    bg = "transparent"
    border_color = "transparent"
    text_color = p.text
    dim_color = p.dim
    ember_color = p.ember
    highlight_color = p.highlight

    return f"""
ArmoryBrowserScreen {{
    align: center middle;
    background: transparent;
    background-tint: transparent;
}}
#armory-dialog {{
    width: 112;
    max-width: 96%;
    height: 34;
    max-height: 88%;
    padding: 1 2;
    background: {bg};
    background-tint: transparent;
    border: none;
    color: {text_color};
}}
#armory-title {{
    text-style: bold;
    color: {ember_color};
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
    background: transparent;
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
#armory-parent-col {{
    display: none;
    width: {_PARENT_COLUMN_WIDTH};
    height: 100%;
    background: transparent;
    border: none;
    padding: 0 1 0 0;
    color: {dim_color};
    scrollbar-size: 0 0;
}}
#armory-current-col {{
    width: 1fr;
    height: 100%;
    background: transparent;
    border: none;
    padding: 0 1;
    color: {text_color};
    scrollbar-size: 0 0;
}}
#armory-current-col > .option-list--option {{
    background: transparent;
    color: {text_color};
    padding: 0;
}}
#armory-current-col > .option-list--option-highlighted {{
    background: {highlight_color};
    color: {text_color};
    padding: 0;
}}
#armory-current-col:focus > .option-list--option-highlighted {{
    background: {highlight_color};
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
    color: {p.error};
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
    background: transparent;
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

    BINDINGS: ClassVar[list[Binding]] = [  # type: ignore[assignment]
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
        title = f"[bold {p.ember}]{self._title}[/bold {p.ember}]"
        with Vertical(id="armory-dialog"):
            yield Static(title, id="armory-title", markup=True)
            yield Static("", id="armory-path")
            with Vertical(id="armory-filter-container"):
                yield Input(
                    placeholder="Filter entries...",
                    id="armory-filter",
                )
            with Horizontal(id="armory-columns"):
                yield OptionList(id="armory-parent-col")
                yield OptionList(id="armory-current-col")
                yield Static("", id="armory-preview")
            with Vertical(id="armory-new-input-container"):
                yield Input(
                    placeholder="Armory name...",
                    id="armory-new-input",
                )
            yield Static("", id="armory-error")
            yield Static(
                "arrows navigate  enter open  n new  / filter  esc cancel",
                id="armory-hint",
            )

    def on_mount(self) -> None:
        self._refresh()
        self._focus_current_col()

    def render_line(self, y: int) -> Strip:
        """Strip Textual's synthetic black modal background in transparent themes."""
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
        show_files = self._should_show_files()
        self._entries = build_entries(
            self._current,
            self._allow_create,
            show_files=show_files,
            filter_query=self._filter_query,
            show_places=True,
        )

        path_widget = self.query_one("#armory-path", Static)
        path_widget.update(str(self._current))

        # Current column
        cur_ol = self.query_one("#armory-current-col", OptionList)
        cur_ol.clear_options()
        for entry in self._entries:
            cur_ol.add_option(_format_entry(entry))
        cur_ol.highlighted = self._first_selectable_index()

        self._update_preview()

    def _should_show_files(self) -> bool:
        """Show files when inside an armory's materials directory."""
        armory_root = _armory_root_from(self._current)
        if armory_root is None:
            return False
        try:
            self._current.relative_to(armory_root)
        except ValueError:
            return False
        return True

    def _set_error(self, message: str) -> None:
        error = self.query_one("#armory-error", Static)
        error.update(message)

    def _update_preview(self) -> None:
        preview = self.query_one("#armory-preview", Static)
        entry = self._highlighted_entry()
        if entry is None:
            preview.update("No selection")
            return
        if not entry.label:
            preview.update("")
            return
        if entry.is_place:
            preview.update(f"Place\n\nJump to:\n{entry.path}")
            return
        if entry.is_create:
            preview.update(
                "New armory\n\n"
                "What module or topic are you studying for?\n"
                "Type the name to create an armory.\n\n"
                "Armories are saved locally in ~/.armories/\n"
                "Add study materials to ~/.armories/<name>/materials/"
            )
            return
        if entry.path is None:
            preview.update("")
            return
        if entry.is_file:
            preview.update(file_detail(entry.path))
        else:
            preview.update(armory_detail(entry.path))

    def _first_selectable_index(self) -> int | None:
        for index, entry in enumerate(self._entries):
            if entry.path is not None or entry.is_create:
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
        elif entry.path is not None:
            if not _is_within_armory_home(entry.path):
                self._set_error(f"Cannot navigate outside armory home: {entry.path}")
                return
            if entry.is_missing or not entry.path.exists():
                self._set_error(f"Missing armory: {entry.path}")
                return
            self.dismiss(entry.path)

    def _move_highlight(self, offset: int) -> None:
        if not self._entries:
            return
        ol = self.query_one("#armory-current-col", OptionList)
        current = ol.highlighted
        if current is None:
            current = -1 if offset > 0 else 0
        for step in range(1, len(self._entries) + 1):
            index = (current + (offset * step)) % len(self._entries)
            entry = self._entries[index]
            if entry.path is not None or entry.is_create:
                ol.highlighted = index
                break
        self._update_preview()

    # -----------------------------------------------------------------------
    # Actions (bound keys)
    # -----------------------------------------------------------------------

    def action_activate(self) -> None:
        """Enter key: open the highlighted armory or activate special entry."""
        if self._creating or self._filtering:
            return
        entry = self._highlighted_entry()
        if entry is not None:
            self._navigate_into(entry)

    def action_cancel(self) -> None:
        """escape/q: cancel or stop creating/filtering."""
        if self._filtering:
            self._stop_filter()
            return
        if self._creating:
            self._stop_new_armory()
            return
        self.dismiss(None)

    def action_new_armory(self) -> None:
        """n key: start creating a new armory."""
        if self._creating or self._filtering:
            return
        if self._allow_create:
            self._start_new_armory()

    def action_start_filter(self) -> None:
        """Slash key: activate fuzzy filter bar."""
        if self._creating or self._filtering:
            return
        self._start_filter()

    # -----------------------------------------------------------------------
    # Filter
    # -----------------------------------------------------------------------

    def _start_filter(self) -> None:
        self._filtering = True
        container = self.query_one("#armory-filter-container", Vertical)
        container.add_class("active")
        inp = self.query_one("#armory-filter", Input)
        inp.value = self._filter_query
        inp.focus()
        hint = self.query_one("#armory-hint", Static)
        hint.update("type to filter  enter accept  esc cancel")

    def _stop_filter(self) -> None:
        self._filtering = False
        container = self.query_one("#armory-filter-container", Vertical)
        container.remove_class("active")
        hint = self.query_one("#armory-hint", Static)
        hint.update("arrows navigate  enter open  n new  / filter  esc cancel")
        self._focus_current_col()

    def _accept_filter(self) -> None:
        """Accept the current filter and return focus to the list."""
        self._filtering = False
        container = self.query_one("#armory-filter-container", Vertical)
        container.remove_class("active")
        hint = self.query_one("#armory-hint", Static)
        hint.update("arrows navigate  enter open  n new  / filter  esc cancel")
        self._focus_current_col()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "armory-filter":
            self._filter_query = event.value
            show_files = self._should_show_files()
            self._entries = build_entries(
                self._current,
                self._allow_create,
                show_files=show_files,
                filter_query=self._filter_query,
                show_places=True,
            )
            cur_ol = self.query_one("#armory-current-col", OptionList)
            cur_ol.clear_options()
            for entry in self._entries:
                cur_ol.add_option(_format_entry(entry))
            cur_ol.highlighted = self._first_selectable_index()
            self._update_preview()
            return
        if event.input.id == "armory-new-input":
            return

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "armory-filter":
            event.stop()
            self._accept_filter()
            return
        if event.input.id != "armory-new-input":
            return
        event.stop()
        name = event.value.strip()
        if not name:
            self._stop_new_armory()
            return
        parent_error = _creation_parent_error(self._current)
        if parent_error is not None:
            self._set_error(parent_error)
            return
        armory_path, name_error = new_armory_path(self._current, name)
        if name_error is not None or armory_path is None:
            self._set_error(name_error or "Invalid armory name.")
            return
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
        container = self.query_one("#armory-new-input-container", Vertical)
        container.add_class("active")
        inp = self.query_one("#armory-new-input", Input)
        inp.value = ""
        inp.focus()
        hint = self.query_one("#armory-hint", Static)
        hint.update("enter confirm  esc cancel")

    def _stop_new_armory(self) -> None:
        self._creating = False
        container = self.query_one("#armory-new-input-container", Vertical)
        container.remove_class("active")
        hint = self.query_one("#armory-hint", Static)
        hint.update("arrows navigate  enter open  n new  / filter  esc cancel")
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

    def on_key(self, event: events.Key) -> None:  # type: ignore[override]
        # When creating, only intercept escape; let the Input handle the rest.
        if self._creating:
            if event.key == "escape":
                self._stop_new_armory()
                event.prevent_default()
                event.stop()
            return

        # When filtering, only intercept escape.
        if self._filtering:
            if event.key == "escape":
                self._stop_filter()
                event.prevent_default()
                event.stop()
            return

        if event.key in ("up", "k"):
            self._move_highlight(-1)
            event.prevent_default()
            event.stop()
            return

        if event.key in ("down", "j"):
            self._move_highlight(1)
            event.prevent_default()
            event.stop()
            return

        if event.key == "n":
            self.action_new_armory()
            event.prevent_default()
            event.stop()
            return

        if event.key == "/":
            self.action_start_filter()
            event.prevent_default()
            event.stop()
            return

        if event.key in ("escape", "q"):
            self.action_cancel()
            event.prevent_default()
            event.stop()
            return
