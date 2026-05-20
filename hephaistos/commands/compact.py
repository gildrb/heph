"""Compact conversation command."""

from __future__ import annotations

from hephaistos.chat.compaction import compact_session
from hephaistos.chat.session import session_has_messages
from hephaistos.commands._base import Command, CommandResult, ensure_session
from hephaistos.diagnostics.events import capture as capture_analytics
from hephaistos.terminal.display import STYLE_DIM, print_info, print_success, styled


class CompactCommand(Command):
    name = "compact"
    description = "Summarize conversation to reduce context size"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        if not session_has_messages(s):
            print_info("Nothing to compact.")
            return CommandResult()

        print(styled("Compacting...", STYLE_DIM))
        compact_session(s)

        print_success("Compacted.")
        capture_analytics(
            "conversation_compacted",
            {
                "model": s.config.model,
                "message_count": sum(1 for m in s.conversation.messages if m.role != "system"),
                "summary_length": 0,  # summary is internal to do_compact
            },
        )
        return CommandResult()
