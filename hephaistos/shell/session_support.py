"""Interactive session setup and persistence helpers."""

from __future__ import annotations

from pathlib import Path

from hephaistos.armory.cli import default_armory_home
from hephaistos.armory.search import add_known_armory, set_last_armory
from hephaistos.armory.storage import ArmoryError, initialize
from hephaistos.chat import storage as chat_storage
from hephaistos.chat.session import (
    ChatSession,
    create_session,
    save_session,
    session_has_messages,
)
from hephaistos.materials import count_material_files
from hephaistos.runtime import ChatConfig
from hephaistos.terminal.display import print_error, print_info, print_success

_HISTORY_DIR = Path.home() / ".cache" / "hephaistos"
_DEFAULT_ARMORY_HOME: Path | None = None


def _onboarding_armory_home() -> Path:
    return _DEFAULT_ARMORY_HOME or default_armory_home()


def _module_name_error(name: str) -> str | None:
    if len(name.encode("utf-8")) > 120:
        return "Module name is too long; use a shorter armory name."
    if name in {".", ".."} or Path(name).is_absolute():
        return "Module name must be a simple folder name, not a path."
    if any(part in {"", ".", ".."} for part in Path(name).parts) or len(Path(name).parts) != 1:
        return "Module name must be a simple folder name, not a path."
    if "/" in name or "\\" in name:
        return "Module name must not contain path separators."
    return None


def _prompt_module_name() -> str | None:
    print_info("What module or topic are you studying for? (e.g. 'gdp', 'algorithms', 'mfi-1')")
    armory_home = _onboarding_armory_home()
    print_info(f"Armories are saved in {armory_home}. You can create as many as you like.")
    while True:
        try:
            name = input("Module name: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if not name or name.lower() in {"q", "quit", "cancel"}:
            return None
        if error := _module_name_error(name):
            print_error(error)
            continue
        return name


def onboard_new_armory(config: ChatConfig) -> ChatSession | None:
    name = _prompt_module_name()
    if name is None:
        return None
    armory_home = _onboarding_armory_home()
    armory_path = armory_home / name
    try:
        initialize(armory_path)
    except (ArmoryError, OSError) as exc:
        print_error(str(exc))
        return None
    _ = add_known_armory(armory_path)
    set_last_armory(armory_path)
    module_name = armory_path.name
    materials_path = armory_path / "materials"
    print_success(f"Created armory '{module_name}' at {armory_path}")
    print_info(f"Add your study materials to {materials_path}")
    print_info("You can create as many armories as you like for different modules.")
    while count_material_files(armory_path) == 0:
        try:
            answer = input(f"Add files to {materials_path}, then Enter (or skip): ")
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if answer.strip().lower() in {"skip", "q", "quit", "cancel"}:
            return None
    return create_session(config, armory_path)


def recover_empty_armory_session(config: ChatConfig, armory_path: Path) -> ChatSession | None:
    while count_material_files(armory_path) == 0:
        try:
            answer = input("Add files now, then press Enter to continue; type skip to cancel > ")
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if answer.strip().lower() in {"skip", "q", "quit", "cancel"}:
            return None
    return create_session(config, armory_path)


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
