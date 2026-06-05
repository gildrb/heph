"""Serializable snapshots of completed chat turns."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime

from _types import is_object_list, is_string_mapping
from rag import TurnEvidence
from runtime import Conversation
from study import LearningState

from chat.turn_contract import TurnContract


@dataclass(frozen=True, slots=True)
class TurnSnapshot:
    turn_id: str
    user_input: str
    assistant_reply: str
    message_count: int
    user_message_index: int
    assistant_message_index: int
    plan_intent: str = ""
    contract: TurnContract | None = None
    evidence: TurnEvidence | None = None
    learning_state: LearningState = field(default_factory=LearningState)
    created_at: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "turn_id": self.turn_id,
            "user_input": self.user_input,
            "assistant_reply": self.assistant_reply,
            "message_count": self.message_count,
            "user_message_index": self.user_message_index,
            "assistant_message_index": self.assistant_message_index,
            "plan_intent": self.plan_intent,
            "contract": self.contract.to_dict() if self.contract is not None else {},
            "evidence": self.evidence.to_dict() if self.evidence is not None else {},
            "learning_state": self.learning_state.to_dict(),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: object) -> TurnSnapshot | None:
        if not is_string_mapping(payload):
            return None
        turn_id = _payload_string(payload, "turn_id").upper()
        user_input = _payload_string(payload, "user_input")
        assistant_reply = _payload_string(payload, "assistant_reply")
        message_count = _payload_int(payload, "message_count")
        user_message_index = _payload_int(payload, "user_message_index")
        assistant_message_index = _payload_int(payload, "assistant_message_index")
        if not turn_id or not user_input or not assistant_reply or message_count < 1:
            return None
        return cls(
            turn_id=turn_id,
            user_input=user_input,
            assistant_reply=assistant_reply,
            message_count=message_count,
            user_message_index=user_message_index,
            assistant_message_index=assistant_message_index,
            plan_intent=_payload_string(payload, "plan_intent"),
            contract=TurnContract.from_dict(payload.get("contract")),
            evidence=TurnEvidence.from_dict(payload.get("evidence")),
            learning_state=LearningState.from_dict(payload.get("learning_state")),
            created_at=_payload_string(payload, "created_at"),
        )


def turn_history_from_payload(payload: object) -> list[TurnSnapshot]:
    if not is_object_list(payload):
        return []
    return [
        snapshot
        for raw_snapshot in payload
        if (snapshot := TurnSnapshot.from_dict(raw_snapshot)) is not None
    ]


def build_turn_snapshot(
    conversation: Conversation,
    existing: Sequence[TurnSnapshot],
    *,
    learning_state: LearningState,
    user_input: str,
    assistant_reply: str,
    evidence: TurnEvidence | None,
    plan_intent: str,
    contract: TurnContract | None,
) -> TurnSnapshot | None:
    assistant_index = _last_role_index(conversation, "assistant")
    if assistant_index is None:
        return None
    user_index = _last_role_index_before(conversation, "user", assistant_index)
    if user_index is None:
        return None
    return TurnSnapshot(
        turn_id=f"T{len(existing) + 1}",
        user_input=conversation.messages[user_index].content or user_input,
        assistant_reply=conversation.messages[assistant_index].content or assistant_reply,
        message_count=assistant_index + 1,
        user_message_index=user_index,
        assistant_message_index=assistant_index,
        plan_intent=plan_intent,
        contract=contract,
        evidence=evidence,
        learning_state=learning_state.clone(),
        created_at=datetime.now(UTC).isoformat(),
    )


def turn_history_through(
    snapshots: Sequence[TurnSnapshot],
    selected: TurnSnapshot,
) -> list[TurnSnapshot]:
    return [snapshot for snapshot in snapshots if snapshot.message_count <= selected.message_count]


def turn_snapshot_by_id(
    snapshots: Sequence[TurnSnapshot],
    turn_id: str,
) -> TurnSnapshot | None:
    normalized = turn_id.strip().upper()
    for snapshot in snapshots:
        if snapshot.turn_id == normalized:
            return snapshot
    return None


def _last_role_index(conversation: Conversation, role: str) -> int | None:
    for index in range(len(conversation.messages) - 1, -1, -1):
        if conversation.messages[index].role == role:
            return index
    return None


def _last_role_index_before(
    conversation: Conversation,
    role: str,
    before_index: int,
) -> int | None:
    for index in range(before_index - 1, -1, -1):
        if conversation.messages[index].role == role:
            return index
    return None


def _payload_string(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    return value.strip() if isinstance(value, str) else ""


def _payload_int(payload: Mapping[str, object], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, int):
        return value
    return 0
