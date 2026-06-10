"""Slash command for private local llama.cpp models."""

from __future__ import annotations

from ai.providers.llama_cpp import (
    LlamaCppCandidate,
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
    direct_input,
    print_error,
    print_info,
    print_success,
    select_option,
)

from heph.commands._base import Command, CommandResult, ensure_session
from heph.local_llm import activate_local_record, install_local_target


class LocalCommand(Command):
    name = "local"
    description = "Install and manage private tool-capable llama.cpp models"

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
            search_text = direct_input("  Search GGUF models > ").strip()
        except (KeyboardInterrupt, EOFError):
            print_info("Cancelled.")
            return
    try:
        candidates = search_gguf_models(search_text, limit=30)
    except Exception as exc:
        print_error(f"Could not search Hugging Face GGUF models: {exc}")
        return
    if not candidates:
        print_info("No public non-gated GGUF models matched that search.")
        return
    selected = select_option("Local GGUF model", _candidate_options(candidates))
    if selected is None:
        print_info("Cancelled.")
        return
    _install_candidate(s, candidates[selected])


def _install_candidate(session: object, candidate: LlamaCppCandidate) -> None:
    _install_target(session, candidate.repo_id if not candidate.quant else candidate.hf_ref)


def _install_target(session: object, target: str) -> None:
    s = ensure_session(session)
    if not target:
        _guided_search(s, "")
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
        print(f"  - {record.model_id} ({status})")


def _candidate_options(candidates: list[LlamaCppCandidate]) -> list[MenuOption]:
    return [
        MenuOption(candidate.label, _candidate_description(candidate)) for candidate in candidates
    ]


def _candidate_description(candidate: LlamaCppCandidate) -> str:
    popularity = []
    if candidate.downloads:
        popularity.append(f"{candidate.downloads:,} downloads")
    if candidate.likes:
        popularity.append(f"{candidate.likes:,} likes")
    return ", ".join(popularity)
