"""TUI slash-command completion engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from hephaistos.agent.persona import list_personas
from hephaistos.commands.suggestions import CommandSuggestion
from hephaistos.providers.config import Provider, ProviderConfig


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

        if not body or " " not in body:
            prefix = body.lower()
            return self._command_candidates(prefix, body, commands)

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

    def _command_candidates(
        self,
        prefix: str,
        body: str,
        commands: list[CommandSuggestion],
    ) -> list[CompletionCandidate]:
        candidates: list[CompletionCandidate] = []
        for command in commands:
            replacement = self._matching_command_token(command, prefix)
            if replacement is None:
                continue
            candidates.append(
                CompletionCandidate(
                    text=replacement + " ",
                    description=command.description,
                    start_position=-len(body),
                )
            )
        if candidates or not prefix:
            return candidates
        return self._closest_command_candidates(prefix, body, commands)

    def _closest_command_candidates(
        self,
        prefix: str,
        body: str,
        commands: list[CommandSuggestion],
    ) -> list[CompletionCandidate]:
        ranked: list[tuple[float, int, CompletionCandidate]] = []
        for index, command in enumerate(commands):
            replacement, score = self._closest_command_token(command, prefix)
            if score == 0.0:
                continue
            ranked.append(
                (
                    score,
                    -index,
                    CompletionCandidate(
                        text=replacement + " ",
                        description=command.description,
                        start_position=-len(body),
                    ),
                )
            )
        ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return [candidate for _score, _index, candidate in ranked]

    def _closest_command_token(
        self,
        command: CommandSuggestion,
        prefix: str,
    ) -> tuple[str, float]:
        best_token = command.name
        best_score = self._token_similarity(command.name, prefix)
        for alias in command.aliases:
            score = self._token_similarity(alias, prefix)
            if score > best_score:
                best_token = alias
                best_score = score
        return best_token, best_score

    def _matching_command_token(
        self,
        command: CommandSuggestion,
        prefix: str,
    ) -> str | None:
        if self._token_matches(command.name, prefix):
            return command.name
        for alias in command.aliases:
            if self._token_matches(alias, prefix):
                return alias
        return None

    def _token_matches(self, token: str, prefix: str) -> bool:
        normalized = token.lower()
        return not prefix or normalized.startswith(prefix)

    def _token_similarity(self, token: str, prefix: str) -> float:
        normalized = token.lower()
        if not prefix or normalized.startswith(prefix):
            return 1.0

        positions: list[int] = []
        search_start = 0
        for char in prefix:
            index = normalized.find(char, search_start)
            if index == -1:
                return 0.0
            positions.append(index)
            search_start = index + 1

        if not positions:
            return 0.0
        span = positions[-1] - positions[0] + 1
        gaps = span - len(prefix)
        coverage = len(prefix) / len(normalized)
        start_penalty = positions[0] / len(normalized)
        gap_penalty = gaps / len(normalized)
        return coverage - start_penalty - gap_penalty

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

    def _persona_suggestions(self, arg_parts: list[str]) -> list[tuple[str, str]]:
        if len(arg_parts) > 1:
            return []
        return [(persona.slug, persona.description) for persona in list_personas()]
