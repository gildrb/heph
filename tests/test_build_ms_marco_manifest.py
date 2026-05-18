from __future__ import annotations

import json
from pathlib import Path

from scripts import build_ms_marco_manifest


def test_build_ms_marco_manifest_from_local_files(tmp_path: Path) -> None:
    source = tmp_path / "msmarco"
    source.mkdir()
    (source / "collection.tsv").write_text(
        "d1\tAlpha relevant passage.\nd2\tBeta distractor passage.\nd3\tGamma relevant passage.\n",
        encoding="utf-8",
    )
    (source / "queries.dev.small.tsv").write_text(
        "q1\talpha question\nq2\tgamma question\n",
        encoding="utf-8",
    )
    (source / "qrels.dev.small.tsv").write_text(
        "q1 0 d1 1\nq1 0 d2 0\nq2 0 d3 1\n",
        encoding="utf-8",
    )
    output = tmp_path / "manifest.json"
    report = tmp_path / "report.json"

    status = build_ms_marco_manifest.main([str(source), str(output), "--json-report", str(report)])

    manifest = json.loads(output.read_text(encoding="utf-8"))
    report_payload = json.loads(report.read_text(encoding="utf-8"))
    assert status == 0
    assert manifest["dataset"] == "ms-marco"
    assert [document["id"] for document in manifest["documents"]] == ["d1", "d3"]
    assert len(manifest["queries"]) == 2
    assert report_payload["documents"] == 2
    assert report_payload["queries"] == 2
