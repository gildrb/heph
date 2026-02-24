# where your CLI is defined (commands, parsing, dispatch).

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from hephaistos.app.menu import run_main_menu
from hephaistos.armory.cli import register as register_armory_commands
from hephaistos.chat.cli import register as register_chat_commands
from hephaistos.parameters.cli import register as register_parameters_commands
from hephaistos.source.cli import register as register_source_commands


def build_parser() -> argparse.ArgumentParser:
    prog = Path(sys.argv[0]).name or "hephaistos"
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Study CLI for armory-based projects and AI chat.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    register_armory_commands(subparsers)
    register_source_commands(subparsers)
    register_chat_commands(subparsers)
    register_parameters_commands(subparsers)
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

    if not argv and sys.stdin.isatty() and sys.stdout.isatty():
        run_main_menu(parser, lambda menu_argv: run_argv(parser, menu_argv))
        return

    run_argv(parser, argv)

