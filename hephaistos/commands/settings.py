"""Settings management command."""

from __future__ import annotations

from pathlib import Path

from hephaistos.chat.session import validate_armory_path
from hephaistos.commands._base import Command, CommandResult, ensure_session
from hephaistos.commands.auth import LoginCommand, LogoutCommand
from hephaistos.commands.memory import MemoryCommand
from hephaistos.commands.model import ModelsCommand
from hephaistos.parameters.settings import (
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
from hephaistos.terminal_display import STYLE_DIM, print_error, print_info, print_success, styled


class SettingsCommand(Command):
    name = "settings"
    description = "Manage cross-session preferences"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        while True:
            settings = load_app_settings()
            default_armory = settings.default_armory_path or "none"
            mode_label = settings.interface_mode.upper()
            options = [
                MenuOption(
                    "Interface",
                    f"Mode: {mode_label}",
                ),
                MenuOption(
                    "Privacy & Diagnostics",
                    "Usage analytics and crash reports",
                ),
                MenuOption(
                    "Appearance",
                    f"Theme: {settings.theme}",
                ),
                MenuOption(
                    "Startup",
                    f"Default armory: {default_armory}",
                ),
                MenuOption(
                    "Default model",
                    f"Current: {s.config.model}",
                ),
                MenuOption(
                    "Study memory",
                    "Local memory and Supermemory setup",
                ),
                MenuOption(
                    "Accounts & credentials",
                    "Connect or clear subscription/API-key access",
                ),
                MenuOption("Back", "Return to the chat prompt."),
            ]
            selected = select_option("Settings", options)
            if selected is None or selected == len(options) - 1:
                return CommandResult()
            if selected == 0:
                self._interface_menu()
            elif selected == 1:
                self._privacy_menu()
            elif selected == 2:
                self._appearance_menu()
            elif selected == 3:
                self._startup_menu()
            elif selected == 4:
                ModelsCommand().handle(s, "")
            elif selected == 5:
                MemoryCommand().handle(s, "status")
            else:
                self._provider_credentials_menu(s)

    def _interface_menu(self) -> None:
        while True:
            options = [
                MenuOption(
                    "TUI",
                    "The only interface mode (Textual TUI)",
                    is_current=True,
                ),
                MenuOption("Back", "Return to settings."),
            ]
            selected = select_option("Interface", options)
            if selected is None or selected == len(options) - 1:
                return

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
                MenuOption("Back", "Return to settings."),
            ]
            selected = select_option("Privacy & Diagnostics", options)
            if selected is None or selected == len(options) - 1:
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
            options.append(MenuOption("Back", "Return to settings."))
            selected = select_option("Appearance", options)
            if selected is None or selected == len(options) - 1:
                return
            theme = THEME_PRESETS[selected]
            if theme == current:
                continue
            save_setting("theme", theme)
            set_theme(theme)

    def _startup_menu(self) -> None:
        while True:
            settings = load_app_settings()
            default_armory = settings.default_armory_path or styled("(not set)", STYLE_DIM)
            options = [
                MenuOption("Set default armory", str(default_armory)),
                MenuOption("Clear default armory", "Disable startup fallback armory"),
                MenuOption("Back", "Return to settings."),
            ]
            selected = select_option("Startup", options)
            if selected is None or selected == len(options) - 1:
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
                MenuOption("Back", "Return to settings."),
            ]
            selected = select_option("Accounts & Credentials", options)
            if selected is None or selected == len(options) - 1:
                return
            if selected == 0:
                ModelsCommand().handle(session, "")
            elif selected == 1:
                LoginCommand().handle(session, "")
            elif selected == 2:
                LogoutCommand().handle(session, "")
