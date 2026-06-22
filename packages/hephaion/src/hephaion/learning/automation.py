"""Local automation for replay training and safe policy promotion."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from hephaion._types import is_string_mapping
from hephaion.armory.state_files import (
    ArmoryStateError,
    append_armory_state_text,
    read_armory_state_text,
    write_armory_state_text,
)
from hephaion.learning.storage import AttemptRecord, LearningStore
from hephaion.learning.training import (
    PUBLIC_SYNTHETIC_REPLAY,
    REWARD_TABLE_BACKEND_NAME,
    TrainingReport,
    train_attempt_policy,
)

AUTOMATION_SCHEMA_VERSION = 1
DEFAULT_MIN_TOTAL_ATTEMPTS = 8
DEFAULT_MIN_NEW_ATTEMPTS = 20


@dataclass(frozen=True, slots=True)
class AutoTrainingConfig:
    min_total_attempts: int = DEFAULT_MIN_TOTAL_ATTEMPTS
    min_new_attempts: int = DEFAULT_MIN_NEW_ATTEMPTS
    include_public_fixture: bool = True
    dataset_paths: tuple[Path, ...] = ()


@dataclass(frozen=True, slots=True)
class AutoTrainingDecision:
    status: str
    reason: str
    attempt_count: int
    new_attempt_count: int
    local_attempt_digest: str
    training_corpus_digest: str
    report: TrainingReport | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": AUTOMATION_SCHEMA_VERSION,
            "status": self.status,
            "reason": self.reason,
            "attempt_count": self.attempt_count,
            "new_attempt_count": self.new_attempt_count,
            "local_attempt_digest": self.local_attempt_digest,
            "training_corpus_digest": self.training_corpus_digest,
        }
        if self.report is not None:
            payload["training_report"] = _portable_training_report(self.report)
        return payload


def maybe_auto_train_attempt_policy(
    armory_path: Path,
    *,
    config: AutoTrainingConfig | None = None,
) -> AutoTrainingDecision:
    """Train and promote when enough new armory-local attempts are available."""

    config = config or AutoTrainingConfig()
    store = LearningStore(armory_path)
    local_records = tuple(store.iter_attempts())
    attempt_count = len(local_records)
    digest = _attempt_digest(local_records)
    corpus_digest = _training_corpus_digest(config)
    state = _load_state(store)
    last_count = _state_int(state, "local_attempt_count")
    last_digest = _state_string(state, "local_attempt_digest")
    last_corpus_digest = _state_string(state, "training_corpus_digest")
    corpus_changed = corpus_digest != last_corpus_digest
    new_attempt_count = (
        attempt_count - last_count if attempt_count >= last_count else attempt_count
    )

    if attempt_count < config.min_total_attempts:
        return _skipped(
            "not enough local attempts",
            attempt_count=attempt_count,
            new_attempt_count=new_attempt_count,
            digest=digest,
            corpus_digest=corpus_digest,
        )
    if digest == last_digest and not corpus_changed:
        return _skipped(
            "local attempts unchanged",
            attempt_count=attempt_count,
            new_attempt_count=0,
            digest=digest,
            corpus_digest=corpus_digest,
        )
    if new_attempt_count < config.min_new_attempts and not corpus_changed:
        return _skipped(
            "not enough new local attempts",
            attempt_count=attempt_count,
            new_attempt_count=new_attempt_count,
            digest=digest,
            corpus_digest=corpus_digest,
        )

    report = train_attempt_policy(
        armory_path=armory_path,
        dataset_paths=_dataset_paths(config),
        include_local=True,
        backend=REWARD_TABLE_BACKEND_NAME,
        promote=True,
        clear_failed_promotion=False,
    )
    decision = AutoTrainingDecision(
        status="trained",
        reason=report.decision,
        attempt_count=attempt_count,
        new_attempt_count=new_attempt_count,
        local_attempt_digest=digest,
        training_corpus_digest=corpus_digest,
        report=report,
    )
    _write_state(store, decision)
    _append_event(store, decision)
    return decision


def _dataset_paths(config: AutoTrainingConfig) -> tuple[Path, ...]:
    if not config.include_public_fixture:
        return config.dataset_paths
    return (PUBLIC_SYNTHETIC_REPLAY, *config.dataset_paths)


def _skipped(
    reason: str,
    *,
    attempt_count: int,
    new_attempt_count: int,
    digest: str,
    corpus_digest: str,
) -> AutoTrainingDecision:
    return AutoTrainingDecision(
        status="skipped",
        reason=reason,
        attempt_count=attempt_count,
        new_attempt_count=new_attempt_count,
        local_attempt_digest=digest,
        training_corpus_digest=corpus_digest,
    )


def _write_state(store: LearningStore, decision: AutoTrainingDecision) -> None:
    report = decision.report
    payload = {
        "schema_version": AUTOMATION_SCHEMA_VERSION,
        "updated_at": _now(),
        "local_attempt_count": decision.attempt_count,
        "local_attempt_digest": decision.local_attempt_digest,
        "training_corpus_digest": decision.training_corpus_digest,
        "last_status": decision.status,
        "last_reason": decision.reason,
        "last_policy_id": report.policy_id if report is not None else "",
        "last_training_decision": report.decision if report is not None else "",
    }
    _write_json(store, store.automation_state_path, payload)


def _append_event(store: LearningStore, decision: AutoTrainingDecision) -> None:
    store.ensure_layout()
    payload = {"created_at": _now(), **decision.to_dict()}
    append_armory_state_text(
        store.armory_path,
        store.state_rel_path(store.automation_events_path),
        json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n",
    )


def _portable_training_report(report: TrainingReport) -> dict[str, object]:
    payload = report.to_dict()
    payload.pop("artifact_path", None)
    payload.pop("manifest_path", None)
    return payload


def _load_state(store: LearningStore) -> Mapping[str, object]:
    try:
        payload = json.loads(
            read_armory_state_text(
                store.armory_path,
                store.state_rel_path(store.automation_state_path),
            )
        )
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}
    except ArmoryStateError:
        raise
    return payload if is_string_mapping(payload) else {}


def _attempt_digest(records: Sequence[AttemptRecord]) -> str:
    digest = hashlib.sha256()
    for record in records:
        digest.update(record.created_at.encode("utf-8"))
        digest.update((record.episode_id or record.turn_id).encode("utf-8"))
        digest.update(record.action.value.encode("utf-8"))
        digest.update(str(round(record.reward.total, 4)).encode("utf-8"))
    return digest.hexdigest()


def _training_corpus_digest(config: AutoTrainingConfig) -> str:
    digest = hashlib.sha256()
    digest.update(str(config.include_public_fixture).encode("utf-8"))
    for path in _dataset_paths(config):
        digest.update(str(path.expanduser()).encode("utf-8"))
        try:
            stat = path.expanduser().stat()
        except OSError:
            digest.update(b"missing")
        else:
            digest.update(str(stat.st_size).encode("utf-8"))
            digest.update(str(stat.st_mtime_ns).encode("utf-8"))
    return digest.hexdigest()


def _write_json(store: LearningStore, path: Path, payload: Mapping[str, object]) -> None:
    write_armory_state_text(
        store.armory_path,
        store.state_rel_path(path),
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
    )


def _state_string(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    return value if isinstance(value, str) else ""


def _state_int(payload: Mapping[str, object], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool):
        return 0
    return value if isinstance(value, int) else 0


def _now() -> str:
    return datetime.now(UTC).isoformat()
