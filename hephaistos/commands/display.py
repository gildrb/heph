"""Display and statistics commands: evidence, tokens, cost, stats, usage."""

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
from hephaistos.rag.context import EvidenceChunk
from hephaistos.rag.source_mapping import (
    SourceLineSpan,
    SourceMappingError,
    chunk_line_span,
    line_label,
    resolve_source_path,
    source_excerpt,
)
from hephaistos.study.state import StudyFeedbackType
from hephaistos.terminal.display import print_error, print_info, print_success
from hephaistos.terminal.source_open import open_source_file
from hephaistos.vocab.parser import scan_armory
from hephaistos.vocab.state import load_schedule, save_schedule


def _parse_evidence_args(args: str) -> tuple[str | None, bool]:
    tokens = args.strip().split()
    if not tokens:
        return None, False
    open_requested = any(token.lower() in {"open", "source"} for token in tokens)
    for token in tokens:
        cleaned = token.strip("[](),;:").upper()
        if cleaned.startswith("E") and cleaned[1:].isdigit():
            return cleaned, open_requested
        if cleaned.isdigit():
            return f"E{cleaned}", open_requested
    return None, open_requested


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


def _preview(content: str, max_chars: int = 160) -> str:
    preview = " ".join(content.split())
    if len(preview) <= max_chars:
        return preview
    return f"{preview[: max_chars - 3]}..."


def _format_evidence_summary(session: ChatSession, item: EvidenceChunk) -> list[str]:
    path, span = _item_path_and_span(session, item)
    location = line_label(span)
    source = item.source if path is None else str(path)
    details = [
        f"  {item.evidence_id}  {source}#chunk={item.chunk_index}",
        f"      {location}; chars {item.chunk.char_start}-{item.chunk.char_end}; "
        f"score={item.score:.3f}",
    ]
    if item.chunk.heading:
        details.append(f"      heading: {item.chunk.heading}")
    preview = _preview(item.content)
    if preview:
        details.append(f"      {preview}")
    return details


def _format_evidence_detail(session: ChatSession, item: EvidenceChunk) -> str:
    path, span = _item_path_and_span(session, item)
    source = item.source if path is None else str(path)
    lines = [
        f"{item.evidence_id}  {source}#chunk={item.chunk_index}",
        f"{line_label(span)}; chars {item.chunk.char_start}-{item.chunk.char_end}; "
        f"score={item.score:.3f}",
    ]
    if item.chunk.heading:
        lines.append(f"heading: {item.chunk.heading}")
    lines.append("")
    if path is not None:
        excerpt = source_excerpt(path, item.chunk)
        if excerpt:
            lines.append(excerpt)
        else:
            lines.append(item.content)
    else:
        lines.append(item.content)
    lines.append("")
    lines.append(f"Open source: /evidence {item.evidence_id} open")
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

        evidence_id, open_requested = _parse_evidence_args(args)
        if evidence_id is not None:
            item = evidence.get(evidence_id)
            if item is None:
                print_error(f"Unknown evidence ID: {evidence_id}")
                return CommandResult()
            if open_requested:
                _open_evidence_item(s, item)
            else:
                print(_format_evidence_detail(s, item))
            return CommandResult()

        if open_requested:
            print_error("Usage: /evidence <EID> open")
            return CommandResult()

        lines = ["Last turn evidence:"]
        for item in evidence.items:
            lines.extend(_format_evidence_summary(s, item))
        lines.append("")
        lines.append("Show context: /evidence E1")
        lines.append("Open source:  /evidence E1 open")
        print("\n".join(lines))
        return CommandResult()


class TokensCommand(Command):
    name = "tokens"
    description = "Show or hide live token estimates"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        value = args.strip().lower()
        if value in ("show", "on", "yes", "true", "1"):
            s.live_tokens_visible = True
        elif value in ("hide", "off", "no", "false", "0"):
            s.live_tokens_visible = False
        elif value:
            print_error("Usage: /tokens [show|hide]")
            return CommandResult()
        else:
            s.live_tokens_visible = not s.live_tokens_visible
        state = "shown" if s.live_tokens_visible else "hidden"
        print_success(f"Live tokens {state}.")
        return CommandResult()


class CostCommand(Command):
    name = "cost"
    description = "Show or hide live cost estimates"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        value = args.strip().lower()
        if value in ("show", "on", "yes", "true", "1"):
            s.live_cost_visible = True
        elif value in ("hide", "off", "no", "false", "0"):
            s.live_cost_visible = False
        elif value:
            print_error("Usage: /cost [show|hide]")
            return CommandResult()
        else:
            s.live_cost_visible = not s.live_cost_visible
        state = "shown" if s.live_cost_visible else "hidden"
        print_success(f"Live cost {state}.")
        return CommandResult()


class StatsCommand(Command):
    name = "stats"
    description = "Show session, armory, and study progress stats"

    def handle(self, session: object, args: str) -> CommandResult:
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
            sessions = chat_storage.list_sessions(s.armory_path)
            usage_summaries = load_usage_summaries(s.armory_path)
            total_calls = sum(int(item["api_calls"]) for item in usage_summaries)
            total_tokens = sum(int(item["total_tokens"]) for item in usage_summaries)
            total_cost = sum(float(item["cost_usd"]) for item in usage_summaries)
            lines.extend(
                [
                    "",
                    "Armory:",
                    f"  Path:       {s.armory_path}",
                    f"  Saved:      {len(sessions)} sessions",
                    f"  API calls:  {total_calls}",
                    f"  Tokens:     {total_tokens}",
                    f"  Cost:       ${total_cost:.4f}",
                ]
            )
            lines.extend(self._vocab_stats(s.armory_path))
            lines.extend(self._study_stats(s))
        print("\n".join(lines))
        return CommandResult()

    @staticmethod
    def _vocab_stats(armory_path: Path) -> list[str]:
        """Return vocabulary scheduling statistics for the armory."""
        deck = scan_armory(armory_path)
        store = load_schedule(armory_path)
        store.sync_with_deck(deck)
        save_schedule(store)
        stats = store.stats()

        if stats["total"] == 0:
            return [
                "",
                "Vocabulary:",
                "  No vocab cards yet. Add Q&A pairs to your materials.",
            ]

        cards = store.card_list
        reviewed = [card for card in cards if not card.is_new]
        avg_easiness = sum(card.easiness for card in reviewed) / len(reviewed) if reviewed else 0.0

        lines = [
            "",
            "Vocabulary:",
            f"  Total cards:  {stats['total']}",
            f"  New:          {stats['new']}",
            f"  Due now:      {stats['due']}",
            f"  Mastered:     {stats['mastered']} ({pct(stats['mastered'], stats['total'])})",
        ]
        if reviewed:
            lines.append(f"  Avg easiness: {avg_easiness:.2f}")

        now = datetime.now(UTC)
        week_ahead = now + timedelta(days=7)
        due_this_week = sum(
            1 for card in cards if card.next_review is not None and card.next_review <= week_ahead
        )
        due_tomorrow = sum(
            1
            for card in cards
            if card.next_review is not None and card.next_review <= now + timedelta(days=1)
        )
        lines.append(f"  Due tomorrow: {due_tomorrow}")
        lines.append(f"  Due this week: {due_this_week}")
        return lines

    @staticmethod
    def _study_stats(session: ChatSession) -> list[str]:
        """Return study mode feedback from the current session state."""
        study = session.study_state
        if study.last_feedback_type == StudyFeedbackType.NONE:
            return []
        lines = [
            "",
            "Study mode:",
            f"  Phase:     {study.phase.value}",
        ]
        if study.current_item:
            lines.append(f"  Item:      {study.current_item[:60]}")
        if study.attempt_count > 0:
            lines.append(f"  Attempts:  {study.attempt_count}")
        lines.append(f"  Feedback:  {study.last_feedback_type.value}")
        return lines


class UsageCommand(Command):
    name = "usage"
    description = "Show token usage and cost for this session"

    def handle(self, session: object, args: str) -> CommandResult:
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
