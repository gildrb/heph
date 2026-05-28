"""CLI commands for armory workspace management."""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from hephaion.armory.storage import (
    ArmoryError,
    initialize,
    normalize_path,
    read_marker,
    validate,
)
from hephaion.env import get_env

if TYPE_CHECKING:
    from collections.abc import Callable

DEFAULT_ARMORY_HOME_ENV = "HEPHAION_ARMORY_HOME"


def default_armory_home() -> Path:
    configured = get_env(DEFAULT_ARMORY_HOME_ENV)
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".armories"


def armory_shortcut_path(name: str, parent: str | None = None) -> Path:
    if parent:
        return Path(parent).expanduser() / ".armories" / name
    return default_armory_home() / name


def _cmd_armory_init(args: argparse.Namespace) -> None:
    armory_home = default_armory_home()
    candidate = Path(args.path).expanduser()
    if (
        not candidate.is_absolute()
        and len(candidate.parts) == 1
        and candidate.name not in {"", "."}
    ):
        armory_path = (armory_home / candidate.name).resolve()
    else:
        armory_path = normalize_path(args.path)

    try:
        armory_path.resolve().relative_to(armory_home.resolve())
    except ValueError:
        print(
            f"error: Armories can only be created in the armories directory ({armory_home}).",
            file=sys.stderr,
        )
        print(f"error: Attempted to create at: {armory_path}", file=sys.stderr)
        raise SystemExit(2) from None

    try:
        initialize(armory_path)
    except (ArmoryError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    post_init = getattr(args, "post_init", None)
    if post_init is not None:
        post_init(armory_path)
    module_name = armory_path.name
    materials_path = armory_path / "materials"
    print(f"Created armory '{module_name}' at {armory_path}")
    print(f"Add source files to: {materials_path}")
    print(f"Then start working with your documents: heph {module_name}")
    print("Armories are stored locally in ~/.armories/")
    analytics = importlib.import_module("hephaion.diagnostics.events")
    analytics.capture("armory_created", {"mode": "cli"})


def _cmd_armory_open(args: argparse.Namespace) -> None:
    try:
        armory_path = normalize_path(args.path)
        validate(armory_path)
        marker = read_marker(armory_path)
    except (ArmoryError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    print(f"Opened armory {armory_path} (created {marker.get('created_at', 'unknown')})")


def register(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    *,
    post_init: Callable[[Path], None] | None = None,
) -> None:
    """Register armory subcommands."""
    armory = subparsers.add_parser(
        "armory",
        help="Create and inspect armories.",
        description=(
            "Create armories named after modules. "
            "Armories can only be created in the armories directory (~/.armories). "
            "Shortcut: `heph armory course-notes` creates ~/.armories/course-notes."
        ),
    )
    armory_sub = armory.add_subparsers(dest="armory_command", required=True)

    init = armory_sub.add_parser("init", help="Create a new named armory folder.")
    init.add_argument(
        "path",
        help="Folder name (armory will be created in ~/.armories/), e.g. course-notes.",
    )
    init.set_defaults(handler=_cmd_armory_init, post_init=post_init)

    open_cmd = armory_sub.add_parser("open", help="Open and validate an armory.")
    open_cmd.add_argument("path", help="Path to an existing armory folder.")
    open_cmd.set_defaults(handler=_cmd_armory_open)
