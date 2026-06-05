"""TUI slash-command completion engine."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from hephaion.providers.config import Provider, ProviderConfig

_COMPLETION_MENU_MAX_VISIBLE_ROWS = 7


class CommandSuggestion(Protocol):
    name: str
    description: str
    aliases: tuple[str, ...]


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


def completion_menu_scroll_y(
    highlighted: int,
    option_count: int,
    rendered_height: int,
    max_visible_rows: int = _COMPLETION_MENU_MAX_VISIBLE_ROWS,
) -> int:
    visible_rows = completion_menu_visible_row_count(
        option_count,
        rendered_height,
        max_visible_rows=max_visible_rows,
    )
    if visible_rows == 0:
        return 0
    max_scroll_y = max(0, option_count - visible_rows)
    centered_scroll_y = highlighted - (visible_rows // 2)
    return min(max(centered_scroll_y, 0), max_scroll_y)


def completion_menu_visible_row_count(
    option_count: int,
    rendered_height: int,
    max_visible_rows: int = _COMPLETION_MENU_MAX_VISIBLE_ROWS,
) -> int:
    if option_count <= 0:
        return 0
    visible_rows = rendered_height if rendered_height > 0 else max_visible_rows
    return max(1, min(option_count, visible_rows, max_visible_rows))


def completion_menu_visible_slice(
    highlighted: int,
    option_count: int,
    rendered_height: int,
    max_visible_rows: int = _COMPLETION_MENU_MAX_VISIBLE_ROWS,
) -> slice:
    visible_rows = completion_menu_visible_row_count(
        option_count,
        rendered_height,
        max_visible_rows=max_visible_rows,
    )
    if visible_rows == 0:
        return slice(0, 0)
    scroll_y = completion_menu_scroll_y(
        highlighted,
        option_count,
        rendered_height,
        max_visible_rows=max_visible_rows,
    )
    return slice(scroll_y, scroll_y + visible_rows)


def changed_highlight_indices(
    previous: int | None,
    highlighted: int,
    option_count: int,
) -> tuple[int, ...]:
    indices = [
        index
        for index in (previous, highlighted)
        if index is not None and 0 <= index < option_count
    ]
    return tuple(dict.fromkeys(indices))


def slash_command_name(value: str) -> str:
    stripped = value.strip()
    if not stripped.startswith("/"):
        return ""
    return stripped[1:].partition(" ")[0].lower()


class SlashCompletionEngine:
    def __init__(
        self,
        *,
        provider_config_loader: _ProviderConfigLoader = ProviderConfig.load,
    ) -> None:
        self._provider_config_loader = provider_config_loader
        self._cached_providers: dict[str, Provider] = {}
        self.refresh()

    def refresh(self) -> None:
        self._cached_providers = dict(self._provider_config_loader().providers)

    def candidates(
        self,
        text_before_cursor: str,
        commands: Sequence[CommandSuggestion],
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

        return self._argument_candidates(cmd_name, arg_parts)

    def _argument_candidates(
        self,
        cmd_name: str,
        arg_parts: list[str],
    ) -> list[CompletionCandidate]:
        candidates = []
        for suggestion, description in self._argument_suggestions(cmd_name):
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
        commands: Sequence[CommandSuggestion],
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
        commands: Sequence[CommandSuggestion],
    ) -> list[CompletionCandidate]:
        candidates: list[CompletionCandidate] = []
        for command in commands:
            replacements = self._matching_command_tokens(command, prefix)
            if not replacements:
                continue
            candidates.extend(
                self._command_candidate(replacement, command.description, body)
                for replacement in replacements
            )
        if candidates or not prefix:
            return candidates
        return self._closest_command_candidates(prefix, body, commands)

    def _closest_command_candidates(
        self,
        prefix: str,
        body: str,
        commands: Sequence[CommandSuggestion],
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
                    self._command_candidate(replacement, command.description, body),
                )
            )
        ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return [candidate for _score, _index, candidate in ranked]

    def _command_candidate(
        self,
        replacement: str,
        description: str,
        body: str,
    ) -> CompletionCandidate:
        return CompletionCandidate(
            text=replacement + " ",
            description=description,
            start_position=-len(body),
        )

    def _command_tokens(self, command: CommandSuggestion) -> tuple[str, ...]:
        return (command.name, *command.aliases)

    def _closest_command_token(
        self,
        command: CommandSuggestion,
        prefix: str,
    ) -> tuple[str, float]:
        best_token = ""
        best_score = 0.0
        for token in self._command_tokens(command):
            score = self._token_similarity(token, prefix)
            if score > best_score:
                best_token = token
                best_score = score
        return best_token, best_score

    def _matching_command_token(
        self,
        command: CommandSuggestion,
        prefix: str,
    ) -> str | None:
        return next(iter(self._matching_command_tokens(command, prefix)), None)

    def _matching_command_tokens(
        self,
        command: CommandSuggestion,
        prefix: str,
    ) -> tuple[str, ...]:
        if not prefix:
            return (command.name,)
        return tuple(
            token for token in self._command_tokens(command) if self._token_matches(token, prefix)
        )

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

    def _argument_suggestions(self, cmd_name: str) -> list[tuple[str, str]]:
        if cmd_name == "sessions":
            return [
                ("list", "List saved sessions in this armory"),
                ("browse", "Choose a saved session to resume"),
                ("resume", "Resume the latest saved session"),
            ]

        if cmd_name == "vocabulary":
            return [
                ("status", "Show vocabulary practice schedule"),
                ("reset", "Reset vocabulary practice history"),
            ]

        return []
