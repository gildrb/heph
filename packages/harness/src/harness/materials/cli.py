"""CLI commands for material management."""

from __future__ import annotations

import argparse
import importlib
import sys
from collections.abc import Callable
from pathlib import Path

from harness.armory.storage import (
    ArmoryError,
    normalize_path,
    validate,
)

IndexHandler = Callable[[argparse.Namespace], None]


def _validated_armory_path(path: str) -> Path:
    try:
        armory_path = normalize_path(path)
        validate(armory_path)
        return armory_path
    except (ArmoryError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


def _cmd_materials_list(args: argparse.Namespace) -> None:
    armory_path = _validated_armory_path(args.path)
    materials = importlib.import_module("harness.materials")
    files = list(materials.iter_material_files(armory_path))
    if not files:
        print("No materials found.")
        return

    for file_path in files:
        print(str(file_path.relative_to(armory_path)))


def _cmd_materials_count(args: argparse.Namespace) -> None:
    armory_path = _validated_armory_path(args.path)
    materials = importlib.import_module("harness.materials")
    print(materials.count_material_files(armory_path))


def _cmd_missing_index_handler(_args: argparse.Namespace) -> None:
    print("error: materials index is unavailable in this context", file=sys.stderr)
    raise SystemExit(2)


def _register_material_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    *,
    name: str,
    help_text: str,
    index_handler: IndexHandler | None,
) -> None:
    materials = subparsers.add_parser(name, help=help_text)
    materials_sub = materials.add_subparsers(dest=f"{name}_command", required=True)

    list_cmd = materials_sub.add_parser("list", help="List material files.")
    list_cmd.add_argument("path", help="Path to the armory folder.")
    list_cmd.set_defaults(handler=_cmd_materials_list)

    count_cmd = materials_sub.add_parser("count", help="Count material files.")
    count_cmd.add_argument("path", help="Path to the armory folder.")
    count_cmd.set_defaults(handler=_cmd_materials_count)

    index_cmd = materials_sub.add_parser("index", help="Build or refresh the RAG index.")
    index_cmd.add_argument("path", help="Path to the armory folder.")
    index_cmd.set_defaults(handler=index_handler or _cmd_missing_index_handler)


def register(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    *,
    index_handler: IndexHandler | None = None,
) -> None:
    _register_material_commands(
        subparsers,
        name="materials",
        help_text="Manage materials in an armory.",
        index_handler=index_handler,
    )
    _register_material_commands(
        subparsers,
        name="source",
        help_text=argparse.SUPPRESS,
        index_handler=index_handler,
    )


__all__ = [
    "register",
]
