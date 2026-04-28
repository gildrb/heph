"""Settings management command."""

from __future__ import annotations

from pathlib import Path

from hephaistos.app.commands._base import Command, CommandResult, ensure_session
from hephaistos.app.commands.auth import ApiCommand, LoginCommand, LogoutCommand
from hephaistos.app.commands.memory import MemoryCommand
from hephaistos.app.commands.model import ModelCommand, ProviderCommand
from hephaistos.app.display import STYLE_DIM, print_error, print_info, print_success, styled
from hephaistos.app.menu import MenuOption, browse_directory, select_option
from hephaistos.app.palette import THEME_PRESETS, current_theme_name, set_theme
from hephaistos.chat.session import validate_armory_path
from hephaistos.parameters.settings import (
    clear_setting,
    load_app_settings,
    save_setting,
)
from hephaistos.providers.config import ProviderConfig
from hephaistos.telemetry import (
    analytics_backend_available,
    analytics_enabled,
    analytics_env_override,
    crash_reports_backend_available,
    crash_reports_enabled,
    crash_reports_env_override,
)


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
                    "Telemetry",
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
                    "Provider & credentials",
                    "Reuse /provider, /api, /login, and /logout flows",
                ),
                MenuOption("Back", "Return to the chat prompt."),
            ]
            selected = select_option("Settings", options)
            if selected is None or selected == len(options) - 1:
                return CommandResult()
            if selected == 0:
                self._interface_menu()
            elif selected == 1:
                self._telemetry_menu()
            elif selected == 2:
                self._appearance_menu()
            elif selected == 3:
                self._startup_menu()
            elif selected == 4:
                ModelCommand().handle(s, "")
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
    def _telemetry_description(
        *,
        enabled: bool,
        available: bool,
        overridden: bool,
    ) -> str:
        status = "enabled" if enabled else "disabled"
        availability = "available" if available else "inactive until configured"
        suffix = " · env override active" if overridden else ""
        return f"{status} · {availability}{suffix}"

    def _telemetry_menu(self) -> None:
        while True:
            settings = load_app_settings()
            options = [
                MenuOption(
                    f"[{'x' if analytics_enabled() else ' '}] Usage analytics",
                    self._telemetry_description(
                        enabled=analytics_enabled(),
                        available=analytics_backend_available(),
                        overridden=analytics_env_override(),
                    ),
                ),
                MenuOption(
                    f"[{'x' if crash_reports_enabled() else ' '}] Crash reports",
                    self._telemetry_description(
                        enabled=crash_reports_enabled(),
                        available=crash_reports_backend_available(),
                        overridden=crash_reports_env_override(),
                    ),
                ),
                MenuOption("Back", "Return to settings."),
            ]
            selected = select_option("Telemetry", options)
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
                MenuOption("Provider status", f"Current: {provider_label}"),
                MenuOption("API key status", "Reuse the /api command"),
                MenuOption("Login OAuth", "Reuse the /login flow"),
                MenuOption("Logout OAuth", "Reuse the /logout flow"),
                MenuOption("Back", "Return to settings."),
            ]
            selected = select_option("Provider & Credentials", options)
            if selected is None or selected == len(options) - 1:
                return
            if selected == 0:
                ProviderCommand().handle(session, "")
                print_info("Use /provider use <slug> to switch providers directly.")
            elif selected == 1:
                ApiCommand().handle(session, "")
                print_info(
                    "Use /api key <key> or /api url <url> to change credentials or endpoint."
                )
            elif selected == 2:
                LoginCommand().handle(session, "")
            elif selected == 3:
                LogoutCommand().handle(session, "")
