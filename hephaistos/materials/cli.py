"""CLI commands for study material management."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from hephaistos.armory.storage import (
    ArmoryError,
    normalize_path,
    validate,
)
from hephaistos.materials import count_material_files, iter_material_files

IndexHandler = Callable[[argparse.Namespace], None]


def _validate_armory(args: argparse.Namespace) -> Path:
    """Validate and return the resolved armory path."""
    armory_path = normalize_path(args.path)
    validate(armory_path)
    return armory_path


def _cmd_materials_list(args: argparse.Namespace) -> None:
    """List study material files in an armory."""
    try:
        armory_path = _validate_armory(args)
    except (ArmoryError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    files = list(iter_material_files(armory_path))
    if not files:
        print("No study materials found.")
        return

    for file_path in files:
        print(str(file_path.relative_to(armory_path)))


def _cmd_materials_count(args: argparse.Namespace) -> None:
    """Show the count of study material files in an armory."""
    try:
        armory_path = _validate_armory(args)
    except (ArmoryError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    print(count_material_files(armory_path))


def _cmd_missing_index_handler(_args: argparse.Namespace) -> None:
    """Guard against registering the CLI without an application index handler."""
    print("error: materials index is unavailable in this context", file=sys.stderr)
    raise SystemExit(2)


def _register_material_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],  # type: ignore[reportPrivateUsage]
    *,
    name: str,
    help_text: str,
    index_handler: IndexHandler | None,
) -> None:
    materials = subparsers.add_parser(name, help=help_text)
    materials_sub = materials.add_subparsers(dest=f"{name}_command", required=True)

    list_cmd = materials_sub.add_parser("list", help="List study material files.")
    list_cmd.add_argument("path", help="Path to the armory folder.")
    list_cmd.set_defaults(handler=_cmd_materials_list)

    count_cmd = materials_sub.add_parser("count", help="Count study material files.")
    count_cmd.add_argument("path", help="Path to the armory folder.")
    count_cmd.set_defaults(handler=_cmd_materials_count)

    index_cmd = materials_sub.add_parser("index", help="Build or refresh the RAG index.")
    index_cmd.add_argument("path", help="Path to the armory folder.")
    index_cmd.set_defaults(handler=index_handler or _cmd_missing_index_handler)


def register(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],  # type: ignore[reportPrivateUsage]
    *,
    index_handler: IndexHandler | None = None,
) -> None:
    """Register preferred materials subcommands."""
    _register_material_commands(
        subparsers,
        name="materials",
        help_text="Manage study materials in an armory.",
        index_handler=index_handler,
    )


def register_source_alias(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],  # type: ignore[reportPrivateUsage]
    *,
    index_handler: IndexHandler | None = None,
) -> None:
    """Register the compatibility ``source`` command namespace."""
    _register_material_commands(
        subparsers,
        name="source",
        help_text="Manage study materials in an armory.",
        index_handler=index_handler,
    )


__all__ = [
    "register",
    "register_source_alias",
]
