"""Dependency-free exported policy artifacts for runtime harness decisions."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from hephaion._types import is_string_mapping
from hephaion.armory.state_files import (
    armory_state_location,
    read_armory_state_text,
    write_armory_state_text,
)
from hephaion.learning.actions import AttemptAction, parse_attempt_action
from hephaion.learning.observation import AttemptObservation
from hephaion.learning.policy import StaticAttemptPolicy
from hephaion.learning.storage import LearningStore

POLICY_SCHEMA_VERSION = 1
PROMOTED_POLICY_FILE = "promoted-policy.json"
PROMOTION_MANIFEST_FILE = "promotion-manifest.json"


class AttemptPolicyProtocol(Protocol):
    def choose(self, observation: AttemptObservation) -> AttemptAction: ...


@dataclass(frozen=True, slots=True)
class ExportedPolicyArtifact:
    policy_id: str
    created_at: str
    table: Mapping[str, AttemptAction]
    manifest: Mapping[str, object]
    schema_version: int = POLICY_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "policy_id": self.policy_id,
            "created_at": self.created_at,
            "table": {key: action.value for key, action in self.table.items()},
            "manifest": dict(self.manifest),
        }

    @classmethod
    def from_dict(cls, payload: object) -> ExportedPolicyArtifact | None:
        if not is_string_mapping(payload):
            return None
        table_payload = payload.get("table")
        table: dict[str, AttemptAction] = {}
        if is_string_mapping(table_payload):
            for key, raw_action in table_payload.items():
                if isinstance(key, str) and isinstance(raw_action, str):
                    table[key] = parse_attempt_action(raw_action)
        policy_id = _payload_string(payload, "policy_id")
        created_at = _payload_string(payload, "created_at")
        if not policy_id or not created_at:
            return None
        manifest = payload.get("manifest")
        return cls(
            schema_version=_payload_int(payload, "schema_version", POLICY_SCHEMA_VERSION),
            policy_id=policy_id,
            created_at=created_at,
            table=table,
            manifest=manifest if is_string_mapping(manifest) else {},
        )


class ExportedAttemptPolicy(AttemptPolicyProtocol):
    def __init__(self, artifact: ExportedPolicyArtifact) -> None:
        self.artifact = artifact
        self.fallback = StaticAttemptPolicy()

    def choose(self, observation: AttemptObservation) -> AttemptAction:
        return (
            self.artifact.table.get(observation_bucket(observation))
            or self.artifact.table.get(_pre_shape_observation_bucket(observation))
            or self.artifact.table.get(_legacy_observation_bucket(observation))
            or self.fallback.choose(observation)
        )


def observation_bucket(observation: AttemptObservation) -> str:
    return "|".join(
        (
            _citation_bucket(observation),
            _evidence_bucket(observation),
            _relevance_bucket(observation),
            _shape_bucket(observation),
            _source_bucket(observation),
            _length_bucket(observation),
            _overview_bucket(observation),
        )
    )


def _legacy_observation_bucket(observation: AttemptObservation) -> str:
    return "|".join(
        (
            _citation_bucket(observation),
            _evidence_bucket(observation),
            _source_bucket(observation),
            _length_bucket(observation),
            _overview_bucket(observation),
        )
    )


def _pre_shape_observation_bucket(observation: AttemptObservation) -> str:
    return "|".join(
        (
            _citation_bucket(observation),
            _evidence_bucket(observation),
            _relevance_bucket(observation),
            _source_bucket(observation),
            _length_bucket(observation),
            _overview_bucket(observation),
        )
    )


def _citation_bucket(observation: AttemptObservation) -> str:
    citation_state = "citation_ok"
    if observation.citation_required and not observation.has_citations:
        citation_state = "missing_citation"
    elif not observation.all_citations_verified or observation.unverified_citation_count:
        citation_state = "invalid_citation"
    return citation_state


def _evidence_bucket(observation: AttemptObservation) -> str:
    evidence_state = "evidence_ok"
    if observation.evidence_recommended_action == "abstain":
        evidence_state = "abstain_recommended"
    elif not observation.evidence_count:
        evidence_state = "no_evidence"
    elif not observation.evidence_sufficient:
        evidence_state = "thin_evidence"
    return evidence_state


def _relevance_bucket(observation: AttemptObservation) -> str:
    if observation.off_topic_answer:
        return "off_topic"
    if observation.answer_relevance_required and observation.answer_relevance_score < 0.35:
        return "weak_relevance"
    return "relevant"


def _shape_bucket(observation: AttemptObservation) -> str:
    return "bad_shape" if observation.answer_shape_failed else "shape_ok"


def _source_bucket(observation: AttemptObservation) -> str:
    return "multi_source" if observation.distinct_source_count >= 2 else "single_source"


def _length_bucket(observation: AttemptObservation) -> str:
    return "long" if observation.reply_chars > 1200 else "normal"


def _overview_bucket(observation: AttemptObservation) -> str:
    return "overview" if observation.retrieval_strategy == "overview" else "targeted"


def load_runtime_policy(armory_path: Path | None) -> AttemptPolicyProtocol:
    if armory_path is None:
        return StaticAttemptPolicy()
    store = LearningStore(armory_path)
    artifact_path = store.policies_dir / PROMOTED_POLICY_FILE
    manifest_path = store.policies_dir / PROMOTION_MANIFEST_FILE
    artifact = load_exported_policy(artifact_path)
    if artifact is None or not _promotion_manifest_approves(manifest_path, artifact.policy_id):
        return StaticAttemptPolicy()
    return ExportedAttemptPolicy(artifact)


def load_exported_policy(path: Path) -> ExportedPolicyArtifact | None:
    try:
        armory_path, rel_path = armory_state_location(path)
        payload = json.loads(read_armory_state_text(armory_path, rel_path))
    except (OSError, json.JSONDecodeError):
        return None
    return ExportedPolicyArtifact.from_dict(payload)


def write_exported_policy(path: Path, artifact: ExportedPolicyArtifact) -> None:
    armory_path, rel_path = armory_state_location(path)
    write_armory_state_text(
        armory_path,
        rel_path,
        json.dumps(artifact.to_dict(), indent=2, sort_keys=True) + "\n",
    )


def _promotion_manifest_approves(path: Path, policy_id: str) -> bool:
    try:
        armory_path, rel_path = armory_state_location(path)
        payload = json.loads(read_armory_state_text(armory_path, rel_path))
    except (OSError, json.JSONDecodeError):
        return False
    if not is_string_mapping(payload):
        return False
    return bool(payload.get("decision") == "promote" and payload.get("policy_id") == policy_id)


def _payload_string(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    return value if isinstance(value, str) else ""


def _payload_int(payload: Mapping[str, object], key: str, default: int) -> int:
    value = payload.get(key)
    if isinstance(value, bool):
        return default
    return value if isinstance(value, int) else default
