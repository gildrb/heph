from __future__ import annotations

import pytest

from scripts.check_repo_policies import (
    PYTORCH_JIT_SCRIPT_POLICY_MESSAGE,
    _check_source,
)


def _messages(source: str, *, rel_path: str = "harness/example.py") -> list[str]:
    return [violation.message for violation in _check_source(source, rel_path)]


def test_repo_policy_allows_regular_pytorch_usage() -> None:
    source = """
from __future__ import annotations

import torch


def to_tensor(value: object) -> object:
    return torch.as_tensor(value)
""".lstrip()

    assert PYTORCH_JIT_SCRIPT_POLICY_MESSAGE not in _messages(source)


@pytest.mark.parametrize(
    "source",
    [
        """
from __future__ import annotations

import torch


def compile_model(model: object) -> object:
    return torch.jit.script(model)
""".lstrip(),
        """
from __future__ import annotations

import torch as th


def compile_model(model: object) -> object:
    return th.jit.script(model)
""".lstrip(),
        """
from __future__ import annotations

import torch.jit as jit


def compile_model(model: object) -> object:
    return jit.script(model)
""".lstrip(),
        """
from __future__ import annotations

from torch import jit


def compile_model(model: object) -> object:
    return jit.script(model)
""".lstrip(),
        """
from __future__ import annotations

from torch.jit import script as compile_script


def compile_model(model: object) -> object:
    return compile_script(model)
""".lstrip(),
        """
from __future__ import annotations

from torch import jit


def compile_model(model: object) -> object:
    return getattr(jit, "script")(model)
""".lstrip(),
    ],
)
def test_repo_policy_rejects_direct_torch_jit_script_usage(source: str) -> None:
    assert _messages(source).count(PYTORCH_JIT_SCRIPT_POLICY_MESSAGE) == 1


def test_repo_policy_ignores_plain_text_torch_jit_script_mentions() -> None:
    source = """
from __future__ import annotations

NOTE = "torch.jit.script appears here as documentation only"
""".lstrip()

    assert PYTORCH_JIT_SCRIPT_POLICY_MESSAGE not in _messages(source)


def test_repo_policy_limits_torch_jit_script_guard_to_runtime_source() -> None:
    source = """
from __future__ import annotations

import torch


def compile_model(model: object) -> object:
    return torch.jit.script(model)
""".lstrip()

    assert PYTORCH_JIT_SCRIPT_POLICY_MESSAGE not in _messages(
        source,
        rel_path="harness/test/test_example.py",
    )
