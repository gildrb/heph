"""Sample benchmark cases deterministically for fast retrieval experiments."""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast


def load_cases(path: Path) -> list[dict[str, object]]:
    """Load JSON or JSONL benchmark cases."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"could not read cases file: {path}") from exc
    try:
        if path.suffix == ".jsonl":
            payload: object = [
                json.loads(line)
                for line in text.splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
        else:
            payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid cases JSON: {path}") from exc
    raw_cases = payload.get("cases") if isinstance(payload, dict) else payload
    if not isinstance(raw_cases, list):
        raise TypeError("cases file must be a JSON list or an object with a 'cases' list")
    cases: list[dict[str, object]] = []
    for index, raw_case in enumerate(raw_cases, start=1):
        if not isinstance(raw_case, dict):
            raise TypeError(f"case {index} must be an object")
        cases.append(cast("dict[str, object]", raw_case))
    return cases


def load_report_labels(path: Path) -> dict[str, bool]:
    """Return case_id -> hit from an external runner report."""
    try:
        data: object = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"could not read benchmark report: {path}") from exc
    if not isinstance(data, dict):
        raise TypeError("benchmark report must be an object")
    labels: dict[str, bool] = {}
    for benchmark in _object_list(data.get("benchmarks")):
        for result in _object_list(benchmark.get("per_query_results")):
            case_id = result.get("case_id")
            hit = result.get("hit")
            if isinstance(case_id, str) and isinstance(hit, bool):
                labels[case_id] = hit
    if not labels:
        raise ValueError("benchmark report contains no per-query hit labels")
    return labels


def _object_list(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [cast("Mapping[str, object]", item) for item in value if isinstance(item, dict)]


def sample_cases(
    cases: Sequence[dict[str, object]],
    *,
    count: int,
    seed: int = 0,
    labels: Mapping[str, bool] | None = None,
    mode: str = "random",
) -> list[dict[str, object]]:
    """Sample cases deterministically."""
    if count <= 0:
        raise ValueError("count must be positive")
    rng = random.Random(seed)
    case_list = list(cases)
    if labels is None or mode == "random":
        return _sample_pool(case_list, count=count, rng=rng)
    hits = [case for case in case_list if labels.get(str(case.get("id"))) is True]
    misses = [case for case in case_list if labels.get(str(case.get("id"))) is False]
    if mode == "hits":
        return _sample_pool(hits, count=count, rng=rng)
    if mode == "misses":
        return _sample_pool(misses, count=count, rng=rng)
    if mode != "mixed":
        raise ValueError(f"unsupported sample mode: {mode}")
    miss_count = min(len(misses), count // 2)
    hit_count = min(len(hits), count - miss_count)
    selected = [
        *_sample_pool(misses, count=miss_count, rng=rng),
        *_sample_pool(hits, count=hit_count, rng=rng),
    ]
    if len(selected) < count:
        selected_ids = {id(case) for case in selected}
        selected.extend(
            _sample_pool(
                [case for case in case_list if id(case) not in selected_ids],
                count=count - len(selected),
                rng=rng,
            )
        )
    selected_by_id = {str(case.get("id")): case for case in selected}
    return [case for case in case_list if str(case.get("id")) in selected_by_id]


def _sample_pool(
    cases: Sequence[dict[str, object]],
    *,
    count: int,
    rng: random.Random,
) -> list[dict[str, object]]:
    pool = list(cases)
    if count >= len(pool):
        return pool
    selected_indices = sorted(rng.sample(range(len(pool)), count))
    return [pool[index] for index in selected_indices]


def write_jsonl(path: Path, cases: Sequence[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(case, ensure_ascii=False, sort_keys=True) + "\n" for case in cases),
        encoding="utf-8",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cases", type=Path, help="Input benchmark cases JSON/JSONL")
    parser.add_argument("output", type=Path, help="Output sampled JSONL path")
    parser.add_argument("--report", type=Path, help="External runner report for hit/miss labels")
    parser.add_argument(
        "--mode",
        choices=("random", "hits", "misses", "mixed"),
        default="random",
        help="Sampling mode; hit/miss modes require --report",
    )
    parser.add_argument("--count", type=int, default=40, help="Number of cases to sample")
    parser.add_argument("--seed", type=int, default=0, help="Deterministic random seed")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    report_path = cast("Path | None", args.report)
    mode = cast("str", args.mode)
    if mode != "random" and report_path is None:
        parser.error(f"--mode {mode} requires --report")
    try:
        cases = load_cases(cast("Path", args.cases))
        labels = load_report_labels(report_path) if report_path is not None else None
        sampled = sample_cases(
            cases,
            count=cast("int", args.count),
            seed=cast("int", args.seed),
            labels=labels,
            mode=mode,
        )
    except (TypeError, ValueError) as exc:
        print(f"sample benchmark cases error: {exc}", file=sys.stderr)
        return 2
    write_jsonl(cast("Path", args.output), sampled)
    print(
        f"sampled {len(sampled)} case(s) from {len(cases)} "
        f"mode={mode} seed={cast('int', args.seed)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
