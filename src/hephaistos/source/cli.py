"""CLI commands for source document ingestion and indexing."""

from __future__ import annotations

import argparse

from hephaistos.source.service import add_source, list_sources, reindex_sources


def _cmd_source_add(args: argparse.Namespace) -> None:
    print(add_source(args.file))


def _cmd_source_list(args: argparse.Namespace) -> None:
    print(list_sources())


def _cmd_source_reindex(args: argparse.Namespace) -> None:
    print(reindex_sources())


def register(subparsers) -> None:
    source = subparsers.add_parser("source", help="Manage source documents.")
    source_sub = source.add_subparsers(dest="source_command", required=True)

    add = source_sub.add_parser("add", help="Add a source file (PDF/doc).")
    add.add_argument("file", help="Path to the source file.")
    add.set_defaults(handler=_cmd_source_add)

    list_cmd = source_sub.add_parser("list", help="List source files in the armory.")
    list_cmd.set_defaults(handler=_cmd_source_list)

    reindex = source_sub.add_parser("reindex", help="Rebuild source indexes.")
    reindex.set_defaults(handler=_cmd_source_reindex)

