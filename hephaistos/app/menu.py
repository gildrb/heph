"""Interactive menu helpers for TTY workflows.

Uses an alternate screen buffer so the user's terminal scrollback is
preserved.  Supports arrow-key / j-k navigation, inline search/filter,
visual borders, current-state markers, and a persistent footer with
keyboard hints.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import select
import sys
import time

if sys.platform != "win32":
    import termios
    import tty

from hephaistos.app.display import (
    BOLD,
    DIM,
    RESET,
    STYLE_DIM,
    STYLE_PROMPT,
    visible_len,
    styled,
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
# Border / frame drawing
# ---------------------------------------------------------------------------

def _hline(width: int, left: str, mid: str, right: str, fill: str = "─") -> str:
    return f"{left}{fill * (width - 2)}{right}"


def _render_menu(
    title: str,
    options: list[MenuOption],
    selected: int,
    filter_text: str,
    escape_pending: bool,
) -> int:
    """Render the menu into the alternate screen.  Returns visible height."""

    cols, _rows = _term_size()
    inner_w = min(cols - 4, 78)
    box_w = inner_w + 4

    _clear_screen()

    lines: list[str] = []

    # ── Top border with title ──
    title_styled = styled(f" {title} ", STYLE_PROMPT)
    title_vis = visible_len(title_styled)
    pad = max(0, inner_w - title_vis)
    # visible line = ─ pad_left ─ title ─ pad_right ─
    raw_title = f" {title} "
    raw_pad_l = pad // 2
    raw_pad_r = pad - raw_pad_l
    top = f"┌{'─' * raw_pad_l}{raw_title}{'─' * raw_pad_r}┐"
    lines.append(styled(top, STYLE_DIM))

    # ── Filter / header line ──
    if filter_text:
        filter_display = styled(f" search: {filter_text}", STYLE_PROMPT)
    else:
        filter_display = styled(" type to filter", DIM)
    filter_padded = filter_display + " " * max(0, inner_w - visible_len(filter_display))
    lines.append(f"│{filter_padded}│")
    lines.append(styled(f"├{'─' * inner_w}┤", STYLE_DIM))

    # ── Options ──
    max_label = max((visible_len(o.label) + (3 if o.is_current else 0) for o in options), default=0) if options else 0

    for idx, option in enumerate(options):
        prefix = " * " if option.is_current else "   "
        if idx == selected:
            marker = f"\033[7m {prefix}{option.label}"
            if option.description:
                inner = f" {prefix}{option.label}  "
                padded = inner.ljust(max_label + 6)
                raw = f"{padded}{option.description}"
            else:
                raw = f" {prefix}{option.label}"
            vis_raw = visible_len(raw)
            pad_r = max(0, inner_w - vis_raw - 2)
            lines.append(f"│\033[7m{raw}{' ' * pad_r}\033[0m│")
        else:
            label = styled(option.label, BOLD)
            cur_marker = styled(" *", STYLE_PROMPT) if option.is_current else ""
            desc = styled(option.description, STYLE_DIM) if option.description else ""
            if desc:
                inner = f" {prefix}{option.label}{cur_marker}  "
                vis_inner = visible_len(inner)
                pad_needed = max(0, max_label + 6 - vis_inner)
                padded = inner + " " * pad_needed
                raw = f"{padded}{desc}"
            else:
                raw = f" {prefix}{option.label}{cur_marker}"
            vis_raw = visible_len(raw)
            pad_r = max(0, inner_w - vis_raw - 2)
            lines.append(f"│{raw}{' ' * pad_r}│")

    # ── Separator ──
    lines.append(styled(f"├{'─' * inner_w}┤", STYLE_DIM))

    # ── Footer with keyboard hints ──
    if escape_pending:
        footer_text = styled(" Press Esc/q again to cancel ", "\033[1m\033[33m")
    else:
        footer_text = styled(" Enter select · ↑↓ navigate · Esc cancel · / filter ", STYLE_DIM)
    footer_pad = max(0, inner_w - visible_len(footer_text))
    lines.append(f"│{footer_text}{' ' * footer_pad}│")

    # ── Bottom border ──
    lines.append(styled(f"└{'─' * inner_w}┘", STYLE_DIM))

    sys.stdout.write("\r\n".join(lines))
    sys.stdout.flush()
    return len(lines)


# ---------------------------------------------------------------------------
# Filter logic
# ---------------------------------------------------------------------------

def _matches_filter(option: MenuOption, filter_text: str) -> bool:
    if not filter_text:
        return True
    ft = filter_text.lower()
    return ft in option.label.lower() or ft in option.description.lower()


# ---------------------------------------------------------------------------
# Interactive arrow-key selector (alternate screen)
# ---------------------------------------------------------------------------

_ESCAPE_GUARD_SECONDS = 2.0


def _select_with_arrow_keys(title: str, options: list[MenuOption]) -> int | None:
    fd = sys.stdin.fileno()
    original = termios.tcgetattr(fd)

    # Build filtered view state
    all_options = options
    filtered: list[tuple[int, MenuOption]] = []  # (original_index, option)
    filter_text = ""
    selected = 0
    escape_pending = False
    escape_time = 0.0

    def _rebuild_filtered() -> None:
        nonlocal filtered, selected
        filtered = [
            (i, o) for i, o in enumerate(all_options) if _matches_filter(o, filter_text)
        ]
        selected = min(selected, max(len(filtered) - 1, 0))

    _rebuild_filtered()

    try:
        _enter_alt_screen()
        tty.setraw(fd)

        while True:
            if not filtered:
                # Nothing matches — render empty state
                _clear_screen()
                cols, _ = _term_size()
                inner_w = min(cols - 4, 78)
                top = styled(f"┌{'─' * ((inner_w - visible_len(styled(f' {title} ', STYLE_PROMPT))) // 2)} {title} {'─' * ((inner_w - visible_len(styled(f' {title} ', STYLE_PROMPT))) // 2)}┐", STYLE_DIM)
                sys.stdout.write(f"{top}\r\n")
                msg = styled(f"  No matches for '{filter_text}'", STYLE_DIM)
                pad = max(0, inner_w - visible_len(msg) - 2)
                sys.stdout.write(f"│{msg}{' ' * pad}│\r\n")
                bot = styled(f"└{'─' * inner_w}┘", STYLE_DIM)
                sys.stdout.write(f"{bot}\r\n")
                sys.stdout.flush()

            else:
                _render_menu(title, [o for _, o in filtered], selected, filter_text, escape_pending)

            key = sys.stdin.read(1)

            # Reset escape guard on any non-escape key
            if key not in ("\x1b", "q"):
                escape_pending = False

            # ── Escape / q ──
            if key in {"q", "\x03"}:
                if escape_pending:
                    return None
                escape_pending = True
                escape_time = time.monotonic()
                continue

            if key == "\x1b":
                ready, _, _ = select.select([fd], [], [], 0.05)
                if not ready:
                    # Bare Escape
                    if escape_pending:
                        return None
                    escape_pending = True
                    escape_time = time.monotonic()
                    continue
                seq = sys.stdin.read(2)
                if seq == "[A":
                    selected = (selected - 1) % len(filtered) if filtered else 0
                    escape_pending = False
                elif seq == "[B":
                    selected = (selected + 1) % len(filtered) if filtered else 0
                    escape_pending = False
                else:
                    escape_pending = False
                continue

            # ── Enter ──
            if key in {"\r", "\n"}:
                if filtered:
                    return filtered[selected][0]
                return None

            # ── j / k navigation ──
            if key == "k":
                selected = (selected - 1) % len(filtered) if filtered else 0
                continue
            if key == "j":
                selected = (selected + 1) % len(filtered) if filtered else 0
                continue

            # ── Backspace (delete filter char) ──
            if key in ("\x7f", "\x08"):
                if filter_text:
                    filter_text = filter_text[:-1]
                    _rebuild_filtered()
                continue

            # ── Printable → append to filter ──
            if ord(key) >= 32:
                filter_text += key
                _rebuild_filtered()
                continue

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
            selected = int(choice) - 1
        except ValueError:
            print("Unknown option.")
            continue
        if 0 <= selected < len(options):
            return selected
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
