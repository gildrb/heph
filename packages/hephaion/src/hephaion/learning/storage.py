"""Armory-local storage for harness learning attempts."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from hephaion._types import is_string_mapping
from hephaion.learning.actions import AttemptAction, parse_attempt_action
from hephaion.learning.observation import AttemptObservation
from hephaion.learning.reward import AttemptReward
from hephaion.rag.context import TurnEvidence

LEARNING_DIR = ".hephaion/learning"
POLICIES_DIR = "policies"
REPLAY_DIR = "replay"
ATTEMPTS_FILE = "attempts.jsonl"
ATTEMPT_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class AttemptRecord:
    session_id: str
    turn_id: str
    action: AttemptAction
    observation: AttemptObservation
    reward: AttemptReward
    user_input: str
    reply: str
    evidence: TurnEvidence | None
    created_at: str
    schema_version: int = ATTEMPT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "session_id": self.session_id,
            "turn_id": self.turn_id,
            "action": self.action.value,
            "observation": self.observation.to_dict(),
            "reward": self.reward.to_dict(),
            "user_input": self.user_input,
            "reply": self.reply,
        }
        if self.evidence is not None:
            payload["evidence"] = self.evidence.to_dict()
        return payload

    @classmethod
    def from_dict(cls, payload: object) -> AttemptRecord | None:
        if not is_string_mapping(payload):
            return None
        session_id = _payload_string(payload, "session_id")
        turn_id = _payload_string(payload, "turn_id")
        created_at = _payload_string(payload, "created_at")
        if not session_id or not turn_id:
            return None
        return cls(
            schema_version=_payload_int(payload, "schema_version", ATTEMPT_SCHEMA_VERSION),
            created_at=created_at or _now(),
            session_id=session_id,
            turn_id=turn_id,
            action=parse_attempt_action(payload.get("action")),
            observation=AttemptObservation.from_dict(payload.get("observation")),
            reward=AttemptReward.from_dict(payload.get("reward")),
            user_input=_payload_string(payload, "user_input"),
            reply=_payload_string(payload, "reply"),
            evidence=TurnEvidence.from_dict(payload.get("evidence")),
        )


class LearningStore:
    def __init__(self, armory_path: Path) -> None:
        self.armory_path = armory_path

    @property
    def root(self) -> Path:
        return self.armory_path / LEARNING_DIR

    @property
    def attempts_path(self) -> Path:
        return self.root / ATTEMPTS_FILE

    @property
    def policies_dir(self) -> Path:
        return self.root / POLICIES_DIR

    @property
    def replay_dir(self) -> Path:
        return self.root / REPLAY_DIR

    def ensure_layout(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.policies_dir.mkdir(parents=True, exist_ok=True)
        self.replay_dir.mkdir(parents=True, exist_ok=True)

    def append_attempt(self, record: AttemptRecord) -> None:
        self.ensure_layout()
        with self.attempts_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    def iter_attempts(self) -> Iterator[AttemptRecord]:
        path = self.attempts_path
        if not path.is_file():
            return
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if record := _record_from_jsonl(line):
                    yield record


def new_attempt_record(
    *,
    session_id: str,
    turn_id: str,
    action: AttemptAction,
    observation: AttemptObservation,
    reward: AttemptReward,
    user_input: str,
    reply: str,
    evidence: TurnEvidence | None,
) -> AttemptRecord:
    return AttemptRecord(
        created_at=_now(),
        session_id=session_id,
        turn_id=turn_id,
        action=action,
        observation=observation,
        reward=reward,
        user_input=user_input,
        reply=reply,
        evidence=evidence,
    )


def _record_from_jsonl(line: str) -> AttemptRecord | None:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return None
    return AttemptRecord.from_dict(payload)


def _payload_string(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    return value if isinstance(value, str) else ""


def _payload_int(payload: Mapping[str, object], key: str, default: int) -> int:
    value = payload.get(key)
    if isinstance(value, bool):
        return default
    return value if isinstance(value, int) else default


def _now() -> str:
    return datetime.now(UTC).isoformat()
