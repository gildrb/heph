"""Model catalog and lookup helpers."""

from __future__ import annotations

import functools
from dataclasses import dataclass

from providers.model_support import is_supported_model_for_provider


@dataclass(frozen=True)
class ModelInfo:
    name: str  # canonical name (e.g. "openai/gpt-5.4")
    provider: str  # provider slug (e.g. "openrouter", "openai-codex")
    display_name: str  # human-readable name
    context_window: int  # max context tokens
    max_output: int  # max completion tokens
    prompt_price_per_1k: float  # USD per 1K prompt tokens
    completion_price_per_1k: float  # USD per 1K completion tokens
    tags: tuple[str, ...] = ()
    reasoning_efforts: tuple[str, ...] = ()
    input_modalities: tuple[str, ...] = ()
    supports_tools: bool = False

    @property
    def is_free(self) -> bool:
        return self.prompt_price_per_1k == 0 and self.completion_price_per_1k == 0


_OPENAI_MODEL_ROWS: tuple[tuple[str, str, int, int, float, float, tuple[str, ...]], ...] = (
    ("gpt-5.5", "GPT-5.5", 1_000_000, 128_000, 0.005, 0.03, ("recommended", "reasoning")),
    ("gpt-5.4", "GPT-5.4", 128_000, 16_384, 0.002, 0.008, ()),
    ("gpt-5.4-mini", "GPT-5.4 Mini", 128_000, 16_384, 0.00015, 0.0006, ("recommended",)),
    ("gpt-5.4-pro", "GPT-5.4 Pro", 128_000, 16_384, 0.005, 0.015, ()),
    ("gpt-5.4-nano", "GPT-5.4 Nano", 128_000, 16_384, 0.00005, 0.0002, ("recommended",)),
    ("gpt-5.3-codex", "GPT-5.3 Codex", 128_000, 16_384, 0.002, 0.008, ()),
    ("gpt-5.2-codex", "GPT-5.2 Codex", 128_000, 16_384, 0.002, 0.008, ()),
    ("gpt-5.2", "GPT-5.2", 128_000, 16_384, 0.002, 0.008, ()),
    ("gpt-5.1-codex-max", "GPT-5.1 Codex Max", 128_000, 16_384, 0.005, 0.015, ()),
    ("gpt-5.1-codex-mini", "GPT-5.1 Codex Mini", 128_000, 16_384, 0.0005, 0.0015, ()),
    ("gpt-5.3-codex-spark", "GPT-5.3 Codex Spark", 128_000, 16_384, 0.001, 0.003, ()),
    ("gpt-4o", "GPT-4o", 128_000, 16_384, 0.0025, 0.01, ()),
    ("gpt-4o-mini", "GPT-4o Mini", 128_000, 16_384, 0.00015, 0.0006, ()),
)

_DEEPSEEK_MODEL_ROWS: tuple[tuple[str, str, int, int, float, float, tuple[str, ...]], ...] = (
    (
        "deepseek-v4-pro",
        "DeepSeek V4 Pro",
        128_000,
        8_192,
        0.00014,
        0.00028,
        ("recommended", "reasoning", "tools"),
    ),
    (
        "deepseek-v4-flash",
        "DeepSeek V4 Flash",
        128_000,
        8_192,
        0.00003,
        0.00006,
        ("recommended", "reasoning", "tools"),
    ),
    ("deepseek-chat", "DeepSeek Chat", 128_000, 8_192, 0.00014, 0.00028, ("tools",)),
    (
        "deepseek-reasoner",
        "DeepSeek Reasoner",
        64_000,
        8_192,
        0.00014,
        0.00028,
        ("reasoning", "tools"),
    ),
)

_DEEPSEEK_REASONING_EFFORTS = ("high", "xhigh")


def _default_reasoning_efforts(tags: tuple[str, ...]) -> tuple[str, ...]:
    if "reasoning" not in tags:
        return ()
    return ("low", "medium", "high", "xhigh")


def _openai_models(provider: str) -> list[ModelInfo]:
    return [
        ModelInfo(
            name,
            provider,
            display_name,
            context_window,
            max_output,
            prompt_price,
            completion_price,
            tags=tags,
            reasoning_efforts=_default_reasoning_efforts(tags),
            supports_tools="tools" in tags,
        )
        for (
            name,
            display_name,
            context_window,
            max_output,
            prompt_price,
            completion_price,
            tags,
        ) in _OPENAI_MODEL_ROWS
    ]


def _deepseek_models() -> list[ModelInfo]:
    return [
        ModelInfo(
            name,
            "deepseek",
            display_name,
            context_window,
            max_output,
            prompt_price,
            completion_price,
            tags=tags,
            reasoning_efforts=_DEEPSEEK_REASONING_EFFORTS if "reasoning" in tags else (),
            supports_tools="tools" in tags,
        )
        for (
            name,
            display_name,
            context_window,
            max_output,
            prompt_price,
            completion_price,
            tags,
        ) in _DEEPSEEK_MODEL_ROWS
    ]


_POLLINATIONS_MODEL_ROWS: tuple[tuple[str, str, int, int, tuple[str, ...]], ...] = (
    ("openai", "GPT (Pollinations)", 128_000, 16_384, ("free", "recommended")),
    ("openai-large", "GPT Large (Pollinations)", 128_000, 16_384, ("free",)),
    ("openai-reasoning", "o4-mini (Pollinations)", 128_000, 16_384, ("free", "reasoning")),
    ("openai-fast", "GPT Nano (Pollinations)", 128_000, 16_384, ("free",)),
    ("mistral", "Mistral (Pollinations)", 32_000, 8_192, ("free",)),
    ("mistral-large", "Mistral Large (Pollinations)", 32_000, 8_192, ("free",)),
    (
        "mistral-reasoning",
        "Mistral Reasoning (Pollinations)",
        32_000,
        8_192,
        ("free", "reasoning"),
    ),
    ("qwen-coder", "Qwen Coder (Pollinations)", 32_000, 8_192, ("free",)),
    (
        "deepseek-reasoning",
        "DeepSeek Reasoning (Pollinations)",
        64_000,
        8_192,
        ("free", "reasoning"),
    ),
    ("deepseek", "DeepSeek (Pollinations)", 64_000, 8_192, ("free",)),
    ("llama", "Llama (Pollinations)", 32_000, 8_192, ("free",)),
    ("llama-scaleway", "Llama Scaleway (Pollinations)", 32_000, 8_192, ("free",)),
    ("gemini", "Gemini (Pollinations)", 1_000_000, 8_192, ("free",)),
    ("gemini-thinking", "Gemini Thinking (Pollinations)", 1_000_000, 8_192, ("free", "reasoning")),
)


_BUILTIN_MODELS: list[ModelInfo] = [
    # --- Pollinations AI (free, no API key required) ---
    *[
        ModelInfo(
            name,
            "pollinations",
            display_name,
            context_window,
            max_output,
            0.0,
            0.0,
            tags=tags,
        )
        for name, display_name, context_window, max_output, tags in _POLLINATIONS_MODEL_ROWS
    ],
    # --- OpenRouter Free Router ---
    ModelInfo(
        "openrouter/free",
        "openrouter",
        "Free Models Router",
        200_000,
        8_192,
        0.0,
        0.0,
        tags=("free", "router"),
    ),
    # --- OpenAI API ---
    *_openai_models("openai"),
    # --- OpenAI Codex subscription ---
    *_openai_models("openai-codex"),
    # --- DeepSeek API ---
    *_deepseek_models(),
    # --- Google (via OpenRouter) ---
    ModelInfo(
        "google/gemini-3-pro-preview",
        "openrouter",
        "Gemini 3 Pro",
        1_000_000,
        8_192,
        0.00125,
        0.005,
        tags=("google", "recommended"),
    ),
    ModelInfo(
        "google/gemini-3-flash-preview",
        "openrouter",
        "Gemini 3 Flash",
        1_000_000,
        8_192,
        0.000075,
        0.0003,
        tags=("google",),
    ),
    ModelInfo(
        "google/gemini-3.1-pro-preview",
        "openrouter",
        "Gemini 3.1 Pro",
        1_000_000,
        8_192,
        0.00125,
        0.005,
        tags=("google",),
    ),
    ModelInfo(
        "google/gemini-3.1-flash-lite-preview",
        "openrouter",
        "Gemini 3.1 Flash Lite",
        1_000_000,
        8_192,
        0.00003,
        0.0001,
        tags=("google",),
    ),
    # --- Qwen (via OpenRouter) ---
    ModelInfo(
        "qwen/qwen3.6-plus:free",
        "openrouter",
        "Qwen 3.6 Plus (free)",
        32_000,
        8_192,
        0.0,
        0.0,
        tags=("qwen", "free", "recommended"),
    ),
    ModelInfo(
        "qwen/qwen3.5-plus-02-15",
        "openrouter",
        "Qwen 3.5 Plus",
        32_000,
        8_192,
        0.0004,
        0.0012,
        tags=("qwen", "recommended"),
    ),
    ModelInfo(
        "qwen/qwen3.5-35b-a3b",
        "openrouter",
        "Qwen 3.5 35B",
        32_000,
        8_192,
        0.0001,
        0.0003,
        tags=("qwen",),
    ),
    # --- Z.AI / GLM ---
    ModelInfo("glm-5", "zai", "GLM-5", 128_000, 8_192, 0.001, 0.001),
    ModelInfo("glm-5-turbo", "zai", "GLM-5 Turbo", 128_000, 8_192, 0.0001, 0.0001),
    ModelInfo("glm-4.7", "zai", "GLM-4.7", 128_000, 8_192, 0.0005, 0.0005),
    ModelInfo("glm-4.5", "zai", "GLM-4.5", 128_000, 8_192, 0.0003, 0.0003),
    ModelInfo(
        "glm-4.5-flash",
        "zai",
        "GLM-4.5 Flash",
        128_000,
        8_192,
        0.00005,
        0.00005,
        tags=("recommended",),
    ),
    ModelInfo(
        "z-ai/glm-5",
        "openrouter",
        "GLM-5 (OpenRouter)",
        128_000,
        8_192,
        0.001,
        0.001,
        tags=("zai",),
    ),
    ModelInfo(
        "z-ai/glm-5-turbo",
        "openrouter",
        "GLM-5 Turbo (OpenRouter)",
        128_000,
        8_192,
        0.0001,
        0.0001,
        tags=("zai",),
    ),
    # --- Other (via OpenRouter) ---
    ModelInfo(
        "stepfun/step-3.5-flash",
        "openrouter",
        "Step 3.5 Flash",
        32_000,
        8_192,
        0.0001,
        0.0003,
    ),
    ModelInfo("minimax/minimax-m2.7", "openrouter", "MiniMax M2.7", 32_000, 8_192, 0.0002, 0.0006),
    ModelInfo("minimax/minimax-m2.5", "openrouter", "MiniMax M2.5", 32_000, 8_192, 0.0001, 0.0003),
    ModelInfo("moonshotai/kimi-k2.5", "openrouter", "Kimi K2.5", 32_000, 8_192, 0.0002, 0.0006),
    ModelInfo("xiaomi/mimo-v2-pro", "openrouter", "MiMo V2 Pro", 32_000, 8_192, 0.0001, 0.0003),
    ModelInfo("x-ai/grok-4.20-beta", "openrouter", "Grok 4.20 Beta", 128_000, 8_192, 0.003, 0.015),
    ModelInfo(
        "nvidia/nemotron-3-super-120b-a12b",
        "openrouter",
        "Nemotron 3 Super",
        32_000,
        8_192,
        0.0002,
        0.0006,
    ),
    ModelInfo(
        "nvidia/nemotron-3-super-120b-a12b:free",
        "openrouter",
        "Nemotron 3 Super (free)",
        32_000,
        8_192,
        0.0,
        0.0,
        tags=("free", "recommended"),
    ),
    ModelInfo(
        "arcee-ai/trinity-large-preview:free",
        "openrouter",
        "Trinity Large (free)",
        32_000,
        8_192,
        0.0,
        0.0,
        tags=("free",),
    ),
]


@functools.lru_cache(maxsize=1)
def builtin_models() -> list[ModelInfo]:
    return list(_BUILTIN_MODELS)


class ModelRegistry:
    def __init__(self, models: list[ModelInfo] | None = None) -> None:
        self._models: dict[str, ModelInfo] = {}
        self._models_by_provider: dict[tuple[str, str], ModelInfo] = {}
        for m in models or builtin_models():
            self.register(m)

    def get(self, model_name: str, provider: str | None = None) -> ModelInfo | None:
        if provider is not None:
            return self._get_provider_model(model_name, provider)
        return self._get_unscoped_model(model_name)

    def _get_provider_model(self, model_name: str, provider: str) -> ModelInfo | None:
        return self._models_by_provider.get((provider, model_name)) or (
            self._get_provider_model_alias(model_name, provider)
        )

    def _get_unscoped_model(self, model_name: str) -> ModelInfo | None:
        return (
            self._models.get(model_name)
            or self._get_short_model_name(model_name)
            or self._get_prefixed_model_name(model_name)
        )

    def _get_short_model_name(self, model_name: str) -> ModelInfo | None:
        if "/" in model_name:
            _, short = model_name.rsplit("/", 1)
            return self._models.get(short)
        return None

    def _get_prefixed_model_name(self, model_name: str) -> ModelInfo | None:
        for key, info in self._models.items():
            if "/" in key and key.rsplit("/", 1)[1] == model_name:
                return info
        return None

    def _get_provider_model_alias(self, model_name: str, provider: str) -> ModelInfo | None:
        if info := self._get_provider_short_alias(model_name, provider):
            return info
        return self._get_provider_suffix_alias(model_name, provider)

    def _get_provider_short_alias(self, model_name: str, provider: str) -> ModelInfo | None:
        if "/" not in model_name:
            return None
        _, short = model_name.rsplit("/", 1)
        return self._models_by_provider.get((provider, short))

    def _get_provider_suffix_alias(self, model_name: str, provider: str) -> ModelInfo | None:
        for provider_model, info in self._models_by_provider.items():
            model_provider, registered_name = provider_model
            if model_provider == provider and registered_name.rsplit("/", 1)[-1] == model_name:
                return info
        return None

    def get_context_window(self, model_name: str) -> int:
        info = self.get(model_name)
        return info.context_window if info else 128_000

    def list_models(self, provider: str | None = None) -> list[ModelInfo]:
        models = (
            (m for m in self._models_by_provider.values() if m.provider == provider)
            if provider
            else self._models.values()
        )
        return sorted(models, key=lambda m: (m.provider, m.name))

    def register(self, model: ModelInfo) -> None:
        if not is_supported_model_for_provider(model.name, model.provider):
            return
        self._models_by_provider[(model.provider, model.name)] = model
        existing = self._models.get(model.name)
        if existing is None or existing.provider == model.provider:
            self._models[model.name] = model


_registry: ModelRegistry | None = None


def get_registry() -> ModelRegistry:
    global _registry  # noqa: PLW0603
    if _registry is None:
        _registry = ModelRegistry()
    return _registry
