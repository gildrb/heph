"""CLI commands for armory workspace management."""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from hephaistos.armory.storage import (
    ArmoryError,
    initialize,
    normalize_path,
    read_marker,
    validate,
)

if TYPE_CHECKING:
    from collections.abc import Callable

DEFAULT_ARMORY_HOME_ENV = "HEPHAISTOS_ARMORY_HOME"


def default_armory_home() -> Path:
    configured = os.environ.get(DEFAULT_ARMORY_HOME_ENV)
    if configured:
        return Path(configured).expanduser()
    return Path.home() / "Armories"


def armory_shortcut_path(name: str, parent: str | None = None) -> Path:
    if parent:
        return Path(parent).expanduser() / "Armories" / name
    return default_armory_home() / name


def _cmd_armory_init(args: argparse.Namespace) -> None:
    try:
        armory_path = normalize_path(args.path)
        initialize(armory_path)
    except (ArmoryError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    post_init = getattr(args, "post_init", None)
    if post_init is not None:
        post_init(armory_path)
    print(f"Initialized armory at {armory_path}")
    print(f"Open it later with: heph {armory_path.name}")
    analytics = importlib.import_module("hephaistos.analytics")
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
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],  # type: ignore[reportPrivateUsage]
    *,
    post_init: Callable[[Path], None] | None = None,
) -> None:
    """Register armory subcommands."""
    armory = subparsers.add_parser(
        "armory",
        help="Create and inspect study armories.",
        description=(
            "Create armories named after modules. Shortcut: "
            "`heph armory mfi-1` creates ~/Armories/mfi-1, while "
            "`heph armory mfi-1 ./Code` creates ./Code/Armories/mfi-1."
        ),
    )
    armory_sub = armory.add_subparsers(dest="armory_command", required=True)

    init = armory_sub.add_parser("init", help="Create a new named armory folder.")
    init.add_argument("path", help="Folder name or path, e.g. gdp or swt.")
    init.set_defaults(handler=_cmd_armory_init, post_init=post_init)

    open_cmd = armory_sub.add_parser("open", help="Open and validate an armory.")
    open_cmd.add_argument("path", help="Path to an existing armory folder.")
    open_cmd.set_defaults(handler=_cmd_armory_open)
