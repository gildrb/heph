from __future__ import annotations

import hashlib
import io
import json
import signal
import stat
import subprocess
import sys
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

import pytest
from ai.providers import llama_cpp
from ai.providers.config import default_config
from ai.providers.endpoints import is_keyless_endpoint, provider_uses_keyless_access
from ai.providers.llama_cpp import (
    LLAMA_CPP_DEFAULT_BASE_URL,
    LLAMA_CPP_DISPLAY_NAME,
    LLAMA_CPP_PROVIDER_SLUG,
    LlamaCppModelRecord,
    LlamaCppServerState,
    ToolCapabilityResult,
)
from ai.runtime import ChatConfig, EngineError, build_client


@dataclass(frozen=True)
class _IsolatedLlamaPaths:
    config_dir: Path
    cache_dir: Path
    state_file: Path
    model_cache_dir: Path


@dataclass(frozen=True)
class _Sibling:
    rfilename: str
    size: int = 0
    lfs: dict[str, object] | None = None


@dataclass(frozen=True)
class _Model:
    id: str
    siblings: list[_Sibling]
    downloads: int = 0
    likes: int = 0


def _isolate_llama_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> _IsolatedLlamaPaths:
    config_dir = tmp_path / "config"
    cache_dir = tmp_path / "cache"
    model_cache_dir = cache_dir / "models"
    state_file = config_dir / "llama_cpp.json"
    monkeypatch.setattr(llama_cpp, "_CONFIG_DIR", config_dir)
    monkeypatch.setattr(llama_cpp, "_CACHE_DIR", cache_dir)
    monkeypatch.setattr(llama_cpp, "_STATE_FILE", state_file)
    monkeypatch.setattr(llama_cpp, "_BIN_DIR", cache_dir / "bin")
    monkeypatch.setattr(llama_cpp, "_MODEL_CACHE_DIR", model_cache_dir)
    monkeypatch.setattr(llama_cpp, "_LOG_FILE", cache_dir / "llama-server.log")
    monkeypatch.setattr(llama_cpp, "_MANAGED_SERVER_PROCESS", None)
    return _IsolatedLlamaPaths(
        config_dir=config_dir,
        cache_dir=cache_dir,
        state_file=state_file,
        model_cache_dir=model_cache_dir,
    )


def test_default_config_includes_keyless_llama_cpp_provider() -> None:
    config = default_config()
    provider = config.providers[LLAMA_CPP_PROVIDER_SLUG]

    assert provider.display_name == LLAMA_CPP_DISPLAY_NAME
    assert provider.endpoint == LLAMA_CPP_DEFAULT_BASE_URL
    assert provider.api_key_env == ""
    assert provider.models == []
    assert provider_uses_keyless_access(provider.slug, provider.endpoint)


def test_build_client_allows_loopback_llama_cpp_without_api_key() -> None:
    config = ChatConfig(
        api_key="",
        base_url="http://127.0.0.1:18888/v1",
        model="llama-cpp/acme-model:Q4_K_M",
    )
    config.apply_provider_reference(LLAMA_CPP_PROVIDER_SLUG, "")

    client = build_client(config)

    assert client.api_key == "no-key-required"
    assert str(client.base_url) == "http://127.0.0.1:18888/v1/"


def test_llama_cpp_keyless_access_requires_loopback_endpoint() -> None:
    assert not provider_uses_keyless_access(
        LLAMA_CPP_PROVIDER_SLUG,
        "https://example.com/v1",
    )


def test_build_client_rejects_external_llama_cpp_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HEPHAION_API_KEY", raising=False)
    config = ChatConfig(
        api_key="",
        base_url="https://example.com/v1",
        model="llama-cpp/acme-model:Q4_K_M",
    )
    config.apply_provider_reference(LLAMA_CPP_PROVIDER_SLUG, "")

    with pytest.raises(EngineError, match="No API key found"):
        build_client(config)


def test_custom_loopback_endpoint_keeps_configured_api_key() -> None:
    config = ChatConfig(
        api_key="local-secret",
        base_url="http://127.0.0.1:18888/v1",
        model="private-model",
    )

    client = build_client(config)

    assert not is_keyless_endpoint(config.base_url)
    assert client.api_key == "local-secret"


def test_state_persists_only_tool_capable_model_choices(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _isolate_llama_paths(monkeypatch, tmp_path)
    passing = LlamaCppModelRecord(
        model_id="llama-cpp/acme/pass:Q4_K_M",
        repo_id="acme/pass",
        quant="Q4_K_M",
        tool_capable=True,
    )
    failing = LlamaCppModelRecord(
        model_id="llama-cpp/acme/fail:Q4_K_M",
        repo_id="acme/fail",
        quant="Q4_K_M",
        tool_capable=False,
    )

    llama_cpp.save_model_record(failing)
    llama_cpp.save_model_record(passing)

    assert paths.state_file.is_file()
    assert llama_cpp.installed_model_ids() == [passing.model_id]
    assert [record.model_id for record in llama_cpp.installed_records()] == [
        failing.model_id,
        passing.model_id,
    ]


def test_state_file_uses_private_permissions(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _isolate_llama_paths(monkeypatch, tmp_path)
    paths.config_dir.mkdir(parents=True, mode=0o755)
    paths.config_dir.chmod(0o755)

    llama_cpp.save_model_record(
        LlamaCppModelRecord(
            model_id="llama-cpp/acme/private:Q4_K_M",
            repo_id="acme/private",
            quant="Q4_K_M",
            tool_capable=True,
        )
    )

    assert stat.S_IMODE(paths.config_dir.stat().st_mode) == 0o700
    assert stat.S_IMODE(paths.state_file.stat().st_mode) == 0o600


def test_state_file_write_falls_back_when_fchmod_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _isolate_llama_paths(monkeypatch, tmp_path)
    monkeypatch.delattr(llama_cpp.os, "fchmod", raising=False)

    llama_cpp.save_model_record(
        LlamaCppModelRecord(
            model_id="llama-cpp/acme/windows:Q4_K_M",
            repo_id="acme/windows",
            quant="Q4_K_M",
            tool_capable=True,
        )
    )

    assert paths.state_file.is_file()
    assert llama_cpp.installed_model_ids() == ["llama-cpp/acme/windows:Q4_K_M"]


def test_search_gguf_models_returns_curated_catalog() -> None:
    candidates = llama_cpp.search_gguf_models("", limit=100)

    assert candidates
    assert candidates[0].repo_id == "LiquidAI/LFM2-350M-GGUF"
    assert candidates[0].display_name == "LFM2 350M"
    assert len(candidates) >= 17
    assert all(candidate.downloads == 0 for candidate in candidates)
    assert all(candidate.likes == 0 for candidate in candidates)
    assert all(0 < candidate.recommended_ram_gb <= 16 for candidate in candidates)
    assert len([candidate for candidate in candidates if candidate.recommended_ram_gb <= 6]) >= 10
    assert llama_cpp.search_gguf_models("andycurrent", limit=10) == []
    assert [
        candidate.repo_id for candidate in llama_cpp.search_gguf_models("gemma", limit=10)
    ] == [
        "google/gemma-4-E2B-it-qat-q4_0-gguf",
        "google/gemma-4-E4B-it-qat-q4_0-gguf",
        "google/gemma-4-12B-it-qat-q4_0-gguf",
    ]


def test_find_gguf_model_honors_curated_requested_quant() -> None:
    candidate = llama_cpp.find_gguf_model("Qwen/Qwen3-4B-GGUF", quant="Q4_K_M")

    assert candidate is not None
    assert candidate.filename == "Qwen3-4B-Q4_K_M.gguf"
    assert candidate.model_id == "llama-cpp/Qwen/Qwen3-4B-GGUF:Q4_K_M"
    assert llama_cpp.find_gguf_model("Qwen/Qwen3-4B-GGUF", quant="Q8_0") is None
    assert llama_cpp.find_gguf_model("Andyvurrent/Gemma-3-1B-Heretic-GGUF") is None


def test_find_hf_candidate_accepts_repo_quant_targets() -> None:
    candidate = llama_cpp.find_hf_candidate("Qwen/Qwen3-4B-GGUF:Q4_K_M")

    assert candidate is not None
    assert candidate.filename == "Qwen3-4B-Q4_K_M.gguf"
    assert llama_cpp.find_hf_candidate(candidate.repo_id) == candidate
    assert llama_cpp.find_hf_candidate("Andyvurrent/Gemma-3-1B-Heretic-GGUF") is None


def test_find_hf_candidate_accepts_ministral_catalog_targets() -> None:
    three_b = llama_cpp.find_hf_candidate("mistralai/Ministral-3-3B-Instruct-2512-GGUF:Q4_K_M")
    eight_b = llama_cpp.find_hf_candidate("mistralai/Ministral-3-8B-Instruct-2512-GGUF:Q4_K_M")

    assert three_b is not None
    assert three_b.filename == "Ministral-3-3B-Instruct-2512-Q4_K_M.gguf"
    assert three_b.hf_ref == "mistralai/Ministral-3-3B-Instruct-2512-GGUF:Q4_K_M"
    assert eight_b is not None
    assert eight_b.filename == "Ministral-3-8B-Instruct-2512-Q4_K_M.gguf"
    assert eight_b.hf_ref == "mistralai/Ministral-3-8B-Instruct-2512-GGUF:Q4_K_M"


def test_probe_tool_capability_accepts_valid_tool_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payloads: list[dict[str, object]] = []

    def fake_post_json(_url: str, payload: dict[str, object]) -> dict[str, object]:
        payloads.append(payload)
        return {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "heph_probe_echo",
                                    "arguments": json.dumps({"value": "ready"}),
                                }
                            }
                        ]
                    }
                }
            ]
        }

    monkeypatch.setattr(llama_cpp, "_post_json", fake_post_json)

    result = llama_cpp.probe_tool_capability(
        "http://127.0.0.1:18080/v1",
        "llama-cpp/acme/model:Q4_K_M",
    )

    assert result.passed is True
    assert payloads[0]["tool_choice"] == {
        "type": "function",
        "function": {"name": "heph_probe_echo"},
    }


@pytest.mark.parametrize(
    ("response", "reason"),
    [
        ({"choices": []}, "probe response did not include choices"),
        ({"choices": [{"message": {"content": "ready"}}]}, "model did not return a tool call"),
        ({"choices": [{"message": {"tool_calls": []}}]}, "model did not return a tool call"),
        (
            {
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "function": {
                                        "name": "heph_probe_echo",
                                        "arguments": "{",
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
            "tool call arguments were not valid JSON",
        ),
    ],
)
def test_probe_tool_capability_rejects_invalid_tool_responses(
    monkeypatch: pytest.MonkeyPatch,
    response: dict[str, object],
    reason: str,
) -> None:
    monkeypatch.setattr(llama_cpp, "_post_json", lambda _url, _payload: response)

    result = llama_cpp.probe_tool_capability(
        "http://127.0.0.1:18080/v1",
        "llama-cpp/acme/model:Q4_K_M",
    )

    assert result.passed is False
    assert result.reason == reason


def test_release_asset_selection_and_cache_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _isolate_llama_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(llama_cpp.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(llama_cpp.platform, "machine", lambda: "arm64")

    asset = llama_cpp.release_asset_for_current_platform()

    assert asset.name == "llama-b9585-bin-macos-arm64.tar.gz"
    assert llama_cpp.llama_cpp_cache_dir() == paths.cache_dir
    assert llama_cpp.llama_cpp_model_cache_dir() == paths.model_cache_dir
    assert llama_cpp.llama_cpp_state_file() == paths.state_file


def test_checksum_verification_rejects_modified_release_asset(tmp_path: Path) -> None:
    archive = tmp_path / "llama.tar.gz"
    archive.write_bytes(b"modified")
    expected = hashlib.sha256(b"official").hexdigest()

    with pytest.raises(RuntimeError, match="checksum mismatch"):
        llama_cpp._verify_sha256(archive, expected)

    assert not archive.exists()


def test_extract_release_asset_rejects_zip_path_escape(tmp_path: Path) -> None:
    archive = tmp_path / "llama.zip"
    with zipfile.ZipFile(archive, "w") as zip_file:
        zip_file.writestr("../owned", "owned")

    with pytest.raises(RuntimeError, match="unsafe llama\\.cpp archive member"):
        llama_cpp._extract_release_asset(archive, tmp_path / "extract")

    assert not (tmp_path / "owned").exists()


def test_extract_release_asset_allows_safe_tar_symlink(tmp_path: Path) -> None:
    probe_target = tmp_path / "probe-target"
    probe_link = tmp_path / "probe-link"
    probe_target.write_text("ok", encoding="utf-8")
    try:
        probe_link.symlink_to(probe_target.name)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")
    probe_link.unlink()

    archive = tmp_path / "llama.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        payload = b"library"
        file_member = tarfile.TarInfo("llama-b9585/libllama.so.0")
        file_member.size = len(payload)
        tar.addfile(file_member, io.BytesIO(payload))
        link_member = tarfile.TarInfo("llama-b9585/libllama.so")
        link_member.type = tarfile.SYMTYPE
        link_member.linkname = "libllama.so.0"
        tar.addfile(link_member)

    destination = tmp_path / "extract"
    llama_cpp._extract_release_asset(archive, destination)

    link = destination / "llama-b9585" / "libllama.so"
    assert link.is_symlink()
    assert link.readlink() == Path("libllama.so.0")
    assert link.read_bytes() == b"library"


def test_extract_release_asset_rejects_tar_link_member(tmp_path: Path) -> None:
    archive = tmp_path / "llama.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        member = tarfile.TarInfo("llama-server")
        member.type = tarfile.SYMTYPE
        member.linkname = "../owned"
        tar.addfile(member)

    with pytest.raises(RuntimeError, match="unsafe llama\\.cpp archive member"):
        llama_cpp._extract_release_asset(archive, tmp_path / "extract")

    assert not (tmp_path / "owned").exists()


def test_llama_http_helpers_reject_non_http_urls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        llama_cpp.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: pytest.fail("urlopen should not be called"),
    )

    assert llama_cpp._get_json("file:///tmp/model.json", timeout=1.0) is None
    assert llama_cpp._post_json("file:///tmp/model.json", {"value": "ready"}) is None


def test_llama_server_path_ignores_unmanaged_path_binary(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _isolate_llama_paths(monkeypatch, tmp_path)
    path_bin = tmp_path / "path-bin"
    path_bin.mkdir()
    (path_bin / "llama-server").write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.setenv("PATH", str(path_bin))

    assert llama_cpp._llama_server_path() is None

    cached = paths.cache_dir / "bin" / "release" / "llama-server"
    cached.parent.mkdir(parents=True)
    cached.write_text("#!/bin/sh\n", encoding="utf-8")

    assert llama_cpp._llama_server_path() == cached


def test_server_command_uses_loopback_alias_hf_and_cache_file_selection() -> None:
    command = llama_cpp._server_command(
        Path("/opt/llama-server"),
        model_id="llama-cpp/acme/model:Q4_K_M",
        port=18081,
        hf_ref="acme/model-GGUF:Q4_K_M",
        hf_file="model-Q4_K_M.gguf",
        local_path=None,
    )

    assert command == [
        "/opt/llama-server",
        "--host",
        "127.0.0.1",
        "--port",
        "18081",
        "--alias",
        "llama-cpp/acme/model:Q4_K_M",
        "--ctx-size",
        "8192",
        "--jinja",
        "-hf",
        "acme/model-GGUF:Q4_K_M",
        "-hff",
        "model-Q4_K_M.gguf",
    ]


def test_install_local_target_uses_local_path_and_alias(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    model_path = tmp_path / "local.gguf"
    model_path.write_bytes(b"gguf")
    result = llama_cpp.LlamaCppInstallResult(
        record=LlamaCppModelRecord(model_id="llama-cpp/custom"),
        capability=ToolCapabilityResult(True),
        server=LlamaCppServerState(
            pid=12345,
            endpoint=LLAMA_CPP_DEFAULT_BASE_URL,
            model_id="",
            started_at=1.0,
        ),
    )
    calls: list[tuple[Path, str | None]] = []

    def fake_install_local_model(
        path: Path,
        *,
        model_id: str | None = None,
    ) -> llama_cpp.LlamaCppInstallResult:
        calls.append((path, model_id))
        return result

    monkeypatch.setattr(llama_cpp, "install_local_model", fake_install_local_model)

    assert llama_cpp.install_local_target(str(model_path), model_id="custom") is result
    assert calls == [(model_path, "custom")]


def test_install_local_target_uses_hf_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    candidate = llama_cpp.find_hf_candidate("Qwen/Qwen3-4B-GGUF:Q4_K_M")
    assert candidate is not None
    result = llama_cpp.LlamaCppInstallResult(
        record=LlamaCppModelRecord(model_id=candidate.model_id),
        capability=ToolCapabilityResult(True),
        server=LlamaCppServerState(
            pid=12345,
            endpoint=LLAMA_CPP_DEFAULT_BASE_URL,
            model_id="",
            started_at=1.0,
        ),
    )
    calls: list[llama_cpp.LlamaCppCandidate] = []

    def fake_install_hf_model(
        selected_candidate: llama_cpp.LlamaCppCandidate,
    ) -> llama_cpp.LlamaCppInstallResult:
        calls.append(selected_candidate)
        return result

    monkeypatch.setattr(llama_cpp, "install_hf_model", fake_install_hf_model)

    assert llama_cpp.install_local_target(candidate.hf_ref) is result
    assert calls == [candidate]


def test_install_local_model_namespaces_custom_alias(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _isolate_llama_paths(monkeypatch, tmp_path)
    model_path = tmp_path / "local.gguf"
    model_path.write_bytes(b"gguf")
    started_model_ids: list[str] = []

    def fake_start_llama_server(
        *,
        model_id: str,
        hf_ref: str = "",
        hf_file: str = "",
        local_path: Path | None = None,
        port: int | None = None,
    ) -> LlamaCppServerState:
        started_model_ids.append(model_id)
        assert hf_ref == ""
        assert hf_file == ""
        assert local_path == model_path
        assert port is None
        return LlamaCppServerState(
            pid=12345,
            endpoint="http://127.0.0.1:18080/v1",
            model_id=model_id,
            started_at=1.0,
        )

    monkeypatch.setattr(llama_cpp, "start_llama_server", fake_start_llama_server)
    monkeypatch.setattr(
        llama_cpp,
        "probe_tool_capability",
        lambda _endpoint, _model_id: ToolCapabilityResult(True),
    )

    result = llama_cpp.install_local_model(model_path, model_id="my-model")

    assert result.record.model_id == "llama-cpp/my-model"
    assert started_model_ids == ["llama-cpp/my-model"]
    assert llama_cpp.installed_model_ids() == ["llama-cpp/my-model"]


def test_install_local_model_stops_failed_tool_probe(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _isolate_llama_paths(monkeypatch, tmp_path)
    model_path = tmp_path / "local.gguf"
    model_path.write_bytes(b"gguf")
    stopped: list[bool] = []

    def fake_start_llama_server(
        *,
        model_id: str,
        hf_ref: str = "",
        hf_file: str = "",
        local_path: Path | None = None,
        port: int | None = None,
    ) -> LlamaCppServerState:
        assert model_id == "llama-cpp/local"
        assert hf_ref == ""
        assert hf_file == ""
        assert local_path == model_path
        assert port is None
        return LlamaCppServerState(
            pid=12345,
            endpoint="http://127.0.0.1:18080/v1",
            model_id=model_id,
            started_at=1.0,
        )

    monkeypatch.setattr(llama_cpp, "start_llama_server", fake_start_llama_server)
    monkeypatch.setattr(
        llama_cpp,
        "probe_tool_capability",
        lambda _endpoint, _model_id: ToolCapabilityResult(False, "no tool call"),
    )
    monkeypatch.setattr(llama_cpp, "stop_llama_server", lambda: stopped.append(True) or True)

    result = llama_cpp.install_local_model(model_path, model_id="local")

    assert result.capability.passed is False
    assert result.record.tool_capable is False
    assert llama_cpp.installed_model_ids() == []
    assert [record.model_id for record in llama_cpp.installed_records()] == ["llama-cpp/local"]
    assert stopped == [True]


def test_install_hf_model_stops_failed_tool_probe(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _isolate_llama_paths(monkeypatch, tmp_path)
    candidate = llama_cpp.LlamaCppCandidate(
        repo_id="acme/model-GGUF",
        filename="model-Q4_K_M.gguf",
        quant="Q4_K_M",
        downloads=12,
        likes=3,
        size_bytes=1024,
    )
    stopped: list[bool] = []

    def fake_start_llama_server(
        *,
        model_id: str,
        hf_ref: str = "",
        hf_file: str = "",
        local_path: Path | None = None,
        port: int | None = None,
    ) -> LlamaCppServerState:
        assert model_id == candidate.model_id
        assert hf_ref == candidate.hf_ref
        assert hf_file == candidate.filename
        assert local_path is None
        assert port is None
        return LlamaCppServerState(
            pid=12345,
            endpoint="http://127.0.0.1:18080/v1",
            model_id=model_id,
            started_at=1.0,
        )

    monkeypatch.setattr(llama_cpp, "start_llama_server", fake_start_llama_server)
    monkeypatch.setattr(
        llama_cpp,
        "probe_tool_capability",
        lambda _endpoint, _model_id: ToolCapabilityResult(False, "no tool call"),
    )
    monkeypatch.setattr(llama_cpp, "stop_llama_server", lambda: stopped.append(True) or True)

    result = llama_cpp.install_hf_model(candidate)

    assert result.capability.passed is False
    assert result.record.tool_capable is False
    assert stopped == [True]


def test_start_llama_server_restarts_same_alias_for_different_local_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _isolate_llama_paths(monkeypatch, tmp_path)
    old_model = (tmp_path / "old.gguf").resolve()
    new_model = (tmp_path / "new.gguf").resolve()
    server = LlamaCppServerState(
        pid=12345,
        endpoint="http://127.0.0.1:18080/v1",
        model_id="llama-cpp/shared",
        started_at=1.0,
        local_path=str(old_model),
    )
    commands: list[list[str]] = []
    stopped: list[bool] = []

    class _FakeProcess:
        pid = 67890

    monkeypatch.setattr(llama_cpp, "_managed_server_state", lambda: server)
    monkeypatch.setattr(llama_cpp, "server_is_ready", lambda _server: True)
    monkeypatch.setattr(llama_cpp, "stop_llama_server", lambda: stopped.append(True) or True)
    monkeypatch.setattr(llama_cpp, "ensure_llama_server", lambda: tmp_path / "llama-server")
    monkeypatch.setattr(llama_cpp, "_find_free_port", lambda: 18081)
    monkeypatch.setattr(llama_cpp, "_wait_for_server", lambda _server: True)

    def fake_popen(command: list[str], **_kwargs: object) -> _FakeProcess:
        commands.append(command)
        return _FakeProcess()

    monkeypatch.setattr(llama_cpp.subprocess, "Popen", fake_popen)

    result = llama_cpp.start_llama_server(model_id="llama-cpp/shared", local_path=new_model)

    assert stopped == [True]
    assert result.pid == 67890
    assert result.local_path == str(new_model)
    assert commands
    assert str(new_model) in commands[0]


def test_revalidate_model_reports_startup_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _isolate_llama_paths(monkeypatch, tmp_path)
    record = LlamaCppModelRecord(
        model_id="llama-cpp/local-missing",
        local_path=str(tmp_path / "missing.gguf"),
        tool_capable=True,
        endpoint="http://127.0.0.1:18080/v1",
    )
    llama_cpp.save_model_record(record)

    def fail_start(_record: LlamaCppModelRecord) -> LlamaCppServerState:
        raise FileNotFoundError("missing.gguf")

    monkeypatch.setattr(llama_cpp, "start_record", fail_start)

    result = llama_cpp.revalidate_model(record.model_id)
    saved = llama_cpp.model_record(record.model_id)

    assert result.passed is False
    assert result.reason == "model could not be started: missing.gguf"
    assert saved is not None
    assert saved.tool_capable is False


def test_revalidate_model_stops_failed_tool_probe(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _isolate_llama_paths(monkeypatch, tmp_path)
    record = LlamaCppModelRecord(
        model_id="llama-cpp/local",
        local_path=str(tmp_path / "local.gguf"),
        tool_capable=True,
        endpoint="http://127.0.0.1:18080/v1",
    )
    llama_cpp.save_model_record(record)
    stopped: list[bool] = []

    monkeypatch.setattr(
        llama_cpp,
        "start_record",
        lambda _record: LlamaCppServerState(
            pid=12345,
            endpoint="http://127.0.0.1:18080/v1",
            model_id=record.model_id,
            started_at=1.0,
            local_path=record.local_path,
        ),
    )
    monkeypatch.setattr(
        llama_cpp,
        "probe_tool_capability",
        lambda _endpoint, _model_id: ToolCapabilityResult(False, "no tool call"),
    )
    monkeypatch.setattr(llama_cpp, "stop_llama_server", lambda: stopped.append(True) or True)

    result = llama_cpp.revalidate_model(record.model_id)
    saved = llama_cpp.model_record(record.model_id)

    assert result.passed is False
    assert saved is not None
    assert saved.tool_capable is False
    assert saved.endpoint == "http://127.0.0.1:18080/v1"
    assert stopped == [True]


def test_start_llama_server_clears_reused_stale_pid_before_starting(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _isolate_llama_paths(monkeypatch, tmp_path)
    old_model = (tmp_path / "old.gguf").resolve()
    new_model = (tmp_path / "new.gguf").resolve()
    server = LlamaCppServerState(
        pid=12345,
        endpoint="http://127.0.0.1:18080/v1",
        model_id="llama-cpp/shared",
        started_at=1.0,
        local_path=str(old_model),
    )
    llama_cpp._save_state(llama_cpp._LlamaCppState(records=[], server=server))
    commands: list[list[str]] = []

    monkeypatch.setattr(llama_cpp, "_pid_running", lambda _pid: True)
    monkeypatch.setattr(
        llama_cpp,
        "_get_json",
        lambda _url, *, timeout: {"data": [{"id": "llama-cpp/other/model:Q4_K_M"}]},
    )
    monkeypatch.setattr(llama_cpp, "_pid_looks_like_llama_server", lambda _pid: False)
    monkeypatch.setattr(llama_cpp, "ensure_llama_server", lambda: tmp_path / "llama-server")
    monkeypatch.setattr(llama_cpp, "_find_free_port", lambda: 18081)
    monkeypatch.setattr(llama_cpp, "_wait_for_server", lambda _server: True)

    class _FakeProcess:
        pid = 67890

    def fake_popen(command: list[str], **_kwargs: object) -> _FakeProcess:
        commands.append(command)
        return _FakeProcess()

    monkeypatch.setattr(llama_cpp.subprocess, "Popen", fake_popen)

    result = llama_cpp.start_llama_server(model_id="llama-cpp/shared", local_path=new_model)

    saved_state = json.loads(paths.state_file.read_text(encoding="utf-8"))
    assert result.pid == 67890
    assert saved_state["server"]["pid"] == 67890
    assert saved_state["server"]["local_path"] == str(new_model)
    assert commands
    assert str(new_model) in commands[0]


def test_start_llama_server_refuses_to_overwrite_unstopped_server(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _isolate_llama_paths(monkeypatch, tmp_path)
    old_model = (tmp_path / "old.gguf").resolve()
    new_model = (tmp_path / "new.gguf").resolve()
    server = LlamaCppServerState(
        pid=12345,
        endpoint="http://127.0.0.1:18080/v1",
        model_id="llama-cpp/shared",
        started_at=1.0,
        local_path=str(old_model),
    )
    llama_cpp._save_state(llama_cpp._LlamaCppState(records=[], server=server))
    kills: list[tuple[int, int]] = []

    monkeypatch.setattr(llama_cpp, "_PID_STOP_GRACE_SECONDS", 0.0)
    monkeypatch.setattr(llama_cpp, "_PID_STOP_KILL_GRACE_SECONDS", 0.0)
    monkeypatch.setattr(llama_cpp, "_pid_running", lambda _pid: True)
    monkeypatch.setattr(llama_cpp, "_pid_looks_like_llama_server", lambda _pid: True)
    monkeypatch.setattr(llama_cpp.os, "kill", lambda pid, sig: kills.append((pid, sig)))
    monkeypatch.setattr(
        llama_cpp,
        "ensure_llama_server",
        lambda: pytest.fail("start should not continue after an unstopped server"),
    )

    with pytest.raises(RuntimeError, match="could not be stopped"):
        llama_cpp.start_llama_server(model_id="llama-cpp/shared", local_path=new_model)

    saved_state = json.loads(paths.state_file.read_text(encoding="utf-8"))
    assert kills == [(12345, signal.SIGTERM), (12345, signal.SIGKILL)]
    assert saved_state["server"]["pid"] == server.pid
    assert saved_state["server"]["local_path"] == str(old_model)


def test_stop_llama_server_does_not_kill_unverified_pid(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _isolate_llama_paths(monkeypatch, tmp_path)
    server = LlamaCppServerState(
        pid=12345,
        endpoint="http://127.0.0.1:18080/v1",
        model_id="llama-cpp/acme/model:Q4_K_M",
        started_at=1.0,
    )
    llama_cpp._save_state(llama_cpp._LlamaCppState(records=[], server=server))
    kills: list[tuple[int, int]] = []

    monkeypatch.setattr(llama_cpp, "_pid_running", lambda _pid: True)
    monkeypatch.setattr(
        llama_cpp,
        "_get_json",
        lambda _url, *, timeout: {"data": [{"id": "llama-cpp/other/model:Q4_K_M"}]},
    )
    monkeypatch.setattr(llama_cpp, "_pid_looks_like_llama_server", lambda _pid: False)
    monkeypatch.setattr(llama_cpp.os, "kill", lambda pid, sig: kills.append((pid, sig)))

    assert llama_cpp.stop_llama_server() is False
    assert kills == []
    saved_state = json.loads(paths.state_file.read_text(encoding="utf-8"))
    assert "server" not in saved_state


def test_stop_llama_server_kills_loading_managed_server(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _isolate_llama_paths(monkeypatch, tmp_path)
    server = LlamaCppServerState(
        pid=12345,
        endpoint="http://127.0.0.1:18080/v1",
        model_id="llama-cpp/acme/model:Q4_K_M",
        started_at=1.0,
    )
    llama_cpp._save_state(llama_cpp._LlamaCppState(records=[], server=server))
    kills: list[tuple[int, int]] = []

    running = iter((True, True, True, False))
    monkeypatch.setattr(llama_cpp, "_pid_running", lambda _pid: next(running, False))
    monkeypatch.setattr(llama_cpp, "_get_json", lambda _url, *, timeout: None)
    monkeypatch.setattr(llama_cpp, "_pid_looks_like_llama_server", lambda _pid: True)
    monkeypatch.setattr(llama_cpp.os, "kill", lambda pid, sig: kills.append((pid, sig)))

    assert llama_cpp.stop_llama_server() is True
    assert kills == [(12345, signal.SIGTERM)]
    assert "server" not in json.loads(paths.state_file.read_text(encoding="utf-8"))


def test_stop_llama_server_reaps_current_process_child(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _isolate_llama_paths(monkeypatch, tmp_path)
    process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    monkeypatch.setattr(llama_cpp, "_MANAGED_SERVER_PROCESS", process)
    server = LlamaCppServerState(
        pid=process.pid,
        endpoint="http://127.0.0.1:18080/v1",
        model_id="llama-cpp/acme/model:Q4_K_M",
        started_at=1.0,
    )
    llama_cpp._save_state(llama_cpp._LlamaCppState(records=[], server=server))

    try:
        assert llama_cpp.stop_llama_server() is True
        assert process.poll() is not None
        assert llama_cpp._MANAGED_SERVER_PROCESS is None
        assert not llama_cpp._pid_running(process.pid)
        assert "server" not in json.loads(paths.state_file.read_text(encoding="utf-8"))
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5.0)


def test_stop_llama_server_kills_loading_windows_managed_server_without_ps(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _isolate_llama_paths(monkeypatch, tmp_path)
    server = LlamaCppServerState(
        pid=12345,
        endpoint="http://127.0.0.1:18080/v1",
        model_id="llama-cpp/acme/model:Q4_K_M",
        started_at=1.0,
    )
    llama_cpp._save_state(llama_cpp._LlamaCppState(records=[], server=server))
    kills: list[tuple[int, int]] = []

    running = iter((True, True, True, False))
    monkeypatch.setattr(llama_cpp.platform, "system", lambda: "Windows")
    monkeypatch.setattr(llama_cpp, "_pid_running", lambda _pid: next(running, False))
    monkeypatch.setattr(llama_cpp, "_get_json", lambda _url, *, timeout: None)
    monkeypatch.setattr(
        llama_cpp.shutil,
        "which",
        lambda name: "C:\\Windows\\System32\\tasklist.exe" if name == "tasklist" else None,
    )
    monkeypatch.setattr(
        llama_cpp.subprocess,
        "run",
        lambda _command, **_kwargs: subprocess.CompletedProcess(
            _command,
            0,
            stdout='"llama-server.exe","12345","Console","1","12,345 K"\n',
            stderr="",
        ),
    )
    monkeypatch.setattr(llama_cpp.os, "kill", lambda pid, sig: kills.append((pid, sig)))
    monkeypatch.setattr(llama_cpp, "_pid_looks_like_llama_server", lambda _pid: True)

    assert llama_cpp.stop_llama_server() is True
    assert kills == [(12345, signal.SIGTERM)]
    assert "server" not in json.loads(paths.state_file.read_text(encoding="utf-8"))


def test_stop_llama_server_kills_verified_server(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _isolate_llama_paths(monkeypatch, tmp_path)
    server = LlamaCppServerState(
        pid=12345,
        endpoint="http://127.0.0.1:18080/v1",
        model_id="llama-cpp/acme/model:Q4_K_M",
        started_at=1.0,
    )
    llama_cpp._save_state(llama_cpp._LlamaCppState(records=[], server=server))
    kills: list[tuple[int, int]] = []

    running = iter((True, True, True, False))
    monkeypatch.setattr(llama_cpp, "_pid_running", lambda _pid: next(running, False))
    monkeypatch.setattr(
        llama_cpp,
        "_get_json",
        lambda _url, *, timeout: {"data": [{"id": server.model_id}]},
    )
    monkeypatch.setattr(llama_cpp, "_pid_looks_like_llama_server", lambda _pid: True)
    monkeypatch.setattr(llama_cpp.os, "kill", lambda pid, sig: kills.append((pid, sig)))

    assert llama_cpp.stop_llama_server() is True
    assert kills == [(12345, signal.SIGTERM)]


def test_stop_llama_server_keeps_state_when_pid_survives(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _isolate_llama_paths(monkeypatch, tmp_path)
    server = LlamaCppServerState(
        pid=12345,
        endpoint="http://127.0.0.1:18080/v1",
        model_id="llama-cpp/acme/model:Q4_K_M",
        started_at=1.0,
    )
    llama_cpp._save_state(llama_cpp._LlamaCppState(records=[], server=server))
    kills: list[tuple[int, int]] = []

    monkeypatch.setattr(llama_cpp, "_PID_STOP_GRACE_SECONDS", 0.0)
    monkeypatch.setattr(llama_cpp, "_PID_STOP_KILL_GRACE_SECONDS", 0.0)
    monkeypatch.setattr(llama_cpp, "_pid_running", lambda _pid: True)
    monkeypatch.setattr(
        llama_cpp,
        "_get_json",
        lambda _url, *, timeout: {"data": [{"id": server.model_id}]},
    )
    monkeypatch.setattr(llama_cpp.os, "kill", lambda pid, sig: kills.append((pid, sig)))
    monkeypatch.setattr(llama_cpp, "_pid_looks_like_llama_server", lambda _pid: True)

    assert llama_cpp.stop_llama_server() is False
    assert kills == [(12345, signal.SIGTERM), (12345, signal.SIGKILL)]
    saved_state = json.loads(paths.state_file.read_text(encoding="utf-8"))
    assert saved_state["server"]["pid"] == server.pid


def test_current_server_state_preserves_loading_managed_server(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _isolate_llama_paths(monkeypatch, tmp_path)
    server = LlamaCppServerState(
        pid=12345,
        endpoint="http://127.0.0.1:18080/v1",
        model_id="llama-cpp/acme/model:Q4_K_M",
        started_at=1.0,
    )
    llama_cpp._save_state(llama_cpp._LlamaCppState(records=[], server=server))

    monkeypatch.setattr(llama_cpp, "_pid_running", lambda _pid: True)
    monkeypatch.setattr(llama_cpp, "_get_json", lambda _url, *, timeout: None)
    monkeypatch.setattr(llama_cpp, "_pid_looks_like_llama_server", lambda _pid: True)

    assert llama_cpp.current_server_state() is None
    assert "server" in json.loads(paths.state_file.read_text(encoding="utf-8"))


def test_pid_running_uses_windows_tasklist_without_os_kill(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands: list[list[str]] = []

    monkeypatch.setattr(llama_cpp.platform, "system", lambda: "Windows")
    monkeypatch.setattr(
        llama_cpp.shutil,
        "which",
        lambda name: "C:\\Windows\\System32\\tasklist.exe" if name == "tasklist" else None,
    )
    monkeypatch.setattr(
        llama_cpp.os,
        "kill",
        lambda _pid, _sig: pytest.fail("Windows liveness probe must not call os.kill"),
    )

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        return subprocess.CompletedProcess(
            command,
            0,
            stdout='"llama-server.exe","12345","Console","1","12,345 K"\n',
            stderr="",
        )

    monkeypatch.setattr(llama_cpp.subprocess, "run", fake_run)

    assert llama_cpp._pid_running(12345) is True
    assert commands == [
        ["C:\\Windows\\System32\\tasklist.exe", "/FI", "PID eq 12345", "/FO", "CSV", "/NH"]
    ]


def test_pid_running_windows_returns_false_when_tasklist_misses_pid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(llama_cpp.platform, "system", lambda: "Windows")
    monkeypatch.setattr(llama_cpp.shutil, "which", lambda _name: "tasklist")
    monkeypatch.setattr(
        llama_cpp.subprocess,
        "run",
        lambda command, **_kwargs: subprocess.CompletedProcess(
            command,
            0,
            stdout='"other.exe","67890","Console","1","12,345 K"\n',
            stderr="",
        ),
    )

    assert llama_cpp._pid_running(12345) is False


def test_models_response_includes_alias() -> None:
    assert llama_cpp._models_response_includes(
        {"data": [{"id": "canonical", "aliases": ["llama-cpp/acme/model:Q4_K_M"]}]},
        "llama-cpp/acme/model:Q4_K_M",
    )


def test_terminate_pid_uses_sigterm(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[int, int]] = []
    running = iter((True, False))
    monkeypatch.setattr(llama_cpp, "_pid_running", lambda _pid: next(running, False))
    monkeypatch.setattr(llama_cpp.os, "kill", lambda pid, sig: calls.append((pid, sig)))

    assert llama_cpp._terminate_pid(12345) is True
    assert calls == [(12345, signal.SIGTERM)]
