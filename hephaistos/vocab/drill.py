"""Vocabulary drill workflow and scheduling coordination."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Protocol

from hephaistos.logging import get_logger
from hephaistos.vocab.parser import scan_armory
from hephaistos.vocab.scheduler import Rating, ScheduleResult, schedule_card, select_due_cards
from hephaistos.vocab.state import VocabCardState, load_schedule, save_schedule

_log = get_logger("vocab.drill")


class DrillUi(Protocol):
    """User-interface boundary for interactive vocabulary drills."""

    def print_line(self, text: str = "") -> None: ...

    def prompt_answer(self, prompt: str) -> str: ...

    def prompt_rating(self) -> Rating | None: ...

    def format_prompt(self, text: str) -> str: ...

    def format_accent(self, text: str) -> str: ...

    def format_dim(self, text: str) -> str: ...


@dataclass(slots=True)
class DrillResult:
    """Summary of a completed drill session."""

    cards_reviewed: int = 0
    hard_count: int = 0
    good_count: int = 0
    easy_count: int = 0

    @property
    def total(self) -> int:
        return self.hard_count + self.good_count + self.easy_count


def _format_interval(days: int) -> str:
    if days < 1:
        return "< 1 day"
    if days == 1:
        return "1 day"
    if days < 7:
        return f"{days} days"
    if days < 30:
        return f"{days // 7} week{'s' if days // 7 != 1 else ''}"
    if days < 365:
        return f"{days // 30} month{'s' if days // 30 != 1 else ''}"
    return f"{days // 365} year{'s' if days // 365 != 1 else ''}"


def _answers_match(user_answer: str, correct_answer: str) -> bool:
    """Case-insensitive fuzzy match for answer comparison."""
    user = user_answer.strip().lower()
    correct = correct_answer.strip().lower()
    return user == correct or user in correct or correct in user


def _apply_schedule(state: VocabCardState, result: ScheduleResult) -> VocabCardState:
    """Apply a schedule result to a card state and advance timestamps."""
    now = datetime.now(UTC)
    state.repetitions = result.repetitions
    state.easiness = result.easiness
    state.interval = result.interval_days
    state.last_review = now
    state.next_review = now + timedelta(days=result.interval_days)
    return state


def _print_header(ui: DrillUi, card_num: int, total: int) -> None:
    ui.print_line()
    ui.print_line(ui.format_dim(f"  -- Card {card_num}/{total} --"))
    ui.print_line()


def _show_answer_comparison(ui: DrillUi, user_answer: str, correct_answer: str) -> None:
    ui.print_line()
    match = _answers_match(user_answer, correct_answer)
    formatted_answer = ui.format_prompt(user_answer) if match else ui.format_dim(user_answer)
    ui.print_line(f"  Your answer:    {formatted_answer}")
    ui.print_line(f"  Correct answer: {ui.format_accent(correct_answer)}")
    ui.print_line()


def run_drill(armory_path: Path, ui: DrillUi, *, card_limit: int = 0) -> DrillResult | None:
    """Run an interactive vocabulary drill session."""
    deck = scan_armory(armory_path)
    store = load_schedule(armory_path)
    new_cards = store.sync_with_deck(deck)

    if not deck.cards:
        save_schedule(store)
        ui.print_line(ui.format_dim("  No vocabulary files found in this armory."))
        ui.print_line(
            ui.format_dim(
                "  Add a markdown file with a table (columns: word, translation) to materials/."
            )
        )
        return None

    if new_cards:
        _log.info("vocab deck synced", extra={"fields": {"new_cards": new_cards}})

    due = select_due_cards(store.card_list, limit=card_limit)
    if not due:
        save_schedule(store)
        stats = store.stats()
        ui.print_line(ui.format_dim("  No cards due for review right now."))
        if stats["new"] > 0:
            ui.print_line(ui.format_dim(f"  ({stats['new']} new cards available)"))
        return None

    total_due = len(due)
    stats = store.stats()
    ui.print_line()
    word_count = f"{stats['total']} words,"
    due_count = f"{total_due} due now"
    ui.print_line(
        f"  {ui.format_prompt('Vocabulary Drill')}  "
        f"{ui.format_dim(word_count)} "
        f"{ui.format_accent(due_count)}"
    )
    ui.print_line(ui.format_dim("  Type your answer, then rate your recall."))
    ui.print_line(ui.format_dim("  Press Ctrl+C to stop early."))

    result = DrillResult()

    for i, card_state in enumerate(due):
        _print_header(ui, i + 1, total_due)
        ui.print_line(f"  {ui.format_prompt('Word:')}   {card_state.front}")

        try:
            user_answer = ui.prompt_answer("  Type translation: ")
        except (KeyboardInterrupt, EOFError):
            ui.print_line()
            ui.print_line(ui.format_dim("  Drill stopped early."))
            break

        if not user_answer.strip():
            ui.print_line(ui.format_dim("  (skipped)"))
            continue

        _show_answer_comparison(ui, user_answer, card_state.back)

        rating = ui.prompt_rating()
        if rating is None:
            ui.print_line(ui.format_dim("  Drill stopped."))
            break

        schedule_result = schedule_card(card_state, rating)
        _apply_schedule(card_state, schedule_result)
        store.update_card(card_state)

        result.cards_reviewed += 1
        if rating == Rating.HARD:
            result.hard_count += 1
        elif rating == Rating.GOOD:
            result.good_count += 1
        else:
            result.easy_count += 1

        next_interval = ui.format_accent(_format_interval(schedule_result.interval_days))
        ui.print_line(f"  -> Next review in {next_interval}")
        ui.print_line()

    save_schedule(store)
    _print_summary(ui, store.card_list, result)
    _log_result(result)
    return result


def _print_summary(ui: DrillUi, cards: list[VocabCardState], result: DrillResult) -> None:
    if result.cards_reviewed <= 0:
        return

    ui.print_line()
    ui.print_line(ui.format_prompt("  -- Session Complete --"))
    ui.print_line(f"  Reviewed: {result.cards_reviewed} cards")
    summary = (
        f"  Hard: {result.hard_count} | Good: {result.good_count} | Easy: {result.easy_count}"
    )
    ui.print_line(summary)

    remaining_due = select_due_cards(cards)
    if remaining_due:
        ui.print_line(f"  Next session: ~{len(remaining_due)} cards due")
        return

    soonest = min(
        (card.next_review for card in cards if card.next_review is not None),
        default=None,
    )
    if soonest:
        days_ahead = max(0, (soonest - datetime.now(UTC)).days)
        ui.print_line(f"  All caught up! Next review in ~{_format_interval(max(1, days_ahead))}")
    else:
        ui.print_line("  All cards reviewed!")


def _log_result(result: DrillResult) -> None:
    _log.info(
        "drill session complete",
        extra={
            "fields": {
                "cards_reviewed": result.cards_reviewed,
                "hard": result.hard_count,
                "good": result.good_count,
                "easy": result.easy_count,
            }
        },
    )
