"""Chat-first interactive shell with rich terminal UX.

Features:
- Slash commands with tab-autocomplete
- Shell mode via ! prefix
- Arrow-key history navigation
- Multi-line input with backslash continuation
- Streaming interrupt via Ctrl+C
"""

from __future__ import annotations

import os
import select
import signal
import subprocess
import sys
import termios
import threading
import time
import tty
from pathlib import Path

from hephaistos.app.autocomplete import match_commands, format_suggestions
from hephaistos.app.commands import get_registry
from hephaistos.app.display import (
    BOLD,
    DIM,
    RED,
    RESET,
    STYLE_ACCENT,
    STYLE_ASSISTANT,
    STYLE_DIM,
    STYLE_ERROR,
    STYLE_PROMPT,
    build_prompt,
    print_error,
    print_info,
    print_shell_intro,
    print_success,
    styled,
    visible_len,
)
from hephaistos import __version__
from hephaistos.app.input_history import InputHistory
from hephaistos.app.menu import MenuOption, select_option
from hephaistos.armory.storage import ArmoryError, initialize, normalize_path
from hephaistos.chat import storage as chat_storage
from hephaistos.chat.engine import EngineError
from hephaistos.harness.permissions import classify_bash_command, tier_allows
from hephaistos.parameters.cli import load_config
from hephaistos.chat.session import (
    ChatSession,
    create_session,
    list_armory_sessions,
    resume_session,
    save_session,
    send_user_message,
    session_has_messages,
    validate_armory_path,
)


ARMORY_MENU_OPTIONS = [
    MenuOption("Open existing armory", "Attach a workspace and load its study context."),
    MenuOption("Create new armory", "Initialize a new workspace and start chatting in it."),
    MenuOption("Resume saved chat", "Pick a saved conversation from an armory."),
    MenuOption("List saved chats", "Show the saved sessions for an armory."),
    MenuOption("Detach armory", "Keep chatting without workspace context."),
    MenuOption("Cancel", "Return to the chat prompt."),
]

_HELP_FOOTER = styled(
    " Enter send · ↑↓ history · Tab complete · / commands · Ctrl+C cancel · Ctrl+D exit",
    STYLE_DIM,
)

_ESCAPE_GUARD_SECONDS = 2.0

_HISTORY_DIR = Path.home() / ".cache" / "hephaistos"


# ---------------------------------------------------------------------------
# Armory management (used by commands.py too)
# ---------------------------------------------------------------------------


def _discover_startup_armory() -> Path | None:
    candidates = [Path.cwd(), Path.cwd() / "armory"]
    for candidate in candidates:
        try:
            return validate_armory_path(str(candidate))
        except ArmoryError:
            continue
    return None


def _default_armory_input(session: ChatSession) -> str:
    if session.armory_path is not None:
        return str(session.armory_path)
    return str((Path.cwd() / "armory").resolve())


def _prompt_path(label: str, default: str) -> str:
    raw = input(f"{label} [{default}]: ").strip()
    return raw or default


def _save_before_switch(session: ChatSession) -> None:
    if not session.dirty:
        return
    if session.armory_path is None:
        print_info("Previous messages were not saved (no armory).")
        return
    try:
        path = save_session(session)
        print_success(f"Saved chat to {path}")
    except chat_storage.ChatStorageError as exc:
        print_error(str(exc))


def _start_fresh_session(session: ChatSession, armory_path: Path | None) -> ChatSession:
    _save_before_switch(session)
    new_session = create_session(session.config, armory_path)
    if armory_path is None:
        print_info("Detached armory. Chat is running without workspace context.")
    else:
        print_success(f"Using armory {armory_path}")
        if new_session.source_file_count:
            print_info(f"Loaded {new_session.source_file_count} file(s).")
    return new_session


def _open_armory(session: ChatSession) -> ChatSession:
    default_path = _default_armory_input(session)
    raw_path = _prompt_path("Armory path", default_path)
    try:
        armory_path = validate_armory_path(raw_path)
    except ArmoryError as exc:
        print_error(str(exc))
        return session
    return _start_fresh_session(session, armory_path)


def _create_armory(session: ChatSession) -> ChatSession:
    default_path = _default_armory_input(session)
    raw_path = _prompt_path("New armory path", default_path)
    armory_path = normalize_path(raw_path)
    try:
        initialize(armory_path)
    except ArmoryError as exc:
        print_error(str(exc))
        return session
    print_success(f"Initialized armory at {armory_path}")
    return _start_fresh_session(session, armory_path)


def _prompt_armory_for_sessions(session: ChatSession) -> Path | None:
    default_path = _default_armory_input(session)
    raw_path = _prompt_path("Armory path", default_path)
    try:
        return validate_armory_path(raw_path)
    except ArmoryError as exc:
        print_error(str(exc))
        return None


def _resume_saved_chat(session: ChatSession) -> ChatSession:
    armory_path = _prompt_armory_for_sessions(session)
    if armory_path is None:
        return session
    sessions = list_armory_sessions(armory_path)
    if not sessions:
        print_info("No saved chats found.")
        return session
    options = [
        MenuOption(
            entry["title"] or entry["session_id"],
            f"{entry['session_id']}  {entry['updated_at']}",
        )
        for entry in sessions
    ]
    selected = select_option("Resume Saved Chat", options)
    if selected is None:
        return session
    entry = sessions[selected]
    _save_before_switch(session)
    try:
        resumed = resume_session(session.config, armory_path, entry["session_id"])
    except chat_storage.ChatStorageError as exc:
        print_error(str(exc))
        return session
    print_success(f"Resumed session {resumed.session_id}")
    if resumed.title:
        print_info(f"Title: {resumed.title}")
    return resumed


def _list_saved_chats(session: ChatSession) -> None:
    armory_path = _prompt_armory_for_sessions(session)
    if armory_path is None:
        return
    sessions = list_armory_sessions(armory_path)
    if not sessions:
        print_info("No saved chats found.")
        return
    print(f"Saved chats for {armory_path}:")
    for entry in sessions:
        title = entry["title"] or "(untitled)"
        print(f"  {entry['session_id']}  {title}  ({entry['updated_at']})")


def _handle_armory_command(session: ChatSession) -> ChatSession:
    selected = select_option("Armory", ARMORY_MENU_OPTIONS)
    if selected is None or selected == 5:
        return session
    if selected == 0:
        return _open_armory(session)
    if selected == 1:
        return _create_armory(session)
    if selected == 2:
        return _resume_saved_chat(session)
    if selected == 3:
        _list_saved_chats(session)
        return session
    if selected == 4:
        return _start_fresh_session(session, None)
    return session


# ---------------------------------------------------------------------------
# Line editor (raw terminal)
# ---------------------------------------------------------------------------


class _LineEditor:
    """A minimal line editor with history, autocomplete, and multi-line."""

    def __init__(self, history: InputHistory) -> None:
        self.history = history
        self.buf = ""
        self.cursor = 0
        self._suggestion_lines: list[str] = []
        self._suggestion_index: int = -1
        self._current_matches: list = []  # list[CommandSuggestion]
        self._escape_pending: bool = False
        self._escape_time: float = 0.0
        self._show_footer: bool = True
        self._first_render: bool = True
        self._flash_message: str = ""  # printed above the panel once
        self._flash_displayed: bool = False  # True after flash has been drawn

    def _reset_suggestion_index(self) -> None:
        """Reset suggestion selection when buffer content changes."""
        self._suggestion_index = -1

    def _handle_arrow(self, key: str, session: ChatSession, fd: int) -> None:
        """Handle an arrow key (A=up, B=down, C=right, D=left)."""
        if key == "A":  # Up
            if self._current_matches:
                if self._suggestion_index <= 0:
                    self._suggestion_index = len(self._current_matches) - 1
                else:
                    self._suggestion_index -= 1
            else:
                self.buf = self.history.up(self.buf)
                self.cursor = len(self.buf)
            self._render(session)
        elif key == "B":  # Down
            if self._current_matches:
                if self._suggestion_index >= len(self._current_matches) - 1:
                    self._suggestion_index = 0
                else:
                    self._suggestion_index += 1
            else:
                self.buf = self.history.down(self.buf)
                self.cursor = len(self.buf)
            self._render(session)
        elif key == "C":  # Right
            if self.cursor < len(self.buf):
                self.cursor += 1
                self._render(session)
        elif key == "D":  # Left
            if self.cursor > 0:
                self.cursor -= 1
                self._render(session)
        elif key == "3":  # Delete key (CSI 3 ~)
            os.read(fd, 1)  # consume ~
            if self.cursor < len(self.buf):
                self.buf = self.buf[: self.cursor] + self.buf[self.cursor + 1 :]
                self._reset_suggestion_index()
                self._render(session)

    def _prompt_str(self, session: ChatSession) -> tuple[str, int]:
        armory_name = session.armory_path.name if session.armory_path else None
        mode = "bash" if self.buf.startswith("!") else "prompt"
        return build_prompt(armory_name, mode)

    def _render(self, session: ChatSession) -> None:
        prompt, prompt_vis_len = self._prompt_str(session)

        # Get terminal width for the chatbox border
        try:
            cols = os.get_terminal_size().columns
        except OSError:
            cols = 80

        # Ensure minimum width for box-drawing
        cols = max(cols, 20)

        # ── Move cursor to the top-border line and clear everything below ──
        # The panel layout from top to bottom is:
        #   0: blank spacer line
        #   1: top border (╭───╮)
        #   2: input line  (│▌ prompt text)
        #   3..N: suggestions (if any)
        #   N+1: bottom border (╰───╯)
        #   N+2: footer (if shown)
        #
        # When _render is called, the cursor sits on the input line (row 2
        # relative to the panel).  We move up two lines to the spacer row
        # so we can overwrite the entire panel in place.
        #
        # On the very first render we push the panel to the bottom of the
        # terminal using cursor positioning so it always anchors at the
        # viewport edge regardless of how much intro text precedes it.

        if self._first_render:
            self._first_render = False
            self._suggestion_lines = []
            # Push the panel to the bottom of the terminal viewport.
            # Panel height: spacer(1) + top border(1) + input line(1)
            #   + suggestions(0 on first render) + bottom border(1)
            #   + footer(1) = 5 lines.
            panel_height = 5
            try:
                rows = os.get_terminal_size().lines
            except OSError:
                rows = 24
            sys.stdout.write(f"\033[{rows};1H")       # move to last row
            sys.stdout.write(f"\033[{panel_height}A")  # move up by panel height
        else:
            # When a flash message was displayed on the previous render, it sits
            # one line above the spacer.  Go up one extra line to erase it.
            up_lines = 3 if self._flash_displayed else 2
            sys.stdout.write(f"\033[{up_lines}A\r")
            sys.stdout.write("\033[J")     # clear from there to end of screen
            self._suggestion_lines = []
            self._flash_displayed = False

            # Print any pending flash message (e.g. error) above the panel
            if self._flash_message:
                sys.stdout.write(self._flash_message + "\r\n")
                self._flash_message = ""
                self._flash_displayed = True

            # Blank line for breathing room above the chatbox
            sys.stdout.write("\r\n")

        # ── Draw the full chatbox panel ──

        # Top border: ╭─...─╮ (bold cyan)
        corner_tl = styled("╭", RED)
        corner_tr = styled("╮", RED)
        top_fill = styled("─" * (cols - 2), RED)
        sys.stdout.write(f"{corner_tl}{top_fill}{corner_tr}\033[K\r\n")

        # Borders for content lines
        corner_left = styled("│ ", RED)
        corner_right = styled(" │", RED)
        content_width = cols - 4  # subtract left "│ " and right " │"

        # Input line: │▌ prompt input │
        accent_bar = styled("▌ ", STYLE_PROMPT)
        input_content = f"{accent_bar}{prompt}{self.buf}"
        input_vis = visible_len(input_content)
        pad = max(0, content_width - input_vis)
        sys.stdout.write(f"{corner_left}{input_content}{' ' * pad}{corner_right}\033[K")

        # If typing a slash command, show suggestions below the prompt
        stripped = self.buf.lstrip()
        if stripped.startswith("/") and " " not in stripped:
            registry = get_registry()
            matches = match_commands(stripped, registry.suggestions())
            self._current_matches = matches
            if matches:
                suggestions = format_suggestions(matches, selected=self._suggestion_index)
                for sug in suggestions:
                    sug_vis = visible_len(sug)
                    sug_pad = max(0, content_width - sug_vis)
                    sys.stdout.write(f"\r\n{corner_left}{sug}{' ' * sug_pad}{corner_right}")
                self._suggestion_lines = suggestions
        else:
            self._current_matches = []

        # Bottom border: ╰─...─╯
        corner_bl = styled("╰", RED)
        corner_br = styled("╯", RED)
        bottom_fill = styled("─" * (cols - 2), RED)
        sys.stdout.write(f"\r\n{corner_bl}{bottom_fill}{corner_br}\033[K")

        # Footer line below the border
        footer_lines = 0
        if self._show_footer:
            if self._escape_pending:
                footer = styled(" Press Esc again to cancel input", "\033[1m\033[33m")
            else:
                footer = _HELP_FOOTER
            sys.stdout.write(f"\r\n{footer}\033[K")
            footer_lines = 1

        # Move cursor back to the input line and to correct column
        lines_below_input = len(self._suggestion_lines) + 1 + footer_lines  # +1 for bottom border
        if lines_below_input:
            sys.stdout.write(f"\033[{lines_below_input}A")
        # vis_col: "│ " (2) + "▌ " (2) + prompt + cursor
        left_border_vis = 2  # "│ "
        accent_vis = 2  # "▌ "
        vis_col = left_border_vis + accent_vis + prompt_vis_len + self.cursor
        sys.stdout.write(f"\r\033[{vis_col}C")
        sys.stdout.flush()

    def _clear_suggestions(self) -> None:
        # Cursor is on the input line. Move up to the top-border row, then
        # erase everything from there to end of screen.  This removes the
        # top border, input line, suggestions, bottom border, and footer in
        # one shot so the chatbox panel is completely cleared.
        sys.stdout.write("\033[2A\r")  # up to blank line above top-border
        sys.stdout.write("\033[J")     # clear from there to end of screen
        self._suggestion_lines = []
        self._suggestion_index = -1
        self._current_matches = []

    def _read_char(self, fd: int) -> str:
        """Read one byte from fd directly, returning it as a single char."""
        b = os.read(fd, 1)
        if not b:
            return ""
        byte = b[0]
        if byte < 0x80:
            return b.decode("utf-8")
        # Multi-byte UTF-8: figure out length and read continuation bytes
        if byte < 0xE0:
            needed = 1
        elif byte < 0xF0:
            needed = 2
        else:
            needed = 3
        buf = b
        for _ in range(needed):
            extra = os.read(fd, 1)
            if not extra:
                break
            buf += extra
        return buf.decode("utf-8", errors="replace")

    def read_line(self, session: ChatSession) -> str | None:
        """Read a line with full editing. Returns None on Ctrl+D."""
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        self.buf = ""
        self.cursor = 0
        self._suggestion_lines = []
        self._suggestion_index = -1
        self._current_matches = []
        self._escape_pending = False
        self._escape_time = 0.0
        self._show_footer = True
        multiline_parts: list[str] = []

        try:
            tty.setraw(fd)
            self._render(session)

            while True:
                ch = self._read_char(fd)

                # Reset escape guard on any key other than Escape
                if ch != "\x1b":
                    self._escape_pending = False

                # Ctrl+C — cancel current input
                if ch == "\x03":
                    self._clear_suggestions()
                    self._show_footer = False
                    sys.stdout.write("\r\n")
                    sys.stdout.flush()
                    return ""

                # Ctrl+D — exit
                if ch == "\x04":
                    self._clear_suggestions()
                    self._show_footer = False
                    sys.stdout.write("\r\n")
                    sys.stdout.flush()
                    return None

                # Enter
                if ch in ("\r", "\n"):
                    # Empty / whitespace input — stay in the editor, do nothing
                    if not self.buf.strip() and not multiline_parts:
                        continue

                    self._clear_suggestions()
                    self._show_footer = False

                    # Backslash continuation for multi-line
                    if self.buf.endswith("\\"):
                        self.buf = self.buf[:-1]
                        multiline_parts.append(self.buf)
                        sys.stdout.write("\r\n  ")
                        sys.stdout.flush()
                        self.buf = ""
                        self.cursor = 0
                        self._show_footer = True
                        continue

                    result = "".join(multiline_parts) + self.buf
                    sys.stdout.write("\r\n")
                    sys.stdout.flush()
                    self.buf = ""
                    self.cursor = 0
                    return result

                # Backspace / Delete
                if ch in ("\x7f", "\x08"):
                    if self.cursor > 0:
                        self.buf = self.buf[: self.cursor - 1] + self.buf[self.cursor :]
                        self.cursor -= 1
                    self._reset_suggestion_index()
                    self._render(session)
                    continue

                # Escape sequences
                if ch == "\x1b":
                    ready, _, _ = select.select([fd], [], [], 0.1)
                    if not ready:
                        # Bare Escape — two-press exit guard
                        if self._escape_pending and (time.monotonic() - self._escape_time < _ESCAPE_GUARD_SECONDS):
                            self._clear_suggestions()
                            self._show_footer = False
                            sys.stdout.write("\r\n")
                            sys.stdout.flush()
                            return ""
                        self._escape_pending = True
                        self._escape_time = time.monotonic()
                        self._render(session)
                        continue
                    seq = self._read_char(fd)
                    # Handle both CSI [A-D and SS3 OA-OD (normal + app mode)
                    if seq == "[":
                        arrow = self._read_char(fd)
                        self._handle_arrow(arrow, session, fd)
                    elif seq == "O":
                        arrow = self._read_char(fd)
                        self._handle_arrow(arrow, session, fd)
                    continue

                # Tab — autocomplete
                if ch == "\t":
                    if self._suggestion_index >= 0 and self._current_matches:
                        # Complete to the highlighted suggestion
                        idx = self._suggestion_index
                        if idx < len(self._current_matches):
                            cmd = self._current_matches[idx]
                            stripped = self.buf.lstrip()
                            prefix_len = len(self.buf) - len(stripped)
                            self.buf = self.buf[:prefix_len] + "/" + cmd.name + " "
                            self.cursor = len(self.buf)
                            self._suggestion_index = -1
                    else:
                        stripped = self.buf.lstrip()
                        if stripped.startswith("/") and " " not in stripped:
                            registry = get_registry()
                            matches = match_commands(stripped, registry.suggestions())
                            if len(matches) == 1:
                                # Auto-complete to the single match
                                prefix_len = len(self.buf) - len(stripped)
                                self.buf = self.buf[:prefix_len] + "/" + matches[0].name + " "
                                self.cursor = len(self.buf)
                    self._render(session)
                    continue

                # Ctrl+A — home
                if ch == "\x01":
                    self.cursor = 0
                    self._render(session)
                    continue

                # Ctrl+E — end
                if ch == "\x05":
                    self.cursor = len(self.buf)
                    self._render(session)
                    continue

                # Ctrl+U — clear line
                if ch == "\x15":
                    self.buf = self.buf[self.cursor :]
                    self.cursor = 0
                    self._reset_suggestion_index()
                    self._render(session)
                    continue

                # Ctrl+K — kill to end
                if ch == "\x0b":
                    self.buf = self.buf[: self.cursor]
                    self._reset_suggestion_index()
                    self._render(session)
                    continue

                # Regular printable character
                if ord(ch) >= 32:
                    self.buf = self.buf[: self.cursor] + ch + self.buf[self.cursor :]
                    self.cursor += 1
                    self._reset_suggestion_index()
                    self._render(session)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


# ---------------------------------------------------------------------------
# Main shell loop
# ---------------------------------------------------------------------------


def _print_shell_intro(session: ChatSession) -> None:
    print_shell_intro(
        version=__version__,
        armory_path=str(session.armory_path) if session.armory_path else None,
        source_file_count=session.source_file_count or 0,
        session_id=session.session_id,
        model=session.config.model,
        base_url=session.config.base_url,
        has_api_key=bool(session.config.api_key),
    )


def _get_history_path(session: ChatSession) -> Path:
    if session.armory_path:
        # Per-armory history
        return session.armory_path / ".hephaistos" / "history.json"
    return _HISTORY_DIR / "default_history.json"


def _run_shell_command(cmd: str) -> None:
    """Execute a shell command and display output."""
    print(styled(f"$ {cmd}", STYLE_DIM))
    try:
        subprocess.run(cmd, shell=True, capture_output=False, text=True)
    except Exception as exc:
        print_error(str(exc))


def _handle_input(session: ChatSession, user_input: str, history: InputHistory, editor: _LineEditor | None = None) -> tuple[ChatSession, bool]:
    """Process a single input. Returns (session, should_continue)."""
    if not user_input:
        return session, True

    # Shell mode: !command
    if user_input.startswith("!"):
        cmd = user_input[1:].strip()
        if cmd:
            history.add(user_input)
            required_tier = classify_bash_command(cmd)
            if not tier_allows(required_tier, session.autonomy):
                print_error(
                    f"Permission denied: command requires '{required_tier}' autonomy "
                    f"(current: '{session.autonomy}')"
                )
            else:
                _run_shell_command(cmd)
        return session, True

    # Slash commands
    if user_input.startswith("/"):
        history.add(user_input)
        stripped = user_input.strip()
        if stripped == "/":
            # Bare "/" — treat as /help
            registry = get_registry()
            cmd = registry.find("help")
            if cmd:
                cmd.handle(session, "")
            return session, True
        space_idx = stripped.find(" ")
        if space_idx == -1:
            cmd_name = stripped[1:].lower()
            cmd_args = ""
        else:
            cmd_name = stripped[1:space_idx].lower()
            cmd_args = stripped[space_idx + 1:].strip()

        registry = get_registry()
        cmd = registry.find(cmd_name)
        if cmd is None:
            print_error(f"Unknown command: {stripped}")
            print_info("Type /help for available commands.")
            return session, True

        result = cmd.handle(session, cmd_args)

        if result.should_exit:
            return session, False

        if result.new_session is not None:
            session = result.new_session  # type: ignore[assignment]

        # Handle /edit resend
        if result.output and result.output.startswith("__RESEND__:"):
            new_input = result.output[len("__RESEND__:"):]
            history.add(new_input)
            print(f"\r{styled('Assistant:', STYLE_ASSISTANT)} ", end="", flush=True)
            abort = threading.Event()
            try:
                send_user_message(session, new_input, abort=abort)
            except EngineError as exc:
                if editor:
                    editor._flash_message = f"{styled('error:', STYLE_ERROR)} {exc}"
                else:
                    print_error(str(exc))
            print()

        return session, True

    # Normal LLM prompt
    history.add(user_input)
    print(f"\r{styled('Assistant:', STYLE_ASSISTANT)} ", end="", flush=True)
    abort = threading.Event()
    try:
        send_user_message(session, user_input, abort=abort)
    except EngineError as exc:
        if editor:
            editor._flash_message = f"{styled('error:', STYLE_ERROR)} {exc}"
        else:
            print_error(str(exc))
    print()
    return session, True


def _save_on_exit(session: ChatSession) -> None:
    if session.armory_path is not None and session.dirty and session_has_messages(session):
        try:
            path = save_session(session)
            print_success(f"Saved chat to {path}")
        except chat_storage.ChatStorageError as exc:
            print_error(str(exc))


def run_chat_shell(session: ChatSession | None = None) -> None:
    """Run the interactive chat shell with rich terminal UX."""
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        _run_fallback_shell(session)
        return

    if session is None:
        config = load_config()
        session = create_session(config, _discover_startup_armory())

    _print_shell_intro(session)

    history_path = _get_history_path(session)
    history = InputHistory.load(history_path)
    editor = _LineEditor(history)

    # Set up Ctrl+C handler for streaming interrupt
    abort_event = threading.Event()
    original_sigint = signal.getsignal(signal.SIGINT)

    def _sigint_handler(signum: int, frame: object) -> None:
        abort_event.set()

    while True:
        try:
            signal.signal(signal.SIGINT, original_sigint)
            user_input = editor.read_line(session)
        except (termios.error, OSError):
            # Terminal not available for raw mode
            signal.signal(signal.SIGINT, original_sigint)
            _run_fallback_shell(session)
            return

        if user_input is None:
            # Ctrl+D
            break

        if not user_input:
            continue

        # Install interrupt handler during LLM call
        signal.signal(signal.SIGINT, _sigint_handler)
        abort_event.clear()

        session, should_continue = _handle_input(session, user_input, history, editor)

        # Restore normal SIGINT
        signal.signal(signal.SIGINT, original_sigint)

        if not should_continue:
            break

    # Save history
    try:
        history.save(history_path)
    except OSError as exc:
        sys.stderr.write(f"Warning: failed to save history: {exc}\n")

    _save_on_exit(session)


def _run_fallback_shell(session: ChatSession | None = None) -> None:
    """Simple fallback shell when raw terminal is not available."""
    if session is None:
        config = load_config()
        session = create_session(config, _discover_startup_armory())

    print("Hephaistos (basic mode)")
    history = InputHistory()

    while True:
        try:
            armory_name = session.armory_path.name if session.armory_path else "heph"
            user_input = input(f"{armory_name}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        session, should_continue = _handle_input(session, user_input, history)
        if not should_continue:
            break

    _save_on_exit(session)
