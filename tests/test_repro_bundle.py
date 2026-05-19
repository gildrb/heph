from __future__ import annotations

import json
from pathlib import Path

from scripts import repro_bundle


def test_export_bundle_copies_artifacts_and_verify_detects_tampering(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    report.write_text('{"pass_rate": 1.0}\n', encoding="utf-8")
    rows = tmp_path / "rows.jsonl"
    rows.write_text('{"case_id": "q1"}\n', encoding="utf-8")

    bundle_dir = tmp_path / "private-bundle"
    export = repro_bundle.export_bundle(
        bundle_dir,
        [
            {"role": "report", "path": report},
            {"role": "per-query", "path": rows},
        ],
        command_invocation="uv run python -m scripts.benchmark_answers answers.json",
    )

    assert export.status == "passed"
    assert export.artifact_count == 2
    manifest_path = Path(export.manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == repro_bundle.BUNDLE_SCHEMA_VERSION
    assert manifest["privacy"]["public_export"] is False
    assert manifest["command_invocation"].startswith("uv run python")
    assert Path(export.bundle_path, "artifacts", "report.json").is_file()

    verification = repro_bundle.verify_bundle(manifest_path)

    assert verification.status == "passed"
    assert verification.artifact_count == 2

    Path(export.bundle_path, "artifacts", "report.json").write_text(
        '{"pass_rate": 0.0}\n',
        encoding="utf-8",
    )

    tampered = repro_bundle.verify_bundle(manifest_path)

    assert tampered.status == "failed"
    assert "artifact report sha256 mismatch" in tampered.errors


def test_export_bundle_rejects_non_private_repo_output(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    report.write_text("{}\n", encoding="utf-8")

    result = repro_bundle.export_bundle(
        Path.cwd() / "public-bundle",
        [{"role": "report", "path": report}],
        command_invocation="uv run python -m scripts.benchmark_answers answers.json",
    )

    assert result.status == "failed"
    assert any("ignored private root" in error for error in result.errors)


def test_verify_bundle_rejects_schema_command_and_path_escape(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "wrong",
                "command_invocation": "",
                "privacy": {"public_export": True},
                "artifacts": [
                    {
                        "role": "escape",
                        "path": "../outside.json",
                        "original_path": "outside.json",
                        "sha256": "abc",
                        "size_bytes": 3,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = repro_bundle.verify_bundle(manifest_path)

    assert result.status == "failed"
    assert "manifest schema_version is unsupported" in result.errors
    assert "manifest command_invocation must be a non-empty string" in result.errors
    assert "manifest privacy.public_export must be false" in result.errors
    assert "artifact escape path escapes bundle" in result.errors


def test_repro_bundle_cli_export_and_verify(tmp_path: Path, capsys) -> None:
    report = tmp_path / "report.json"
    report.write_text('{"ok": true}\n', encoding="utf-8")
    bundle_dir = tmp_path / "cli-bundle"

    export_status = repro_bundle.main(
        [
            "export",
            str(bundle_dir),
            "--artifact",
            f"report={report}",
            "--command-invocation",
            "uv run python -m scripts.benchmark_answers answers.json",
        ]
    )

    assert export_status == 0
    export_output = json.loads(capsys.readouterr().out)
    assert export_output["status"] == "passed"

    verify_status = repro_bundle.main(["verify", str(bundle_dir / "manifest.json"), "--json"])

    assert verify_status == 0
    verify_output = json.loads(capsys.readouterr().out)
    assert verify_output["status"] == "passed"
