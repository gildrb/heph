from __future__ import annotations

import pytest

from scripts import benchmark_prompt_cache


def test_prompt_cache_benchmark_passes() -> None:
    report = benchmark_prompt_cache.run_benchmark()

    assert report.pass_rate == 1.0
    assert report.stable_hash_reuse_rate == 1.0
    assert report.prefix_invalidation_rate == 1.0
    assert report.dynamic_tail_preservation_rate == 1.0
    assert report.request_order_preservation_rate == 1.0
    assert report.failures == ()


def test_prompt_cache_benchmark_cli_json(capsys: pytest.CaptureFixture[str]) -> None:
    status = benchmark_prompt_cache.main(["--json"])

    captured = capsys.readouterr()
    assert status == 0
    assert '"pass_rate": 1.0' in captured.out
