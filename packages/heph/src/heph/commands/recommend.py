"""Model recommendation slash command."""

from __future__ import annotations

from heph_ai.providers.config import ProviderConfig
from heph_ai.providers.model_recommendations import recommended_model_choices

from heph.commands._base import Command, CommandResult, ensure_session


class RecommendCommand(Command):
    name = "recommend"
    description = "List recommended model picks"

    def handle(self, session: object, args: str) -> CommandResult:
        s = ensure_session(session)
        query = args.strip()
        recommendations = recommended_model_choices(
            ProviderConfig.load(),
            query=query,
            current_model=s.config.model,
        )
        print("Model picks (recommended):")
        if not recommendations:
            print("  No matching models found.")
            return CommandResult()
        for recommendation in recommendations:
            reasons = ", ".join(recommendation.reasons)
            print(f"  {recommendation.display_name}: {recommendation.model} ({reasons})")
        return CommandResult()
