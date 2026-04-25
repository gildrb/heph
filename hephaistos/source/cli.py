"""CLI commands for source document management."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from hephaistos.armory.storage import (
    ArmoryError,
    normalize_path,
    validate,
)
from hephaistos.harness.rag.index import build_index, iter_source_files


def _iter_source_files(armory_path: Path) -> list[Path]:
    """Return sorted list of source files across source/ and library/ dirs."""
    return list(iter_source_files(armory_path))


def _validate_armory(args: argparse.Namespace) -> Path:
    """Validate and return the resolved armory path."""
    armory_path = normalize_path(args.path)
    validate(armory_path)
    return armory_path


def _cmd_source_list(args: argparse.Namespace) -> None:
    """List source documents in an armory."""
    try:
        armory_path = _validate_armory(args)
    except (ArmoryError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    files = _iter_source_files(armory_path)
    if not files:
        print("No source documents found.")
        return

    for file_path in files:
        print(str(file_path.relative_to(armory_path)))


def _cmd_source_count(args: argparse.Namespace) -> None:
    """Show the count of source documents in an armory."""
    try:
        armory_path = _validate_armory(args)
    except (ArmoryError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    count = len(_iter_source_files(armory_path))
    print(count)


def _cmd_source_index(args: argparse.Namespace) -> None:
    """Build or refresh the RAG index for source documents."""
    try:
        armory_path = _validate_armory(args)
    except (ArmoryError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    index = build_index(armory_path)
    print(f"Indexed {len(index.documents)} documents ({index.chunk_count} chunks)")


def register(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],  # type: ignore[reportPrivateUsage]
) -> None:
    """Register source subcommands."""
    source = subparsers.add_parser("source", help="Manage source documents in an armory.")
    source_sub = source.add_subparsers(dest="source_command", required=True)

    list_cmd = source_sub.add_parser("list", help="List source documents.")
    list_cmd.add_argument("path", help="Path to the armory folder.")
    list_cmd.set_defaults(handler=_cmd_source_list)

    count_cmd = source_sub.add_parser("count", help="Count source documents.")
    count_cmd.add_argument("path", help="Path to the armory folder.")
    count_cmd.set_defaults(handler=_cmd_source_count)

    index_cmd = source_sub.add_parser("index", help="Build or refresh the RAG index.")
    index_cmd.add_argument("path", help="Path to the armory folder.")
    index_cmd.set_defaults(handler=_cmd_source_index)
