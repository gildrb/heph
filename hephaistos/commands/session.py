"""Session management commands: status, new, sessions, resume, edit."""

from __future__ import annotations

from hephaistos.chat import storage as chat_storage
from hephaistos.chat.session import save_session, session_has_messages
from hephaistos.commands._base import Command, CommandResult, ensure_session
from hephaistos.shell.actions import start_replacement_session
from hephaistos.shell.armory_actions import (
    create_armory as create_armory_command,
)
from hephaistos.shell.armory_actions import (
    handle_armory_command,
)
from hephaistos.shell.armory_actions import (
    open_armory as open_armory_command,
)
from hephaistos.shell.saved_chats import list_saved_chats, resume_saved_chat
from hephaistos.shell.status import render_session_status
from hephaistos.terminal import STYLE_PROMPT, confirm
from hephaistos.terminal.display import direct_input, print_error, print_info, styled


class StatusCommand(Command):
    name = "status"
    description = "Show armory, session, and model info"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        return CommandResult(output=render_session_status(s))


class SaveCommand(Command):
    name = "save"
    description = "Save current chat to armory"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        try:
            path = save_session(s)
        except chat_storage.ChatStorageError as exc:
            return CommandResult(output=f"error: {exc}")
        return CommandResult(output=f"Saved to {path}")


class ClearCommand(Command):
    name = "clear"
    description = "Start a fresh chat session"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)

        if session_has_messages(s) and not confirm("Clear conversation?", default=False):
            print_info("Cancelled.")
            return CommandResult()

        new = start_replacement_session(
            s,
            analytics_event="session_cleared",
            success_message="Started fresh session.",
            announce_autosave=True,
        )
        return CommandResult(new_session=new)


class NewCommand(Command):
    name = "new"
    description = "Start a new chat"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        new = start_replacement_session(
            s,
            analytics_event="session_new",
            success_message="New chat started.",
            announce_autosave=False,
        )
        return CommandResult(new_session=new)


class ArmoryCommand(Command):
    name = "armory"
    description = "Browse, open, or create armories"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        subcmd = args.strip().lower()
        if subcmd in ("", "menu", "manage"):
            new = handle_armory_command(s)
            return CommandResult(new_session=new)
        if subcmd == "open":
            return CommandResult(new_session=open_armory_command(s))
        if subcmd in ("create", "new"):
            return CommandResult(new_session=create_armory_command(s))
        print_error("Usage: /armory [open|create]")
        print_info("Browse, open, or create a local study armory for materials and saved chats.")
        return CommandResult()


class ChatsCommand(Command):
    name = "chats"
    description = "List saved chats in the active armory"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        list_saved_chats(s)
        return CommandResult()


class SessionsCommand(Command):
    name = "sessions"
    description = "Switch between saved sessions"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        subcmd = args.strip().lower()
        if subcmd in ("", "list", "recent"):
            list_saved_chats(s)
            return CommandResult()
        if subcmd in ("browse", "menu"):
            return CommandResult(new_session=resume_saved_chat(s, "browse"))
        if subcmd in ("resume", "last", "latest"):
            return CommandResult(new_session=resume_saved_chat(s, "latest"))
        print_error("Usage: /sessions [list|recent|browse|resume]")
        return CommandResult()


class ResumeCommand(Command):
    name = "resume"
    description = "Resume the latest saved chat, or pass an ID prefix"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        new = resume_saved_chat(s, args.strip())
        return CommandResult(new_session=new)


class EditCommand(Command):
    name = "edit"
    description = "Edit and resend the last user message"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        last_user = None
        last_user_idx = -1
        for i in range(len(s.conversation.messages) - 1, -1, -1):
            if s.conversation.messages[i].role == "user":
                last_user = s.conversation.messages[i]
                last_user_idx = i
                break
        if last_user is None:
            print_info("No user messages to edit.")
            return CommandResult()

        original = last_user.content
        print_info(f"Last message: {original[:100]}{'...' if len(original) > 100 else ''}")
        print(styled("Enter new message (empty to cancel):", STYLE_PROMPT))
        try:
            new_text = direct_input("  ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return CommandResult()

        if not new_text:
            print_info("Cancelled.")
            return CommandResult()
        s.conversation.messages = s.conversation.messages[:last_user_idx]
        s.dirty = True

        return CommandResult(output=f"__RESEND__:{new_text}")
