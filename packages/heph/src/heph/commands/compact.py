"""Compact conversation command."""

from __future__ import annotations

from heph_interfaces.terminal import STYLE_DIM, print_info, print_success, styled
from hephaion.chat.compaction import compact_session
from hephaion.chat.session import session_has_messages
from hephaion.diagnostics.events import capture as capture_analytics

from heph.commands._base import Command, CommandResult, ensure_session


class CompactCommand(Command):
    name = "compact"
    description = "Summarize conversation to reduce context size"

    def handle(self, session: object, args: str) -> CommandResult:
        del args
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
