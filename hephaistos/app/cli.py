from __future__ import annotations

import argparse
import cProfile
import pstats
import sys
import tracemalloc
from datetime import UTC, datetime
from importlib.metadata import version as _pkg_version
from pathlib import Path

from hephaistos.analytics import init_analytics, shutdown_analytics
from hephaistos.app.shell import run_chat_shell
from hephaistos.armory.cli import register as register_armory_commands
from hephaistos.chat.cli import register as register_chat_commands
from hephaistos.chat.cli import resolve_armory_session
from hephaistos.observability import init_observability, shutdown_observability
from hephaistos.parameters.cli import (
    register as register_config_commands,
)
from hephaistos.source.cli import register as register_source_commands


def _package_version() -> str:
    try:
        return _pkg_version("hephaistos")
    except Exception:
        return "0.1.0"


def _version_string() -> str:
    """Lazy version string — avoids importlib.metadata scan at import time."""
    return f"%(prog)s {_package_version()}"


def _hide_subparser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],  # type: ignore[reportPrivateUsage]
    name: str,
) -> None:
    subparsers._choices_actions = [
        action for action in subparsers._choices_actions if getattr(action, "dest", None) != name
    ]


def _cmd_start(args: argparse.Namespace) -> None:
    """Start the interactive shell, optionally attached to a specific armory."""
    if args.path:
        session = resolve_armory_session(args.path)
        run_chat_shell(session)
        return
    run_chat_shell()


def _get_subcommand_names(parser: argparse.ArgumentParser) -> set[str]:
    """Return the set of registered subcommand names."""
    for action in parser._actions:  # type: ignore[reportPrivateUsage]
        if isinstance(action, argparse._SubParsersAction):  # type: ignore[reportPrivateUsage]
            return set(action.choices.keys())  # type: ignore[reportUnknownMemberType,reportUnknownArgumentType]
    return set()


def _inject_start_if_path(argv: list[str], known_commands: set[str]) -> list[str]:
    """Prepend 'start' if the first non-flag arg is not a known subcommand."""
    for i, arg in enumerate(argv):
        if not arg.startswith("-"):
            if arg not in known_commands:
                return [*argv[:i], "start", *argv[i:]]
            break
    return argv


def build_parser() -> argparse.ArgumentParser:
    prog = Path(sys.argv[0]).name or "hephaistos"
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Chat-first study CLI.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=_version_string(),
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Enable CPU profiling (cProfile) for this session",
    )
    parser.add_argument(
        "--profile-memory",
        action="store_true",
        help="Enable memory profiling (tracemalloc) for this session",
    )
    subparsers = parser.add_subparsers(
        dest="command",
        metavar="command",
    )

    # Hidden backwards-compatible alias: `heph start [path]`
    start = subparsers.add_parser(
        "start",
        help=argparse.SUPPRESS,
    )
    start.add_argument("path", nargs="?", help=argparse.SUPPRESS)
    start.set_defaults(handler=_cmd_start)

    register_armory_commands(subparsers)
    register_source_commands(subparsers)
    register_chat_commands(subparsers, run_shell=run_chat_shell)
    register_config_commands(subparsers)
    _hide_subparser(subparsers, "chat")

    return parser


def run_argv(parser: argparse.ArgumentParser, argv: list[str]) -> None:
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        # No subcommand → launch the interactive shell directly
        run_chat_shell()
        return
    handler(args)


def main() -> None:
    init_analytics()
    init_observability()

    # Detect profile flags before argparse (so profiling covers argparse itself)
    _profile = "--profile" in sys.argv[1:]
    _profile_memory = "--profile-memory" in sys.argv[1:]

    _prof = None
    if _profile:
        _prof = cProfile.Profile()
        _prof.enable()

    if _profile_memory:
        tracemalloc.start()

    try:
        parser = build_parser()
        argv = sys.argv[1:]

        # If the first non-flag arg isn't a known subcommand (e.g. a path),
        # transparently inject "start" so `heph /my/armory` just works.
        known_commands = _get_subcommand_names(parser)
        argv = _inject_start_if_path(argv, known_commands)

        run_argv(parser, argv)
    finally:
        if _profile_memory:
            _report_memory()
        if _profile and _prof is not None:
            _prof.disable()
            _report_profile(_prof)
        shutdown_analytics()
        shutdown_observability()


def _report_memory() -> None:
    """Print top memory allocations from tracemalloc."""
    snapshot = tracemalloc.take_snapshot()
    tracemalloc.stop()
    top = snapshot.statistics("lineno")[:20]
    sys.stderr.write("\n=== Memory Profile (top 20) ===\n")
    for stat in top:
        sys.stderr.write(f"  {stat}\n")
    sys.stderr.write("\n")


def _report_profile(prof: cProfile.Profile) -> None:
    """Save cProfile results and print summary."""
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    profile_dir = Path.home() / ".cache" / "hephaistos" / "profiles"
    profile_dir.mkdir(parents=True, exist_ok=True)
    profile_path = profile_dir / f"{ts}.prof"
    prof.dump_stats(str(profile_path))

    sys.stderr.write(f"\n=== CPU Profile saved to {profile_path} ===\n")
    stats = pstats.Stats(prof, stream=sys.stderr)
    stats.strip_dirs().sort_stats("cumulative").print_stats(20)
    sys.stderr.write("\n")
