"""CLI commands for armory workspace management."""

from __future__ import annotations

import argparse
from pathlib import Path


def _cmd_armory_init(args: argparse.Namespace) -> None:
    path = Path(args.path).expanduser().resolve()
    print(f"[todo] armory init at {path}")


def _cmd_armory_open(args: argparse.Namespace) -> None:
    path = Path(args.path).expanduser().resolve()
    print(f"[todo] armory open {path}")


def register_armory_commands(subparsers) -> None:
    armory = subparsers.add_parser("armory", help="Manage armories (workspaces).")
    armory_sub = armory.add_subparsers(dest="armory_command", required=True)

    init = armory_sub.add_parser("init", help="Create a new armory folder.")
    init.add_argument("path", help="Path to the armory folder.")
    init.set_defaults(handler=_cmd_armory_init)

    open_cmd = armory_sub.add_parser("open", help="Open and validate an armory.")
    open_cmd.add_argument("path", help="Path to an existing armory folder.")
    open_cmd.set_defaults(handler=_cmd_armory_open)
