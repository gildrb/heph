"""TUI-facing session action wrappers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from hephaistos.chat.cli import resolve_armory_session as chat_resolve_armory_session
from hephaistos.shell.armory_actions import start_fresh_session as shell_start_fresh_session
from hephaistos.shell.lifecycle import (
    create_startup_session as shell_create_startup_session,
)
from hephaistos.shell.lifecycle import get_history_path as shell_get_history_path
from hephaistos.shell.lifecycle import save_on_exit as shell_save_on_exit

if TYPE_CHECKING:
    from hephaistos.chat.session import ChatSession
    from hephaistos.runtime import ChatConfig


def start_fresh_session(session: ChatSession, armory_path: Path | None) -> ChatSession:
    return shell_start_fresh_session(session, armory_path)


def create_startup_session(config: ChatConfig) -> ChatSession:
    return shell_create_startup_session(config)


def get_history_path(session: ChatSession) -> Path:
    return shell_get_history_path(session)


def save_on_exit(session: ChatSession) -> None:
    shell_save_on_exit(session)


def resolve_armory_session(path: str) -> ChatSession:
    return chat_resolve_armory_session(path)
