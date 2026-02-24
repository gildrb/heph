"""CLI commands for armory workspace management."""

from __future__ import annotations

import argparse
import sys

from hephaistos.armory.service import init_armory, open_armory
from hephaistos.armory.storage import ArmoryError


def _cmd_armory_init(args: argparse.Namespace) -> None:
    try:
        message = init_armory(args.path)
    except ArmoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    print(message)


def _cmd_armory_open(args: argparse.Namespace) -> None:
    try:
        message = open_armory(args.path)
    except ArmoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    print(message)


def register(subparsers) -> None:
    armory = subparsers.add_parser("armory", help="Manage armories (workspaces).")
    armory_sub = armory.add_subparsers(dest="armory_command", required=True)

    init = armory_sub.add_parser("init", help="Create a new armory folder.")
    init.add_argument("path", help="Path to the armory folder.")
    init.set_defaults(handler=_cmd_armory_init)

    open_cmd = armory_sub.add_parser("open", help="Open and validate an armory.")
    open_cmd.add_argument("path", help="Path to an existing armory folder.")
    open_cmd.set_defaults(handler=_cmd_armory_open)

