"""Vocabulary drill workflow and scheduling coordination."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Protocol

from ai.logging import get_logger
from parameters.settings import (
    VOCAB_STRICTNESS_LENIENT,
    load_app_settings,
)

from vocab.parser import scan_armory
from vocab.scheduler import Rating, schedule_card, select_due_cards
from vocab.state import (
    VocabCardState,
    VocabScheduleStore,
    load_schedule,
    save_schedule,
)

_log = get_logger("vocab.drill")
type _IntervalUnit = tuple[int, int, str]
_INTERVAL_UNITS: tuple[_IntervalUnit, ...] = (
    (7, 1, "day"),
    (30, 7, "week"),
    (365, 30, "month"),
)


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
    cards_reviewed: int = 0
    hard_count: int = 0
    good_count: int = 0
    easy_count: int = 0


def _format_interval(days: int) -> str:
    if days < 1:
        return "< 1 day"
    for upper_bound, divisor, unit in _INTERVAL_UNITS:
        if days < upper_bound:
            return _plural_interval(days // divisor, unit)
    return _plural_interval(days // 365, "year")


def _plural_interval(count: int, unit: str) -> str:
    suffix = "" if count == 1 else "s"
    return f"{count} {unit}{suffix}"


def _answer_matches(user_answer: str, correct_answer: str) -> bool:
    user = user_answer.strip().casefold()
    correct = correct_answer.strip().casefold()
    if user == correct:
        return True
    if load_app_settings().vocab_strictness != VOCAB_STRICTNESS_LENIENT:
        return False
    return _normalize_lenient_answer(user) == _normalize_lenient_answer(correct)


def _normalize_lenient_answer(answer: str) -> str:
    alnum_words = "".join(ch for ch in answer if ch.isalnum() or ch.isspace())
    return " ".join(alnum_words.split())


def run_drill(armory_path: Path, ui: DrillUi, *, card_limit: int = 0) -> DrillResult | None:
    deck = scan_armory(armory_path)
    store = load_schedule(armory_path)
    new_cards = store.sync_with_deck(deck)

    if not deck.cards:
        _finish_without_cards(store, ui)
        return None

    if new_cards:
        _log.info("vocab deck synced", extra={"fields": {"new_cards": new_cards}})

    due = select_due_cards(store.card_list, limit=card_limit)
    if not due:
        _finish_without_due_cards(store, ui)
        return None

    _print_drill_header(store, ui, total_due=len(due))

    result = DrillResult()

    for i, card_state in enumerate(due):
        user_answer = _prompt_card_answer(ui, card_state, index=i, total_due=len(due))
        if user_answer is None:
            break

        if not user_answer.strip():
            ui.print_line(ui.format_dim("  (skipped)"))
            continue

        _print_answer_feedback(ui, user_answer, card_state.back)

        rating = ui.prompt_rating()
        if rating is None:
            ui.print_line(ui.format_dim("  Drill stopped."))
            break

        interval_days = _record_card_review(store, card_state, rating)
        _record_rating(result, rating)
        _print_next_review(ui, interval_days)

    save_schedule(store)
    _print_session_summary(ui, store, result)
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
    return result


def _finish_without_cards(store: VocabScheduleStore, ui: DrillUi) -> None:
    save_schedule(store)
    ui.print_line(ui.format_dim("  No vocabulary files found in this armory."))
    ui.print_line(
        ui.format_dim(
            "  Add a markdown file with a table (columns: word, translation) to materials/."
        )
    )


def _finish_without_due_cards(store: VocabScheduleStore, ui: DrillUi) -> None:
    save_schedule(store)
    stats = store.stats()
    ui.print_line(ui.format_dim("  No cards due for review right now."))
    if stats["new"] > 0:
        ui.print_line(ui.format_dim(f"  ({stats['new']} new cards available)"))


def _print_drill_header(store: VocabScheduleStore, ui: DrillUi, *, total_due: int) -> None:
    stats = store.stats()
    word_count = f"{stats['total']} words,"
    due_count = f"{total_due} due now"
    ui.print_line()
    ui.print_line(
        f"  {ui.format_prompt('Vocabulary Drill')}  "
        f"{ui.format_dim(word_count)} "
        f"{ui.format_accent(due_count)}"
    )
    ui.print_line(ui.format_dim("  Type your answer, then rate your recall."))
    ui.print_line(ui.format_dim("  Press Ctrl+C to stop early."))


def _prompt_card_answer(
    ui: DrillUi,
    card_state: VocabCardState,
    *,
    index: int,
    total_due: int,
) -> str | None:
    ui.print_line()
    ui.print_line(ui.format_dim(f"  -- Card {index + 1}/{total_due} --"))
    ui.print_line()
    ui.print_line(f"  {ui.format_prompt('Word:')}   {card_state.front}")
    try:
        return ui.prompt_answer("  Type translation: ")
    except (KeyboardInterrupt, EOFError):
        ui.print_line()
        ui.print_line(ui.format_dim("  Drill stopped early."))
        return None


def _print_answer_feedback(ui: DrillUi, user_answer: str, correct_answer: str) -> None:
    ui.print_line()
    match = _answer_matches(user_answer, correct_answer)
    formatted_answer = ui.format_prompt(user_answer) if match else ui.format_dim(user_answer)
    ui.print_line(f"  Your answer:    {formatted_answer}")
    ui.print_line(f"  Correct answer: {ui.format_accent(correct_answer)}")
    ui.print_line()


def _record_card_review(
    store: VocabScheduleStore,
    card_state: VocabCardState,
    rating: Rating,
) -> int:
    schedule_result = schedule_card(card_state, rating)
    review_time = datetime.now(UTC)
    card_state.repetitions = schedule_result.repetitions
    card_state.easiness = schedule_result.easiness
    card_state.interval = schedule_result.interval_days
    card_state.last_review = review_time
    card_state.next_review = review_time + timedelta(days=schedule_result.interval_days)
    store.update_card(card_state)
    return schedule_result.interval_days


def _record_rating(result: DrillResult, rating: Rating) -> None:
    result.cards_reviewed += 1
    if rating == Rating.HARD:
        result.hard_count += 1
    elif rating == Rating.GOOD:
        result.good_count += 1
    else:
        result.easy_count += 1


def _print_next_review(ui: DrillUi, interval_days: int) -> None:
    next_interval = ui.format_accent(_format_interval(interval_days))
    ui.print_line(f"  -> Next review in {next_interval}")
    ui.print_line()


def _print_session_summary(ui: DrillUi, store: VocabScheduleStore, result: DrillResult) -> None:
    if result.cards_reviewed <= 0:
        return
    ui.print_line()
    ui.print_line(ui.format_prompt("  -- Session Complete --"))
    ui.print_line(f"  Reviewed: {result.cards_reviewed} cards")
    ui.print_line(
        f"  Hard: {result.hard_count} | Good: {result.good_count} | Easy: {result.easy_count}"
    )
    _print_remaining_due_summary(ui, store)


def _print_remaining_due_summary(ui: DrillUi, store: VocabScheduleStore) -> None:
    remaining_due = select_due_cards(store.card_list)
    if remaining_due:
        ui.print_line(f"  Next session: ~{len(remaining_due)} cards due")
        return
    soonest = min(
        (card.next_review for card in store.card_list if card.next_review is not None),
        default=None,
    )
    if soonest:
        days_ahead = max(0, (soonest - datetime.now(UTC)).days)
        ui.print_line(f"  All caught up! Next review in ~{_format_interval(max(1, days_ahead))}")
    else:
        ui.print_line("  All cards reviewed!")
