"""Compact conversation command."""

from __future__ import annotations

from hephaistos.analytics import capture as capture_analytics
from hephaistos.app.commands._base import Command, CommandResult, do_compact, ensure_session
from hephaistos.app.display import STYLE_DIM, print_info, print_success, styled
from hephaistos.chat.session import session_has_messages


class CompactCommand(Command):
    name = "compact"
    description = "Summarize conversation to reduce context size"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        if not session_has_messages(s):
            print_info("Nothing to compact.")
            return CommandResult()

        non_system = [m for m in s.conversation.messages if m.role != "system"]

        print(styled("Compacting...", STYLE_DIM))
        do_compact(s)

        print_success("Compacted.")
        capture_analytics(
            "conversation_compacted",
            {
                "model": s.config.model,
                "message_count": len(non_system),
                "summary_length": 0,  # summary is internal to do_compact
            },
        )
        return CommandResult()
