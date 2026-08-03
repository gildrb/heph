"""Compact conversation command."""

from __future__ import annotations

from harness.chat.compaction import compact_session
from harness.chat.session import session_has_messages
from interfaces.terminal import STYLE_DIM, print_info, print_success, styled

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
        return CommandResult()
