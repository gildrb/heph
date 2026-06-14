"""Slash command for private local llama.cpp models."""

from __future__ import annotations

from pathlib import Path

from ai.providers.llama_cpp import (
    LlamaCppCandidate,
    catalog_candidate_for_model_id,
    current_server_state,
    installed_records,
    llama_cpp_cache_dir,
    llama_cpp_model_cache_dir,
    model_record,
    revalidate_model,
    search_gguf_models,
    stop_llama_server,
)
from interfaces.terminal import (
    MenuOption,
    confirm,
    direct_input,
    menu_label_value,
    print_error,
    print_info,
    print_success,
    select_option,
)

from heph.commands._base import Command, CommandResult, ensure_session
from heph.local_llm import activate_local_record, find_hf_candidate, install_local_target


class LocalCommand(Command):
    name = "local"
    description = "Install and manage curated local llama.cpp models"

    def handle(self, session: object, args: str) -> CommandResult:
        action, remainder = _split_local_args(args)
        if action == "status":
            _print_status()
            return CommandResult()
        if action == "stop":
            _stop_server()
            return CommandResult()
        if action == "revalidate":
            _revalidate(session, remainder)
            return CommandResult()
        if action == "install":
            _install_target(session, remainder)
            return CommandResult()
        _guided_search(session, remainder)
        return CommandResult()


def _split_local_args(args: str) -> tuple[str, str]:
    command, separator, remainder = args.strip().partition(" ")
    if separator and command in {"search", "install", "status", "revalidate", "stop"}:
        return command, remainder.strip()
    if command in {"search", "install", "status", "revalidate", "stop"}:
        return command, ""
    return "search", args.strip()


def _guided_search(session: object, query: str) -> None:
    s = ensure_session(session)
    search_text = query
    if not search_text:
        try:
            search_text = direct_input("  Search local model catalog > ").strip()
        except (KeyboardInterrupt, EOFError):
            print_info("Cancelled.")
            return
    try:
        candidates = search_gguf_models(search_text, limit=30)
    except Exception as exc:
        print_error(f"Could not load local model catalog: {exc}")
        return
    if not candidates:
        print_info("No curated local models matched that search.")
        return
    selected = select_option("Local GGUF model", _candidate_options(candidates))
    if selected is None:
        print_info("Cancelled.")
        return
    _install_candidate(s, candidates[selected])


def _install_candidate(session: object, candidate: LlamaCppCandidate) -> None:
    target = candidate.repo_id if not candidate.quant else candidate.hf_ref
    _install_target(session, target, candidate)


def _install_target(
    session: object,
    target: str,
    candidate: LlamaCppCandidate | None = None,
) -> None:
    s = ensure_session(session)
    if not target:
        _guided_search(s, "")
        return
    candidate = candidate or _candidate_for_target(target)
    if candidate is None and not _target_is_local_file(target):
        print_error("No curated local model matched that target.")
        return
    if not _confirm_local_load(target, candidate):
        print_info("Cancelled.")
        return
    print_info("Downloading or starting llama.cpp, then probing tool-call support.")
    try:
        result = install_local_target(target)
    except Exception as exc:
        print_error(f"Local model install failed: {exc}")
        return
    if not result.capability.passed:
        reason = result.capability.reason or "model did not return a valid tool call"
        print_error(
            f"Local model installed but not activated because the tool-call probe failed: {reason}"
        )
        return
    activate_local_record(result.record, s)
    print_success(f"Local model activated: {result.record.model_id}")


def _revalidate(session: object, model_id: str) -> None:
    s = ensure_session(session)
    if not model_id:
        print_error("Usage: /local revalidate <model-id>")
        return
    capability = revalidate_model(model_id)
    record = model_record(model_id)
    if record is None:
        print_error(capability.reason or "model is not installed")
        return
    if not capability.passed:
        reason = capability.reason or "model did not return a valid tool call"
        print_error(f"Tool-call probe failed: {reason}")
        return
    activate_local_record(record, s)
    print_success(f"Local model revalidated and activated: {model_id}")


def _stop_server() -> None:
    if stop_llama_server():
        print_success("Stopped llama.cpp.")
        return
    print_info("No managed llama.cpp server was running.")


def _print_status() -> None:
    print("Local llama.cpp")
    print(f"  cache: {llama_cpp_cache_dir()}")
    print(f"  models: {llama_cpp_model_cache_dir()}")
    server = current_server_state()
    if server is None:
        print("  server: stopped")
    else:
        print(f"  server: running on {server.endpoint}")
        print(f"  active model: {server.model_id}")
    records = installed_records()
    if not records:
        print("  installed: none")
        return
    print("  installed:")
    for record in records:
        status = "tool-capable" if record.tool_capable else "not selectable"
        candidate = catalog_candidate_for_model_id(record.model_id)
        label = candidate.label if candidate is not None else record.model_id
        resource = _candidate_description(candidate) if candidate is not None else ""
        details = [status, f"MODEL {record.model_id}"]
        if resource:
            details.append(resource)
        print(f"  - {label} ({'; '.join(details)})")


def _candidate_options(candidates: list[LlamaCppCandidate]) -> list[MenuOption]:
    return [
        MenuOption(candidate.label, _candidate_description(candidate)) for candidate in candidates
    ]


def _candidate_description(candidate: LlamaCppCandidate) -> str:
    parts = [menu_label_value("quant", candidate.quant)] if candidate.quant else []
    size = _format_bytes(candidate.size_bytes)
    if size:
        parts.append(menu_label_value("size", size))
    if candidate.recommended_ram_gb:
        parts.append(menu_label_value("ram", f"{candidate.recommended_ram_gb} GB"))
    return "  ".join(part for part in parts if part)


def _candidate_for_target(target: str) -> LlamaCppCandidate | None:
    return find_hf_candidate(target)


def _target_is_local_file(target: str) -> bool:
    path = Path(target).expanduser()
    return path.is_file() or target.lower().endswith(".gguf")


def _confirm_local_load(target: str, candidate: LlamaCppCandidate | None) -> bool:
    if candidate is not None:
        return confirm(
            f"Load {candidate.label}? {_candidate_description(candidate)}.",
            default=False,
        )
    path = Path(target).expanduser()
    size = _format_bytes(path.stat().st_size) if path.is_file() else "unknown size"
    return confirm(
        f"Load local GGUF {path.name}? {size} download; RAM depends on the file.",
        default=False,
    )


def _format_bytes(size_bytes: int) -> str:
    if size_bytes <= 0:
        return ""
    size_gb = size_bytes / 1024**3
    if size_gb < 0.05:
        return "<0.1 GB"
    return f"{size_gb:.1f} GB"
