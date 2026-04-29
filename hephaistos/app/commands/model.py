"""Model and provider management commands."""

from __future__ import annotations

from hephaistos.analytics import capture as capture_analytics
from hephaistos.app.commands._base import Command, CommandResult, ensure_session
from hephaistos.app.display import STYLE_DIM, print_error, print_info, print_success, styled
from hephaistos.app.menu import MenuOption, select_option
from hephaistos.app.model_picker import configured_model_choices, switch_model
from hephaistos.chat.engine import is_keyless_endpoint
from hephaistos.chat.session import ChatSession
from hephaistos.providers.config import ProviderConfig
from hephaistos.providers.registry import get_registry as get_provider_registry


class ProviderCommand(Command):
    name = "provider"
    description = "Show or switch LLM provider and model"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        pc = ProviderConfig.load()
        parts = args.strip().split()

        if not parts:
            return self._show(pc)

        sub = parts[0].lower()
        if sub == "use" and len(parts) >= 2:
            slug = parts[1].lower()
            model = parts[2] if len(parts) >= 3 else ""
            return self._use(pc, s, slug, model)
        if sub == "model" and len(parts) >= 2:
            return self._set_model(pc, s, parts[1])

        print_error("Usage: /provider [use <slug> [model] | model <name>]")
        return CommandResult()

    @staticmethod
    def _show(pc: ProviderConfig) -> CommandResult:
        active = pc.get_active()
        if active:
            print(f"  Current: {active.resolved_model} via {active.display_name}")
        else:
            print_info("No active provider configured.")
        print()
        print("  Configured providers & models:")

        for slug, p in pc.providers.items():
            bracket = f"    [{slug}]"
            if p.active:
                bracket += " \u2190 active"
            print(bracket)

            if slug == "custom":
                print(f"      endpoint: {p.endpoint}")
                print(f"      {styled('(use /provider use custom <model> to set)', STYLE_DIM)}")
            else:
                for m in p.models:
                    line = f"      {m}"
                    if p.active and m == p.current_model:
                        line += " \u2190 current"
                    print(line)
            print()

        return CommandResult()

    @staticmethod
    def _use(pc: ProviderConfig, session: ChatSession, slug: str, model: str) -> CommandResult:
        if slug not in pc.providers:
            print_error(f"Unknown provider: {slug}")
            print_info(f"Available: {', '.join(pc.providers)}")
            return CommandResult()

        pc.set_active(slug)
        p = pc.providers[slug]

        if model:
            if model in p.models:
                p.current_model = model
            elif p.models:
                print_error(f"Model '{model}' not found in {slug}")
                print_info(f"Available: {', '.join(p.models)}")
                pc.apply_to_config(session.config)
                pc.save()
                return CommandResult()
        elif not p.current_model and p.models:
            p.current_model = p.models[0]

        pc.apply_to_config(session.config)
        pc.save()
        print_success(f"Switched to {p.display_name} / {p.resolved_model}")
        capture_analytics(
            "provider_changed",
            {
                "provider": slug,
                "model": p.resolved_model,
            },
        )
        return CommandResult()

    @staticmethod
    def _set_model(pc: ProviderConfig, session: ChatSession, model: str) -> CommandResult:
        active = pc.get_active()
        if active is None:
            print_error("No active provider. Use /provider use <slug> first.")
            return CommandResult()
        if model not in active.models:
            print_error(f"Model '{model}' not found in {active.slug}")
            print_info(f"Available: {', '.join(active.models)}")
            return CommandResult()

        active.current_model = model
        pc.apply_to_config(session.config)
        pc.save()
        print_success(f"Model: {model}")
        capture_analytics(
            "model_changed",
            {
                "provider": active.slug,
                "to_model": model,
            },
        )
        return CommandResult()


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
                "  No matching models configured. Use /provider to set up providers.",
            ]
            print("\n".join(lines))
            return CommandResult()

        active = pc.get_active()
        current_model = s.config.model
        choices = sorted(
            choices,
            key=lambda choice: 0
            if active is not None and active.slug == choice[0] and choice[1] == current_model
            else 1,
        )
        options: list[MenuOption] = []
        model_map: list[tuple[str, str]] = []
        for slug, model, display_name, is_free in choices:
            is_current = active is not None and active.slug == slug and model == current_model
            desc = f"via {display_name}"
            if is_free:
                desc += "  free"
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
    description = "Recommend models for study sessions"

    def handle(self, session: object, args: str) -> CommandResult:
        registry = get_provider_registry()
        models = [model for model in registry.list_models() if "study" in model.tags]
        if not models:
            print_info("No study models in registry.")
            return CommandResult()
        print_info(
            "Study picks favor low cost, speed, and instruction following because "
            "Hephaistos handles RAG retrieval and citation checks."
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
