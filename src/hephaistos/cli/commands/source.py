"""CLI commands for source document ingestion and indexing."""

from __future__ import annotations

import argparse
from pathlib import Path


def _cmd_source_add(args: argparse.Namespace) -> None:
    file_path = Path(args.file).expanduser().resolve()
    print(f"[todo] source add {file_path}")


def _cmd_source_list(args: argparse.Namespace) -> None:
    print("[todo] source list")


def _cmd_source_reindex(args: argparse.Namespace) -> None:
    print("[todo] source reindex")


def register_source_commands(subparsers) -> None:
    source = subparsers.add_parser("source", help="Manage source documents.")
    source_sub = source.add_subparsers(dest="source_command", required=True)

    add = source_sub.add_parser("add", help="Add a source file (PDF/doc).")
    add.add_argument("file", help="Path to the source file.")
    add.set_defaults(handler=_cmd_source_add)

    list_cmd = source_sub.add_parser("list", help="List source files in the armory.")
    list_cmd.set_defaults(handler=_cmd_source_list)

    reindex = source_sub.add_parser("reindex", help="Rebuild source indexes.")
    reindex.set_defaults(handler=_cmd_source_reindex)
