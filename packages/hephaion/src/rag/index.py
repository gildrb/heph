"""Armory index: scans materials, chunks files, persists to disk.

The index stores all chunks with metadata and content hashes for
incremental rebuild detection.
"""

from __future__ import annotations

import contextlib
import hashlib
import hmac
import json
import math
import os
import secrets
import signal
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from _types import is_object_list, is_string_mapping
from ai_logging import Timer, get_logger
from materials import MATERIALS_DIR, iter_material_files
from parameters.settings import user_config_dir

from rag.chunker import (
    Chunk,
    ChunkedDocument,
    ChunkStrategy,
    _can_convert_binary_file,
    _is_docling_available,  # noqa: F401 - compatibility monkeypatch surface
    _is_docling_file,
    _is_text_file,
    _normalize_extracted_text,
    chunk_file,
)
from rag.retrieval_types import RetrieverCacheKey

_log = get_logger("rag.index")

_INDEX_FILE = "rag_index.json"
_CHUNK_SIZE = 500
_OVERLAP = 100
_FILE_TIMEOUT_ENV = "HEPHAION_INDEX_FILE_TIMEOUT_SECONDS"

# Persisted index format version — bump when layout changes.
_INDEX_VERSION = 8
_SUPPORTED_INDEX_VERSIONS = frozenset({1, 2, 3, 5, 6, 7, 8})
IndexProgress = Callable[[str, str], None]
_CACHE_SIGNING_KEY_FILE = "rag_cache.key"
_CACHE_SIGNING_KEY_PATH_ENV = "HEPHAION_RAG_CACHE_KEY_FILE"


class _IndexFileTimeoutError(TimeoutError):
    pass


@dataclass(frozen=True, slots=True)
class _SourceFileState:
    rel: str
    path: Path
    content_hash: str


@dataclass(slots=True)
class _IndexBuildStats:
    reused: int = 0
    rebuilt: int = 0


@dataclass(frozen=True, slots=True)
class _LoadedIndexData:
    data: dict[str, object]
    version: int
    raw_documents: list[object]


@dataclass(frozen=True, slots=True)
class _MaterialSourceMatch:
    path: Path
    content_hash: str


def _file_hash(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    except OSError:
        return None


def _read_json_mapping(path: Path) -> dict[str, object] | None:
    try:
        data: object = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if is_string_mapping(data) else None


def _unindexable_reason(path: Path) -> str:
    if _is_docling_file(path):
        if _can_convert_binary_file(path):
            return "document conversion failed (empty or corrupt document)"
        return (
            "binary document; document conversion backend unavailable "
            "(update or reinstall Heph, then rebuild the index)"
        )
    return "binary file; unsupported format"


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
        raise _IndexFileTimeoutError(
            f"document conversion timed out after {timeout_seconds} second(s)"
        )

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


def _can_reuse_previous_document(
    previous: ArmoryIndex,
    previous_document: ChunkedDocument | None,
    *,
    strategy: ChunkStrategy,
    rel: str,
    content_hash: str | None,
) -> bool:
    return (
        previous.strategy == strategy
        and content_hash is not None
        and previous._file_hashes.get(rel) == content_hash
        and previous_document is not None
    )


def _report_index_progress(
    progress: IndexProgress | None,
    event: str,
    message: str,
) -> None:
    if progress is not None:
        progress(event, message)


def _unindexable_index_reason(
    file_path: Path,
    *,
    timed_out: bool,
    timeout_seconds: int,
) -> str:
    if timed_out:
        return f"document conversion timed out after {timeout_seconds} second(s)"
    return _unindexable_reason(file_path)


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


def _cache_signing_key() -> bytes | None:
    raw_path = os.environ.get(_CACHE_SIGNING_KEY_PATH_ENV, "").strip()
    key_path = (
        Path(raw_path).expanduser() if raw_path else user_config_dir() / _CACHE_SIGNING_KEY_FILE
    )
    try:
        key_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        key_path.parent.chmod(0o700)
        if key_path.is_file():
            key_path.chmod(0o600)
            raw_key = key_path.read_text(encoding="utf-8").strip()
            key = bytes.fromhex(raw_key)
            if len(key) < 32:
                raise ValueError("rag cache signing key is too short")
            return key
        key = secrets.token_bytes(32)
        _write_cache_signing_key(key_path, key)
        return key
    except (OSError, ValueError):
        return None


def _write_cache_signing_key(key_path: Path, key: bytes) -> None:
    fd = os.open(str(key_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.fchmod(fd, 0o600)
    except Exception:
        os.close(fd)
        raise
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        file.write(f"{key.hex()}\n")


def _index_signature_payload(data: Mapping[str, object]) -> bytes:
    signable_keys = (
        "version",
        "chunk_size",
        "overlap",
        "strategy",
        "file_hashes",
        "documents_digest",
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


def _coerce_embedding_row(raw_row: object) -> list[float] | None:
    if not isinstance(raw_row, list):
        return None
    typed_row: list[float] = []
    for raw_value in cast("list[object]", raw_row):
        value = _coerce_embedding_value(raw_value)
        if value is None:
            return None
        typed_row.append(value)
    return typed_row


def _coerce_embedding_value(raw_value: object) -> float | None:
    try:
        value = float(raw_value) if isinstance(raw_value, int | float) else float(str(raw_value))
    except (OverflowError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _coerce_embedding_rows(raw_embeddings: object) -> list[list[float]] | None:
    if not isinstance(raw_embeddings, list):
        return None
    typed: list[list[float]] = []
    for raw_row in cast("list[object]", raw_embeddings):
        typed_row = _coerce_embedding_row(raw_row)
        if typed_row is None:
            return None
        typed.append(typed_row)
    return typed


def _string_field(data: Mapping[str, object], key: str) -> str:
    value = data.get(key, "")
    return value if isinstance(value, str) else ""


def _int_field(data: Mapping[str, object], key: str) -> int:
    value = data.get(key, 0)
    return value if isinstance(value, int) else 0


def _read_index_data(index_path: Path) -> dict[str, object] | None:
    try:
        data: object = json.loads(index_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if is_string_mapping(data) else None


def _index_data_version(data: Mapping[str, object]) -> int | None:
    raw_version = data.get("version", 1)
    version = raw_version if isinstance(raw_version, int) else 1
    return version if version in _SUPPORTED_INDEX_VERSIONS else None


def _index_data_documents(data: Mapping[str, object]) -> list[object] | None:
    raw_documents = data.get("documents", [])
    return raw_documents if is_object_list(raw_documents) else None


def _load_index_data(index_path: Path) -> _LoadedIndexData | None:
    data = _read_index_data(index_path)
    if data is None:
        return None
    version = _index_data_version(data)
    if version is None:
        return None
    raw_documents = _index_data_documents(data)
    if raw_documents is None:
        return None
    if not _index_documents_signature_valid(data, raw_documents, version):
        return None
    return _LoadedIndexData(
        data=data,
        version=version,
        raw_documents=raw_documents,
    )


def _index_documents_signature_valid(
    data: Mapping[str, object],
    raw_documents: list[object],
    version: int,
) -> bool:
    raw_documents_digest = data.get("documents_digest")
    if version >= 7:
        return _signed_index_documents_valid(data, raw_documents_digest, raw_documents)
    return _legacy_index_documents_valid(raw_documents_digest, raw_documents, version)


def _signed_index_documents_valid(
    data: Mapping[str, object],
    raw_documents_digest: object,
    raw_documents: list[object],
) -> bool:
    return (
        isinstance(raw_documents_digest, str)
        and _documents_digest_matches(raw_documents_digest, raw_documents)
        and _index_signature_matches(data)
    )


def _documents_digest_matches(raw_documents_digest: str, raw_documents: list[object]) -> bool:
    return raw_documents_digest == _documents_digest(raw_documents)


def _legacy_index_documents_valid(
    raw_documents_digest: object,
    raw_documents: list[object],
    version: int,
) -> bool:
    if version < 4 or not isinstance(raw_documents_digest, str):
        return True
    return raw_documents_digest == _documents_digest(raw_documents)


def _parse_cached_chunk(raw_chunk: object, version: int) -> Chunk | None:
    if not is_string_mapping(raw_chunk):
        return None
    text = _string_field(raw_chunk, "text")
    if version < 8:
        text = _normalize_extracted_text(text)
    return Chunk(
        text=text,
        source=_string_field(raw_chunk, "source"),
        index=_int_field(raw_chunk, "index"),
        char_start=_int_field(raw_chunk, "char_start"),
        char_end=_int_field(raw_chunk, "char_end"),
        heading=_string_field(raw_chunk, "heading"),
        heading_level=_int_field(raw_chunk, "heading_level"),
    )


def _parse_cached_document(doc_data: object, version: int) -> ChunkedDocument | None:
    if not is_string_mapping(doc_data):
        return None
    raw_chunks = doc_data.get("chunks", [])
    if not is_object_list(raw_chunks):
        return None
    chunks = [
        chunk
        for raw_chunk in raw_chunks
        if (chunk := _parse_cached_chunk(raw_chunk, version)) is not None
    ]
    return ChunkedDocument(
        source=_string_field(doc_data, "source"),
        chunks=chunks,
        content_hash=_string_field(doc_data, "content_hash"),
    )


class ArmoryIndex:
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
        self._retriever_cache: dict[RetrieverCacheKey, object] = {}
        self.unindexable_files: dict[str, str] = {}  # rel_path -> reason

    @property
    def all_chunks(self) -> list[Chunk]:
        chunks: list[Chunk] = []
        for doc in self.documents:
            chunks.extend(doc.chunks)
        return chunks

    @property
    def retriever_backend_names(self) -> tuple[str, ...]:
        return tuple(
            sorted({type(retriever).__name__ for retriever in self._retriever_cache.values()})
        )

    @property
    def content_hash(self) -> str:
        hasher = hashlib.sha256()
        for doc in self.documents:
            hasher.update(doc.content_hash.encode())
            hasher.update(str(len(doc.chunks)).encode())
        return hasher.hexdigest()[:16]

    def _embedding_cache_path(self, model_name: str, cache_key: str | None = None) -> Path:
        slug = model_name.replace("/", "_")
        if cache_key is not None:
            digest = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()[:16]
            slug = f"{slug}_{digest}"
        return self.armory_path / ".hephaion" / f"embeddings_{self.content_hash}_{slug}.json"

    def _retriever_state_path(self, retriever_type: str) -> Path:
        return (
            self.armory_path
            / ".hephaion"
            / f"retriever_{self.content_hash}_{retriever_type.replace('/', '_')}.json"
        )

    def save_embeddings(
        self,
        embeddings: list[list[float]],
        model_name: str,
        *,
        cache_key: str | None = None,
    ) -> Path | None:
        if not embeddings:
            return None
        embed_path = self._embedding_cache_path(model_name, cache_key)
        embed_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "content_hash": self.content_hash,
            "model_name": model_name,
            "cache_key": cache_key or model_name,
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

    def load_embeddings(
        self,
        model_name: str,
        *,
        cache_key: str | None = None,
    ) -> list[list[float]] | None:
        embed_path = self._embedding_cache_path(model_name, cache_key)
        if not embed_path.is_file():
            return None
        data = _read_json_mapping(embed_path)
        if data is None or not self._embedding_cache_matches(
            data,
            model_name=model_name,
            cache_key=cache_key,
        ):
            return None
        raw_embeddings = data.get("embeddings")
        typed = _coerce_embedding_rows(raw_embeddings)
        if typed is None:
            return None
        _log.debug(
            "embeddings loaded from cache",
            extra={"fields": {"path": str(embed_path), "chunks": len(typed)}},
        )
        return typed

    def _embedding_cache_matches(
        self,
        data: Mapping[str, object],
        *,
        model_name: str,
        cache_key: str | None,
    ) -> bool:
        return (
            data.get("content_hash") == self.content_hash
            and data.get("model_name") == model_name
            and data.get("cache_key", model_name) == (cache_key or model_name)
            and data.get("chunk_count") == len(self.all_chunks)
        )

    def save_retriever_state(self, retriever_type: str, state: dict[str, object]) -> Path | None:
        state_path = self._retriever_state_path(retriever_type)
        data = {
            "content_hash": self.content_hash,
            "retriever_type": retriever_type,
            "state": state,
        }
        try:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        except (OSError, TypeError):
            return None
        _log.debug(
            "retriever state saved",
            extra={"fields": {"path": str(state_path), "type": retriever_type}},
        )
        return state_path

    def load_retriever_state(self, retriever_type: str) -> dict[str, object] | None:
        state_path = self._retriever_state_path(retriever_type)
        if not state_path.is_file():
            return None
        data = _read_json_mapping(state_path)
        if data is None or not self._retriever_state_cache_matches(data, retriever_type):
            return None
        raw_state = data.get("state")
        if not is_string_mapping(raw_state):
            return None
        _log.debug(
            "retriever state loaded",
            extra={"fields": {"path": str(state_path), "type": retriever_type}},
        )
        return raw_state

    def _retriever_state_cache_matches(
        self,
        data: Mapping[str, object],
        retriever_type: str,
    ) -> bool:
        return (
            data.get("content_hash") == self.content_hash
            and data.get("retriever_type") == retriever_type
        )

    @property
    def chunk_count(self) -> int:
        return sum(len(doc.chunks) for doc in self.documents)

    def build(self, *, progress: IndexProgress | None = None) -> None:
        self._reset_build_state()
        timer = Timer()
        rebuilt = 0
        with timer:
            for file_path in self._iter_source_files():
                rebuilt += self._index_source_file(file_path, progress=progress)
        _log.info(
            "index built",
            extra={
                "fields": {
                    "armory": str(self.armory_path),
                    "strategy": self.strategy.value,
                    "documents": len(self.documents),
                    "chunks": self.chunk_count,
                    "rebuilt_files": rebuilt,
                    "latency_ms": timer.ms,
                }
            },
        )

    def build_incremental(
        self,
        previous: ArmoryIndex,
        *,
        progress: IndexProgress | None = None,
    ) -> None:
        previous_documents = {document.source: document for document in previous.documents}
        self._reset_build_state()
        timer = Timer()
        stats = _IndexBuildStats()
        with timer:
            for file_path in self._iter_source_files():
                rel = str(file_path.relative_to(self.armory_path))
                content_hash = _file_hash(file_path)
                if content_hash is not None:
                    self._file_hashes[rel] = content_hash
                previous_document = previous_documents.get(rel)
                if self._reuse_previous_document(
                    previous,
                    previous_document,
                    rel=rel,
                    content_hash=content_hash,
                    progress=progress,
                ):
                    stats.reused += 1
                    continue
                stats.rebuilt += self._index_source_file(
                    file_path,
                    content_hash=content_hash,
                    progress=progress,
                )
        _log.info(
            "index built incrementally",
            extra={
                "fields": {
                    "armory": str(self.armory_path),
                    "strategy": self.strategy.value,
                    "documents": len(self.documents),
                    "chunks": self.chunk_count,
                    "reused_files": stats.reused,
                    "rebuilt_files": stats.rebuilt,
                    "latency_ms": timer.ms,
                }
            },
        )

    def _reuse_previous_document(
        self,
        previous: ArmoryIndex,
        previous_document: ChunkedDocument | None,
        *,
        rel: str,
        content_hash: str | None,
        progress: IndexProgress | None,
    ) -> bool:
        if not _can_reuse_previous_document(
            previous,
            previous_document,
            strategy=self.strategy,
            rel=rel,
            content_hash=content_hash,
        ):
            return False
        assert previous_document is not None
        self.documents.append(previous_document)
        if progress is not None:
            progress("reading", rel)
            progress("indexed", f"{rel} ({len(previous_document.chunks)} chunks, reused)")
        return True

    def _reset_build_state(self) -> None:
        self.documents = []
        self._file_hashes = {}
        self._retriever = None
        self._retriever_cache = {}
        self.unindexable_files = {}

    def _index_source_file(
        self,
        file_path: Path,
        *,
        content_hash: str | None = None,
        progress: IndexProgress | None = None,
    ) -> int:
        rel = str(file_path.relative_to(self.armory_path))
        _report_index_progress(progress, "reading", rel)
        self._record_source_file_hash(rel, file_path, content_hash)

        timeout_seconds = _file_timeout_seconds()
        doc, timed_out = _chunk_file_with_timeout(
            file_path,
            self.armory_path,
            strategy=self.strategy,
            timeout_seconds=timeout_seconds,
        )
        if doc is not None and doc.chunks:
            self._add_indexed_document(rel, doc, progress)
        else:
            self._record_unindexable_source(
                file_path,
                rel=rel,
                timed_out=timed_out,
                timeout_seconds=timeout_seconds,
                progress=progress,
            )
        return 1

    def _record_source_file_hash(
        self,
        rel: str,
        file_path: Path,
        content_hash: str | None,
    ) -> None:
        content_hash = content_hash if content_hash is not None else _file_hash(file_path)
        if content_hash is not None:
            self._file_hashes[rel] = content_hash

    def _add_indexed_document(
        self,
        rel: str,
        document: ChunkedDocument,
        progress: IndexProgress | None,
    ) -> None:
        self.documents.append(document)
        _report_index_progress(progress, "indexed", f"{rel} ({len(document.chunks)} chunks)")

    def _record_unindexable_source(
        self,
        file_path: Path,
        *,
        rel: str,
        timed_out: bool,
        timeout_seconds: int,
        progress: IndexProgress | None,
    ) -> None:
        if _is_text_file(file_path):
            return
        reason = _unindexable_index_reason(
            file_path,
            timed_out=timed_out,
            timeout_seconds=timeout_seconds,
        )
        self.unindexable_files[rel] = reason
        _report_index_progress(progress, "skipped", f"{rel}: {reason}")

    def save(self) -> Path:
        index_path = self.armory_path / ".hephaion" / _INDEX_FILE
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

    def load(self, *, allow_stale: bool = False) -> bool:
        index_path = self.armory_path / ".hephaion" / _INDEX_FILE
        if not index_path.is_file():
            return False

        loaded = _load_index_data(index_path)
        if loaded is None:
            return False
        self._reset_build_state()
        self._restore_loaded_index(loaded)

        if not self._loaded_cache_is_usable(loaded, allow_stale=allow_stale):
            return False
        self._rebuild_unindexable_files()
        return True

    def _loaded_cache_is_usable(
        self,
        loaded: _LoadedIndexData,
        *,
        allow_stale: bool,
    ) -> bool:
        return self._cached_file_hashes_are_usable(
            allow_stale=allow_stale,
        ) and self._cached_documents_are_usable(
            allow_stale=allow_stale,
            version=loaded.version,
        )

    def _restore_loaded_index(self, loaded: _LoadedIndexData) -> None:
        self._restore_cached_strategy(loaded.data, loaded.version)
        self._restore_cached_file_hashes(loaded.data)
        self._restore_cached_documents(loaded.raw_documents, loaded.version)

    def _restore_cached_strategy(self, data: Mapping[str, object], version: int) -> None:
        if version < 2 or "strategy" not in data:
            return
        raw_strategy = data["strategy"]
        if isinstance(raw_strategy, str):
            with contextlib.suppress(ValueError):
                self.strategy = ChunkStrategy(raw_strategy)

    def _restore_cached_file_hashes(self, data: Mapping[str, object]) -> None:
        file_hashes_raw = data.get("file_hashes", {})
        if is_string_mapping(file_hashes_raw):
            self._file_hashes = {key: str(value) for key, value in file_hashes_raw.items()}

    def _restore_cached_documents(self, raw_documents: list[object], version: int) -> None:
        for doc_data in raw_documents:
            doc = _parse_cached_document(doc_data, version)
            if doc is None:
                continue
            self.documents.append(doc)
            if doc.content_hash and doc.source not in self._file_hashes:
                self._file_hashes[doc.source] = doc.content_hash

    def _cached_file_hashes_are_usable(
        self,
        *,
        allow_stale: bool,
    ) -> bool:
        if self._file_hashes_match_material_files():
            return True
        _log.warning(
            "rag index cache does not match material files",
            extra={"fields": {"armory": str(self.armory_path)}},
        )
        if allow_stale:
            return True
        self._clear_loaded_cache()
        return False

    def _cached_documents_are_usable(
        self,
        *,
        allow_stale: bool,
        version: int,
    ) -> bool:
        if self._documents_match_material_sources(
            allow_binary_cache=version >= 7,
            trust_text_cache=version >= 7,
        ):
            return True
        _log.warning(
            "rag index cache chunks do not match material files",
            extra={"fields": {"armory": str(self.armory_path)}},
        )
        if allow_stale and version >= 7:
            return True
        self._clear_loaded_cache()
        return False

    def _clear_loaded_cache(self) -> None:
        self.documents = []
        self._file_hashes = {}

    def is_stale(self) -> bool:
        if not self._file_hashes:
            return True
        return self._source_files_changed()

    def _source_files_changed(self) -> bool:
        indexed_sources = {doc.source for doc in self.documents}
        source_count = 0

        for file_path in self._iter_source_files():
            source_count += 1
            if self._source_file_makes_index_stale(file_path, indexed_sources):
                return True
        return len(self._file_hashes) != source_count

    def _iter_source_files(self) -> Iterator[Path]:
        for file_path in iter_source_files(self.armory_path):
            if _resolved_path_within_materials(file_path, self.armory_path) is None:
                continue
            yield file_path

    def _source_file_state(self, file_path: Path) -> _SourceFileState | None:
        content_hash = _file_hash(file_path)
        if content_hash is None:
            return None
        return _SourceFileState(
            rel=str(file_path.relative_to(self.armory_path)),
            path=file_path,
            content_hash=content_hash,
        )

    def _source_file_makes_index_stale(
        self,
        file_path: Path,
        indexed_sources: set[str],
    ) -> bool:
        source_state = self._source_file_state(file_path)
        if source_state is None:
            return True
        if source_state.rel not in self._file_hashes:
            return True
        if source_state.content_hash != self._file_hashes.get(source_state.rel):
            return True
        return self._convertible_binary_missing_from_index(source_state, indexed_sources)

    def _convertible_binary_missing_from_index(
        self,
        source_state: _SourceFileState,
        indexed_sources: set[str],
    ) -> bool:
        return (
            _can_convert_binary_file(source_state.path)
            and _is_docling_file(source_state.path)
            and source_state.rel not in indexed_sources
        )

    def _documents_match_material_sources(
        self,
        *,
        allow_binary_cache: bool,
        trust_text_cache: bool,
    ) -> bool:
        for document in self.documents:
            if not self._document_matches_material_source(
                document,
                allow_binary_cache=allow_binary_cache,
                trust_text_cache=trust_text_cache,
            ):
                return False
        return True

    def _document_matches_material_source(
        self,
        document: ChunkedDocument,
        *,
        allow_binary_cache: bool,
        trust_text_cache: bool,
    ) -> bool:
        source_match = self._material_source_match(document)
        if source_match is None:
            return False
        if _is_text_file(source_match.path):
            return self._text_document_matches_source(
                document,
                source_match.path,
                trust_text_cache=trust_text_cache,
            )
        return self._binary_document_matches_source(
            document,
            source_match.content_hash,
            allow_binary_cache=allow_binary_cache,
        )

    def _material_source_match(
        self,
        document: ChunkedDocument,
    ) -> _MaterialSourceMatch | None:
        resolved_path = self._resolved_document_source_path(document)
        if resolved_path is None or not resolved_path.is_file():
            return None
        material_hash = _file_hash(resolved_path)
        if material_hash is None or not self._document_hash_matches_cache(document, material_hash):
            return None
        return _MaterialSourceMatch(path=resolved_path, content_hash=material_hash)

    def _resolved_document_source_path(self, document: ChunkedDocument) -> Path | None:
        if not document.source:
            return None
        source_path = self.armory_path / document.source
        return _resolved_path_within_materials(source_path, self.armory_path)

    def _document_hash_matches_cache(
        self,
        document: ChunkedDocument,
        material_hash: str,
    ) -> bool:
        return self._file_hashes.get(document.source) == material_hash

    def _text_document_matches_source(
        self,
        document: ChunkedDocument,
        resolved_path: Path,
        *,
        trust_text_cache: bool,
    ) -> bool:
        if trust_text_cache:
            return True
        source_text = _read_normalized_source_text(resolved_path)
        if source_text is None:
            return False
        if not _document_text_hash_matches(document, source_text):
            return False
        return _document_chunks_match_source_text(document, source_text)

    @staticmethod
    def _binary_document_matches_source(
        document: ChunkedDocument,
        material_hash: str,
        *,
        allow_binary_cache: bool,
    ) -> bool:
        if document.content_hash and document.content_hash != material_hash:
            return False
        return allow_binary_cache or not document.chunks

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
        indexed_sources = {doc.source for doc in self.documents}
        self.unindexable_files = {}
        for file_path in self._iter_source_files():
            rel = str(file_path.relative_to(self.armory_path))
            if rel not in indexed_sources and not _is_text_file(file_path):
                self.unindexable_files[rel] = _unindexable_reason(file_path)


def _read_normalized_source_text(path: Path) -> str | None:
    try:
        return _normalize_extracted_text(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, OSError):
        return None


def _document_text_hash_matches(document: ChunkedDocument, source_text: str) -> bool:
    text_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()[:16]
    return not document.content_hash or document.content_hash == text_hash


def _document_chunks_match_source_text(document: ChunkedDocument, source_text: str) -> bool:
    return all(
        chunk.source == document.source and _normalized_text_contains(source_text, chunk.text)
        for chunk in document.chunks
    )


def iter_source_files(armory_path: Path) -> Iterator[Path]:
    yield from iter_material_files(armory_path)


def scan_unindexable_files(armory_path: Path) -> dict[str, str]:
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
    previous: ArmoryIndex | None = None,
) -> ArmoryIndex:
    previous_loaded = previous is not None
    if previous is None:
        previous = ArmoryIndex(armory_path, strategy=strategy)
        previous_loaded = previous.load(allow_stale=True)
    index = ArmoryIndex(armory_path, strategy=strategy)
    if previous_loaded:
        assert previous is not None
        index.build_incremental(previous, progress=progress)
    else:
        index.build(progress=progress)
    if progress is not None:
        progress("writing", str(index.armory_path / ".hephaion" / _INDEX_FILE))
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
    index = ArmoryIndex(armory_path, strategy=strategy)
    loaded = index.load(allow_stale=True)
    if _can_use_loaded_index(index, loaded=loaded, strategy=strategy):
        if progress is not None:
            index_path = armory_path / ".hephaion" / _INDEX_FILE
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
    return build_index(
        armory_path,
        strategy=strategy,
        progress=progress,
        previous=index if loaded else None,
    )


def _can_use_loaded_index(
    index: ArmoryIndex,
    *,
    loaded: bool,
    strategy: ChunkStrategy,
) -> bool:
    return loaded and index.strategy == strategy and not index.is_stale()
