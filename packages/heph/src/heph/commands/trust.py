from __future__ import annotations

from pathlib import Path

from heph.commands._base import Command, CommandResult
from heph.trust import format_trust_report


class TrustCommand(Command):
    name = "trust"
    description = "Show data, cache, prompt, and compute ownership"

    def handle(self, session: object, args: str) -> CommandResult:
        del args
        armory_path = getattr(session, "armory_path", None)
        print(format_trust_report(armory_path if isinstance(armory_path, Path) else None))
        return CommandResult()
