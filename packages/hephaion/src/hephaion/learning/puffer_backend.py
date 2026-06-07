"""PufferLib-backed replay training for Heph harness attempt policies."""

from __future__ import annotations

import contextlib
import io
import signal
import tempfile
import threading
import warnings
from collections.abc import Callable, Collection, Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import ClassVar

from hephaion.learning.actions import AttemptAction
from hephaion.learning.observation import AttemptObservation
from hephaion.learning.storage import AttemptRecord


@contextlib.contextmanager
def _pufferlib_import_context() -> Iterator[None]:
    warning_filters = list(warnings.filters)
    sigint_handler = signal.getsignal(signal.SIGINT)
    original_signal = signal.signal
    main_thread = threading.current_thread() is threading.main_thread()

    def _thread_signal(
        signalnum: int,
        _handler: object,
    ) -> object:
        return signal.getsignal(signalnum)

    try:
        if not main_thread:
            signal.signal = _thread_signal  # ty:ignore[invalid-assignment]
        with (
            tempfile.TemporaryDirectory(prefix="heph-pufferlib-import-") as import_dir,
            contextlib.chdir(import_dir),
        ):
            yield
    finally:
        signal.signal = original_signal
        warnings.filters = warning_filters
        if sigint_handler is not None and main_thread:
            signal.signal(signal.SIGINT, sigint_handler)


with _pufferlib_import_context():
    import numpy as np
    import pufferlib.models
    import pufferlib.vector
    import torch
    from gymnasium import spaces
    from numpy.typing import NDArray
    from pufferlib.emulation import GymnasiumPufferEnv
    from pufferlib.pufferl import NoLogger, PuffeRL

PUFFERLIB_BACKEND_NAME = "pufferlib"

_PUFFER_ACTIONS: tuple[AttemptAction, ...] = tuple(AttemptAction)
_DEFAULT_SEED = 13
_MAX_SEGMENTS = 8


type FeatureValue = Callable[[AttemptObservation], float]


@dataclass(frozen=True, slots=True)
class PufferTrainingResult:
    table: Mapping[str, AttemptAction]
    metadata: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class _ObservationFeature:
    name: str
    value: FeatureValue


def _evidence_segment_score_feature(index: int) -> _ObservationFeature:
    return _ObservationFeature(
        f"evidence_segment_{index + 1}_score",
        lambda observation, segment_index=index: _segment_score(observation, segment_index),
    )


def _evidence_segment_mask_feature(index: int) -> _ObservationFeature:
    return _ObservationFeature(
        f"evidence_segment_{index + 1}_mask",
        lambda observation, segment_index=index: _segment_mask(observation, segment_index),
    )


def _source_segment_mask_feature(index: int) -> _ObservationFeature:
    return _ObservationFeature(
        f"source_segment_{index + 1}_mask",
        lambda observation, segment_index=index: _source_segment_mask(
            observation,
            segment_index,
        ),
    )


_OBSERVATION_FEATURES: tuple[_ObservationFeature, ...] = (
    _ObservationFeature(
        "attempt_index", lambda observation: _bounded(observation.attempt_index / 5.0)
    ),
    _ObservationFeature(
        "citation_required", lambda observation: _flag(observation.citation_required)
    ),
    _ObservationFeature(
        "evidence_count", lambda observation: _bounded(observation.evidence_count / 8.0)
    ),
    _ObservationFeature(
        "distinct_source_count",
        lambda observation: _bounded(observation.distinct_source_count / 5.0),
    ),
    _ObservationFeature(
        "sampled_source_count",
        lambda observation: _bounded(observation.sampled_source_count / 10.0),
    ),
    _ObservationFeature(
        "total_source_count",
        lambda observation: _bounded(observation.total_source_count / 20.0),
    ),
    _ObservationFeature("top_score", lambda observation: _bounded(observation.top_score)),
    _ObservationFeature(
        "evidence_sufficient", lambda observation: _flag(observation.evidence_sufficient)
    ),
    _ObservationFeature(
        "evidence_confidence",
        lambda observation: _bounded(observation.evidence_confidence),
    ),
    _ObservationFeature(
        "evidence_recommended_abstain",
        lambda observation: _flag(observation.evidence_recommended_action == "abstain"),
    ),
    _ObservationFeature("has_citations", lambda observation: _flag(observation.has_citations)),
    _ObservationFeature(
        "citation_count", lambda observation: _bounded(observation.citation_count / 8.0)
    ),
    _ObservationFeature(
        "all_citations_verified",
        lambda observation: _flag(observation.all_citations_verified),
    ),
    _ObservationFeature(
        "unverified_citation_count",
        lambda observation: _bounded(observation.unverified_citation_count / 4.0),
    ),
    _ObservationFeature(
        "unsupported_claim_count",
        lambda observation: _bounded(observation.unsupported_claim_count / 4.0),
    ),
    _ObservationFeature(
        "answer_relevance_score",
        lambda observation: _bounded(observation.answer_relevance_score),
    ),
    _ObservationFeature(
        "off_topic_answer", lambda observation: _flag(observation.off_topic_answer)
    ),
    _ObservationFeature(
        "answer_shape_failed", lambda observation: _flag(observation.answer_shape_failed)
    ),
    _ObservationFeature(
        "grounded_partial_progress",
        lambda observation: _flag(observation.grounded_partial_progress),
    ),
    _ObservationFeature(
        "missing_required_citation_count",
        lambda observation: _bounded(observation.missing_required_citation_count / 4.0),
    ),
    _ObservationFeature(
        "confident_thin_evidence",
        lambda observation: _flag(observation.confident_thin_evidence),
    ),
    _ObservationFeature(
        "reply_chars", lambda observation: _bounded(observation.reply_chars / 1600.0)
    ),
    _ObservationFeature(
        "retrieval_strategy_overview",
        lambda observation: _flag(observation.retrieval_strategy == "overview"),
    ),
    *tuple(_evidence_segment_score_feature(index) for index in range(_MAX_SEGMENTS)),
    *tuple(_evidence_segment_mask_feature(index) for index in range(_MAX_SEGMENTS)),
    *tuple(_source_segment_mask_feature(index) for index in range(_MAX_SEGMENTS)),
)
_FEATURE_COUNT = len(_OBSERVATION_FEATURES)


def train_pufferlib_policy_table(
    records: Sequence[AttemptRecord],
    *,
    bucket: Callable[[AttemptObservation], str],
    seed: int = _DEFAULT_SEED,
) -> PufferTrainingResult:
    """Train a tiny PufferLib policy over replay rewards and export bucket actions."""

    if not records:
        return PufferTrainingResult(table={}, metadata=_metadata(seed, 0, 0, 0))

    num_envs = min(4, max(1, len(records)))
    bptt_horizon = 2
    batch_size = num_envs * bptt_horizon
    total_timesteps = max(batch_size * 8, len(records) * 32)
    table = _train_and_infer_table(
        records,
        bucket=bucket,
        seed=seed,
        num_envs=num_envs,
        batch_size=batch_size,
        bptt_horizon=bptt_horizon,
        total_timesteps=total_timesteps,
    )
    return PufferTrainingResult(
        table=table,
        metadata=_metadata(seed, num_envs, batch_size, total_timesteps),
    )


class _HephReplayGymEnv:
    metadata: ClassVar[dict[str, object]] = {"render_modes": ()}

    def __init__(self, records: Sequence[AttemptRecord], *, seed: int = _DEFAULT_SEED) -> None:
        self._records = tuple(records)
        self._index = seed % max(1, len(self._records))
        self._rng = np.random.default_rng(seed)
        self._active_segment_count = 0
        self.observation_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(_FEATURE_COUNT,),
            dtype=np.float32,
        )
        self.action_space = spaces.Discrete(len(_PUFFER_ACTIONS))
        self.render_mode = None
        self._randomize_active_segments()

    def reset(
        self,
        *,
        seed: int | None = None,
        options: Mapping[str, object] | None = None,
    ) -> tuple[NDArray[np.float32], dict[str, object]]:
        if seed is not None:
            self._index = seed % max(1, len(self._records))
            self._rng = np.random.default_rng(seed)
        self._randomize_active_segments()
        return self._current_features(), {}

    def step(
        self,
        action: int,
    ) -> tuple[NDArray[np.float32], float, bool, bool, dict[str, object]]:
        if not self._records:
            return np.zeros(_FEATURE_COUNT, dtype=np.float32), 0.0, True, False, {}
        record = self._records[self._index]
        chosen = _PUFFER_ACTIONS[max(0, min(int(action), len(_PUFFER_ACTIONS) - 1))]
        outcome = record.outcome_for(chosen)
        self._index = (self._index + 1) % len(self._records)
        self._randomize_active_segments()
        return (
            self._current_features(),
            outcome.reward.total,
            False,
            False,
            {
                "action": chosen.value,
                "final_outcome": outcome.final_outcome,
                "attempts": outcome.attempts,
            },
        )

    def _current_features(self) -> NDArray[np.float32]:
        if not self._records:
            return np.zeros(_FEATURE_COUNT, dtype=np.float32)
        observation = randomized_segment_observation(
            self._records[self._index].observation,
            active_segment_count=self._active_segment_count,
        )
        return observation_features(observation)

    def _randomize_active_segments(self) -> None:
        if not self._records:
            self._active_segment_count = 0
            return
        max_segments = min(
            _MAX_SEGMENTS, max(0, self._records[self._index].observation.evidence_count)
        )
        if max_segments <= 0:
            self._active_segment_count = 0
            return
        self._active_segment_count = int(self._rng.integers(0, max_segments + 1))


def observation_features(observation: AttemptObservation) -> NDArray[np.float32]:
    """Return numeric structural features for the replay policy."""

    return _observation_features(observation, active_feature_names=None)


def masked_observation_features(
    observation: AttemptObservation,
    active_feature_names: Collection[str],
) -> NDArray[np.float32]:
    """Return replay features with inactive observation slots zeroed."""

    return _observation_features(
        observation,
        active_feature_names=frozenset(active_feature_names),
    )


def observation_feature_names() -> tuple[str, ...]:
    """Return the ordered replay observation feature names."""

    return tuple(feature.name for feature in _OBSERVATION_FEATURES)


def randomized_segment_observation(
    observation: AttemptObservation,
    *,
    active_segment_count: int,
) -> AttemptObservation:
    """Return an observation view with missing evidence/source segment slots zeroed."""

    visible_segments = max(0, min(_MAX_SEGMENTS, active_segment_count, observation.evidence_count))
    if visible_segments == observation.evidence_count:
        return observation
    visible_sources = min(observation.distinct_source_count, visible_segments)
    evidence_is_visible = visible_segments > 0
    return replace(
        observation,
        evidence_count=visible_segments,
        distinct_source_count=visible_sources,
        sampled_source_count=min(observation.sampled_source_count, visible_sources),
        total_source_count=min(observation.total_source_count, visible_sources),
        top_score=observation.top_score if evidence_is_visible else 0.0,
        evidence_sufficient=(
            observation.evidence_sufficient
            and visible_segments >= min(observation.evidence_count, _MAX_SEGMENTS)
        ),
        evidence_confidence=observation.evidence_confidence if evidence_is_visible else 0.0,
    )


def _observation_features(
    observation: AttemptObservation,
    *,
    active_feature_names: frozenset[str] | None,
) -> NDArray[np.float32]:
    return np.asarray(
        [
            feature.value(observation)
            if active_feature_names is None or feature.name in active_feature_names
            else 0.0
            for feature in _OBSERVATION_FEATURES
        ],
        dtype=np.float32,
    )


def _segment_score(observation: AttemptObservation, index: int) -> float:
    if index >= observation.evidence_count:
        return 0.0
    return _bounded(observation.top_score)


def _segment_mask(observation: AttemptObservation, index: int) -> float:
    if index >= observation.evidence_count:
        return 0.0
    return 1.0


def _source_segment_mask(observation: AttemptObservation, index: int) -> float:
    if index >= observation.distinct_source_count:
        return 0.0
    return 1.0


def _train_and_infer_table(
    records: Sequence[AttemptRecord],
    *,
    bucket: Callable[[AttemptObservation], str],
    seed: int,
    num_envs: int,
    batch_size: int,
    bptt_horizon: int,
    total_timesteps: int,
) -> dict[str, AttemptAction]:
    torch.manual_seed(seed)
    np.random.seed(seed)
    vecenv = pufferlib.vector.make(
        lambda buf=None, seed=seed: _puffer_env(records, buf=buf, seed=seed),
        backend=pufferlib.vector.Serial,
        num_envs=num_envs,
        seed=seed,
        batch_size=num_envs,
    )
    config = _puffer_config(
        seed=seed,
        batch_size=batch_size,
        bptt_horizon=bptt_horizon,
        total_timesteps=total_timesteps,
    )
    trainer: PuffeRL | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="heph-pufferlib-") as run_dir:
            config["data_dir"] = run_dir
            with contextlib.redirect_stdout(io.StringIO()):
                policy = pufferlib.models.Default(vecenv, hidden_size=32)
                trainer = PuffeRL(config, vecenv, policy, logger=NoLogger(config))
                for _ in range(trainer.total_epochs):
                    trainer.evaluate()
                    trainer.train()
                _stop_pufferlib(trainer)
            return _infer_bucket_table(records, policy, bucket=bucket)
    finally:
        if trainer is not None:
            _stop_pufferlib(trainer)


def _puffer_env(
    records: Sequence[AttemptRecord],
    *,
    buf: object | None,
    seed: int,
) -> GymnasiumPufferEnv:
    return GymnasiumPufferEnv(
        env_creator=lambda: _HephReplayGymEnv(records, seed=seed),
        buf=buf,
        seed=seed,
    )


def _infer_bucket_table(
    records: Sequence[AttemptRecord],
    policy: pufferlib.models.Default,
    *,
    bucket: Callable[[AttemptObservation], str],
) -> dict[str, AttemptAction]:
    observations_by_bucket: dict[str, AttemptObservation] = {}
    for record in records:
        key = bucket(record.observation)
        observations_by_bucket.setdefault(key, record.observation)

    keys = tuple(sorted(observations_by_bucket))
    if not keys:
        return {}
    features = np.stack(
        [observation_features(observations_by_bucket[key]) for key in keys],
        axis=0,
    )
    with torch.no_grad():
        logits, _values = policy.forward_eval(torch.as_tensor(features, dtype=torch.float32))
        choices = logits.argmax(dim=1).cpu().numpy().tolist()
    model_table = {
        key: _PUFFER_ACTIONS[max(0, min(int(choice), len(_PUFFER_ACTIONS) - 1))]
        for key, choice in zip(keys, choices, strict=True)
    }
    return _reward_checked_bucket_table(records, model_table, bucket=bucket)


def _reward_checked_bucket_table(
    records: Sequence[AttemptRecord],
    model_table: Mapping[str, AttemptAction],
    *,
    bucket: Callable[[AttemptObservation], str],
) -> dict[str, AttemptAction]:
    totals: dict[str, dict[AttemptAction, float]] = {}
    counts: dict[str, dict[AttemptAction, int]] = {}
    for record in records:
        key = bucket(record.observation)
        bucket_totals = totals.setdefault(key, {})
        bucket_counts = counts.setdefault(key, {})
        for action in _PUFFER_ACTIONS:
            bucket_totals[action] = (
                bucket_totals.get(action, 0.0) + record.outcome_for(action).reward.total
            )
            bucket_counts[action] = bucket_counts.get(action, 0) + 1

    table: dict[str, AttemptAction] = {}
    for key, model_action in model_table.items():
        table[key] = _reward_checked_action(
            model_action,
            totals.get(key, {}),
            counts.get(key, {}),
        )
    return table


def _reward_checked_action(
    model_action: AttemptAction,
    totals: Mapping[AttemptAction, float],
    counts: Mapping[AttemptAction, int],
) -> AttemptAction:
    best_action = model_action
    best_reward = _average_action_reward(model_action, totals, counts)
    for action in _PUFFER_ACTIONS:
        reward = _average_action_reward(action, totals, counts)
        if reward > best_reward:
            best_action = action
            best_reward = reward
    return best_action


def _average_action_reward(
    action: AttemptAction,
    totals: Mapping[AttemptAction, float],
    counts: Mapping[AttemptAction, int],
) -> float:
    count = counts.get(action, 0)
    if count <= 0:
        return float("-inf")
    return totals.get(action, 0.0) / count


def _puffer_config(
    *,
    seed: int,
    batch_size: int,
    bptt_horizon: int,
    total_timesteps: int,
) -> dict[str, object]:
    return {
        "env": "heph_replay",
        "seed": seed,
        "torch_deterministic": True,
        "cpu_offload": False,
        "device": "cpu",
        "optimizer": "adam",
        "anneal_lr": False,
        "precision": "float32",
        "total_timesteps": total_timesteps,
        "learning_rate": 0.02,
        "gamma": 0.95,
        "gae_lambda": 0.9,
        "update_epochs": 2,
        "clip_coef": 0.2,
        "vf_coef": 1.0,
        "vf_clip_coef": 0.2,
        "max_grad_norm": 1.0,
        "ent_coef": 0.001,
        "adam_beta1": 0.9,
        "adam_beta2": 0.999,
        "adam_eps": 1e-8,
        "data_dir": "",
        "checkpoint_interval": 1_000_000,
        "batch_size": batch_size,
        "minibatch_size": batch_size,
        "max_minibatch_size": batch_size,
        "bptt_horizon": bptt_horizon,
        "compile": False,
        "compile_mode": "default",
        "compile_fullgraph": False,
        "vtrace_rho_clip": 1.0,
        "vtrace_c_clip": 1.0,
        "prio_alpha": 0.8,
        "prio_beta0": 0.2,
        "use_rnn": False,
    }


def _stop_pufferlib(trainer: PuffeRL) -> None:
    with contextlib.suppress(Exception):
        trainer.vecenv.close()
    with contextlib.suppress(Exception):
        trainer.utilization.stop()


def _metadata(
    seed: int,
    num_envs: int,
    batch_size: int,
    total_timesteps: int,
) -> dict[str, object]:
    return {
        "backend": PUFFERLIB_BACKEND_NAME,
        "algorithm": "ppo",
        "trainer": "pufferlib.pufferl.PuffeRL",
        "pufferlib_version": "3.0.0",
        "seed": seed,
        "num_envs": num_envs,
        "batch_size": batch_size,
        "total_timesteps": total_timesteps,
        "export": "ppo_reward_checked_bucket_table",
        "remote_logging": False,
    }


def _flag(value: bool) -> float:
    return 1.0 if value else -1.0


def _bounded(value: float) -> float:
    return max(-1.0, min(1.0, value))
