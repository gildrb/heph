"""Session startup discovery helpers."""

from __future__ import annotations

import sys
from pathlib import Path

from hephaistos.chat.session import (
    ChatSession,
    SessionError,
    create_plain_session,
    create_session,
    empty_armory_guidance,
)
from hephaistos.runtime import ChatConfig
from hephaistos.shell import session_support as _support
from hephaistos.shell.startup_discovery import discover_available_armories, discover_startup_armory
from hephaistos.terminal.display import print_error, print_info


def _stdio_is_interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def get_history_path(session: ChatSession) -> Path:
    return _support.get_history_path(session)


def save_on_exit(session: ChatSession) -> None:
    _support.save_on_exit(session)


def create_startup_session(config: ChatConfig) -> ChatSession:
    """Create a startup study session, running onboarding when no armory is usable."""
    armory = discover_startup_armory()
    if armory is None:
        if discover_available_armories():
            print_info("Multiple armories found. Use /armory to choose one.")
            return create_plain_session(config)
        if (
            _stdio_is_interactive()
            and (onboarded := _support.onboard_new_armory(config)) is not None
        ):
            return onboarded
        print_error("No study armory attached; onboarding was not completed.")
        print_info("Run `heph armory init <name>`, add files to ~/.armories/<name>/materials/.")
        return create_plain_session(config)
    try:
        return create_session(config, armory)
    except SessionError:
        print_error("Auto-discovered armory has no study materials.")
        print_info(empty_armory_guidance(armory))
        if (
            _stdio_is_interactive()
            and (resumed := _support.recover_empty_armory_session(config, armory)) is not None
        ):
            return resumed
        print_error("No study session started because the armory still has no materials.")
        return create_plain_session(config)
