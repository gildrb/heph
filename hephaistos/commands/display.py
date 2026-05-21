from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from hephaistos.chat import storage as chat_storage
from hephaistos.chat.session import ChatSession
from hephaistos.chat.usage import load_usage_summaries
from hephaistos.commands._base import (
    Command,
    CommandResult,
    ensure_session,
    format_duration,
    pct,
)
from hephaistos.rag.context import EvidenceChunk, TurnEvidence
from hephaistos.rag.source_mapping import (
    SourceLineSpan,
    SourceMappingError,
    chunk_line_span,
    evidence_location_label,
    resolve_source_path,
    source_excerpt,
)
from hephaistos.study.schedule import load_recall_schedule
from hephaistos.study.state import LearningFeedbackType
from hephaistos.terminal import print_error, print_info, print_success
from hephaistos.terminal.source_open import open_source_file
from hephaistos.vocab.parser import scan_armory
from hephaistos.vocab.state import VocabCardState, load_schedule, save_schedule

_VISIBILITY_ON = ("show", "on", "yes", "true", "1")
_VISIBILITY_OFF = ("hide", "off", "no", "false", "0")


def _evidence_request(args: str) -> tuple[str | None, bool]:
    tokens = args.strip().split()
    open_requested = any(token.lower() in {"open", "source"} for token in tokens)
    evidence_id = next(
        (evidence_id for token in tokens if (evidence_id := _evidence_id_from_token(token))),
        None,
    )
    return evidence_id, open_requested


def _evidence_id_from_token(token: str) -> str | None:
    cleaned = token.strip("[](),;:").upper()
    if cleaned.startswith("E") and cleaned[1:].isdigit():
        return cleaned
    if cleaned.isdigit():
        return f"E{cleaned}"
    return None


def _item_path_and_span(
    session: ChatSession,
    item: EvidenceChunk,
) -> tuple[Path | None, SourceLineSpan | None]:
    if session.armory_path is None:
        return None, None
    try:
        path = resolve_source_path(session.armory_path, item.source)
    except SourceMappingError:
        return None, None
    return path, chunk_line_span(path, item.chunk)


def _format_evidence_overview(session: ChatSession, items: tuple[EvidenceChunk, ...]) -> str:
    by_source: dict[str, list[EvidenceChunk]] = {}
    for item in items:
        by_source.setdefault(item.source, []).append(item)

    lines = ["Last turn sources:"]
    for source, source_items in by_source.items():
        lines.append(f"{source}")
        for item in source_items:
            path, span = _item_path_and_span(session, item)
            location = evidence_location_label(item.source, item.chunk, span)
            lines.append(f"  {item.evidence_id}  {location}; score={item.score:.3f}")
            if item.chunk.heading:
                lines.append(f"      heading: {item.chunk.heading}")
            preview = " ".join(item.content.split())
            if len(preview) > 160:
                preview = f"{preview[:157]}..."
            if preview:
                lines.append(f"      {preview}")
            lines.append(f"      expand: /evidence {item.evidence_id}")
            if path is not None:
                lines.append(f"      open:   /evidence {item.evidence_id} open")
    lines.append("")
    lines.append("Expand exact source text: /evidence E1")
    lines.append("Open source at line:      /evidence E1 open")
    return "\n".join(lines)


def _format_evidence_detail(session: ChatSession, item: EvidenceChunk) -> str:
    path, span = _item_path_and_span(session, item)
    source = item.source if path is None else str(path)
    location = evidence_location_label(item.source, item.chunk, span)
    lines = [
        f"{item.evidence_id}  {source}",
        f"{location}; score={item.score:.3f}",
    ]
    if item.chunk.heading:
        lines.append(f"heading: {item.chunk.heading}")
    lines += ["", "Source text:"]
    excerpt = source_excerpt(path, item.chunk) if path is not None else ""
    lines.append(excerpt or item.content)
    lines += ["", f"Open source: /evidence {item.evidence_id} open"]
    return "\n".join(lines)


def _open_evidence_item(session: ChatSession, item: EvidenceChunk) -> None:
    if session.armory_path is None:
        print_error("No armory attached; cannot open evidence source.")
        return
    try:
        path = resolve_source_path(session.armory_path, item.source)
    except SourceMappingError as exc:
        print_error(str(exc))
        return
    if not path.exists():
        print_error(f"Evidence source not found: {path}")
        return
    span = chunk_line_span(path, item.chunk)
    line = span.start_line if span is not None else None
    try:
        result = open_source_file(path, line)
    except OSError as exc:
        print_error(str(exc))
        return
    print_success(result.message)


def _update_visibility(session: ChatSession, args: str, attr: str, label: str, usage: str) -> None:
    value = args.strip().lower()
    if value in _VISIBILITY_ON:
        visible = True
    elif value in _VISIBILITY_OFF:
        visible = False
    elif value:
        print_error(usage)
        return
    else:
        visible = not bool(getattr(session, attr))
    setattr(session, attr, visible)
    state = "shown" if visible else "hidden"
    print_success(f"{label} {state}.")


class EvidenceCommand(Command):
    name = "evidence"
    description = "Show retrieved evidence for the last turn"
    aliases = ("sources",)

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        evidence = s.last_turn_evidence
        if evidence is None or not evidence.items:
            print_info("No evidence was retrieved for the last turn.")
            return CommandResult()

        evidence_id, open_requested = _evidence_request(args)
        if evidence_id is not None:
            return _handle_evidence_item(s, evidence, evidence_id, open_requested)

        if open_requested:
            print_error("Usage: /evidence <EID> open")
            return CommandResult()

        print(_format_evidence_overview(s, evidence.items))
        return CommandResult()


def _handle_evidence_item(
    session: ChatSession,
    evidence: TurnEvidence,
    evidence_id: str,
    open_requested: bool,
) -> CommandResult:
    item = evidence.get(evidence_id)
    if item is None:
        print_error(f"Unknown evidence ID: {evidence_id}")
        return CommandResult()
    if open_requested:
        _open_evidence_item(session, item)
    else:
        print(_format_evidence_detail(session, item))
    return CommandResult()


class TokensCommand(Command):
    name = "tokens"
    description = "Show or hide live token estimates"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        _update_visibility(
            s, args, "live_tokens_visible", "Live tokens", "Usage: /tokens [show|hide]"
        )
        return CommandResult()


class CostCommand(Command):
    name = "cost"
    description = "Show or hide live cost estimates"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        _update_visibility(s, args, "live_cost_visible", "Live cost", "Usage: /cost [show|hide]")
        return CommandResult()


class StatsCommand(Command):
    name = "stats"
    description = "Show session, armory, and review stats"

    def handle(self, session: object, args: str) -> CommandResult:
        del args
        s = ensure_session(session)
        user_msgs = sum(1 for message in s.conversation.messages if message.role == "user")
        assistant_msgs = sum(
            1 for message in s.conversation.messages if message.role == "assistant"
        )
        usage = s.usage.summary()
        lines = [
            "Current session:",
            f"  Session:    {s.session_id}",
            f"  Runtime:    {format_duration(s.current_run_seconds)}",
            f"  Turns:      {user_msgs}",
            f"  Assistant:  {assistant_msgs} messages",
            f"  API calls:  {usage['api_calls']}",
            f"  Tokens:     {usage['total_tokens']}",
            f"  Cost:       ${usage['cost_usd']:.4f}",
        ]
        if s.armory_path is not None:
            lines.extend(_armory_stats(s.armory_path))
            lines.extend(_vocab_stats(s.armory_path))
            lines.extend(_learning_stats(s))
        print("\n".join(lines))
        return CommandResult()


def _armory_stats(armory_path: Path) -> list[str]:
    usage_summaries = load_usage_summaries(armory_path)
    return [
        "",
        "Armory:",
        f"  Path:       {armory_path}",
        f"  Saved:      {len(chat_storage.list_sessions(armory_path))} sessions",
        f"  API calls:  {sum(int(item['api_calls']) for item in usage_summaries)}",
        f"  Tokens:     {sum(int(item['total_tokens']) for item in usage_summaries)}",
        f"  Cost:       ${sum(float(item['cost_usd']) for item in usage_summaries):.4f}",
    ]


def _vocab_stats(armory_path: Path) -> list[str]:
    deck = scan_armory(armory_path)
    store = load_schedule(armory_path)
    store.sync_with_deck(deck)
    save_schedule(store)
    stats = store.stats()
    if stats["total"] == 0:
        return ["", "Vocabulary:", "  No vocabulary cards yet. Add Q&A pairs to your materials."]
    return _reviewed_vocab_stats(store.card_list, stats)


def _reviewed_vocab_stats(cards: list[VocabCardState], stats: dict[str, int]) -> list[str]:
    reviewed = [card for card in cards if not card.is_new]
    lines = [
        "",
        "Vocabulary:",
        f"  Total cards:  {stats['total']}",
        f"  New:          {stats['new']}",
        f"  Due now:      {stats['due']}",
        f"  Mastered:     {stats['mastered']} ({pct(stats['mastered'], stats['total'])})",
    ]
    if reviewed:
        avg_easiness = sum(card.easiness for card in reviewed) / len(reviewed)
        lines.append(f"  Avg easiness: {avg_easiness:.2f}")
    lines.extend(_vocab_due_lines(cards))
    return lines


def _vocab_due_lines(cards: list[VocabCardState]) -> list[str]:
    now = datetime.now(UTC)
    due_tomorrow = _due_vocab_count(cards, now + timedelta(days=1))
    due_this_week = _due_vocab_count(cards, now + timedelta(days=7))
    return [f"  Due tomorrow: {due_tomorrow}", f"  Due this week: {due_this_week}"]


def _due_vocab_count(cards: list[VocabCardState], deadline: datetime) -> int:
    return sum(
        1 for card in cards if card.next_review is not None and card.next_review <= deadline
    )


def _learning_stats(session: ChatSession) -> list[str]:
    learning = session.learning_state
    if learning.last_feedback_type == LearningFeedbackType.NONE:
        return []
    lines = [
        "",
        "Learning state:",
        f"  Phase:     {learning.phase.value}",
        *_learning_optional_lines(session),
        f"  Feedback:  {learning.last_feedback_type.value}",
    ]
    lines.extend(_learning_schedule_lines(session))
    return lines


def _learning_optional_lines(session: ChatSession) -> list[str]:
    learning = session.learning_state
    lines: list[str] = []
    if learning.time_budget_minutes is not None:
        lines.append(f"  Budget:    {learning.time_budget_minutes}m")
    if learning.current_item:
        lines.append(f"  Item:      {learning.current_item[:60]}")
    if learning.attempt_count > 0:
        lines.append(f"  Attempts:  {learning.attempt_count}")
    if learning.hint_level > 0:
        lines.append(f"  Hint lvl:  {learning.hint_level}")
    if learning.last_recall_seconds is not None:
        lines.append(f"  Recall:    {format_duration(learning.last_recall_seconds)}")
    if learning.last_recall_rating.value != "none":
        lines.append(f"  Effort:    {learning.last_recall_rating.value}")
    return lines


def _learning_schedule_lines(session: ChatSession) -> list[str]:
    if session.armory_path is None:
        return []
    store = load_recall_schedule(session.armory_path)
    if not store.item_list:
        return []
    now = datetime.now(UTC)
    due = sum(
        1 for item in store.item_list if item.next_review is not None and item.next_review <= now
    )
    lines = [f"  Scheduled: {len(store.item_list)} item(s), {due} due"]
    if store.policy_stats:
        best_move, stats = max(
            store.policy_stats.items(),
            key=lambda item: (item[1].success_rate, item[1].avg_mastery_delta),
        )
        lines.append(f"  Best move: {best_move} ({stats.success_rate:.0%} success)")
    return lines


class UsageCommand(Command):
    name = "usage"
    description = "Show token usage and cost for this session"

    def handle(self, session: object, args: str) -> CommandResult:
        del args
        s = ensure_session(session)
        summary = s.usage.summary()
        lines = [
            f"  API calls:     {summary['api_calls']}",
            f"  Prompt tokens: {summary['prompt_tokens']}",
            f"  Output tokens: {summary['completion_tokens']}",
            f"  Total tokens:  {summary['total_tokens']}",
            f"  Estimated cost: ${summary['cost_usd']:.4f}",
        ]
        print("\n".join(lines))
        return CommandResult()
