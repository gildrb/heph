from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Optional

from hephaistos.app.shell import run_chat_shell
from hephaistos.armory.cli import register as register_armory_commands
from hephaistos.chat.cli import register as register_chat_commands


def _find_bun() -> Optional[Path]:
    bun_path = shutil.which("bun")
    if bun_path:
        return Path(bun_path)
    return None


def _hide_subparser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    name: str,
) -> None:
    subparsers._choices_actions = [
        action
        for action in subparsers._choices_actions
        if getattr(action, "dest", None) != name
    ]


def build_parser() -> argparse.ArgumentParser:
    prog = Path(sys.argv[0]).name or "hephaistos"
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Chat-first study CLI.",
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        metavar="command",
    )

    register_armory_commands(subparsers)
    register_chat_commands(subparsers)
    _hide_subparser(subparsers, "chat")

    parser.add_argument(
        "--tui",
        action="store_true",
        help="Launch the rich TUI interface (requires bun)",
    )

    return parser


def run_argv(parser: argparse.ArgumentParser, argv: list[str]) -> None:
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return
    handler(args)


def _run_tui() -> int:
    """Launch the TUI: starts the WS server then runs bun.

    The WS server runs in a daemon thread so it is terminated when the
    parent process exits (i.e. when the TUI window is closed). This is
    acceptable for local dev usage where the TUI is the only interface.
    """
    bun_path = _find_bun()
    if bun_path is None:
        print(
            "error: bun is required for TUI mode. Install from https://bun.sh",
            file=sys.stderr,
        )
        return 1

    tui_script = Path(__file__).parent.parent.parent / "tui" / "src" / "index.tsx"
    if not tui_script.exists():
        print(f"error: TUI script not found at {tui_script}", file=sys.stderr)
        return 1

    from hephaistos.app import ws_server
    import threading
    import asyncio
    import time

    server_thread = threading.Thread(
        target=lambda: asyncio.run(ws_server.run_server()),
        daemon=True,
    )
    server_thread.start()
    time.sleep(0.5)

    try:
        result = subprocess.run(
            [str(bun_path), "run", str(tui_script)],
            check=True,
        )
        return result.returncode
    except subprocess.CalledProcessError as e:
        return e.returncode


def main() -> None:
    argv = sys.argv[1:]

    if "--tui" in argv:
        exit(_run_tui())

    parser = build_parser()

    if not argv:
        if sys.stdin.isatty() and sys.stdout.isatty():
            bun_path = _find_bun()
            if bun_path is not None:
                exit(_run_tui())
            else:
                run_chat_shell()
        else:
            parser.print_help()
        return

    run_argv(parser, argv)
