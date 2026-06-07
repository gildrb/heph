"""PufferLib Constellation export for local Heph learning attempts."""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from hephaion.armory.state_files import write_armory_state_text
from hephaion.learning.storage import AttemptRecord, LearningStore

CONSTELLATION_EXPERIMENTS_PATH = Path(".hephaion/learning/constellation/experiments.json")

_PUFFER_HYPER_DEFAULTS: Mapping[str, float] = {
    "train/learning_rate": 0.02,
    "train/ent_coef": 0.001,
    "train/gamma": 0.95,
    "train/gae_lambda": 0.9,
    "train/vtrace_rho_clip": 1.0,
    "train/vtrace_c_clip": 1.0,
    "train/clip_coef": 0.2,
    "train/vf_clip_coef": 0.2,
    "train/vf_coef": 1.0,
    "train/max_grad_norm": 1.0,
    "train/beta1": 0.9,
    "train/beta2": 0.999,
    "train/eps": 1e-8,
    "train/prio_alpha": 0.8,
    "train/prio_beta0": 0.2,
    "train/horizon": 2.0,
    "train/replay_ratio": 1.0,
    "train/minibatch_size": 2.0,
    "policy/hidden_size": 32.0,
    "policy/num_layers": 1.0,
    "vec/total_agents": 1.0,
}

type RecordMetric = Callable[[AttemptRecord, int, float], float]


@dataclass(frozen=True, slots=True)
class ConstellationExport:
    output_path: Path
    groups: Mapping[str, int]

    def to_dict(self) -> dict[str, object]:
        return {
            "output_path": str(self.output_path),
            "groups": dict(self.groups),
        }


def export_armory_constellation(
    armory_path: Path,
    *,
    output_path: Path | None = None,
    env_name: str | None = None,
) -> ConstellationExport:
    """Write PufferLib Constellation data for an armory's local learning attempts."""

    records = tuple(LearningStore(armory_path).iter_attempts())
    name = _clean_env_name(env_name or armory_path.name or "heph")
    if output_path is None:
        return _export_armory_state_constellation(
            armory_path,
            records,
            env_name=name,
        )
    return export_constellation_records(records, output_path=output_path, env_name=name)


def export_constellation_records(
    records: Sequence[AttemptRecord],
    *,
    output_path: Path,
    env_name: str,
) -> ConstellationExport:
    """Write PufferLib Constellation-shaped numeric series data."""

    payload, groups = _constellation_payload(records, env_name=env_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    return ConstellationExport(output_path=output_path, groups=groups)


def _export_armory_state_constellation(
    armory_path: Path,
    records: Sequence[AttemptRecord],
    *,
    env_name: str,
) -> ConstellationExport:
    payload, groups = _constellation_payload(records, env_name=env_name)
    output_path = write_armory_state_text(
        armory_path,
        CONSTELLATION_EXPERIMENTS_PATH,
        json.dumps(payload, sort_keys=True) + "\n",
    )
    return ConstellationExport(output_path=output_path, groups=groups)


def _constellation_payload(
    records: Sequence[AttemptRecord],
    *,
    env_name: str,
) -> tuple[dict[str, dict[str, str]], dict[str, int]]:
    if not records:
        raise ValueError("no learning attempts available to export")
    group_name = _clean_env_name(env_name)
    return {group_name: _constellation_group(records)}, {group_name: len(records)}


def _constellation_group(records: Sequence[AttemptRecord]) -> dict[str, str]:
    cumulative_latency = _cumulative_latency_seconds(records)
    metrics = _base_constellation_metrics(records, cumulative_latency)
    _add_constellation_hyper_metrics(metrics, records)
    _add_constellation_structural_metrics(metrics, records, cumulative_latency)
    return {key: _numeric_series(values) for key, values in metrics.items()}


def _base_constellation_metrics(
    records: Sequence[AttemptRecord],
    cumulative_latency: Sequence[float],
) -> dict[str, list[float]]:
    return {
        "agent_steps": [float(index + 1) for index, _record in enumerate(records)],
        "uptime": list(cumulative_latency),
        "env/score": [record.reward.total for record in records],
        "env/perf": [_reward_perf(record.reward.total) for record in records],
        "tsne1": [_tsne_x(record) for record in records],
        "tsne2": [_tsne_y(record) for record in records],
    }


def _add_constellation_hyper_metrics(
    metrics: dict[str, list[float]],
    records: Sequence[AttemptRecord],
) -> None:
    for key, value in _PUFFER_HYPER_DEFAULTS.items():
        metrics[key] = [value for _record in records]


def _add_constellation_structural_metrics(
    metrics: dict[str, list[float]],
    records: Sequence[AttemptRecord],
    cumulative_latency: Sequence[float],
) -> None:
    for key, metric in _HEPH_STRUCTURAL_METRICS.items():
        metrics[key] = [
            metric(record, index, cumulative_latency[index])
            for index, record in enumerate(records)
        ]


_HEPH_STRUCTURAL_METRICS: Mapping[str, RecordMetric] = {
    "heph/attempt_index": lambda record, _index, _uptime: float(record.attempt_index),
    "heph/action_accept": lambda record, _index, _uptime: _flag(record.accepted),
    "heph/action_abstain": lambda record, _index, _uptime: _flag(record.abstained),
    "heph/evidence_count": lambda record, _index, _uptime: float(
        record.observation.evidence_count
    ),
    "heph/distinct_source_count": lambda record, _index, _uptime: float(
        record.observation.distinct_source_count
    ),
    "heph/top_score": lambda record, _index, _uptime: record.observation.top_score,
    "heph/evidence_confidence": lambda record, _index, _uptime: (
        record.observation.evidence_confidence
    ),
    "heph/citation_count": lambda record, _index, _uptime: float(
        record.observation.citation_count
    ),
    "heph/unverified_citation_count": lambda record, _index, _uptime: float(
        record.observation.unverified_citation_count
    ),
    "heph/unsupported_claim_count": lambda record, _index, _uptime: float(
        record.observation.unsupported_claim_count
    ),
    "heph/grounded_partial_progress": lambda record, _index, _uptime: _flag(
        record.observation.grounded_partial_progress
    ),
    "heph/answer_relevance_score": lambda record, _index, _uptime: (
        record.observation.answer_relevance_score
    ),
    "heph/reply_chars": lambda record, _index, _uptime: float(record.observation.reply_chars),
    "heph/latency_ms": lambda record, _index, _uptime: record.latency_ms,
    "heph/cost_usd": lambda record, _index, _uptime: record.cost_usd,
}


def _cumulative_latency_seconds(records: Sequence[AttemptRecord]) -> list[float]:
    total = 0.0
    values: list[float] = []
    for record in records:
        latency_ms = record.latency_ms or record.observation.latency_ms
        total += max(0.0, latency_ms) / 1000.0
        values.append(total)
    return values


def _tsne_x(record: AttemptRecord) -> float:
    observation = record.observation
    return observation.top_score - (0.25 * observation.missing_required_citation_count)


def _tsne_y(record: AttemptRecord) -> float:
    observation = record.observation
    return observation.evidence_confidence + (0.1 * observation.distinct_source_count)


def _reward_perf(value: float) -> float:
    return max(0.0, min(1.0, (value + 1.0) / 2.0))


def _numeric_series(values: Sequence[float]) -> str:
    return ",".join(_format_number(value) for value in values)


def _format_number(value: float) -> str:
    if not math.isfinite(value):
        return "0"
    return f"{value:.6g}"


def _flag(value: bool) -> float:
    return 1.0 if value else 0.0


def _clean_env_name(value: str) -> str:
    name = value.strip()
    return name or "heph"
