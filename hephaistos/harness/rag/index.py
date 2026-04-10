"""Armory index: scans source/library, chunks files, persists to disk.

The index stores all chunks with metadata and content hashes for
incremental rebuild detection.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
from pathlib import Path

from hephaistos.harness.rag.chunker import (
    Chunk,
    ChunkedDocument,
    ChunkStrategy,
    chunk_file,
)
from hephaistos.logging import Timer, get_logger

_log = get_logger("rag.index")

_INDEX_FILE = "rag_index.json"
_SOURCE_DIRS = ("source", "library")

_CHUNK_SIZE = 500
_OVERLAP = 100

# Persisted index format version — bump when layout changes.
_INDEX_VERSION = 2


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

    @property
    def all_chunks(self) -> list[Chunk]:
        chunks: list[Chunk] = []
        for doc in self.documents:
            chunks.extend(doc.chunks)
        return chunks

    @property
    def chunk_count(self) -> int:
        return sum(len(doc.chunks) for doc in self.documents)

    def build(self) -> None:
        """Scan source directories and build the chunk index."""
        timer = Timer()
        self.documents = []
        self._file_hashes = {}

        with timer:
            for dirname in _SOURCE_DIRS:
                folder = self.armory_path / dirname
                if not folder.is_dir():
                    continue
                for file_path in sorted(folder.rglob("*")):
                    if not file_path.is_file():
                        continue
                    if any(part.startswith(".") for part in file_path.relative_to(folder).parts):
                        continue
                    doc = chunk_file(
                        file_path,
                        self.armory_path,
                        _CHUNK_SIZE,
                        _OVERLAP,
                        strategy=self.strategy,
                    )
                    if doc is not None and doc.chunks:
                        self.documents.append(doc)
                        self._file_hashes[doc.source] = doc.content_hash

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
            data = json.loads(index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return False

        version = data.get("version", 1)
        if version not in (1, 2):
            return False
        if version >= 2 and "strategy" in data:
            with contextlib.suppress(ValueError):
                self.strategy = ChunkStrategy(data["strategy"])

        self.documents = []
        self._file_hashes = {}
        for doc_data in data.get("documents", []):
            chunks = [
                Chunk(
                    text=c["text"],
                    source=c["source"],
                    index=c["index"],
                    char_start=c["char_start"],
                    char_end=c["char_end"],
                    heading=c.get("heading", ""),
                    heading_level=c.get("heading_level", 0),
                )
                for c in doc_data.get("chunks", [])
            ]
            doc = ChunkedDocument(
                source=doc_data["source"],
                chunks=chunks,
                content_hash=doc_data.get("content_hash", ""),
            )
            self.documents.append(doc)
            if doc.content_hash:
                self._file_hashes[doc.source] = doc.content_hash

        return True

    def is_stale(self) -> bool:
        """Check if any source files changed since last index build."""
        if not self._file_hashes:
            return True

        for dirname in _SOURCE_DIRS:
            folder = self.armory_path / dirname
            if not folder.is_dir():
                continue
            for file_path in sorted(folder.rglob("*")):
                if not file_path.is_file():
                    continue
                if any(part.startswith(".") for part in file_path.relative_to(folder).parts):
                    continue
                rel = str(file_path.relative_to(self.armory_path))
                if rel not in self._file_hashes:
                    return True
                h = _file_hash(file_path)
                if h is not None and h != self._file_hashes.get(rel):
                    return True

        return len(self._file_hashes) != self._count_source_files()

    def _count_source_files(self) -> int:
        count = 0
        for dirname in _SOURCE_DIRS:
            folder = self.armory_path / dirname
            if not folder.is_dir():
                continue
            for file_path in sorted(folder.rglob("*")):
                if not file_path.is_file():
                    continue
                if any(part.startswith(".") for part in file_path.relative_to(folder).parts):
                    continue
                count += 1
        return count


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
