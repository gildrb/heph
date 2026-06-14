"""Local llama.cpp provider management and GGUF model discovery."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import shutil
import signal
import socket
import ssl
import stat
import subprocess
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import certifi

from ai.providers.registry import ModelInfo
from ai.types import is_object_list, is_string_mapping

LLAMA_CPP_PROVIDER_SLUG = "llama-cpp"
LLAMA_CPP_DISPLAY_NAME = "Local llama.cpp"
LLAMA_CPP_DEFAULT_PORT = 18080
LLAMA_CPP_DEFAULT_BASE_URL = f"http://127.0.0.1:{LLAMA_CPP_DEFAULT_PORT}/v1"

_CONFIG_DIR = Path.home() / ".config" / "hephaion"
_CACHE_DIR = Path.home() / ".cache" / "hephaion" / "llama.cpp"
_STATE_FILE = _CONFIG_DIR / "llama_cpp.json"
_BIN_DIR = _CACHE_DIR / "bin"
_MODEL_CACHE_DIR = _CACHE_DIR / "models"
_LOG_FILE = _CACHE_DIR / "llama-server.log"
_RELEASE_TAG = "b9585"
_SERVER_START_TIMEOUT_SECONDS = 900.0
_PROBE_TIMEOUT_SECONDS = 45.0
_PID_STOP_GRACE_SECONDS = 5.0
_PID_STOP_KILL_GRACE_SECONDS = 2.0
_PID_STOP_POLL_SECONDS = 0.1
_DEFAULT_CONTEXT_TOKENS = 8192
_STATE_DIR_MODE = 0o700
_STATE_FILE_MODE = 0o600
_MANAGED_SERVER_PROCESS: subprocess.Popen[bytes] | None = None


@dataclass(frozen=True, slots=True)
class LlamaCppReleaseAsset:
    system: str
    machine: str
    name: str
    sha256: str

    @property
    def url(self) -> str:
        return (
            f"https://github.com/ggml-org/llama.cpp/releases/download/{_RELEASE_TAG}/{self.name}"
        )


@dataclass(frozen=True, slots=True)
class LlamaCppCandidate:
    repo_id: str
    filename: str
    quant: str
    downloads: int
    likes: int
    size_bytes: int
    display_name: str = ""
    recommended_ram_gb: int = 0
    summary: str = ""

    @property
    def model_id(self) -> str:
        quant = self.quant or _quant_from_filename(self.filename)
        suffix = f":{quant}" if quant else ""
        return f"{LLAMA_CPP_PROVIDER_SLUG}/{self.repo_id}{suffix}"

    @property
    def hf_ref(self) -> str:
        return f"{self.repo_id}:{self.quant}" if self.quant else self.repo_id

    @property
    def label(self) -> str:
        if self.display_name:
            return self.display_name
        quant = f" {self.quant}" if self.quant else ""
        size = _format_bytes(self.size_bytes)
        size_suffix = f" {size}" if size else ""
        return f"{self.repo_id}{quant}{size_suffix}".strip()


@dataclass(frozen=True, slots=True)
class LlamaCppModelRecord:
    model_id: str
    repo_id: str = ""
    filename: str = ""
    quant: str = ""
    local_path: str = ""
    tool_capable: bool = False
    endpoint: str = LLAMA_CPP_DEFAULT_BASE_URL
    created_at: float = 0.0
    last_validated_at: float = 0.0

    @property
    def source_ref(self) -> str:
        if self.local_path:
            return self.local_path
        return f"{self.repo_id}:{self.quant}" if self.quant else self.repo_id


@dataclass(frozen=True, slots=True)
class LlamaCppServerState:
    pid: int
    endpoint: str
    model_id: str
    started_at: float
    hf_ref: str = ""
    hf_file: str = ""
    local_path: str = ""


@dataclass(frozen=True, slots=True)
class ToolCapabilityResult:
    passed: bool
    reason: str = ""


@dataclass(frozen=True, slots=True)
class LlamaCppInstallResult:
    record: LlamaCppModelRecord
    capability: ToolCapabilityResult
    server: LlamaCppServerState


@dataclass(frozen=True, slots=True)
class _LlamaCppCatalogEntry:
    repo_id: str
    filename: str
    quant: str
    display_name: str
    size_bytes: int
    recommended_ram_gb: int
    summary: str


@dataclass(frozen=True, slots=True)
class _LlamaCppState:
    records: list[LlamaCppModelRecord]
    server: LlamaCppServerState | None = None


_RELEASE_ASSETS: tuple[LlamaCppReleaseAsset, ...] = (
    LlamaCppReleaseAsset(
        "Darwin",
        "arm64",
        "llama-b9585-bin-macos-arm64.tar.gz",
        "e88f05f82c8c0c0f5a861ff7822f096ad6641128e6f64c666eee743f46730db6",
    ),
    LlamaCppReleaseAsset(
        "Darwin",
        "x86_64",
        "llama-b9585-bin-macos-x64.tar.gz",
        "31151226ac563764df3456b615c261d10a92f09e99be48a64d39985f15e7a15b",
    ),
    LlamaCppReleaseAsset(
        "Linux",
        "x86_64",
        "llama-b9585-bin-ubuntu-x64.tar.gz",
        "be111dd28e6228fc4cb6a6ec41f03a67947ab61f315a3d22d0e68ac7372a58ab",
    ),
    LlamaCppReleaseAsset(
        "Linux",
        "aarch64",
        "llama-b9585-bin-ubuntu-arm64.tar.gz",
        "42f957019f74abb14009916e444b08f2d76e11e25b091d8dfdf31f6bea680f71",
    ),
    LlamaCppReleaseAsset(
        "Windows",
        "AMD64",
        "llama-b9585-bin-win-cpu-x64.zip",
        "23c0e329e2228f7cbcc83884f42c7787f1a3133e5548ea99e89d60202e1fd89c",
    ),
    LlamaCppReleaseAsset(
        "Windows",
        "ARM64",
        "llama-b9585-bin-win-cpu-arm64.zip",
        "9dd7cde8fdc2a5c932f63e4392c1c10ce6f65d39a70a781d9a3978e68ca9c215",
    ),
)

_CURATED_GGUF_MODELS: tuple[_LlamaCppCatalogEntry, ...] = (
    _LlamaCppCatalogEntry(
        repo_id="LiquidAI/LFM2-350M-GGUF",
        filename="LFM2-350M-Q4_K_M.gguf",
        quant="Q4_K_M",
        display_name="LFM2 350M",
        size_bytes=229_309_376,
        recommended_ram_gb=4,
        summary="Liquid AI edge release; tiniest general chat option",
    ),
    _LlamaCppCatalogEntry(
        repo_id="HuggingFaceTB/SmolLM2-360M-Instruct-GGUF",
        filename="smollm2-360m-instruct-q8_0.gguf",
        quant="Q8_0",
        display_name="SmolLM2 360M Instruct",
        size_bytes=386_404_992,
        recommended_ram_gb=4,
        summary="Hugging Face TB tiny instruct release; fastest low-resource option",
    ),
    _LlamaCppCatalogEntry(
        repo_id="Qwen/Qwen2.5-0.5B-Instruct-GGUF",
        filename="qwen2.5-0.5b-instruct-q4_k_m.gguf",
        quant="Q4_K_M",
        display_name="Qwen2.5 0.5B Instruct",
        size_bytes=491_400_032,
        recommended_ram_gb=4,
        summary="Qwen release; tiny general instruction model",
    ),
    _LlamaCppCatalogEntry(
        repo_id="Qwen/Qwen3-0.6B-GGUF",
        filename="Qwen3-0.6B-Q8_0.gguf",
        quant="Q8_0",
        display_name="Qwen3 0.6B",
        size_bytes=639_446_688,
        recommended_ram_gb=4,
        summary="official Qwen release; smallest Qwen3 text-generation model",
    ),
    _LlamaCppCatalogEntry(
        repo_id="allenai/OLMo-2-0425-1B-Instruct-GGUF",
        filename="OLMo-2-0425-1B-Instruct-Q4_K_M.gguf",
        quant="Q4_K_M",
        display_name="OLMo 2 1B Instruct",
        size_bytes=935_515_296,
        recommended_ram_gb=4,
        summary="official AllenAI release; compact open instruct model",
    ),
    _LlamaCppCatalogEntry(
        repo_id="HuggingFaceTB/SmolLM2-1.7B-Instruct-GGUF",
        filename="smollm2-1.7b-instruct-q4_k_m.gguf",
        quant="Q4_K_M",
        display_name="SmolLM2 1.7B Instruct",
        size_bytes=1_055_609_536,
        recommended_ram_gb=6,
        summary="Hugging Face TB small instruct release; low-memory daily use",
    ),
    _LlamaCppCatalogEntry(
        repo_id="Qwen/Qwen2.5-1.5B-Instruct-GGUF",
        filename="qwen2.5-1.5b-instruct-q4_k_m.gguf",
        quant="Q4_K_M",
        display_name="Qwen2.5 1.5B Instruct",
        size_bytes=1_117_320_736,
        recommended_ram_gb=6,
        summary="Qwen release; small general instruction model",
    ),
    _LlamaCppCatalogEntry(
        repo_id="Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF",
        filename="qwen2.5-coder-1.5b-instruct-q4_k_m.gguf",
        quant="Q4_K_M",
        display_name="Qwen2.5 Coder 1.5B Instruct",
        size_bytes=1_117_320_768,
        recommended_ram_gb=6,
        summary="official Qwen coder release; tiny code-oriented option",
    ),
    _LlamaCppCatalogEntry(
        repo_id="ibm-granite/granite-3.3-2b-instruct-GGUF",
        filename="granite-3.3-2b-instruct-Q4_K_M.gguf",
        quant="Q4_K_M",
        display_name="Granite 3.3 2B Instruct",
        size_bytes=1_545_303_328,
        recommended_ram_gb=6,
        summary="official IBM Granite release; compact instruction model",
    ),
    _LlamaCppCatalogEntry(
        repo_id="Qwen/Qwen3-1.7B-GGUF",
        filename="Qwen3-1.7B-Q8_0.gguf",
        quant="Q8_0",
        display_name="Qwen3 1.7B",
        size_bytes=1_834_426_016,
        recommended_ram_gb=6,
        summary="official Qwen release; small Qwen3 reasoning model",
    ),
    _LlamaCppCatalogEntry(
        repo_id="mistralai/Ministral-3-3B-Instruct-2512-GGUF",
        filename="Ministral-3-3B-Instruct-2512-Q4_K_M.gguf",
        quant="Q4_K_M",
        display_name="Ministral 3 3B Instruct",
        size_bytes=2_147_023_008,
        recommended_ram_gb=8,
        summary="official Mistral edge release; compact instruction model",
    ),
    _LlamaCppCatalogEntry(
        repo_id="microsoft/Phi-3-mini-4k-instruct-gguf",
        filename="Phi-3-mini-4k-instruct-q4.gguf",
        quant="Q4_0",
        display_name="Phi-3 Mini 4K Instruct",
        size_bytes=2_393_231_072,
        recommended_ram_gb=8,
        summary="official Microsoft release; small reasoning model",
    ),
    _LlamaCppCatalogEntry(
        repo_id="Qwen/Qwen3-4B-GGUF",
        filename="Qwen3-4B-Q4_K_M.gguf",
        quant="Q4_K_M",
        display_name="Qwen3 4B",
        size_bytes=2_497_280_256,
        recommended_ram_gb=8,
        summary="official Qwen release; strong low-cost default",
    ),
    _LlamaCppCatalogEntry(
        repo_id="google/gemma-4-E2B-it-qat-q4_0-gguf",
        filename="gemma-4-E2B_q4_0-it.gguf",
        quant="Q4_0",
        display_name="Gemma 4 E2B Instruct",
        size_bytes=3_349_514_112,
        recommended_ram_gb=8,
        summary="official Google QAT release; efficient small Gemma option",
    ),
    _LlamaCppCatalogEntry(
        repo_id="google/gemma-4-E4B-it-qat-q4_0-gguf",
        filename="gemma-4-E4B_q4_0-it.gguf",
        quant="Q4_0",
        display_name="Gemma 4 E4B Instruct",
        size_bytes=5_154_939_136,
        recommended_ram_gb=12,
        summary="official Google QAT release; balanced Gemma option",
    ),
    _LlamaCppCatalogEntry(
        repo_id="Qwen/Qwen3-8B-GGUF",
        filename="Qwen3-8B-Q4_K_M.gguf",
        quant="Q4_K_M",
        display_name="Qwen3 8B",
        size_bytes=5_027_783_488,
        recommended_ram_gb=12,
        summary="official Qwen release; higher-quality local option",
    ),
    _LlamaCppCatalogEntry(
        repo_id="mistralai/Ministral-3-8B-Instruct-2512-GGUF",
        filename="Ministral-3-8B-Instruct-2512-Q4_K_M.gguf",
        quant="Q4_K_M",
        display_name="Ministral 3 8B Instruct",
        size_bytes=5_198_911_904,
        recommended_ram_gb=12,
        summary="official Mistral release; agentic and JSON capable",
    ),
    _LlamaCppCatalogEntry(
        repo_id="google/gemma-4-12B-it-qat-q4_0-gguf",
        filename="gemma-4-12b-it-qat-q4_0.gguf",
        quant="Q4_0",
        display_name="Gemma 4 12B Instruct",
        size_bytes=6_975_877_728,
        recommended_ram_gb=16,
        summary="official Google QAT release; best catalog quality, largest footprint",
    ),
)


def llama_cpp_cache_dir() -> Path:
    return _CACHE_DIR


def llama_cpp_model_cache_dir() -> Path:
    return _MODEL_CACHE_DIR


def llama_cpp_state_file() -> Path:
    return _STATE_FILE


def is_llama_cpp_endpoint(base_url: str) -> bool:
    normalized = _normalize_endpoint(base_url)
    return normalized.startswith("http://127.0.0.1:") and normalized.endswith("/v1")


def search_gguf_models(query: str = "", *, limit: int = 20) -> list[LlamaCppCandidate]:
    """Return curated publisher GGUF models that fit Heph's local resource budget."""

    candidates = [_candidate_from_catalog_entry(entry) for entry in _CURATED_GGUF_MODELS]
    terms = query.casefold().split()
    if terms:
        candidates = [
            candidate
            for candidate in candidates
            if all(_candidate_matches_term(candidate, term) for term in terms)
        ]
    return candidates[: max(0, limit)]


def find_gguf_model(repo_id: str, *, quant: str = "") -> LlamaCppCandidate | None:
    """Find an exact curated publisher GGUF repo and optional quantization."""

    cleaned_repo_id = _normalize_remote_repo_id(repo_id)
    if not cleaned_repo_id:
        return None
    requested_quant = quant.strip().upper()
    for entry in _CURATED_GGUF_MODELS:
        if entry.repo_id != cleaned_repo_id:
            continue
        if requested_quant and entry.quant != requested_quant:
            return None
        return _candidate_from_catalog_entry(entry)
    return None


def find_hf_candidate(target: str) -> LlamaCppCandidate | None:
    repo_id, quant = _split_hf_target(target)
    if quant:
        return find_gguf_model(repo_id, quant=quant)
    candidate = find_gguf_model(repo_id)
    if candidate is not None:
        return candidate
    candidates = search_gguf_models(repo_id, limit=50)
    for candidate in candidates:
        if candidate.repo_id == repo_id:
            return candidate
    return None


def install_local_target(target: str, *, model_id: str = "") -> LlamaCppInstallResult:
    path = Path(target).expanduser()
    if path.is_file() or target.casefold().endswith(".gguf"):
        return install_local_model(path, model_id=model_id or None)
    candidate = find_hf_candidate(target)
    if candidate is None:
        msg = "No curated GGUF model matched that Hugging Face target."
        raise RuntimeError(msg)
    return install_hf_model(candidate)


def _split_hf_target(target: str) -> tuple[str, str]:
    repo_id, separator, quant = target.strip().rpartition(":")
    if separator and repo_id and quant:
        return repo_id, quant.upper()
    return target.strip(), ""


def catalog_candidate_for_model_id(model_id: str) -> LlamaCppCandidate | None:
    normalized = model_id.strip()
    for entry in _CURATED_GGUF_MODELS:
        candidate = _candidate_from_catalog_entry(entry)
        if normalized in {candidate.model_id, candidate.hf_ref, candidate.repo_id}:
            return candidate
    return None


def install_hf_model(candidate: LlamaCppCandidate) -> LlamaCppInstallResult:
    server = start_llama_server(
        model_id=candidate.model_id,
        hf_ref=candidate.hf_ref,
        hf_file=candidate.filename,
    )
    capability = probe_tool_capability(server.endpoint, candidate.model_id)
    record = LlamaCppModelRecord(
        model_id=candidate.model_id,
        repo_id=candidate.repo_id,
        filename=candidate.filename,
        quant=candidate.quant,
        tool_capable=capability.passed,
        endpoint=server.endpoint,
        created_at=time.time(),
        last_validated_at=time.time() if capability.passed else 0.0,
    )
    save_model_record(record)
    _stop_failed_probe(capability)
    return LlamaCppInstallResult(record=record, capability=capability, server=server)


def install_local_model(path: Path, *, model_id: str | None = None) -> LlamaCppInstallResult:
    model_path = path.expanduser().resolve()
    if not model_path.is_file():
        raise FileNotFoundError(f"GGUF model not found: {model_path}")
    alias = _normalize_local_model_id(model_path, model_id)
    server = start_llama_server(model_id=alias, local_path=model_path)
    capability = probe_tool_capability(server.endpoint, alias)
    record = LlamaCppModelRecord(
        model_id=alias,
        local_path=str(model_path),
        tool_capable=capability.passed,
        endpoint=server.endpoint,
        created_at=time.time(),
        last_validated_at=time.time() if capability.passed else 0.0,
    )
    save_model_record(record)
    _stop_failed_probe(capability)
    return LlamaCppInstallResult(record=record, capability=capability, server=server)


def _stop_failed_probe(capability: ToolCapabilityResult) -> None:
    if capability.passed:
        return
    # The model is not usable by Heph; avoid leaving a large local server resident.
    stop_llama_server()


def revalidate_model(model_id: str) -> ToolCapabilityResult:
    record = model_record(model_id)
    if record is None:
        return ToolCapabilityResult(False, "model is not installed")
    try:
        server = start_record(record)
    except (OSError, RuntimeError, ValueError) as exc:
        capability = ToolCapabilityResult(False, f"model could not be started: {exc}")
        _save_revalidation_result(record, capability, record.endpoint)
        return capability
    capability = probe_tool_capability(server.endpoint, record.model_id)
    _save_revalidation_result(record, capability, server.endpoint)
    _stop_failed_probe(capability)
    return capability


def start_record(record: LlamaCppModelRecord) -> LlamaCppServerState:
    if record.local_path:
        return start_llama_server(model_id=record.model_id, local_path=Path(record.local_path))
    return start_llama_server(
        model_id=record.model_id,
        hf_ref=record.source_ref,
        hf_file=record.filename,
    )


def start_llama_server(
    *,
    model_id: str,
    hf_ref: str = "",
    hf_file: str = "",
    local_path: Path | None = None,
    port: int | None = None,
) -> LlamaCppServerState:
    existing = _managed_server_state()
    if existing is not None and _server_matches_request(
        existing,
        model_id=model_id,
        hf_ref=hf_ref,
        hf_file=hf_file,
        local_path=local_path,
    ):
        return existing
    if existing is not None:
        stopped = stop_llama_server()
        if not stopped and _managed_server_state() is not None:
            msg = "existing managed llama-server could not be stopped"
            raise RuntimeError(msg)

    binary = ensure_llama_server()
    selected_port = port or _find_free_port()
    endpoint = f"http://127.0.0.1:{selected_port}/v1"
    command = _server_command(
        binary,
        model_id=model_id,
        port=selected_port,
        hf_ref=hf_ref,
        hf_file=hf_file,
        local_path=local_path,
    )
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["LLAMA_CACHE"] = str(_MODEL_CACHE_DIR)
    _MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    log = _LOG_FILE.open("ab")
    try:
        process = subprocess.Popen(
            command,
            cwd=str(_CACHE_DIR),
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    finally:
        log.close()
    _remember_managed_process(process)

    server = LlamaCppServerState(
        pid=process.pid,
        endpoint=endpoint,
        model_id=model_id,
        started_at=time.time(),
        hf_ref=hf_ref,
        hf_file=hf_file,
        local_path=_local_path_text(local_path),
    )
    _save_state(_replace_server(_load_state(), server))
    if not _wait_for_server(server):
        _terminate_process(process)
        _clear_managed_process(process)
        _save_state(_replace_server(_load_state(), None))
        raise RuntimeError(f"llama-server did not become ready; see {_LOG_FILE}")
    return server


def stop_llama_server() -> bool:
    server = _managed_server_state()
    if server is None:
        return False
    stopped = _terminate_managed_server(server)
    if stopped or not _pid_running(server.pid):
        _save_state(_replace_server(_load_state(), None))
    return stopped


def current_server_state() -> LlamaCppServerState | None:
    server = _managed_server_state()
    if server is None:
        return None
    return server if server_is_ready(server) else None


def _managed_server_state() -> LlamaCppServerState | None:
    state = _load_state()
    server = state.server
    if server is None:
        return None
    if _server_state_pid_is_managed(server):
        return server
    _save_state(_replace_server(state, None))
    return None


def server_is_ready(server: LlamaCppServerState) -> bool:
    response = _get_json(f"{server.endpoint}/models", timeout=2.0)
    return _models_response_includes(response, server.model_id)


def _server_matches_request(
    server: LlamaCppServerState,
    *,
    model_id: str,
    hf_ref: str,
    hf_file: str,
    local_path: Path | None,
) -> bool:
    return (
        server.model_id == model_id
        and server.hf_ref == hf_ref
        and server.hf_file == hf_file
        and server.local_path == _local_path_text(local_path)
        and server_is_ready(server)
    )


def installed_tool_capable_records() -> list[LlamaCppModelRecord]:
    return [record for record in _load_state().records if record.tool_capable]


def installed_records() -> list[LlamaCppModelRecord]:
    return list(_load_state().records)


def installed_model_ids() -> list[str]:
    return [record.model_id for record in installed_tool_capable_records()]


def model_record(model_id: str) -> LlamaCppModelRecord | None:
    return next((record for record in _load_state().records if record.model_id == model_id), None)


def save_model_record(record: LlamaCppModelRecord) -> None:
    state = _load_state()
    records = [existing for existing in state.records if existing.model_id != record.model_id]
    records.append(record)
    _save_state(_LlamaCppState(records=records, server=state.server))


def model_info_for_record(record: LlamaCppModelRecord) -> ModelInfo:
    return ModelInfo(
        record.model_id,
        LLAMA_CPP_PROVIDER_SLUG,
        _display_name_for_record(record),
        _DEFAULT_CONTEXT_TOKENS,
        4096,
        0.0,
        0.0,
        tags=("local", "tools"),
        supports_tools=True,
    )


def ensure_llama_server() -> Path:
    existing = _llama_server_path()
    if existing is not None:
        return existing
    asset = release_asset_for_current_platform()
    archive = _download_release_asset(asset)
    _verify_sha256(archive, asset.sha256)
    _extract_release_asset(archive, _BIN_DIR)
    installed = _llama_server_path()
    if installed is None:
        raise FileNotFoundError("downloaded llama.cpp release did not include llama-server")
    installed.chmod(installed.stat().st_mode | 0o755)
    return installed


def release_asset_for_current_platform() -> LlamaCppReleaseAsset:
    system = platform.system()
    machine = platform.machine()
    normalized_machine = {"arm64": "arm64", "aarch64": "aarch64", "x86_64": "x86_64"}.get(
        machine,
        machine,
    )
    for asset in _RELEASE_ASSETS:
        if asset.system == system and asset.machine == normalized_machine:
            return asset
    raise RuntimeError(f"No pinned llama.cpp release asset for {system}/{machine}")


def probe_tool_capability(endpoint: str, model_id: str) -> ToolCapabilityResult:
    payload = {
        "model": model_id,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are validating tool calling. Call the provided tool exactly once "
                    "with value set to ready."
                ),
            },
            {"role": "user", "content": "Call heph_probe_echo now."},
        ],
        "tools": [_probe_tool_schema()],
        "tool_choice": {"type": "function", "function": {"name": "heph_probe_echo"}},
        "temperature": 0,
        "stream": False,
        "max_tokens": 64,
    }
    response = _post_json(f"{_normalize_endpoint(endpoint)}/chat/completions", payload)
    if response is None:
        return ToolCapabilityResult(False, "probe request failed")
    return _tool_capability_from_response(response)


def _candidate_from_catalog_entry(entry: _LlamaCppCatalogEntry) -> LlamaCppCandidate:
    return LlamaCppCandidate(
        repo_id=entry.repo_id,
        filename=entry.filename,
        quant=entry.quant,
        downloads=0,
        likes=0,
        size_bytes=entry.size_bytes,
        display_name=entry.display_name,
        recommended_ram_gb=entry.recommended_ram_gb,
        summary=entry.summary,
    )


def _candidate_matches_term(candidate: LlamaCppCandidate, term: str) -> bool:
    fields = (
        candidate.display_name,
        candidate.repo_id,
        candidate.filename,
        candidate.quant,
        candidate.summary,
    )
    return any(term in field.casefold() for field in fields)


def _normalize_remote_repo_id(repo_id: str) -> str:
    return repo_id.strip().removeprefix(f"{LLAMA_CPP_PROVIDER_SLUG}/")


def _quant_from_filename(filename: str) -> str:
    stem = Path(filename).name.removesuffix(".gguf")
    for part in reversed(stem.split("-")):
        normalized = part.upper()
        if normalized.startswith(("Q2_", "Q3_", "Q4_", "Q5_", "Q6_", "Q8_", "IQ")):
            return normalized
    for part in reversed(stem.split(".")):
        normalized = part.upper()
        if normalized.startswith(("Q2_", "Q3_", "Q4_", "Q5_", "Q6_", "Q8_", "IQ")):
            return normalized
    return ""


def _display_name_for_record(record: LlamaCppModelRecord) -> str:
    if candidate := catalog_candidate_for_model_id(record.model_id):
        return candidate.label
    if record.repo_id:
        quant = f" {record.quant}" if record.quant else ""
        return f"{record.repo_id}{quant}".strip()
    if record.local_path:
        return Path(record.local_path).name
    return record.model_id


def _local_model_id(path: Path) -> str:
    safe_name = path.stem.replace(" ", "-")
    return f"{LLAMA_CPP_PROVIDER_SLUG}/local-{safe_name}"


def _normalize_local_model_id(path: Path, model_id: str | None) -> str:
    raw_model_id = (model_id or "").strip()
    if not raw_model_id:
        return _local_model_id(path)
    prefix = f"{LLAMA_CPP_PROVIDER_SLUG}/"
    suffix = raw_model_id.removeprefix(prefix).strip("/")
    if not suffix or any(character.isspace() for character in suffix):
        raise ValueError("local model id alias must be non-empty and contain no whitespace")
    return f"{prefix}{suffix}"


def _local_path_text(local_path: Path | None) -> str:
    return str(local_path.expanduser().resolve()) if local_path is not None else ""


def _save_revalidation_result(
    record: LlamaCppModelRecord,
    capability: ToolCapabilityResult,
    endpoint: str,
) -> None:
    save_model_record(
        LlamaCppModelRecord(
            model_id=record.model_id,
            repo_id=record.repo_id,
            filename=record.filename,
            quant=record.quant,
            local_path=record.local_path,
            tool_capable=capability.passed,
            endpoint=endpoint,
            created_at=record.created_at,
            last_validated_at=time.time() if capability.passed else record.last_validated_at,
        )
    )


def _server_command(
    binary: Path,
    *,
    model_id: str,
    port: int,
    hf_ref: str,
    hf_file: str,
    local_path: Path | None,
) -> list[str]:
    command = [
        str(binary),
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--alias",
        model_id,
        "--ctx-size",
        str(_DEFAULT_CONTEXT_TOKENS),
        "--jinja",
    ]
    if local_path is not None:
        command.extend(("-m", str(local_path)))
        return command
    if not hf_ref:
        raise ValueError("hf_ref or local_path is required")
    command.extend(("-hf", hf_ref))
    if hf_file:
        command.extend(("-hff", hf_file))
    return command


def _download_release_asset(asset: LlamaCppReleaseAsset) -> Path:
    _BIN_DIR.mkdir(parents=True, exist_ok=True)
    archive = _BIN_DIR / asset.name
    if archive.is_file():
        return archive
    _require_url_scheme(asset.url, ("https",))
    request = urllib.request.Request(asset.url, headers={"User-Agent": "hephaion-llama-cpp"})
    context = ssl.create_default_context(cafile=certifi.where())
    # asset.url is restricted to HTTPS before opening.
    with (
        urllib.request.urlopen(  # nosec B310
            request,
            timeout=60,
            context=context,
        ) as response,
        archive.open("wb") as file,
    ):
        shutil.copyfileobj(response, file)
    return archive


def _verify_sha256(path: Path, expected: str) -> None:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != expected:
        path.unlink(missing_ok=True)
        raise RuntimeError(f"llama.cpp release checksum mismatch for {path.name}")


def _extract_release_asset(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as zip_file:
            _extract_zip_members(zip_file, destination)
        return
    with tarfile.open(archive) as tar:
        _extract_tar_members(tar, destination)


def _extract_zip_members(zip_file: zipfile.ZipFile, destination: Path) -> None:
    for member in zip_file.infolist():
        target = _validate_archive_target(destination, member.filename)
        mode = member.external_attr >> 16
        if stat.S_ISLNK(mode):
            raise RuntimeError(f"unsafe llama.cpp archive member: {member.filename}")
        if member.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with zip_file.open(member) as source, target.open("wb") as file:
            shutil.copyfileobj(source, file)
        if mode:
            target.chmod(mode & 0o777)


def _extract_tar_members(tar: tarfile.TarFile, destination: Path) -> None:
    for member in tar.getmembers():
        target = _validate_archive_target(destination, member.name)
        if member.isdir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        if member.issym():
            _extract_tar_symlink(member, target, destination)
            continue
        if not member.isfile():
            raise RuntimeError(f"unsafe llama.cpp archive member: {member.name}")
        source = tar.extractfile(member)
        if source is None:
            raise RuntimeError(f"llama.cpp archive member could not be read: {member.name}")
        target.parent.mkdir(parents=True, exist_ok=True)
        with source, target.open("wb") as file:
            shutil.copyfileobj(source, file)
        target.chmod(member.mode & 0o777)


def _extract_tar_symlink(member: tarfile.TarInfo, target: Path, destination: Path) -> None:
    _validate_archive_symlink_target(destination, target, member.linkname, member.name)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        target.unlink()
    target.symlink_to(member.linkname)


def _validate_archive_target(destination: Path, member_name: str) -> Path:
    target = (destination / member_name).resolve()
    if not target.is_relative_to(destination.resolve()):
        raise RuntimeError(f"unsafe llama.cpp archive member: {member_name}")
    return target


def _validate_archive_symlink_target(
    destination: Path,
    target: Path,
    linkname: str,
    member_name: str,
) -> None:
    link_path = Path(linkname)
    if not linkname or link_path.is_absolute():
        raise RuntimeError(f"unsafe llama.cpp archive member: {member_name}")
    resolved = (target.parent / link_path).resolve(strict=False)
    if not resolved.is_relative_to(destination.resolve()):
        raise RuntimeError(f"unsafe llama.cpp archive member: {member_name}")


def _require_url_scheme(url: str, schemes: tuple[str, ...]) -> None:
    scheme = urllib.parse.urlparse(url).scheme.lower()
    if scheme not in schemes:
        expected = ", ".join(schemes)
        raise ValueError(f"llama.cpp URL must use {expected}: {url}")


def _llama_server_path() -> Path | None:
    names = ("llama-server.exe", "llama-server")
    for name in names:
        for path in _BIN_DIR.rglob(name):
            if path.is_file():
                return path
    return None


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server(server: LlamaCppServerState) -> bool:
    deadline = time.time() + _SERVER_START_TIMEOUT_SECONDS
    while time.time() < deadline:
        if server_is_ready(server):
            return True
        if not _pid_running(server.pid):
            return False
        time.sleep(0.5)
    return False


def _remember_managed_process(process: subprocess.Popen[bytes]) -> None:
    global _MANAGED_SERVER_PROCESS  # noqa: PLW0603
    _MANAGED_SERVER_PROCESS = process


def _managed_process_for_pid(pid: int) -> subprocess.Popen[bytes] | None:
    process = _MANAGED_SERVER_PROCESS
    if process is None or process.pid != pid:
        return None
    return process


def _clear_managed_process(process: subprocess.Popen[bytes]) -> None:
    global _MANAGED_SERVER_PROCESS  # noqa: PLW0603
    if _MANAGED_SERVER_PROCESS is process:
        _MANAGED_SERVER_PROCESS = None


def _terminate_process(process: subprocess.Popen[bytes]) -> bool:
    try:
        process.terminate()
        process.wait(timeout=5.0)
    except subprocess.TimeoutExpired:
        try:
            process.kill()
            process.wait(timeout=5.0)
        except (OSError, subprocess.TimeoutExpired):
            return process.poll() is not None
    except OSError:
        return process.poll() is not None
    return True


def _terminate_pid(pid: int) -> bool:
    if not _pid_running(pid):
        return False
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return not _pid_running(pid)
    if _wait_for_pid_exit(pid, timeout_seconds=_PID_STOP_GRACE_SECONDS):
        return True

    kill_signal = getattr(signal, "SIGKILL", signal.SIGTERM)
    try:
        os.kill(pid, kill_signal)
    except OSError:
        return not _pid_running(pid)
    return _wait_for_pid_exit(pid, timeout_seconds=_PID_STOP_KILL_GRACE_SECONDS)


def _terminate_managed_server(server: LlamaCppServerState) -> bool:
    if not _pid_running(server.pid):
        return False
    if process := _managed_process_for_pid(server.pid):
        stopped = _terminate_process(process)
        if stopped:
            _clear_managed_process(process)
        return stopped
    if not _pid_looks_like_llama_server(server.pid):
        return False
    return _terminate_pid(server.pid)


def _server_state_pid_is_managed(server: LlamaCppServerState) -> bool:
    if not _pid_running(server.pid):
        return False
    return _managed_process_for_pid(server.pid) is not None or _pid_looks_like_llama_server(
        server.pid
    )


def _wait_for_pid_exit(pid: int, *, timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not _pid_running(pid):
            return True
        time.sleep(_PID_STOP_POLL_SECONDS)
    return not _pid_running(pid)


def _pid_looks_like_llama_server(pid: int) -> bool:
    if platform.system() == "Windows":
        return _windows_pid_looks_like_llama_server(pid)
    ps = shutil.which("ps")
    if ps is None:
        return False
    try:
        completed = subprocess.run(
            [ps, "-p", str(pid), "-o", "comm="],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=1.0,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    if completed.returncode != 0:
        return False
    command_name = Path(completed.stdout.strip()).name
    return command_name in {"llama-server", "llama-server.exe"}


def _windows_pid_looks_like_llama_server(pid: int) -> bool:
    completed = _run_windows_tasklist(pid)
    return completed is not None and _tasklist_stdout_has_llama_server(completed.stdout, pid)


def _run_windows_tasklist(pid: int) -> subprocess.CompletedProcess[str] | None:
    tasklist = shutil.which("tasklist")
    if tasklist is None:
        return None
    try:
        result = subprocess.run(
            [tasklist, "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=1.0,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result


def _tasklist_stdout_has_pid(stdout: str, pid: int) -> bool:
    return any(_tasklist_row_pid(row) == str(pid) for row in csv.reader(stdout.splitlines()))


def _tasklist_stdout_has_llama_server(stdout: str, pid: int) -> bool:
    for row in csv.reader(stdout.splitlines()):
        process_id = _tasklist_row_pid(row)
        if not process_id:
            continue
        image_name = Path(row[0].strip()).name
        if process_id == str(pid) and image_name in {"llama-server", "llama-server.exe"}:
            return True
    return False


def _tasklist_row_pid(row: list[str]) -> str:
    return row[1].strip() if len(row) >= 2 else ""


def _pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    if platform.system() == "Windows":
        completed = _run_windows_tasklist(pid)
        return completed is not None and _tasklist_stdout_has_pid(completed.stdout, pid)
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _probe_tool_schema() -> dict[str, object]:
    return {
        "type": "function",
        "function": {
            "name": "heph_probe_echo",
            "description": "Return the requested validation marker.",
            "parameters": {
                "type": "object",
                "properties": {"value": {"type": "string"}},
                "required": ["value"],
                "additionalProperties": False,
            },
        },
    }


def _tool_capability_from_response(response: dict[str, object]) -> ToolCapabilityResult:
    choices = response.get("choices")
    if not is_object_list(choices):
        return ToolCapabilityResult(False, "probe response did not include choices")
    if not choices:
        return ToolCapabilityResult(False, "probe response did not include choices")
    first = choices[0]
    if not is_string_mapping(first):
        return ToolCapabilityResult(False, "probe choice was malformed")
    message = first.get("message")
    if not is_string_mapping(message):
        return ToolCapabilityResult(False, "probe choice did not include a message")
    tool_calls = message.get("tool_calls")
    if not is_object_list(tool_calls):
        return ToolCapabilityResult(False, "model did not return a tool call")
    if not tool_calls:
        return ToolCapabilityResult(False, "model did not return a tool call")
    call = tool_calls[0]
    if not is_string_mapping(call):
        return ToolCapabilityResult(False, "tool call was malformed")
    function = call.get("function")
    if not is_string_mapping(function):
        return ToolCapabilityResult(False, "tool call did not include a function")
    if function.get("name") != "heph_probe_echo":
        return ToolCapabilityResult(False, "tool call used the wrong function")
    raw_arguments = function.get("arguments")
    if not isinstance(raw_arguments, str):
        return ToolCapabilityResult(False, "tool call arguments were not JSON text")
    try:
        arguments = json.loads(raw_arguments)
    except json.JSONDecodeError:
        return ToolCapabilityResult(False, "tool call arguments were not valid JSON")
    if not is_string_mapping(arguments) or arguments.get("value") != "ready":
        return ToolCapabilityResult(False, "tool call arguments failed validation")
    return ToolCapabilityResult(True)


def _models_response_includes(response: dict[str, object] | None, model_id: str) -> bool:
    if response is None:
        return False
    data = response.get("data")
    if not is_object_list(data):
        return False
    return any(
        is_string_mapping(item) and _models_response_item_matches(item, model_id) for item in data
    )


def _models_response_item_matches(item: dict[str, object], model_id: str) -> bool:
    if item.get("id") == model_id:
        return True
    aliases = item.get("aliases")
    if not isinstance(aliases, list):
        return False
    return any(isinstance(alias, str) and alias == model_id for alias in aliases)


def _post_json(url: str, payload: Mapping[str, object]) -> dict[str, object] | None:
    body = json.dumps(payload).encode("utf-8")
    try:
        _require_url_scheme(url, ("http", "https"))
        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Authorization": "Bearer no-key-required",
                "Content-Type": "application/json",
                "User-Agent": "hephaion-llama-cpp",
            },
            method="POST",
        )
        # url is restricted to HTTP(S) before opening.
        with urllib.request.urlopen(  # nosec B310
            request,
            timeout=_PROBE_TIMEOUT_SECONDS,
        ) as response:
            parsed = json.loads(response.read().decode("utf-8"))
    except (ValueError, OSError, urllib.error.URLError, json.JSONDecodeError):
        return None
    return parsed if is_string_mapping(parsed) else None


def _get_json(url: str, *, timeout: float) -> dict[str, object] | None:
    try:
        _require_url_scheme(url, ("http", "https"))
        # url is restricted to HTTP(S) before opening.
        with urllib.request.urlopen(  # nosec B310
            url,
            timeout=timeout,
        ) as response:
            parsed = json.loads(response.read().decode("utf-8"))
    except (ValueError, OSError, urllib.error.URLError, json.JSONDecodeError):
        return None
    return parsed if is_string_mapping(parsed) else None


def _load_state() -> _LlamaCppState:
    if not _STATE_FILE.is_file():
        return _LlamaCppState(records=[])
    try:
        payload = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _LlamaCppState(records=[])
    if not is_string_mapping(payload):
        return _LlamaCppState(records=[])
    return _LlamaCppState(
        records=_records_from_payload(payload.get("records")),
        server=_server_from_payload(payload.get("server")),
    )


def _save_state(state: _LlamaCppState) -> None:
    payload: dict[str, object] = {
        "records": [_record_payload(record) for record in state.records],
    }
    if state.server is not None:
        payload["server"] = _server_payload(state.server)
    _ensure_private_state_dir()
    _write_private_state_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _ensure_private_state_dir() -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True, mode=_STATE_DIR_MODE)
    _CONFIG_DIR.chmod(_STATE_DIR_MODE)


def _write_private_state_text(text: str) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(str(_STATE_FILE), flags, _STATE_FILE_MODE)
    try:
        _set_private_state_file_mode(fd)
    except Exception:
        os.close(fd)
        raise
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        file.write(text)


def _set_private_state_file_mode(fd: int) -> None:
    try:
        os.fchmod(fd, _STATE_FILE_MODE)
    except AttributeError:
        _STATE_FILE.chmod(_STATE_FILE_MODE)


def _replace_server(
    state: _LlamaCppState,
    server: LlamaCppServerState | None,
) -> _LlamaCppState:
    return _LlamaCppState(records=state.records, server=server)


def _records_from_payload(raw_records: object) -> list[LlamaCppModelRecord]:
    if not is_object_list(raw_records):
        return []
    return [
        record
        for raw_record in raw_records
        if is_string_mapping(raw_record)
        if (record := _record_from_payload(raw_record)) is not None
    ]


def _record_from_payload(payload: dict[str, object]) -> LlamaCppModelRecord | None:
    model_id = _str_field(payload, "model_id")
    if not model_id:
        return None
    return LlamaCppModelRecord(
        model_id=model_id,
        repo_id=_str_field(payload, "repo_id"),
        filename=_str_field(payload, "filename"),
        quant=_str_field(payload, "quant"),
        local_path=_str_field(payload, "local_path"),
        tool_capable=bool(payload.get("tool_capable", False)),
        endpoint=_str_field(payload, "endpoint") or LLAMA_CPP_DEFAULT_BASE_URL,
        created_at=_float_field(payload, "created_at"),
        last_validated_at=_float_field(payload, "last_validated_at"),
    )


def _server_from_payload(payload: object) -> LlamaCppServerState | None:
    if not is_string_mapping(payload):
        return None
    pid = payload.get("pid")
    endpoint = _str_field(payload, "endpoint")
    model_id = _str_field(payload, "model_id")
    if not isinstance(pid, int) or not endpoint or not model_id:
        return None
    return LlamaCppServerState(
        pid=pid,
        endpoint=endpoint,
        model_id=model_id,
        started_at=_float_field(payload, "started_at"),
        hf_ref=_str_field(payload, "hf_ref"),
        hf_file=_str_field(payload, "hf_file"),
        local_path=_str_field(payload, "local_path"),
    )


def _record_payload(record: LlamaCppModelRecord) -> dict[str, object]:
    return {
        "model_id": record.model_id,
        "repo_id": record.repo_id,
        "filename": record.filename,
        "quant": record.quant,
        "local_path": record.local_path,
        "tool_capable": record.tool_capable,
        "endpoint": record.endpoint,
        "created_at": record.created_at,
        "last_validated_at": record.last_validated_at,
    }


def _server_payload(server: LlamaCppServerState) -> dict[str, object]:
    return {
        "pid": server.pid,
        "endpoint": server.endpoint,
        "model_id": server.model_id,
        "started_at": server.started_at,
        "hf_ref": server.hf_ref,
        "hf_file": server.hf_file,
        "local_path": server.local_path,
    }


def _str_field(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    return value if isinstance(value, str) else ""


def _float_field(payload: dict[str, object], key: str) -> float:
    value = payload.get(key)
    return float(value) if isinstance(value, int | float) else 0.0


def _normalize_endpoint(base_url: str) -> str:
    return base_url.strip().rstrip("/")


def _format_bytes(size: int) -> str:
    if size <= 0:
        return ""
    units = ("B", "KB", "MB", "GB", "TB")
    value = float(size)
    unit = units[0]
    for unit in units:
        if value < 1024 or unit == units[-1]:
            break
        value /= 1024
    return f"{value:.1f}{unit}"
