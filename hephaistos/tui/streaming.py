"""Streaming turn adapter helpers.

Named after Codex's focused TUI streaming modules: chat/session workflow stays in
`chat`, while this adapter converts chat events into UI callbacks.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from threading import Event
from typing import TYPE_CHECKING

from hephaistos.chat.automation import iter_chat_events
from hephaistos.chat.events import (
    AssistantDeltaEvent,
    MaterialOperationEvent,
    NoticeEvent,
    ToolCallEvent,
    ToolResultEvent,
    TurnCompleteEvent,
)
from hephaistos.parameters.settings import (
    ACTIVITY_TRACE_HIDDEN_TOOL_CALLS,
    ACTIVITY_TRACE_MINIMAL_TOOL_CALLS,
    ACTIVITY_TRACE_TOOL_CALLS,
    load_app_settings,
)
from hephaistos.runtime import (
    EngineError,
    StreamRecoveryError,
    is_network_error,
    offline_message,
)

if TYPE_CHECKING:
    from hephaistos.chat.session import ChatSession

_MAX_PROGRESS_TEXT = 64
_MAX_SUMMARY_TEXT = 160
_MAX_ACTIVITY_TEXT = 180
_ACTIVITY_TRACE_INDENT = "    "


def _clean_text(text: str) -> str:
    return " ".join(text.split())


def _truncate(text: str, limit: int) -> str:
    clean = _clean_text(text)
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "…"


def _metadata_int(metadata: Mapping[str, object], key: str) -> int | None:
    value = metadata.get(key)
    if isinstance(value, int):
        return value
    return None


def _metadata_number(metadata: Mapping[str, object], key: str) -> float | None:
    value = metadata.get(key)
    if isinstance(value, int | float):
        return float(value)
    return None


def _metadata_str(metadata: Mapping[str, object], key: str) -> str | None:
    value = metadata.get(key)
    if isinstance(value, str):
        return value
    return None


def _metadata_str_list(metadata: Mapping[str, object], key: str) -> list[str]:
    value = metadata.get(key)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _plural(count: int, singular: str, plural: str | None = None) -> str:
    word = singular if count == 1 else (plural or f"{singular}s")
    return f"{count} {word}"


def _compact_tool_call(event: ToolCallEvent) -> str:
    if event.name == "bash":
        command = _metadata_str(event.arguments, "command")
        if command:
            return f"bash `{_truncate(command, 72)}`"
    if event.name in {"read_file", "write_file", "edit_file"}:
        path = _metadata_str(event.arguments, "path")
        if path:
            return f"{event.name} {_truncate(path, 72)}"
    if event.name == "search_materials":
        query = _metadata_str(event.arguments, "query")
        if query:
            return f"search_materials `{_truncate(query, 72)}`"
    if event.name == "open_material":
        source = _metadata_str(event.arguments, "source")
        if source:
            return f"open_material {_truncate(source, 72)}"
    return event.name


def _activity_line(
    event: ToolCallEvent | ToolResultEvent | MaterialOperationEvent | NoticeEvent,
) -> str | None:
    if isinstance(event, ToolCallEvent):
        return f"{_ACTIVITY_TRACE_INDENT}Ran {_compact_tool_call(event)}"
    if isinstance(event, ToolResultEvent):
        latency = _metadata_number(event.metadata, "latency_ms")
        elapsed = f" in {latency:.0f}ms" if latency is not None else ""
        if not event.success:
            error = event.error or event.summary or "tool failed"
            return (
                f"{_ACTIVITY_TRACE_INDENT}! {event.name} failed{elapsed}: "
                f"{_truncate(error, _MAX_ACTIVITY_TEXT)}"
            )
        summary = _clean_text(event.summary) or _clean_text(event.content)
        if summary:
            prefix = f"{event.name} finished{elapsed}: " if latency is not None else ""
            return f"{_ACTIVITY_TRACE_INDENT}-> {prefix}{_truncate(summary, _MAX_ACTIVITY_TEXT)}"
        return f"{_ACTIVITY_TRACE_INDENT}-> {event.name} finished{elapsed}"
    if isinstance(event, MaterialOperationEvent):
        return f"{_ACTIVITY_TRACE_INDENT}{_truncate(event.message, _MAX_ACTIVITY_TEXT)}"
    if event.code in {
        "reading",
        "writing",
        "evidence",
        "model_request",
        "model_delta",
        "model_complete",
        "verification",
        "context_warning",
        "tool_runtime",
        "auto_compact",
        "manual_compact",
        "max_turns",
        "dry_run",
    }:
        return f"{_ACTIVITY_TRACE_INDENT}{_truncate(event.message, _MAX_ACTIVITY_TEXT)}"
    return None


def _progress_text(
    event: ToolCallEvent | ToolResultEvent | MaterialOperationEvent | NoticeEvent,
) -> str:
    if isinstance(event, ToolCallEvent):
        return f"tool {event.name}"
    if isinstance(event, ToolResultEvent):
        return f"tool {event.name} {'failed' if not event.success else 'done'}"
    if isinstance(event, MaterialOperationEvent):
        labels = {
            "index_ready": "material index ready",
            "sample_overview": "sampling materials",
            "open_stored_evidence": "opening recall evidence",
            "search_index": "searching materials",
            "read_excerpt": "reading evidence",
            "search_result": "search complete",
            "read_all_scope": "checking read scope",
        }
        return labels.get(event.operation, "working with materials")
    notice_labels = {
        "reading": "reading materials",
        "evidence": "checking evidence",
        "writing": "writing response",
        "verification": "checking citations",
        "auto_compact": "compacting context",
        "manual_compact": "compacting context",
        "context_warning": "checking context",
        "tool_runtime": "checking tool result",
    }
    return notice_labels.get(event.code, _truncate(event.message, _MAX_PROGRESS_TEXT))


@dataclass(slots=True)
class _TurnActivitySummary:
    indexed_sources: int | None = None
    indexed_chunks: int | None = None
    evidence_blocks: int | None = None
    sampled_sources: int | None = None
    total_sources: int | None = None
    searched_query: str | None = None
    opened_refs: list[str] = field(default_factory=list)
    no_material_matches: bool = False
    read_all_scope: bool = False
    tool_calls: list[str] = field(default_factory=list)
    tool_failures: list[str] = field(default_factory=list)
    tool_result_count: int = 0
    important_notices: list[str] = field(default_factory=list)
    fallback_notices: list[str] = field(default_factory=list)

    def record(
        self,
        event: ToolCallEvent | ToolResultEvent | MaterialOperationEvent | NoticeEvent,
    ) -> None:
        if isinstance(event, ToolCallEvent):
            self.tool_calls.append(_compact_tool_call(event))
            return
        if isinstance(event, ToolResultEvent):
            self.tool_result_count += 1
            if not event.success:
                error = event.error or "tool failed"
                self.tool_failures.append(f"{event.name}: {_truncate(error, 90)}")
            return
        if isinstance(event, MaterialOperationEvent):
            self._record_material_operation(event)
            return
        self._record_notice(event)

    def lines(self) -> list[str]:
        lines = []
        if material := self._material_line():
            lines.append(material)
        if tools := self._tool_line():
            lines.append(tools)
        notices = self.important_notices or ([] if lines else self.fallback_notices)
        lines.extend(_truncate(notice, _MAX_SUMMARY_TEXT) for notice in notices[:2])
        if len(notices) > 2:
            lines.append(f"{len(notices) - 2} more notices kept in the trace.")
        return lines

    def _record_material_operation(self, event: MaterialOperationEvent) -> None:
        metadata = event.metadata
        if event.operation == "index_ready":
            self.indexed_sources = _metadata_int(metadata, "indexed_sources")
            self.indexed_chunks = _metadata_int(metadata, "indexed_chunks")
            return
        if event.operation == "sample_overview":
            self.evidence_blocks = _metadata_int(metadata, "evidence_blocks")
            self.sampled_sources = _metadata_int(metadata, "sampled_sources")
            self.total_sources = _metadata_int(metadata, "total_sources")
            self.searched_query = _metadata_str(metadata, "query")
            return
        if event.operation in {"search_index", "search_result"}:
            self.searched_query = _metadata_str(metadata, "query")
            self.no_material_matches = event.operation == "search_result"
            return
        if event.operation == "open_stored_evidence":
            self.opened_refs.extend(_metadata_str_list(metadata, "refs"))
            return
        if event.operation == "read_excerpt":
            if ref := _metadata_str(metadata, "ref"):
                self.opened_refs.append(ref)
            return
        if event.operation == "read_all_scope":
            self.read_all_scope = True

    def _record_notice(self, event: NoticeEvent) -> None:
        if event.code == "evidence":
            self._record_evidence_notice(event.metadata)
            return
        if event.code in {"reading", "writing"}:
            return
        clean = _clean_text(event.message)
        if not clean:
            return
        if event.code in {
            "verification",
            "context_warning",
            "tool_runtime",
            "max_turns",
            "dry_run",
            "auto_compact",
            "manual_compact",
            "steering",
        }:
            self.important_notices.append(clean)
            return
        self.fallback_notices.append(clean)

    def _record_evidence_notice(self, metadata: dict[str, object]) -> None:
        coverage = metadata.get("coverage")
        if isinstance(coverage, dict):
            coverage_metadata = {
                key: value for key, value in coverage.items() if isinstance(key, str)
            }
            evidence_blocks = _metadata_int(coverage_metadata, "evidence_blocks")
            sampled_sources = _metadata_int(coverage_metadata, "sampled_sources")
            total_sources = _metadata_int(coverage_metadata, "total_sources")
            self.evidence_blocks = evidence_blocks or self.evidence_blocks
            self.sampled_sources = sampled_sources or self.sampled_sources
            self.total_sources = total_sources or self.total_sources
        refs = _metadata_str_list(metadata, "refs")
        if refs:
            self.opened_refs.extend(ref for ref in refs if ref not in self.opened_refs)

    def _material_line(self) -> str:
        parts: list[str] = []
        if self.indexed_sources is not None and self.indexed_chunks is not None:
            parts.append(
                f"index {_plural(self.indexed_sources, 'source')} / "
                f"{_plural(self.indexed_chunks, 'chunk')}"
            )
        if self.no_material_matches:
            searched = self._searched_fragment()
            if searched:
                parts.append(f"{searched}; no matching evidence")
            else:
                parts.append("no matching evidence")
        elif self.evidence_blocks is not None:
            detail = f"using {_plural(self.evidence_blocks, 'evidence excerpt')}"
            if self.sampled_sources is not None and self.total_sources is not None:
                if self.total_sources > self.sampled_sources:
                    detail += f" from {self.sampled_sources} of {self.total_sources} sources"
                else:
                    detail += f" from {_plural(self.sampled_sources, 'source')}"
            parts.append(detail)
        elif self.opened_refs:
            parts.append(f"opened {_plural(len(set(self.opened_refs)), 'evidence excerpt')}")
        elif self.searched_query:
            parts.append(self._searched_fragment())
        if self.read_all_scope:
            parts.append("sampled indexed evidence, not every file end to end")
        if not parts:
            return ""
        suffix = " Details: /evidence" if self.evidence_blocks or self.opened_refs else ""
        return f"materials: {'; '.join(parts)}.{suffix}"

    def _searched_fragment(self) -> str:
        if not self.searched_query:
            return ""
        return f"searched `{_truncate(self.searched_query, 80)}`"

    def _tool_line(self) -> str:
        if not self.tool_calls and not self.tool_failures:
            return ""
        if len(self.tool_calls) == 1:
            line = f"tool: {self.tool_calls[0]}"
        else:
            shown = ", ".join(self.tool_calls[:3])
            if len(self.tool_calls) > 3:
                shown += f", +{len(self.tool_calls) - 3} more"
            line = f"tools: {len(self.tool_calls)} calls ({shown})"
        if self.tool_failures:
            shown_failures = "; ".join(self.tool_failures[:2])
            line += f"; failed {shown_failures}"
        elif self.tool_result_count:
            line += "; results summarized"
        return f"{line}."


def run_tui_turn(
    session: ChatSession,
    user_input: str,
    abort_event: Event,
    *,
    on_reply: Callable[[str], None],
    on_notice: Callable[[str], None],
    on_error: Callable[[str], None],
    on_finish: Callable[[], None],
    on_progress: Callable[[str], None] | None = None,
    on_activity: Callable[[str], None] | None = None,
) -> None:
    """Run one chat turn and report UI-ready events through callbacks."""
    parts: list[str] = []
    completed_reply: str | None = None
    activity = _TurnActivitySummary()
    activity_trace_mode = load_app_settings().activity_trace_mode
    show_full_activity = activity_trace_mode == ACTIVITY_TRACE_TOOL_CALLS
    show_minimal_activity = activity_trace_mode == ACTIVITY_TRACE_MINIMAL_TOOL_CALLS
    show_activity = activity_trace_mode != ACTIVITY_TRACE_HIDDEN_TOOL_CALLS

    def report_activity() -> None:
        if not show_activity:
            return
        if not show_minimal_activity and on_activity is not None:
            return
        if summary_lines := activity.lines():
            on_notice("\n".join(summary_lines))

    try:
        for event in iter_chat_events(session, user_input, abort=abort_event):
            if isinstance(event, AssistantDeltaEvent):
                parts.append(event.delta)
            elif isinstance(event, TurnCompleteEvent):
                completed_reply = event.full_text
            elif isinstance(
                event,
                ToolCallEvent | ToolResultEvent | MaterialOperationEvent | NoticeEvent,
            ):
                if show_activity:
                    activity.record(event)
                if show_activity and on_progress is not None:
                    on_progress(_truncate(_progress_text(event), _MAX_PROGRESS_TEXT))
                if show_full_activity and on_activity is not None:
                    line = _activity_line(event)
                    if line:
                        on_activity(line)
        report_activity()
        reply = (completed_reply if completed_reply is not None else "".join(parts)).strip()
        if not reply and parts:
            reply = "".join(parts).strip()
        if reply:
            on_reply(reply)
    except (StreamRecoveryError, EngineError) as exc:
        report_activity()
        provider = session.config.provider_slug or "the provider"
        if is_network_error(exc):
            on_notice(offline_message(provider))
        else:
            on_error(str(exc))
    finally:
        on_finish()
