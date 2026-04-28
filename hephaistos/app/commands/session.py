"""Session management commands: status, save, clear, new, chats, sessions, resume, edit."""

from __future__ import annotations

from contextlib import suppress

from hephaistos.analytics import capture as capture_analytics
from hephaistos.app.commands._base import Command, CommandResult, ensure_session
from hephaistos.app.display import (
    STYLE_DIM,
    direct_input,
    print_error,
    print_info,
    print_success,
    styled,
)
from hephaistos.app.menu import confirm
from hephaistos.app.palette import STYLE_PROMPT
from hephaistos.app.workspace import (
    handle_armory_command,
    list_saved_chats,
    resume_saved_chat,
)
from hephaistos.chat import storage as chat_storage
from hephaistos.chat.engine import is_keyless_endpoint
from hephaistos.chat.session import (
    ChatSession,
    SessionError,
    create_plain_session,
    create_session,
    save_session,
    session_has_messages,
)


class StatusCommand(Command):
    name = "status"
    description = "Show armory, session, and model info"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        armory = str(s.armory_path) if s.armory_path else styled("none", STYLE_DIM)
        title = s.title or styled("(untitled)", STYLE_DIM)
        msg_count = sum(1 for m in s.conversation.messages if m.role != "system")
        tool_count = 7 if s.armory_path else 0
        mode = "agent (tools)" if s.armory_path else "plain chat"
        usage_summary = s.usage.summary()
        mem_count = len(s.memory.entries) if s.memory else 0

        lines = [
            f"  Armory:    {armory}",
            f"  Session:   {s.session_id}",
            f"  Title:     {title}",
            f"  Model:     {s.config.model}",
            f"  Persona:   {s.persona.display_name}",
            f"  API:       {s.config.base_url}",
            (
                "  Key:       not needed (free provider)"
                if is_keyless_endpoint(s.config.base_url)
                else (
                    "  Key:       configured"
                    if s.config.resolved_api_key
                    else f"  Key:       {styled('not set', STYLE_DIM)}"
                )
            ),
            f"  Mode:      {mode}",
            f"  Tools:     {tool_count}",
            f"  Messages:  {msg_count}",
            f"  Memory:    {mem_count} concepts",
            f"  API calls: {usage_summary['api_calls']}",
            (
                f"  Tokens:    {usage_summary['total_tokens']}"
                f" (prompt: {usage_summary['prompt_tokens']},"
                f" completion: {usage_summary['completion_tokens']})"
            ),
            f"  Cost:      ${usage_summary['cost_usd']:.4f}",
            f"  Dirty:     {'yes' if s.dirty else 'no'}",
        ]
        print("\n".join(lines))
        return CommandResult()


class SaveCommand(Command):
    name = "save"
    description = "Save current chat to armory"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        try:
            path = save_session(s)
        except chat_storage.ChatStorageError as exc:
            print_error(str(exc))
            return CommandResult()
        print_success(f"Saved to {path}")
        return CommandResult()


class ClearCommand(Command):
    name = "clear"
    description = "Start a fresh chat session"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)

        if session_has_messages(s) and not confirm("Clear conversation?", default=False):
            print_info("Cancelled.")
            return CommandResult()

        if s.armory_path and s.dirty and session_has_messages(s):
            try:
                save_session(s)
                print_info("Previous session saved.")
            except chat_storage.ChatStorageError:
                pass
        new: ChatSession
        try:
            new = (
                create_plain_session(s.config)
                if s.armory_path is None
                else create_session(s.config, s.armory_path)
            )
        except SessionError as exc:
            print_error(str(exc))
            return CommandResult()
        print_success("Started fresh session.")
        capture_analytics(
            "session_cleared",
            {
                "mode": "armory" if new.armory_path is not None else "plain",
                "model": new.config.model,
            },
        )
        return CommandResult(new_session=new)


class NewCommand(Command):
    name = "new"
    description = "Start a new chat (saves previous automatically)"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        if s.armory_path and s.dirty and session_has_messages(s):
            with suppress(chat_storage.ChatStorageError):
                save_session(s)
        new: ChatSession
        try:
            new = (
                create_plain_session(s.config)
                if s.armory_path is None
                else create_session(s.config, s.armory_path)
            )
        except SessionError as exc:
            print_error(str(exc))
            return CommandResult()
        print_success("New chat started.")
        capture_analytics(
            "session_new",
            {
                "mode": "armory" if new.armory_path is not None else "plain",
                "model": new.config.model,
            },
        )
        return CommandResult(new_session=new)


class ArmoryCommand(Command):
    name = "armory"
    description = "Open the armory management menu"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        new = handle_armory_command(s)
        return CommandResult(new_session=new)


class ChatsCommand(Command):
    name = "chats"
    description = "List saved chats in the active armory"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        list_saved_chats(s)
        return CommandResult()


class SessionsCommand(Command):
    name = "sessions"
    description = "List or resume saved sessions"

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
