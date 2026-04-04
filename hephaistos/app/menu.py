"""Interactive menu helpers for TTY workflows.

Uses an alternate screen buffer so the user's terminal scrollback is
preserved.  Supports arrow-key navigation only (no typing).
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
    RED,
    RESET,
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


def _pad_to(text: str, width: int) -> str:
    """Pad *text* with trailing spaces so its visible width equals *width*."""
    vis = visible_len(text)
    if vis >= width:
        return text
    return text + " " * (width - vis)


# Box-drawing characters
_BOX_TL = "╭"
_BOX_TR = "╮"
_BOX_BL = "╰"
_BOX_BR = "╯"
_BOX_H = "─"
_BOX_V = "│"

# Style for the box border
_BOX_STYLE = RED


def _box_line(content: str, inner_width: int, left: str, right: str, style: str = _BOX_STYLE) -> str:
    """Render a content line wrapped in box vertical characters, padded to *inner_width*."""
    padded = _pad_to(content, inner_width)
    return f"{style}{left}{RESET}{padded}{style}{right}{RESET}"


def _box_horizontal(fill_char: str, inner_width: int, left: str, right: str, style: str = _BOX_STYLE) -> str:
    """Render a horizontal box line (top or bottom border)."""
    return f"{style}{left}{fill_char * inner_width}{right}{RESET}"


def _render_menu(
    title: str,
    options: list[MenuOption],
    selected: int,
) -> int:
    """Render the full-viewport menu inside a box.  Returns the number of lines written."""

    cols, rows = _term_size()
    _clear_screen()

    # Inner width: leave 4 columns margin on each side for the box + padding
    box_inner = max(20, cols - 8)

    # ── Build content lines ──
    content: list[str] = []

    # Blank line above title
    content.append("")

    # Title line: ⚡ Hephaistos — {title} ⚡
    title_text = styled(f"  ⚡ Hephaistos — {title} ⚡  ", STYLE_PROMPT)
    content.append(_box_line(_center(title_text, box_inner), box_inner, _BOX_V, _BOX_V))

    # Separator line inside box
    sep_inner = styled(f"{_BOX_H * box_inner}", _BOX_STYLE)
    content.append(f"{_BOX_STYLE}{_BOX_V}{RESET}{sep_inner}{_BOX_STYLE}{_BOX_V}{RESET}")

    content.append(_box_line("", box_inner, _BOX_V, _BOX_V))  # blank line

    # Options
    for idx, option in enumerate(options):
        if idx == selected:
            arrow = styled("  ▸ ", STYLE_ACCENT)
            label = styled(option.label, BOLD)
            line_text = f"{arrow}{label}"
        else:
            label = styled(option.label, STYLE_DIM)
            line_text = f"    {label}"
        content.append(_box_line(line_text, box_inner, _BOX_V, _BOX_V))

        if option.description:
            if idx == selected:
                desc = styled(f"      {option.description}", STYLE_DIM)
            else:
                desc = styled(f"      {option.description}", STYLE_DIM)
            content.append(_box_line(desc, box_inner, _BOX_V, _BOX_V))
        else:
            content.append(_box_line("", box_inner, _BOX_V, _BOX_V))  # spacing

    content.append(_box_line("", box_inner, _BOX_V, _BOX_V))  # blank line

    # Bottom separator inside box
    content.append(f"{_BOX_STYLE}{_BOX_V}{RESET}{sep_inner}{_BOX_STYLE}{_BOX_V}{RESET}")

    # Footer inside box
    footer = styled("  ↑↓ navigate · Enter select · Esc cancel  ", STYLE_DIM)
    content.append(_box_line(_center(footer, box_inner), box_inner, _BOX_V, _BOX_V))

    # Blank line below footer
    content.append("")

    # ── Assemble with top/bottom borders ──
    output_lines: list[str] = []

    # Top border
    top_border = _box_horizontal(_BOX_H, box_inner, _BOX_TL, _BOX_TR)
    bottom_border = _box_horizontal(_BOX_H, box_inner, _BOX_BL, _BOX_BR)

    # Vertically center the whole block
    total_lines = 1 + len(content) + 1  # top_border + content + bottom_border
    top_pad = max(0, (rows - total_lines) // 2)
    for _ in range(top_pad):
        output_lines.append("")

    output_lines.append(top_border)
    output_lines.extend(content)
    output_lines.append(bottom_border)

    sys.stdout.write("\r\n".join(output_lines))
    sys.stdout.flush()
    return len(output_lines)


# ---------------------------------------------------------------------------
# Escape sequence reader (robust)
# ---------------------------------------------------------------------------

def _read_escape_sequence(fd: int) -> str | None:
    """After reading \\x1b, consume the rest of an escape sequence.

    Returns a canonical key name:
      "up", "down", "left", "right", "delete", "escape" for bare Escape,
      or None for unrecognized sequences (silently consumed).
    A bare Escape (no following bytes within 200 ms) returns "escape".
    Unrecognized sequences return None so the caller can ignore them.
    """
    ready, _, _ = select.select([fd], [], [], 0.2)
    if not ready:
        return "escape"  # bare Escape

    ch = os.read(fd, 1)
    if not ch:
        return "escape"

    b = ch[0]

    # CSI sequence: ESC [ ... final_byte
    if b == 0x5B:  # '['
        # Read parameter bytes and intermediate bytes until final byte (0x40..0x7E)
        params = b""
        while True:
            r, _, _ = select.select([fd], [], [], 0.1)
            if not r:
                return None  # incomplete/unrecognized CSI → ignore
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
                    return None  # unrecognized CSI → ignore
            elif 0x20 <= nb <= 0x3F:
                params += next_byte
            else:
                return None

    # SS3 sequence: ESC O ...
    if b == 0x4F:  # 'O'
        r, _, _ = select.select([fd], [], [], 0.1)
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

    # Any other escape initiator that we don't recognize → ignore
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
                if key == "escape":
                    # Bare Escape → cancel
                    return None
                elif key == "up":
                    selected = (selected - 1) % len(options) if options else 0
                elif key == "down":
                    selected = (selected + 1) % len(options) if options else 0
                # left/right/delete/unrecognized → ignore
                continue

            # ── Ctrl+C → cancel ──
            if byte == 0x03:
                return None

            # ── Enter ──
            if byte in (0x0D, 0x0A):
                return selected if options else None

            # All other keys (including printable characters) are ignored

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
