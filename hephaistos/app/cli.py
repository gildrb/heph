from __future__ import annotations

import argparse
import sys
from importlib.metadata import version as _pkg_version
from pathlib import Path

from hephaistos.analytics import init_analytics, shutdown_analytics
from hephaistos.app.shell import run_chat_shell
from hephaistos.armory.cli import register as register_armory_commands
from hephaistos.chat.cli import register as register_chat_commands
from hephaistos.observability import init_observability, shutdown_observability
from hephaistos.parameters.cli import register as register_config_commands
from hephaistos.source.cli import register as register_source_commands


def _package_version() -> str:
    try:
        return _pkg_version("hephaistos")
    except Exception:
        return "0.1.0"


_VERSION = _package_version()


def _hide_subparser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],  # type: ignore[reportPrivateUsage]
    name: str,
) -> None:
    subparsers._choices_actions = [
        action for action in subparsers._choices_actions if getattr(action, "dest", None) != name
    ]


def build_parser() -> argparse.ArgumentParser:
    prog = Path(sys.argv[0]).name or "hephaistos"
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Chat-first study CLI.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_VERSION}",
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
        required=True,
        metavar="command",
    )

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
        parser.print_help()
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
        import cProfile

        _prof = cProfile.Profile()
        _prof.enable()

    if _profile_memory:
        import tracemalloc

        tracemalloc.start()

    try:
        parser = build_parser()
        argv = sys.argv[1:]

        # Launch shell if only profile flags (no real command) or no args
        _real_args = [a for a in argv if a not in ("--profile", "--profile-memory")]
        if not _real_args:
            if sys.stdin.isatty() and sys.stdout.isatty():
                run_chat_shell()
            else:
                parser.print_help()
            return

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
    import tracemalloc

    snapshot = tracemalloc.take_snapshot()
    tracemalloc.stop()
    top = snapshot.statistics("lineno")[:20]
    sys.stderr.write("\n=== Memory Profile (top 20) ===\n")
    for stat in top:
        sys.stderr.write(f"  {stat}\n")
    sys.stderr.write("\n")


def _report_profile(prof: object) -> None:
    """Save cProfile results and print summary."""
    import pstats
    from datetime import UTC, datetime

    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    profile_dir = Path.home() / ".cache" / "hephaistos" / "profiles"
    profile_dir.mkdir(parents=True, exist_ok=True)
    profile_path = profile_dir / f"{ts}.prof"
    prof.dump_stats(str(profile_path))  # type: ignore[union-attr]

    sys.stderr.write(f"\n=== CPU Profile saved to {profile_path} ===\n")
    stats = pstats.Stats(prof, stream=sys.stderr)  # type: ignore[arg-type]
    stats.strip_dirs().sort_stats("cumulative").print_stats(20)
    sys.stderr.write("\n")
