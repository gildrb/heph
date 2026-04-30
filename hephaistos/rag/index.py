"""Armory index: scans source/library, chunks files, persists to disk.

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
from hephaistos.materials import count_material_files, iter_material_files
from hephaistos.rag.chunker import (
    Chunk,
    ChunkedDocument,
    ChunkStrategy,
    chunk_file,
)

_log = get_logger("rag.index")

_INDEX_FILE = "rag_index.json"

_CHUNK_SIZE = 500
_OVERLAP = 100

# Persisted index format version — bump when layout changes.
_INDEX_VERSION = 3


def _file_hash(path: Path) -> str | None:
    """Compute a content hash for a file.

    Uses ``read_bytes()`` so binary files (PDF, DOCX, etc.) are hashed
    correctly without decode errors.
    """
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    except OSError:
        return None


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
        """Scan source directories and build the chunk index."""
        timer = Timer()
        self.documents = []
        self._file_hashes = {}
        self._retriever = None
        self._retriever_cache = {}

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
        if version not in (1, 2, 3):
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

        return True

    def is_stale(self) -> bool:
        """Check if any source files changed since last index build."""
        if not self._file_hashes:
            return True

        for file_path in self._iter_source_files():
            rel = str(file_path.relative_to(self.armory_path))
            if rel not in self._file_hashes:
                return True
            h = _file_hash(file_path)
            if h is None or h != self._file_hashes.get(rel):
                return True

        return len(self._file_hashes) != self._count_source_files()

    def _count_source_files(self) -> int:
        return count_material_files(self.armory_path)

    def _iter_source_files(self) -> Iterator[Path]:
        yield from iter_source_files(self.armory_path)


def iter_source_files(armory_path: Path) -> Iterator[Path]:
    """Compatibility wrapper for visible study material files."""
    yield from iter_material_files(armory_path)


def build_index(
    armory_path: Path,
    *,
    strategy: ChunkStrategy = ChunkStrategy.AUTO,
) -> ArmoryIndex:
    """Build a fresh index for the armory and persist it."""
    index = ArmoryIndex(armory_path, strategy=strategy)
    index.build()
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
