"""Interactive main menu for no-args CLI startup."""

from __future__ import annotations

import argparse
from collections.abc import Callable


def _clear_screen() -> None:
    print("\033[2J\033[H", end="")


def _banner() -> None:
    print("\033[92m")
    print(" _   _ _____ ____  _   _ ")
    print("| | | | ____|  _ \\| | | |")
    print("| |_| |  _| | |_) | |_| |")
    print("|  _  | |___|  __/|  _  |")
    print("|_| |_|_____|_|   |_| |_|")
    print("\033[0m")


def _menu_text() -> None:
    print("Hephaistos CLI")
    print("1. Armory Init       Create a new armory folder")
    print("2. Armory Open       Validate and open an armory")
    print("3. Source List       List source documents")
    print("4. Chat New          Start a new chat")
    print("5. Parameters List   List parameter profiles")
    print("h. Help              Show command help")
    print("q. Quit")


def _run_choice(run_command: Callable[[list[str]], None], argv: list[str]) -> None:
    try:
        run_command(argv)
    except SystemExit as exc:
        if exc.code:
            print(f"command failed with exit code {exc.code}")


def run_main_menu(
    parser: argparse.ArgumentParser,
    run_command: Callable[[list[str]], None],
) -> None:
    """Run an interactive menu loop and dispatch commands."""
    while True:
        _clear_screen()
        _banner()
        _menu_text()
        choice = input("\nSelect option: ").strip().lower()

        if choice in {"q", "quit", "exit"}:
            return
        if choice in {"h", "help"}:
            parser.print_help()
            input("\nPress Enter to continue...")
            continue
        if choice == "1":
            raw = input("Armory path [./armory]: ").strip()
            path = raw or "./armory"
            _run_choice(run_command, ["armory", "init", path])
            input("\nPress Enter to continue...")
            continue
        if choice == "2":
            raw = input("Armory path [./armory]: ").strip()
            path = raw or "./armory"
            _run_choice(run_command, ["armory", "open", path])
            input("\nPress Enter to continue...")
            continue
        if choice == "3":
            _run_choice(run_command, ["source", "list"])
            input("\nPress Enter to continue...")
            continue
        if choice == "4":
            title = input("Chat title (optional): ").strip()
            if title:
                _run_choice(run_command, ["chat", "new", "--title", title])
            else:
                _run_choice(run_command, ["chat", "new"])
            input("\nPress Enter to continue...")
            continue
        if choice == "5":
            _run_choice(run_command, ["parameters", "list"])
            input("\nPress Enter to continue...")
            continue

        print("Unknown option.")
        input("Press Enter to continue...")

