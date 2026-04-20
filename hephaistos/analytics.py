"""PostHog product analytics for Hephaistos.

All tracking is opt-in via environment variables.  When ``POSTHOG_PROJECT_TOKEN``
is unset, every call in this module is a safe no-op so the application works
normally without telemetry.

Configuration (environment variables):
    POSTHOG_PROJECT_TOKEN  - PostHog project token (required for tracking).
                             When unset, all calls are no-ops.
    POSTHOG_HOST           - PostHog ingestion host (optional).
"""

from __future__ import annotations

import contextlib
import json
import os
import uuid
from pathlib import Path
from typing import Any

_INSTALL_ID_PATH = Path.home() / ".cache" / "hephaistos" / "install_id"

_posthog_client: Any = None
_install_id: str = ""


def _get_or_create_install_id() -> str:
    """Return a stable per-installation UUID (created on first run)."""
    global _install_id  # noqa: PLW0603
    if _install_id:
        return _install_id
    _INSTALL_ID_PATH.parent.mkdir(parents=True, exist_ok=True)
    if _INSTALL_ID_PATH.exists():
        with contextlib.suppress(Exception):
            data = json.loads(_INSTALL_ID_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("install_id"):
                _install_id = str(data["install_id"])
                return _install_id
    _install_id = f"heph_{uuid.uuid4().hex}"
    with contextlib.suppress(Exception):
        _INSTALL_ID_PATH.write_text(json.dumps({"install_id": _install_id}), encoding="utf-8")
    return _install_id


def get_distinct_id() -> str:
    """Return the stable per-installation distinct ID used for PostHog events."""
    return _get_or_create_install_id()


def init_analytics() -> None:
    """Initialise the PostHog client.  No-op when ``POSTHOG_PROJECT_TOKEN`` is not set."""
    global _posthog_client  # noqa: PLW0603
    token = os.environ.get("POSTHOG_PROJECT_TOKEN", "").strip()
    if not token:
        return
    try:
        from posthog import Posthog

        host = os.environ.get("POSTHOG_HOST", "")
        kwargs: dict[str, Any] = {"enable_exception_autocapture": True}
        if host:
            kwargs["host"] = host
        _posthog_client = Posthog(token, **kwargs)
    except ImportError:  # pragma: no cover
        pass


def capture(event: str, properties: dict[str, Any] | None = None) -> None:
    """Capture a PostHog event.  No-op when analytics are not initialised."""
    if _posthog_client is None:
        return
    with contextlib.suppress(Exception):
        _posthog_client.capture(
            distinct_id=get_distinct_id(),
            event=event,
            properties=properties or {},
        )


def shutdown_analytics() -> None:
    """Flush and shut down the PostHog client."""
    if _posthog_client is None:
        return
    with contextlib.suppress(Exception):
        _posthog_client.shutdown()
