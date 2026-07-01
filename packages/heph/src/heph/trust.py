from __future__ import annotations

from pathlib import Path

from ai.providers.llama_cpp import llama_cpp_cache_dir, llama_cpp_model_cache_dir
from harness.armory.storage import default_armory_home
from harness.parameters.settings import user_config_dir


def format_trust_report(armory_path: Path | None = None) -> str:
    lines = [
        "Heph trust contract",
        "",
        "1. Who owns the data?",
        "   You do. Armory materials, indexes, memory, chats, traces, and usage snapshots "
        "are local files in the armory. Heph has no hosted sync service.",
        "",
        "2. Where is the cache?",
        f"   Armory state: {_armory_state_path(armory_path)}",
        f"   Named armories: {default_armory_home()}",
        f"   User settings: {user_config_dir()}",
        f"   Local llama.cpp cache: {llama_cpp_cache_dir()}",
        f"   Local GGUF models: {llama_cpp_model_cache_dir()}",
        "",
        "3. Are the prompts secure?",
        "   With local llama.cpp compute, prompts, retrieved chunks, and tool calls stay on "
        "your machine. With a hosted provider, Heph sends only the active question, "
        "system instructions, and selected retrieved chunks needed for the answer to that "
        "provider. Diagnostics are opt-in and must not include document content or chat "
        "history.",
        "",
        "Ownership model",
        "   Mode: local armory workflow by default; optional diagnostics and web fetch stay "
        "explicit.",
        "   Application: open-source Heph process and SDK you can run, inspect, fork, or embed.",
        "   Compute: swappable provider layer; choose local llama.cpp, your own endpoint, or "
        "a hosted provider you trust.",
    ]
    return "\n".join(lines)


def _armory_state_path(armory_path: Path | None) -> str:
    if armory_path is None:
        return "<armory>/.harness/"
    return str(armory_path / ".harness")
