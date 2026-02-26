"""Interactive menu for no-args CLI startup."""

from __future__ import annotations
from dataclasses import dataclass

import argparse
from collections.abc import Callable



@dataclass(frozen=True)
class MenuItem:
    label: str                  # e.g. "armory init"
    description: str            # e.g. "Create a new armory folder"
    prompts: dict[str, str]     # e.g. {"name": "Enter armory name"}
    defaults: dict[str, str]    # e.g. {"name": "my_armory"}
    argv: list[str]             # e.g. ["armory", "init"]

def run(self, argv: list[str]) -> None:
    """Run the command associated with this option."""
    _run_choice(self.command, argv)

def _print_menu(items: list[MenuItem]) -> None:
    print("Hephaistos CLI")
    for i, item in enumerate(items, start=1):
        print(f"{i}. {item.label:<20s}{item.description}")
    print("h. Help              Show command help")
    print("q. Quit")

def _clear_screen() -> None:
    print("\033[2J\033[H", end="")


def _menu_text() -> None:
    print("Hephaistos CLI")
    print("1. Armory Init       Create a new armory folder")
    print("2. Armory Open       Validate and open an armory")
    print("h. Help              Show command help")
    print("q. Quit")


 
def _run_choice(run_command: Callable[[list[str]], None], argv: list[str]) -> None:
    try:
        run_command(argv)
    except SystemExit as exc:
        if exc.code:
            print(f"command failed with exit code {exc.code}")

def _dispatch_item(
    item: MenuItem,
    run_command: Callable[[list[str]], None],
) -> None:
    argv = list(item.argv)
    for arg_name, prompt_text in item.prompts.items():
        raw = input(prompt_text).strip()
        argv.append(raw or item.defaults.get(arg_name, ""))
    _run_choice(run_command, argv)

def run_main_menu(
    parser: argparse.ArgumentParser,
    items: list[MenuItem],
    run_command: Callable[[list[str]], None],
) -> None:
    """Run an interactive menu loop and dispatch commands."""
    while True:
        _clear_screen()
        _print_menu(items)
        choice = input("\nSelect option: ").strip().lower()
 
        if choice in {"q", "quit", "exit"}:
            return
        if choice in {"h", "help"}:
            parser.print_help()
            input("\nPress Enter to continue...")
            continue
 
        # numeric selection
        try:
            idx = int(choice) - 1
        except ValueError:
            print("Unknown option.")
            input("Press Enter to continue...")
            continue
 
        if 0 <= idx < len(items):
            _dispatch_item(items[idx], run_command)
            input("\nPress Enter to continue...")
        else:
            print("Unknown option.")
            input("Press Enter to continue...")