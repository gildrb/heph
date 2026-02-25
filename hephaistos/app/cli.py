from __future__ import annotations

import argparse
from pathlib import Path
import sys

from hephaistos.app.menu import run_main_menu
from hephaistos.armory.cli import register as register_armory_commands


def build_parser() -> argparse.ArgumentParser:
    prog = Path(sys.argv[0]).name or "hephaistos"
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Armory-first study CLI.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    register_armory_commands(subparsers)
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
            run_main_menu(parser, lambda menu_argv: run_argv(parser, menu_argv))
        else:
            parser.print_help()
        return

    run_argv(parser, argv)
