"""Interactive menu helpers for TTY workflows."""

from __future__ import annotations

from dataclasses import dataclass
import select
import sys

if sys.platform != "win32":
    import termios
    import tty

from hephaistos.app.display import (
    BOLD,
    STYLE_DIM,
    STYLE_PROMPT,
    styled,
)


@dataclass(frozen=True)
class MenuOption:
    label: str
    description: str


def _clear_screen() -> None:
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def _render_menu(title: str, options: list[MenuOption], selected: int) -> None:
    _clear_screen()

    # Title
    sys.stdout.write(f"{styled(title, STYLE_PROMPT)}\r\n")
    sys.stdout.write(
        f"{styled('Use Up/Down or j/k, Enter to select, q to cancel.', STYLE_DIM)}\r\n\r\n"
    )

    max_label = max(len(opt.label) for opt in options) if options else 0

    for index, option in enumerate(options):
        if index == selected:
            # Inverse highlight (same as slash command autocomplete)
            label = f"\033[7m {option.label} \033[0m"
            if option.description:
                padded = f" {option.label} ".ljust(max_label + 2)
                line = f"\033[7m>{padded}  {option.description}\033[0m"
            else:
                line = f"\033[7m> {option.label}\033[0m"
        else:
            label = styled(option.label, BOLD)
            desc = styled(option.description, STYLE_DIM) if option.description else ""
            if desc:
                padded = f"  {option.label}".ljust(max_label + 4)
                line = f" {padded}{desc}"
            else:
                line = f" {label}"

        sys.stdout.write(f"{line}\r\n")

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

            ready, _, _ = select.select([fd], [], [], 0.05)
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
    print(styled(title, STYLE_PROMPT))
    for index, option in enumerate(options, start=1):
        label = styled(option.label, BOLD)
        desc = styled(option.description, STYLE_DIM) if option.description else ""
        if desc:
            max_label = max(len(opt.label) for opt in options)
            padded = f"  {option.label}".ljust(max_label + 4)
            print(f"  {index}. {padded}{desc}")
        else:
            print(f"  {index}. {label}")
    print(f"  {styled('q.', STYLE_DIM)} Cancel")

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
