"""Optional dependency adapters for RAG retrieval backends."""

from __future__ import annotations

from typing import Protocol, cast

try:
    import bm25s as _imported_bm25s  # type: ignore[import-untyped]
except ImportError:
    _imported_bm25s = None

try:
    from sklearn.feature_extraction.text import (
        TfidfVectorizer as _ImportedSklearnTfidfVectorizer,  # type: ignore[import-untyped]
    )

    _has_sklearn = True
except ImportError:
    _has_sklearn = False
    _ImportedSklearnTfidfVectorizer = None

try:
    from sentence_transformers import (
        CrossEncoder as _ImportedCrossEncoder,  # type: ignore[import-untyped]
    )
    from sentence_transformers import (
        SentenceTransformer as _ImportedSentenceTransformer,  # type: ignore[import-untyped]
    )
except ImportError:
    _ImportedCrossEncoder = None
    _ImportedSentenceTransformer = None


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


class Bm25Factory(Protocol):
    def __call__(self) -> Bm25Protocol: ...


HAS_SKLEARN = _has_sklearn

SKLEARN_TFIDF_VECTORIZER: SklearnVectorizerFactory | None = (
    None
    if _ImportedSklearnTfidfVectorizer is None
    else cast("SklearnVectorizerFactory", _ImportedSklearnTfidfVectorizer)
)

CROSS_ENCODER: CrossEncoderFactory | None = (
    None if _ImportedCrossEncoder is None else cast("CrossEncoderFactory", _ImportedCrossEncoder)
)
SENTENCE_TRANSFORMER: SentenceTransformerFactory | None = (
    None
    if _ImportedSentenceTransformer is None
    else cast("SentenceTransformerFactory", _ImportedSentenceTransformer)
)
BM25_CLASS: Bm25Factory | None = (
    None if _imported_bm25s is None else cast("Bm25Factory", _imported_bm25s.BM25)
)


def sentence_transformers_available() -> bool:
    """Return True when dense retrieval dependencies are importable."""
    return SENTENCE_TRANSFORMER is not None
