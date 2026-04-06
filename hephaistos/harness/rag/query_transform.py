"""Query transformation strategies for improved RAG retrieval.

Transforms user queries into alternative forms to improve recall and
precision before passing them to the retriever.  Three strategies are
provided:

- **HyDE** (Hypothetical Document Embeddings): generates a hypothetical
  answer to the query using an LLM, then uses that answer (which
  lexically resembles real documents) for retrieval.
- **Multi-Query**: asks an LLM to produce multiple reformulations of the
  query, retrieves for each, and merges the results with Reciprocal Rank
  Fusion.
- **Query Expansion**: extracts keywords from the query and expands them
  with related terms (using NLTK WordNet when available, otherwise a
  simple heuristic expansion).  No LLM call is required.

All transformers implement the ``QueryTransformerProtocol`` so they can
be plugged into the retrieval pipeline interchangeably.  The top-level
``transform_query()`` function applies a chain of transformers and
returns the expanded set of query strings.

LLM-based transformers (HyDE, Multi-Query) require a *prompt function* —
a ``Callable[[str], str]`` that sends a prompt to the model and returns
the text response.  This keeps the RAG layer decoupled from the chat
engine.  When no prompt function is available these transformers degrade
gracefully to identity (returning the original query unchanged).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from enum import Enum
from typing import Protocol, runtime_checkable

from hephaistos.logging import get_logger

_log = get_logger("rag.query_transform")


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


class TransformStrategy(Enum):
    """Selects which query transformation strategy to apply."""

    IDENTITY = "identity"        # no transformation (passthrough)
    HYDE = "hyde"                # Hypothetical Document Embeddings
    MULTI_QUERY = "multi_query"  # multi-query reformulation
    EXPANSION = "expansion"      # keyword expansion (no LLM needed)


@runtime_checkable
class QueryTransformerProtocol(Protocol):
    """Minimal interface every query transformer must implement."""

    def transform(self, query: str) -> list[str]:
        """Return one or more transformed query strings.

        The returned list always contains at least one string.  The
        original query may or may not be included depending on the
        strategy.
        """
        ...


#: Type alias for the LLM prompt function used by HyDE and Multi-Query.
#: Must accept a prompt string and return the model's text response.
PromptFn = Callable[[str], str]


# ---------------------------------------------------------------------------
# Identity transformer (passthrough — always available)
# ---------------------------------------------------------------------------


class IdentityTransformer:
    """Returns the original query unchanged.

    Useful as a no-op placeholder or the default when no transformation
    is requested.
    """

    def transform(self, query: str) -> list[str]:
        return [query]


# ---------------------------------------------------------------------------
# Query expansion (no LLM — keyword-based)
# ---------------------------------------------------------------------------


_WORD_RE = re.compile(r"[a-zA-Z]{3,}")

# Common domain-agnostic expansion heuristics
_EXPANSION_SUFFIXES = [
    "tutorial",
    "guide",
    "example",
    "explanation",
    "overview",
    "introduction",
    "definition",
    "concept",
]

# Simple synonym map for common query terms (no external deps needed)
_SYNONYM_MAP: dict[str, list[str]] = {
    "learn": ["train", "study", "understand", "education"],
    "create": ["build", "make", "generate", "construct", "develop"],
    "use": ["utilize", "apply", "employ", "usage"],
    "find": ["search", "locate", "discover", "identify"],
    "change": ["modify", "update", "alter", "transform", "edit"],
    "remove": ["delete", "erase", "clear", "eliminate"],
    "start": ["begin", "initiate", "launch", "run"],
    "stop": ["halt", "terminate", "end", "quit"],
    "error": ["bug", "issue", "problem", "fault", "exception"],
    "speed": ["performance", "fast", "optimization", "efficiency"],
    "connect": ["link", "join", "attach", "bind", "network"],
    "data": ["information", "records", "dataset", "storage"],
    "system": ["framework", "platform", "architecture", "infrastructure"],
    "method": ["function", "procedure", "approach", "technique", "algorithm"],
    "test": ["verify", "validate", "check", "assert"],
    "deploy": ["release", "publish", "ship", "install"],
    "configure": ["setup", "setting", "customize", "preference"],
    "analyze": ["examine", "inspect", "evaluate", "assess"],
    "compare": ["contrast", "difference", "versus", "evaluation"],
    "install": ["setup", "add", "download", "dependency"],
}


def _expand_with_wordnet(word: str) -> list[str]:
    """Try to expand a word using NLTK WordNet.  Returns empty list on failure."""
    try:
        from nltk.corpus import wordnet  # type: ignore[import-untyped]

        synsets = wordnet.synsets(word)
        lemmas: set[str] = set()
        for syn in synsets[:3]:  # limit to top synsets
            for lemma in syn.lemmas()[:3]:  # limit lemmas per synset
                name = lemma.name().replace("_", " ").lower()
                if name != word.lower() and len(name) > 2:
                    lemmas.add(name)
        return list(lemmas)[:5]  # cap expansions
    except ImportError:
        return []
    except Exception:
        # WordNet data may not be downloaded
        return []


class QueryExpander:
    """Keyword-based query expansion without LLM calls.

    Extracts content words from the query, looks up synonyms via
    NLTK WordNet (when available) and a built-in synonym map, then
    constructs expanded query strings combining the original with
    additional terms.

    Produces exactly two query strings:

    1. The original query (preserved for exact-match retrieval).
    2. An expanded query with synonyms/related terms appended.
    """

    def __init__(self, *, use_wordnet: bool = True) -> None:
        self._use_wordnet = use_wordnet

    def transform(self, query: str) -> list[str]:
        """Expand the query with related terms."""
        words = _WORD_RE.findall(query.lower())
        if not words:
            return [query]

        expansions: set[str] = set()
        for word in words:
            # Built-in synonym map
            if word in _SYNONYM_MAP:
                expansions.update(_SYNONYM_MAP[word][:3])

            # WordNet expansion (optional)
            if self._use_wordnet:
                wn_synonyms = _expand_with_wordnet(word)
                expansions.update(wn_synonyms[:3])

        if not expansions:
            return [query]

        # Build the expanded query: original + top expansion terms
        expanded_terms = list(expansions)[:8]  # cap to avoid query bloat
        expanded_query = f"{query} {' '.join(expanded_terms)}"

        _log.debug("query expanded", extra={"fields": {
            "original": query[:80],
            "expansions": expanded_terms,
        }})

        return [query, expanded_query]


# ---------------------------------------------------------------------------
# HyDE — Hypothetical Document Embeddings (requires LLM)
# ---------------------------------------------------------------------------


_HYDE_SYSTEM_PROMPT = (
    "You are a knowledgeable assistant.  Write a detailed, informative answer "
    "to the following question.  Use technical language and specific details "
    "as if you were writing a textbook passage or documentation section.  "
    "Do not prefix your answer with any commentary — just write the passage."
)


class HyDETransformer:
    """Hypothetical Document Embeddings transformer.

    Uses an LLM to generate a hypothetical answer to the user's query.
    The generated passage (which lexically resembles real documents in the
    corpus) is then used for retrieval instead of the raw query, typically
    yielding better similarity matches.

    Returns exactly one query string: the hypothetical document.  The
    original query is also included so exact-match retrieval still works.
    """

    def __init__(self, prompt_fn: PromptFn | None = None) -> None:
        self._prompt_fn = prompt_fn

    def transform(self, query: str) -> list[str]:
        """Generate a hypothetical document and return it alongside the original query."""
        if self._prompt_fn is None:
            _log.debug("HyDE: no prompt function, returning original query")
            return [query]

        prompt = f"{_HYDE_SYSTEM_PROMPT}\n\nQuestion: {query}"
        try:
            hypothetical_doc = self._prompt_fn(prompt)
        except Exception as exc:
            _log.warning("HyDE generation failed, falling back to original query",
                         extra={"fields": {"error": str(exc)}})
            return [query]

        if not hypothetical_doc or not hypothetical_doc.strip():
            return [query]

        _log.debug("HyDE: generated hypothetical document", extra={"fields": {
            "query_len": len(query),
            "doc_len": len(hypothetical_doc),
        }})

        # Return both the hypothetical document (primary) and the original
        # query (for fallback keyword matching)
        return [hypothetical_doc.strip(), query]


# ---------------------------------------------------------------------------
# Multi-Query (requires LLM)
# ---------------------------------------------------------------------------


_MULTI_QUERY_PROMPT = (
    "You are an AI assistant that helps generate multiple versions of a "
    "search query to improve document retrieval.  Given the original query, "
    "generate exactly 3 alternative phrasings that capture the same "
    "information need from different angles.\n\n"
    "Output ONLY the alternative queries, one per line.  Do not number them, "
    "add prefixes, or include any other text."
)


class MultiQueryTransformer:
    """Multi-query reformulation transformer.

    Uses an LLM to generate multiple alternative phrasings of the user's
    query.  Each alternative is a different angle on the same information
    need.  The retriever is then called for each query and results are
    merged with Reciprocal Rank Fusion.

    Returns the original query plus the generated alternatives.
    """

    def __init__(
        self,
        prompt_fn: PromptFn | None = None,
        *,
        max_alternatives: int = 3,
    ) -> None:
        self._prompt_fn = prompt_fn
        self._max_alternatives = max_alternatives

    def transform(self, query: str) -> list[str]:
        """Generate alternative query phrasings."""
        if self._prompt_fn is None:
            _log.debug("multi-query: no prompt function, returning original query")
            return [query]

        prompt = f"{_MULTI_QUERY_PROMPT}\n\nOriginal query: {query}"
        try:
            response = self._prompt_fn(prompt)
        except Exception as exc:
            _log.warning("multi-query generation failed, falling back to original query",
                         extra={"fields": {"error": str(exc)}})
            return [query]

        if not response or not response.strip():
            return [query]

        # Parse the response into individual queries
        alternatives = [
            line.strip()
            for line in response.strip().splitlines()
            if line.strip()
        ]

        # Filter out lines that look like numbering or labels
        cleaned: list[str] = []
        for alt in alternatives:
            # Strip leading numbering like "1. " or "- " or "* "
            alt = re.sub(r'^[\d\-\*]+\.\s*', '', alt).strip()
            if alt and len(alt) > 5:  # skip very short fragments
                cleaned.append(alt)

        # Cap to max_alternatives
        cleaned = cleaned[:self._max_alternatives]

        if not cleaned:
            return [query]

        # Always include the original query
        queries = [query] + cleaned

        _log.debug("multi-query: generated alternatives", extra={"fields": {
            "original": query[:80],
            "alternatives": len(cleaned),
            "total_queries": len(queries),
        }})

        return queries


# ---------------------------------------------------------------------------
# Composite transformer (chains multiple transformers)
# ---------------------------------------------------------------------------


class CompositeTransformer:
    """Applies a chain of transformers sequentially.

    Each transformer receives the output of the previous one.  The final
    result is the union of all produced queries (deduplicated, order
    preserved).
    """

    def __init__(self, transformers: list[QueryTransformerProtocol]) -> None:
        self._transformers = transformers

    def transform(self, query: str) -> list[str]:
        """Apply all transformers in sequence, collecting unique queries."""
        seen: set[str] = set()
        result: list[str] = []

        # Start with the initial query from the first transformer
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
            current_queries = next_queries if next_queries else current_queries

        # Ensure at least the original query is present
        if query not in seen:
            result.insert(0, query)

        return result if result else [query]


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------


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
    if strategy == TransformStrategy.HYDE:
        return HyDETransformer(prompt_fn=prompt_fn)
    if strategy == TransformStrategy.MULTI_QUERY:
        return MultiQueryTransformer(prompt_fn=prompt_fn)
    # Fallback
    return IdentityTransformer()


# ---------------------------------------------------------------------------
# Convenience function (public API)
# ---------------------------------------------------------------------------


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

    _log.info("query transformed", extra={"fields": {
        "strategy": strategy.value,
        "original_len": len(query),
        "num_queries": len(result),
    }})

    return result
