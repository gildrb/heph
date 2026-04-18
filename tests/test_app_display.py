from __future__ import annotations

import io
import sys

from hephaistos.app import display


class _ProxyStdout:
    def __init__(self, original_stdout) -> None:
        self.original_stdout = original_stdout


def test_real_stdout_unwraps_patch_stdout_proxy(monkeypatch) -> None:
    real_stdout = io.StringIO()
    monkeypatch.setattr(sys, "stdout", _ProxyStdout(_ProxyStdout(real_stdout)))

    assert display._real_stdout() is real_stdout


def test_direct_print_writes_to_real_stdout(monkeypatch) -> None:
    real_stdout = io.StringIO()
    proxy_stdout = _ProxyStdout(real_stdout)
    monkeypatch.setattr(sys, "stdout", proxy_stdout)

    display.direct_print("hello", end="!")

    assert real_stdout.getvalue() == "hello!"


def test_direct_input_swaps_stdout_and_restores_it(monkeypatch) -> None:
    real_stdout = io.StringIO()
    proxy_stdout = _ProxyStdout(real_stdout)
    seen = []

    def fake_input(prompt: str = "") -> str:
        seen.append((prompt, sys.stdout))
        return "typed"

    monkeypatch.setattr(sys, "stdout", proxy_stdout)
    monkeypatch.setattr("builtins.input", fake_input)

    assert display.direct_input("prompt> ") == "typed"
    assert seen == [("prompt> ", real_stdout)]
    assert sys.stdout is proxy_stdout
