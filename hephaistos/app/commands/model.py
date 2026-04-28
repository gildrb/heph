"""Model and provider management commands."""

from __future__ import annotations

from hephaistos.analytics import capture as capture_analytics
from hephaistos.app.commands._base import Command, CommandResult, ensure_session
from hephaistos.app.display import STYLE_DIM, print_error, print_info, print_success, styled
from hephaistos.app.menu import MenuOption, select_option
from hephaistos.app.palette import STYLE_PROMPT
from hephaistos.chat.engine import is_keyless_endpoint
from hephaistos.chat.session import ChatSession
from hephaistos.providers.config import ProviderConfig
from hephaistos.providers.model_support import is_supported_model_for_endpoint
from hephaistos.providers.registry import get_registry as get_provider_registry


class ModelCommand(Command):
    name = "model"
    description = "Show or switch the active model"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        if args.strip():
            model_name = args.strip()
            if not is_supported_model_for_endpoint(model_name, s.config.base_url):
                print_error("Model unavailable.")
                return CommandResult()
            old = s.config.model
            s.config.model = model_name
            print_success(f"Model: {old} -> {s.config.model}")
            capture_analytics("model_changed", {"from_model": old, "to_model": s.config.model})
            return CommandResult()
        pc = ProviderConfig.load()
        active = pc.get_active()
        current_model = s.config.model
        options: list[MenuOption] = []
        model_map: list[tuple[str, str]] = []  # parallel to options: (slug, model)

        for slug, provider in pc.providers.items():
            if slug == "custom" and not provider.models:
                continue
            for model in provider.models:
                is_current = (provider.active and model == current_model) or (
                    not active and model == current_model
                )
                desc = f"via {provider.display_name}"
                if is_current:
                    desc += " ← current"
                options.append(MenuOption(model, desc, is_current=is_current))
                model_map.append((slug, model))

        if not options:
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
                "  No models configured. Use /provider to set up providers.",
            ]
            print("\n".join(lines))
            return CommandResult()

        selected = select_option("Model", options)
        if selected is None:
            return CommandResult()

        slug, model = model_map[selected]
        pc.set_active(slug)
        p = pc.providers[slug]
        p.current_model = model
        pc.apply_to_config(s.config)
        pc.save()
        print_success(f"Switched to {p.display_name} / {model}")
        capture_analytics(
            "model_changed",
            {
                "provider": slug,
                "to_model": model,
            },
        )
        return CommandResult()


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
    description = "List all available models across providers"

    def handle(self, session: object, args: str) -> CommandResult:
        registry = get_provider_registry()
        models = registry.list_models()
        if args.strip().lower() == "study":
            models = [model for model in models if "study" in model.tags]

        if not models:
            print_info("No models in registry.")
            return CommandResult()
        if args.strip().lower() == "study":
            print_info(
                "Study picks favor low cost, speed, and instruction following because "
                "Hephaistos handles RAG retrieval and citation checks."
            )
        current_provider = ""
        for m in models:
            if m.provider != current_provider:
                current_provider = m.provider
                print(f"\n  {styled(current_provider, STYLE_PROMPT)}")

            price = (
                f"${m.prompt_price_per_1k:.4f}/${m.completion_price_per_1k:.4f}"
                if not m.is_free
                else "free"
            )
            ctx = f"{m.context_window // 1000}k ctx"
            tags = f" [{', '.join(m.tags)}]" if m.tags else ""
            print(f"    {m.name:<45} {ctx:<12} {price}{tags}")

        print()
        return CommandResult()


class RecommendCommand(Command):
    name = "recommend"
    description = "Recommend models for study sessions"

    def handle(self, session: object, args: str) -> CommandResult:
        return ModelsCommand().handle(session, "study")
