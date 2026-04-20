"""CLI commands for armory workspace management."""

from __future__ import annotations

import argparse
import sys

from hephaistos.analytics import capture as analytics_capture
from hephaistos.armory.storage import (
    ArmoryError,
    initialize,
    normalize_path,
    read_marker,
    validate,
)


def _cmd_armory_init(args: argparse.Namespace) -> None:
    try:
        armory_path = normalize_path(args.path)
        initialize(armory_path)
    except (ArmoryError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    print(f"Initialized armory at {armory_path}")
    analytics_capture("armory_initialized")


def _cmd_armory_open(args: argparse.Namespace) -> None:
    try:
        armory_path = normalize_path(args.path)
        validate(armory_path)
        marker = read_marker(armory_path)
    except (ArmoryError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    print(f"Opened armory {armory_path} (created {marker.get('created_at', 'unknown')})")


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:  # type: ignore[reportPrivateUsage]
    """Register armory subcommands."""
    armory = subparsers.add_parser("armory", help="Manage armories (workspaces).")
    armory_sub = armory.add_subparsers(dest="armory_command", required=True)

    init = armory_sub.add_parser("init", help="Create a new armory folder.")
    init.add_argument("path", help="Path to the armory folder.")
    init.set_defaults(handler=_cmd_armory_init)

    open_cmd = armory_sub.add_parser("open", help="Open and validate an armory.")
    open_cmd.add_argument("path", help="Path to an existing armory folder.")
    open_cmd.set_defaults(handler=_cmd_armory_open)
