"""Model and provider management commands."""

from __future__ import annotations

from hephaistos.chat.model_selection import switch_model
from hephaistos.commands._base import Command, CommandResult, ensure_session
from hephaistos.diagnostics.events import capture as capture_analytics
from hephaistos.providers.config import ProviderConfig
from hephaistos.providers.endpoints import is_keyless_endpoint
from hephaistos.providers.model_choices import configured_model_choices, model_free_description
from hephaistos.providers.registry import get_registry as get_provider_registry
from hephaistos.terminal import (
    STYLE_DIM,
    MenuOption,
    print_error,
    print_info,
    print_success,
    select_option,
    styled,
)


class ModelsCommand(Command):
    name = "models"
    description = "Pick the active model"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        query = args.strip().lower()
        pc = ProviderConfig.load()
        choices = configured_model_choices(pc)
        if query:
            choices = [
                choice
                for choice in choices
                if query in choice[1].lower() or query in choice[2].lower()
            ]

        if not choices:
            key_label = (
                "not needed (free provider)"
                if is_keyless_endpoint(s.config.base_url)
                else ("configured" if s.config.resolved_api_key else styled("not set", STYLE_DIM))
            )
            lines = [
                f"  Model:   {s.config.model}",
                f"  API:     {s.config.base_url}",
                f"  Key:     {key_label}",
                "",
                "  No matching models available. Use /login to connect a provider.",
            ]
            print("\n".join(lines))
            return CommandResult()

        active = pc.get_active()
        current_model = s.config.model
        options: list[MenuOption] = []
        model_map: list[tuple[str, str]] = []
        for slug, model, display_name, is_free in choices:
            is_current = active is not None and active.slug == slug and model == current_model
            desc = f"via {display_name}"
            if is_free:
                desc += f"  {model_free_description(pc.providers[slug].endpoint)}"
            if is_current:
                desc += "  current"
            options.append(MenuOption(model, desc, is_current=is_current))
            model_map.append((slug, model))

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


class RecommendCommand(Command):
    name = "recommend"
    description = "Recommend models for sessions"

    def handle(self, session: object, args: str) -> CommandResult:
        del session, args
        registry = get_provider_registry()
        models = [model for model in registry.list_models() if "study" in model.tags]
        if not models:
            print_info("No recommended models in registry.")
            return CommandResult()
        print_info(
            "Model picks favor low cost, speed, and instruction following because "
            "Heph handles RAG retrieval and citation checks."
        )
        for model in models:
            price = (
                "free"
                if model.is_free
                else (f"${model.prompt_price_per_1k:.4f}/${model.completion_price_per_1k:.4f}")
            )
            ctx = f"{model.context_window // 1000}k ctx"
            tags = f" [{', '.join(model.tags)}]" if model.tags else ""
            print(f"  {model.name:<45} {ctx:<12} {price}{tags}")
        print()
        return CommandResult()
