"""Optional dependency adapters for RAG retrieval backends."""

from __future__ import annotations

import importlib
import importlib.util
from typing import Protocol, cast


class SklearnVectorizerProtocol(Protocol):
    def fit_transform(self, texts: list[str]) -> object: ...

    def transform(self, texts: list[str]) -> object: ...


class SklearnVectorizerFactory(Protocol):
    def __call__(
        self,
        *,
        stop_words: str,
        sublinear_tf: bool,
        max_features: int,
        token_pattern: str,
    ) -> SklearnVectorizerProtocol: ...


class SentenceTransformerProtocol(Protocol):
    def encode(
        self,
        texts: list[str],
        *,
        convert_to_numpy: bool,
        show_progress_bar: bool,
    ) -> object: ...


class SentenceTransformerFactory(Protocol):
    def __call__(self, model_name: str) -> SentenceTransformerProtocol: ...


class CrossEncoderProtocol(Protocol):
    def predict(self, pairs: list[tuple[str, str]]) -> object: ...


class CrossEncoderFactory(Protocol):
    def __call__(self, model_name: str) -> CrossEncoderProtocol: ...


class Bm25Protocol(Protocol):
    def index(self, _corpus_tokens: list[list[str]], *, show_progress: bool) -> object: ...

    def retrieve(
        self,
        query_tokens: list[list[str]],
        *,
        k: int,
        show_progress: bool,
    ) -> tuple[object, object]: ...

    def save(self, _path: object, **_kwargs: object) -> object: ...


class Bm25Factory(Protocol):
    def __call__(self) -> Bm25Protocol: ...

    def load(
        self,
        path: object,
        *,
        load_corpus: bool,
        mmap: bool,
    ) -> Bm25Protocol: ...


_UNSET = object()
_sentence_transformers_available: bool | None = None

HAS_SKLEARN: bool | object = _UNSET
SKLEARN_TFIDF_VECTORIZER: SklearnVectorizerFactory | None | object = _UNSET
CROSS_ENCODER: CrossEncoderFactory | None | object = _UNSET
SENTENCE_TRANSFORMER: SentenceTransformerFactory | None | object = _UNSET
BM25_CLASS: Bm25Factory | None | object = _UNSET


def _find_spec(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def sklearn_tfidf_vectorizer() -> SklearnVectorizerFactory | None:
    """Return the scikit-learn TF-IDF vectorizer, importing it only when needed."""
    global HAS_SKLEARN, SKLEARN_TFIDF_VECTORIZER  # noqa: PLW0603
    if SKLEARN_TFIDF_VECTORIZER is _UNSET:
        try:
            module = importlib.import_module("sklearn.feature_extraction.text")
            raw_vectorizer = getattr(module, "TfidfVectorizer", None)
        except ImportError:
            raw_vectorizer = None
        SKLEARN_TFIDF_VECTORIZER = (
            None if raw_vectorizer is None else cast("SklearnVectorizerFactory", raw_vectorizer)
        )
        HAS_SKLEARN = SKLEARN_TFIDF_VECTORIZER is not None
    if SKLEARN_TFIDF_VECTORIZER is None:
        return None
    return cast("SklearnVectorizerFactory", SKLEARN_TFIDF_VECTORIZER)


def has_sklearn() -> bool:
    """Return whether the sklearn backend is available."""
    if isinstance(HAS_SKLEARN, bool):
        return HAS_SKLEARN
    return sklearn_tfidf_vectorizer() is not None


def bm25_class() -> Bm25Factory | None:
    """Return the BM25 backend class, importing bm25s only when needed."""
    global BM25_CLASS  # noqa: PLW0603
    if BM25_CLASS is _UNSET:
        try:
            module = importlib.import_module("bm25s")
            raw_bm25 = getattr(module, "BM25", None)
        except ImportError:
            raw_bm25 = None
        BM25_CLASS = None if raw_bm25 is None else cast("Bm25Factory", raw_bm25)
    if BM25_CLASS is None:
        return None
    return cast("Bm25Factory", BM25_CLASS)


def sentence_transformer() -> SentenceTransformerFactory | None:
    """Return the sentence-transformers factory, importing the package lazily."""
    global SENTENCE_TRANSFORMER, _sentence_transformers_available  # noqa: PLW0603
    if SENTENCE_TRANSFORMER is _UNSET:
        try:
            module = importlib.import_module("sentence_transformers")
            raw_transformer = getattr(module, "SentenceTransformer", None)
        except ImportError:
            raw_transformer = None
        SENTENCE_TRANSFORMER = (
            None
            if raw_transformer is None
            else cast("SentenceTransformerFactory", raw_transformer)
        )
        _sentence_transformers_available = SENTENCE_TRANSFORMER is not None
    if SENTENCE_TRANSFORMER is None:
        return None
    return cast("SentenceTransformerFactory", SENTENCE_TRANSFORMER)


def cross_encoder() -> CrossEncoderFactory | None:
    """Return the cross-encoder factory, importing sentence-transformers lazily."""
    global CROSS_ENCODER, _sentence_transformers_available  # noqa: PLW0603
    if CROSS_ENCODER is _UNSET:
        try:
            module = importlib.import_module("sentence_transformers")
            raw_encoder = getattr(module, "CrossEncoder", None)
        except ImportError:
            raw_encoder = None
        CROSS_ENCODER = None if raw_encoder is None else cast("CrossEncoderFactory", raw_encoder)
        if raw_encoder is not None:
            _sentence_transformers_available = True
    if CROSS_ENCODER is None:
        return None
    return cast("CrossEncoderFactory", CROSS_ENCODER)


def sentence_transformers_available() -> bool:
    """Return True when dense retrieval dependencies are importable."""
    global _sentence_transformers_available  # noqa: PLW0603
    if SENTENCE_TRANSFORMER is not _UNSET:
        return SENTENCE_TRANSFORMER is not None
    if _sentence_transformers_available is None:
        _sentence_transformers_available = _find_spec("sentence_transformers")
    return _sentence_transformers_available
