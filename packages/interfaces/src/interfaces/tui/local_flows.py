from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, ParamSpec, Protocol, TypeVar

from ai.providers import llama_cpp
from ai.providers.llama_cpp import (
    LLAMA_CPP_PROVIDER_SLUG,
    LlamaCppCandidate,
    LlamaCppModelRecord,
    ToolCapabilityResult,
)
from hephaion.chat.model_selection import switch_model

from interfaces.tui.flow_state import InlineFlow

try:
    from textual.widgets import Input
except ImportError:
    Input = None  # ty:ignore[invalid-assignment]

if TYPE_CHECKING:
    from hephaion.chat.session import ChatSession

_P = ParamSpec("_P")
_WidgetT = TypeVar("_WidgetT")

_LOCAL_SEARCH_LIMIT = 30


class _LocalFlowHost(Protocol):
    session: ChatSession
    _inline_flow: InlineFlow
    _local_flow_candidates: dict[str, LlamaCppCandidate]

    def query_one(self, selector: str, expect_type: type[_WidgetT]) -> _WidgetT: ...

    def run_worker(self, work: Callable[[], object], *, thread: bool = False) -> object: ...

    def call_from_thread(
        self,
        callback: Callable[_P, object],
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> object: ...

    def _append_notice(self, text: str) -> None: ...

    def _append_error(self, text: str) -> None: ...

    def _refresh_status(self) -> None: ...

    def _update_info_panel(self) -> None: ...

    def _filter_inline_menu_options(self, query: str) -> None: ...

    def _open_inline_menu(
        self,
        *,
        name: str,
        step: str,
        title: str,
        options: list[tuple[str, str]],
        prompts: dict[str, str] | None = None,
        selected_label: str | None = None,
    ) -> None: ...

    def _close_inline_flow(self, notice: str = "") -> None: ...

    def _open_local_flow(self, query: str = "") -> None: ...

    def _refresh_local_flow_worker(self, query: str) -> None: ...

    def _refresh_local_flow_options(self, candidates: list[LlamaCppCandidate]) -> None: ...

    def _local_flow_search_failed(self, message: str) -> None: ...

    def _handle_local_choice(self, label: str) -> None: ...

    def _activate_local_model_worker(self, model_id: str) -> None: ...

    def _install_local_candidate_worker(self, candidate: LlamaCppCandidate) -> None: ...

    def _revalidate_local_model_worker(self, model_id: str) -> None: ...

    def _local_model_activated(self, model_id: str) -> None: ...

    def _local_model_failed(self, message: str) -> None: ...


class TuiLocalFlowMixin:
    def _open_local_flow(self: _LocalFlowHost, query: str = "") -> None:
        search_query = query.strip()
        self._local_flow_candidates = {}
        options = _local_flow_options(
            llama_cpp.installed_records(),
            [],
            current_model=self.session.config.model,
        )
        self._open_inline_menu(
            name="local",
            step="menu",
            title=f"Local models  current: {self.session.config.model}",
            options=options,
        )
        self._inline_flow.slug = search_query
        self._append_notice("Searching public non-gated GGUF models...")
        self.run_worker(lambda: self._refresh_local_flow_worker(search_query), thread=True)

    def _refresh_local_flow_worker(self: _LocalFlowHost, query: str) -> None:
        try:
            candidates = llama_cpp.search_gguf_models(query, limit=_LOCAL_SEARCH_LIMIT)
        except Exception as exc:
            self.call_from_thread(self._local_flow_search_failed, str(exc))
            return
        self.call_from_thread(self._refresh_local_flow_options, candidates)

    def _refresh_local_flow_options(
        self: _LocalFlowHost,
        candidates: list[LlamaCppCandidate],
    ) -> None:
        if not self._inline_flow.active or self._inline_flow.name != "local":
            return
        self._local_flow_candidates = {candidate.model_id: candidate for candidate in candidates}
        self._inline_flow.all_options = _local_flow_options(
            llama_cpp.installed_records(),
            candidates,
            current_model=self.session.config.model,
        )
        composer = self.query_one("#composer", Input)
        self._filter_inline_menu_options(composer.value)

    def _local_flow_search_failed(self: _LocalFlowHost, message: str) -> None:
        if not self._inline_flow.active or self._inline_flow.name != "local":
            return
        self._append_error(f"Could not search Hugging Face GGUF models: {message}")

    def _handle_local_choice(self: _LocalFlowHost, label: str) -> None:
        record = llama_cpp.model_record(label)
        if record is not None:
            self._close_inline_flow(_local_record_action_notice(record))
            if record.tool_capable:
                self.run_worker(
                    lambda: self._activate_local_model_worker(record.model_id),
                    thread=True,
                )
                return
            self.run_worker(
                lambda: self._revalidate_local_model_worker(record.model_id),
                thread=True,
            )
            return

        candidate = self._local_flow_candidates.get(label)
        if candidate is None:
            self._close_inline_flow("Local model not found.")
            return
        self._close_inline_flow(f"installing local model: {candidate.model_id}")
        self.run_worker(lambda: self._install_local_candidate_worker(candidate), thread=True)

    def _activate_local_model_worker(self: _LocalFlowHost, model_id: str) -> None:
        if not switch_model(self.session, LLAMA_CPP_PROVIDER_SLUG, model_id):
            self.call_from_thread(self._local_model_failed, "Local model unavailable.")
            return
        self.call_from_thread(self._local_model_activated, model_id)

    def _install_local_candidate_worker(
        self: _LocalFlowHost,
        candidate: LlamaCppCandidate,
    ) -> None:
        try:
            result = llama_cpp.install_hf_model(candidate)
        except Exception as exc:
            self.call_from_thread(self._local_model_failed, f"Local model install failed: {exc}")
            return
        if not result.capability.passed:
            reason = _capability_failure_reason(result.capability)
            self.call_from_thread(
                self._local_model_failed,
                f"Local model downloaded but not activated: {reason}",
            )
            return
        if not switch_model(self.session, LLAMA_CPP_PROVIDER_SLUG, result.record.model_id):
            self.call_from_thread(
                self._local_model_failed,
                "Local model installed but could not be activated.",
            )
            return
        self.call_from_thread(self._local_model_activated, result.record.model_id)

    def _revalidate_local_model_worker(self: _LocalFlowHost, model_id: str) -> None:
        capability = llama_cpp.revalidate_model(model_id)
        if not capability.passed:
            self.call_from_thread(
                self._local_model_failed,
                f"Tool-call probe failed: {_capability_failure_reason(capability)}",
            )
            return
        if not switch_model(self.session, LLAMA_CPP_PROVIDER_SLUG, model_id):
            self.call_from_thread(
                self._local_model_failed,
                "Local model revalidated but could not be activated.",
            )
            return
        self.call_from_thread(self._local_model_activated, model_id)

    def _local_model_activated(self: _LocalFlowHost, model_id: str) -> None:
        self._append_notice(f"local model: {model_id}")
        self._refresh_status()
        self._update_info_panel()

    def _local_model_failed(self: _LocalFlowHost, message: str) -> None:
        self._append_error(message)
        self._refresh_status()
        self._update_info_panel()


def _local_flow_options(
    records: Sequence[LlamaCppModelRecord],
    candidates: Sequence[LlamaCppCandidate],
    *,
    current_model: str,
) -> list[tuple[str, str]]:
    downloaded_ids = {record.model_id for record in records}
    record_options = [
        _local_record_option(record, current_model=current_model)
        for record in sorted(records, key=_local_record_sort_key)
    ]
    candidate_options = [
        _local_candidate_option(candidate)
        for candidate in candidates
        if candidate.model_id not in downloaded_ids
    ]
    return [*record_options, *candidate_options]


def _local_record_sort_key(record: LlamaCppModelRecord) -> tuple[int, str]:
    return (0 if record.tool_capable else 1, record.model_id.casefold())


def _local_record_option(
    record: LlamaCppModelRecord,
    *,
    current_model: str,
) -> tuple[str, str]:
    status = "tool-capable" if record.tool_capable else "revalidate needed"
    parts = ["downloaded", status, _local_record_source(record)]
    if record.model_id == current_model:
        parts.append("current")
    return record.model_id, _description_parts(parts)


def _local_candidate_option(candidate: LlamaCppCandidate) -> tuple[str, str]:
    parts = [
        "not downloaded",
        candidate.quant,
        _format_bytes(candidate.size_bytes),
        _popularity_text(candidate),
    ]
    return candidate.model_id, _description_parts(parts)


def _description_parts(parts: Sequence[str]) -> str:
    return ", ".join(part for part in parts if part)


def _local_record_source(record: LlamaCppModelRecord) -> str:
    if record.local_path:
        return Path(record.local_path).name
    return record.quant


def _popularity_text(candidate: LlamaCppCandidate) -> str:
    parts = []
    if candidate.downloads:
        parts.append(f"{candidate.downloads:,} downloads")
    if candidate.likes:
        parts.append(f"{candidate.likes:,} likes")
    return ", ".join(parts)


def _format_bytes(size_bytes: int) -> str:
    if size_bytes <= 0:
        return ""
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return ""


def _local_record_action_notice(record: LlamaCppModelRecord) -> str:
    if record.tool_capable:
        return f"starting local model: {record.model_id}"
    return f"revalidating local model: {record.model_id}"


def _capability_failure_reason(capability: ToolCapabilityResult) -> str:
    return capability.reason or "model did not return a valid tool call"
