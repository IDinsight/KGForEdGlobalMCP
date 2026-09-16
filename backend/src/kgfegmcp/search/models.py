"""This module defines immutable contracts for deterministic package-scoped search.

This module contains the public data models used to request search, select exact or
federated package scopes, apply controlled filters, describe deterministic matches,
report capability warnings, paginate results, and expose index metadata.

The request models keep lexical, exact-code, and prefix-code behavior separate so a
caller cannot accidentally supply options that do not belong to the selected search
mode. Result models preserve the exact source node, graph-package identity, matched
fields, normalized terms, score explanation, facet evidence, code-scope evidence, and
code-parent derivation evidence for every hit.

Cursors are opaque immutable values whose private payload is created and validated by
the search service. Package identities and source records remain explicit so a
federated result never loses its package provenance.

These models describe contracts only. They do not build indexes, search graph packages,
access configuration, read files, validate packages, infer hierarchy, or perform
semantic matching.
"""

# Future Library
from __future__ import annotations

# Standard Library
import unicodedata

from enum import StrEnum
from typing import Annotated, Literal, TypeAlias

# Third Party Library
from pydantic import ConfigDict, Field, RootModel, StringConstraints, model_validator

# Package Library
from kgfegmcp.domain.enums import EpistemicStatus, GraphType, NormalizedStatementType
from kgfegmcp.domain.identifiers import FrameworkId, NodeId, Sha256Digest, SnapshotId
from kgfegmcp.graph.models import (
    GraphPackageIdentity,
    LearningComponentNode,
    StandardNode,
)
from kgfegmcp.schemas import FrozenSchema
from kgfegmcp.search.normalizers import (
    normalize_facet_value,
    normalize_lexical_text,
    normalize_nfkc,
)

CodeQueryText = Annotated[str, StringConstraints(max_length=256, min_length=1)]
FilterValue = Annotated[str, StringConstraints(max_length=128, min_length=1)]
TagQueryText = Annotated[str, StringConstraints(max_length=128, min_length=1)]
SearchQueryText = Annotated[str, StringConstraints(max_length=512, min_length=1)]


class SearchMode(StrEnum):
    """Identify one deterministic search mode."""

    CODE_EXACT = "code_exact"
    CODE_PREFIX = "code_prefix"
    TEXT = "text"


class LearningComponentSearchMode(StrEnum):
    """Identify one deterministic learning-component search mode."""

    SUPPORTED_CODE_EXACT = "learning_component_supported_code_exact"
    SUPPORTED_CODE_PREFIX = "learning_component_supported_code_prefix"
    TAG = "learning_component_tag"
    TEXT = "learning_component_text"


class SearchSelectionMode(StrEnum):
    """Identify exact-package or federated package selection."""

    EXACT = "exact"
    FEDERATED = "federated"


class TextMatchMode(StrEnum):
    """Identify token or contiguous exact-phrase lexical matching."""

    EXACT_PHRASE = "exact_phrase"
    TOKENS = "tokens"


class TextOperator(StrEnum):
    """Control whether any or all distinct query tokens must match."""

    ALL = "all"
    ANY = "any"


class SearchField(StrEnum):
    """Identify a source field that produced deterministic search evidence."""

    DESCRIPTION = "description"
    STATEMENT_CODE = "statement_code"
    SUPPORTED_STATEMENT_CODE = "supported_statement_code"
    TAG = "tag"


class SearchScoreAlgorithm(StrEnum):
    """Identify the versioned deterministic scoring rule used for one hit."""

    CODE_EXACT_V1 = "code_exact_v1"
    CODE_PREFIX_V1 = "code_prefix_v1"
    LEXICAL_TOKEN_COVERAGE_V1 = "lexical_token_coverage_v1"
    SUPPORTED_CODE_EXACT_V1 = "supported_code_exact_v1"
    SUPPORTED_CODE_PREFIX_V1 = "supported_code_prefix_v1"
    TAG_EXACT_V1 = "tag_exact_v1"


class SearchWarningCode(StrEnum):
    """Identify a deterministic package-level or hit-level search warning."""

    CODE_PREFIX_UNAVAILABLE = "code_prefix_unavailable"
    CODE_SEARCH_UNAVAILABLE = "code_search_unavailable"
    DERIVED_PARENT_CODE_MULTIPLE = "derived_parent_code_multiple"
    DERIVED_PARENT_CODE_NOT_FOUND = "derived_parent_code_not_found"
    MULTIPLE_CODE_MATCHES = "multiple_code_matches"
    PARTIAL_CODE_COVERAGE = "partial_code_coverage"
    TEXT_SEARCH_UNAVAILABLE = "text_search_unavailable"


class CodeParentDerivationStatus(StrEnum):
    """Identify the deterministic outcome of one configured parent-code derivation."""

    MATCHED_MULTIPLE = "matched_multiple"
    MATCHED_UNIQUE = "matched_unique"
    NOT_FOUND = "not_found"


class SearchCursor(RootModel[str]):
    """Carry an opaque immutable base64url pagination cursor."""

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def validate_cursor(self) -> SearchCursor:
        """Validate the encoded cursor surface without decoding its private payload.

        Returns
        -------
        SearchCursor
            The unchanged validated opaque cursor.

        Raises
        ------
        ValueError
            If the cursor is blank, oversized, or contains non-base64url characters.
        """

        value = self.root

        if not value or len(value) > 4_096:
            raise ValueError(
                "Search cursors must contain between 1 and 4096 characters."
            )

        if any(
            character
            not in ("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
            for character in value
        ):
            raise ValueError("Search cursors must use unpadded base64url characters.")

        return self


class ExactPackageSearchScope(FrozenSchema):
    """Select one exact or unique-current graph package through the catalog."""

    framework_id: FrameworkId
    graph_type: GraphType
    selection_mode: Literal[SearchSelectionMode.EXACT]
    snapshot_id: SnapshotId | None = None


class FederatedPackageSearchScope(FrozenSchema):
    """Select a deterministic subset of accepted package runtimes for aggregation."""

    framework_ids: tuple[FrameworkId, ...] = Field(default=(), max_length=64)
    graph_types: tuple[GraphType, ...] = Field(default=(), max_length=64)
    selection_mode: Literal[SearchSelectionMode.FEDERATED]
    snapshot_ids: tuple[SnapshotId, ...] = Field(default=(), max_length=64)

    @model_validator(mode="after")
    def validate_scope_uniqueness(self) -> FederatedPackageSearchScope:
        """Require every federated package-selection tuple to be duplicate-free.

        Returns
        -------
        FederatedPackageSearchScope
            The unchanged validated federated scope.

        Raises
        ------
        ValueError
            If a framework, graph type, or snapshot is repeated.
        """

        collections = (
            ("framework_ids", tuple(str(value) for value in self.framework_ids)),
            ("graph_types", tuple(value.value for value in self.graph_types)),
            ("snapshot_ids", tuple(str(value) for value in self.snapshot_ids)),
        )

        for field_name, values in collections:
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} must not contain duplicates.")

        return self


PackageSearchScope: TypeAlias = Annotated[
    ExactPackageSearchScope | FederatedPackageSearchScope,
    Field(discriminator="selection_mode"),
]


class SearchFilters(FrozenSchema):
    """Define package-local source and normalized facets applied to search hits."""

    include_groupings: bool
    local_grade_labels: tuple[FilterValue, ...] = Field(default=(), max_length=64)
    local_subjects: tuple[FilterValue, ...] = Field(default=(), max_length=64)
    normalized_grades: tuple[FilterValue, ...] = Field(default=(), max_length=64)
    normalized_statement_types: tuple[NormalizedStatementType, ...] = Field(
        default=(), max_length=64
    )
    normalized_subjects: tuple[FilterValue, ...] = Field(default=(), max_length=64)
    statement_types: tuple[FilterValue, ...] = Field(default=(), max_length=64)

    @model_validator(mode="after")
    def validate_filters(self) -> SearchFilters:
        """Reject duplicate, unsafe, or grouping-conflicting filter values.

        Returns
        -------
        SearchFilters
            The unchanged validated search filters.

        Raises
        ------
        ValueError
            If a filter contains duplicate or unsafe values, or conflicts with the
            grouping selection flag.
        """

        string_collections = (
            ("local_grade_labels", self.local_grade_labels),
            ("local_subjects", self.local_subjects),
            ("normalized_grades", self.normalized_grades),
            ("normalized_subjects", self.normalized_subjects),
            ("statement_types", self.statement_types),
        )

        for field_name, values in string_collections:
            normalized_values = tuple(normalize_facet_value(value) for value in values)

            if any(not value for value in normalized_values):
                raise ValueError(f"{field_name} must not contain blank values.")

            if len(normalized_values) != len(set(normalized_values)):
                raise ValueError(f"{field_name} must not contain duplicate values.")

            for value in values:
                _require_no_control_characters(value)

        normalized_statement_type_values = tuple(
            value.value for value in self.normalized_statement_types
        )

        if len(normalized_statement_type_values) != len(
            set(normalized_statement_type_values)
        ):
            raise ValueError(
                "normalized_statement_types must not contain duplicate values."
            )

        if (
            not self.include_groupings
            and NormalizedStatementType.STANDARD_GROUPING
            in self.normalized_statement_types
        ):
            raise ValueError(
                "include_groupings must be true when filtering for Standard Grouping."
            )

        return self


class TokenTextMatch(FrozenSchema):
    """Configure deterministic token matching with any-or-all semantics."""

    match_mode: Literal[TextMatchMode.TOKENS]
    operator: TextOperator


class ExactPhraseTextMatch(FrozenSchema):
    """Configure contiguous normalized phrase matching within one source field."""

    match_mode: Literal[TextMatchMode.EXACT_PHRASE]


TextMatch: TypeAlias = Annotated[
    TokenTextMatch | ExactPhraseTextMatch, Field(discriminator="match_mode")
]


class TextSearchQuery(FrozenSchema):
    """Request deterministic lexical search over package-local descriptions."""

    cursor: SearchCursor | None = None
    filters: SearchFilters
    limit: int = Field(default=25, ge=1, le=100)
    match: TextMatch
    mode: Literal[SearchMode.TEXT]
    query: SearchQueryText
    scope: PackageSearchScope

    @model_validator(mode="after")
    def validate_text_query(self) -> TextSearchQuery:
        """Require a safe lexical query containing at most 32 normalized tokens.

        Returns
        -------
        TextSearchQuery
            The unchanged validated lexical request.

        Raises
        ------
        ValueError
            If the query contains control characters, normalizes to no tokens, or
            exceeds the deterministic token bound.
        """

        _require_no_control_characters(self.query)
        tokens = normalize_lexical_text(self.query)
        distinct_tokens = tuple(dict.fromkeys(tokens))

        if not distinct_tokens:
            raise ValueError("Text search queries must contain a searchable token.")

        if len(tokens) > 32:
            raise ValueError("Text search queries may contain at most 32 tokens.")

        return self


class ExactCodeSearchQuery(FrozenSchema):
    """Request profile-governed exact code lookup within selected packages."""

    cursor: SearchCursor | None = None
    filters: SearchFilters
    limit: int = Field(default=25, ge=1, le=100)
    mode: Literal[SearchMode.CODE_EXACT]
    query: CodeQueryText
    scope: PackageSearchScope

    @model_validator(mode="after")
    def validate_code_query(self) -> ExactCodeSearchQuery:
        """Require a safe code query with at least one substantive Unicode character.

        Returns
        -------
        ExactCodeSearchQuery
            The unchanged validated exact-code request.

        Raises
        ------
        ValueError
            If the query contains controls or only whitespace and punctuation.
        """

        _require_code_query(self.query)
        return self


class PrefixCodeSearchQuery(FrozenSchema):
    """Request profile-governed delimiter-boundary code-prefix lookup."""

    cursor: SearchCursor | None = None
    filters: SearchFilters
    limit: int = Field(default=25, ge=1, le=100)
    mode: Literal[SearchMode.CODE_PREFIX]
    query: CodeQueryText
    scope: PackageSearchScope

    @model_validator(mode="after")
    def validate_code_query(self) -> PrefixCodeSearchQuery:
        """Require a safe prefix query with substantive Unicode content.

        Returns
        -------
        PrefixCodeSearchQuery
            The unchanged validated code-prefix request.

        Raises
        ------
        ValueError
            If the query contains controls or only whitespace and punctuation.
        """

        _require_code_query(self.query)
        return self


SearchQuery: TypeAlias = Annotated[
    ExactCodeSearchQuery | PrefixCodeSearchQuery | TextSearchQuery,
    Field(discriminator="mode"),
]


class LearningComponentTextSearchQuery(FrozenSchema):
    """Request deterministic lexical search over learning-component descriptions."""

    cursor: SearchCursor | None = None
    limit: int = Field(default=25, ge=1, le=100)
    match: TextMatch
    mode: Literal[LearningComponentSearchMode.TEXT]
    query: SearchQueryText
    scope: PackageSearchScope

    @model_validator(mode="after")
    def validate_query(self) -> LearningComponentTextSearchQuery:
        """Require one safe lexical query that normalizes to at least one token.

        Returns
        -------
        LearningComponentTextSearchQuery
            The unchanged validated lexical request.

        Raises
        ------
        ValueError
            If the query contains controls or normalizes to no tokens.
        """

        _require_no_control_characters(self.query)

        if not normalize_lexical_text(self.query):
            raise ValueError("Text search queries must contain searchable characters.")

        return self


class LearningComponentTagSearchQuery(FrozenSchema):
    """Request exact controlled-tag lookup over learning-component tags."""

    cursor: SearchCursor | None = None
    limit: int = Field(default=25, ge=1, le=100)
    mode: Literal[LearningComponentSearchMode.TAG]
    query: TagQueryText
    scope: PackageSearchScope

    @model_validator(mode="after")
    def validate_query(self) -> LearningComponentTagSearchQuery:
        """Require one safe tag query that normalizes to a non-blank facet key.

        Returns
        -------
        LearningComponentTagSearchQuery
            The unchanged validated tag request.

        Raises
        ------
        ValueError
            If the query contains controls or normalizes to a blank facet key.
        """

        _require_no_control_characters(self.query)

        if not normalize_facet_value(self.query):
            raise ValueError("Tag search queries must contain searchable characters.")

        return self


class LearningComponentSupportedCodeExactSearchQuery(FrozenSchema):
    """Request learning components supporting one exact standards statement code."""

    cursor: SearchCursor | None = None
    limit: int = Field(default=25, ge=1, le=100)
    mode: Literal[LearningComponentSearchMode.SUPPORTED_CODE_EXACT]
    query: CodeQueryText
    scope: PackageSearchScope

    @model_validator(mode="after")
    def validate_query(self) -> LearningComponentSupportedCodeExactSearchQuery:
        """Require one safe exact supported-code query.

        Returns
        -------
        LearningComponentSupportedCodeExactSearchQuery
            The unchanged validated exact supported-code request.

        Raises
        ------
        ValueError
            If the query contains controls or only whitespace and punctuation.
        """

        _require_code_query(self.query)
        return self


class LearningComponentSupportedCodePrefixSearchQuery(FrozenSchema):
    """Request learning components supporting a standards statement-code prefix."""

    cursor: SearchCursor | None = None
    limit: int = Field(default=25, ge=1, le=100)
    mode: Literal[LearningComponentSearchMode.SUPPORTED_CODE_PREFIX]
    query: CodeQueryText
    scope: PackageSearchScope

    @model_validator(mode="after")
    def validate_query(self) -> LearningComponentSupportedCodePrefixSearchQuery:
        """Require one safe supported-code prefix query.

        Returns
        -------
        LearningComponentSupportedCodePrefixSearchQuery
            The unchanged validated supported-code prefix request.

        Raises
        ------
        ValueError
            If the query contains controls or only whitespace and punctuation.
        """

        _require_code_query(self.query)
        return self


LearningComponentSearchQuery: TypeAlias = Annotated[
    LearningComponentSupportedCodeExactSearchQuery
    | LearningComponentSupportedCodePrefixSearchQuery
    | LearningComponentTagSearchQuery
    | LearningComponentTextSearchQuery,
    Field(discriminator="mode"),
]


class SearchMatchedField(FrozenSchema):
    """Record exact source-field evidence for one deterministic match."""

    field: SearchField
    matched_terms: tuple[str, ...] = Field(min_length=1)
    phrase_matched: bool
    source_value: str = Field(min_length=1)


class SearchScore(FrozenSchema):
    """Explain a deterministic integer score without model-derived relevance."""

    algorithm: SearchScoreAlgorithm
    matched_term_count: int = Field(ge=1)
    phrase_matched: bool
    query_term_count: int = Field(ge=1)
    value: int = Field(ge=1, le=1_000_000)

    @model_validator(mode="after")
    def validate_score_counts(self) -> SearchScore:
        """Require matched-term evidence to fit within the query-term count.

        Returns
        -------
        SearchScore
            The unchanged internally consistent deterministic score.

        Raises
        ------
        ValueError
            If matched-term evidence exceeds the number of distinct query terms or an
            exact phrase does not report complete term coverage.
        """

        if self.matched_term_count > self.query_term_count:
            raise ValueError("matched_term_count may not exceed query_term_count.")

        if self.phrase_matched and self.matched_term_count != self.query_term_count:
            raise ValueError(
                "Exact phrase scores must report complete query-term coverage."
            )

        return self


class SearchFacetEvidence(FrozenSchema):
    """Expose source and normalized package-local facets used for filtering."""

    local_subject: str | None
    node_grade_levels: tuple[str, ...]
    normalized_grades: tuple[str, ...]
    normalized_statement_type: NormalizedStatementType | None
    normalized_subjects: tuple[str, ...]
    resolved_local_grade_labels: tuple[str, ...]
    statement_type: str | None


class CodeScopeEvidence(FrozenSchema):
    """Expose one exact graph node that supplies configured code scope."""

    scope_node: StandardNode
    scope_statement_type: str = Field(min_length=1)


class CodeParentDerivationEvidence(FrozenSchema):
    """Expose one configured child-to-parent code transformation outcome."""

    child_code_type: str = Field(min_length=1)
    derived_code: str = Field(min_length=1)
    matched_parent_node_ids: tuple[NodeId, ...]
    normalized_derived_code: str = Field(min_length=1)
    parent_code_type: str = Field(min_length=1)
    status: CodeParentDerivationStatus


class CodeMatchEvidence(FrozenSchema):
    """Expose exact authored code, normalized key, scope, and parent evidence."""

    authored_code: str = Field(min_length=1)
    code_type: str = Field(min_length=1)
    normalized_code: str = Field(min_length=1)
    parent_derivations: tuple[CodeParentDerivationEvidence, ...]
    scopes: tuple[CodeScopeEvidence, ...]


class SearchWarning(FrozenSchema):
    """Describe one deterministic capability or data-evidence warning."""

    code: SearchWarningCode
    message: str = Field(min_length=1)
    node_id: NodeId | None = None
    package_identity: GraphPackageIdentity


class SearchHit(FrozenSchema):
    """Return one exact source node with package identity and search evidence."""

    code_match: CodeMatchEvidence | None = None
    epistemic_status: Literal[EpistemicStatus.RETRIEVAL_CANDIDATE]  # type: ignore[valid-type]
    facets: SearchFacetEvidence
    matched_fields: tuple[SearchMatchedField, ...] = Field(min_length=1)
    matched_terms: tuple[str, ...] = Field(min_length=1)
    node: StandardNode
    package_identity: GraphPackageIdentity
    retrieval_method: SearchMode
    score: SearchScore
    warnings: tuple[SearchWarning, ...] = ()

    @model_validator(mode="after")
    def validate_hit_mode(self) -> SearchHit:
        """Require code evidence only for code modes and lexical evidence for text.

        Returns
        -------
        SearchHit
            The unchanged internally consistent hit.

        Raises
        ------
        ValueError
            If retrieval mode and evidence fields disagree.
        """

        is_text = self.retrieval_method is SearchMode.TEXT

        if is_text == (self.code_match is not None):
            raise ValueError("Search hit code evidence does not match retrieval mode.")

        expected_field = (
            SearchField.DESCRIPTION if is_text else SearchField.STATEMENT_CODE
        )

        if any(field.field is not expected_field for field in self.matched_fields):
            raise ValueError("Search hit matched fields do not match retrieval mode.")

        return self


class SearchPage(FrozenSchema):
    """Return one immutable deterministic page of package-scoped search hits."""

    has_more: bool
    hits: tuple[SearchHit, ...]
    mode: SearchMode
    next_cursor: SearchCursor | None
    returned_count: int = Field(ge=0)
    warnings: tuple[SearchWarning, ...]

    @model_validator(mode="after")
    def validate_page(self) -> SearchPage:
        """Require page counts, modes, and continuation state to agree.

        Returns
        -------
        SearchPage
            The unchanged internally consistent search page.

        Raises
        ------
        ValueError
            If counts, hit modes, or cursor state disagree.
        """

        if self.returned_count != len(self.hits):
            raise ValueError("returned_count must equal the number of hits.")

        if any(hit.retrieval_method is not self.mode for hit in self.hits):
            raise ValueError("Every hit must use the page search mode.")

        if self.has_more != (self.next_cursor is not None):
            raise ValueError("has_more and next_cursor must agree.")

        return self


class SupportedStandardReference(FrozenSchema):
    """Report one standards item a learning component supports.

    Reported whether or not the standard carries a statement code, so a component
    bridging a coded and an uncoded standard is never flattened to one. Grade levels
    and description are projected from the standard; a component has no grade of its
    own, and an uncoded standard is otherwise only a bare identifier.
    """

    description: str
    grade_levels: tuple[str, ...] = ()
    node_id: NodeId
    statement_code: str | None = Field(default=None, min_length=1)
    support_confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class LearningComponentSearchHit(FrozenSchema):
    """Return one learning component with package identity and search evidence."""

    epistemic_status: Literal[EpistemicStatus.RETRIEVAL_CANDIDATE]  # type: ignore[valid-type]
    matched_codes: tuple[SupportedStandardReference, ...] = ()
    matched_fields: tuple[SearchMatchedField, ...] = Field(min_length=1)
    matched_terms: tuple[str, ...] = Field(min_length=1)
    node: LearningComponentNode
    package_identity: GraphPackageIdentity
    retrieval_method: LearningComponentSearchMode
    score: SearchScore
    supported_standards: tuple[SupportedStandardReference, ...]
    warnings: tuple[SearchWarning, ...] = ()

    @model_validator(mode="after")
    def validate_hit_mode(self) -> LearningComponentSearchHit:
        """Require matched-field and matched-code evidence to match retrieval mode.

        Returns
        -------
        LearningComponentSearchHit
            The unchanged internally consistent hit.

        Raises
        ------
        ValueError
            If retrieval mode and evidence fields disagree.
        """

        expected_fields = {
            LearningComponentSearchMode.SUPPORTED_CODE_EXACT: (
                SearchField.SUPPORTED_STATEMENT_CODE
            ),
            LearningComponentSearchMode.SUPPORTED_CODE_PREFIX: (
                SearchField.SUPPORTED_STATEMENT_CODE
            ),
            LearningComponentSearchMode.TAG: SearchField.TAG,
            LearningComponentSearchMode.TEXT: SearchField.DESCRIPTION,
        }
        expected_field = expected_fields[self.retrieval_method]

        if any(field.field is not expected_field for field in self.matched_fields):
            raise ValueError(
                "Learning component hit matched fields do not match retrieval mode."
            )

        is_supported_code = expected_field is SearchField.SUPPORTED_STATEMENT_CODE

        if is_supported_code != bool(self.matched_codes):
            raise ValueError(
                "Learning component hit matched codes do not match retrieval mode."
            )

        return self


class LearningComponentSearchPage(FrozenSchema):
    """Return one immutable deterministic page of learning-component search hits."""

    has_more: bool
    hits: tuple[LearningComponentSearchHit, ...]
    mode: LearningComponentSearchMode
    next_cursor: SearchCursor | None
    returned_count: int = Field(ge=0)
    warnings: tuple[SearchWarning, ...]

    @model_validator(mode="after")
    def validate_page(self) -> LearningComponentSearchPage:
        """Require page counts, modes, and continuation state to agree.

        Returns
        -------
        LearningComponentSearchPage
            The unchanged internally consistent search page.

        Raises
        ------
        ValueError
            If counts, hit modes, or cursor state disagree.
        """

        if self.returned_count != len(self.hits):
            raise ValueError("returned_count must equal the number of hits.")

        if any(hit.retrieval_method is not self.mode for hit in self.hits):
            raise ValueError("Every hit must use the page search mode.")

        if self.has_more != (self.next_cursor is not None):
            raise ValueError("has_more and next_cursor must agree.")

        return self


class PackageSearchIndexMetadata(FrozenSchema):
    """Describe one immutable package-local lexical and code index."""

    code_normalizer_version: str = Field(min_length=1)
    coded_node_count: int = Field(ge=0)
    cursor_version: int = Field(ge=1)
    learning_component_document_count: int = Field(ge=0)
    index_sha256: Sha256Digest
    lexical_document_count: int = Field(ge=0)
    lexical_normalizer_version: str = Field(min_length=1)
    lexical_posting_count: int = Field(ge=0)
    lexical_unique_token_count: int = Field(ge=0)
    normalized_code_key_count: int = Field(ge=0)
    package_identity: GraphPackageIdentity
    ranking_version: str = Field(min_length=1)
    tag_vocabulary_size: int = Field(ge=0)


class SearchIndexMetadata(FrozenSchema):
    """Describe the complete deterministic set of package-local search indexes."""

    cursor_version: int = Field(ge=1)
    index_set_sha256: Sha256Digest
    packages: tuple[PackageSearchIndexMetadata, ...] = Field(min_length=1)


def _require_code_query(value: str) -> None:
    """Require one safe code query with substantive Unicode content.

    Parameters
    ----------
    value
        Raw code query supplied by the caller.

    Raises
    ------
    ValueError
        If the query contains controls or only punctuation and whitespace.
    """

    _require_no_control_characters(value)
    normalized = normalize_nfkc(value)
    has_substantive_character = any(
        unicodedata.category(character)[0] in {"L", "M", "N", "S"}
        for character in normalized
    )

    if not has_substantive_character:
        raise ValueError(
            "Code search queries must contain a letter, mark, number, or symbol."
        )


def _require_no_control_characters(value: str) -> None:
    """Reject Unicode control characters while allowing normalizable whitespace.

    Parameters
    ----------
    value
        Caller-supplied query or filter text.

    Raises
    ------
    ValueError
        If the value contains a Unicode control character.
    """

    if any(unicodedata.category(character).startswith("C") for character in value):
        raise ValueError("Search text may not contain control characters.")
