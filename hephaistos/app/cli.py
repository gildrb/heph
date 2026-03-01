from __future__ import annotations

import argparse
from pathlib import Path
import sys

from hephaistos.app.menu import MenuItem, run_main_menu
from hephaistos.armory.cli import register as register_armory_commands
from hephaistos.armory.cli import MENU_ITEMS as armory_menu_items
from hephaistos.chat.cli import register as register_chat_commands
from hephaistos.chat.cli import MENU_ITEMS as chat_menu_items



def build_parser() -> tuple[argparse.ArgumentParser, list[MenuItem]]:
    prog = Path(sys.argv[0]).name or "hephaistos"
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Armory-first study CLI.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
 
    register_armory_commands(subparsers)
    register_chat_commands(subparsers)
 
    menu_items: list[MenuItem] = []
    menu_items.extend(armory_menu_items)
    menu_items.extend(chat_menu_items)
 
    return parser, menu_items


def run_argv(parser: argparse.ArgumentParser, argv: list[str]) -> None:
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return
    handler(args)


def main() -> None:
    parser, menu_items = build_parser()
    argv = sys.argv[1:]
 
    if not argv:
        if sys.stdin.isatty() and sys.stdout.isatty():
            run_main_menu(parser, menu_items, lambda menu_argv: run_argv(parser, menu_argv))
        else:
            parser.print_help()
        return
 
    run_argv(parser, argv)
