"""Release-time privacy and diagnostics configuration.

This file is tracked with safe stub values in the repository. Official release
workflows overwrite it in the CI workspace just before building artifacts.
"""

from __future__ import annotations

POSTHOG_HOST: str | None = None
POSTHOG_PROJECT_TOKEN: str | None = None
SENTRY_DSN: str | None = None
RELEASE_CHANNEL: str | None = None
RELEASE_VERSION: str | None = None
