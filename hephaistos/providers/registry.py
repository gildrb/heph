"""Model registry: unified catalog of models, context windows, and pricing.

Centralizes model metadata that was previously scattered across
``chat/usage.py`` and ``providers/config.py``.  The registry provides:

- Context window sizes per model
- Pricing (prompt + completion per 1K tokens)
- Capabilities (reasoning, tool support, vision)
- Provider mapping (which endpoint serves which model)
- Lookup by model name (with prefix matching)

Loaded once at startup and used by the context budget manager,
the model picker, and cost tracking.
"""

from __future__ import annotations

import functools
from dataclasses import dataclass

from hephaistos.logging import get_logger
from hephaistos.providers.model_support import is_supported_model_for_provider

_log = get_logger("providers.registry")


@dataclass(frozen=True)
class ModelInfo:
    """Metadata for a single model."""

    name: str  # canonical name (e.g. "openai/gpt-5.4")
    provider: str  # provider slug (e.g. "openrouter", "openai-codex")
    display_name: str  # human-readable name
    context_window: int  # max context tokens
    max_output: int  # max completion tokens
    prompt_price_per_1k: float  # USD per 1K prompt tokens
    completion_price_per_1k: float  # USD per 1K completion tokens
    tags: tuple[str, ...] = ()

    @property
    def is_free(self) -> bool:
        return self.prompt_price_per_1k == 0 and self.completion_price_per_1k == 0


_BUILTIN_MODELS: list[ModelInfo] = [
    # --- OpenAI ---
    ModelInfo("gpt-5.4", "openai-codex", "GPT-5.4", 128_000, 16_384, 0.002, 0.008),
    ModelInfo(
        "gpt-5.4-mini",
        "openai-codex",
        "GPT-5.4 Mini",
        128_000,
        16_384,
        0.00015,
        0.0006,
        tags=("study",),
    ),
    ModelInfo("gpt-5.4-pro", "openai-codex", "GPT-5.4 Pro", 128_000, 16_384, 0.005, 0.015),
    ModelInfo(
        "gpt-5.4-nano",
        "openai-codex",
        "GPT-5.4 Nano",
        128_000,
        16_384,
        0.00005,
        0.0002,
        tags=("study",),
    ),
    ModelInfo("gpt-5.3-codex", "openai-codex", "GPT-5.3 Codex", 128_000, 16_384, 0.002, 0.008),
    ModelInfo("gpt-5.2-codex", "openai-codex", "GPT-5.2 Codex", 128_000, 16_384, 0.002, 0.008),
    ModelInfo("gpt-5.2", "openai-codex", "GPT-5.2", 128_000, 16_384, 0.002, 0.008),
    ModelInfo(
        "gpt-5.1-codex-max",
        "openai-codex",
        "GPT-5.1 Codex Max",
        128_000,
        16_384,
        0.005,
        0.015,
    ),
    ModelInfo(
        "gpt-5.1-codex-mini",
        "openai-codex",
        "GPT-5.1 Codex Mini",
        128_000,
        16_384,
        0.0005,
        0.0015,
    ),
    ModelInfo(
        "gpt-5.3-codex-spark",
        "openai-codex",
        "GPT-5.3 Codex Spark",
        128_000,
        16_384,
        0.001,
        0.003,
    ),
    ModelInfo("gpt-4o", "openai-codex", "GPT-4o", 128_000, 16_384, 0.0025, 0.01),
    ModelInfo("gpt-4o-mini", "openai-codex", "GPT-4o Mini", 128_000, 16_384, 0.00015, 0.0006),
    # --- Google (via OpenRouter) ---
    ModelInfo(
        "google/gemini-3-pro-preview",
        "openrouter",
        "Gemini 3 Pro",
        1_000_000,
        8_192,
        0.00125,
        0.005,
        tags=("google", "study"),
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
        tags=("qwen", "free", "study"),
    ),
    ModelInfo(
        "qwen/qwen3.5-plus-02-15",
        "openrouter",
        "Qwen 3.5 Plus",
        32_000,
        8_192,
        0.0004,
        0.0012,
        tags=("qwen", "study"),
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
        tags=("study",),
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
        tags=("free", "study"),
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
    """Return the built-in model catalog (constructed lazily on first access)."""
    return list(_BUILTIN_MODELS)


class ModelRegistry:
    """Lookup table for model metadata."""

    def __init__(self, models: list[ModelInfo] | None = None) -> None:
        self._models: dict[str, ModelInfo] = {}
        for m in models or builtin_models():
            if not is_supported_model_for_provider(m.name, m.provider):
                continue
            self._models[m.name] = m

    def get(self, model_name: str) -> ModelInfo | None:
        """Look up a model by exact name, then provider-prefix match."""
        if model_name in self._models:
            return self._models[model_name]

        # Try stripping provider prefix: "openai/gpt-5.4" -> "gpt-5.4"
        if "/" in model_name:
            _, short = model_name.rsplit("/", 1)
            if short in self._models:
                return self._models[short]

        # Try adding provider prefixes: "gpt-5.4" -> "openai/gpt-5.4"
        for key, info in self._models.items():
            if "/" in key and key.rsplit("/", 1)[1] == model_name:
                return info

        return None

    def get_context_window(self, model_name: str) -> int:
        """Get context window size, with fallback."""
        info = self.get(model_name)
        return info.context_window if info else 128_000

    def list_models(self, provider: str | None = None) -> list[ModelInfo]:
        """List all known models, optionally filtered by provider."""
        models = list(self._models.values())
        if provider:
            models = [m for m in models if m.provider == provider]
        return sorted(models, key=lambda m: (m.provider, m.name))

    def register(self, model: ModelInfo) -> None:
        """Add or replace a model in the registry."""
        if not is_supported_model_for_provider(model.name, model.provider):
            return
        self._models[model.name] = model


_registry: ModelRegistry | None = None


def get_registry() -> ModelRegistry:
    """Get the global model registry (lazy-loaded)."""
    global _registry  # noqa: PLW0603
    if _registry is None:
        _registry = ModelRegistry()
    return _registry
