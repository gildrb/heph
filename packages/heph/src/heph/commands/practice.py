"""Practice and vocabulary commands."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from harness.chat.session import ChatSession
from harness.documents import (
    RecallFeedbackType,
    RecallPhase,
    RecallRating,
)
from harness.documents.exam_bank import (
    ExamBank,
    ExamBankItem,
    exam_bank_build_prompt,
    exam_bank_path,
    load_exam_bank,
    select_exam_bank_item,
)
from harness.documents.priority import (
    PriorityAnalysis,
    PriorityPdfError,
    analyze_priority,
    generate_priority_report,
    priority_tier,
)
from harness.materials import material_display_name
from harness.rag.index import load_or_build
from harness.vocab.drill import run_drill
from harness.vocab.parser import scan_armory
from harness.vocab.scheduler import Rating
from harness.vocab.state import load_schedule, save_schedule
from interfaces.terminal import (
    STYLE_ACCENT,
    STYLE_DIM,
    STYLE_PROMPT,
    MenuOption,
    confirm,
    direct_input,
    direct_print,
    menu_label_value,
    print_error,
    print_info,
    print_success,
    select_option,
    styled,
)

from heph.commands._base import Command, CommandResult, ensure_session

_HARD_OPTION = MenuOption("HARD", menu_label_value("effort", "had to think"))
_GOOD_OPTION = MenuOption("GOOD", menu_label_value("effort", "knew it"))
_EASY_OPTION = MenuOption("EASY", menu_label_value("effort", "instant recall"))
_RATING_OPTIONS = [_HARD_OPTION, _GOOD_OPTION, _EASY_OPTION]
_PRIORITY_PROGRESS_MESSAGES = {
    "loaded": "Read index cache {detail}.",
    "reading": "Read material source @{detail}.",
    "indexed": "Indexed @{detail}.",
    "writing": "Wrote index cache {detail}.",
    "skipped": "Skipped material source {detail}.",
}


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
        run_drill(s.armory_path, TerminalDrillUi())
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
    session.recall_state.phase = RecallPhase.RECALL
    session.recall_state.current_item = item.question
    session.recall_state.expected_source_refs = item.source_refs
    session.recall_state.attempt_count = 0
    session.recall_state.last_feedback_type = RecallFeedbackType.CALIBRATING
    session.recall_state.retrieval_query = item.question
    session.recall_state.recall_started_at = datetime.now(UTC)
    session.recall_state.last_recall_seconds = None
    session.recall_state.last_recall_rating = RecallRating.NONE
    session.recall_state.last_confidence = None
    session.recall_state.hint_level = 0
    session.recall_state.start_practice_session(
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
