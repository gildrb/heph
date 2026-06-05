"""Run a real PTY stress test for TUI resize ghosting.

The Textual test harness can prove widget state, but terminal ghosting is a
cell-level artifact. This script launches ``heph`` in a pseudo-terminal,
drives resize sequences through the visible states that have regressed before,
and inspects the final terminal buffer for duplicate or stale chrome.
"""

from __future__ import annotations

import argparse
import fcntl
import os
import selectors
import shlex
import signal
import struct
import subprocess
import sys
import tempfile
import termios
import time
import warnings
from collections.abc import Iterable
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree, which

from interfaces.tui.display_text import COMPOSER_PLACEHOLDER

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WIDTH = 150
DEFAULT_HEIGHT = 30
NARROW_WIDTH = 74
NARROW_HEIGHT = 10
TERMINAL_CLEAR_SEQUENCE = "\x1b[2J"
WIDE_RESIZE_SEQUENCE = (
    (118, 23),
    (88, 12),
    (74, 8),
    (126, 24),
    (141, 27),
    (79, 9),
    (121, 18),
    (92, 11),
    (140, 24),
    (83, 10),
    (132, 22),
    (150, 30),
)
NARROW_RESIZE_SEQUENCE = (
    (141, 27),
    (118, 23),
    (83, 10),
    (132, 22),
    (92, 11),
    (126, 24),
    (88, 12),
    (121, 18),
    (79, 9),
    (74, 10),
)
TMUX_RESIZE_SEQUENCE = (
    (120, 30),
    (90, 20),
    (150, 38),
    (80, 14),
    (135, 32),
)


@dataclass(frozen=True, slots=True)
class StressCase:
    name: str
    input_bytes: bytes


@dataclass(frozen=True, slots=True)
class ResizeRun:
    name: str
    sequence: tuple[tuple[int, int], ...]
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class TerminalSnapshot:
    stream: str
    screen: str


@dataclass(frozen=True, slots=True)
class StressResult:
    case_name: str
    resize_run_name: str
    terminal_clear_seen: bool
    composer_prompt_count: int
    footer_count: int
    placeholder_count: int
    slash_help_count: int
    settings_count: int
    material_count: int
    armory_filter_count: int

    def summary(self) -> str:
        return (
            f"{self.resize_run_name}/{self.case_name}: clear={self.terminal_clear_seen} "
            f"composer_prompt={self.composer_prompt_count} "
            f"footer={self.footer_count} placeholder={self.placeholder_count} "
            f"slash_help={self.slash_help_count} settings={self.settings_count} "
            f"material={self.material_count} armory_filter={self.armory_filter_count}"
        )


def _resize_terminal(fd: int, width: int, height: int) -> None:
    winsize = struct.pack("HHHH", height, width, 0, 0)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)


def _read_available(fd: int, selector: selectors.DefaultSelector, timeout: float) -> str:
    chunks: list[bytes] = []
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        wait = max(0.0, min(0.025, deadline - time.monotonic()))
        events = selector.select(wait)
        if not events:
            continue
        try:
            chunk = os.read(fd, 65536)
        except (BlockingIOError, OSError):
            break
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks).decode("utf-8", errors="ignore")


def _parse_number(parts: list[str], index: int, default: int) -> int:
    if index >= len(parts):
        return default
    value = parts[index]
    return int(value) if value.isdigit() else default


def _move_cursor(
    command: str,
    parts: list[str],
    x: int,
    y: int,
    *,
    width: int,
    height: int,
) -> tuple[int, int]:
    distance = _parse_number(parts, 0, 1)
    if command == "A":
        return x, max(0, y - distance)
    if command == "B":
        return x, min(height - 1, y + distance)
    if command == "C":
        return min(width - 1, x + distance), y
    if command == "D":
        return max(0, x - distance), y
    return x, y


def _clear_screen(
    rows: list[list[str]],
    *,
    x: int,
    y: int,
    width: int,
    height: int,
    mode: int,
    private: bool,
) -> tuple[list[list[str]], int, int]:
    if mode in {2, 3} or private:
        return [[" "] * width for _ in range(height)], 0, 0
    if mode == 0:
        for row_index in range(y, height):
            start = x if row_index == y else 0
            for column in range(start, width):
                rows[row_index][column] = " "
    return rows, x, y


def _handle_escape_sequence(
    stream: str,
    index: int,
    rows: list[list[str]],
    x: int,
    y: int,
    *,
    width: int,
    height: int,
) -> tuple[int, list[list[str]], int, int]:
    if index + 1 >= len(stream) or stream[index + 1] != "[":
        return index + 2, rows, x, y
    index += 2
    params = ""
    while index < len(stream) and not ("@" <= stream[index] <= "~"):
        params += stream[index]
        index += 1
    if index >= len(stream):
        return index, rows, x, y

    command = stream[index]
    private = params.startswith("?")
    parts = [part for part in params.replace("?", "").split(";") if part]
    if command in {"H", "f"}:
        row = _parse_number(parts, 0, 1)
        column = _parse_number(parts, 1, 1)
        y = max(0, min(height - 1, row - 1))
        x = max(0, min(width - 1, column - 1))
    elif command == "J":
        mode = _parse_number(parts, 0, 0)
        rows, x, y = _clear_screen(
            rows,
            x=x,
            y=y,
            width=width,
            height=height,
            mode=mode,
            private=private,
        )
    elif command == "K":
        for column in range(x, width):
            rows[y][column] = " "
    elif command in {"A", "B", "C", "D"}:
        x, y = _move_cursor(command, parts, x, y, width=width, height=height)
    return index + 1, rows, x, y


def _parse_screen(stream: str, *, width: int, height: int) -> str:
    rows = [[" "] * width for _ in range(height)]
    x = 0
    y = 0
    index = 0
    while index < len(stream):
        char = stream[index]
        if char == "\x1b":
            index, rows, x, y = _handle_escape_sequence(
                stream,
                index,
                rows,
                x,
                y,
                width=width,
                height=height,
            )
            continue
        if char == "\r":
            x = 0
        elif char == "\n":
            y = min(height - 1, y + 1)
            x = 0
        elif char == "\b":
            x = max(0, x - 1)
        elif char >= " ":
            rows[y][x] = char
            x += 1
            if x >= width:
                x = 0
                y = min(height - 1, y + 1)
        index += 1
    return "\n".join("".join(row).rstrip() for row in rows)


def _run_heph(
    armory: Path,
    armory_home: Path,
) -> tuple[int, int, selectors.DefaultSelector, str]:
    pid, fd = os.forkpty()
    if pid == 0:
        os.environ["TERM"] = "xterm-256color"
        os.environ["HEPHAION_ARMORY_HOME"] = str(armory_home)
        os.environ["COLUMNS"] = "240"
        os.environ["LINES"] = "60"
        os.chdir(ROOT)
        os.execvp(sys.executable, [sys.executable, "-m", "hephaion", str(armory)])
    selector = selectors.DefaultSelector()
    selector.register(fd, selectors.EVENT_READ)
    _resize_terminal(fd, 130, 24)
    return pid, fd, selector, _read_available(fd, selector, 1.8)


def _close_heph(pid: int, fd: int, selector: selectors.DefaultSelector) -> None:
    try:
        os.write(fd, b"\x03")
        time.sleep(0.1)
    except OSError:
        pass
    with suppress(OSError):
        os.kill(pid, signal.SIGTERM)
    with suppress(ChildProcessError):
        os.waitpid(pid, 0)
    selector.close()
    with suppress(OSError):
        os.close(fd)


def _run_case(
    case: StressCase,
    *,
    armory: Path,
    armory_home: Path,
    resize_run: ResizeRun,
) -> TerminalSnapshot:
    pid, fd, selector, stream = _run_heph(armory, armory_home)
    try:
        if case.input_bytes:
            os.write(fd, case.input_bytes)
            stream += _read_available(fd, selector, 0.35)
        for resize_width, resize_height in resize_run.sequence:
            _resize_terminal(fd, resize_width, resize_height)
            os.kill(pid, signal.SIGWINCH)
            stream += _read_available(fd, selector, 0.055)
        stream += _read_available(fd, selector, 0.5)
        return TerminalSnapshot(
            stream=stream,
            screen=_parse_screen(stream, width=resize_run.width, height=resize_run.height),
        )
    finally:
        _close_heph(pid, fd, selector)


def _result_for_case(
    case: StressCase,
    resize_run: ResizeRun,
    snapshot: TerminalSnapshot,
) -> StressResult:
    screen = snapshot.screen
    return StressResult(
        case_name=case.name,
        resize_run_name=resize_run.name,
        terminal_clear_seen=TERMINAL_CLEAR_SEQUENCE in snapshot.stream,
        composer_prompt_count=_composer_prompt_count(screen),
        footer_count=screen.count("ctrl+o armory"),
        placeholder_count=screen.count(COMPOSER_PLACEHOLDER),
        slash_help_count=screen.count("/help"),
        settings_count=screen.count("Settings"),
        material_count=screen.count("resize-stress"),
        armory_filter_count=screen.count("Filter armory paths"),
    )


def _composer_prompt_count(screen: str) -> int:
    count = 0
    for line in screen.splitlines():
        stripped = line.lstrip()
        if not stripped.startswith(("->", "→")):
            continue
        if stripped.startswith(("-> @", "→ @")):
            continue
        count += 1
    return count


def _failure_reasons(result: StressResult) -> list[str]:
    failures: list[str] = []
    if not result.terminal_clear_seen:
        failures.append("terminal clear sequence was not observed")
    if result.case_name == "empty-placeholder":
        if result.composer_prompt_count != 1:
            failures.append("empty composer state did not end with exactly one prompt")
        if result.resize_run_name == "wide-final" and result.footer_count != 1:
            failures.append("empty composer state did not end with exactly one footer")
        if result.placeholder_count != 1:
            failures.append("empty composer state did not end with exactly one placeholder")
    elif result.case_name == "slash-completion":
        if result.composer_prompt_count != 1:
            failures.append("slash completion state did not end with exactly one prompt")
        if result.resize_run_name == "wide-final" and result.footer_count != 1:
            failures.append("slash completion state did not end with exactly one footer")
        if result.slash_help_count != 1:
            failures.append("slash completion menu did not end with exactly one /help row")
    elif result.case_name == "settings-inline":
        if result.composer_prompt_count != 1:
            failures.append("settings inline state did not end with exactly one prompt")
        if result.resize_run_name == "wide-final" and result.footer_count != 1:
            failures.append("settings inline state did not end with exactly one footer")
        if result.settings_count > 1:
            failures.append("settings inline state duplicated its title")
    elif result.case_name == "materials-inline":
        if result.footer_count > 1:
            failures.append("materials inline state duplicated footer chrome")
        if result.material_count < 1:
            failures.append("materials inline state lost the stress material")
    elif result.case_name == "armory-inline":
        if result.armory_filter_count != 1:
            failures.append("armory inline state did not end with one filter placeholder")
        if result.footer_count > 1:
            failures.append("armory inline state duplicated footer chrome")
    return failures


def _init_armory(path: Path, armory_home: Path) -> None:
    env = os.environ.copy()
    env["HEPHAION_ARMORY_HOME"] = str(armory_home)
    subprocess.run(
        [sys.executable, "-m", "hephaion", "armory", "init", str(path)],
        cwd=ROOT,
        env=env,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _prepare_armories() -> tuple[Path, Path]:
    armory_home = Path(tempfile.mkdtemp(prefix="heph-armory-home-"))
    armory = armory_home / "resize-target"
    sibling = armory_home / "other-armory"
    _init_armory(armory, armory_home)
    _init_armory(sibling, armory_home)
    materials = armory / "materials"
    materials.mkdir(exist_ok=True)
    material_text = "# Resize Stress\n\n" + (
        "A long resize verification sentence wraps cleanly. " * 12
    )
    (materials / "resize-stress.md").write_text(material_text, encoding="utf-8")
    return armory_home, armory


def _default_cases() -> tuple[StressCase, ...]:
    return (
        StressCase("empty-placeholder", b""),
        StressCase("slash-completion", b"/"),
        StressCase("settings-inline", b"/settings\r"),
        StressCase("materials-inline", b"/materials\r"),
        StressCase("armory-inline", b"/armory\r"),
    )


def _default_resize_runs(*, wide_width: int, wide_height: int) -> tuple[ResizeRun, ...]:
    return (
        ResizeRun(
            "wide-final",
            WIDE_RESIZE_SEQUENCE,
            wide_width,
            wide_height,
        ),
        ResizeRun(
            "narrow-final",
            NARROW_RESIZE_SEQUENCE,
            NARROW_WIDTH,
            NARROW_HEIGHT,
        ),
    )


def _run_stress(
    cases: Iterable[StressCase],
    resize_runs: Iterable[ResizeRun],
) -> int:
    armory_home, armory = _prepare_armories()
    try:
        failed = False
        for resize_run in resize_runs:
            for case in cases:
                snapshot = _run_case(
                    case,
                    armory=armory,
                    armory_home=armory_home,
                    resize_run=resize_run,
                )
                result = _result_for_case(case, resize_run, snapshot)
                print(result.summary())
                reasons = _failure_reasons(result)
                if reasons:
                    failed = True
                    for reason in reasons:
                        print(f"  - {reason}")
        return 1 if failed else 0
    finally:
        rmtree(armory_home, ignore_errors=True)


def _tmux_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("tmux", *args),
        check=True,
        capture_output=True,
        text=True,
    )


def _launch_tmux_heph(session: str, armory: Path, armory_home: Path) -> str:
    command = " ".join(
        (
            "TERM=xterm-256color",
            "COLUMNS=240",
            "LINES=60",
            f"HEPHAION_ARMORY_HOME={shlex.quote(str(armory_home))}",
            "uv run heph",
            shlex.quote(str(armory)),
        )
    )
    result = _tmux_command(
        "new-session",
        "-d",
        "-P",
        "-F",
        "#{pane_id}",
        "-s",
        session,
        "-x",
        "180",
        "-y",
        "40",
        "-c",
        str(ROOT),
        command,
    )
    return result.stdout.strip()


def _tmux_capture(session: str, pane: str) -> str:
    _tmux_command("split-window", "-h", "-p", "25", "-t", session, "sleep 60")
    time.sleep(1.0)
    _tmux_command("send-keys", "-t", pane, "/")
    time.sleep(1.0)
    for width, height in TMUX_RESIZE_SEQUENCE:
        _tmux_command("resize-pane", "-t", pane, "-x", str(width), "-y", str(height))
        time.sleep(0.25)
    time.sleep(1.0)
    return _tmux_command("capture-pane", "-p", "-t", pane, "-S", "-").stdout


def _tmux_failure_reasons(capture: str) -> list[str]:
    failures: list[str] = []
    max_width = max((len(line) for line in capture.splitlines()), default=0)
    checks = (
        ("composer prompt", _composer_prompt_count(capture), 1),
        ("slash help row", capture.count("/help"), 1),
        ("footer", capture.count("ctrl+o armory"), 1),
        ("grounding panel", capture.count("Grounding"), 1),
    )
    for label, actual, expected in checks:
        if actual != expected:
            failures.append(
                f"tmux split ended with {actual} {label} instances, expected {expected}"
            )
    if COMPOSER_PLACEHOLDER in capture:
        failures.append("tmux split left stale composer placeholder while slash menu was active")
    if max_width > 135:
        failures.append(f"tmux split captured a line wider than the Heph pane: {max_width}")
    return failures


def _run_tmux_stress() -> int:
    if which("tmux") is None:
        print("tmux stress skipped: tmux is not installed")
        return 0
    armory_home, armory = _prepare_armories()
    session = f"heph-resize-{os.getpid()}"
    try:
        pane = _launch_tmux_heph(session, armory, armory_home)
        time.sleep(3.0)
        capture = _tmux_capture(session, pane)
        max_width = max((len(line) for line in capture.splitlines()), default=0)
        print(
            "tmux-split/slash-completion: "
            f"composer_prompt={_composer_prompt_count(capture)} "
            f"slash_help={capture.count('/help')} "
            f"footer={capture.count('ctrl+o armory')} "
            f"grounding={capture.count('Grounding')} "
            f"max_width={max_width}"
        )
        reasons = _tmux_failure_reasons(capture)
        for reason in reasons:
            print(f"  - {reason}")
        return 1 if reasons else 0
    finally:
        with suppress(subprocess.CalledProcessError):
            _tmux_command("kill-session", "-t", session)
        rmtree(armory_home, ignore_errors=True)


def main() -> int:
    warnings.filterwarnings(
        "ignore",
        message=".*forkpty.*",
        category=DeprecationWarning,
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--tmux", action="store_true", help="also run a tmux split-pane stress")
    args = parser.parse_args()
    status = _run_stress(
        _default_cases(),
        _default_resize_runs(wide_width=args.width, wide_height=args.height),
    )
    if args.tmux:
        status = max(status, _run_tmux_stress())
    return status


if __name__ == "__main__":
    raise SystemExit(main())
