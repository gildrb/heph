from __future__ import annotations

import argparse
import sys
from pathlib import Path

from hephaistos.app.shell import run_chat_shell
from hephaistos.armory.cli import register as register_armory_commands
from hephaistos.chat.cli import register as register_chat_commands

try:
    from importlib.metadata import version as _pkg_version

    _VERSION = _pkg_version("hephaistos")
except Exception:
    _VERSION = "0.1.0"


def _hide_subparser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    name: str,
) -> None:
    subparsers._choices_actions = [
        action for action in subparsers._choices_actions if getattr(action, "dest", None) != name
    ]


def build_parser() -> argparse.ArgumentParser:
    prog = Path(sys.argv[0]).name or "hephaistos"
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Chat-first study CLI.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_VERSION}",
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        metavar="command",
    )

    register_armory_commands(subparsers)
    register_chat_commands(subparsers)
    _hide_subparser(subparsers, "chat")

    return parser


def run_argv(parser: argparse.ArgumentParser, argv: list[str]) -> None:
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return
    handler(args)


def main() -> None:
    parser = build_parser()
    argv = sys.argv[1:]

    if not argv:
        if sys.stdin.isatty() and sys.stdout.isatty():
            run_chat_shell()
        else:
            parser.print_help()
        return

    run_argv(parser, argv)
