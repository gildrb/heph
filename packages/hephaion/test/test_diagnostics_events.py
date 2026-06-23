"""Tests for diagnostics.events."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Self

import pytest
from hephaion.diagnostics.events import capture, get_distinct_id, init_analytics

from hephaion.privacy import consent


def test_get_distinct_id_is_stable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(consent, "_INSTALL_ID_PATH", tmp_path / "install_id.json")

    first = get_distinct_id()
    second = get_distinct_id()

    assert first == second
    assert first.startswith("heph_")


def test_capture_is_noop_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("hephaion.diagnostics.events.analytics_backend_available", lambda: False)
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
        data = json.loads(request.data.decode("utf-8"))  # ty:ignore[unresolved-attribute]
        responses.append(data)
        return _Response()

    monkeypatch.setattr("hephaion.diagnostics.events.analytics_backend_available", lambda: True)
    monkeypatch.setattr("hephaion.diagnostics.events.analytics_enabled", lambda: True)
    monkeypatch.setattr("hephaion.diagnostics.events.posthog_project_token", lambda: "phc_test")
    monkeypatch.setattr(
        "hephaion.diagnostics.events.posthog_host", lambda: "https://app.posthog.com"
    )
    monkeypatch.setattr("hephaion.diagnostics.events.get_distinct_id", lambda: "heph_test")
    monkeypatch.setattr(
        "hephaion.diagnostics.events.runtime_context",
        lambda: {"app_version": "0.0.53", "release_channel": "pypi"},
    )
    monkeypatch.setattr("hephaion.diagnostics.events.urllib.request.urlopen", _fake_urlopen)

    capture(
        "session_created",
        {
            "mode": "plain",
            "model": "openai/gpt-5.4",
            "path": "/tmp/secret",
        },
    )

    payload = responses[0]
    assert payload["api_key"] == "phc_test"
    assert payload["event"] == "session_created"
    assert payload["distinct_id"] == "heph_test"
    properties = payload["properties"]
    assert isinstance(properties, dict)
    assert properties["model"] == "openai/gpt-5.4"  # ty:ignore[invalid-argument-type]
    assert "path" not in properties


def test_capture_rejects_non_https_posthog_host(monkeypatch: pytest.MonkeyPatch) -> None:
    opened: list[object] = []

    def _fake_urlopen(request: object, timeout: int = 0) -> object:
        del timeout
        opened.append(request)
        raise AssertionError("urlopen should not be called")

    monkeypatch.setattr("hephaion.diagnostics.events.analytics_backend_available", lambda: True)
    monkeypatch.setattr("hephaion.diagnostics.events.analytics_enabled", lambda: True)
    monkeypatch.setattr("hephaion.diagnostics.events.posthog_project_token", lambda: "phc_test")
    monkeypatch.setattr("hephaion.diagnostics.events.posthog_host", lambda: "http://example.com")
    monkeypatch.setattr("hephaion.diagnostics.events.urllib.request.urlopen", _fake_urlopen)

    capture("session_created")

    assert opened == []


def test_init_analytics_is_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    """init_analytics() no longer eagerly warms install_id — deferred to capture()."""
    calls: list[str] = []
    monkeypatch.setattr("hephaion.diagnostics.events.analytics_backend_available", lambda: True)
    monkeypatch.setattr(
        "hephaion.diagnostics.events.install_id",
        lambda: calls.append("install_id") or "heph_x",
    )

    init_analytics()

    assert calls == []
