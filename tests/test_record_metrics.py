from __future__ import annotations

import json

import pytest

from scripts import record_metrics


def test_extract_jobs_supports_wrapped_jobs_payload() -> None:
    payload = json.dumps(
        {
            "jobs": [
                {"startedAt": "2026-04-22T10:00:00Z", "completedAt": "2026-04-22T10:00:03Z"},
                {"startedAt": "2026-04-22T10:00:05Z", "completedAt": "2026-04-22T10:00:09Z"},
            ]
        }
    )

    jobs = record_metrics._extract_jobs(payload)  # type: ignore[reportPrivateUsage]

    assert len(jobs) == 2
    assert jobs[0]["startedAt"] == "2026-04-22T10:00:00Z"


def test_get_recent_run_durations_handles_wrapped_jobs_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_gh(*args: str) -> str:
        if args[:2] == ("run", "list"):
            return json.dumps(
                [
                    {
                        "conclusion": "success",
                        "createdAt": "2026-04-22T10:00:00Z",
                        "databaseId": 123,
                        "headBranch": "main",
                    }
                ]
            )
        if args[:3] == ("run", "view", "123"):
            return json.dumps(
                {
                    "jobs": [
                        {
                            "startedAt": "2026-04-22T10:00:00Z",
                            "completedAt": "2026-04-22T10:00:03Z",
                        },
                        {
                            "startedAt": "2026-04-22T10:00:05Z",
                            "completedAt": "2026-04-22T10:00:09Z",
                        },
                    ]
                }
            )
        raise AssertionError(f"Unexpected gh args: {args}")

    monkeypatch.setattr(record_metrics, "_gh", fake_gh)

    durations = record_metrics._get_recent_run_durations(limit=1)  # type: ignore[reportPrivateUsage]

    assert durations == [
        {
            "run_id": "123",
            "duration_ms": 7000.0,
            "created_at": "2026-04-22T10:00:00Z",
        }
    ]


def test_parse_iso_accepts_utc_z_suffix() -> None:
    parsed = record_metrics._parse_iso("2026-04-22T10:00:00Z")  # type: ignore[reportPrivateUsage]

    assert parsed is not None
