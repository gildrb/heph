"""Study and vocabulary commands: vocab, remind."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from hephaistos.chat.session import ChatSession
from hephaistos.commands._base import Command, CommandResult, ensure_session
from hephaistos.diagnostics.events import capture as capture_analytics
from hephaistos.rag.index import load_or_build
from hephaistos.study import StudyFeedbackType, StudyPhase, StudyRecallRating
from hephaistos.study.exam import select_exam_question, supporting_source_refs
from hephaistos.study.priority import PriorityAnalysis, analyze_priority, generate_priority_report
from hephaistos.study.schedule import StudyItemState, load_study_schedule
from hephaistos.terminal import (
    STYLE_PROMPT,
    MenuOption,
    confirm,
    direct_input,
    direct_print,
    select_option,
)
from hephaistos.terminal.display import (
    STYLE_ACCENT,
    STYLE_DIM,
    STYLE_SUCCESS,
    print_error,
    print_info,
    print_success,
    styled,
)
from hephaistos.vocab.drill import run_drill
from hephaistos.vocab.parser import scan_armory
from hephaistos.vocab.scheduler import Rating, select_due_cards
from hephaistos.vocab.state import VocabCardState, load_schedule, save_schedule

_HARD_OPTION = MenuOption("Hard", "had to think about it")
_GOOD_OPTION = MenuOption("Good", "knew it")
_EASY_OPTION = MenuOption("Easy", "instant recall")
_RATING_OPTIONS = [_HARD_OPTION, _GOOD_OPTION, _EASY_OPTION]


def _format_relative_seconds(seconds: float) -> str:
    hours = seconds / 3600
    if hours < 1:
        return f"{int(seconds / 60)}m"
    if hours < 48:
        return f"{int(hours)}h"
    return f"{int(hours / 24)}d"


def _format_study_item_metadata(item: StudyItemState) -> str:
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


class TerminalDrillUi:
    """Terminal adapter for the reusable vocabulary drill workflow."""

    def print_line(self, text: str = "") -> None:
        direct_print(text)

    def prompt_answer(self, prompt: str) -> str:
        return direct_input(prompt)

    def prompt_rating(self) -> Rating | None:
        selected = select_option("How did it feel?", _RATING_OPTIONS)
        if selected is None:
            return None
        return [Rating.HARD, Rating.GOOD, Rating.EASY][selected]

    def format_prompt(self, text: str) -> str:
        return styled(text, STYLE_PROMPT)

    def format_accent(self, text: str) -> str:
        return styled(text, STYLE_ACCENT)

    def format_dim(self, text: str) -> str:
        return styled(text, STYLE_DIM)


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
        study_store = load_study_schedule(s.armory_path)
        due_study_items = study_store.due_items(now=now)

        if not all_cards and not study_store.item_list:
            print_info(
                "No scheduled reviews yet. Use /exam or ask for a material-backed question "
                "to start active recall."
            )
            return CommandResult()

        lines: list[str] = []

        if due:
            lines.append(f"You have {len(due)} card{'s' if len(due) != 1 else ''} due for review.")
            lines.append(f"  Run {styled('/vocab drill', STYLE_ACCENT)} to study them now.")
        elif all_cards:
            lines.append(styled("Vocabulary is caught up.", STYLE_SUCCESS))

        if due_study_items:
            item_plural = "s" if len(due_study_items) != 1 else ""
            lines.append(
                f"You have {len(due_study_items)} study item{item_plural} due for active recall."
            )
            lines.append(f"  Run {styled('/exam', STYLE_ACCENT)} or ask to review a due item.")
        elif study_store.item_list:
            lines.append(styled("Material-backed study items are caught up.", STYLE_SUCCESS))

        if not lines:
            lines.append("No vocabulary cards yet, but you can start with /exam or /priority.")

        scheduled_study = [item for item in study_store.item_list if item.next_review is not None]
        if scheduled_study:
            next_item = min(scheduled_study, key=lambda item: item.next_review or now)
            assert next_item.next_review is not None
            delta = next_item.next_review - now
            secs = float(delta.total_seconds())
            if secs > 0:
                lines.append(
                    f"  Next study item in {_format_relative_seconds(secs)} "
                    f"({len(scheduled_study)} item(s) scheduled)."
                )

        if due_study_items:
            lines.append("")
            lines.append("Due study items:")
            for item in due_study_items[:10]:
                label = item.item or item.retrieval_query
                lines.append(f"  {styled(label[:60], STYLE_DIM)}")
                metadata = _format_study_item_metadata(item)
                if metadata:
                    lines.append(f"    {styled(metadata, STYLE_DIM)}")
            if len(due_study_items) > 10:
                lines.append(f"  ... and {len(due_study_items) - 10} more")

        if not all_cards:
            print("\n".join(lines))
            return CommandResult()

        if not due and not due_study_items and not any("caught up" in line for line in lines):
            lines.append(styled("All caught up!", STYLE_SUCCESS))

        with_scheduled = [c for c in all_cards if c.next_review is not None]
        scheduled = sorted(with_scheduled, key=lambda c: c.next_review)  # type: ignore[arg-type]
        if scheduled:
            next_card: VocabCardState = scheduled[0]  # type: ignore[reportUnknownVariableType]
            assert next_card.next_review is not None  # type: ignore[reportUnknownMemberType]
            delta = next_card.next_review - now  # type: ignore[reportUnknownMemberType,reportUnknownVariableType]
            secs = float(delta.total_seconds())  # type: ignore[reportUnknownMemberType]
            if secs > 0:
                when = _format_relative_seconds(secs)
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


class ExamCommand(Command):
    name = "exam"
    description = "Start an active-recall exam question"
    aliases = ("drill",)

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        if s.armory_path is None:
            print_error("No armory attached. Use /armory to open one first.")
            return CommandResult()
        print_info(
            "Active recall works best with materials aside unless your exam allows a cheat "
            "sheet. Use the time limit as real exam pressure."
        )
        topic = args.strip()
        chunks = list(load_or_build(s.armory_path).all_chunks)
        question = select_exam_question(chunks, topic=topic)
        if question is not None:
            source_refs = [
                question.source_ref,
                *supporting_source_refs(chunks, question.question),
            ]
            s.study_state.phase = StudyPhase.RECALL
            s.study_state.current_item = question.question
            s.study_state.expected_source_refs = source_refs
            s.study_state.attempt_count = 0
            s.study_state.last_feedback_type = StudyFeedbackType.CALIBRATING
            s.study_state.retrieval_query = question.question
            s.study_state.recall_started_at = datetime.now(UTC)
            s.study_state.last_recall_seconds = None
            s.study_state.last_recall_rating = StudyRecallRating.NONE
            print(
                "\n".join(
                    [
                        "Exam question",
                        f"Time limit: {question.time_limit_minutes} minutes",
                        question.question,
                        "Answer from memory. Do not open the material unless your exam allows it.",
                    ]
                )
            )
            return CommandResult()
        if topic:
            prompt = (
                f"Ask me one random exam-style question about {topic}. Include a concrete "
                "time limit, require me to reason from memory, and do not show the result, "
                "answer key, rubric, source explanation, source IDs, or citations until "
                "after my attempt."
            )
        else:
            prompt = (
                "Ask me one random exam-style question from my past exams and materials. "
                "Include a concrete time limit, require me to reason from memory, and do "
                "not show the result, answer key, rubric, source explanation, source IDs, "
                "or citations until after my attempt."
            )
        return CommandResult(output=f"__RESEND__:{prompt}")


class PriorityCommand(Command):
    name = "priority"
    description = "Find priority topics and prerequisites"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        if s.armory_path is None:
            print_error("No armory attached. Use /armory to open one first.")
            return CommandResult()
        focus = args.strip()
        index = load_or_build(s.armory_path)
        enabled_chunks = [
            chunk for chunk in index.all_chunks if chunk.source not in s.disabled_source_files
        ]
        analysis = analyze_priority(enabled_chunks, limit=12)
        report = generate_priority_report(
            analysis,
            _priority_output_dir(),
            config=s.config,
            focus=focus,
        )
        print_info(_priority_terminal_summary(analysis))
        if focus:
            print_info(f"Focus requested: {focus}")
        print_success(
            f"Priority report saved to {report.path} "
            f"({report.topic_count} topics, {report.source_count} sources)."
        )
        return CommandResult()


def _priority_output_dir() -> Path:
    return Path.home() / "Downloads"


def _priority_terminal_summary(analysis: PriorityAnalysis, *, limit: int = 5) -> str:
    """Render a compact human-facing priority summary for terminal transcripts."""
    if not analysis.topics:
        return "Local priority scan: no recurring indexed topics were found."

    past_exam_count = len(analysis.past_exam_sources)
    support_count = len(analysis.material_sources)
    lines = [
        (
            "Local priority scan: "
            f"{len(analysis.topics)} candidate topics, "
            f"{past_exam_count} past exam source(s), "
            f"{support_count} supporting source(s)."
        )
    ]
    lines.append("Top candidates:")
    lines.extend(
        (
            f"  - {topic.topic}: score {topic.score:.1f}, "
            f"exam hits {topic.exam_hits}, exam marks {topic.exam_marks}, "
            f"material hits {topic.material_hits}"
        )
        for topic in analysis.topics[:limit]
    )
    if len(analysis.topics) > limit:
        lines.append(f"  - ... {len(analysis.topics) - limit} more in the HTML report")
    return "\n".join(lines)
