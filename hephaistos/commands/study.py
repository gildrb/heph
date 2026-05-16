"""Study and vocabulary commands: vocab, remind."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from hephaistos.chat.session import ChatSession
from hephaistos.commands._base import Command, CommandResult, ensure_session
from hephaistos.diagnostics.events import capture as capture_analytics
from hephaistos.rag.index import load_or_build
from hephaistos.study import (
    AutopilotSessionType,
    ExamSession,
    StudyAutonomyMode,
    StudyFeedbackType,
    StudyPhase,
    StudyRecallRating,
    activate_exam_session_item,
    exam_session_from_questions,
    milestones_from_exam_session,
    milestones_from_priority,
    next_exam_session_index,
    parse_time_budget_minutes,
    session_type_from_text,
)
from hephaistos.study.exam import (
    ExamChunk,
    select_exam_question,
    select_exam_questions,
    supporting_source_refs,
)
from hephaistos.study.milestones import MilestoneTracker
from hephaistos.study.priority import (
    PriorityAnalysis,
    PriorityChunk,
    PriorityPdfError,
    PriorityTopic,
    analyze_priority,
    generate_priority_report,
    priority_tier,
)
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
_MODE_ALIASES = {
    "manual": StudyAutonomyMode.MANUAL,
    "off": StudyAutonomyMode.MANUAL,
    "guided": StudyAutonomyMode.GUIDED,
    "on": StudyAutonomyMode.AUTOPILOT,
    "autopilot": StudyAutonomyMode.AUTOPILOT,
}


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

        with_scheduled = [card for card in all_cards if card.next_review is not None]
        scheduled = sorted(with_scheduled, key=lambda card: card.next_review or now)
        if scheduled:
            next_card: VocabCardState = scheduled[0]
            assert next_card.next_review is not None
            delta = next_card.next_review - now
            secs = float(delta.total_seconds())
            if secs > 0:
                when = _format_relative_seconds(secs)
                n_scheduled = len(scheduled)
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


class ModeCommand(Command):
    name = "mode"
    description = "Set manual, guided, or autopilot study mode"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        requested = args.strip().lower()
        if not requested:
            _print_mode_status(s)
            return CommandResult()
        mode = _MODE_ALIASES.get(requested)
        if mode is None:
            print_error("Usage: /mode manual, /mode guided, or /mode autopilot")
            return CommandResult()
        if mode is StudyAutonomyMode.AUTOPILOT:
            session_type = AutopilotSessionType.GENERAL
            _start_autopilot_session(s, session_type, None, requested)
            print_success(f"Study mode set to {mode.value}.")
            prompt = _autopilot_start_prompt(session_type, None)
            return CommandResult(output=f"__RESEND__:{prompt}")
        _set_study_mode(s, mode)
        print_success(f"Study mode set to {mode.value}.")
        return CommandResult()


class AutopilotCommand(Command):
    name = "autopilot"
    description = "Let Heph drive a bounded autonomous study session"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        requested = args.strip()
        normalized = requested.lower()
        if normalized == "status":
            _print_mode_status(s)
            return CommandResult()
        if not requested:
            requested = "on"
            normalized = "on"
        if normalized in {"off", "manual"}:
            _set_study_mode(s, StudyAutonomyMode.MANUAL)
            _clear_autopilot_session(s)
            print_success("Autopilot off. Manual study mode is active.")
            return CommandResult()
        if normalized == "guided":
            _set_study_mode(s, StudyAutonomyMode.GUIDED)
            _clear_autopilot_session(s)
            print_success("Guided study mode is active.")
            return CommandResult()

        session_type = session_type_from_text(requested)
        time_budget = parse_time_budget_minutes(requested)
        _start_autopilot_session(s, session_type, time_budget, requested)
        print_success(_autopilot_status_line(session_type, time_budget))
        prompt = _autopilot_start_prompt(session_type, time_budget)
        return CommandResult(output=f"__RESEND__:{prompt}")


class ExamCommand(Command):
    name = "exam"
    description = "Start an active-recall exam question"
    aliases = ("drill",)

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        if s.armory_path is None:
            print_error("No armory attached. Use /armory to open one first.")
            return CommandResult()
        normalized_args = args.strip()
        subcommand_parts = normalized_args.split(maxsplit=1)
        subcommand = subcommand_parts[0].lower() if subcommand_parts else ""
        subcommand_args = subcommand_parts[1] if len(subcommand_parts) > 1 else ""
        if subcommand == "session":
            return self._start_session(s, subcommand_args.strip())
        if subcommand == "next":
            return self._next_question(s)
        if subcommand == "jump":
            return self._jump_question(s, subcommand_args.strip())
        print_info(
            "Active recall works best with materials aside unless your exam allows a cheat "
            "sheet. Use the time limit as real exam pressure."
        )
        topic = normalized_args
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

    @staticmethod
    def _start_session(session: ChatSession, topic: str) -> CommandResult:
        armory_path = session.armory_path
        if armory_path is None:
            print_error("No armory attached. Use /armory to open one first.")
            return CommandResult()
        print_info("Loading all extracted past-exam questions...")
        chunks = list(load_or_build(armory_path).all_chunks)
        questions = select_exam_questions(chunks, topic=topic)
        if not questions:
            print_error("No exam questions found in enabled past-exam materials.")
            return CommandResult()
        exam_session = exam_session_from_questions(questions)
        session.study_state.exam_session = exam_session
        session.study_state.milestone_tracker = MilestoneTracker(
            milestones=milestones_from_exam_session(exam_session)
        )
        label = "question" if len(questions) == 1 else "questions"
        print_success(f"Exam session started with {len(questions)} {label}.")
        return _activate_exam_session_question(session, chunks, 0)

    @staticmethod
    def _next_question(session: ChatSession) -> CommandResult:
        exam_session = session.study_state.exam_session
        if exam_session is None:
            print_error("No exam session is active. Run /exam session first.")
            return CommandResult()
        next_index = next_exam_session_index(exam_session)
        if next_index is None:
            print(_exam_session_summary(exam_session))
            return CommandResult()
        armory_path = session.armory_path
        if armory_path is None:
            print_error("No armory attached. Use /armory to open one first.")
            return CommandResult()
        chunks = list(load_or_build(armory_path).all_chunks)
        return _activate_exam_session_question(session, chunks, next_index)

    @staticmethod
    def _jump_question(session: ChatSession, raw_index: str) -> CommandResult:
        exam_session = session.study_state.exam_session
        if exam_session is None:
            print_error("No exam session is active. Run /exam session first.")
            return CommandResult()
        try:
            index = int(raw_index) - 1
        except ValueError:
            print_error("Usage: /exam jump N")
            return CommandResult()
        if not 0 <= index < len(exam_session.items):
            print_error(f"Question number must be between 1 and {len(exam_session.items)}.")
            return CommandResult()
        armory_path = session.armory_path
        if armory_path is None:
            print_error("No armory attached. Use /armory to open one first.")
            return CommandResult()
        chunks = list(load_or_build(armory_path).all_chunks)
        return _activate_exam_session_question(session, chunks, index)


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
            print_info(_priority_index_progress_line(state, detail))

        print_info("Preparing indexed materials for priority analysis...")
        index = load_or_build(s.armory_path, progress=report_index_progress)
        enabled_chunks = [
            chunk for chunk in index.all_chunks if chunk.source not in s.disabled_source_files
        ]
        enabled_sources = _priority_enabled_sources(enabled_chunks)
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
        s.study_state.milestone_tracker = MilestoneTracker(
            milestones=milestones_from_priority(analysis)
        )
        print_info(_priority_terminal_summary(analysis))
        if focus:
            print_info(f"Focus requested: {focus}")
        print_success(
            f"Priority sheet saved to {report.path} "
            f"({report.topic_count} topics, {report.source_count} sources)."
        )
        return CommandResult()


def _activate_exam_session_question(
    session: ChatSession,
    chunks: Sequence[ExamChunk],
    index: int,
) -> CommandResult:
    exam_session = session.study_state.exam_session
    if exam_session is None:
        print_error("No exam session is active. Run /exam session first.")
        return CommandResult()
    session.study_state.exam_session = activate_exam_session_item(exam_session, index)
    exam_session = session.study_state.exam_session
    active_item = exam_session.active_item
    if active_item is None:
        print_error("Could not activate that exam question.")
        return CommandResult()
    source_refs = [active_item.source_ref, *supporting_source_refs(chunks, active_item.question)]
    session.study_state.phase = StudyPhase.RECALL
    session.study_state.current_item = active_item.question
    session.study_state.expected_source_refs = source_refs
    session.study_state.attempt_count = 0
    session.study_state.last_feedback_type = StudyFeedbackType.CALIBRATING
    session.study_state.retrieval_query = active_item.question
    session.study_state.recall_started_at = datetime.now(UTC)
    session.study_state.last_recall_seconds = None
    session.study_state.last_recall_rating = StudyRecallRating.NONE
    session.study_state.hint_level = 0
    session.study_state.milestone_tracker = MilestoneTracker(
        milestones=milestones_from_exam_session(exam_session)
    )
    print(
        "\n".join(
            [
                f"Exam question {index + 1}/{len(exam_session.items)}",
                _exam_time_limit_line(active_item.marks),
                active_item.question,
                "Answer from memory. Do not open the material unless your exam allows it.",
            ]
        )
    )
    return CommandResult()


def _exam_time_limit_line(marks: int | None) -> str:
    if marks is None:
        minutes = 5
    elif marks <= 4:
        minutes = 3
    elif marks <= 10:
        minutes = 8
    else:
        minutes = 12
    return f"Time limit: {minutes} minutes"


def _exam_session_summary(exam_session: ExamSession) -> str:
    gaps: list[str] = []
    passed = 0
    for index, item in enumerate(exam_session.items, start=1):
        if item.status == "correct":
            passed += 1
            continue
        gaps.append(f"  Q{index}: {item.status} — {item.question[:80]}")
    lines = [
        "Exam session summary",
        f"  Completed: {exam_session.completed_count}/{len(exam_session.items)}",
        f"  Correct: {passed}/{len(exam_session.items)}",
    ]
    if gaps:
        lines.extend(["", "Gap report:", *gaps])
    else:
        lines.append("No gaps recorded.")
    return "\n".join(lines)


def _priority_output_dir() -> Path:
    return Path.home() / "Downloads"


def _priority_enabled_sources(chunks: Sequence[PriorityChunk]) -> list[str]:
    seen_sources: set[str] = set()
    ordered_sources: list[str] = []
    for chunk in chunks:
        if chunk.source in seen_sources:
            continue
        seen_sources.add(chunk.source)
        ordered_sources.append(chunk.source)
    return ordered_sources


def _priority_index_progress_line(state: str, detail: str) -> str:
    if state == "loaded":
        return f"Read index cache {detail}."
    if state == "reading":
        return f"Read material source @{detail.removeprefix('materials/')}."
    if state == "indexed":
        return f"Indexed @{detail.removeprefix('materials/')}."
    if state == "writing":
        return f"Wrote index cache {detail}."
    if state == "skipped":
        return f"Skipped material source {detail}."
    return f"{state}: {detail}"


def _set_study_mode(session: ChatSession, mode: StudyAutonomyMode) -> None:
    session.study_state.autonomy_mode = mode
    if mode is not StudyAutonomyMode.AUTOPILOT:
        session.study_state.autopilot_started_at = None
    session.dirty = True


def _clear_autopilot_session(session: ChatSession) -> None:
    session.study_state.session_goal = ""
    session.study_state.time_budget_minutes = None
    session.study_state.autopilot_session_type = ""
    session.study_state.autopilot_started_at = None
    session.study_state.autopilot_turns = 0
    session.study_state.autopilot_stop_reason = ""
    session.dirty = True


def _start_autopilot_session(
    session: ChatSession,
    session_type: AutopilotSessionType,
    time_budget_minutes: int | None,
    raw_request: str,
) -> None:
    session.study_state.autonomy_mode = StudyAutonomyMode.AUTOPILOT
    session.study_state.session_goal = _autopilot_goal(session_type, raw_request)
    session.study_state.time_budget_minutes = time_budget_minutes
    session.study_state.autopilot_session_type = session_type.value
    session.study_state.autopilot_started_at = datetime.now(UTC)
    session.study_state.autopilot_turns = 0
    session.study_state.autopilot_stop_reason = ""
    session.dirty = True


def _autopilot_goal(session_type: AutopilotSessionType, raw_request: str) -> str:
    if session_type is AutopilotSessionType.EXAM:
        return "exam preparation"
    if session_type is AutopilotSessionType.WEAK_TOPICS:
        return "weak-topic repair"
    if session_type is AutopilotSessionType.REVIEW:
        return "due review"
    if session_type is AutopilotSessionType.SOCRATIC:
        return "Socratic study"
    if session_type is AutopilotSessionType.CRAM:
        return "cram session"
    if session_type is AutopilotSessionType.DEEP:
        return "deep understanding"
    normalized = raw_request.strip().casefold()
    if normalized in {"", "on", "autopilot"}:
        return "autonomous study"
    return raw_request or "autonomous study"


def _autopilot_status_line(
    session_type: AutopilotSessionType,
    time_budget_minutes: int | None,
) -> str:
    suffix = f" for {time_budget_minutes} minute(s)" if time_budget_minutes is not None else ""
    return f"Autopilot {session_type.value} session started{suffix}."


def _autopilot_start_prompt(
    session_type: AutopilotSessionType,
    time_budget_minutes: int | None,
) -> str:
    budget = f"I have {time_budget_minutes} minutes. " if time_budget_minutes is not None else ""
    goal = _autopilot_goal(session_type, "")
    return (
        f"Start an autopilot study session from my materials using the "
        f"{session_type.value} profile. {budget}"
        f"Use {goal} as the session goal. "
        "Drive the session yourself, start with active recall when appropriate, ask one "
        "diagnostic or review question, require my confidence from 0-100%, and do not "
        "reveal answers before I attempt them."
    )


def _print_mode_status(session: ChatSession) -> None:
    study = session.study_state
    lines: list[str] = [f"Study mode: {study.autonomy_mode.value}"]
    if study.autopilot_session_type:
        lines.append(f"Autopilot type: {study.autopilot_session_type}")
    if study.session_goal:
        lines.append(f"Goal: {study.session_goal}")
    if study.time_budget_minutes is not None:
        lines.append(f"Budget: {study.time_budget_minutes} minute(s)")
    if study.autopilot_turns:
        lines.append(f"Autopilot turns: {study.autopilot_turns}")
    if study.autopilot_stop_reason:
        lines.append(f"Stop reason: {study.autopilot_stop_reason}")
    print_info("\n".join(lines))


def _priority_terminal_summary(analysis: PriorityAnalysis, *, limit: int = 5) -> str:
    """Render a compact human-facing priority summary for terminal transcripts."""
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
    lines.extend(
        (f"  - {topic.topic}: {_terminal_priority_tier(topic)}")
        for topic in analysis.topics[:limit]
    )
    if len(analysis.topics) > limit:
        lines.append(f"  - ... {len(analysis.topics) - limit} more in the PDF")
    return "\n".join(lines)


def _terminal_priority_tier(topic: PriorityTopic) -> str:
    return priority_tier(topic)
