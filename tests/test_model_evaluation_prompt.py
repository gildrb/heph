from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from hephaistos.armory.storage import initialize
from scripts import run_external_benchmarks

ROOT = Path(__file__).resolve().parent.parent
PROMPT_PATH = ROOT / "benchmarks" / "model-evaluation-prompt.md"


def _prompt_text() -> str:
    assert PROMPT_PATH.is_file()
    return PROMPT_PATH.read_text(encoding="utf-8")


def _write_jsonl(path: Path, rows: Sequence[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_report(path: Path) -> dict[str, object]:
    return cast("dict[str, object]", json.loads(path.read_text(encoding="utf-8")))


def _make_suite(root: Path) -> Path:
    suite = root / "suite"
    armory = suite / "armory"
    initialize(armory)
    (armory / "materials" / "alpha.md").write_text(
        "Alpha evidence explains deterministic benchmark retrieval and evaluation.\n",
        encoding="utf-8",
    )
    _write_jsonl(
        suite / "rag.jsonl",
        [
            {
                "id": "alpha",
                "query": "deterministic benchmark retrieval alpha evidence",
                "expected": ["materials/alpha.md"],
                "top_k": 3,
            }
        ],
    )
    return suite


def test_model_evaluation_prompt_defines_identity_and_protocol_sections() -> None:
    text = _prompt_text()

    assert "Prompt-ID: hephaistos-benchmark-evaluation" in text
    assert "Prompt-Version:" in text
    assert "## Evaluation Protocol" in text
    assert "## Required Inputs" in text
    assert "## Expected Output" in text
    assert "## Result Interpretation" in text


def test_model_evaluation_prompt_requires_grounded_deterministic_reporting() -> None:
    text = _prompt_text().lower()

    for term in (
        "benchmark evidence",
        "hit rate",
        "mrr",
        "expected recall",
        "latency",
        "reproducibility",
        "statistical analysis",
        "deterministic",
        "unsupported extrapolation",
        "missing data",
    ):
        assert term in text
    assert "do not invent" in text
    assert "limit conclusions to the supplied benchmark artifacts" in text


def test_runner_records_prompt_identity_metadata(tmp_path: Path) -> None:
    suite = _make_suite(tmp_path)
    report_path = tmp_path / "runner.json"
    expected_hash = hashlib.sha256(PROMPT_PATH.read_bytes()).hexdigest()

    status = run_external_benchmarks.main(
        [
            "beir",
            "beir/fixture",
            "--suite",
            str(suite),
            "--prompt",
            str(PROMPT_PATH),
            "--model-label",
            "fixture-model",
            "--json-report",
            str(report_path),
        ]
    )

    report = _read_report(report_path)
    raw_metadata = report["metadata"]
    assert isinstance(raw_metadata, dict)
    metadata = cast("dict[str, object]", raw_metadata)
    assert status == 0
    assert metadata["prompt_path"] == str(PROMPT_PATH.resolve())
    assert metadata["prompt_hash"] == expected_hash
    assert metadata["prompt_title"] == "Hephaistos Benchmark Evaluation Prompt"
    assert metadata["prompt_version"] == "1.0.0"
    assert metadata["model"] == "fixture-model"
