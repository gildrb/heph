"""Session startup, history, and shutdown helpers."""

from __future__ import annotations

import sys
from pathlib import Path

from hephaistos.armory.search import add_known_armory
from hephaistos.armory.storage import ArmoryError, initialize
from hephaistos.chat import storage as chat_storage
from hephaistos.chat.session import (
    ChatSession,
    SessionError,
    create_plain_session,
    create_session,
    empty_armory_guidance,
    save_session,
    session_has_messages,
    validate_armory_path,
)
from hephaistos.materials import count_material_files
from hephaistos.runtime import ChatConfig
from hephaistos.terminal.display import print_error, print_info, print_success

_HISTORY_DIR = Path.home() / ".cache" / "hephaistos"
_DEFAULT_ARMORY_HOME = Path.home() / ".armories"


def _stdio_is_interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _default_onboarding_path() -> Path:
    return _DEFAULT_ARMORY_HOME


def _prompt_module_name() -> str | None:
    print_info("What module or topic are you studying for? (e.g. 'gdp', 'algorithms', 'mfi-1')")
    print_info("Armories are saved in ~/.armories/. You can create as many as you like.")
    try:
        name = input("Module name: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None
    if not name or name.lower() in {"q", "quit", "cancel"}:
        return None
    return name


def _prompt_onboarding_path(default_path: Path) -> Path | None:
    name = _prompt_module_name()
    if name is None:
        return None
    return default_path / name


def _onboard_new_armory(config: ChatConfig) -> ChatSession | None:
    armory_path = _prompt_onboarding_path(_default_onboarding_path())
    if armory_path is None:
        return None
    try:
        initialize(armory_path)
    except (ArmoryError, OSError) as exc:
        print_error(str(exc))
        return None
    add_known_armory(armory_path)
    module_name = armory_path.name
    print_success(f"Created armory '{module_name}' at {armory_path}")
    print_info(f"Add your study materials to ~/.armories/{module_name}/materials/")
    print_info("You can create as many armories as you like for different modules.")

    while count_material_files(armory_path) == 0:
        try:
            answer = input(
                f"Add files to ~/.armories/{module_name}/materials/, then Enter (or skip): "
            )
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if answer.strip().lower() in {"skip", "q", "quit", "cancel"}:
            return None

    return create_session(config, armory_path)


def discover_startup_armory() -> Path | None:
    try:
        return validate_armory_path(str(Path.cwd()))
    except ArmoryError:
        pass
    return None


def get_history_path(session: ChatSession) -> Path:
    if session.armory_path is None:
        return _HISTORY_DIR / "plain-history"
    return session.armory_path / ".hephaistos" / "history"


def save_on_exit(session: ChatSession) -> None:
    if session.dirty and session_has_messages(session) and session.armory_path is not None:
        try:
            path = save_session(session)
            print_success(f"Saved chat to {path}")
        except chat_storage.ChatStorageError as exc:
            print_error(str(exc))
    session.trace.close()


def create_startup_session(config: ChatConfig) -> ChatSession:
    """Create a startup study session, running onboarding when no armory is usable."""
    armory = discover_startup_armory()
    if armory is None:
        if _stdio_is_interactive():
            onboarded = _onboard_new_armory(config)
            if onboarded is not None:
                return onboarded
        print_error("No study armory attached; onboarding was not completed.")
        print_info("Run `heph armory init <name>`, add files to ~/.armories/<name>/materials/.")
        return create_plain_session(config)
    try:
        return create_session(config, armory)
    except SessionError:
        print_error("Auto-discovered armory has no study materials.")
        print_info(empty_armory_guidance(armory))
        if _stdio_is_interactive():
            while count_material_files(armory) == 0:
                try:
                    answer = input(
                        "Add files now, then press Enter to continue; type skip to cancel > "
                    )
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
                if answer.strip().lower() in {"skip", "q", "quit", "cancel"}:
                    break
            if count_material_files(armory) > 0:
                return create_session(config, armory)
        print_error("No study session started because the armory still has no materials.")
        return create_plain_session(config)
