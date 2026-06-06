"""PufferLib-backed replay training for Heph harness attempt policies."""

from __future__ import annotations

import contextlib
import io
import signal
import tempfile
import threading
import warnings
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
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
_FEATURE_COUNT = 20
_DEFAULT_SEED = 13


@dataclass(frozen=True, slots=True)
class PufferTrainingResult:
    table: Mapping[str, AttemptAction]
    metadata: Mapping[str, object]


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
        self.observation_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(_FEATURE_COUNT,),
            dtype=np.float32,
        )
        self.action_space = spaces.Discrete(len(_PUFFER_ACTIONS))
        self.render_mode = None

    def reset(
        self,
        *,
        seed: int | None = None,
        options: Mapping[str, object] | None = None,
    ) -> tuple[NDArray[np.float32], dict[str, object]]:
        if seed is not None:
            self._index = seed % max(1, len(self._records))
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
        return (
            self._current_features(),
            outcome.reward.total,
            True,
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
        return observation_features(self._records[self._index].observation)


def observation_features(observation: AttemptObservation) -> NDArray[np.float32]:
    """Return numeric structural features for the replay policy."""

    return np.asarray(
        [
            _bounded(observation.attempt_index / 5.0),
            _flag(observation.citation_required),
            _bounded(observation.evidence_count / 8.0),
            _bounded(observation.distinct_source_count / 5.0),
            _bounded(observation.sampled_source_count / 10.0),
            _bounded(observation.total_source_count / 20.0),
            _bounded(observation.top_score),
            _flag(observation.evidence_sufficient),
            _bounded(observation.evidence_confidence),
            _flag(observation.evidence_recommended_action == "abstain"),
            _flag(observation.has_citations),
            _bounded(observation.citation_count / 8.0),
            _flag(observation.all_citations_verified),
            _bounded(observation.unverified_citation_count / 4.0),
            _bounded(observation.unsupported_claim_count / 4.0),
            _bounded(observation.answer_relevance_score),
            _flag(observation.off_topic_answer),
            _bounded(observation.missing_required_citation_count / 4.0),
            _flag(observation.confident_thin_evidence),
            _bounded(observation.reply_chars / 1600.0),
        ],
        dtype=np.float32,
    )


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
        observations_by_bucket.setdefault(bucket(record.observation), record.observation)

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
    return {
        key: _PUFFER_ACTIONS[max(0, min(int(choice), len(_PUFFER_ACTIONS) - 1))]
        for key, choice in zip(keys, choices, strict=True)
    }


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
        "pufferlib_version": "3.0.0",
        "seed": seed,
        "num_envs": num_envs,
        "batch_size": batch_size,
        "total_timesteps": total_timesteps,
        "export": "bucket_table",
        "remote_logging": False,
    }


def _flag(value: bool) -> float:
    return 1.0 if value else -1.0


def _bounded(value: float) -> float:
    return max(-1.0, min(1.0, value))
