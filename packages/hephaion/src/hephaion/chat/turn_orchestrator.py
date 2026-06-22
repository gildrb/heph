"""Composable turn orchestrator implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ai.runtime.errors import RetryConfig

from hephaion.chat.armory_turn import ArmoryTurnMixin
from hephaion.chat.turn_execution import TurnExecutionMixin
from hephaion.chat.turn_finalization import TurnFinalizationMixin
from hephaion.chat.turn_lifecycle import TurnLifecycleMixin
from hephaion.learning.actions import AttemptAction

if TYPE_CHECKING:
    from hephaion.chat.session import ChatSession


@dataclass(slots=True)
class TurnOrchestrator(
    TurnLifecycleMixin,
    ArmoryTurnMixin,
    TurnExecutionMixin,
    TurnFinalizationMixin,
):
    """Compose turn lifecycle, planning, execution, and finalization services."""

    session: ChatSession
    retry: RetryConfig | None = None
    last_reply: str = field(default="", init=False)
    last_internal_passes: int = field(default=1, init=False)
    _last_reply_citation_required: bool | None = field(default=None, init=False)
    _learning_action_override: AttemptAction | None = field(default=None, init=False)
    _learning_followup_seed_blocked: bool = field(default=False, init=False)
