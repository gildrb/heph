"""Settings command shim.

The interactive settings UI lives in the TUI inline flow. The slash command
remains in the registry so automation and help output can discover it without
carrying a second terminal menu implementation.
"""

from __future__ import annotations

from ai.providers.config import ProviderConfig
from parameters.settings import (
    ACTIVITY_TRACE_LABELS,
    ACTIVITY_TRACE_TOOL_CALLS,
    VOCAB_STRICTNESS_LABELS,
    load_app_settings,
)
from privacy.consent import (
    analytics_enabled,
    crash_reports_enabled,
)

from commands._base import Command, CommandResult, ensure_session


class SettingsCommand(Command):
    name = "settings"
    description = "Manage cross-session preferences"

    def handle(self, session: object, args: str) -> CommandResult:
        del args
        ensure_session(session)
        settings = load_app_settings()
        active_provider = ProviderConfig.load().get_active()
        provider = active_provider.display_name if active_provider else "none"
        activity = ACTIVITY_TRACE_LABELS.get(
            settings.activity_trace_mode,
            ACTIVITY_TRACE_LABELS[ACTIVITY_TRACE_TOOL_CALLS],
        )
        vocab = VOCAB_STRICTNESS_LABELS.get(settings.vocab_strictness, settings.vocab_strictness)
        default_armory = settings.default_armory_path or "none"
        analytics = "enabled" if analytics_enabled() else "disabled"
        crash_reports = "enabled" if crash_reports_enabled() else "disabled"
        print(
            "Settings are managed in the TUI with /settings. "
            f"Theme: {settings.theme}; Activity trace: {activity}; "
            f"Vocabulary practice: {vocab}; Default armory: {default_armory}; "
            f"Usage analytics: {analytics}; Crash reports: {crash_reports}; "
            f"Provider: {provider}."
        )
        return CommandResult()
