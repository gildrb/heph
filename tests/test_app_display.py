from __future__ import annotations

import io
import sys

import pytest

from hephaistos.terminal import (
    _real_stdout,
    display,
)


class _ProxyStdout:
    def __init__(self, original_stdout: object) -> None:
        self.original_stdout = original_stdout


def test_real_stdout_unwraps_patch_stdout_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    real_stdout = io.StringIO()
    monkeypatch.setattr(sys, "stdout", _ProxyStdout(_ProxyStdout(real_stdout)))

    assert _real_stdout() is real_stdout


def test_direct_print_writes_to_real_stdout(monkeypatch: pytest.MonkeyPatch) -> None:
    real_stdout = io.StringIO()
    proxy_stdout = _ProxyStdout(real_stdout)
    monkeypatch.setattr(sys, "stdout", proxy_stdout)

    display.direct_print("hello", end="!")

    assert real_stdout.getvalue() == "hello!"


def test_direct_input_swaps_stdout_and_restores_it(monkeypatch: pytest.MonkeyPatch) -> None:
    real_stdout = io.StringIO()
    proxy_stdout = _ProxyStdout(real_stdout)
    seen: list[tuple[str, object]] = []

    def fake_input(prompt: str = "") -> str:
        seen.append((prompt, sys.stdout))
        return "typed"

    monkeypatch.setattr(sys, "stdout", proxy_stdout)
    monkeypatch.setattr("builtins.input", fake_input)

    assert display.direct_input("prompt> ") == "typed"
    assert seen == [("prompt> ", real_stdout)]
    assert sys.stdout is proxy_stdout
