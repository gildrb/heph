"""Replay training and evaluation for local Heph attempt policies."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from hephaion.learning.actions import AttemptAction
from hephaion.learning.policy import StaticAttemptPolicy
from hephaion.learning.policy_artifact import (
    PROMOTED_POLICY_FILE,
    PROMOTION_MANIFEST_FILE,
    ExportedAttemptPolicy,
    ExportedPolicyArtifact,
    observation_bucket,
    write_exported_policy,
)
from hephaion.learning.storage import AttemptRecord, LearningStore

PUBLIC_SYNTHETIC_REPLAY = Path(__file__).parent / "fixtures" / "public_synthetic_replay.jsonl"
TRAINING_REPORT_SCHEMA_VERSION = 1
PUFFERLIB_BACKEND_NAME = "pufferlib"


@dataclass(frozen=True, slots=True)
class DatasetSplit:
    train: tuple[AttemptRecord, ...]
    heldout: tuple[AttemptRecord, ...]


@dataclass(frozen=True, slots=True)
class PolicyMetrics:
    count: int
    average_reward: float
    abstention_correctness: float
    average_attempts: float
    average_latency_ms: float
    average_cost_usd: float

    def to_dict(self) -> dict[str, object]:
        return {
            "count": self.count,
            "average_reward": self.average_reward,
            "abstention_correctness": self.abstention_correctness,
            "average_attempts": self.average_attempts,
            "average_latency_ms": self.average_latency_ms,
            "average_cost_usd": self.average_cost_usd,
        }


type MetricValue = Callable[[PolicyMetrics], float]
type MetricRegression = Callable[[float, float], bool]


@dataclass(frozen=True, slots=True)
class _MetricGate:
    reason: str
    origin_reason: str
    value: MetricValue
    failed: MetricRegression


def _average_reward(metrics: PolicyMetrics) -> float:
    return metrics.average_reward


def _abstention_correctness(metrics: PolicyMetrics) -> float:
    return metrics.abstention_correctness


def _average_attempts(metrics: PolicyMetrics) -> float:
    return metrics.average_attempts


def _average_latency_ms(metrics: PolicyMetrics) -> float:
    return metrics.average_latency_ms


def _average_cost_usd(metrics: PolicyMetrics) -> float:
    return metrics.average_cost_usd


def _not_greater_than_baseline(trained: float, baseline: float) -> bool:
    return trained <= baseline


def _less_than_baseline(trained: float, baseline: float) -> bool:
    return trained < baseline


def _greater_than_baseline(trained: float, baseline: float) -> bool:
    return trained > baseline


_PROMOTION_METRIC_GATES: tuple[_MetricGate, ...] = (
    _MetricGate(
        reason="trained policy did not beat static fallback reward",
        origin_reason="trained policy did not beat fallback reward on {origin}",
        value=_average_reward,
        failed=_not_greater_than_baseline,
    ),
    _MetricGate(
        reason="trained policy regressed abstention correctness",
        origin_reason="trained policy regressed abstention correctness on {origin}",
        value=_abstention_correctness,
        failed=_less_than_baseline,
    ),
    _MetricGate(
        reason="trained policy regressed average attempts",
        origin_reason="",
        value=_average_attempts,
        failed=_greater_than_baseline,
    ),
    _MetricGate(
        reason="trained policy regressed latency",
        origin_reason="",
        value=_average_latency_ms,
        failed=_greater_than_baseline,
    ),
    _MetricGate(
        reason="trained policy regressed cost",
        origin_reason="",
        value=_average_cost_usd,
        failed=_greater_than_baseline,
    ),
)


@dataclass(frozen=True, slots=True)
class TrainingReport:
    policy_id: str
    decision: str
    reasons: tuple[str, ...]
    dataset_counts: Mapping[str, int]
    split_counts: Mapping[str, int]
    baseline_metrics: PolicyMetrics
    trained_metrics: PolicyMetrics
    origin_baseline_metrics: Mapping[str, PolicyMetrics]
    origin_trained_metrics: Mapping[str, PolicyMetrics]
    artifact_path: Path
    manifest_path: Path
    backend: str

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": TRAINING_REPORT_SCHEMA_VERSION,
            "policy_id": self.policy_id,
            "decision": self.decision,
            "reasons": list(self.reasons),
            "dataset_counts": dict(self.dataset_counts),
            "split_counts": dict(self.split_counts),
            "baseline_metrics": self.baseline_metrics.to_dict(),
            "trained_policy_metrics": self.trained_metrics.to_dict(),
            "origin_baseline_metrics": {
                origin: metrics.to_dict()
                for origin, metrics in self.origin_baseline_metrics.items()
            },
            "origin_trained_policy_metrics": {
                origin: metrics.to_dict()
                for origin, metrics in self.origin_trained_metrics.items()
            },
            "artifact_path": str(self.artifact_path),
            "manifest_path": str(self.manifest_path),
            "backend": self.backend,
        }


class TrainedTablePolicy:
    def __init__(self, table: Mapping[str, AttemptAction]) -> None:
        self.table = table
        self.fallback = StaticAttemptPolicy()

    def choose(self, record: AttemptRecord) -> AttemptAction:
        return self.table.get(observation_bucket(record.observation)) or self.fallback.choose(
            record.observation
        )


def train_attempt_policy(
    *,
    armory_path: Path,
    dataset_paths: Sequence[Path] | None = None,
    include_local: bool = True,
    backend: str = PUFFERLIB_BACKEND_NAME,
    promote: bool = False,
    clear_failed_promotion: bool = True,
) -> TrainingReport:
    if backend != PUFFERLIB_BACKEND_NAME:
        raise ValueError(f"unknown learning backend: {backend}")
    store = LearningStore(armory_path)
    records = load_training_records(
        armory_path=armory_path,
        dataset_paths=dataset_paths,
        include_local=include_local,
    )
    split = split_records(records)
    policy_id = _policy_id(records)
    table, backend_metadata = _train_policy_table(split.train, backend)
    trained_policy = TrainedTablePolicy(table)
    fallback = StaticAttemptPolicy()
    baseline_metrics = evaluate_policy(split.heldout, fallback)
    trained_metrics = evaluate_record_policy(split.heldout, trained_policy)
    origin_baseline = _origin_metrics(split.heldout, fallback)
    origin_trained = _origin_metrics(split.heldout, trained_policy)
    reasons = _promotion_reasons(
        split,
        baseline_metrics,
        trained_metrics,
        origin_baseline,
        origin_trained,
    )
    decision = "promote" if promote and not reasons else "keep_fallback"
    artifact_path = store.policies_dir / f"{policy_id}.json"
    manifest_path = store.policies_dir / f"{policy_id}.manifest.json"
    manifest = {
        "schema_version": TRAINING_REPORT_SCHEMA_VERSION,
        "policy_id": policy_id,
        "decision": decision,
        "reasons": list(reasons),
        "dataset_counts": _dataset_counts(records),
        "split_counts": {"train": len(split.train), "heldout": len(split.heldout)},
        "baseline_metrics": baseline_metrics.to_dict(),
        "trained_policy_metrics": trained_metrics.to_dict(),
        "backend": backend,
        "backend_metadata": backend_metadata,
    }
    artifact = ExportedPolicyArtifact(
        policy_id=policy_id,
        created_at=_now(),
        table=table,
        manifest=manifest,
    )
    write_exported_policy(artifact_path, artifact)
    _write_json(manifest_path, manifest)
    if decision == "promote":
        write_exported_policy(store.policies_dir / PROMOTED_POLICY_FILE, artifact)
        _write_json(store.policies_dir / PROMOTION_MANIFEST_FILE, manifest)
    elif promote and clear_failed_promotion:
        _clear_promoted_policy(store.policies_dir)
    return TrainingReport(
        policy_id=policy_id,
        decision=decision,
        reasons=reasons,
        dataset_counts=_dataset_counts(records),
        split_counts={"train": len(split.train), "heldout": len(split.heldout)},
        baseline_metrics=baseline_metrics,
        trained_metrics=trained_metrics,
        origin_baseline_metrics=origin_baseline,
        origin_trained_metrics=origin_trained,
        artifact_path=artifact_path,
        manifest_path=manifest_path,
        backend=backend,
    )


def load_training_records(
    *,
    armory_path: Path,
    dataset_paths: Sequence[Path] | None,
    include_local: bool,
) -> tuple[AttemptRecord, ...]:
    records: list[AttemptRecord] = []
    paths = (PUBLIC_SYNTHETIC_REPLAY,) if dataset_paths is None else tuple(dataset_paths)
    for path in paths:
        records.extend(load_records_from_jsonl(path))
    if include_local:
        records.extend(LearningStore(armory_path).iter_attempts())
    return tuple(records)


def load_records_from_jsonl(path: Path) -> tuple[AttemptRecord, ...]:
    records: list[AttemptRecord] = []
    if not path.is_file():
        raise FileNotFoundError(f"learning replay dataset not found: {path}")
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = _record_from_line(line)
            if record is not None:
                records.append(record)
    return tuple(records)


def _train_policy_table(
    records: Sequence[AttemptRecord],
    backend: str,
) -> tuple[dict[str, AttemptAction], Mapping[str, object]]:
    if backend == PUFFERLIB_BACKEND_NAME:
        with tempfile.TemporaryDirectory(prefix="heph-pufferlib-import-") as import_dir:
            original_cwd = Path.cwd()
            try:
                os.chdir(import_dir)
                from hephaion.learning.puffer_backend import train_pufferlib_policy_table
            finally:
                os.chdir(original_cwd)

        result = train_pufferlib_policy_table(records, bucket=observation_bucket)
        return dict(result.table), result.metadata
    raise ValueError(f"unknown learning backend: {backend}")


def _clear_promoted_policy(policies_dir: Path) -> None:
    for filename in (PROMOTED_POLICY_FILE, PROMOTION_MANIFEST_FILE):
        (policies_dir / filename).unlink(missing_ok=True)


def split_records(records: Sequence[AttemptRecord], heldout_percent: int = 30) -> DatasetSplit:
    train: list[AttemptRecord] = []
    heldout: list[AttemptRecord] = []
    for record in records:
        bucket = _stable_bucket(record.episode_id or record.turn_id)
        if bucket < heldout_percent:
            heldout.append(record)
        else:
            train.append(record)
    if records and not heldout:
        heldout.append(records[-1])
        train = list(records[:-1])
    if len(records) > 1 and not train:
        train.append(heldout.pop(0))
    return DatasetSplit(train=tuple(train), heldout=tuple(heldout))


def evaluate_policy(
    records: Sequence[AttemptRecord], policy: StaticAttemptPolicy
) -> PolicyMetrics:
    return _evaluate_actions(
        records,
        tuple(policy.choose(record.observation) for record in records),
    )


def evaluate_record_policy(
    records: Sequence[AttemptRecord],
    policy: TrainedTablePolicy | ExportedAttemptPolicy,
) -> PolicyMetrics:
    actions: list[AttemptAction] = []
    for record in records:
        if isinstance(policy, TrainedTablePolicy):
            actions.append(policy.choose(record))
        else:
            actions.append(policy.choose(record.observation))
    return _evaluate_actions(records, tuple(actions))


def _evaluate_actions(
    records: Sequence[AttemptRecord],
    actions: Sequence[AttemptAction],
) -> PolicyMetrics:
    if not records:
        return PolicyMetrics(
            count=0,
            average_reward=0.0,
            abstention_correctness=0.0,
            average_attempts=0.0,
            average_latency_ms=0.0,
            average_cost_usd=0.0,
        )
    rewards: list[float] = []
    attempts: list[int] = []
    latencies: list[float] = []
    costs: list[float] = []
    abstain_needed = 0
    abstain_correct = 0
    for record, action in zip(records, actions, strict=True):
        outcome = record.outcome_for(action)
        rewards.append(outcome.reward.total)
        attempts.append(outcome.attempts)
        latencies.append(outcome.latency_ms)
        costs.append(outcome.cost_usd)
        if _abstention_expected(record):
            abstain_needed += 1
            if action is AttemptAction.ABSTAIN:
                abstain_correct += 1
    return PolicyMetrics(
        count=len(records),
        average_reward=_average(rewards),
        abstention_correctness=(
            round(abstain_correct / abstain_needed, 4) if abstain_needed else 1.0
        ),
        average_attempts=_average_ints(attempts),
        average_latency_ms=_average(latencies),
        average_cost_usd=_average(costs),
    )


def _origin_metrics(
    records: Sequence[AttemptRecord],
    policy: StaticAttemptPolicy | TrainedTablePolicy,
) -> dict[str, PolicyMetrics]:
    by_origin: dict[str, list[AttemptRecord]] = {}
    for record in records:
        by_origin.setdefault(_record_origin(record), []).append(record)
    metrics: dict[str, PolicyMetrics] = {}
    for origin, origin_records in by_origin.items():
        if isinstance(policy, StaticAttemptPolicy):
            metrics[origin] = evaluate_policy(origin_records, policy)
        else:
            metrics[origin] = evaluate_record_policy(origin_records, policy)
    return metrics


def _promotion_reasons(
    split: DatasetSplit,
    baseline: PolicyMetrics,
    trained: PolicyMetrics,
    origin_baseline: Mapping[str, PolicyMetrics],
    origin_trained: Mapping[str, PolicyMetrics],
) -> tuple[str, ...]:
    return (
        *_split_promotion_reasons(split),
        *_metric_promotion_reasons(baseline, trained),
        *_origin_promotion_reasons(origin_baseline, origin_trained),
    )


def _split_promotion_reasons(split: DatasetSplit) -> tuple[str, ...]:
    reasons: list[str] = []
    if not split.train:
        reasons.append("no training records")
    if not split.heldout:
        reasons.append("no held-out records")
    return tuple(reasons)


def _metric_promotion_reasons(
    baseline: PolicyMetrics,
    trained: PolicyMetrics,
) -> tuple[str, ...]:
    return tuple(
        gate.reason
        for gate in _PROMOTION_METRIC_GATES
        if _promotion_gate_failed(gate, baseline, trained)
    )


def _origin_promotion_reasons(
    origin_baseline: Mapping[str, PolicyMetrics],
    origin_trained: Mapping[str, PolicyMetrics],
) -> tuple[str, ...]:
    reasons: list[str] = []
    for origin, baseline_metrics in origin_baseline.items():
        trained_metrics = origin_trained.get(origin)
        if trained_metrics is None:
            reasons.append(f"missing trained metrics for {origin}")
            continue
        reasons.extend(_origin_metric_reasons(origin, baseline_metrics, trained_metrics))
    return tuple(reasons)


def _origin_metric_reasons(
    origin: str,
    baseline: PolicyMetrics,
    trained: PolicyMetrics,
) -> tuple[str, ...]:
    return tuple(
        gate.origin_reason.format(origin=origin)
        for gate in _PROMOTION_METRIC_GATES
        if gate.origin_reason and _promotion_gate_failed(gate, baseline, trained)
    )


def _promotion_gate_failed(
    gate: _MetricGate,
    baseline: PolicyMetrics,
    trained: PolicyMetrics,
) -> bool:
    return gate.failed(gate.value(trained), gate.value(baseline))


def _dataset_counts(records: Sequence[AttemptRecord]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        origin = _record_origin(record)
        counts[origin] = counts.get(origin, 0) + 1
    return counts


def _record_origin(record: AttemptRecord) -> str:
    metadata = record.replay_metadata or {}
    for key in ("data_origin", "dataset_kind", "label_source"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "local"


def _abstention_expected(record: AttemptRecord) -> bool:
    observation = record.observation
    return bool(
        observation.evidence_recommended_action == "abstain"
        or (observation.citation_required and observation.evidence_count == 0)
    )


def _record_from_line(line: str) -> AttemptRecord | None:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return None
    return AttemptRecord.from_dict(payload)


def _policy_id(records: Sequence[AttemptRecord]) -> str:
    digest = hashlib.sha256()
    for record in records:
        digest.update((record.episode_id or record.turn_id).encode("utf-8"))
        digest.update(record.action.value.encode("utf-8"))
    return f"heph-policy-{digest.hexdigest()[:12]}"


def _stable_bucket(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 100


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _average(values: Iterable[float]) -> float:
    items = tuple(values)
    return round(sum(items) / len(items), 4) if items else 0.0


def _average_ints(values: Iterable[int]) -> float:
    items = tuple(values)
    return round(sum(items) / len(items), 4) if items else 0.0


def _now() -> str:
    return datetime.now(UTC).isoformat()
