"""Armory management commands: armory, import, index, export."""

from __future__ import annotations

import filecmp
import shlex
import shutil
from dataclasses import dataclass
from pathlib import Path

from hephaion.armory.search import (
    add_known_armory,
    load_known_armories,
    remove_known_armory,
)
from hephaion.chat.session import ChatSession, refresh_armory_sources
from hephaion.commands._base import Command, CommandResult, ensure_session
from hephaion.materials import MATERIALS_DIR, material_display_name
from hephaion.rag.index import ArmoryIndex, build_index
from hephaion.terminal import print_error, print_info, print_success

_SUPPORTED_IMPORT_SUFFIXES = frozenset(
    (
        ".bash",
        ".bib",
        ".c",
        ".cfg",
        ".cpp",
        ".csv",
        ".css",
        ".doc",
        ".docx",
        ".fish",
        ".go",
        ".graphql",
        ".h",
        ".hpp",
        ".html",
        ".ini",
        ".java",
        ".json",
        ".kt",
        ".log",
        ".md",
        ".mdown",
        ".markdown",
        ".odp",
        ".ods",
        ".odt",
        ".pdf",
        ".php",
        ".ppt",
        ".pptx",
        ".py",
        ".rb",
        ".rst",
        ".rtf",
        ".rs",
        ".sh",
        ".sql",
        ".svg",
        ".swift",
        ".tex",
        ".toml",
        ".ts",
        ".tsv",
        ".txt",
        ".xls",
        ".xlsx",
        ".xml",
        ".yaml",
        ".yml",
        ".zig",
        ".zsh",
    )
)
_INDEX_REMOVE_COMMANDS = frozenset(("remove", "rm", "delete"))


@dataclass(slots=True)
class _MaterialIndexRefreshStats:
    reused: int = 0
    rebuilt: int = 0
    skipped: int = 0

    def record(self, state: str, detail: str) -> None:
        if state == "indexed" and detail.endswith(", reused)"):
            self.reused += 1
        elif state == "indexed":
            self.rebuilt += 1
        elif state == "skipped":
            self.skipped += 1


class ImportCommand(Command):
    name = "import"
    description = "Import files into the armory materials directory"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        if s.armory_path is None:
            print_error("No armory attached. Use /armory to open one.")
            return CommandResult()

        raw = args.strip()
        if not raw:
            print_error("Usage: /import <file-or-directory>")
            return CommandResult()

        source = _resolve_import_source(raw)
        if not source.exists():
            print_error(f"Path not found: {source}")
            return CommandResult()

        imported = _import_material_files(source, s.armory_path / MATERIALS_DIR)
        if not imported:
            print_info("No new files to import (unsupported format or already present).")
            return CommandResult()

        _print_imported_files(imported)
        refresh_armory_sources(s)
        print_info("Use /materials to browse or /vocabulary to review extracted cards.")
        return CommandResult()


class ExportCommand(Command):
    name = "export"
    description = "Export the current session to a markdown file"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        dest = args.strip()
        if not dest:
            dest = f"session-{s.session_id[:8]}.md"

        path = Path(dest).expanduser().resolve()
        if path.is_dir():
            path = path / f"session-{s.session_id[:8]}.md"

        messages = [msg for msg in s.conversation.messages if msg.role in {"user", "assistant"}]
        if not messages:
            print_info("Nothing to export — the session has no messages yet.")
            return CommandResult()

        lines: list[str] = []
        if s.title:
            lines.append(f"# {s.title}")
            lines.append("")

        for msg in messages:
            heading = "You" if msg.role == "user" else "Heph"
            lines.extend((f"## {heading}", "", msg.content, ""))

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8")
        print_success(f"Session exported to {path}")
        return CommandResult()


def _import_material_files(source: Path, dest_dir: Path) -> list[str]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    imported: list[str] = []
    for target in _import_targets(source):
        dest = _next_import_destination(target, dest_dir)
        if dest is None:
            continue
        shutil.copy2(target, dest)
        imported.append(dest.name)
    return imported


def _import_targets(source: Path) -> list[Path]:
    targets = sorted(source.rglob("*")) if source.is_dir() else [source]
    return [target for target in targets if _supported_import_target(target, source)]


def _supported_import_target(target: Path, source: Path) -> bool:
    if target.is_symlink() or not target.is_file():
        return False
    if source.is_dir() and _path_has_hidden_part(target, source):
        return False
    return target.suffix.lower() in _SUPPORTED_IMPORT_SUFFIXES


def _path_has_hidden_part(target: Path, source: Path) -> bool:
    try:
        parts = target.relative_to(source).parts
    except ValueError:
        return True
    return any(part.startswith(".") for part in parts)


def _resolve_import_source(raw: str) -> Path:
    source = Path(raw).expanduser()
    if source.exists():
        return source.resolve()

    try:
        parts = shlex.split(raw)
    except ValueError:
        return source.resolve()

    if len(parts) == 1:
        return Path(parts[0]).expanduser().resolve()
    return source.resolve()


def _next_import_destination(target: Path, dest_dir: Path) -> Path | None:
    dest = dest_dir / target.name
    if not dest.exists():
        return dest
    if _same_file_content(target, dest):
        return None

    stem = target.stem
    suffix = target.suffix
    for index in range(2, 10_000):
        candidate = dest_dir / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
        if _same_file_content(target, candidate):
            return None

    msg = f"Could not find a free filename for {target.name}"
    raise RuntimeError(msg)


def _same_file_content(left: Path, right: Path) -> bool:
    try:
        return filecmp.cmp(left, right, shallow=False)
    except OSError:
        return False


def _print_imported_files(imported: list[str]) -> None:
    print_success(f"Imported {len(imported)} file{'s' if len(imported) != 1 else ''}:")
    for name in imported:
        print(f"  {name}")


class IndexCommand(Command):
    name = "index"
    description = "Refresh the current armory materials index"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        parts = args.strip().split(maxsplit=1)
        subcmd = parts[0].lower() if parts else ""
        value = parts[1].strip() if len(parts) > 1 else ""

        if not subcmd:
            return _handle_material_index_refresh(s)
        if subcmd == "list":
            return _handle_index_list()
        if subcmd == "add":
            return _handle_index_add(value)
        if subcmd in _INDEX_REMOVE_COMMANDS:
            return _handle_index_remove(value)
        print_error("Usage: /index [list | add <path> | remove <path>]")
        print_info("Run bare /index to refresh the current armory materials index.")
        return CommandResult()


def _handle_material_index_refresh(session: ChatSession) -> CommandResult:
    if session.armory_path is None:
        print_error("No armory attached. Use /armory to open one.")
        return CommandResult()

    stats = _MaterialIndexRefreshStats()
    index = build_index(session.armory_path, progress=stats.record)
    session.rag_index = index
    return CommandResult(output=_material_index_summary(index, stats))


def _material_index_summary(
    index: ArmoryIndex,
    stats: _MaterialIndexRefreshStats,
) -> str:
    line = (
        f"Index refreshed: {_count_label(len(index.documents), 'source')}, "
        f"{_count_label(index.chunk_count, 'chunk')}; "
        f"cache {stats.reused} reused, {stats.rebuilt} rebuilt, {stats.skipped} skipped"
    )
    if stats.skipped:
        skipped = ", ".join(
            f"@{material_display_name(source)}" for source in sorted(index.unindexable_files)[:3]
        )
        suffix = "..." if len(index.unindexable_files) > 3 else ""
        line = f"{line}; skipped {skipped}{suffix}"
    return f"{line}."


def _count_label(count: int, noun: str) -> str:
    suffix = "" if count == 1 else "s"
    return f"{count} {noun}{suffix}"


def _handle_index_list() -> CommandResult:
    armories = load_known_armories()
    if not armories:
        print_info("No cross-armory search locations saved. Use /index add <path> to add one.")
        return CommandResult()
    lines = ["Cross-armory search locations:"]
    lines.extend(f"  {p}" for p in armories)
    print("\n".join(lines))
    return CommandResult()


def _handle_index_add(value: str) -> CommandResult:
    if not value:
        print_error("Usage: /index add <path>")
        return CommandResult()
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        print_error(f"Not a directory: {path}")
        return CommandResult()
    paths = add_known_armory(path)
    print_success(f"Added {path}. {len(paths)} armory/armories indexed.")
    return CommandResult()


def _handle_index_remove(value: str) -> CommandResult:
    if not value:
        print_error("Usage: /index remove <path>")
        return CommandResult()
    path = Path(value).expanduser().resolve()
    paths = remove_known_armory(path)
    print_success(f"Removed {path}. {len(paths)} armory/armories indexed.")
    return CommandResult()
