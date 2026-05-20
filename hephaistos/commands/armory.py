"""Armory management commands: armory, import, index, export."""

from __future__ import annotations

import shutil
from pathlib import Path

from hephaistos.armory.search import (
    add_known_armory,
    load_known_armories,
    remove_known_armory,
)
from hephaistos.chat.session import refresh_armory_sources
from hephaistos.commands._base import Command, CommandResult, ensure_session
from hephaistos.terminal.display import print_error, print_info, print_success


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

        source = Path(raw).expanduser().resolve()
        if not source.exists():
            print_error(f"Path not found: {source}")
            return CommandResult()

        dest_dir = s.armory_path / "materials"
        dest_dir.mkdir(parents=True, exist_ok=True)
        imported: list[str] = []

        targets = sorted(source.iterdir()) if source.is_dir() else [source]
        for target in targets:
            if target.is_dir():
                continue
            if target.suffix.lower() not in (".md", ".txt", ".pdf", ".rst", ".py", ".json"):
                continue
            dest = dest_dir / target.name
            if dest.exists():
                continue
            shutil.copy2(target, dest)
            imported.append(target.name)

        if not imported:
            print_info("No new files to import (unsupported format or already present).")
            return CommandResult()

        print_success(f"Imported {len(imported)} file{'s' if len(imported) != 1 else ''}:")
        for name in imported:
            print(f"  {name}")
        refresh_armory_sources(s)
        print_info("Use /materials to browse or /vocab drill to review extracted cards.")
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
            heading = "You" if msg.role == "user" else "Hephaistos"
            lines.extend((f"## {heading}", "", msg.content, ""))

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8")
        print_success(f"Session exported to {path}")
        return CommandResult()


class IndexCommand(Command):
    name = "index"
    description = "Manage cross-armory search index"

    def handle(self, session: object, args: str) -> CommandResult:
        parts = args.strip().split(maxsplit=1)
        subcmd = parts[0].lower() if parts else "list"
        value = parts[1].strip() if len(parts) > 1 else ""

        if subcmd == "list":
            armories = load_known_armories()
            if not armories:
                print_info("No armories indexed. Use /index add <path> to add one.")
                return CommandResult()
            lines = ["Indexed armories:"]
            lines.extend(f"  {p}" for p in armories)
            print("\n".join(lines))
            return CommandResult()
        if subcmd == "add":
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
        if subcmd in ("remove", "rm", "delete"):
            if not value:
                print_error("Usage: /index remove <path>")
                return CommandResult()
            path = Path(value).expanduser().resolve()
            paths = remove_known_armory(path)
            print_success(f"Removed {path}. {len(paths)} armory/armories indexed.")
            return CommandResult()
        print_error("Usage: /index [list | add <path> | remove <path>]")
        return CommandResult()
