"""Display and statistics commands: history, evidence, tokens, cost, stats, usage."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from hephaistos.app.commands._base import (
    Command,
    CommandResult,
    ensure_session,
    format_duration,
    pct,
)
from hephaistos.app.display import print_error, print_info, print_success
from hephaistos.app.workspace import list_saved_chats, resume_saved_chat
from hephaistos.chat import storage as chat_storage
from hephaistos.chat.session import ChatSession
from hephaistos.chat.usage import load_usage_summaries
from hephaistos.study.state import StudyFeedbackType
from hephaistos.vocab.parser import scan_armory
from hephaistos.vocab.state import load_schedule, save_schedule


class HistoryCommand(Command):
    name = "history"
    description = "List or resume saved study chats"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        subcmd = args.strip()
        normalized = subcmd.lower()
        if normalized in ("stats", "current"):
            self._print_current_chat_stats(s)
            return CommandResult()
        if s.armory_path is None:
            print_info("Attach an armory to view saved chat history.")
            return CommandResult()
        if normalized in ("", "list", "recent"):
            list_saved_chats(s)
            return CommandResult()
        if normalized in ("browse", "menu"):
            return CommandResult(new_session=resume_saved_chat(s, "browse"))
        if normalized in ("resume", "last", "latest"):
            return CommandResult(new_session=resume_saved_chat(s, "latest"))
        return CommandResult(new_session=resume_saved_chat(s, subcmd))

    def _print_current_chat_stats(self, session: ChatSession) -> None:
        user_msgs = [m for m in session.conversation.messages if m.role == "user"]
        asst_msgs = [m for m in session.conversation.messages if m.role == "assistant"]
        tool_msgs = [m for m in session.conversation.messages if m.role == "tool"]
        total_chars = sum(len(m.content) for m in session.conversation.messages)
        est_tokens = total_chars // 4
        usage_summary = session.usage.summary()
        lines = [
            f"  Turns:     {len(user_msgs)}",
            f"  User:      {len(user_msgs)} messages",
            f"  Assistant: {len(asst_msgs)} messages",
        ]
        if tool_msgs:
            lines.append(f"  Tool:      {len(tool_msgs)} results")
        mem_count = len(session.memory.entries) if session.memory else 0
        lines.extend(
            [
                f"  Memory:    {mem_count} concepts learned",
                f"  Chars:     {total_chars}",
                f"  ~Tokens:   ~{est_tokens}",
                f"  Max tokens: {session.config.max_tokens}",
                "",
                f"  API calls: {usage_summary['api_calls']}",
                f"  Tokens:    {usage_summary['total_tokens']}",
                f"  Cost:      ${usage_summary['cost_usd']:.4f}",
            ]
        )
        print("\n".join(lines))


class EvidenceCommand(Command):
    name = "evidence"
    description = "Show retrieved evidence for the last turn"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        evidence = s.last_turn_evidence
        if evidence is None or not evidence.items:
            print_info("No evidence was retrieved for the last turn.")
            return CommandResult()
        lines = ["Last turn evidence:"]
        for item in evidence.items:
            preview = " ".join(item.content.split())
            if len(preview) > 120:
                preview = f"{preview[:117]}..."
            lines.append(
                f"  {item.evidence_id}  {item.source}#chunk={item.chunk_index}"
                f"  score={item.score:.3f}"
            )
            if preview:
                lines.append(f"      {preview}")
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
