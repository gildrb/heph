"""Armory index: scans materials, chunks files, persists to disk.

The index stores all chunks with metadata and content hashes for
incremental rebuild detection.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
from collections.abc import Iterator
from pathlib import Path
from typing import cast

from hephaistos._types import is_object_list, is_string_mapping
from hephaistos.logging import Timer, get_logger
from hephaistos.materials import MATERIALS_DIR, iter_material_files
from hephaistos.rag.chunker import (
    Chunk,
    ChunkedDocument,
    ChunkStrategy,
    _is_docling_available,
    _is_docling_file,
    _is_text_file,
    chunk_file,
)

_log = get_logger("rag.index")

_INDEX_FILE = "rag_index.json"

_CHUNK_SIZE = 500
_OVERLAP = 100

# Persisted index format version — bump when layout changes.
_INDEX_VERSION = 4


def _file_hash(path: Path) -> str | None:
    """Compute a content hash for a file.

    Uses ``read_bytes()`` so binary files (PDF, DOCX, etc.) are hashed
    correctly without decode errors.
    """
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    except OSError:
        return None


def _unindexable_reason(path: Path) -> str:
    """Return a human-readable reason why a file could not be indexed."""
    if _is_docling_file(path):
        if _is_docling_available():
            return "docling conversion failed (empty or corrupt document)"
        return (
            "binary document; document conversion backend unavailable "
            "(update or reinstall Hephaistos, then rebuild the index)"
        )
    return "binary file; unsupported format"


def _resolved_path_within_materials(path: Path, armory_path: Path) -> Path | None:
    if path.is_symlink():
        _log.warning(
            "skipping symlinked material",
            extra={"fields": {"path": str(path), "armory": str(armory_path)}},
        )
        return None
    materials_path = armory_path / MATERIALS_DIR
    if materials_path.is_symlink():
        _log.warning(
            "skipping symlinked material directory",
            extra={"fields": {"path": str(materials_path), "armory": str(armory_path)}},
        )
        return None
    try:
        resolved_materials = materials_path.resolve(strict=True)
        resolved_path = path.resolve(strict=True)
    except OSError:
        return None
    if not resolved_path.is_relative_to(resolved_materials):
        _log.warning(
            "skipping material outside material directory",
            extra={"fields": {"path": str(path), "armory": str(armory_path)}},
        )
        return None
    return resolved_path


def _chunks_match(left: Chunk, right: Chunk, *, include_heading: bool) -> bool:
    if left.text != right.text:
        return False
    if left.source != right.source:
        return False
    if left.index != right.index:
        return False
    if left.char_start != right.char_start or left.char_end != right.char_end:
        return False
    if not include_heading:
        return True
    return left.heading == right.heading and left.heading_level == right.heading_level


def _documents_match(
    loaded: list[ChunkedDocument],
    expected: list[ChunkedDocument],
    *,
    include_heading: bool,
) -> bool:
    if len(loaded) != len(expected):
        return False
    for left_doc, right_doc in zip(loaded, expected, strict=True):
        if left_doc.source != right_doc.source:
            return False
        if left_doc.content_hash != right_doc.content_hash:
            return False
        if len(left_doc.chunks) != len(right_doc.chunks):
            return False
        for left_chunk, right_chunk in zip(left_doc.chunks, right_doc.chunks, strict=True):
            if not _chunks_match(left_chunk, right_chunk, include_heading=include_heading):
                return False
    return True


class ArmoryIndex:
    """Manages the chunk index for an armory."""

    def __init__(
        self,
        armory_path: Path,
        *,
        strategy: ChunkStrategy = ChunkStrategy.AUTO,
    ) -> None:
        self.armory_path = armory_path
        self.strategy = strategy
        self.documents: list[ChunkedDocument] = []
        self._file_hashes: dict[str, str] = {}  # rel_path -> hash
        self._retriever: object | None = None  # cached default retriever instance
        self._retriever_cache: dict[tuple[str, int | None], object] = {}
        self.unindexable_files: dict[str, str] = {}  # rel_path -> reason

    @property
    def all_chunks(self) -> list[Chunk]:
        chunks: list[Chunk] = []
        for doc in self.documents:
            chunks.extend(doc.chunks)
        return chunks

    @property
    def content_hash(self) -> str:
        """Stable hash of the index content for cache invalidation."""
        hasher = hashlib.sha256()
        for doc in self.documents:
            hasher.update(doc.content_hash.encode())
            hasher.update(str(len(doc.chunks)).encode())
        return hasher.hexdigest()[:16]

    def save_embeddings(self, embeddings: list[list[float]], model_name: str) -> Path | None:
        """Persist computed embeddings keyed by content hash + model name."""
        if not embeddings:
            return None
        embed_path = (
            self.armory_path
            / ".hephaistos"
            / f"embeddings_{self.content_hash}_{model_name.replace('/', '_')}.json"
        )
        embed_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "content_hash": self.content_hash,
            "model_name": model_name,
            "chunk_count": len(self.all_chunks),
            "embeddings": embeddings,
        }
        embed_path.write_text(
            json.dumps(data, ensure_ascii=False),
            encoding="utf-8",
        )
        _log.debug(
            "embeddings saved",
            extra={"fields": {"path": str(embed_path), "chunks": len(embeddings)}},
        )
        return embed_path

    def load_embeddings(self, model_name: str) -> list[list[float]] | None:
        """Load persisted embeddings if they match the current index."""
        embed_path = (
            self.armory_path
            / ".hephaistos"
            / f"embeddings_{self.content_hash}_{model_name.replace('/', '_')}.json"
        )
        if not embed_path.is_file():
            return None
        try:
            data: object = json.loads(embed_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if not is_string_mapping(data):
            return None
        if data.get("content_hash") != self.content_hash:
            return None
        if data.get("model_name") != model_name:
            return None
        if data.get("chunk_count") != len(self.all_chunks):
            return None
        raw_embeddings = data.get("embeddings")
        if not isinstance(raw_embeddings, list):
            return None
        typed: list[list[float]] = []
        for raw_row in cast("list[object]", raw_embeddings):
            if not isinstance(raw_row, list):
                return None
            typed_row: list[float] = []
            for raw_val in cast("list[object]", raw_row):
                if isinstance(raw_val, int | float):
                    typed_row.append(float(raw_val))
                else:
                    typed_row.append(float(str(raw_val)))
            typed.append(typed_row)
        _log.debug(
            "embeddings loaded from cache",
            extra={"fields": {"path": str(embed_path), "chunks": len(typed)}},
        )
        return typed

    @property
    def chunk_count(self) -> int:
        return sum(len(doc.chunks) for doc in self.documents)

    def build(self) -> None:
        """Scan material files and build the chunk index."""
        timer = Timer()
        self.documents = []
        self._file_hashes = {}
        self._retriever = None
        self._retriever_cache = {}
        self.unindexable_files = {}

        with timer:
            for file_path in self._iter_source_files():
                rel = str(file_path.relative_to(self.armory_path))
                content_hash = _file_hash(file_path)
                if content_hash is not None:
                    self._file_hashes[rel] = content_hash

                doc = chunk_file(
                    file_path,
                    self.armory_path,
                    _CHUNK_SIZE,
                    _OVERLAP,
                    strategy=self.strategy,
                )
                if doc is not None and doc.chunks:
                    self.documents.append(doc)
                elif not _is_text_file(file_path):
                    reason = _unindexable_reason(file_path)
                    self.unindexable_files[rel] = reason

        _log.info(
            "index built",
            extra={
                "fields": {
                    "armory": str(self.armory_path),
                    "strategy": self.strategy.value,
                    "documents": len(self.documents),
                    "chunks": self.chunk_count,
                    "latency_ms": timer.ms,
                }
            },
        )

    def save(self) -> Path:
        """Persist the index to ``.hephaistos/rag_index.json``."""
        index_path = self.armory_path / ".hephaistos" / _INDEX_FILE
        index_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": _INDEX_VERSION,
            "chunk_size": _CHUNK_SIZE,
            "overlap": _OVERLAP,
            "strategy": self.strategy.value,
            "file_hashes": self._file_hashes,
            "documents": [
                {
                    "source": doc.source,
                    "content_hash": doc.content_hash,
                    "chunks": [
                        {
                            "text": c.text,
                            "source": c.source,
                            "index": c.index,
                            "char_start": c.char_start,
                            "char_end": c.char_end,
                            "heading": c.heading,
                            "heading_level": c.heading_level,
                        }
                        for c in doc.chunks
                    ],
                }
                for doc in self.documents
            ],
        }
        index_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return index_path

    def load(self) -> bool:
        """Load the index from disk. Returns False if index is missing/corrupt."""
        index_path = self.armory_path / ".hephaistos" / _INDEX_FILE
        if not index_path.is_file():
            return False

        try:
            data: object = json.loads(index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return False
        if not is_string_mapping(data):
            return False

        raw_version = data.get("version", 1)
        version = raw_version if isinstance(raw_version, int) else 1
        if version not in (1, 2, 3, 4):
            return False
        if version >= 2 and "strategy" in data:
            raw_strategy = data["strategy"]
            if isinstance(raw_strategy, str):
                with contextlib.suppress(ValueError):
                    self.strategy = ChunkStrategy(raw_strategy)

        self.documents = []
        self._file_hashes = {}
        self._retriever = None
        self._retriever_cache = {}
        self.unindexable_files = {}
        file_hashes_raw = data.get("file_hashes", {})
        if is_string_mapping(file_hashes_raw):
            self._file_hashes = {key: str(value) for key, value in file_hashes_raw.items()}

        raw_documents = data.get("documents", [])
        if not is_object_list(raw_documents):
            return False
        for doc_data in raw_documents:
            if not is_string_mapping(doc_data):
                continue
            raw_chunks = doc_data.get("chunks", [])
            if not is_object_list(raw_chunks):
                continue
            chunks: list[Chunk] = []
            for raw_chunk in raw_chunks:
                if not is_string_mapping(raw_chunk):
                    continue
                raw_text = raw_chunk.get("text", "")
                text = raw_text if isinstance(raw_text, str) else ""
                raw_source = raw_chunk.get("source", "")
                source = raw_source if isinstance(raw_source, str) else ""
                raw_index = raw_chunk.get("index", 0)
                index = raw_index if isinstance(raw_index, int) else 0
                raw_char_start = raw_chunk.get("char_start", 0)
                char_start = raw_char_start if isinstance(raw_char_start, int) else 0
                raw_char_end = raw_chunk.get("char_end", 0)
                char_end = raw_char_end if isinstance(raw_char_end, int) else 0
                raw_heading = raw_chunk.get("heading", "")
                heading = raw_heading if isinstance(raw_heading, str) else ""
                raw_heading_level = raw_chunk.get("heading_level", 0)
                heading_level = raw_heading_level if isinstance(raw_heading_level, int) else 0
                chunks.append(
                    Chunk(
                        text=text,
                        source=source,
                        index=index,
                        char_start=char_start,
                        char_end=char_end,
                        heading=heading,
                        heading_level=heading_level,
                    )
                )
            raw_doc_source = doc_data.get("source", "")
            doc_source = raw_doc_source if isinstance(raw_doc_source, str) else ""
            raw_content_hash = doc_data.get("content_hash", "")
            content_hash = raw_content_hash if isinstance(raw_content_hash, str) else ""
            doc = ChunkedDocument(
                source=doc_source,
                chunks=chunks,
                content_hash=content_hash,
            )
            self.documents.append(doc)
            if doc.content_hash and doc.source not in self._file_hashes:
                self._file_hashes[doc.source] = doc.content_hash

        if not self._matches_material_files(include_heading=version >= 2):
            _log.warning(
                "rag index cache does not match material files",
                extra={"fields": {"armory": str(self.armory_path)}},
            )
            self.documents = []
            self._file_hashes = {}
            return False

        self._rebuild_unindexable_files()
        return True

    def is_stale(self) -> bool:
        """Check if any material files changed since last index build."""
        if not self._file_hashes:
            return True

        indexed_sources = {doc.source for doc in self.documents}
        for file_path in self._iter_source_files():
            rel = str(file_path.relative_to(self.armory_path))
            if rel not in self._file_hashes:
                return True
            h = _file_hash(file_path)
            if h is None or h != self._file_hashes.get(rel):
                return True
            if (
                _is_docling_available()
                and _is_docling_file(file_path)
                and rel not in indexed_sources
            ):
                return True

        return len(self._file_hashes) != self._count_source_files()

    def _count_source_files(self) -> int:
        return sum(1 for _ in self._iter_source_files())

    def _iter_source_files(self) -> Iterator[Path]:
        for file_path in iter_source_files(self.armory_path):
            if _resolved_path_within_materials(file_path, self.armory_path) is None:
                continue
            yield file_path

    def _fresh_documents_and_hashes(self) -> tuple[list[ChunkedDocument], dict[str, str]]:
        documents: list[ChunkedDocument] = []
        file_hashes: dict[str, str] = {}
        loaded_by_source = {doc.source: doc for doc in self.documents}
        docling_available = _is_docling_available()
        for file_path in self._iter_source_files():
            rel = str(file_path.relative_to(self.armory_path))
            content_hash = _file_hash(file_path)
            if content_hash is not None:
                file_hashes[rel] = content_hash
            loaded_doc = loaded_by_source.get(rel)
            if not docling_available and _is_docling_file(file_path):
                if loaded_doc is not None and loaded_doc.content_hash == content_hash:
                    documents.append(loaded_doc)
                continue
            doc = chunk_file(
                file_path,
                self.armory_path,
                _CHUNK_SIZE,
                _OVERLAP,
                strategy=self.strategy,
            )
            if doc is not None and doc.chunks:
                documents.append(doc)
            elif (
                _is_docling_file(file_path)
                and loaded_doc is not None
                and loaded_doc.content_hash == content_hash
            ):
                documents.append(loaded_doc)
        return documents, file_hashes

    def _preserve_unavailable_docling_documents_from(self, previous: ArmoryIndex) -> None:
        """Keep converted Docling chunks when this runtime cannot recreate them."""
        if _is_docling_available():
            return
        indexed_sources = {doc.source for doc in self.documents}
        for document in previous.documents:
            if document.source in indexed_sources or not _is_docling_file(Path(document.source)):
                continue
            if self._file_hashes.get(document.source) != document.content_hash:
                continue
            self.documents.append(document)
            self.unindexable_files.pop(document.source, None)

    def _matches_material_files(self, *, include_heading: bool) -> bool:
        documents, file_hashes = self._fresh_documents_and_hashes()
        if self._file_hashes != file_hashes:
            return False
        return _documents_match(self.documents, documents, include_heading=include_heading)

    def _rebuild_unindexable_files(self) -> None:
        """Populate ``unindexable_files`` by comparing scanned files against indexed docs."""
        indexed_sources = {doc.source for doc in self.documents}
        self.unindexable_files = {}
        for file_path in self._iter_source_files():
            rel = str(file_path.relative_to(self.armory_path))
            if rel not in indexed_sources and not _is_text_file(file_path):
                self.unindexable_files[rel] = _unindexable_reason(file_path)


def iter_source_files(armory_path: Path) -> Iterator[Path]:
    """Compatibility wrapper for visible study material files."""
    yield from iter_material_files(armory_path)


def scan_unindexable_files(armory_path: Path) -> dict[str, str]:
    """Return a mapping of material files that cannot be indexed to the reason.

    This is a lightweight scan that does not require building the full RAG index.
    Used to inform the system prompt about files the LLM cannot read or search.
    """
    result: dict[str, str] = {}
    materials_dir = armory_path / MATERIALS_DIR
    if not materials_dir.is_dir():
        return result
    for file_path in sorted(materials_dir.rglob("*")):
        if not file_path.is_file():
            continue
        rel = str(file_path.relative_to(armory_path))
        # Skip hidden files
        if any(part.startswith(".") for part in Path(rel).parts):
            continue
        if not _is_text_file(file_path) and not (
            _is_docling_file(file_path) and _is_docling_available()
        ):
            result[rel] = _unindexable_reason(file_path)
    return result


def build_index(
    armory_path: Path,
    *,
    strategy: ChunkStrategy = ChunkStrategy.AUTO,
) -> ArmoryIndex:
    """Build a fresh index for the armory and persist it."""
    previous = ArmoryIndex(armory_path, strategy=strategy)
    previous_loaded = previous.load()
    index = ArmoryIndex(armory_path, strategy=strategy)
    index.build()
    if previous_loaded:
        index._preserve_unavailable_docling_documents_from(previous)
    index.save()
    _log.info(
        "index built and saved",
        extra={
            "fields": {
                "armory": str(armory_path),
                "strategy": strategy.value,
                "chunks": index.chunk_count,
            }
        },
    )
    return index


def load_or_build(
    armory_path: Path,
    *,
    strategy: ChunkStrategy = ChunkStrategy.AUTO,
) -> ArmoryIndex:
    """Load existing index if fresh, otherwise rebuild."""
    index = ArmoryIndex(armory_path, strategy=strategy)
    if index.load() and not index.is_stale():
        _log.info(
            "index loaded from cache",
            extra={
                "fields": {
                    "armory": str(armory_path),
                    "chunks": index.chunk_count,
                }
            },
        )
        return index
    _log.info(
        "index stale or missing, rebuilding",
        extra={
            "fields": {
                "armory": str(armory_path),
            }
        },
    )
    return build_index(armory_path, strategy=strategy)
