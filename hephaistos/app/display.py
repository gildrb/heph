"""ANSI terminal helpers: styling, prompt rendering, spinner."""

from __future__ import annotations

import re
import sys
import threading

# ANSI escape codes
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
RESET = "\033[0m"

# Shortcuts for common styles
STYLE_PROMPT = f"{BOLD}{CYAN}"
STYLE_ACCENT = f"{BOLD}{GREEN}"
STYLE_DIM = DIM
STYLE_ERROR = f"{BOLD}{RED}"
STYLE_WARNING = f"{BOLD}{YELLOW}"
STYLE_MODE = f"{BOLD}{MAGENTA}"
STYLE_ASSISTANT = f"{BOLD}{BLUE}"


def styled(text: str, style: str) -> str:
    return f"{style}{text}{RESET}"


def clear_line() -> None:
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()


def clear_screen() -> None:
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def move_cursor_up(n: int) -> None:
    if n > 0:
        sys.stdout.write(f"\033[{n}A")
        sys.stdout.flush()


def move_cursor_down(n: int) -> None:
    if n > 0:
        sys.stdout.write(f"\033[{n}B")
        sys.stdout.flush()


def move_cursor_to_column(col: int) -> None:
    sys.stdout.write(f"\r\033[{col + 1}C")
    sys.stdout.flush()


_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def visible_len(text: str) -> int:
    """Return the visible (non-ANSI) character count of a string."""
    return len(_ANSI_RE.sub("", text))


def build_prompt(armory_name: str | None, mode: str = "prompt") -> tuple[str, int]:
    """Build the styled prompt string. Returns (prompt_with_ansi, visible_length)."""
    if mode == "bash":
        prefix = styled("!", STYLE_MODE)
    else:
        prefix = styled(">", STYLE_PROMPT)

    if armory_name:
        label = styled(armory_name, STYLE_ACCENT)
    else:
        label = styled("heph", STYLE_DIM)

    prompt = f"{label} {prefix} "
    return prompt, visible_len(prompt)


def render_markdown_lite(text: str) -> str:
    """Render basic markdown to ANSI-styled terminal output.

    Handles: **bold**, *italic*, `code`, ```code blocks```.
    """
    import re

    result = text

    # Code blocks (triple backtick)
    def _code_block(m: re.Match[str]) -> str:
        lang = m.group(1) or ""
        code = m.group(2)
        header = styled(f"  {lang}", STYLE_DIM) if lang else ""
        lines = []
        for line in code.rstrip("\n").split("\n"):
            lines.append(styled(f"  {line}", STYLE_DIM))
        body = "\n".join(lines)
        return f"{header}\n{body}"

    result = re.sub(r"```(\w*)\n(.*?)```", _code_block, result, flags=re.DOTALL)

    # Inline code
    result = re.sub(r"`([^`]+)`", lambda m: styled(m.group(1), STYLE_DIM), result)

    # Bold
    result = re.sub(r"\*\*(.+?)\*\*", lambda m: styled(m.group(1), BOLD), result)

    # Italic (single * not preceded/followed by *)
    result = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", lambda m: styled(m.group(1), ITALIC), result)

    return result


class Spinner:
    """A simple terminal spinner that runs in a background thread."""

    FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")

    def __init__(self, message: str = "Thinking") -> None:
        self._message = message
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join()
            self._thread = None
            clear_line()

    def _spin(self) -> None:
        idx = 0
        while not self._stop_event.is_set():
            frame = self.FRAMES[idx % len(self.FRAMES)]
            clear_line()
            sys.stdout.write(f"\r{styled(frame, STYLE_PROMPT)} {self._message}")
            sys.stdout.flush()
            idx += 1
            self._stop_event.wait(0.08)


def print_error(msg: str) -> None:
    print(f"{styled('error:', STYLE_ERROR)} {msg}")


def print_warning(msg: str) -> None:
    print(f"{styled('warning:', STYLE_WARNING)} {msg}")


def print_info(msg: str) -> None:
    print(f"{styled('info:', STYLE_DIM)} {msg}")


def print_success(msg: str) -> None:
    print(f"{styled(msg, STYLE_ACCENT)}")
