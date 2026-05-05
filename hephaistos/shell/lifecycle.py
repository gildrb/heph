"""Session startup discovery helpers."""

from __future__ import annotations

import sys
from pathlib import Path

from hephaistos.armory.search import load_known_armory_entries
from hephaistos.armory.storage import ArmoryError
from hephaistos.chat.session import (
    ChatSession,
    SessionError,
    create_plain_session,
    create_session,
    empty_armory_guidance,
    validate_armory_path,
)
from hephaistos.runtime import ChatConfig
from hephaistos.shell import session_support as _session_support
from hephaistos.terminal.display import print_error, print_info


def _stdio_is_interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def discover_startup_armory() -> Path | None:
    try:
        return validate_armory_path(str(Path.cwd()))
    except ArmoryError:
        pass
    valid = [entry.path for entry in load_known_armory_entries() if entry.valid]
    if len(valid) == 1:
        return valid[0]
    return None


def get_history_path(session: ChatSession) -> Path:
    return _session_support.get_history_path(session)


def save_on_exit(session: ChatSession) -> None:
    _session_support.save_on_exit(session)


def create_startup_session(config: ChatConfig) -> ChatSession:
    """Create a startup study session, running onboarding when no armory is usable."""
    armory = discover_startup_armory()
    if armory is None:
        if (
            _stdio_is_interactive()
            and (onboarded := _session_support.onboard_new_armory(config)) is not None
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
            and (resumed := _session_support.recover_empty_armory_session(config, armory))
            is not None
        ):
            return resumed
        print_error("No study session started because the armory still has no materials.")
        return create_plain_session(config)
