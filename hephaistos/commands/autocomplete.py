"""Slash command autocomplete suggestions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from hephaistos.agent.persona import list_personas
from hephaistos.commands.model_picker import configured_model_choices, model_picker_columns
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
    display_provider: str = ""
    display_model: str = ""
    display_source: str = ""
    display_tags: str = ""


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
            return self._model_picker_candidates([], start_position=0, prefix_space=True)

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

        if cmd_name == "models":
            current = arg_parts[-1] if arg_parts else ""
            return self._model_picker_candidates(arg_parts, start_position=-len(current))

        candidates = []
        for suggestion, description in self._argument_suggestions(cmd_name, arg_parts):
            current = arg_parts[-1] if arg_parts else ""
            if current and not suggestion.lower().startswith(current.lower()):
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

    def _model_picker_candidates(
        self,
        arg_parts: list[str],
        *,
        start_position: int,
        prefix_space: bool = False,
    ) -> list[CompletionCandidate]:
        query = " ".join(arg_parts).strip().lower()
        candidates: list[CompletionCandidate] = []
        active = self._provider_config_loader().get_active()
        current_model = active.current_model if active is not None else ""
        choices = configured_model_choices(self._provider_config_loader())
        for slug, model, display_name, is_free in choices:
            is_current = active is not None and active.slug == slug and model == current_model
            provider_config = self._provider_config_loader().providers[slug]
            provider, model_label, source, tags = model_picker_columns(
                slug=slug,
                model=model,
                display_name=display_name,
                endpoint=provider_config.endpoint,
                is_free=is_free,
                is_current=is_current,
            )
            haystack = f"{provider} {model} {model_label} {source} {slug}".lower()
            if query and query not in haystack:
                continue
            candidates.append(
                CompletionCandidate(
                    text=f"{' ' if prefix_space else ''}{model} ",
                    description=source,
                    start_position=start_position,
                    display_provider=provider,
                    display_model=model_label,
                    display_source=source,
                    display_tags=tags,
                )
            )
        return candidates

    def _persona_suggestions(self, arg_parts: list[str]) -> list[tuple[str, str]]:
        if len(arg_parts) > 1:
            return []
        return [(persona.slug, persona.description) for persona in list_personas()]
