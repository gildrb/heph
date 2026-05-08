# pylint: disable=duplicate-code
"""Inline Textual armory browser screen with Miller-column layout.

A ModalScreen that uses three columns — parent directory, current directory,
and a preview/detail pane — inspired by the Yazi file manager UX.  The parent
column shows the siblings of the current directory.  The current column shows
directory entries (and file entries when inside an armory).  The preview pane
shows metadata or file content snippets.

All interaction is keyboard-first: hjkl or arrows to navigate, enter to drill
into directories, c to choose the current directory as an armory, n to create
a new armory, / to focus the fuzzy filter, and escape/q to cancel.

All Textual imports are guarded so the module can be imported safely in
environments where Textual is not installed.
"""

from __future__ import annotations

import os
import stat
import time
from pathlib import Path
from typing import ClassVar

from hephaistos.armory.search import load_known_armory_entries
from hephaistos.armory.storage import MARKER_FILE, ArmoryError, initialize
from hephaistos.matching import ranked_matches
from hephaistos.materials import count_material_files
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

_PARENT_LABEL = ".."
_NEW_ARMORY_LABEL = "+ new armory"
_DIR_PREFIX = "  "
_FILE_PREFIX = "  "
_ARMORY_BADGE = "  armory"
_RECENT_PREFIX = "recent  "
_MISSING_BADGE = "  missing"
_PARENT_COLUMN_WIDTH = 24
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
    ) -> None:
        self.label = label
        self.path = path
        self.is_parent = is_parent
        self.is_create = is_create
        self.is_recent = is_recent
        self.is_missing = is_missing
        self.is_file = is_file
        self.is_place = is_place


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
    entries: list[_DirEntry] = []
    for known in load_known_armory_entries():
        if len(entries) >= 5:
            break
        if not _is_within_armory_home(known.path):
            continue
        badge = _MISSING_BADGE if known.missing else _ARMORY_BADGE
        entries.append(
            _DirEntry(
                f"{_RECENT_PREFIX}{known.path.name}{badge}",
                path=known.path,
                is_recent=True,
                is_missing=known.missing,
            )
        )
    return entries


def build_entries(
    current: Path,
    allow_create: bool,
    *,
    show_files: bool = False,
    filter_query: str = "",
    show_places: bool = False,
) -> list[_DirEntry]:
    """Build the ordered list of browser entries for the current column."""
    place_entries = _place_entries() if show_places else []
    recent_entries = _recent_entries()
    entries: list[_DirEntry] = []

    child_entries: list[_DirEntry] = []
    children = (
        _list_entries(current, show_files=show_files) if _is_within_armory_home(current) else []
    )
    for child in children:
        if not _is_within_armory_home(child):
            continue

        is_file = child.is_file()
        if is_file:
            prefix = _FILE_PREFIX
            badge = ""
        else:
            prefix = _DIR_PREFIX
            badge = _ARMORY_BADGE if _is_armory(child) else ""
        child_entries.append(
            _DirEntry(f"{prefix}{child.name}{badge}", path=child, is_file=is_file)
        )

    if filter_query.strip():
        searchable = [*place_entries, *recent_entries, *child_entries]
        matches = ranked_matches(
            filter_query,
            searchable,
            key=lambda e: e.label.strip(),
            limit=50,
            min_score=30.0,
        )
        return [m.value for m in matches]

    entries.extend(place_entries)
    if entries and recent_entries:
        entries.append(_DirEntry(""))
    entries.extend(recent_entries)
    if entries:
        entries.append(_DirEntry(""))
    entries.append(_DirEntry(_PARENT_LABEL, is_parent=True))
    if allow_create:
        entries.append(_DirEntry(_NEW_ARMORY_LABEL, is_create=True))
    entries.extend(child_entries)
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
    width: {_PARENT_COLUMN_WIDTH};
    height: 100%;
    background: transparent;
    border-right: solid {border_color};
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
    """Modal directory browser with Miller-column layout.

    Three columns: parent siblings | current directory entries | preview.
    Keyboard-first interaction using OptionList widgets.  Returns the chosen
    *Path* when the user picks a directory, or *None* when cancelled.
    """

    BINDINGS: ClassVar[list[Binding]] = [  # type: ignore[assignment]
        Binding("escape", "cancel", "Cancel"),
        Binding("q", "cancel", "Cancel", show=False),
        Binding("c", "choose", "Choose"),
        Binding("n", "new_armory", "New"),
        Binding("slash", "start_filter", "Filter", show=False),
        Binding("enter", "activate", "Open", show=False),
        Binding("right", "navigate_into", "Open", show=False),
        Binding("l", "navigate_into", "Open", show=False),
        Binding("left", "navigate_parent", "Back", show=False),
        Binding("h", "navigate_parent", "Back", show=False),
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
        self._parent_entries: list[tuple[str, Path]] = []
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
                "arrows navigate  enter/right open  c choose  n new  / filter  esc cancel",
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
        self._parent_entries = build_parent_entries(self._current)

        path_widget = self.query_one("#armory-path", Static)
        path_widget.update(str(self._current))

        # Parent column
        parent_ol = self.query_one("#armory-parent-col", OptionList)
        parent_ol.clear_options()
        for label, _path in self._parent_entries:
            parent_ol.add_option(label)

        # Current column
        cur_ol = self.query_one("#armory-current-col", OptionList)
        cur_ol.clear_options()
        for entry in self._entries:
            cur_ol.add_option(_format_entry(entry))
        if self._entries:
            cur_ol.highlighted = 0

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
            preview.update("Recent armories\n\nEnter opens a recent armory directly.")
            return
        if entry.is_parent:
            preview.update("Parent directory\n\nMove up one folder.\n\nLeft/h also navigates up.")
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

    def _navigate_parent(self) -> None:
        parent = self._current.parent
        if parent != self._current and parent.exists() and _is_within_armory_home(parent):
            self._current = parent
            self._filter_query = ""
            self._refresh()

    def _navigate_into(self, entry: _DirEntry) -> None:
        if not entry.label:
            return
        if entry.is_parent:
            self._navigate_parent()
        elif entry.is_create:
            self._start_new_armory()
        elif entry.is_recent and entry.path is not None:
            if not _is_within_armory_home(entry.path):
                self._set_error(f"Cannot navigate outside armory home: {entry.path}")
                return
            if entry.is_missing or not entry.path.exists():
                self._set_error(f"Missing armory: {entry.path}")
                return
            self.dismiss(entry.path)
        elif entry.path is not None and entry.path.is_dir():
            if not _is_within_armory_home(entry.path):
                self._set_error(f"Cannot navigate outside armory home: {entry.path}")
                return
            self._current = entry.path
            self._filter_query = ""
            self._refresh()
        elif entry.path is not None and entry.is_file:
            # Files don't navigate but could be previewed — already shown
            pass

    def _move_highlight(self, offset: int) -> None:
        if not self._entries:
            return
        ol = self.query_one("#armory-current-col", OptionList)
        current = ol.highlighted
        if current is None:
            current = 0
        ol.highlighted = (current + offset) % len(self._entries)
        self._update_preview()

    # -----------------------------------------------------------------------
    # Actions (bound keys)
    # -----------------------------------------------------------------------

    def action_activate(self) -> None:
        """Enter key: drill into directory or activate special entry."""
        if self._creating or self._filtering:
            return
        entry = self._highlighted_entry()
        if entry is not None:
            self._navigate_into(entry)

    def action_choose(self) -> None:
        """c key: choose the current directory as the armory."""
        if self._creating or self._filtering:
            return
        if not _is_within_armory_home(self._current):
            self._set_error(f"Cannot choose a folder outside armory home: {self._current}")
            return
        self.dismiss(self._current)

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

    def action_navigate_parent(self) -> None:
        """Left/h: navigate to parent directory."""
        if self._creating or self._filtering:
            return
        self._navigate_parent()

    def action_navigate_into(self) -> None:
        """Right/l: drill into the highlighted directory."""
        if self._creating or self._filtering:
            return
        entry = self._highlighted_entry()
        if entry is not None:
            self._navigate_into(entry)

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
        hint.update("arrows navigate  enter/right open  c choose  n new  / filter  esc cancel")
        self._focus_current_col()

    def _accept_filter(self) -> None:
        """Accept the current filter and return focus to the list."""
        self._filtering = False
        container = self.query_one("#armory-filter-container", Vertical)
        container.remove_class("active")
        hint = self.query_one("#armory-hint", Static)
        hint.update("arrows navigate  enter/right open  c choose  n new  / filter  esc cancel")
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
            if self._entries:
                cur_ol.highlighted = 0
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
        hint.update("arrows navigate  enter/right open  c choose  n new  / filter  esc cancel")
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
        if event.option_list.id == "armory-parent-col":
            event.stop()
            idx = event.option_list.highlighted
            if idx is not None and 0 <= idx < len(self._parent_entries):
                _label, path = self._parent_entries[idx]
                if path.is_dir() and _is_within_armory_home(path):
                    self._current = path
                    self._filter_query = ""
                    self._refresh()
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

        if event.key in ("left", "h"):
            self.action_navigate_parent()
            event.prevent_default()
            event.stop()
            return

        if event.key in ("right", "l"):
            self.action_navigate_into()
            event.prevent_default()
            event.stop()
            return

        if event.key == "c":
            self.action_choose()
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
