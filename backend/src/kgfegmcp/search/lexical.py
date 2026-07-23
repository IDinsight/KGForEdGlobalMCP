"""This module builds and queries immutable package-local lexical description indexes.

This module creates one independent word index for the source descriptions in each
accepted graph package. Every indexed document retains the exact source
`~kgfegmcp.graph.models.StandardNode` instance and the deterministic normalized tokens
derived from its description.

Lexical search supports any-token matching, all-token matching, and contiguous
exact-phrase matching. Results are returned with deterministic token evidence and
integer coverage scores so the service layer can rank them without fuzzy, statistical,
semantic, or model-generated inference.

Only source descriptions are searchable through this index. Statement codes,
identifiers, grades, subjects, relationship data, raw properties, and source export
order are not treated as lexical text.

The index is package-local and immutable. This module does not select packages, apply
catalog routing, perform pagination, read files, validate packages, or merge lexical
namespaces across graph packages.
"""

# Future Library
from __future__ import annotations

# Standard Library
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

# Package Library
from kgfegmcp.catalog.models import CatalogPackageRuntime
from kgfegmcp.domain.identifiers import NodeId
from kgfegmcp.graph.models import GraphPackageIdentity, StandardNode
from kgfegmcp.search.models import (
    TextMatch,
    TextMatchMode,
    TextOperator,
    TokenTextMatch,
)
from kgfegmcp.search.normalizers import normalize_lexical_text


@dataclass(frozen=True, slots=True)
class LexicalDocument:
    """Retain one exact source node and its normalized description tokens."""

    node: StandardNode
    tokens: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LexicalCandidate:
    """Return deterministic package-local lexical candidate evidence."""

    matched_terms: tuple[str, ...]
    node: StandardNode
    phrase_matched: bool
    query_term_count: int
    score_value: int
    source_value: str


@dataclass(frozen=True, slots=True)
class LexicalIndex:
    """Own one immutable lexical index for exactly one accepted graph package."""

    documents_by_id: Mapping[NodeId, LexicalDocument]
    package_identity: GraphPackageIdentity
    posting_count: int
    postings_by_token: Mapping[str, tuple[LexicalDocument, ...]]

    @classmethod
    def from_runtime(cls, runtime: CatalogPackageRuntime) -> LexicalIndex:
        """Build a package-local description index from an accepted catalog runtime.

        Parameters
        ----------
        runtime
            Exact accepted package runtime whose source node instances are retained.

        Returns
        -------
        LexicalIndex
            Immutable package-local lexical index.
        """

        documents_by_id: dict[NodeId, LexicalDocument] = {}
        mutable_postings: dict[str, list[LexicalDocument]] = {}

        for node in runtime.loaded_package.item_nodes:
            if node.description is None:
                continue

            tokens = normalize_lexical_text(node.description)

            if not tokens:
                continue

            document = LexicalDocument(node=node, tokens=tokens)
            documents_by_id[node.node_id] = document

            for token in dict.fromkeys(tokens):
                if token not in mutable_postings:
                    mutable_postings[token] = []

                mutable_postings[token].append(document)

        postings_by_token = {
            token: tuple(documents)
            for token, documents in sorted(mutable_postings.items())
        }
        posting_count = sum(len(documents) for documents in postings_by_token.values())

        return cls(
            documents_by_id=MappingProxyType(documents_by_id),
            package_identity=runtime.catalog_package.package_identity,
            posting_count=posting_count,
            postings_by_token=MappingProxyType(postings_by_token),
        )

    @property
    def document_count(self) -> int:
        """Return the number of source descriptions retained in the index.

        Returns
        -------
        int
            Number of indexed source descriptions.
        """

        return len(self.documents_by_id)

    @property
    def unique_token_count(self) -> int:
        """Return the number of distinct normalized lexical tokens.

        Returns
        -------
        int
            Number of unique package-local token keys.
        """

        return len(self.postings_by_token)

    def candidates(
        self, *, match: TextMatch, query: str
    ) -> tuple[LexicalCandidate, ...]:
        """Return deterministic lexical candidates for one package-local query.

        Parameters
        ----------
        match
            Token or exact-phrase matching contract.
        query
            Raw caller-supplied lexical query.

        Returns
        -------
        tuple[LexicalCandidate, ...]
            Candidates in exact source tuple order before service-level ranking.
        """

        query_tokens = normalize_lexical_text(query)

        if match.match_mode is TextMatchMode.EXACT_PHRASE:
            return self._phrase_candidates(query_tokens)

        return self._token_candidates(match=match, query_tokens=query_tokens)

    def _candidate_node_ids(
        self, *, operator: TextOperator, query_terms: tuple[str, ...]
    ) -> frozenset[NodeId]:
        """Resolve token postings to an any-or-all candidate node set.

        Parameters
        ----------
        operator
            Any-or-all token matching behavior.
        query_terms
            Ordered distinct normalized query terms.

        Returns
        -------
        frozenset[NodeId]
            Exact package-local candidate node identifiers.
        """

        posting_sets = tuple(
            frozenset(
                document.node.node_id
                for document in (
                    self.postings_by_token[term]
                    if term in self.postings_by_token
                    else ()
                )
            )
            for term in query_terms
        )

        if not posting_sets:
            return frozenset()

        if operator is TextOperator.ALL:
            candidate_ids = set(posting_sets[0])

            for posting_set in posting_sets[1:]:
                candidate_ids.intersection_update(posting_set)

            return frozenset(candidate_ids)

        candidate_ids = set()

        for posting_set in posting_sets:
            candidate_ids.update(posting_set)

        return frozenset(candidate_ids)

    def _phrase_candidates(
        self, query_tokens: tuple[str, ...]
    ) -> tuple[LexicalCandidate, ...]:
        """Return documents containing the complete normalized token sequence.

        Parameters
        ----------
        query_tokens
            Ordered normalized query token sequence.

        Returns
        -------
        tuple[LexicalCandidate, ...]
            Exact phrase candidates in source tuple order.
        """

        distinct_terms = tuple(dict.fromkeys(query_tokens))
        candidate_ids = self._candidate_node_ids(
            operator=TextOperator.ALL, query_terms=distinct_terms
        )
        candidates: list[LexicalCandidate] = []

        for document in self.documents_by_id.values():
            if document.node.node_id not in candidate_ids:
                continue

            if not _contains_contiguous_tokens(
                document_tokens=document.tokens, query_tokens=query_tokens
            ):
                continue

            source_value = document.node.description

            if source_value is None:
                continue

            candidates.append(
                LexicalCandidate(
                    matched_terms=query_tokens,
                    node=document.node,
                    phrase_matched=True,
                    query_term_count=len(distinct_terms),
                    score_value=1_000_000,
                    source_value=source_value,
                )
            )

        return tuple(candidates)

    def _token_candidates(
        self, *, match: TokenTextMatch, query_tokens: tuple[str, ...]
    ) -> tuple[LexicalCandidate, ...]:
        """Return any-or-all token candidates with integer coverage scores.

        Parameters
        ----------
        match
            Token match contract and any-or-all operator.
        query_tokens
            Ordered normalized query tokens.

        Returns
        -------
        tuple[LexicalCandidate, ...]
            Token candidates in source tuple order before ranking.
        """

        query_terms = tuple(dict.fromkeys(query_tokens))
        candidate_ids = self._candidate_node_ids(
            operator=match.operator, query_terms=query_terms
        )
        candidates: list[LexicalCandidate] = []

        for document in self.documents_by_id.values():
            if document.node.node_id not in candidate_ids:
                continue

            document_terms = frozenset(document.tokens)
            matched_terms = tuple(
                term for term in query_terms if term in document_terms
            )

            if match.operator is TextOperator.ALL and len(matched_terms) != len(
                query_terms
            ):
                continue

            source_value = document.node.description

            if source_value is None:
                continue

            score_value = 1_000_000 * len(matched_terms) // len(query_terms)
            candidates.append(
                LexicalCandidate(
                    matched_terms=matched_terms,
                    node=document.node,
                    phrase_matched=False,
                    query_term_count=len(query_terms),
                    score_value=score_value,
                    source_value=source_value,
                )
            )

        return tuple(candidates)


def _contains_contiguous_tokens(
    *, document_tokens: tuple[str, ...], query_tokens: tuple[str, ...]
) -> bool:
    """Return whether one token sequence occurs contiguously inside another.

    Parameters
    ----------
    document_tokens
        Normalized source-description token sequence.
    query_tokens
        Normalized query token sequence.

    Returns
    -------
    bool
        ``True`` when the complete query sequence occurs without gaps or reordering.
    """

    if len(query_tokens) > len(document_tokens):
        return False

    final_start = len(document_tokens) - len(query_tokens)

    for start in range(final_start + 1):
        stop = start + len(query_tokens)

        if document_tokens[start:stop] == query_tokens:
            return True

    return False
