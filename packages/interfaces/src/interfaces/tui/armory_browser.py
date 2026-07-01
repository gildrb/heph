"""Armory discovery and validation helpers for the TUI inline armory surface."""

from __future__ import annotations

import os
from pathlib import Path

from harness.armory.search import (
    MAX_RECENT_ARMORIES,
    ArmoryEntry,
    load_recent_armory_entries,
    load_remembered_armory_entries,
)
from harness.armory.storage import has_marker
from harness.matching import ranked_matches
from harness.materials import count_material_files

from interfaces.tui.display_text import label_value_line
from interfaces.tui.startup_discovery import discover_available_armories

_NEW_ARMORY_LABEL = label_value_line("create", "new")
_DIR_PREFIX = ""
_ARMORY_BADGE = ""
_RECENT_PREFIX = ""
_RECENT_HEADING = label_value_line("group", "recent")
_ALL_HEADING = label_value_line("group", "all")
_EMPTY_RECENT_LABEL = label_value_line("state", "no recent")
_EMPTY_ALL_LABEL = label_value_line("state", "none found")
_DEFAULT_ARMORY_HOME_ENV = "HARNESS_ARMORY_HOME"


def _list_entries(path: Path) -> list[Path]:
    try:
        entries = sorted(path.iterdir())
    except OSError:
        return []
    result: list[Path] = []
    for entry in entries:
        if entry.name.startswith("."):
            continue
        if entry.is_dir():
            result.append(entry)
    return result


def _is_armory(path: Path) -> bool:
    try:
        return has_marker(path)
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
        recent = load_remembered_armory_entries()
    for remembered in recent:
        if len(entries) >= MAX_RECENT_ARMORIES:
            break
        if entry := _recent_entry(remembered):
            entries.append(entry)
    return entries


def _recent_entry(remembered: ArmoryEntry) -> _DirEntry | None:
    path = _resolved_armory_home_child(remembered.path)
    if not remembered.valid or path is None:
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
    all_entries = [_DirEntry(_NEW_ARMORY_LABEL, is_create=True), *child_entries]
    entries.extend(
        _entry_section(
            _ALL_HEADING,
            all_entries if allow_create else child_entries,
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
        return "\n".join(
            (
                label_value_line("state", "missing"),
                label_value_line("action", "locate with /armory"),
                label_value_line("path", path),
            )
        )
    if not _is_armory(path):
        return "\n".join(
            (
                label_value_line("state", "folder"),
                label_value_line("action", "initialize before using"),
                label_value_line("path", path),
            )
        )
    material_count = count_material_files(path)
    return "\n".join(
        (
            label_value_line("state", "valid"),
            label_value_line("files", material_count),
            label_value_line("materials", "materials/"),
            label_value_line("state dir", ".harness/"),
            label_value_line("path", path),
        )
    )
