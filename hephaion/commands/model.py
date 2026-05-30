"""Model and provider management commands."""

from __future__ import annotations

from collections.abc import Sequence

from hephaion.chat.model_selection import switch_model
from hephaion.commands._base import Command, CommandResult, ensure_session
from hephaion.diagnostics.events import capture as capture_analytics
from hephaion.providers.config import ProviderConfig
from hephaion.providers.endpoints import is_keyless_endpoint
from hephaion.providers.model_choices import configured_model_choices, model_free_description
from hephaion.providers.model_recommendations import (
    ModelRecommendation,
    recommended_model_choices,
)
from hephaion.terminal import (
    STYLE_DIM,
    MenuOption,
    print_error,
    print_info,
    print_success,
    select_option,
    styled,
)

type ModelChoice = tuple[str, str, str, bool]


class ModelsCommand(Command):
    name = "models"
    description = "Pick the active model"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        query = args.strip().lower()
        pc = ProviderConfig.load()
        choices = _filtered_model_choices(configured_model_choices(pc), query)

        if not choices:
            print(_no_matching_model_text(s))
            return CommandResult()

        active = pc.get_active()
        current_model = s.config.model
        options, model_map = _model_menu_items(
            choices,
            pc,
            active_slug=active.slug if active else "",
            current_model=current_model,
        )
        selected = select_option("Model", options)
        if selected is None:
            return CommandResult()

        slug, model = model_map[selected]
        if not switch_model(s, slug, model):
            print_error("Model unavailable.")
            return CommandResult()
        provider = ProviderConfig.load().providers[slug]
        capture_analytics("model_changed", {"provider": slug, "to_model": model})
        print_success(f"Switched to {provider.display_name} / {model}")
        return CommandResult()


def _filtered_model_choices(choices: Sequence[ModelChoice], query: str) -> list[ModelChoice]:
    if not query:
        return list(choices)
    return [
        choice for choice in choices if query in choice[1].lower() or query in choice[2].lower()
    ]


def _no_matching_model_text(session: object) -> str:
    s = ensure_session(session)
    lines = [
        f"  Model:   {s.config.model}",
        f"  API:     {s.config.base_url}",
        f"  Key:     {_model_key_status(s.config.base_url, s.config.resolved_api_key)}",
        "",
        "  No matching models available. Use /login to connect a provider.",
    ]
    return "\n".join(lines)


def _model_key_status(base_url: str, resolved_api_key: str) -> str:
    if is_keyless_endpoint(base_url):
        return "not needed (free provider)"
    return "configured" if resolved_api_key else styled("not set", STYLE_DIM)


def _model_menu_items(
    choices: Sequence[ModelChoice],
    pc: ProviderConfig,
    *,
    active_slug: str,
    current_model: str,
) -> tuple[list[MenuOption], list[tuple[str, str]]]:
    options: list[MenuOption] = []
    model_map: list[tuple[str, str]] = []
    for slug, model, display_name, is_free in choices:
        is_current = slug == active_slug and model == current_model
        options.append(
            MenuOption(
                model,
                _model_option_description(pc, slug, display_name, is_free, is_current),
                is_current=is_current,
            )
        )
        model_map.append((slug, model))
    return options, model_map


def _model_option_description(
    pc: ProviderConfig,
    slug: str,
    display_name: str,
    is_free: bool,
    is_current: bool,
) -> str:
    parts = [f"via {display_name}"]
    if is_free:
        parts.append(model_free_description(pc.providers[slug].endpoint))
    if is_current:
        parts.append("current")
    return "  ".join(parts)


class RecommendCommand(Command):
    name = "recommend-model"
    description = "Recommend a quick, reliable model"
    aliases = ("recommend",)

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        pc = ProviderConfig.load()
        recommendations = recommended_model_choices(
            pc,
            refresh_live=True,
            query=args.strip(),
            current_model=s.config.model,
        )
        if not recommendations:
            print_info("No available models to recommend. Use /login to connect a provider.")
            return CommandResult()
        print_info(
            "Ranked from models available to your connected providers; best quick, "
            "reliable defaults are first."
        )
        active = pc.get_active()
        options, model_map = _recommendation_menu_items(
            recommendations,
            active_slug=active.slug if active else "",
            current_model=s.config.model,
        )
        selected = select_option("Recommended model", options)
        if selected is None:
            return CommandResult()

        slug, model = model_map[selected]
        if not switch_model(s, slug, model):
            print_error("Model unavailable.")
            return CommandResult()
        provider = ProviderConfig.load().providers[slug]
        capture_analytics("model_changed", {"provider": slug, "to_model": model})
        print_success(f"Switched to {provider.display_name} / {model}")
        return CommandResult()


def _recommendation_menu_items(
    recommendations: Sequence[ModelRecommendation],
    *,
    active_slug: str,
    current_model: str,
) -> tuple[list[MenuOption], list[tuple[str, str]]]:
    duplicates = _duplicate_recommendation_models(recommendations)
    options: list[MenuOption] = []
    model_map: list[tuple[str, str]] = []
    for recommendation in recommendations:
        is_current = recommendation.slug == active_slug and recommendation.model == current_model
        options.append(
            MenuOption(
                _recommendation_label(
                    recommendation, duplicate=recommendation.model in duplicates
                ),
                _recommendation_description(recommendation),
                is_current=is_current,
            )
        )
        model_map.append((recommendation.slug, recommendation.model))
    return options, model_map


def _duplicate_recommendation_models(
    recommendations: Sequence[ModelRecommendation],
) -> set[str]:
    counts: dict[str, int] = {}
    for recommendation in recommendations:
        counts[recommendation.model] = counts.get(recommendation.model, 0) + 1
    return {model for model, count in counts.items() if count > 1}


def _recommendation_label(recommendation: ModelRecommendation, *, duplicate: bool) -> str:
    if not duplicate:
        return recommendation.model
    return f"{recommendation.model} [{recommendation.display_name}]"


def _recommendation_description(recommendation: ModelRecommendation) -> str:
    return f"via {recommendation.display_name}  {', '.join(recommendation.reasons)}"
