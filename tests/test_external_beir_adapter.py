from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path
from typing import cast

import pytest

from scripts.external_benchmarks import beir_adapter
from scripts.external_benchmarks.conversion import MATERIAL_METADATA_NAME, RAG_DATASET_NAME


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def _as_dict(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast("dict[str, object]", value)


def _as_list(value: object) -> list[object]:
    assert isinstance(value, list)
    return cast("list[object]", value)


def _beir_fixture(tmp_path: Path) -> Path:
    fixture = tmp_path / "beir-fixture"
    _write_jsonl(
        fixture / "corpus.jsonl",
        [
            {
                "_id": "doc-alpha",
                "title": "Alpha document",
                "text": "Alpha source explains receptor signaling and clinical retrieval.",
                "metadata": {"source_url": "https://example.edu/alpha", "role": "paper"},
            },
            {
                "_id": "doc-beta",
                "title": "Beta document",
                "text": "Beta source is a plausible but non-relevant distractor.",
                "metadata": {"role": "reading"},
            },
            {
                "_id": "doc-gamma",
                "title": "Gamma document",
                "text": "Gamma source covers treatment evidence for the second query.",
                "metadata": {"role": "guideline"},
            },
        ],
    )
    _write_jsonl(
        fixture / "queries.jsonl",
        [
            {"_id": "query-1", "text": "Which source explains receptor signaling?"},
            {"_id": "query-2", "text": "Which source covers treatment evidence?"},
        ],
    )
    (fixture / "qrels").mkdir()
    (fixture / "qrels" / "test.tsv").write_text(
        "\n".join(
            [
                "query-id\tcorpus-id\tscore",
                "query-1\tdoc-alpha\t2",
                "query-1\tdoc-beta\t0",
                "query-2\tdoc-gamma\t1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return fixture


def _beir_zip_fixture(tmp_path: Path) -> Path:
    source = _beir_fixture(tmp_path)
    zip_path = tmp_path / "beir-fixture.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, Path("fixture") / path.relative_to(source))
    return zip_path


def _read_report(path: Path) -> dict[str, object]:
    return cast("dict[str, object]", json.loads(path.read_text(encoding="utf-8")))


def _assert_reported_local_cache_assets_exist(report: dict[str, object]) -> Path:
    cache = _as_dict(report["cache"])
    cache_path = Path(cast("str", cache["path"])).resolve()
    assert cache_path.is_dir()
    local_assets: list[Path] = []
    for raw_asset in _as_list(cache["assets"]):
        assert isinstance(raw_asset, str)
        if raw_asset.startswith("https://"):
            continue
        local_assets.append(Path(raw_asset).resolve())
    assert local_assets
    for asset in local_assets:
        assert asset.exists()
    return cache_path


def test_beir_adapter_maps_positive_qrels_to_expected_references(tmp_path: Path) -> None:
    source = _beir_fixture(tmp_path)
    output = tmp_path / "out"
    report_path = tmp_path / "report.json"

    status = beir_adapter.main(
        [
            "beir/fixture",
            "--source-dir",
            str(source),
            "--output",
            str(output),
            "--top-k",
            "7",
            "--json-report",
            str(report_path),
        ]
    )

    assert status == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "success"
    assert report["adapter"] == "beir"
    assert report["dataset"] == "beir/fixture"
    assert report["source_format"] == "beir-jsonl"
    assert report["counts"]["documents"] == 3
    assert report["counts"]["queries"] == 2
    assert report["counts"]["qrels"] == 3
    assert report["counts"]["cases"] == 2
    assert report["counts"]["positive_references"] == 2
    assert report["deterministic_parameters"]["top_k"] == 7
    assert report["cache"]["enabled"] is False
    assert (output / "armory" / ".hephaistos" / "armory.toml").is_file()
    assert (output / "armory" / "materials" / "doc-alpha.md").read_text(encoding="utf-8")

    cases = _read_jsonl(output / RAG_DATASET_NAME)
    first_case = cases[0]
    assert first_case["expected"] == ["materials/doc-alpha.md"]
    assert first_case["top_k"] == 7
    metadata = _as_dict(first_case["metadata"])
    assert metadata["original_query_id"] == "query-1"
    judgments = metadata["relevance_judgments"]
    assert judgments == [
        {
            "grade": 2,
            "metadata": {"line": 2, "qrels_path": "test.tsv"},
            "original_document_id": "doc-alpha",
            "positive": True,
            "source_id": "materials/doc-alpha.md",
        },
        {
            "grade": 0,
            "metadata": {"line": 3, "qrels_path": "test.tsv"},
            "original_document_id": "doc-beta",
            "positive": False,
            "source_id": "materials/doc-beta.md",
        },
    ]
    assert metadata["positive_threshold"] == 1
    material_metadata = _read_jsonl(output / MATERIAL_METADATA_NAME)
    assert material_metadata[0]["original_document_id"] == "doc-alpha"
    assert _as_dict(material_metadata[0]["metadata"])["role"] == "paper"


def test_beir_adapter_source_zip_default_cache_stays_outside_output(
    tmp_path: Path,
) -> None:
    source_zip = _beir_zip_fixture(tmp_path)
    output = tmp_path / "out"
    report_path = tmp_path / "report.json"

    status = beir_adapter.main(
        [
            "beir/fixture",
            "--source-zip",
            str(source_zip),
            "--output",
            str(output),
            "--json-report",
            str(report_path),
        ]
    )

    assert status == 0
    report = _read_report(report_path)
    assert report["status"] == "success"
    cache = _as_dict(report["cache"])
    assert cache["enabled"] is True
    assert cache["used"] is True
    cache_path = _assert_reported_local_cache_assets_exist(report)
    assert not cache_path.is_relative_to(output.resolve())
    assert not (output / ".adapter-cache").exists()
    assert (output / RAG_DATASET_NAME).is_file()


def test_beir_adapter_download_default_cache_does_not_populate_output_before_conversion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_zip = _beir_zip_fixture(tmp_path)
    output = tmp_path / "out"
    report_path = tmp_path / "report.json"
    download_url = "https://example.edu/beir-fixture.zip"
    observed: dict[str, object] = {}

    def fake_urlretrieve(url: str, filename: str | Path) -> tuple[str, object]:
        assert url == download_url
        observed["output_exists_before_download"] = output.exists()
        target = Path(filename).resolve()
        observed["download_target"] = str(target)
        shutil.copyfile(source_zip, target)
        return str(target), None

    monkeypatch.setattr(beir_adapter.urllib.request, "urlretrieve", fake_urlretrieve)

    status = beir_adapter.main(
        [
            "beir/fixture",
            "--download-url",
            download_url,
            "--output",
            str(output),
            "--json-report",
            str(report_path),
        ]
    )

    assert status == 0
    assert observed["output_exists_before_download"] is False
    download_target = Path(cast("str", observed["download_target"])).resolve()
    assert not download_target.is_relative_to(output.resolve())
    report = _read_report(report_path)
    cache_path = _assert_reported_local_cache_assets_exist(report)
    assert not cache_path.is_relative_to(output.resolve())
    assert not (output / ".adapter-cache").exists()


def test_beir_adapter_source_zip_overwrite_preserves_reported_cache_assets(
    tmp_path: Path,
) -> None:
    source_zip = _beir_zip_fixture(tmp_path)
    output = tmp_path / "out"
    first_report_path = tmp_path / "first-report.json"
    second_report_path = tmp_path / "second-report.json"

    first_status = beir_adapter.main(
        [
            "beir/fixture",
            "--source-zip",
            str(source_zip),
            "--output",
            str(output),
            "--json-report",
            str(first_report_path),
        ]
    )
    assert first_status == 0
    first_report = _read_report(first_report_path)
    first_cache_path = _assert_reported_local_cache_assets_exist(first_report)
    stale_generated_file = output / "armory" / "materials" / "stale.md"
    stale_generated_file.write_text("stale generated material\n", encoding="utf-8")

    second_status = beir_adapter.main(
        [
            "beir/fixture",
            "--source-zip",
            str(source_zip),
            "--output",
            str(output),
            "--json-report",
            str(second_report_path),
            "--overwrite",
        ]
    )

    assert second_status == 0
    second_report = _read_report(second_report_path)
    second_cache_path = _assert_reported_local_cache_assets_exist(second_report)
    assert second_cache_path == first_cache_path
    assert first_cache_path.exists()
    assert not stale_generated_file.exists()
    assert (output / RAG_DATASET_NAME).is_file()


def test_beir_adapter_source_zip_preserves_explicit_cache_dir_outside_output(
    tmp_path: Path,
) -> None:
    source_zip = _beir_zip_fixture(tmp_path)
    output = tmp_path / "out"
    cache_dir = tmp_path / "explicit-cache"
    report_path = tmp_path / "report.json"

    status = beir_adapter.main(
        [
            "beir/fixture",
            "--source-zip",
            str(source_zip),
            "--cache-dir",
            str(cache_dir),
            "--output",
            str(output),
            "--json-report",
            str(report_path),
        ]
    )

    assert status == 0
    report = _read_report(report_path)
    reported_cache_path = _assert_reported_local_cache_assets_exist(report)
    assert reported_cache_path == cache_dir.resolve()
    assert not reported_cache_path.is_relative_to(output.resolve())


def test_beir_adapter_output_is_deterministic(tmp_path: Path) -> None:
    source = _beir_fixture(tmp_path)
    first_output = tmp_path / "first"
    second_output = tmp_path / "second"

    for output in (first_output, second_output):
        status = beir_adapter.main(
            ["beir/fixture", "--source-dir", str(source), "--output", str(output)]
        )
        assert status == 0

    first_files = _relative_file_contents(first_output)
    second_files = _relative_file_contents(second_output)
    assert first_files == second_files


def test_beir_adapter_refuses_existing_output_without_overwrite(tmp_path: Path) -> None:
    source = _beir_fixture(tmp_path)
    output = tmp_path / "out"
    report_path = tmp_path / "report.json"
    output.mkdir()
    sentinel = output / "sentinel.txt"
    sentinel.write_text("keep me\n", encoding="utf-8")

    status = beir_adapter.main(
        [
            "beir/fixture",
            "--source-dir",
            str(source),
            "--output",
            str(output),
            "--json-report",
            str(report_path),
        ]
    )

    assert status == 2
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "error"
    assert report["error"]["code"] == "output_exists"
    assert sentinel.read_text(encoding="utf-8") == "keep me\n"
    assert not (output / RAG_DATASET_NAME).exists()


def test_beir_adapter_rejects_symlinked_output_root(tmp_path: Path) -> None:
    source = _beir_fixture(tmp_path)
    outside = tmp_path / "outside-output-target"
    outside.mkdir()
    output = tmp_path / "out-link"
    try:
        output.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are not supported on this filesystem")
    report_path = tmp_path / "report.json"

    status = beir_adapter.main(
        [
            "beir/fixture",
            "--source-dir",
            str(source),
            "--output",
            str(output),
            "--json-report",
            str(report_path),
        ]
    )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert status == 2
    assert report["status"] == "error"
    assert report["error"]["code"] == "unsafe_output_path"
    assert list(outside.iterdir()) == []


def test_beir_adapter_rejects_zip_path_traversal(tmp_path: Path) -> None:
    zip_path = tmp_path / "traversal.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("../escape.txt", "escape")
    output = tmp_path / "out"
    report_path = tmp_path / "report.json"

    status = beir_adapter.main(
        [
            "beir/fixture",
            "--source-zip",
            str(zip_path),
            "--output",
            str(output),
            "--json-report",
            str(report_path),
        ]
    )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert status == 2
    assert report["status"] == "error"
    assert report["error"]["code"] == "unsafe_archive"
    assert not (tmp_path / "escape.txt").exists()
    assert not output.exists()


def test_beir_adapter_reports_missing_referenced_document(tmp_path: Path) -> None:
    source = _beir_fixture(tmp_path)
    (source / "qrels" / "test.tsv").write_text(
        "\n".join(["query-id\tcorpus-id\tscore", "query-1\tmissing-doc\t1"]) + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "out"
    report_path = tmp_path / "report.json"

    status = beir_adapter.main(
        [
            "beir/fixture",
            "--source-dir",
            str(source),
            "--output",
            str(output),
            "--json-report",
            str(report_path),
        ]
    )

    assert status == 2
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "error"
    assert report["error"]["code"] == "missing_referenced_document"
    assert "missing-doc" in report["error"]["message"]
    assert not output.exists()


def _relative_file_contents(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
