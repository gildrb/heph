"""Replay training and evaluation for local Heph attempt policies."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from hephaion.armory.state_files import ensure_armory_state_dir, write_armory_state_text
from hephaion.learning.actions import FALLBACK_ACTION_ORDER, AttemptAction
from hephaion.learning.observation import AttemptObservation
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
REWARD_TABLE_BACKEND_NAME = "reward-table"
TRAJECTORY_WINDOW_SIZE = 7
_TRAJECTORY_FAILURE_PENALTY = -0.08
_TRAJECTORY_PROGRESS_BONUS = 0.04
_TRAINING_ACTION_ORDER: tuple[AttemptAction, ...] = (AttemptAction.ACCEPT, *FALLBACK_ACTION_ORDER)


@dataclass(frozen=True, slots=True)
class DatasetSplit:
    train: tuple[AttemptRecord, ...]
    heldout: tuple[AttemptRecord, ...]


@dataclass(frozen=True, slots=True)
class PolicyMetrics:
    count: int
    average_reward: float
    grounded_progress_rate: float
    bad_accept_rate: float
    unnecessary_abstain_rate: float
    abstain_rate: float
    no_evidence_abstain_safety: float
    average_attempts: float
    average_latency_ms: float
    average_cost_usd: float

    def to_dict(self) -> dict[str, object]:
        return {
            "count": self.count,
            "average_reward": self.average_reward,
            "grounded_progress_rate": self.grounded_progress_rate,
            "bad_accept_rate": self.bad_accept_rate,
            "unnecessary_abstain_rate": self.unnecessary_abstain_rate,
            "abstain_rate": self.abstain_rate,
            "no_evidence_abstain_safety": self.no_evidence_abstain_safety,
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


def _grounded_progress_rate(metrics: PolicyMetrics) -> float:
    return metrics.grounded_progress_rate


def _bad_accept_rate(metrics: PolicyMetrics) -> float:
    return metrics.bad_accept_rate


def _unnecessary_abstain_rate(metrics: PolicyMetrics) -> float:
    return metrics.unnecessary_abstain_rate


def _no_evidence_abstain_safety(metrics: PolicyMetrics) -> float:
    return metrics.no_evidence_abstain_safety


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
        reason="trained policy regressed grounded progress",
        origin_reason="trained policy regressed grounded progress on {origin}",
        value=_grounded_progress_rate,
        failed=_less_than_baseline,
    ),
    _MetricGate(
        reason="trained policy increased bad accepts",
        origin_reason="trained policy increased bad accepts on {origin}",
        value=_bad_accept_rate,
        failed=_greater_than_baseline,
    ),
    _MetricGate(
        reason="trained policy increased unnecessary abstains",
        origin_reason="trained policy increased unnecessary abstains on {origin}",
        value=_unnecessary_abstain_rate,
        failed=_greater_than_baseline,
    ),
    _MetricGate(
        reason="trained policy regressed no-evidence abstain safety",
        origin_reason="trained policy regressed no-evidence abstain safety on {origin}",
        value=_no_evidence_abstain_safety,
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
    backend: str = REWARD_TABLE_BACKEND_NAME,
    promote: bool = False,
    clear_failed_promotion: bool = True,
) -> TrainingReport:
    if backend != REWARD_TABLE_BACKEND_NAME:
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
        "trajectory_window_size": TRAJECTORY_WINDOW_SIZE,
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
    _write_json(store, manifest_path, manifest)
    if decision == "promote":
        write_exported_policy(store.policies_dir / PROMOTED_POLICY_FILE, artifact)
        _write_json(store, store.policies_dir / PROMOTION_MANIFEST_FILE, manifest)
    elif promote and clear_failed_promotion:
        _clear_promoted_policy(store)
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
    if backend == REWARD_TABLE_BACKEND_NAME:
        return _train_reward_table(records), _reward_table_metadata(records)
    raise ValueError(f"unknown learning backend: {backend}")


def _train_reward_table(records: Sequence[AttemptRecord]) -> dict[str, AttemptAction]:
    totals: dict[str, dict[AttemptAction, float]] = {}
    counts: dict[str, dict[AttemptAction, int]] = {}
    for record in records:
        bucket = observation_bucket(record.observation)
        bucket_totals = totals.setdefault(bucket, {})
        bucket_counts = counts.setdefault(bucket, {})
        for action in _TRAINING_ACTION_ORDER:
            outcome = record.outcome_for(action)
            bucket_totals[action] = bucket_totals.get(action, 0.0) + outcome.reward.total
            bucket_counts[action] = bucket_counts.get(action, 0) + 1

    table: dict[str, AttemptAction] = {}
    for bucket in sorted(totals):
        table[bucket] = _best_reward_action(totals[bucket], counts[bucket])
    return table


def _best_reward_action(
    totals: Mapping[AttemptAction, float],
    counts: Mapping[AttemptAction, int],
) -> AttemptAction:
    best_action = AttemptAction.ACCEPT
    best_reward = float("-inf")
    for action in _TRAINING_ACTION_ORDER:
        count = counts.get(action, 0)
        if count <= 0:
            continue
        reward = totals.get(action, 0.0) / count
        if reward > best_reward:
            best_action = action
            best_reward = reward
    return best_action


def _reward_table_metadata(records: Sequence[AttemptRecord]) -> dict[str, object]:
    return {
        "backend": REWARD_TABLE_BACKEND_NAME,
        "algorithm": "structural_reward_table",
        "bucket_count": len({observation_bucket(record.observation) for record in records}),
        "record_count": len(records),
        "action_order": [action.value for action in _TRAINING_ACTION_ORDER],
        "export": "best_average_reward_bucket_table",
    }


def _clear_promoted_policy(store: LearningStore) -> None:
    policies_dir = ensure_armory_state_dir(
        store.armory_path, store.state_rel_path(store.policies_dir)
    )
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
            grounded_progress_rate=0.0,
            bad_accept_rate=0.0,
            unnecessary_abstain_rate=0.0,
            abstain_rate=0.0,
            no_evidence_abstain_safety=0.0,
            average_attempts=0.0,
            average_latency_ms=0.0,
            average_cost_usd=0.0,
        )
    rewards: list[float] = []
    attempts: list[int] = []
    latencies: list[float] = []
    costs: list[float] = []
    grounded_progress_count = 0
    bad_accept_count = 0
    unnecessary_abstain_count = 0
    abstain_count = 0
    no_evidence_abstain_needed = 0
    no_evidence_abstain_correct = 0
    trajectory_adjustments = _trajectory_reward_adjustments(records, actions)
    for index, (record, action) in enumerate(zip(records, actions, strict=True)):
        outcome = record.outcome_for(action)
        rewards.append(_clamp_reward(outcome.reward.total + trajectory_adjustments[index]))
        attempts.append(outcome.attempts)
        latencies.append(outcome.latency_ms)
        costs.append(outcome.cost_usd)
        if _grounded_progress_action(record, action):
            grounded_progress_count += 1
        if _bad_accept_action(record, action):
            bad_accept_count += 1
        if action is AttemptAction.ABSTAIN:
            abstain_count += 1
            if _unnecessary_abstain_action(record):
                unnecessary_abstain_count += 1
        if _no_evidence_abstain_expected(record):
            no_evidence_abstain_needed += 1
            if action is AttemptAction.ABSTAIN:
                no_evidence_abstain_correct += 1
    return PolicyMetrics(
        count=len(records),
        average_reward=_average(rewards),
        grounded_progress_rate=round(grounded_progress_count / len(records), 4),
        bad_accept_rate=round(bad_accept_count / len(records), 4),
        unnecessary_abstain_rate=round(unnecessary_abstain_count / len(records), 4),
        abstain_rate=round(abstain_count / len(records), 4),
        no_evidence_abstain_safety=(
            round(no_evidence_abstain_correct / no_evidence_abstain_needed, 4)
            if no_evidence_abstain_needed
            else 1.0
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


def _trajectory_reward_adjustments(
    records: Sequence[AttemptRecord],
    actions: Sequence[AttemptAction],
) -> list[float]:
    adjustments = [0.0 for _record in records]
    for indices in _indices_by_session(records).values():
        _apply_trajectory_failure_penalties(adjustments, records, actions, indices)
        _apply_trajectory_progress_bonuses(adjustments, records, actions, indices)
    return [_clamp_adjustment(value) for value in adjustments]


def _indices_by_session(records: Sequence[AttemptRecord]) -> dict[str, list[int]]:
    indices_by_session: dict[str, list[int]] = {}
    for index, record in enumerate(records):
        indices_by_session.setdefault(record.session_id, []).append(index)
    return indices_by_session


def _apply_trajectory_failure_penalties(
    adjustments: list[float],
    records: Sequence[AttemptRecord],
    actions: Sequence[AttemptAction],
    indices: Sequence[int],
) -> None:
    for position, index in enumerate(indices):
        if not _trajectory_failure_turn(records[index], actions[index]):
            continue
        start = max(0, position - TRAJECTORY_WINDOW_SIZE + 1)
        for penalized in indices[start : position + 1]:
            adjustments[penalized] += _TRAJECTORY_FAILURE_PENALTY


def _apply_trajectory_progress_bonuses(
    adjustments: list[float],
    records: Sequence[AttemptRecord],
    actions: Sequence[AttemptAction],
    indices: Sequence[int],
) -> None:
    for offset in range(len(indices) - TRAJECTORY_WINDOW_SIZE + 1):
        window = indices[offset : offset + TRAJECTORY_WINDOW_SIZE]
        if not _progress_window(records, actions, window):
            continue
        for rewarded in window:
            adjustments[rewarded] += _TRAJECTORY_PROGRESS_BONUS


def _progress_window(
    records: Sequence[AttemptRecord],
    actions: Sequence[AttemptAction],
    indices: Sequence[int],
) -> bool:
    return all(_grounded_progress_action(records[index], actions[index]) for index in indices)


def _trajectory_failure_turn(record: AttemptRecord, action: AttemptAction) -> bool:
    return bool(
        _bad_accept_action(record, action)
        or (action is AttemptAction.ABSTAIN and _unnecessary_abstain_action(record))
        or (action is AttemptAction.ACCEPT and record.observation.reply_chars <= 0)
    )


def _grounded_progress_action(record: AttemptRecord, action: AttemptAction) -> bool:
    observation = record.observation
    return bool(
        action is AttemptAction.ACCEPT
        and observation.reply_chars > 0
        and not _bad_accept_action(record, action)
        and (observation.evidence_sufficient or observation.grounded_partial_progress)
    )


def _bad_accept_action(record: AttemptRecord, action: AttemptAction) -> bool:
    return bool(
        action is AttemptAction.ACCEPT
        and (
            _invalid_accept_reply(record.observation)
            or _insufficient_cited_answer(record.observation)
        )
    )


def _invalid_accept_reply(observation: AttemptObservation) -> bool:
    return bool(
        observation.reply_chars <= 0
        or observation.off_topic_answer
        or observation.answer_shape_failed
        or observation.unsupported_claim_count > 0
        or observation.missing_required_citation_count > 0
        or observation.unverified_citation_count > 0
        or not observation.all_citations_verified
    )


def _insufficient_cited_answer(observation: AttemptObservation) -> bool:
    return bool(
        not observation.evidence_sufficient
        and not observation.grounded_partial_progress
        and observation.citation_required
    )


def _unnecessary_abstain_action(record: AttemptRecord) -> bool:
    observation = record.observation
    return bool(observation.evidence_sufficient or observation.grounded_partial_progress)


def _no_evidence_abstain_expected(record: AttemptRecord) -> bool:
    observation = record.observation
    return bool(
        observation.evidence_count == 0
        and (observation.evidence_recommended_action == "abstain" or observation.citation_required)
    )


def _clamp_adjustment(value: float) -> float:
    return max(-0.4, min(0.4, round(value, 4)))


def _clamp_reward(value: float) -> float:
    return max(-1.0, min(1.0, round(value, 4)))


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


def _write_json(store: LearningStore, path: Path, payload: Mapping[str, object]) -> None:
    write_armory_state_text(
        store.armory_path,
        store.state_rel_path(path),
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
    )


def _average(values: Iterable[float]) -> float:
    items = tuple(values)
    return round(sum(items) / len(items), 4) if items else 0.0


def _average_ints(values: Iterable[int]) -> float:
    items = tuple(values)
    return round(sum(items) / len(items), 4) if items else 0.0


def _now() -> str:
    return datetime.now(UTC).isoformat()
