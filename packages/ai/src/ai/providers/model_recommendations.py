"""Model recommendation scoring for quick, reliable answers."""

from __future__ import annotations

from dataclasses import dataclass

from ai.providers.config import ProviderConfig
from ai.providers.endpoints import is_keyless_endpoint
from ai.providers.model_choices import configured_model_choices
from ai.providers.registry import ModelInfo
from ai.providers.registry import get_registry as get_provider_registry

type ModelChoice = tuple[str, str, str, bool]

_DEFAULT_RECOMMENDATION_LIMIT = 6
_FAST_VARIANT_TERMS: tuple[tuple[str, float], ...] = (
    ("flash", 1.0),
    ("mini", 0.9),
    ("turbo", 0.8),
    ("fast", 0.7),
    ("lite", 0.6),
    ("nano", 0.5),
)
_HEAVY_VARIANT_TERMS: tuple[tuple[str, float], ...] = (
    ("large", 0.5),
    ("pro", 0.4),
    ("max", 0.4),
    ("reasoning", 0.3),
    ("thinking", 0.3),
    ("preview", 0.2),
)


@dataclass(frozen=True, slots=True)
class ModelRecommendation:
    slug: str
    model: str
    display_name: str
    is_free: bool
    score: float
    reasons: tuple[str, ...]


def recommended_model_choices(
    pc: ProviderConfig | None = None,
    *,
    refresh_live: bool = False,
    limit: int = _DEFAULT_RECOMMENDATION_LIMIT,
    query: str = "",
    current_model: str = "",
) -> list[ModelRecommendation]:
    pc = pc or ProviderConfig.load()
    choices = configured_model_choices(pc, refresh_live=refresh_live)
    choices = _filtered_choices(choices, query)
    active = pc.get_active()
    active_slug = active.slug if active is not None else ""
    active_model = current_model or (active.resolved_model if active is not None else "")
    registry = get_provider_registry()
    recommendations = [
        _recommendation(
            pc,
            choice,
            info=registry.get(choice[1], provider=choice[0]),
            active_slug=active_slug,
            current_model=active_model,
        )
        for choice in choices
    ]
    recommendations.sort(key=_recommendation_sort_key)
    return recommendations if limit <= 0 else recommendations[:limit]


def _filtered_choices(choices: list[ModelChoice], query: str) -> list[ModelChoice]:
    normalized = query.strip().casefold()
    if not normalized:
        return choices
    return [
        choice
        for choice in choices
        if normalized in f"{choice[0]} {choice[1]} {choice[2]}".casefold()
    ]


def _recommendation(
    pc: ProviderConfig,
    choice: ModelChoice,
    *,
    info: ModelInfo | None,
    active_slug: str,
    current_model: str,
) -> ModelRecommendation:
    slug, model, display_name, is_free = choice
    provider = pc.providers[slug]
    is_current = slug == active_slug and model == current_model
    score = _recommendation_score(
        info,
        model=model,
        is_free=is_free,
        endpoint=provider.endpoint,
        is_active_provider=slug == active_slug,
        is_current=is_current,
    )
    reasons = _recommendation_reasons(
        info,
        model=model,
        is_free=is_free,
        endpoint=provider.endpoint,
        is_current=is_current,
    )
    return ModelRecommendation(
        slug=slug,
        model=model,
        display_name=display_name,
        is_free=is_free,
        score=score,
        reasons=reasons,
    )


def _recommendation_score(
    info: ModelInfo | None,
    *,
    model: str,
    is_free: bool,
    endpoint: str,
    is_active_provider: bool,
    is_current: bool,
) -> float:
    score = 0.4 if is_free else 0.0
    if info is not None:
        score += _cost_score(info, is_free=is_free)
        score += _context_score(info.context_window)
        score += _output_score(info.max_output)
        score += _tag_score(info)
        score += _variant_score(model)
    if is_keyless_endpoint(endpoint):
        score += 0.4
    if is_active_provider:
        score += 0.2
    if is_current:
        score += 0.15
    return score


def _cost_score(info: ModelInfo, *, is_free: bool) -> float:
    if is_free:
        return 1.0
    total = info.prompt_price_per_1k + info.completion_price_per_1k
    if total <= 0.001:
        return 1.4
    if total <= 0.005:
        return 1.0
    if total <= 0.02:
        return 0.4
    return -0.5


def _context_score(context_window: int) -> float:
    if context_window >= 1_000_000:
        return 1.4
    if context_window >= 128_000:
        return 1.0
    if context_window >= 64_000:
        return 0.5
    return 0.0


def _output_score(max_output: int) -> float:
    if max_output >= 32_000:
        return 0.5
    if max_output >= 16_000:
        return 0.4
    if max_output >= 8_192:
        return 0.2
    return 0.0


def _tag_score(info: ModelInfo) -> float:
    tags = set(info.tags)
    score = 0.0
    if "recommended" in tags:
        score += 1.2
    if "tools" in tags or info.supports_tools:
        score += 0.5
    if "reasoning" in tags:
        score += 0.3
    if "router" in tags:
        score -= 1.0
    return score


def _variant_score(model: str) -> float:
    normalized = model.casefold()
    fast_score = max(
        (score for term, score in _FAST_VARIANT_TERMS if term in normalized),
        default=0.0,
    )
    heavy_penalty = sum(score for term, score in _HEAVY_VARIANT_TERMS if term in normalized)
    return fast_score - heavy_penalty


def _recommendation_reasons(
    info: ModelInfo | None,
    *,
    model: str,
    is_free: bool,
    endpoint: str,
    is_current: bool,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if is_current:
        reasons.append("current")
    if is_free:
        reasons.append("free")
    elif info is not None and _cost_score(info, is_free=False) >= 1.0:
        reasons.append("low estimated cost")
    if _speed_term(model):
        reasons.append("speed-oriented variant")
    if info is not None:
        if info.context_window >= 128_000:
            reasons.append(f"{info.context_window // 1000}k context")
        if "recommended" in info.tags:
            reasons.append("strong default")
        if "tools" in info.tags or info.supports_tools:
            reasons.append("tool-capable")
        if "reasoning" in info.tags:
            reasons.append("reasoning-capable")
    if is_keyless_endpoint(endpoint):
        reasons.append("no API key needed")
    if not reasons:
        reasons.append("available now")
    return tuple(dict.fromkeys(reasons))[:4]


def _speed_term(model: str) -> str:
    normalized = model.casefold()
    return next((term for term, _score in _FAST_VARIANT_TERMS if term in normalized), "")


def _recommendation_sort_key(
    recommendation: ModelRecommendation,
) -> tuple[float, str, str, str]:
    return (
        -recommendation.score,
        recommendation.display_name.casefold(),
        recommendation.model.casefold(),
        recommendation.slug.casefold(),
    )
