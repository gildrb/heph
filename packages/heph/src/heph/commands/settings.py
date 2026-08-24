"""Settings command shim.

The interactive settings UI lives in the TUI inline flow. The slash command
remains in the registry so automation and help output can discover it without
carrying a second terminal menu implementation.
"""

from __future__ import annotations

from ai.providers.config import ProviderConfig
from harness.parameters.settings import (
    ACTIVITY_TRACE_LABELS,
    ACTIVITY_TRACE_TOOL_CALLS,
    THINKING_VISIBILITY_LABELS,
    load_app_settings,
)

from heph.commands._base import Command, CommandResult, ensure_session


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
        thinking = THINKING_VISIBILITY_LABELS.get(
            settings.thinking_visibility,
            settings.thinking_visibility,
        )
        default_armory = settings.default_armory_path or "none"
        live_tokens = "shown" if settings.live_tokens_visible else "hidden"
        live_cost = "shown" if settings.live_cost_visible else "hidden"
        print(
            "Settings are managed in the TUI with /settings. "
            f"Theme: {settings.theme}; Activity trace: {activity}; "
            f"Model thinking: {thinking}; "
            f"Live tokens: {live_tokens}; Live cost: {live_cost}; "
            f"Default armory: {default_armory}; "
            f"Provider: {provider}."
        )
        return CommandResult()
