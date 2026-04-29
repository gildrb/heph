"""Slash command autocomplete suggestions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from hephaistos.agent.persona import list_personas
from hephaistos.app.model_picker import configured_model_choices
from hephaistos.providers.config import Provider, ProviderConfig


@dataclass(frozen=True)
class CommandSuggestion:
    name: str
    description: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class CompletionCandidate:
    text: str
    description: str
    start_position: int


class _ProviderConfigLoader(Protocol):
    def __call__(self) -> ProviderConfig: ...


class SlashCompletionEngine:
    """Context-aware slash completion for the TUI."""

    def __init__(
        self,
        *,
        provider_config_loader: _ProviderConfigLoader = ProviderConfig.load,
    ) -> None:
        self._provider_config_loader = provider_config_loader
        self._cached_providers: dict[str, Provider] = {}
        self.refresh()

    def refresh(self) -> None:
        """Reload provider/model suggestions from cached configuration."""
        self._cached_providers = dict(self._provider_config_loader().providers)

    def candidates(
        self,
        text_before_cursor: str,
        commands: list[CommandSuggestion],
    ) -> list[CompletionCandidate]:
        stripped = text_before_cursor.lstrip()

        if not stripped.startswith("/") or "\n" in stripped:
            return []

        body = stripped[1:]

        if body.lower() == "models":
            return [
                CompletionCandidate(
                    text=" " + suggestion + " ",
                    description=description,
                    start_position=0,
                )
                for suggestion, description in self._model_picker_suggestions([])
            ]

        if not body or " " not in body:
            prefix = body.lower()
            seen: set[str] = set()
            candidates: list[CompletionCandidate] = []
            for command in commands:
                matches_name = command.name.lower().startswith(prefix)
                alias_match = next(
                    (alias for alias in command.aliases if alias.lower().startswith(prefix)),
                    "",
                )
                if not (matches_name or alias_match) or command.name in seen:
                    continue
                seen.add(command.name)
                replacement = command.name if matches_name else alias_match
                candidates.append(
                    CompletionCandidate(
                        text=replacement + " ",
                        description=command.description,
                        start_position=-len(body),
                    )
                )
            return candidates

        parts = body.split()
        if not parts:
            return []

        ends_with_space = stripped.endswith(" ")
        cmd_name = parts[0].lower()
        arg_parts = parts[1:]
        if ends_with_space:
            arg_parts.append("")

        candidates = []
        for suggestion, description in self._argument_suggestions(cmd_name, arg_parts):
            current = arg_parts[-1] if arg_parts else ""
            if (
                cmd_name != "models"
                and current
                and not suggestion.lower().startswith(current.lower())
            ):
                continue
            suffix = "" if suggestion.endswith(" ") else " "
            candidates.append(
                CompletionCandidate(
                    text=suggestion + suffix,
                    description=description,
                    start_position=-len(current),
                )
            )
        return candidates

    def suggestion(
        self,
        value: str,
        commands: list[CommandSuggestion],
    ) -> str | None:
        """Return the full suggested input value for Textual's ghost completion."""
        candidates = self.candidates(value, commands)
        if not candidates:
            return None
        candidate = candidates[0]
        replacement_start = len(value) + candidate.start_position
        suggestion = value[:replacement_start] + candidate.text
        if suggestion == value:
            return None
        return suggestion

    def _argument_suggestions(
        self,
        cmd_name: str,
        arg_parts: list[str],
    ) -> list[tuple[str, str]]:
        if cmd_name == "api":
            if len(arg_parts) <= 1:
                return [
                    ("key", "Store an API key for the active provider"),
                    ("url", "Override the provider base URL"),
                ]
            return []

        if cmd_name == "provider":
            return self._provider_suggestions(arg_parts)

        if cmd_name == "models":
            return self._model_picker_suggestions(arg_parts)

        if cmd_name == "memory":
            return [
                ("status", "Show memory backend and Supermemory setup"),
                ("setup", "Connect Supermemory for cross-armory study memory"),
                ("profile", "View or change the Supermemory profile"),
                ("disable", "Use local memory only"),
            ]

        if cmd_name == "persona":
            return self._persona_suggestions(arg_parts)

        return []

    def _provider_suggestions(self, arg_parts: list[str]) -> list[tuple[str, str]]:
        if len(arg_parts) <= 1:
            return [
                ("use", "Switch active provider (and optional model)"),
                ("model", "Switch model within the active provider"),
            ]

        subcmd = arg_parts[0].lower()
        providers = self._cached_providers

        if subcmd == "use":
            if len(arg_parts) == 2:
                return [(slug, provider.display_name) for slug, provider in providers.items()]
            if len(arg_parts) == 3:
                provider = providers.get(arg_parts[1].lower())
                if provider is None:
                    return []
                return [(model, provider.display_name) for model in provider.models]

        if subcmd == "model":
            active = self._provider_config_loader().get_active()
            if active is None:
                return []
            return [(model, active.display_name) for model in active.models]

        return []

    def _model_picker_suggestions(self, arg_parts: list[str]) -> list[tuple[str, str]]:
        query = " ".join(arg_parts).strip().lower()
        suggestions: list[tuple[str, str]] = []
        active = self._provider_config_loader().get_active()
        current_model = active.current_model if active is not None else ""
        choices = configured_model_choices(self._provider_config_loader())
        choices = sorted(
            choices,
            key=lambda item: 0
            if active is not None and active.slug == item[0] and item[1] == current_model
            else 1,
        )
        for slug, model, display_name, is_free in choices:
            haystack = f"{model} {display_name} {slug}".lower()
            if query and query not in haystack:
                continue
            parts = [f"via {display_name}"]
            if is_free:
                parts.append("free")
            if active is not None and active.slug == slug and model == current_model:
                parts.append("current")
            suggestions.append((model, "  ".join(parts)))
        return suggestions

    def _persona_suggestions(self, arg_parts: list[str]) -> list[tuple[str, str]]:
        if len(arg_parts) > 1:
            return []
        return [(persona.slug, persona.description) for persona in list_personas()]
