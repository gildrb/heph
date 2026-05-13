"""Armory index: scans materials, chunks files, persists to disk.

The index stores all chunks with metadata and content hashes for
incremental rebuild detection.
"""

from __future__ import annotations

import contextlib
import hashlib
import hmac
import json
import os
import secrets
import signal
from collections.abc import Callable, Iterator, Mapping
from pathlib import Path
from typing import cast

from hephaistos._types import is_object_list, is_string_mapping
from hephaistos.logging import Timer, get_logger
from hephaistos.materials import MATERIALS_DIR, iter_material_files
from hephaistos.parameters.settings import user_config_dir
from hephaistos.rag.chunker import (
    Chunk,
    ChunkedDocument,
    ChunkStrategy,
    _can_convert_binary_file,
    _is_docling_available,
    _is_docling_file,
    _is_text_file,
    _normalize_extracted_text,
    chunk_file,
)

_log = get_logger("rag.index")

_INDEX_FILE = "rag_index.json"

_CHUNK_SIZE = 500
_OVERLAP = 100
_FILE_TIMEOUT_ENV = "HEPHAISTOS_INDEX_FILE_TIMEOUT_SECONDS"

# Persisted index format version — bump when layout changes.
_INDEX_VERSION = 7
IndexProgress = Callable[[str, str], None]
_CACHE_SIGNING_KEY_FILE = "rag_cache.key"
_CACHE_SIGNING_KEY_PATH_ENV = "HEPHAISTOS_RAG_CACHE_KEY_FILE"


class _IndexFileTimeoutError(TimeoutError):
    """Raised when a single material file exceeds the configured index budget."""


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
        if _can_convert_binary_file(path):
            return "document conversion failed (empty or corrupt document)"
        return (
            "binary document; document conversion backend unavailable "
            "(update or reinstall Hephaistos, then rebuild the index)"
        )
    return "binary file; unsupported format"


def _timeout_reason(seconds: int) -> str:
    return f"document conversion timed out after {seconds} second(s)"


def _file_timeout_seconds() -> int:
    raw = os.environ.get(_FILE_TIMEOUT_ENV, "").strip()
    if not raw:
        return 0
    try:
        seconds = int(raw)
    except ValueError:
        return 0
    return max(seconds, 0)


def _chunk_file_with_timeout(
    file_path: Path,
    armory_path: Path,
    *,
    strategy: ChunkStrategy,
    timeout_seconds: int,
) -> tuple[ChunkedDocument | None, bool]:
    if timeout_seconds <= 0:
        return (
            chunk_file(
                file_path,
                armory_path,
                _CHUNK_SIZE,
                _OVERLAP,
                strategy=strategy,
            ),
            False,
        )
    timed_out = False
    previous_handler = signal.getsignal(signal.SIGALRM)

    def _handle_timeout(_signum: int, _frame: object) -> None:
        nonlocal timed_out
        timed_out = True
        raise _IndexFileTimeoutError(_timeout_reason(timeout_seconds))

    signal.signal(signal.SIGALRM, _handle_timeout)
    signal.alarm(timeout_seconds)
    try:
        document = chunk_file(
            file_path,
            armory_path,
            _CHUNK_SIZE,
            _OVERLAP,
            strategy=strategy,
        )
    except _IndexFileTimeoutError:
        document = None
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)
    return document, timed_out


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


def _documents_digest(documents: object) -> str:
    encoded = json.dumps(documents, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


def _cache_signing_key_path() -> Path:
    raw_path = os.environ.get(_CACHE_SIGNING_KEY_PATH_ENV, "").strip()
    if raw_path:
        return Path(raw_path).expanduser()
    return user_config_dir() / _CACHE_SIGNING_KEY_FILE


def _cache_signing_key() -> bytes | None:
    key_path = _cache_signing_key_path()
    try:
        key_path.parent.mkdir(parents=True, exist_ok=True)
        if key_path.is_file():
            raw_key = key_path.read_text(encoding="utf-8").strip()
            key = bytes.fromhex(raw_key)
            if len(key) < 32:
                raise ValueError("rag cache signing key is too short")
            return key
        key = secrets.token_bytes(32)
        key_path.write_text(f"{key.hex()}\n", encoding="utf-8")
        with contextlib.suppress(OSError):
            key_path.chmod(0o600)
        return key
    except (OSError, ValueError):
        return None


def _index_signature_payload(data: Mapping[str, object]) -> bytes:
    signable_keys = (
        "version",
        "chunk_size",
        "overlap",
        "strategy",
        "file_hashes",
        "documents_digest",
        "documents",
    )
    signable = {key: data[key] for key in signable_keys if key in data}
    encoded = json.dumps(signable, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return encoded.encode("utf-8")


def _index_signature(data: Mapping[str, object]) -> str | None:
    key = _cache_signing_key()
    if key is None:
        return None
    return hmac.new(key, _index_signature_payload(data), hashlib.sha256).hexdigest()


def _index_signature_matches(data: Mapping[str, object]) -> bool:
    raw_signature = data.get("cache_signature")
    if not isinstance(raw_signature, str) or not raw_signature:
        return False
    expected = _index_signature(data)
    return expected is not None and hmac.compare_digest(raw_signature, expected)


def _normalized_text_contains(source_text: str, chunk_text: str) -> bool:
    if chunk_text in source_text:
        return True
    compact_source = " ".join(source_text.split())
    compact_chunk = " ".join(chunk_text.split())
    return bool(compact_chunk) and compact_chunk in compact_source


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

    def build(self, *, progress: IndexProgress | None = None) -> None:
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
                if progress is not None:
                    progress("reading", rel)
                content_hash = _file_hash(file_path)
                if content_hash is not None:
                    self._file_hashes[rel] = content_hash

                timeout_seconds = _file_timeout_seconds()
                doc, timed_out = _chunk_file_with_timeout(
                    file_path,
                    self.armory_path,
                    strategy=self.strategy,
                    timeout_seconds=timeout_seconds,
                )
                if doc is not None and doc.chunks:
                    self.documents.append(doc)
                    if progress is not None:
                        progress("indexed", f"{rel} ({len(doc.chunks)} chunks)")
                elif not _is_text_file(file_path):
                    reason = (
                        _timeout_reason(timeout_seconds)
                        if timed_out
                        else _unindexable_reason(file_path)
                    )
                    self.unindexable_files[rel] = reason
                    if progress is not None:
                        progress("skipped", f"{rel}: {reason}")

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
        documents = [
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
        ]

        data = {
            "version": _INDEX_VERSION,
            "chunk_size": _CHUNK_SIZE,
            "overlap": _OVERLAP,
            "strategy": self.strategy.value,
            "file_hashes": self._file_hashes,
            "documents_digest": _documents_digest(documents),
            "documents": documents,
        }
        signature = _index_signature(data)
        if signature is not None:
            data["cache_signature"] = signature
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
        if version not in (1, 2, 3, 5, 6, 7):
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
        raw_documents_digest = data.get("documents_digest")
        documents_digest = _documents_digest(raw_documents)
        if version >= 7:
            if (
                not isinstance(raw_documents_digest, str)
                or raw_documents_digest != documents_digest
            ):
                return False
            if not _index_signature_matches(data):
                return False
        elif (
            version >= 4
            and isinstance(raw_documents_digest, str)
            and raw_documents_digest != documents_digest
        ):
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
                text = _normalize_extracted_text(text)
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

        if not self._file_hashes_match_material_files():
            _log.warning(
                "rag index cache does not match material files",
                extra={"fields": {"armory": str(self.armory_path)}},
            )
            self.documents = []
            self._file_hashes = {}
            return False

        if not self._documents_match_material_sources(allow_binary_cache=version >= 7):
            _log.warning(
                "rag index cache chunks do not match material files",
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
                _can_convert_binary_file(file_path)
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

    def _preserve_failed_binary_documents_from(self, previous: ArmoryIndex) -> None:
        """Keep unchanged converted binary docs when conversion fails transiently."""
        indexed_sources = {doc.source for doc in self.documents}
        for document in previous.documents:
            if document.source in indexed_sources:
                continue
            if document.source not in self.unindexable_files:
                continue
            if _is_text_file(self.armory_path / document.source):
                continue
            if self._file_hashes.get(document.source) != document.content_hash:
                continue
            self.documents.append(document)
            self.unindexable_files.pop(document.source, None)

    def _documents_match_material_sources(self, *, allow_binary_cache: bool) -> bool:
        for document in self.documents:
            if not document.source:
                return False
            source_path = self.armory_path / document.source
            resolved_path = _resolved_path_within_materials(source_path, self.armory_path)
            if resolved_path is None or not resolved_path.is_file():
                return False
            material_hash = _file_hash(resolved_path)
            if material_hash is None or self._file_hashes.get(document.source) != material_hash:
                return False
            if _is_text_file(resolved_path):
                try:
                    source_text = _normalize_extracted_text(
                        resolved_path.read_text(encoding="utf-8")
                    )
                except (UnicodeDecodeError, OSError):
                    return False
                text_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()[:16]
                if document.content_hash and document.content_hash != text_hash:
                    return False
                for chunk in document.chunks:
                    if chunk.source != document.source:
                        return False
                    if not _normalized_text_contains(source_text, chunk.text):
                        return False
            else:
                if document.content_hash and document.content_hash != material_hash:
                    return False
                if document.chunks and not allow_binary_cache:
                    return False
        return True

    def _file_hashes_match_material_files(self) -> bool:
        file_hashes: dict[str, str] = {}
        for file_path in self._iter_source_files():
            rel = str(file_path.relative_to(self.armory_path))
            content_hash = _file_hash(file_path)
            if content_hash is None:
                continue
            file_hashes[rel] = content_hash
        return self._file_hashes == file_hashes

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
    for file_path in iter_source_files(armory_path):
        if _resolved_path_within_materials(file_path, armory_path) is None:
            continue
        rel = str(file_path.relative_to(armory_path))
        if not _is_text_file(file_path) and not _can_convert_binary_file(file_path):
            result[rel] = _unindexable_reason(file_path)
    return result


def build_index(
    armory_path: Path,
    *,
    strategy: ChunkStrategy = ChunkStrategy.AUTO,
    progress: IndexProgress | None = None,
) -> ArmoryIndex:
    """Build a fresh index for the armory and persist it."""
    previous = ArmoryIndex(armory_path, strategy=strategy)
    previous_loaded = previous.load()
    index = ArmoryIndex(armory_path, strategy=strategy)
    index.build(progress=progress)
    if previous_loaded:
        index._preserve_unavailable_docling_documents_from(previous)
        index._preserve_failed_binary_documents_from(previous)
    if progress is not None:
        progress("writing", str(index.armory_path / ".hephaistos" / _INDEX_FILE))
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
    progress: IndexProgress | None = None,
) -> ArmoryIndex:
    """Load existing index if fresh, otherwise rebuild."""
    index = ArmoryIndex(armory_path, strategy=strategy)
    if index.load() and not index.is_stale():
        if progress is not None:
            index_path = armory_path / ".hephaistos" / _INDEX_FILE
            progress("loaded", f"{index_path} ({index.chunk_count} chunks)")
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
    return build_index(armory_path, strategy=strategy, progress=progress)
