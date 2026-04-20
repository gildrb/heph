"""Tests for hephaistos.analytics — PostHog product analytics."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from hephaistos.analytics import (
    capture,
    get_distinct_id,
    init_analytics,
    shutdown_analytics,
)


class TestNoOpWithoutToken:
    """When POSTHOG_PROJECT_TOKEN is not set, all calls are no-ops."""

    def test_init_is_noop(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import hephaistos.analytics as mod

        monkeypatch.delenv("POSTHOG_PROJECT_TOKEN", raising=False)
        mod._posthog_client = None  # type: ignore[reportPrivateUsage]
        init_analytics()
        assert mod._posthog_client is None  # type: ignore[reportPrivateUsage]

    def test_capture_is_noop(self) -> None:
        import hephaistos.analytics as mod

        prev = mod._posthog_client  # type: ignore[reportPrivateUsage]
        mod._posthog_client = None  # type: ignore[reportPrivateUsage]
        try:
            capture("test_event", {"key": "value"})  # should not raise
        finally:
            mod._posthog_client = prev  # type: ignore[reportPrivateUsage]

    def test_shutdown_is_noop(self) -> None:
        import hephaistos.analytics as mod

        prev = mod._posthog_client  # type: ignore[reportPrivateUsage]
        mod._posthog_client = None  # type: ignore[reportPrivateUsage]
        try:
            shutdown_analytics()  # should not raise
        finally:
            mod._posthog_client = prev  # type: ignore[reportPrivateUsage]


class TestCaptureWithClient:
    """When a PostHog client is set, capture forwards events."""

    def test_capture_forwards_event(self) -> None:
        import hephaistos.analytics as mod

        mock_client = MagicMock()
        prev = mod._posthog_client  # type: ignore[reportPrivateUsage]
        mod._posthog_client = mock_client  # type: ignore[reportPrivateUsage]
        try:
            capture("button_clicked", {"button": "save"})
            mock_client.capture.assert_called_once()
            call_kwargs = mock_client.capture.call_args[1]
            assert call_kwargs["event"] == "button_clicked"
            assert call_kwargs["properties"] == {"button": "save"}
        finally:
            mod._posthog_client = prev  # type: ignore[reportPrivateUsage]

    def test_shutdown_flushes_client(self) -> None:
        import hephaistos.analytics as mod

        mock_client = MagicMock()
        prev = mod._posthog_client  # type: ignore[reportPrivateUsage]
        mod._posthog_client = mock_client  # type: ignore[reportPrivateUsage]
        try:
            shutdown_analytics()
            mock_client.shutdown.assert_called_once()
        finally:
            mod._posthog_client = prev  # type: ignore[reportPrivateUsage]


class TestInitWithPosthog:
    """Init with a real token creates a PostHog client."""

    def test_init_creates_client(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import hephaistos.analytics as mod

        monkeypatch.setenv("POSTHOG_PROJECT_TOKEN", "phc_test123")
        mod._posthog_client = None  # type: ignore[reportPrivateUsage]

        mock_posthog = MagicMock()
        with patch.dict("sys.modules", {"posthog": mock_posthog}):
            init_analytics()
            assert mod._posthog_client is not None  # type: ignore[reportPrivateUsage]

        mod._posthog_client = None  # type: ignore[reportPrivateUsage]


class TestDistinctId:
    """Install ID is stable and stored on disk."""

    def test_returns_string(self) -> None:
        did = get_distinct_id()
        assert isinstance(did, str)
        assert did.startswith("heph_")
