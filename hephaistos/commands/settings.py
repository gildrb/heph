"""Settings management command."""

from __future__ import annotations

from pathlib import Path

from hephaistos.chat.session import validate_armory_path
from hephaistos.commands._base import Command, CommandResult, ensure_session
from hephaistos.commands.auth import LoginCommand, LogoutCommand
from hephaistos.commands.memory import MemoryCommand
from hephaistos.parameters.settings import (
    ACTIVITY_TRACE_HIDDEN_TOOL_CALLS,
    ACTIVITY_TRACE_LABELS,
    ACTIVITY_TRACE_MINIMAL_TOOL_CALLS,
    ACTIVITY_TRACE_MODES,
    ACTIVITY_TRACE_TOOL_CALLS,
    THEME_PRESETS,
    clear_setting,
    load_app_settings,
    save_setting,
)
from hephaistos.privacy.consent import (
    analytics_backend_available,
    analytics_enabled,
    analytics_env_override,
    crash_reports_backend_available,
    crash_reports_enabled,
    crash_reports_env_override,
)
from hephaistos.providers.config import ProviderConfig
from hephaistos.terminal import (
    MenuOption,
    browse_directory,
    current_theme_name,
    select_option,
    set_theme,
)
from hephaistos.terminal.display import STYLE_DIM, print_error, print_info, print_success, styled

_ACTIVITY_TRACE_DESCRIPTIONS = {
    ACTIVITY_TRACE_TOOL_CALLS: "Show live reads, commands, model calls, tool results",
    ACTIVITY_TRACE_MINIMAL_TOOL_CALLS: "Show compact status and final activity summary",
    ACTIVITY_TRACE_HIDDEN_TOOL_CALLS: "Hide internal activity trace lines",
}


class SettingsCommand(Command):
    name = "settings"
    description = "Manage cross-session preferences"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        while True:
            settings = load_app_settings()
            default_armory = settings.default_armory_path or "none"
            options = [
                MenuOption(
                    "Privacy & Diagnostics",
                    "Usage analytics and crash reports",
                ),
                MenuOption(
                    "Appearance",
                    f"Theme: {settings.theme}",
                ),
                MenuOption(
                    "Activity trace",
                    ACTIVITY_TRACE_LABELS.get(
                        settings.activity_trace_mode,
                        ACTIVITY_TRACE_LABELS[ACTIVITY_TRACE_TOOL_CALLS],
                    ),
                ),
                MenuOption(
                    "Startup",
                    f"Default armory: {default_armory}",
                ),
                MenuOption(
                    "Study memory",
                    "Local armory learning memory",
                ),
                MenuOption(
                    "Accounts & credentials",
                    "Connect or clear subscription/API-key access",
                ),
            ]
            selected = select_option("Settings", options)
            if selected is None:
                return CommandResult()
            actions = (
                self._privacy_menu,
                self._appearance_menu,
                self._activity_trace_menu,
                self._startup_menu,
                lambda: MemoryCommand().handle(s, "status"),
                lambda: self._provider_credentials_menu(s),
            )
            actions[selected]()

    @staticmethod
    def _privacy_description(
        *,
        enabled: bool,
        available: bool,
        overridden: bool,
    ) -> str:
        status = "enabled" if enabled else "disabled"
        availability = "available" if available else "inactive until configured"
        suffix = " · env override active" if overridden else ""
        return f"{status} · {availability}{suffix}"

    def _privacy_menu(self) -> None:
        while True:
            settings = load_app_settings()
            options = [
                MenuOption(
                    f"[{'x' if analytics_enabled() else ' '}] Usage analytics",
                    self._privacy_description(
                        enabled=analytics_enabled(),
                        available=analytics_backend_available(),
                        overridden=analytics_env_override(),
                    ),
                ),
                MenuOption(
                    f"[{'x' if crash_reports_enabled() else ' '}] Crash reports",
                    self._privacy_description(
                        enabled=crash_reports_enabled(),
                        available=crash_reports_backend_available(),
                        overridden=crash_reports_env_override(),
                    ),
                ),
            ]
            selected = select_option("Privacy & Diagnostics", options)
            if selected is None:
                return
            if selected == 0:
                save_setting("analytics_enabled", str(not settings.analytics_enabled).lower())
                if analytics_env_override():
                    print_info(
                        "Saved analytics preference updated, but "
                        "HEPHAISTOS_ANALYTICS_ENABLED is overriding it right now."
                    )
            elif selected == 1:
                save_setting(
                    "crash_reports_enabled",
                    str(not settings.crash_reports_enabled).lower(),
                )
                if crash_reports_env_override():
                    print_info(
                        "Saved crash-report preference updated, but "
                        "HEPHAISTOS_CRASH_REPORTS_ENABLED is overriding it right now."
                    )

    def _appearance_menu(self) -> None:
        while True:
            current = current_theme_name()
            options = [
                MenuOption(
                    theme.replace("_", " ").title(),
                    "Theme preset",
                    is_current=(theme == current),
                )
                for theme in THEME_PRESETS
            ]
            selected = select_option("Appearance", options)
            if selected is None:
                return
            theme = THEME_PRESETS[selected]
            if theme == current:
                continue
            save_setting("theme", theme)
            set_theme(theme)

    def _activity_trace_menu(self) -> None:
        while True:
            current = load_app_settings().activity_trace_mode
            options = [
                MenuOption(
                    ACTIVITY_TRACE_LABELS[mode],
                    _ACTIVITY_TRACE_DESCRIPTIONS[mode],
                    is_current=(mode == current),
                )
                for mode in ACTIVITY_TRACE_MODES
            ]
            selected = select_option("Activity Trace", options)
            if selected is None:
                return
            mode = ACTIVITY_TRACE_MODES[selected]
            save_setting("activity_trace_mode", mode)
            print_success(f"Activity trace: {ACTIVITY_TRACE_LABELS[mode]}")

    def _startup_menu(self) -> None:
        while True:
            settings = load_app_settings()
            default_armory = settings.default_armory_path or styled("(not set)", STYLE_DIM)
            options = [
                MenuOption("Set default armory", str(default_armory)),
                MenuOption("Clear default armory", "Disable startup fallback armory"),
            ]
            selected = select_option("Startup", options)
            if selected is None:
                return
            if selected == 1:
                clear_setting("default_armory_path")
                print_success("Cleared default armory.")
                continue

            start_path = (
                Path(settings.default_armory_path) if settings.default_armory_path else Path.home()
            )
            chosen = browse_directory("Default Armory", start=start_path)
            if chosen is None:
                print_info("Cancelled.")
                continue
            try:
                armory_path = validate_armory_path(str(chosen))
            except Exception as exc:
                print_error(str(exc))
                continue
            save_setting("default_armory_path", str(armory_path))
            print_success(f"Default armory: {armory_path}")

    def _provider_credentials_menu(self, session: object) -> None:
        while True:
            active = ProviderConfig.load().get_active()
            provider_label = active.display_name if active else "none"
            options = [
                MenuOption("Current access", f"Model source: {provider_label}"),
                MenuOption("Login", "Connect a subscription or API key"),
                MenuOption("Logout", "Clear stored subscription or API-key access"),
            ]
            selected = select_option("Accounts & Credentials", options)
            if selected is None:
                return
            if selected == 0:
                if active:
                    print_success(f"Current: {active.display_name} / {active.current_model}")
                    print_info("Use /models to change the active model.")
                else:
                    print_info("No provider configured. Use /login to connect.")
            elif selected == 1:
                LoginCommand().handle(session, "")
            elif selected == 2:
                LogoutCommand().handle(session, "")
