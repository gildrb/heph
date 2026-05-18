"""Build a deterministic standard-RAG manifest from local MS MARCO files."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Sequence
from pathlib import Path


class ManifestError(Exception):
    """Expected manifest builder failure."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _first_existing(root: Path, names: Sequence[str]) -> Path:
    for name in names:
        path = root / name
        if path.is_file():
            return path
    joined = ", ".join(names)
    raise ManifestError(f"missing one of: {joined}")


def _read_collection(path: Path) -> dict[str, str]:
    documents: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        document_id, text = parts
        if document_id.strip() and text.strip():
            documents[document_id.strip()] = text.strip()
    if not documents:
        raise ManifestError(f"collection is empty: {path}")
    return documents


def _read_queries(path: Path) -> dict[str, str]:
    queries: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        query_id, text = parts
        if query_id.strip() and text.strip():
            queries[query_id.strip()] = text.strip()
    if not queries:
        raise ManifestError(f"queries are empty: {path}")
    return queries


def _read_qrels(path: Path) -> dict[str, dict[str, float]]:
    qrels: dict[str, dict[str, float]] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 4:
            query_id, _, document_id, raw_grade = parts[:4]
        elif len(parts) == 3:
            query_id, document_id, raw_grade = parts
        else:
            continue
        try:
            grade = float(raw_grade)
        except ValueError:
            continue
        qrels.setdefault(query_id, {})[document_id] = grade
    if not qrels:
        raise ManifestError(f"qrels are empty: {path}")
    return qrels


def build_manifest(source_dir: Path, output_path: Path) -> dict[str, object]:
    root = source_dir.expanduser().resolve()
    collection_path = _first_existing(root, ("collection.tsv", "corpus.tsv"))
    queries_path = _first_existing(
        root,
        ("queries.dev.small.tsv", "queries.dev.tsv", "queries.eval.tsv", "queries.tsv"),
    )
    qrels_path = _first_existing(
        root,
        ("qrels.dev.small.tsv", "qrels.dev.tsv", "qrels.train.tsv", "qrels.tsv"),
    )
    documents_by_id = _read_collection(collection_path)
    queries_by_id = _read_queries(queries_path)
    qrels_by_query = _read_qrels(qrels_path)
    referenced_documents = {
        document_id
        for rows in qrels_by_query.values()
        for document_id, grade in rows.items()
        if grade > 0
    }
    documents = [
        {"id": document_id, "text": documents_by_id[document_id]}
        for document_id in sorted(referenced_documents & documents_by_id.keys())
    ]
    queries = [
        {
            "id": query_id,
            "question": queries_by_id[query_id],
            "relevant_documents": dict(sorted(qrels_by_query[query_id].items())),
        }
        for query_id in sorted(qrels_by_query)
        if query_id in queries_by_id
        and any(document_id in documents_by_id for document_id in qrels_by_query[query_id])
    ]
    if not documents or not queries:
        raise ManifestError("MS MARCO inputs produced no manifest documents or queries")
    manifest = {
        "dataset": "ms-marco",
        "domain": "open-domain-retrieval",
        "split": qrels_path.stem,
        "task_type": "passage-retrieval",
        "documents": documents,
        "queries": queries,
        "metadata": {
            "source_dir": str(root),
            "collection_sha256": _sha256(collection_path),
            "queries_sha256": _sha256(queries_path),
            "qrels_sha256": _sha256(qrels_path),
            "collection_count": len(documents_by_id),
            "manifest_document_count": len(documents),
            "query_count": len(queries),
            "qrels_query_count": len(qrels_by_query),
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--json-report", type=Path)
    args = parser.parse_args(argv)
    try:
        manifest = build_manifest(args.source_dir, args.output)
        status = 0
        error = ""
    except ManifestError as exc:
        manifest = {"documents": [], "queries": []}
        status = 2
        error = str(exc)
    report = {
        "status": "success" if status == 0 else "error",
        "output": str(args.output.expanduser().resolve()),
        "documents": len(manifest["documents"]),
        "queries": len(manifest["queries"]),
        "error": error,
    }
    if args.json_report is not None:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
