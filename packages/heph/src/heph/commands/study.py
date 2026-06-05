"""Learning and vocabulary commands: vocabulary, remind."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from hephaion.chat.session import ChatSession
from hephaion.diagnostics.events import capture as capture_analytics
from hephaion.materials import material_display_name
from hephaion.rag.index import load_or_build
from hephaion.study import (
    LearningFeedbackType,
    LearningPhase,
    RecallRating,
)
from hephaion.study.exam_bank import (
    ExamBank,
    ExamBankItem,
    exam_bank_build_prompt,
    exam_bank_path,
    load_exam_bank,
    select_exam_bank_item,
)
from hephaion.study.priority import (
    PriorityAnalysis,
    PriorityPdfError,
    analyze_priority,
    generate_priority_report,
    priority_tier,
)
from hephaion.study.schedule import RecallItemState, load_recall_schedule
from hephaion.vocab.drill import run_drill
from hephaion.vocab.parser import scan_armory
from hephaion.vocab.scheduler import Rating, select_due_cards
from hephaion.vocab.state import VocabCardState, load_schedule, save_schedule
from interfaces.terminal import (
    STYLE_ACCENT,
    STYLE_DIM,
    STYLE_PROMPT,
    STYLE_SUCCESS,
    MenuOption,
    confirm,
    direct_input,
    direct_print,
    print_error,
    print_info,
    print_success,
    select_option,
    styled,
)

from heph.commands._base import Command, CommandResult, ensure_session

_HARD_OPTION = MenuOption("Hard", "had to think about it")
_GOOD_OPTION = MenuOption("Good", "knew it")
_EASY_OPTION = MenuOption("Easy", "instant recall")
_RATING_OPTIONS = [_HARD_OPTION, _GOOD_OPTION, _EASY_OPTION]
_PRIORITY_PROGRESS_MESSAGES = {
    "loaded": "Read index cache {detail}.",
    "reading": "Read material source @{detail}.",
    "indexed": "Indexed @{detail}.",
    "writing": "Wrote index cache {detail}.",
    "skipped": "Skipped material source {detail}.",
}


@dataclass(frozen=True, slots=True)
class ReminderState:
    all_cards: Sequence[VocabCardState]
    due_cards: Sequence[VocabCardState]
    recall_items: Sequence[RecallItemState]
    due_recall_items: Sequence[RecallItemState]
    now: datetime


def _format_recall_item_metadata(item: RecallItemState) -> str:
    details: list[str] = []
    if item.concept:
        details.append(f"concept: {item.concept[:40]}")
    if item.error_type:
        details.append(f"last: {item.error_type}")
    if item.failures > 0:
        details.append(f"failures: {item.failures}")
    if item.last_confidence is not None:
        details.append(f"confidence: {item.last_confidence:.0%}")
    if item.exam_importance > 0:
        details.append(f"exam priority: {item.exam_importance:.0%}")
    return ", ".join(details)


def _next_scheduled_line(
    next_reviews: Sequence[datetime | None],
    now: datetime,
    template: str,
) -> str | None:
    scheduled = sorted(review for review in next_reviews if review is not None)
    if not scheduled:
        return None
    secs = float((scheduled[0] - now).total_seconds())
    if secs <= 0:
        return None
    hours = secs / 3600
    if hours < 1:
        when = f"{int(secs / 60)}m"
    elif hours < 48:
        when = f"{int(hours)}h"
    else:
        when = f"{int(hours / 24)}d"
    count = len(scheduled)
    return template.format(
        when=when,
        count=count,
        plural="" if count == 1 else "s",
    )


def _remind_status_lines(
    all_cards: Sequence[VocabCardState],
    due_cards: Sequence[VocabCardState],
    recall_items: Sequence[RecallItemState],
    due_recall_items: Sequence[RecallItemState],
) -> list[str]:
    lines: list[str] = []

    if due_cards:
        lines.append(
            f"You have {len(due_cards)} card{'s' if len(due_cards) != 1 else ''} due for review."
        )
        lines.append(f"  Run {styled('/vocabulary', STYLE_ACCENT)} to review them now.")
    elif all_cards:
        lines.append(styled("Vocabulary is caught up.", STYLE_SUCCESS))

    if due_recall_items:
        item_plural = "s" if len(due_recall_items) != 1 else ""
        lines.append(f"You have {len(due_recall_items)} recall item{item_plural} due.")
        lines.append(f"  Run {styled('/exam', STYLE_ACCENT)} or ask to review a due recall item.")
    elif recall_items:
        lines.append(styled("Material-backed recall items are caught up.", STYLE_SUCCESS))

    return lines or ["No vocabulary cards yet, but you can start with /exam or /priority."]


def _due_recall_item_lines(due_recall_items: Sequence[RecallItemState]) -> list[str]:
    if not due_recall_items:
        return []
    lines = ["", "Due recall items:"]
    for item in due_recall_items[:10]:
        label = item.item or item.retrieval_query
        lines.append(f"  {styled(label[:60], STYLE_DIM)}")
        metadata = _format_recall_item_metadata(item)
        if metadata:
            lines.append(f"    {styled(metadata, STYLE_DIM)}")
    if len(due_recall_items) > 10:
        lines.append(f"  ... and {len(due_recall_items) - 10} more")
    return lines


def _due_vocab_card_lines(due_cards: Sequence[VocabCardState]) -> list[str]:
    if not due_cards:
        return []
    lines = ["", "Due cards:"]
    lines.extend(f"  {styled(card.front[:60], STYLE_DIM)}" for card in due_cards[:10])
    if len(due_cards) > 10:
        lines.append(f"  ... and {len(due_cards) - 10} more")
    return lines


class TerminalDrillUi:
    prompt_answer = staticmethod(direct_input)

    def print_line(self, text: str = "") -> None:
        direct_print(text)

    def prompt_rating(self) -> Rating | None:
        selected = select_option("How did it feel?", _RATING_OPTIONS)
        return None if selected is None else [Rating.HARD, Rating.GOOD, Rating.EASY][selected]

    def format_prompt(self, text: str) -> str:
        return styled(text, STYLE_PROMPT)

    def format_accent(self, text: str) -> str:
        return styled(text, STYLE_ACCENT)

    def format_dim(self, text: str) -> str:
        return styled(text, STYLE_DIM)


class VocabCommand(Command):
    name = "vocabulary"
    description = "Practice vocabulary translations from your materials"

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
        result = run_drill(s.armory_path, TerminalDrillUi())
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
        source_files = ", ".join(deck.source_files) if deck.source_files else "none"
        print(
            f"Vocabulary: Total cards {stats['total']}; new {stats['new']}; "
            f"due now {stats['due']}; mastered {stats['mastered']}; "
            f"material files: {source_files}."
        )
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
    description = "Show upcoming review reminders and due cards"

    def handle(self, session: object, args: str) -> CommandResult:
        del args
        s = ensure_session(session)
        if s.armory_path is None:
            print_error("No armory attached. Use /armory to open one.")
            return CommandResult()

        reminders = _load_reminder_state(s.armory_path)
        if not reminders.all_cards and not reminders.recall_items:
            print_info(
                "No scheduled reviews yet. Use /exam or ask for a material-backed question "
                "to start active recall."
            )
            return CommandResult()

        print("\n".join(_reminder_lines(reminders)))
        return CommandResult()


def _load_reminder_state(armory_path: Path) -> ReminderState:
    deck = scan_armory(armory_path)
    store = load_schedule(armory_path)
    store.sync_with_deck(deck)
    save_schedule(store)

    now = datetime.now(UTC)
    recall_store = load_recall_schedule(armory_path)
    return ReminderState(
        all_cards=store.card_list,
        due_cards=select_due_cards(store.card_list),
        recall_items=recall_store.item_list,
        due_recall_items=recall_store.due_items(now=now),
        now=now,
    )


def _reminder_lines(reminders: ReminderState) -> list[str]:
    lines = _remind_status_lines(
        reminders.all_cards,
        reminders.due_cards,
        reminders.recall_items,
        reminders.due_recall_items,
    )
    lines.extend(_next_recall_lines(reminders))
    lines.extend(_due_recall_item_lines(reminders.due_recall_items))
    if not reminders.all_cards:
        return lines
    if (
        not reminders.due_cards
        and not reminders.due_recall_items
        and not _has_caught_up_line(lines)
    ):
        lines.append(styled("All caught up!", STYLE_SUCCESS))
    lines.extend(_next_vocab_lines(reminders))
    lines.extend(_due_vocab_card_lines(reminders.due_cards))
    return lines


def _next_recall_lines(reminders: ReminderState) -> list[str]:
    line = _next_scheduled_line(
        [item.next_review for item in reminders.recall_items],
        reminders.now,
        "  Next recall item in {when} ({count} item(s) scheduled).",
    )
    return [] if line is None else [line]


def _next_vocab_lines(reminders: ReminderState) -> list[str]:
    line = _next_scheduled_line(
        [card.next_review for card in reminders.all_cards],
        reminders.now,
        "  Next review in {when} ({count} card{plural} scheduled).",
    )
    return [] if line is None else [line]


def _has_caught_up_line(lines: Sequence[str]) -> bool:
    return any("caught up" in line for line in lines)


class ExamCommand(Command):
    name = "exam"
    description = "Start an active-recall exam question"
    aliases = ("drill",)

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        if s.armory_path is None:
            print_error("No armory attached. Use /armory to open one first.")
            return CommandResult()
        topic = _exam_topic(args)
        bank_path = exam_bank_path(s.armory_path)
        if _exam_build_requested(args):
            print_info("Building a structured exam bank from indexed materials...")
            return CommandResult(output=f"__RESEND__:{exam_bank_build_prompt()}")
        if not bank_path.is_file():
            print_info(
                "No structured exam bank found. Run /exam build once, then /exam starts "
                "from the saved bank without filling the chat context."
            )
            return CommandResult()

        bank = _enabled_exam_bank(load_exam_bank(s.armory_path), s.disabled_source_files)
        item = select_exam_bank_item(bank, topic=topic)
        if item is not None:
            _start_exam_recall(s, item)
            _print_exam_item(item)
            return CommandResult()
        print_info(
            "No eligible exam-bank items are available. Run /exam build to regenerate the "
            "structured bank, or add material that pairs practice prompts with source-backed "
            "evaluation refs."
        )
        return CommandResult()


def _exam_build_requested(args: str) -> bool:
    return args.strip().casefold() in {"build", "rebuild"}


def _exam_topic(args: str) -> str:
    stripped = args.strip()
    return "" if _exam_build_requested(stripped) else stripped


def _enabled_exam_bank(bank: ExamBank, disabled_sources: set[str]) -> ExamBank:
    return ExamBank(
        items=tuple(item for item in bank.items if _exam_item_enabled(item, disabled_sources))
    )


def _exam_item_enabled(item: ExamBankItem, disabled_sources: set[str]) -> bool:
    return bool(
        item.question
        and _has_enabled_ref(item.question_source_refs, disabled_sources)
        and _has_enabled_ref(item.result_source_refs, disabled_sources)
    )


def _has_enabled_ref(refs: Sequence[str], disabled_sources: set[str]) -> bool:
    return any(_source_from_ref(ref) not in disabled_sources for ref in refs)


def _source_from_ref(ref: str) -> str:
    return ref.partition("#chunk=")[0]


def _start_exam_recall(session: ChatSession, item: ExamBankItem) -> None:
    session.learning_state.phase = LearningPhase.RECALL
    session.learning_state.current_item = item.question
    session.learning_state.expected_source_refs = item.source_refs
    session.learning_state.attempt_count = 0
    session.learning_state.last_feedback_type = LearningFeedbackType.CALIBRATING
    session.learning_state.retrieval_query = item.question
    session.learning_state.recall_started_at = datetime.now(UTC)
    session.learning_state.last_recall_seconds = None
    session.learning_state.last_recall_rating = RecallRating.NONE
    session.learning_state.last_confidence = None
    session.learning_state.hint_level = 0
    session.learning_state.start_practice_session(
        session_type="exam",
        session_goal=", ".join(item.topics) or "structured exam-bank practice",
        time_budget_minutes=None,
    )


def _print_exam_item(item: ExamBankItem) -> None:
    print_info(
        "Active recall works best with materials aside unless your exam allows a cheat "
        "sheet. Use the time limit as real exam pressure."
    )
    print(
        "\n".join(
            [
                "Exam question",
                f"Time limit: {item.effective_time_limit_minutes} minutes",
                item.question,
                "Answer from memory. Then tell Heph what your result was.",
            ]
        )
    )


class PriorityCommand(Command):
    name = "priority"
    description = "Generate a printable priority PDF cheat sheet"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        if s.armory_path is None:
            print_error("No armory attached. Use /armory to open one first.")
            return CommandResult()
        focus = args.strip()

        def report_priority_progress(message: str) -> None:
            print_info(message)

        def report_index_progress(state: str, detail: str) -> None:
            template = _PRIORITY_PROGRESS_MESSAGES.get(state)
            print_info(
                template.format(detail=material_display_name(detail))
                if template is not None
                else f"{state}: {detail}"
            )

        print_info("Preparing indexed materials for priority analysis...")
        index = load_or_build(s.armory_path, progress=report_index_progress)
        enabled_chunks = [
            chunk for chunk in index.all_chunks if chunk.source not in s.disabled_source_files
        ]
        enabled_sources = list(dict.fromkeys(chunk.source for chunk in enabled_chunks))
        print_info(
            "Indexed "
            f"{len(enabled_sources)} enabled source(s) across {len(enabled_chunks)} chunk(s)."
        )

        print_info("Analyzing recurring topics from enabled materials...")
        analysis = analyze_priority(enabled_chunks, limit=12, progress=report_priority_progress)
        print_info("Generating printable priority sheet...")
        try:
            report = generate_priority_report(
                analysis,
                _priority_output_dir(),
                config=s.config,
                focus=focus,
                progress=report_priority_progress,
            )
        except PriorityPdfError as exc:
            print_error(str(exc))
            return CommandResult()
        print_info(_priority_terminal_summary(analysis))
        if focus:
            print_info(f"Focus requested: {focus}")
        print_success(
            f"Priority sheet saved to {report.path} "
            f"({report.topic_count} topics, {report.source_count} sources)."
        )
        return CommandResult()


def _priority_output_dir() -> Path:
    return Path.home() / "Downloads"


def _priority_terminal_summary(analysis: PriorityAnalysis, *, limit: int = 5) -> str:
    if not analysis.topics:
        return "Local priority scan: no recurring indexed topics were found."

    past_exam_count = len(analysis.past_exam_sources)
    support_count = len(analysis.material_sources)
    top_priorities = ", ".join(topic.topic for topic in analysis.topics[:3])
    lines = [
        (
            "Local priority scan: "
            f"{len(analysis.topics)} candidate topics, "
            f"{past_exam_count} past exam source(s), "
            f"{support_count} supporting source(s)."
        )
    ]
    lines.append(f"Top priorities: {top_priorities}.")
    lines.append("Priority tiers:")
    lines.extend(f"  - {topic.topic}: {priority_tier(topic)}" for topic in analysis.topics[:limit])
    if len(analysis.topics) > limit:
        lines.append(f"  - ... {len(analysis.topics) - limit} more in the PDF")
    return "\n".join(lines)
