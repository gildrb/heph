# where your CLI is defined (commands, parsing, dispatch).

from __future__ import annotations

import argparse

from hephaistos.cli.commands.armory import register_armory_commands
from hephaistos.cli.commands.chat import register_chat_commands
from hephaistos.cli.commands.parameters import register_parameters_commands
from hephaistos.cli.commands.source import register_source_commands


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hephaistos",
        description="Study CLI for armory-based projects and AI chat.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    register_armory_commands(subparsers)
    register_source_commands(subparsers)
    register_chat_commands(subparsers)
    register_parameters_commands(subparsers)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return
    handler(args)
