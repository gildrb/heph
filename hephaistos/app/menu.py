"""Interactive menu helpers for TTY workflows.

Uses an alternate screen buffer so the user's terminal scrollback is
preserved.  Supports arrow-key / j-k navigation only (no typing).
The menu fills the full terminal viewport and is centered with the
Hephaistos visual identity.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import select
import sys

if sys.platform != "win32":
    import termios
    import tty

from hephaistos.app.display import (
    BOLD,
    STYLE_ACCENT,
    STYLE_DIM,
    STYLE_PROMPT,
    styled,
    visible_len,
)


@dataclass(frozen=True)
class MenuOption:
    label: str
    description: str = ""
    is_current: bool = False


# ---------------------------------------------------------------------------
# Alternate screen buffer helpers
# ---------------------------------------------------------------------------

def _enter_alt_screen() -> None:
    sys.stdout.write("\033[?1049h")
    sys.stdout.flush()


def _leave_alt_screen() -> None:
    sys.stdout.write("\033[?1049l")
    sys.stdout.flush()


def _clear_screen() -> None:
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Terminal size helper
# ---------------------------------------------------------------------------

def _term_size() -> tuple[int, int]:
    try:
        cols, rows = os.get_terminal_size()
        return max(cols, 20), max(rows, 6)
    except OSError:
        return 80, 24


# ---------------------------------------------------------------------------
# Full-viewport rendering
# ---------------------------------------------------------------------------

def _center(text: str, width: int) -> str:
    """Return *text* centered in *width* columns (ANSI-aware)."""
    vis = visible_len(text)
    pad = max(0, (width - vis) // 2)
    return f"{' ' * pad}{text}"


def _render_menu(
    title: str,
    options: list[MenuOption],
    selected: int,
) -> int:
    """Render the full-viewport menu.  Returns the number of lines written."""

    cols, rows = _term_size()
    _clear_screen()

    # ── Build content lines ──
    content: list[str] = []

    # Title line: ⚡ Hephaistos — {title} ⚡
    title_text = f"⚡ Hephaistos — {title} ⚡"
    content.append(styled(title_text, STYLE_PROMPT))

    # Separator
    sep = styled("─" * len(title_text), STYLE_DIM)
    content.append(sep)
    content.append("")  # blank line

    # Options
    for idx, option in enumerate(options):
        if idx == selected:
            # Selected item: ▸ label (bold + reverse video) with description
            arrow = styled("▸", STYLE_ACCENT)
            label = styled(option.label, BOLD)
            content.append(_center(f"{arrow} {label}", cols))
            if option.description:
                content.append(_center(styled(f"  {option.description}", STYLE_DIM), cols))
        else:
            # Unselected item
            label = styled(option.label, STYLE_DIM)
            content.append(_center(f"  {label}", cols))
            if option.description:
                content.append(_center(styled(f"  {option.description}", STYLE_DIM), cols))
        content.append("")  # spacing between items

    # Bottom separator
    content.append(sep)

    # Footer
    footer = styled("↑↓ navigate · Enter select · Esc cancel", STYLE_DIM)
    content.append(_center(footer, cols))

    # ── Vertically center the content block ──
    total_content_lines = len(content)
    top_pad = max(0, (rows - total_content_lines) // 2)

    # Move cursor to the correct starting row
    output_lines: list[str] = []
    for _ in range(top_pad):
        output_lines.append("")
    output_lines.extend(content)

    # Clear screen then write everything
    sys.stdout.write("\r\n".join(output_lines))
    sys.stdout.flush()
    return len(output_lines)


# ---------------------------------------------------------------------------
# Escape sequence reader (robust)
# ---------------------------------------------------------------------------

def _read_escape_sequence(fd: int) -> str | None:
    """After reading \\x1b, consume the rest of an escape sequence.

    Returns a canonical key name:
      "up", "down", "left", "right", or None for unrecognized/bare Escape.
    A bare Escape (no following bytes within 200 ms) returns None.
    """
    ready, _, _ = select.select([fd], [], [], 0.2)
    if not ready:
        return None  # bare Escape

    ch = os.read(fd, 1)
    if not ch:
        return None

    b = ch[0]

    # CSI sequence: ESC [ ... final_byte
    if b == 0x5B:  # '['
        # Read parameter bytes and intermediate bytes until final byte (0x40..0x7E)
        params = b""
        while True:
            r, _, _ = select.select([fd], [], [], 0.05)
            if not r:
                return None
            next_byte = os.read(fd, 1)
            if not next_byte:
                return None
            nb = next_byte[0]
            if 0x40 <= nb <= 0x7E:
                # final byte
                code = bytes([nb])
                if params == b"" and code == b"A":
                    return "up"
                elif params == b"" and code == b"B":
                    return "down"
                elif params == b"" and code == b"C":
                    return "right"
                elif params == b"" and code == b"D":
                    return "left"
                elif params == b"3" and code == b"~":
                    return "delete"
                else:
                    return None  # unrecognized CSI
            elif 0x20 <= nb <= 0x3F:
                params += next_byte
            else:
                return None

    # SS3 sequence: ESC O ...
    if b == 0x4F:  # 'O'
        r, _, _ = select.select([fd], [], [], 0.05)
        if not r:
            return None
        next_byte = os.read(fd, 1)
        if not next_byte:
            return None
        nb = next_byte[0]
        if nb == 0x41:
            return "up"
        elif nb == 0x42:
            return "down"
        elif nb == 0x43:
            return "right"
        elif nb == 0x44:
            return "left"
        return None

    return None


# ---------------------------------------------------------------------------
# Interactive arrow-key selector (alternate screen)
# ---------------------------------------------------------------------------

def _select_with_arrow_keys(title: str, options: list[MenuOption]) -> int | None:
    fd = sys.stdin.fileno()
    original = termios.tcgetattr(fd)
    selected = 0

    try:
        _enter_alt_screen()
        tty.setraw(fd)

        while True:
            _render_menu(title, options, selected)

            ch = os.read(fd, 1)
            if not ch:
                continue
            byte = ch[0]

            # ── Escape ──
            if byte == 0x1B:
                key = _read_escape_sequence(fd)
                if key is None:
                    # Bare Escape → cancel
                    return None
                elif key == "up":
                    selected = (selected - 1) % len(options) if options else 0
                elif key == "down":
                    selected = (selected + 1) % len(options) if options else 0
                # left/right/delete → ignore
                continue

            # ── Ctrl+C → cancel ──
            if byte == 0x03:
                return None

            # ── Enter ──
            if byte in (0x0D, 0x0A):
                return selected if options else None

            # ── j / k navigation ──
            if byte == 0x6B:  # 'k'
                selected = (selected - 1) % len(options) if options else 0
                continue
            if byte == 0x6A:  # 'j'
                selected = (selected + 1) % len(options) if options else 0
                continue

            # All other keys are ignored

    finally:
        _leave_alt_screen()
        termios.tcsetattr(fd, termios.TCSADRAIN, original)


# ---------------------------------------------------------------------------
# Fallback: numbered prompt
# ---------------------------------------------------------------------------

def _select_with_prompt(title: str, options: list[MenuOption]) -> int | None:
    print(styled(title, STYLE_PROMPT))
    for index, option in enumerate(options, start=1):
        label = styled(option.label, BOLD)
        desc = styled(option.description, STYLE_DIM) if option.description else ""
        cur = styled(" *", STYLE_PROMPT) if option.is_current else ""
        if desc:
            max_label = max(visible_len(o.label) for o in options)
            padded = f"  {option.label}{cur}".ljust(max_label + 6)
            print(f"  {index}. {padded}{desc}")
        else:
            print(f"  {index}. {label}{cur}")
    print(f"  {styled('q.', STYLE_DIM)} Cancel")

    while True:
        choice = input("\nSelect option: ").strip().lower()
        if choice in {"q", "quit", "exit"}:
            return None
        try:
            idx = int(choice) - 1
        except ValueError:
            print("Unknown option.")
            continue
        if 0 <= idx < len(options):
            return idx
        print("Unknown option.")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

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


def confirm(title: str, default: bool = False) -> bool:
    """Show a yes/no confirmation menu.  Returns True for yes."""
    opts = [
        MenuOption("Yes", ""),
        MenuOption("No", "", is_current=not default),
    ]
    if default:
        opts[0] = MenuOption("Yes", "", is_current=True)
        opts[1] = MenuOption("No", "")
    selected = select_option(title, opts)
    return selected == 0
