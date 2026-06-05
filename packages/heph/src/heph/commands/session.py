"""Session management commands: status, new, and sessions."""

from __future__ import annotations

from contextlib import suppress
from datetime import UTC, datetime, timedelta
from pathlib import Path

from heph_ai.providers.endpoints import is_keyless_endpoint
from heph_ai.runtime import has_configured_access
from heph_interfaces.terminal import STYLE_DIM, print_error, print_info, print_success, styled
from hephaion.chat import storage as chat_storage
from hephaion.chat.session import (
    ChatSession,
    SessionError,
    create_plain_session,
    create_session,
    save_session,
    session_has_messages,
)
from hephaion.chat.usage import load_usage_summaries
from hephaion.diagnostics.events import capture as capture_analytics
from hephaion.study.schedule import load_recall_schedule
from hephaion.study.state import LearningFeedbackType
from hephaion.vocab.parser import scan_armory
from hephaion.vocab.state import VocabCardState, load_schedule, save_schedule

from heph.commands._base import (
    Command,
    CommandResult,
    ensure_session,
    format_duration,
    pct,
)


def _session_status(session: ChatSession) -> str:
    msg_count = sum(1 for message in session.conversation.messages if message.role != "system")
    user_msgs = sum(1 for message in session.conversation.messages if message.role == "user")
    assistant_msgs = sum(
        1 for message in session.conversation.messages if message.role == "assistant"
    )
    usage_summary = session.usage.summary()
    lines = [
        "Current session:",
        f"  Armory:    {_session_armory_label(session)}",
        f"  Session:   {session.session_id}",
        f"  Title:     {session.title or styled('(untitled)', STYLE_DIM)}",
        f"  Model:     {session.config.model}",
        f"  API:       {session.config.base_url}",
        f"  Key:       {_session_key_status(session)}",
        f"  Mode:      {_session_runtime_label(session)}",
        f"  Runtime:   {format_duration(session.current_run_seconds)}",
        f"  Tools:     {_session_tool_count(session)}",
        f"  Messages:  {msg_count}",
        f"  Turns:     {user_msgs}",
        f"  Assistant: {assistant_msgs} messages",
        f"  Memory:    {_session_memory_count(session)} concepts",
        f"  API calls: {usage_summary['api_calls']}",
        (
            f"  Tokens:    {usage_summary['total_tokens']}"
            f" (prompt: {usage_summary['prompt_tokens']},"
            f" completion: {usage_summary['completion_tokens']})"
        ),
        f"  Cost:      ${usage_summary['cost_usd']:.4f}",
        f"  Dirty:     {'yes' if session.dirty else 'no'}",
    ]
    if session.armory_path is not None:
        lines.extend(_armory_stats(session.armory_path))
        lines.extend(_vocab_stats(session.armory_path))
        lines.extend(_learning_stats(session))
    return "\n".join(lines)


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


def _session_armory_label(session: ChatSession) -> str:
    return str(session.armory_path) if session.armory_path else styled("none", STYLE_DIM)


def _session_key_status(session: ChatSession) -> str:
    if is_keyless_endpoint(session.config.base_url):
        return "not needed (free provider)"
    if has_configured_access(session.config, refresh_oauth=False):
        return "configured"
    return styled("not set", STYLE_DIM)


def _session_runtime_label(session: ChatSession) -> str:
    return "agent (tools)" if session.armory_path else "plain chat"


def _session_tool_count(session: ChatSession) -> int:
    return 7 if session.armory_path else 0


def _session_memory_count(session: ChatSession) -> int:
    return len(session.memory.entries) if session.memory else 0


def _autosave_before_new_chat(session: ChatSession) -> None:
    if not (session.armory_path and session.dirty and session_has_messages(session)):
        return
    with suppress(chat_storage.ChatStorageError):
        save_session(session)


def _create_new_chat(session: ChatSession) -> ChatSession | None:
    _autosave_before_new_chat(session)
    try:
        if session.armory_path is None:
            new_session = create_plain_session(session.config)
        else:
            new_session = create_session(session.config, session.armory_path)
    except SessionError as exc:
        print_error(str(exc))
        return None
    capture_analytics(
        "session_new",
        {
            "mode": "armory" if new_session.armory_path is not None else "plain",
            "model": new_session.config.model,
        },
    )
    print_success("New chat started.")
    return new_session


class StatusCommand(Command):
    name = "status"
    description = "Show session, usage, armory, and review info"

    def handle(self, session: object, args: str) -> CommandResult:
        del args
        s = ensure_session(session)
        return CommandResult(output=_session_status(s))


class StatsCommand(StatusCommand):
    name = "stats"
    description = "Alias for /status with session and armory statistics"

    def handle(self, session: object, args: str) -> CommandResult:
        result = super().handle(session, args)
        if result.output is not None:
            print(result.output)
        return CommandResult()


class NewCommand(Command):
    name = "new"
    description = "Start a new chat"

    def handle(self, session: object, args: str) -> CommandResult:
        del args
        s = ensure_session(session)
        new = _create_new_chat(s)
        return CommandResult(new_session=new)


class ArmoryCommand(Command):
    name = "armory"
    description = "Browse, open, or create armories"

    def handle(self, session: object, args: str) -> CommandResult:
        del session
        subcmd = args.strip().lower()
        if subcmd not in {"", "menu", "manage", "open", "create", "new"}:
            print_error("Usage: /armory [open|create]")
            return CommandResult()
        print_info("Use the /armory browser in the TUI to open or create armories.")
        return CommandResult()


class SessionsCommand(Command):
    name = "sessions"
    description = "Switch between saved sessions"

    def handle(self, session: object, args: str) -> CommandResult:
        del session
        subcmd = args.strip().lower()
        if subcmd not in {"", "list", "recent", "browse", "menu", "resume", "last", "latest"}:
            print_error("Usage: /sessions [list|recent|browse|resume]")
            return CommandResult()
        print_info("Use the /sessions browser in the TUI to list or resume saved chats.")
        return CommandResult()


class TurnCommand(Command):
    name = "turn"
    description = "Branch from an earlier completed turn"

    def handle(self, session: object, args: str) -> CommandResult:
        del session
        subcmd = args.strip().lower()
        known_subcommands = {"list", "history", "browse", "menu", "resume", "last", "latest"}
        if subcmd and subcmd not in known_subcommands and not subcmd.startswith("t"):
            print_error("Usage: /turn [list|browse|T#]")
            return CommandResult()
        print_info("Use the /turn browser in the TUI to branch from an earlier reply.")
        return CommandResult()
