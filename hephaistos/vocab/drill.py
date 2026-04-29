"""Interactive vocabulary drill controller — zero-LLM TUI flow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from hephaistos.logging import get_logger
from hephaistos.terminal import (
    STYLE_ACCENT,
    STYLE_DIM,
    STYLE_PROMPT,
    MenuOption,
    direct_input,
    direct_print,
    select_option,
    styled,
)
from hephaistos.vocab.parser import scan_armory
from hephaistos.vocab.scheduler import Rating, ScheduleResult, schedule_card, select_due_cards
from hephaistos.vocab.state import VocabCardState, load_schedule, save_schedule

_log = get_logger("vocab.drill")

_HARD_OPTION = MenuOption("Hard", "had to think about it")
_GOOD_OPTION = MenuOption("Good", "knew it")
_EASY_OPTION = MenuOption("Easy", "instant recall")
_RATING_OPTIONS = [_HARD_OPTION, _GOOD_OPTION, _EASY_OPTION]


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
    u = user_answer.strip().lower()
    c = correct_answer.strip().lower()
    return u == c or u in c or c in u


def _apply_schedule(state: VocabCardState, result: ScheduleResult) -> VocabCardState:
    """Apply a schedule result to a card state and advance timestamps."""
    now = datetime.now(UTC)
    state.repetitions = result.repetitions
    state.easiness = result.easiness
    state.interval = result.interval_days
    state.last_review = now
    state.next_review = now + timedelta(days=result.interval_days)
    return state


def _print_header(card_num: int, total: int, _card: VocabCardState) -> None:
    direct_print("")
    direct_print(
        styled(
            f"  -- Card {card_num}/{total} --",
            STYLE_DIM,
        )
    )
    direct_print("")


def _show_answer_comparison(user_answer: str, correct_answer: str) -> None:
    direct_print("")
    match = _answers_match(user_answer, correct_answer)
    if match:
        direct_print(f"  Your answer:    {styled(user_answer, STYLE_PROMPT)}")
    else:
        direct_print(f"  Your answer:    {styled(user_answer, STYLE_DIM)}")
    direct_print(f"  Correct answer: {styled(correct_answer, STYLE_ACCENT)}")
    direct_print("")


def _get_rating() -> Rating | None:
    """Show rating menu and return the user's choice, or None on cancel."""
    selected = select_option("How did it feel?", _RATING_OPTIONS)
    if selected is None:
        return None
    return [Rating.HARD, Rating.GOOD, Rating.EASY][selected]


def run_drill(armory_path: Path, *, card_limit: int = 0) -> DrillResult | None:
    """Run an interactive vocabulary drill session.

    Parameters
    ----------
    armory_path :
        Path to the armory containing vocab files.
    card_limit :
        Maximum number of cards to drill. 0 means drill all due cards.

    Returns
    -------
    DrillResult or None
        Session summary, or None if there are no cards to drill.
    """
    deck = scan_armory(armory_path)
    store = load_schedule(armory_path)
    new_cards = store.sync_with_deck(deck)

    if not deck.cards:
        save_schedule(store)
        direct_print(styled("  No vocabulary files found in this armory.", STYLE_DIM))
        direct_print(
            styled(
                "  Add a markdown file with a table (columns: word, translation) "
                "to source/ or library/.",
                STYLE_DIM,
            )
        )
        return None

    if new_cards:
        _log.info(
            "vocab deck synced",
            extra={"fields": {"new_cards": new_cards}},
        )

    due = select_due_cards(store.card_list, limit=card_limit)
    if not due:
        save_schedule(store)
        stats = store.stats()
        direct_print(styled("  No cards due for review right now.", STYLE_DIM))
        if stats["new"] > 0:
            direct_print(styled(f"  ({stats['new']} new cards available)", STYLE_DIM))
        return None

    total_due = len(due)
    stats = store.stats()
    direct_print("")
    direct_print(
        f"  {styled('Vocabulary Drill', STYLE_PROMPT)}  "
        f"{styled(f'{stats["total"]} words,', STYLE_DIM)} "
        f"{styled(f'{total_due} due now', STYLE_ACCENT)}"
    )
    direct_print(styled("  Type your answer, then rate your recall.", STYLE_DIM))
    direct_print(styled("  Press Ctrl+C to stop early.", STYLE_DIM))

    result = DrillResult()

    for i, card_state in enumerate(due):
        _print_header(i + 1, total_due, card_state)

        # Show the front (the word to translate).
        direct_print(f"  {styled('Word:', STYLE_PROMPT)}   {card_state.front}")

        # Get user's answer.
        try:
            user_answer = direct_input("  Type translation: ")
        except (KeyboardInterrupt, EOFError):
            direct_print("")
            direct_print(styled("  Drill stopped early.", STYLE_DIM))
            break

        if not user_answer.strip():
            direct_print(styled("  (skipped)", STYLE_DIM))
            continue

        # Show comparison.
        _show_answer_comparison(user_answer, card_state.back)

        # Get rating.
        rating = _get_rating()
        if rating is None:
            direct_print(styled("  Drill stopped.", STYLE_DIM))
            break

        # Apply SM-2 scheduling.
        schedule_result = schedule_card(card_state, rating)
        _apply_schedule(card_state, schedule_result)
        store.update_card(card_state)

        # Track stats.
        result.cards_reviewed += 1
        if rating == Rating.HARD:
            result.hard_count += 1
        elif rating == Rating.GOOD:
            result.good_count += 1
        else:
            result.easy_count += 1

        # Show next interval.
        next_interval = styled(_format_interval(schedule_result.interval_days), STYLE_ACCENT)
        direct_print(f"  -> Next review in {next_interval}")
        direct_print("")

    # Persist all changes.
    save_schedule(store)

    # Show session summary.
    if result.cards_reviewed > 0:
        direct_print("")
        direct_print(styled("  -- Session Complete --", STYLE_PROMPT))
        direct_print(f"  Reviewed: {result.cards_reviewed} cards")
        direct_print(
            f"  Hard: {result.hard_count} | Good: {result.good_count} | Easy: {result.easy_count}"
        )

        # Estimate next session.
        remaining_due = select_due_cards(store.card_list)
        if remaining_due:
            direct_print(f"  Next session: ~{len(remaining_due)} cards due")
        else:
            # Find the soonest next review.
            soonest: datetime | None = None
            for cs in store.card_list:
                if cs.next_review is not None and (soonest is None or cs.next_review < soonest):
                    soonest = cs.next_review
            if soonest:
                days_ahead = max(0, (soonest - datetime.now(UTC)).days)
                direct_print(
                    f"  All caught up! Next review in ~{_format_interval(max(1, days_ahead))}"
                )
            else:
                direct_print("  All cards reviewed!")

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
