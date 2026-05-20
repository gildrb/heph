"""Study and vocabulary commands: vocabulary, remind."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from hephaistos.chat.session import ChatSession
from hephaistos.commands._base import Command, CommandResult, ensure_session
from hephaistos.diagnostics.events import capture as capture_analytics
from hephaistos.materials import material_display_name
from hephaistos.rag.index import load_or_build
from hephaistos.study import (
    AutopilotSessionType,
    StudyAutonomyMode,
    StudyFeedbackType,
    StudyPhase,
    StudyRecallRating,
    parse_time_budget_minutes,
    session_type_from_text,
)
from hephaistos.study.exam import select_exam_question, supporting_source_refs
from hephaistos.study.priority import (
    PriorityAnalysis,
    PriorityPdfError,
    analyze_priority,
    generate_priority_report,
    priority_tier,
)
from hephaistos.study.schedule import StudyItemState, load_study_schedule
from hephaistos.terminal import (
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
_AUTOPILOT_GOALS = {
    AutopilotSessionType.EXAM: "exam preparation",
    AutopilotSessionType.WEAK_TOPICS: "weak-topic repair",
    AutopilotSessionType.REVIEW: "due review",
    AutopilotSessionType.SOCRATIC: "Socratic review",
    AutopilotSessionType.CRAM: "cram session",
    AutopilotSessionType.DEEP: "deep understanding",
}
_PRIORITY_PROGRESS_MESSAGES = {
    "loaded": "Read index cache {detail}.",
    "reading": "Read material source @{detail}.",
    "indexed": "Indexed @{detail}.",
    "writing": "Wrote index cache {detail}.",
    "skipped": "Skipped material source {detail}.",
}


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
    study_items: Sequence[StudyItemState],
    due_study_items: Sequence[StudyItemState],
) -> list[str]:
    lines: list[str] = []

    if due_cards:
        lines.append(
            f"You have {len(due_cards)} card{'s' if len(due_cards) != 1 else ''} due for review."
        )
        lines.append(f"  Run {styled('/vocabulary', STYLE_ACCENT)} to review them now.")
    elif all_cards:
        lines.append(styled("Vocabulary is caught up.", STYLE_SUCCESS))

    if due_study_items:
        item_plural = "s" if len(due_study_items) != 1 else ""
        lines.append(f"You have {len(due_study_items)} recall item{item_plural} due.")
        lines.append(f"  Run {styled('/exam', STYLE_ACCENT)} or ask to review a due item.")
    elif study_items:
        lines.append(styled("Material-backed recall items are caught up.", STYLE_SUCCESS))

    return lines or ["No vocabulary cards yet, but you can start with /exam or /priority."]


def _due_study_item_lines(due_study_items: Sequence[StudyItemState]) -> list[str]:
    if not due_study_items:
        return []
    lines = ["", "Due recall items:"]
    for item in due_study_items[:10]:
        label = item.item or item.retrieval_query
        lines.append(f"  {styled(label[:60], STYLE_DIM)}")
        metadata = _format_study_item_metadata(item)
        if metadata:
            lines.append(f"    {styled(metadata, STYLE_DIM)}")
    if len(due_study_items) > 10:
        lines.append(f"  ... and {len(due_study_items) - 10} more")
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
    description = "Show upcoming review reminders and due cards"

    def handle(self, session: object, args: str) -> CommandResult:
        del args
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

        lines = _remind_status_lines(
            all_cards,
            due,
            study_store.item_list,
            due_study_items,
        )
        next_study_line = _next_scheduled_line(
            [item.next_review for item in study_store.item_list],
            now,
            "  Next recall item in {when} ({count} item(s) scheduled).",
        )
        if next_study_line is not None:
            lines.append(next_study_line)

        lines.extend(_due_study_item_lines(due_study_items))

        if not all_cards:
            print("\n".join(lines))
            return CommandResult()

        if not due and not due_study_items and not any("caught up" in line for line in lines):
            lines.append(styled("All caught up!", STYLE_SUCCESS))

        next_vocab_line = _next_scheduled_line(
            [card.next_review for card in all_cards],
            now,
            "  Next review in {when} ({count} card{plural} scheduled).",
        )
        if next_vocab_line is not None:
            lines.append(next_vocab_line)

        lines.extend(_due_vocab_card_lines(due))

        print("\n".join(lines))
        return CommandResult()


class ModeCommand(Command):
    name = "mode"
    description = "Set manual, guided, or autopilot review mode"

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
            print_success(f"Review mode set to {mode.value}.")
            prompt = _autopilot_start_prompt(session_type, None)
            return CommandResult(output=f"__RESEND__:{prompt}")
        _set_study_mode(s, mode)
        print_success(f"Review mode set to {mode.value}.")
        return CommandResult()


class AutopilotCommand(Command):
    name = "autopilot"
    description = "Let Heph drive a bounded material review session"

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
            print_success("Autopilot off. Manual review mode is active.")
            return CommandResult()
        if normalized == "guided":
            _set_study_mode(s, StudyAutonomyMode.GUIDED)
            print_success("Guided review mode is active.")
            return CommandResult()

        session_type = session_type_from_text(requested)
        time_budget = parse_time_budget_minutes(requested)
        _start_autopilot_session(s, session_type, time_budget, requested)
        suffix = f" for {time_budget} minute(s)" if time_budget is not None else ""
        print_success(f"Autopilot {session_type.value} session started{suffix}.")
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
        scope = f"about {topic}" if topic else "from my past exams and materials"
        prompt = (
            f"Ask me one random exam-style question {scope}. Include a concrete time limit, "
            "require me to reason from memory, and do not show the result, answer key, "
            "rubric, source explanation, source IDs, or citations until after my attempt."
        )
        return CommandResult(output=f"__RESEND__:{prompt}")


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


def _set_study_mode(session: ChatSession, mode: StudyAutonomyMode) -> None:
    session.study_state.autonomy_mode = mode
    if mode is not StudyAutonomyMode.AUTOPILOT:
        session.study_state.clear_autopilot_session()
    session.dirty = True


def _start_autopilot_session(
    session: ChatSession,
    session_type: AutopilotSessionType,
    time_budget_minutes: int | None,
    raw_request: str,
) -> None:
    session.study_state.start_autopilot_session(
        session_type=session_type.value,
        session_goal=_autopilot_goal(session_type, raw_request),
        time_budget_minutes=time_budget_minutes,
    )
    session.dirty = True


def _autopilot_goal(session_type: AutopilotSessionType, raw_request: str) -> str:
    if session_type in _AUTOPILOT_GOALS:
        return _AUTOPILOT_GOALS[session_type]
    normalized = raw_request.strip().casefold()
    if normalized in {"", "on", "autopilot"}:
        return "guided material review"
    return raw_request or "guided material review"


def _autopilot_start_prompt(
    session_type: AutopilotSessionType,
    time_budget_minutes: int | None,
) -> str:
    budget = f"I have {time_budget_minutes} minutes. " if time_budget_minutes is not None else ""
    goal = _autopilot_goal(session_type, "")
    return (
        f"Start an autopilot session from my materials using the "
        f"{session_type.value} profile. {budget}"
        f"Use {goal} as the session goal. "
        "Drive the session yourself, start with active recall when appropriate, ask one "
        "diagnostic or review question, require my confidence from 0-100%, and do not "
        "reveal answers before I attempt them."
    )


def _print_mode_status(session: ChatSession) -> None:
    study = session.study_state
    lines: list[str] = [f"Learning mode: {study.autonomy_mode.value}"]
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
