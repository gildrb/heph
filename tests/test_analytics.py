"""Tests for hephaistos.analytics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Self

import pytest

from hephaistos import telemetry
from hephaistos.analytics import capture, get_distinct_id, init_analytics


def test_get_distinct_id_is_stable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(telemetry, "_INSTALL_ID_PATH", tmp_path / "install_id.json")

    first = get_distinct_id()
    second = get_distinct_id()

    assert first == second
    assert first.startswith("heph_")


def test_capture_is_noop_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hephaistos.analytics.analytics_backend_available", lambda: False)
    capture("test_event", {"model": "gpt-5.4"})


def test_capture_posts_sanitized_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    responses: list[dict[str, object]] = []

    class _Response:
        def __enter__(self) -> Self:
            return self

        def __exit__(self, *args: object) -> None:
            return None

    def _fake_urlopen(request: object, timeout: int = 0) -> _Response:
        assert timeout == 5
        data = json.loads(request.data.decode("utf-8"))  # type: ignore[attr-defined]
        responses.append(data)
        return _Response()

    monkeypatch.setattr("hephaistos.analytics.analytics_backend_available", lambda: True)
    monkeypatch.setattr("hephaistos.analytics.analytics_enabled", lambda: True)
    monkeypatch.setattr("hephaistos.analytics.posthog_project_token", lambda: "phc_test")
    monkeypatch.setattr("hephaistos.analytics.posthog_host", lambda: "https://app.posthog.com")
    monkeypatch.setattr("hephaistos.analytics.get_distinct_id", lambda: "heph_test")
    monkeypatch.setattr(
        "hephaistos.analytics.runtime_context",
        lambda: {"app_version": "0.1.0", "release_channel": "pypi"},
    )
    monkeypatch.setattr("hephaistos.analytics.urllib.request.urlopen", _fake_urlopen)

    capture(
        "shell_started",
        {
            "model": "openai/gpt-5.4",
            "source_file_count": 3,
            "path": "/tmp/secret",
        },
    )

    payload = responses[0]
    assert payload["api_key"] == "phc_test"
    assert payload["event"] == "shell_started"
    assert payload["distinct_id"] == "heph_test"
    properties = payload["properties"]
    assert isinstance(properties, dict)
    assert properties["model"] == "openai/gpt-5.4"
    assert "path" not in properties


def test_init_analytics_is_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    """init_analytics() no longer eagerly warms install_id — deferred to capture()."""
    calls: list[str] = []
    monkeypatch.setattr("hephaistos.analytics.analytics_backend_available", lambda: True)
    monkeypatch.setattr(
        "hephaistos.analytics.install_id",
        lambda: calls.append("install_id") or "heph_x",
    )

    init_analytics()

    assert calls == []
