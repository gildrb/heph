"""ANSI terminal helpers: styling, prompt rendering, spinner."""

from __future__ import annotations

import os
import re
import sys
import threading

# ANSI escape codes
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
RED = "\033[91m"
GREEN = "\033[32m"
YELLOW = "\033[33m"

MAGENTA = "\033[35m"

RESET = "\033[0m"

# Shortcuts for common styles
STYLE_PROMPT = f"{BOLD}{RED}"
STYLE_ACCENT = f"{BOLD}{GREEN}"
STYLE_DIM = DIM
STYLE_ERROR = f"{BOLD}{RED}"
STYLE_WARNING = f"{BOLD}{YELLOW}"
STYLE_MODE = f"{BOLD}{MAGENTA}"
STYLE_ASSISTANT = f"{BOLD}{RED}"


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


_BANNER = r"""
    __  __           __          _      __            
   / / / /__  ____  / /_  ____ _(_)____/ /_____  _____
  / /_/ / _ \/ __ \/ __ \/ __ `/ / ___/ __/ __ \/ ___/
 / __  /  __/ /_/ / / / / /_/ / (__  ) /_/ /_/ (__  ) 
/_/ /_/\___/ .___/_/ /_/\__,_/_/____/\__/\____/____/  
          /_/                                         
""".strip()


def print_banner(version: str = "") -> None:
    """Print the Hephaistos ASCII art banner centered across the terminal."""
    try:
        cols = os.get_terminal_size().columns
    except OSError:
        cols = 80
    lines = _BANNER.split("\n")
    banner_width = max(visible_len(line) for line in lines)
    pad = max(0, (cols - banner_width) // 2)
    for line in lines:
        sys.stdout.write(f"{' ' * pad}{RED}{BOLD}{line}{RESET}\n")
    if version:
        ver_text = f"v{version}"
        ver_pad = max(0, (cols - len(ver_text)) // 2)
        sys.stdout.write(f"\n{' ' * ver_pad}{styled(ver_text, STYLE_DIM)}\n")
    sys.stdout.write("\n")


def _center_line(text: str, width: int = 80) -> str:
    """Center a line of text (accounting for ANSI escape codes)."""
    vis = visible_len(text)
    pad = max(0, (width - vis) // 2)
    return f"{' ' * pad}{text}"


def print_shell_intro(
    version: str,
    armory_path: str | None,
    source_file_count: int,
    session_id: str,
    model: str,
    base_url: str,
    has_api_key: bool,
) -> None:
    """Print the full startup screen with banner, status, and tips."""
    try:
        cols = os.get_terminal_size().columns
    except OSError:
        cols = 80

    print_banner(version)

    # --- Status line ---
    armory_status = styled(str(armory_path), STYLE_ACCENT) if armory_path else styled("none", STYLE_DIM)
    api_status = styled("ok", GREEN) if has_api_key else styled("not configured", RED)
    model_display = styled(model, STYLE_PROMPT)

    status = f"{styled('armory', STYLE_DIM)} {armory_status}    {styled('model', STYLE_DIM)} {model_display}    {styled('api', STYLE_DIM)} {api_status}"
    if source_file_count:
        status += f"    {styled('context', STYLE_DIM)} {styled(f'{source_file_count} files', STYLE_ACCENT)}"
    print(_center_line(status, cols))
    print()

    # --- Tips ---
    tips = [
        f"Type {styled('/help', STYLE_ACCENT)} for commands  ·  {styled('/armory', STYLE_ACCENT)} to open a workspace  ·  {styled('!', STYLE_ACCENT)} prefix for shell mode",
    ]
    if not has_api_key:
        tips.insert(0, f"{styled('Set your API key:', STYLE_WARNING)} {styled('/api key <your-key>', STYLE_ACCENT)}")

    for tip in tips:
        print(_center_line(tip, cols))

    print()
