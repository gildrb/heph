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
    find_hf_candidate,
    install_local_target,
)
from hephaion.chat.model_selection import switch_model

from interfaces.tui.display_text import menu_label_value
from interfaces.tui.flow_state import InlineFlow
from interfaces.tui.inline_menu import local_model_option_description

try:
    from textual.css.query import NoMatches
    from textual.widgets import Input
except ImportError:
    Input = None  # ty:ignore[invalid-assignment]
    NoMatches = LookupError  # ty:ignore[invalid-assignment]

if TYPE_CHECKING:
    from hephaion.chat.session import ChatSession

_P = ParamSpec("_P")
_WidgetT = TypeVar("_WidgetT")

_LOCAL_SEARCH_LIMIT = 30
_LOCAL_CONFIRM_LABEL = "LOAD MODEL"
_LOCAL_CANCEL_LABEL = "CANCEL"


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

    def _open_local_install_target_flow(self, target: str) -> None: ...

    def _refresh_local_flow_worker(self, query: str) -> None: ...

    def _refresh_local_flow_options(self, candidates: list[LlamaCppCandidate]) -> None: ...

    def _local_flow_search_failed(self, message: str) -> None: ...

    def _handle_local_choice(self, label: str) -> None: ...

    def _handle_confirmed_local_choice(self, label: str) -> None: ...

    def _open_local_confirmation(
        self,
        *,
        model_id: str,
        target_label: str,
        description: str,
    ) -> None: ...

    def _activate_local_model_worker(self, model_id: str) -> None: ...

    def _install_local_candidate_worker(self, candidate: LlamaCppCandidate) -> None: ...

    def _install_local_target_worker(self, target: str) -> None: ...

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
            title=f"Local models  {menu_label_value('model', self.session.config.model)}",
            options=options,
        )
        self._inline_flow.slug = search_query
        self._append_notice("Showing curated local GGUF models.")
        self.run_worker(lambda: self._refresh_local_flow_worker(search_query), thread=True)

    def _open_local_install_target_flow(self: _LocalFlowHost, target: str) -> None:
        install_target = target.strip()
        if not install_target:
            self._open_local_flow("")
            return

        self._local_flow_candidates = {}
        if record := _local_record_for_label(install_target):
            self._open_local_confirmation(
                model_id=record.model_id,
                target_label=_local_record_label(record),
                description=_local_record_confirmation_description(record),
            )
            return

        candidate = find_hf_candidate(install_target)
        if candidate is not None:
            self._local_flow_candidates = _local_candidate_lookup([candidate])
            self._open_local_confirmation(
                model_id=candidate.model_id,
                target_label=candidate.label,
                description=_local_candidate_confirmation_description(candidate),
            )
            return

        if _target_is_local_gguf(install_target):
            path = Path(install_target).expanduser()
            self._open_local_confirmation(
                model_id=install_target,
                target_label=path.name or install_target,
                description=_local_target_confirmation_description(install_target),
            )
            return

        self._append_error("No curated local model matched that target.")

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
        if (
            not self._inline_flow.active
            or self._inline_flow.name != "local"
            or self._inline_flow.step != "menu"
        ):
            return
        self._local_flow_candidates = _local_candidate_lookup(candidates)
        self._inline_flow.all_options = _local_flow_options(
            llama_cpp.installed_records(),
            candidates,
            current_model=self.session.config.model,
        )
        try:
            composer = self.query_one("#composer", Input)
            self._filter_inline_menu_options(composer.value)
        except NoMatches:
            return

    def _local_flow_search_failed(self: _LocalFlowHost, message: str) -> None:
        if not self._inline_flow.active or self._inline_flow.name != "local":
            return
        self._append_error(f"Could not load local model catalog: {message}")

    def _handle_local_choice(self: _LocalFlowHost, label: str) -> None:
        if self._inline_flow.step == "confirm":
            self._handle_confirmed_local_choice(label)
            return

        record = _local_record_for_label(label)
        if record is not None:
            self._open_local_confirmation(
                model_id=record.model_id,
                target_label=_local_record_label(record),
                description=_local_record_confirmation_description(record),
            )
            return

        candidate = self._local_flow_candidates.get(label)
        if candidate is None:
            self._close_inline_flow("Local model not found.")
            return
        self._open_local_confirmation(
            model_id=candidate.model_id,
            target_label=candidate.label,
            description=_local_candidate_confirmation_description(candidate),
        )

    def _handle_confirmed_local_choice(self: _LocalFlowHost, label: str) -> None:
        if label != _LOCAL_CONFIRM_LABEL:
            self._close_inline_flow("Cancelled.")
            return

        model_id = self._inline_flow.slug
        record = _local_record_for_label(model_id)
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

        candidate = self._local_flow_candidates.get(model_id)
        if candidate is None:
            self._close_inline_flow(f"installing local model: {model_id}")
            self.run_worker(lambda: self._install_local_target_worker(model_id), thread=True)
            return
        self._close_inline_flow(f"installing local model: {candidate.model_id}")
        self.run_worker(lambda: self._install_local_candidate_worker(candidate), thread=True)

    def _open_local_confirmation(
        self: _LocalFlowHost,
        *,
        model_id: str,
        target_label: str,
        description: str,
    ) -> None:
        self._open_inline_menu(
            name="local",
            step="confirm",
            title=_local_confirmation_title(target_label),
            options=[
                (_LOCAL_CONFIRM_LABEL, description),
                (_LOCAL_CANCEL_LABEL, ""),
            ],
        )
        self._inline_flow.slug = model_id

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

    def _install_local_target_worker(self: _LocalFlowHost, target: str) -> None:
        try:
            result = install_local_target(target)
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
    record_labels = _local_record_labels(records)
    record_options = [
        _local_record_option(
            record,
            current_model=current_model,
            label=record_labels[record.model_id],
        )
        for record in sorted(
            records, key=lambda record: _local_record_sort_key(record, record_labels)
        )
    ]
    candidate_options = [
        _local_candidate_option(candidate)
        for candidate in candidates
        if candidate.model_id not in downloaded_ids
    ]
    return [*record_options, *candidate_options]


def _local_record_sort_key(
    record: LlamaCppModelRecord,
    record_labels: dict[str, str],
) -> tuple[int, str]:
    return (0 if record.tool_capable else 1, record_labels[record.model_id].casefold())


def _local_record_option(
    record: LlamaCppModelRecord,
    *,
    current_model: str,
    label: str,
) -> tuple[str, str]:
    if record.model_id == current_model:
        status = "current"
    elif record.tool_capable:
        status = "ready"
    else:
        status = "needs probe"
    candidate = llama_cpp.catalog_candidate_for_model_id(record.model_id)
    quant = record.quant or (candidate.quant if candidate is not None else "")
    size = _format_bytes(candidate.size_bytes) if candidate is not None else ""
    resource_detail = _local_candidate_resource_detail(candidate) if candidate is not None else ""
    detail = _local_record_menu_detail(record, label=label, status=status, extra=resource_detail)
    return label, local_model_option_description(
        "",
        "",
        quant,
        size,
        detail,
    )


def _local_candidate_option(candidate: LlamaCppCandidate) -> tuple[str, str]:
    return candidate.label, local_model_option_description(
        "",
        "",
        candidate.quant,
        _format_bytes(candidate.size_bytes),
        _local_candidate_resource_detail(candidate),
    )


def _local_candidate_lookup(
    candidates: Sequence[LlamaCppCandidate],
) -> dict[str, LlamaCppCandidate]:
    lookup: dict[str, LlamaCppCandidate] = {}
    for candidate in candidates:
        lookup[candidate.model_id] = candidate
        lookup[candidate.hf_ref] = candidate
        lookup[candidate.repo_id] = candidate
        lookup[candidate.label] = candidate
    return lookup


def _local_record_label(record: LlamaCppModelRecord) -> str:
    candidate = llama_cpp.catalog_candidate_for_model_id(record.model_id)
    if candidate is not None:
        return candidate.label
    if record.local_path:
        return Path(record.local_path).name
    return record.model_id


def _local_record_labels(records: Sequence[LlamaCppModelRecord]) -> dict[str, str]:
    duplicate_local_names = _duplicate_local_filenames(records)
    return {
        record.model_id: _local_record_menu_label(record, duplicate_local_names)
        for record in records
    }


def _duplicate_local_filenames(records: Sequence[LlamaCppModelRecord]) -> set[str]:
    seen_names: set[str] = set()
    duplicate_names: set[str] = set()
    for record in records:
        if not record.local_path:
            continue
        name = Path(record.local_path).name
        if name in seen_names:
            duplicate_names.add(name)
            continue
        seen_names.add(name)
    return duplicate_names


def _local_record_menu_label(
    record: LlamaCppModelRecord,
    duplicate_local_names: set[str],
) -> str:
    label = _local_record_label(record)
    if record.local_path and label in duplicate_local_names:
        return record.model_id
    return label


def _local_record_for_label(label: str) -> LlamaCppModelRecord | None:
    if record := llama_cpp.model_record(label):
        return record
    records = llama_cpp.installed_records()
    record_labels = _local_record_labels(records)
    return next(
        (
            record
            for record in records
            if label in {record.model_id, record_labels[record.model_id]}
        ),
        None,
    )


def _local_record_source(record: LlamaCppModelRecord) -> str:
    if record.local_path:
        return Path(record.local_path).name
    return record.quant


def _target_is_local_gguf(target: str) -> bool:
    path = Path(target).expanduser()
    return path.is_file() or target.casefold().endswith(".gguf")


def _local_target_confirmation_description(target: str) -> str:
    path = Path(target).expanduser()
    size = _format_bytes(path.stat().st_size) if path.is_file() else "unknown size"
    return _local_confirmation_description(
        ("format", "gguf"),
        ("size", size),
        ("source", "local file"),
    )


def _local_confirmation_title(target_label: str) -> str:
    return (
        f"Local models  {menu_label_value('action', 'load')}  "
        f"{menu_label_value('model', target_label)}"
    )


def _local_candidate_resource_detail(candidate: LlamaCppCandidate) -> str:
    if candidate.recommended_ram_gb <= 0:
        return ""
    return menu_label_value("ram", f"{candidate.recommended_ram_gb} gb")


def _local_record_menu_detail(
    record: LlamaCppModelRecord,
    *,
    label: str,
    status: str,
    extra: str = "",
) -> str:
    parts = [menu_label_value("state", status)]
    if extra:
        parts.append(extra)
    source = _local_record_source(record)
    if source and source != label:
        parts.append(menu_label_value("source", source))
    return "  ".join(parts)


def _local_candidate_confirmation_description(candidate: LlamaCppCandidate) -> str:
    return _local_confirmation_description(
        ("quant", candidate.quant),
        ("size", _format_bytes(candidate.size_bytes)),
        ("ram", _local_candidate_ram_value(candidate)),
    )


def _local_record_confirmation_description(record: LlamaCppModelRecord) -> str:
    candidate = llama_cpp.catalog_candidate_for_model_id(record.model_id)
    if candidate is not None:
        return _local_candidate_confirmation_description(candidate)
    return _local_confirmation_description(
        ("quant", record.quant),
        ("source", _local_record_source(record)),
    )


def _local_confirmation_description(*fields: tuple[str, str]) -> str:
    return "  ".join(menu_label_value(label, value) for label, value in fields if value)


def _local_candidate_ram_value(candidate: LlamaCppCandidate) -> str:
    if candidate.recommended_ram_gb <= 0:
        return ""
    return f"{candidate.recommended_ram_gb} gb"


def _format_bytes(size_bytes: int) -> str:
    if size_bytes <= 0:
        return ""
    size_gb = size_bytes / 1024**3
    if size_gb < 0.05:
        return "<0.1 GB"
    return f"{size_gb:.1f} GB"


def _local_record_action_notice(record: LlamaCppModelRecord) -> str:
    if record.tool_capable:
        return f"starting local model: {record.model_id}"
    return f"revalidating local model: {record.model_id}"


def _capability_failure_reason(capability: ToolCapabilityResult) -> str:
    return capability.reason or "model did not return a valid tool call"
