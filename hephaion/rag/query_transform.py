"""Query transformation strategies for RAG retrieval.

Transformers can expand queries deterministically, ask an optional LLM
prompt function for HyDE or multi-query rewrites, or split hybrid
retrieval into sparse and dense formulations. LLM-backed strategies
degrade to identity when no prompt function is available.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from enum import Enum
from typing import Protocol, cast, runtime_checkable

from hephaion.logging import get_logger

_log = get_logger("rag.query_transform")


class _WordNetProtocol(Protocol):
    def synsets(self, word: str) -> list[object]: ...


try:
    from nltk.corpus import wordnet as _imported_wordnet
except ImportError:
    _wordnet: _WordNetProtocol | None = None
else:
    _wordnet = cast("_WordNetProtocol", _imported_wordnet)


class TransformStrategy(Enum):
    IDENTITY = "identity"
    HYDE = "hyde"
    MULTI_QUERY = "multi_query"
    EXPANSION = "expansion"
    MODE_SPECIFIC = "mode_specific"


@runtime_checkable
class QueryTransformerProtocol(Protocol):
    def transform(self, query: str) -> list[str]:
        """Return one or more transformed query strings.

        The returned list always contains at least one string.  The
        original query may or may not be included depending on the
        strategy.
        """
        ...


@runtime_checkable
class ModeSpecificQueryTransformerProtocol(QueryTransformerProtocol, Protocol):
    def transform_sparse(self, query: str) -> list[str]: ...

    def transform_dense(self, query: str) -> list[str]: ...


PromptFn = Callable[[str], str]


class IdentityTransformer:
    def transform(self, query: str) -> list[str]:
        return [query]


_WORD_RE = re.compile(r"[a-zA-Z]{3,}")


def _expand_with_wordnet(word: str) -> list[str]:
    if _wordnet is None:
        return []
    try:
        synsets = _wordnet.synsets(word)
        lemmas: set[str] = set()
        for syn in synsets[:3]:
            lemma_getter = getattr(syn, "lemmas", None)
            if not callable(lemma_getter):
                continue
            raw_lemmas: object = lemma_getter()
            if not isinstance(raw_lemmas, list):
                continue
            typed_lemmas = cast("list[object]", raw_lemmas)
            for lemma in typed_lemmas[:3]:
                name_getter = getattr(lemma, "name", None)
                if not callable(name_getter):
                    continue
                name = str(name_getter()).replace("_", " ").lower()
                if name != word.lower() and len(name) > 2:
                    lemmas.add(name)
        return list(lemmas)[:5]  # cap expansions
    except Exception:
        return []


class QueryExpander:
    def __init__(self, *, use_wordnet: bool = True) -> None:
        self._use_wordnet = use_wordnet

    def transform(self, query: str) -> list[str]:
        words = _WORD_RE.findall(query.lower())
        if not words:
            return [query]

        expansions: set[str] = set()
        for word in words:
            if self._use_wordnet:
                wn_synonyms = _expand_with_wordnet(word)
                expansions.update(wn_synonyms[:3])

        if not expansions:
            return [query]
        expanded_terms = list(expansions)[:8]  # cap to avoid query bloat
        expanded_query = f"{query} {' '.join(expanded_terms)}"

        _log.debug(
            "query expanded",
            extra={
                "fields": {
                    "original": query[:80],
                    "expansions": expanded_terms,
                }
            },
        )

        return [query, expanded_query]


_MODE_SPECIFIC_PROMPT = (
    "Rewrite the search query for a hybrid retriever.\n"
    "Return exactly two lines:\n"
    "SPARSE: a compact keyword bag with synonyms, abbreviations, and domain terms\n"
    "DENSE: a fluent natural-language description of the same information need\n\n"
    "Do not add commentary or change the user's intent."
)


class ModeSpecificQueryPlanner:
    def __init__(self, prompt_fn: PromptFn | None = None) -> None:
        self._prompt_fn = prompt_fn

    def transform(self, query: str) -> list[str]:
        sparse_query, dense_query = self._planned_queries(query)
        return _dedupe_queries([query, sparse_query, dense_query])

    def transform_sparse(self, query: str) -> list[str]:
        sparse_query, _dense_query = self._planned_queries(query)
        return _dedupe_queries([query, sparse_query])

    def transform_dense(self, query: str) -> list[str]:
        _sparse_query, dense_query = self._planned_queries(query)
        return _dedupe_queries([query, dense_query])

    def _planned_queries(self, query: str) -> tuple[str, str]:
        if self._prompt_fn is None:
            return query, query
        prompt = f"{_MODE_SPECIFIC_PROMPT}\n\nOriginal query: {query}"
        try:
            response = self._prompt_fn(prompt)
        except Exception as exc:
            _log.warning(
                "mode-specific query planning failed, falling back to original query",
                extra={"fields": {"error": str(exc)}},
            )
            return query, query
        sparse_query = ""
        dense_query = ""
        for line in response.splitlines():
            label, separator, value = line.partition(":")
            if not separator:
                continue
            normalized_label = label.strip().lower()
            if normalized_label == "sparse":
                sparse_query = value.strip()
            elif normalized_label == "dense":
                dense_query = value.strip()
        return sparse_query or query, dense_query or query


def _dedupe_queries(queries: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for query in queries:
        normalized = " ".join(query.split())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


_HYDE_SYSTEM_PROMPT = (
    "You are a knowledgeable assistant.  Write a detailed, informative answer "
    "to the following question.  Use technical language and specific details "
    "as if you were writing a textbook passage or documentation section.  "
    "Do not prefix your answer with any commentary — just write the passage."
)


class HyDETransformer:
    def __init__(self, prompt_fn: PromptFn | None = None) -> None:
        self._prompt_fn = prompt_fn

    def transform(self, query: str) -> list[str]:
        if self._prompt_fn is None:
            _log.debug("HyDE: no prompt function, returning original query")
            return [query]

        prompt = f"{_HYDE_SYSTEM_PROMPT}\n\nQuestion: {query}"
        try:
            hypothetical_doc = self._prompt_fn(prompt)
        except Exception as exc:
            _log.warning(
                "HyDE generation failed, falling back to original query",
                extra={"fields": {"error": str(exc)}},
            )
            return [query]

        if not hypothetical_doc or not hypothetical_doc.strip():
            return [query]

        _log.debug(
            "HyDE: generated hypothetical document",
            extra={
                "fields": {
                    "query_len": len(query),
                    "doc_len": len(hypothetical_doc),
                }
            },
        )

        return [hypothetical_doc.strip(), query]


_MULTI_QUERY_PROMPT = (
    "You are an AI assistant that helps generate multiple versions of a "
    "search query to improve document retrieval.  Given the original query, "
    "generate exactly 3 alternative phrasings that capture the same "
    "information need from different angles.\n\n"
    "Output ONLY the alternative queries, one per line.  Do not number them, "
    "add prefixes, or include any other text."
)


class MultiQueryTransformer:
    def __init__(
        self,
        prompt_fn: PromptFn | None = None,
        *,
        max_alternatives: int = 3,
    ) -> None:
        self._prompt_fn = prompt_fn
        self._max_alternatives = max_alternatives

    def transform(self, query: str) -> list[str]:
        if self._prompt_fn is None:
            _log.debug("multi-query: no prompt function, returning original query")
            return [query]

        response = self._generate_response(query)
        if not response:
            return [query]

        cleaned = self._clean_alternatives(response)
        if not cleaned:
            return [query]
        queries = [query, *cleaned]
        self._log_generated_alternatives(query, cleaned, queries)
        return queries

    def _generate_response(self, query: str) -> str | None:
        if self._prompt_fn is None:
            return None
        prompt = f"{_MULTI_QUERY_PROMPT}\n\nOriginal query: {query}"
        try:
            response = self._prompt_fn(prompt)
        except Exception as exc:
            _log.warning(
                "multi-query generation failed, falling back to original query",
                extra={"fields": {"error": str(exc)}},
            )
            return None
        return response.strip() if response and response.strip() else None

    def _clean_alternatives(self, response: str) -> list[str]:
        alternatives = [line.strip() for line in response.splitlines() if line.strip()]
        return [
            cleaned
            for alternative in alternatives
            if len(cleaned := self._clean_alternative(alternative)) > 5
        ][: self._max_alternatives]

    @staticmethod
    def _clean_alternative(alternative: str) -> str:
        return re.sub(r"^[\d\-\*]+\.\s*", "", alternative).strip()

    @staticmethod
    def _log_generated_alternatives(
        query: str,
        cleaned: list[str],
        queries: list[str],
    ) -> None:
        _log.debug(
            "multi-query: generated alternatives",
            extra={
                "fields": {
                    "original": query[:80],
                    "alternatives": len(cleaned),
                    "total_queries": len(queries),
                }
            },
        )


class CompositeTransformer:
    def __init__(self, transformers: list[QueryTransformerProtocol]) -> None:
        self._transformers = transformers

    def transform(self, query: str) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        current_queries = [query]

        for transformer in self._transformers:
            next_queries: list[str] = []
            for q in current_queries:
                transformed = transformer.transform(q)
                for t in transformed:
                    if t not in seen:
                        seen.add(t)
                        next_queries.append(t)
                        result.append(t)
            current_queries = next_queries or current_queries
        if query not in seen:
            result.insert(0, query)

        return result or [query]


def create_transformer(
    strategy: TransformStrategy = TransformStrategy.IDENTITY,
    prompt_fn: PromptFn | None = None,
    *,
    use_wordnet: bool = True,
) -> QueryTransformerProtocol:
    """Create a query transformer for the given strategy.

    LLM-based strategies (HyDE, Multi-Query) degrade gracefully to
    identity when no *prompt_fn* is provided.
    """
    if strategy == TransformStrategy.IDENTITY:
        return IdentityTransformer()
    if strategy == TransformStrategy.EXPANSION:
        return QueryExpander(use_wordnet=use_wordnet)
    if strategy == TransformStrategy.MODE_SPECIFIC:
        return ModeSpecificQueryPlanner(prompt_fn=prompt_fn)
    if strategy == TransformStrategy.HYDE:
        return HyDETransformer(prompt_fn=prompt_fn)
    if strategy == TransformStrategy.MULTI_QUERY:
        return MultiQueryTransformer(prompt_fn=prompt_fn)
    return IdentityTransformer()


def transform_query(
    query: str,
    strategy: TransformStrategy = TransformStrategy.IDENTITY,
    prompt_fn: PromptFn | None = None,
) -> list[str]:
    """Transform a query using the specified strategy.

    Returns a list of query strings (at least one — the original).
    This is the main entry point for query transformation.
    """
    transformer = create_transformer(strategy, prompt_fn)
    result = transformer.transform(query)

    _log.info(
        "query transformed",
        extra={
            "fields": {
                "strategy": strategy.value,
                "original_len": len(query),
                "num_queries": len(result),
            }
        },
    )

    return result
