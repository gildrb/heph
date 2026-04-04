"""Interactive menu helpers for TTY workflows."""

from __future__ import annotations

from dataclasses import dataclass
import select
import sys

if sys.platform != "win32":
    import termios
    import tty


@dataclass(frozen=True)
class MenuOption:
    label: str
    description: str


def _clear_screen() -> None:
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def _render_menu(title: str, options: list[MenuOption], selected: int) -> None:
    _clear_screen()
    sys.stdout.write(f"{title}\r\n")
    sys.stdout.write("Use Up/Down or j/k, Enter to select, q to cancel.\r\n\r\n")
    for index, option in enumerate(options):
        prefix = ">" if index == selected else " "
        sys.stdout.write(f"{prefix} {option.label}\r\n")
        if option.description:
            sys.stdout.write(f"   {option.description}\r\n")
    sys.stdout.flush()


def _select_with_arrow_keys(title: str, options: list[MenuOption]) -> int | None:
    fd = sys.stdin.fileno()
    original = termios.tcgetattr(fd)
    selected = 0

    try:
        tty.setraw(fd)
        while True:
            _render_menu(title, options, selected)
            key = sys.stdin.read(1)

            if key in {"q", "\x03"}:
                _clear_screen()
                return None
            if key in {"\r", "\n"}:
                _clear_screen()
                return selected
            if key == "k":
                selected = (selected - 1) % len(options)
                continue
            if key == "j":
                selected = (selected + 1) % len(options)
                continue
            if key != "\x1b":
                continue

            ready, _, _ = select.select([sys.stdin], [], [], 0.05)
            if not ready:
                _clear_screen()
                return None
            sequence = sys.stdin.read(2)
            if sequence == "[A":
                selected = (selected - 1) % len(options)
            elif sequence == "[B":
                selected = (selected + 1) % len(options)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, original)


def _select_with_prompt(title: str, options: list[MenuOption]) -> int | None:
    print(title)
    for index, option in enumerate(options, start=1):
        print(f"{index}. {option.label}")
        if option.description:
            print(f"   {option.description}")
    print("q. Cancel")

    while True:
        choice = input("\nSelect option: ").strip().lower()
        if choice in {"q", "quit", "exit"}:
            return None
        try:
            selected = int(choice) - 1
        except ValueError:
            print("Unknown option.")
            continue
        if 0 <= selected < len(options):
            return selected
        print("Unknown option.")


def select_option(title: str, options: list[MenuOption]) -> int | None:
    """Return the selected option index or ``None`` when cancelled."""
    if not options:
        return None

    can_use_tty = sys.stdin.isatty() and sys.stdout.isatty() and sys.platform != "win32"
    if can_use_tty:
        try:
            return _select_with_arrow_keys(title, options)
        except (OSError, termios.error):
            pass

    return _select_with_prompt(title, options)
