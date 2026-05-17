"""Interactive armory workspace actions."""

from __future__ import annotations

from pathlib import Path

from hephaistos.armory.search import add_known_armory, set_last_armory
from hephaistos.armory.storage import ArmoryError, initialize, normalize_path
from hephaistos.chat.session import (
    ChatSession,
    SessionError,
    create_plain_session,
    create_session,
    validate_armory_path,
)
from hephaistos.diagnostics.events import capture as capture_analytics
from hephaistos.shell.saved_chats import list_saved_chats, resume_saved_chat, save_before_switch
from hephaistos.terminal import MenuOption, browse_directory, select_option
from hephaistos.terminal.display import print_error, print_info, print_success

ARMORY_MENU_OPTIONS = [
    MenuOption("Open existing armory", "Attach a workspace and load its context."),
    MenuOption("Create new armory", "Initialize a new workspace and start chatting in it."),
    MenuOption("Detach armory", "Switch to plain chat without workspace tools."),
    MenuOption("Resume saved chat", "Pick a saved conversation from an armory."),
    MenuOption("List saved chats", "Show the saved sessions for an armory."),
    MenuOption("Cancel", "Return to the chat prompt."),
]


def start_fresh_session(
    session: ChatSession,
    armory_path: Path | None,
) -> ChatSession:
    if armory_path is None and session.armory_path is None:
        print_info("Already in plain chat mode.")
        return session
    save_before_switch(session)
    try:
        if armory_path is None:
            new_session = create_plain_session(session.config)
        else:
            new_session = create_session(session.config, armory_path)
    except SessionError as exc:
        print_error(str(exc))
        return session
    if armory_path is None:
        print_success("Detached armory. Plain chat mode.")
        capture_analytics("armory_detached", {"model": new_session.config.model})
        return new_session
    add_known_armory(armory_path)
    set_last_armory(armory_path)
    print_success(f"Using armory {armory_path}")
    if new_session.source_file_count:
        print_info(f"Loaded {new_session.source_file_count} file(s).")
    capture_analytics(
        "armory_attached",
        {
            "source_file_count": new_session.source_file_count,
            "model": new_session.config.model,
        },
    )
    return new_session


def detach_armory(session: ChatSession) -> ChatSession:
    return start_fresh_session(session, None)


def open_armory(session: ChatSession) -> ChatSession:
    default_path = Path(session.armory_path or Path.cwd())
    chosen = browse_directory("Open Armory", start=default_path)
    if chosen is None:
        print_info("Cancelled.")
        return session
    try:
        armory_path = validate_armory_path(str(chosen))
    except ArmoryError as exc:
        print_error(str(exc))
        return session
    return start_fresh_session(session, armory_path)


def create_armory(session: ChatSession) -> ChatSession:
    default_path = Path(session.armory_path or Path.cwd())
    chosen = browse_directory("Create Armory", start=default_path)
    if chosen is None:
        print_info("Cancelled.")
        return session
    armory_path = normalize_path(str(chosen))
    try:
        initialize(armory_path)
    except ArmoryError as exc:
        print_error(str(exc))
        return session
    print_success(f"Created armory '{armory_path.name}' at {armory_path}")
    capture_analytics("armory_created", {"mode": "shell"})
    try:
        return start_fresh_session(session, armory_path)
    except SessionError as exc:
        print_error(str(exc))
        print_info(f"Add source files to ~/.armories/{armory_path.name}/materials/")
        return session


def handle_armory_command(session: ChatSession) -> ChatSession:
    selected = select_option("Armory", ARMORY_MENU_OPTIONS)
    handlers = [
        open_armory,
        create_armory,
        detach_armory,
        resume_saved_chat,
        list_saved_chats,
    ]
    if selected is None or selected < 0 or selected >= len(handlers):
        return session
    result = handlers[selected](session)
    if result is None:
        return session
    return result
