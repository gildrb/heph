"""Study and vocabulary commands: vocab, remind."""

from __future__ import annotations

from datetime import UTC, datetime

from hephaistos.analytics import capture as capture_analytics
from hephaistos.app.commands._base import Command, CommandResult, ensure_session
from hephaistos.app.display import (
    STYLE_ACCENT,
    STYLE_DIM,
    STYLE_SUCCESS,
    print_error,
    print_info,
    print_success,
    styled,
)
from hephaistos.app.menu import confirm
from hephaistos.chat.session import ChatSession
from hephaistos.vocab.drill import run_drill
from hephaistos.vocab.parser import scan_armory
from hephaistos.vocab.scheduler import select_due_cards
from hephaistos.vocab.state import VocabCardState, load_schedule, save_schedule


class VocabCommand(Command):
    name = "vocab"
    description = "Vocabulary drill with spaced repetition"
    aliases = ("v",)

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        if s.armory_path is None:
            print_error("No armory attached. Use /armory to open one first.")
            return CommandResult()

        subcmd = args.strip().lower()

        if subcmd == "status":
            return self._status(s)
        if subcmd == "reset":
            return self._reset(s)

        # Default: start drill.
        result = run_drill(s.armory_path)
        if result and result.cards_reviewed > 0:
            capture_analytics(
                "vocab_drill",
                {
                    "cards_reviewed": result.cards_reviewed,
                    "hard": result.hard_count,
                    "good": result.good_count,
                    "easy": result.easy_count,
                },
            )
        return CommandResult()

    @staticmethod
    def _status(session: ChatSession) -> CommandResult:
        armory_path = session.armory_path
        if armory_path is None:
            print_error("No armory attached. Use /armory to open one first.")
            return CommandResult()

        deck = scan_armory(armory_path)
        store = load_schedule(armory_path)
        store.sync_with_deck(deck)
        save_schedule(store)
        stats = store.stats()
        lines = [
            f"  Total cards:  {stats['total']}",
            f"  New:          {stats['new']}",
            f"  Due now:      {stats['due']}",
            f"  Mastered:     {stats['mastered']}",
            f"  Material files: {', '.join(deck.source_files) if deck.source_files else 'none'}",
        ]
        print("\n".join(lines))
        return CommandResult()

    @staticmethod
    def _reset(session: ChatSession) -> CommandResult:
        armory_path = session.armory_path
        if armory_path is None:
            print_error("No armory attached. Use /armory to open one first.")
            return CommandResult()
        if not confirm("Reset all vocabulary scheduling data?", default=False):
            print_info("Cancelled.")
            return CommandResult()
        deck = scan_armory(armory_path)
        store = load_schedule(armory_path)
        store.sync_with_deck(deck)
        store.reset_all()
        store.save()
        print_success("Vocabulary schedule reset. All cards are now new.")
        return CommandResult()


class RemindCommand(Command):
    name = "remind"
    description = "Show upcoming study reminders and due cards"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        if s.armory_path is None:
            print_error("No armory attached. Use /armory to open one.")
            return CommandResult()

        deck = scan_armory(s.armory_path)
        store = load_schedule(s.armory_path)
        store.sync_with_deck(deck)
        save_schedule(store)

        all_cards = store.card_list
        due = select_due_cards(all_cards)
        now = datetime.now(UTC)

        if not all_cards:
            print_info("No vocab cards yet. Add Q&A pairs to your materials.")
            return CommandResult()

        lines: list[str] = []

        if due:
            lines.append(f"You have {len(due)} card{'s' if len(due) != 1 else ''} due for review.")
            lines.append(f"  Run {styled('/vocab drill', STYLE_ACCENT)} to study them now.")
        else:
            lines.append(styled("All caught up!", STYLE_SUCCESS))

        with_scheduled = [c for c in all_cards if c.next_review is not None]
        scheduled = sorted(with_scheduled, key=lambda c: c.next_review)  # type: ignore[arg-type]
        if scheduled:
            next_card: VocabCardState = scheduled[0]  # type: ignore[reportUnknownVariableType]
            assert next_card.next_review is not None  # type: ignore[reportUnknownMemberType]
            delta = next_card.next_review - now  # type: ignore[reportUnknownMemberType,reportUnknownVariableType]
            secs = float(delta.total_seconds())  # type: ignore[reportUnknownMemberType]
            if secs > 0:
                hours = secs / 3600
                if hours < 1:
                    when = f"{int(secs / 60)}m"  # type: ignore[reportUnknownArgumentType]
                elif hours < 48:
                    when = f"{int(hours)}h"  # type: ignore[reportUnknownArgumentType]
                else:
                    when = f"{int(hours / 24)}d"  # type: ignore[reportUnknownArgumentType]
                n_scheduled = len(scheduled)  # type: ignore[reportUnknownArgumentType]
                plural = "s" if n_scheduled != 1 else ""
                lines.append(f"  Next review in {when} ({n_scheduled} card{plural} scheduled).")

        if due:
            lines.append("")
            lines.append("Due cards:")
            lines.extend(f"  {styled(card.front[:60], STYLE_DIM)}" for card in due[:10])
            if len(due) > 10:
                lines.append(f"  ... and {len(due) - 10} more")

        print("\n".join(lines))
        return CommandResult()
