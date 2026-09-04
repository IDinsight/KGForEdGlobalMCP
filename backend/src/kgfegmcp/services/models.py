"""This module defines immutable request and result models.

This module contains the validated data contracts shared by the ordinary services and
the MCP tool adapters. The models describe framework discovery, framework lookup,
standards search, exact standard lookup, graph context, framework statistics, runtime
capabilities, typed identifier namespaces, pagination cursors, and supporting count or
status evidence.

The models compose existing catalog, graph, traversal, and search contracts while
preserving exact source records, normalized evidence, package identity, profile
identity, warnings, relationship statuses, and pagination state.

This module defines and validates data shapes only. It does not access the filesystem,
load packages, route catalog requests, execute search, traverse graphs, calculate
statistics, retrieve application state, or register FastMCP components.
"""

# Future Library
from __future__ import annotations

# Standard Library
from typing import Annotated, Literal, Self, TypeAlias

# Third Party Library
from pydantic import ConfigDict, Field, RootModel, StringConstraints, model_validator

# Package Library
from kgfegmcp.catalog.models import (
    CatalogFrameworkSnapshot,
    CatalogGraphPackage,
    CatalogSourceMetadata,
)
from kgfegmcp.domain.enums import GraphType, NormalizedStatementType, ValidationStatus
from kgfegmcp.domain.identifiers import (
    ArtifactName,
    CaseIdentifierUri,
    CaseIdentifierUuid,
    FrameworkId,
    LanguageTag,
    NodeId,
    RelationshipId,
    SchemaVersion,
    Sha256Digest,
    SnapshotId,
)
from kgfegmcp.graph.models import (
    DirectNodeRelationshipsResult,
    RootPathsResult,
    StandardNode,
    TraversalResult,
)
from kgfegmcp.schemas import FrozenSchema
from kgfegmcp.search.models import (
    CodeQueryText,
    PackageSearchIndexMetadata,
    PackageSearchScope,
    SearchCursor,
    SearchFacetEvidence,
    SearchMode,
    SearchPage,
    SearchQueryText,
    TextMatch,
)

CatalogFilterValue = Annotated[str, StringConstraints(max_length=128, min_length=1)]
CatalogQueryText = Annotated[str, StringConstraints(max_length=256, min_length=1)]

_CURSOR_BOUND_LIMIT_DESCRIPTION = (
    "Maximum results returned on one page. This value is cursor-bound and must "
    "remain unchanged when continuing a paginated request."
)
_FRAMEWORK_CURSOR_DESCRIPTION = (
    "Opaque continuation cursor. When supplied, submit the exact previous "
    "list_frameworks request and replace only this cursor field. Every other "
    "field, including limit and all filters, is cursor-bound and must remain "
    "unchanged."
)
_SEARCH_CURSOR_DESCRIPTION = (
    "Opaque continuation cursor. When supplied, submit the exact previous "
    "search_standards request and replace only this cursor field. Every other "
    "field, including limit, scope, filters, mode, query, and match settings, "
    "is cursor-bound and must remain unchanged."
)


def _require_exact_uniqueness(*, field_name: str, values: tuple[str, ...]) -> None:
    """Require one exact string tuple to contain no duplicate values.

    Parameters
    ----------
    field_name
        Public field name used in the validation message.
    values
        Exact string values to validate.

    Raises
    ------
    ValueError
        If the tuple contains a duplicate value.
    """

    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must not contain duplicate values.")


class FrameworkCursor(RootModel[str]):
    """Carry an opaque checksum-protected framework-catalog pagination cursor."""

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def validate_cursor(self) -> FrameworkCursor:
        """Validate the encoded cursor surface without decoding its payload.

        Returns
        -------
        FrameworkCursor
            The unchanged validated cursor.

        Raises
        ------
        ValueError
            If the cursor is empty, oversized, or not unpadded base64url text.
        """

        value = self.root

        if not value or len(value) > 4_096:
            raise ValueError(
                "Framework cursors must contain between 1 and 4096 characters."
            )

        allowed_characters = (
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        )

        if any(character not in allowed_characters for character in value):
            raise ValueError(
                "Framework cursors must use unpadded base64url characters."
            )

        return self


class NodeIdStandardIdentifier(FrozenSchema):
    """Select a graph node through the outer node-identifier namespace."""

    identifier_type: Literal["node_id"]
    node_id: NodeId


class CaseUuidStandardIdentifier(FrozenSchema):
    """Select a graph node through the CASE UUID namespace."""

    case_identifier_uuid: CaseIdentifierUuid
    identifier_type: Literal["case_identifier_uuid"]


class CaseUriStandardIdentifier(FrozenSchema):
    """Select a graph node through the CASE URI namespace."""

    case_identifier_uri: CaseIdentifierUri
    identifier_type: Literal["case_identifier_uri"]


StandardIdentifier: TypeAlias = Annotated[
    CaseUriStandardIdentifier | CaseUuidStandardIdentifier | NodeIdStandardIdentifier,
    Field(discriminator="identifier_type"),
]


class NullableValueCount(FrozenSchema):
    """Associate one exact optional source value with a deterministic count."""

    count: int = Field(ge=0)
    value: str | None


class IntegerValueCount(FrozenSchema):
    """Associate one integer distribution value with the number of times it occurs."""

    count: int = Field(ge=0)
    value: int = Field(ge=0)


class DepthCount(FrozenSchema):
    """Associate one minimum hierarchy depth with a node count."""

    depth: int = Field(ge=0)
    node_count: int = Field(ge=0)


class ParentCountBucket(FrozenSchema):
    """Associate one exact direct-parent count with the number of target nodes."""

    node_count: int = Field(ge=0)
    parent_count: int = Field(ge=0)


class CodePresenceStatistics(FrozenSchema):
    """Describe exact coded and uncoded item-node counts."""

    coded_item_count: int = Field(ge=0)
    uncoded_item_count: int = Field(ge=0)


class MultiParentStatistics(FrozenSchema):
    """Describe deterministic direct-parent cardinality in one hierarchy graph."""

    maximum_parent_count: int = Field(ge=0)
    parent_count_distribution: tuple[ParentCountBucket, ...]
    target_count: int = Field(ge=0)


class UnresolvedRelationshipStatistics(FrozenSchema):
    """Describe exact relationship-resolution status counts."""

    resolved_count: int = Field(ge=0)
    status_counts: tuple[NullableValueCount, ...]
    unresolved_count: int = Field(ge=0)


class ListFrameworksRequest(FrozenSchema):
    """Request filtered deterministic discovery of accepted framework snapshots."""

    cursor: FrameworkCursor | None = Field(
        default=None, description=_FRAMEWORK_CURSOR_DESCRIPTION
    )
    graph_types: tuple[GraphType, ...] = Field(default=(), max_length=16)
    is_current: bool | None = None
    issuing_authorities: tuple[CatalogFilterValue, ...] = Field(
        default=(), max_length=64
    )
    jurisdiction_types: tuple[CatalogFilterValue, ...] = Field(
        default=(), max_length=64
    )
    jurisdictions: tuple[CatalogFilterValue, ...] = Field(default=(), max_length=64)
    languages: tuple[LanguageTag, ...] = Field(default=(), max_length=64)
    limit: int = Field(
        default=25, description=_CURSOR_BOUND_LIMIT_DESCRIPTION, ge=1, le=100
    )
    local_grades: tuple[CatalogFilterValue, ...] = Field(default=(), max_length=64)
    normalized_grades: tuple[CatalogFilterValue, ...] = Field(default=(), max_length=64)
    query: CatalogQueryText | None = None
    subjects: tuple[CatalogFilterValue, ...] = Field(default=(), max_length=64)
    validation_status: tuple[ValidationStatus, ...] = Field(default=(), max_length=8)

    @model_validator(mode="after")
    def validate_filters(self) -> ListFrameworksRequest:
        """Require every tuple filter to be duplicate-free.

        Returns
        -------
        ListFrameworksRequest
            The unchanged validated request.

        Raises
        ------
        ValueError
            If a tuple filter contains a duplicate exact value.
        """

        collections = (
            ("graph_types", tuple(value.value for value in self.graph_types)),
            ("issuing_authorities", self.issuing_authorities),
            ("jurisdiction_types", self.jurisdiction_types),
            ("jurisdictions", self.jurisdictions),
            ("languages", tuple(str(value) for value in self.languages)),
            ("local_grades", self.local_grades),
            ("normalized_grades", self.normalized_grades),
            ("subjects", self.subjects),
            (
                "validation_status",
                tuple(value.value for value in self.validation_status),
            ),
        )

        for field_name, values in collections:
            _require_exact_uniqueness(field_name=field_name, values=values)

        if self.query is not None and not self.query.strip():
            raise ValueError("query must contain non-whitespace text.")

        return self


class ListFrameworksResult(FrozenSchema):
    """Return one deterministic page of accepted framework snapshots."""

    catalog_sha256: Sha256Digest
    has_more: bool
    items: tuple[CatalogFrameworkSnapshot, ...]
    next_cursor: FrameworkCursor | None
    returned_count: int = Field(ge=0)
    total_matching_count: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_page(self) -> ListFrameworksResult:
        """Require page counts and continuation state to agree.

        Returns
        -------
        ListFrameworksResult
            The unchanged validated page.

        Raises
        ------
        ValueError
            If counts or continuation state disagree.
        """

        if self.returned_count != len(self.items):
            raise ValueError("returned_count must equal the number of items.")

        if self.has_more != (self.next_cursor is not None):
            raise ValueError("has_more and next_cursor must agree.")

        if self.returned_count > self.total_matching_count:
            raise ValueError("returned_count may not exceed total_matching_count.")

        return self


class GetFrameworkRequest(FrozenSchema):
    """Request one exact or unique-current framework snapshot."""

    framework_id: FrameworkId
    snapshot_id: SnapshotId | None = None


class GetFrameworkResult(FrozenSchema):
    """Return one complete accepted framework snapshot."""

    framework: CatalogFrameworkSnapshot


class StandardsSearchRequestBase(FrozenSchema):
    """Define fields shared by canonical text and code standards searches."""

    cursor: SearchCursor | None = Field(
        default=None, description=_SEARCH_CURSOR_DESCRIPTION
    )
    framework_ids: tuple[FrameworkId, ...] = Field(default=(), max_length=64)
    include_groupings: bool = False
    jurisdictions: tuple[CatalogFilterValue, ...] = Field(default=(), max_length=64)
    languages: tuple[LanguageTag, ...] = Field(default=(), max_length=64)
    limit: int = Field(
        default=25, description=_CURSOR_BOUND_LIMIT_DESCRIPTION, ge=1, le=100
    )
    local_grade_labels: tuple[CatalogFilterValue, ...] = Field(
        default=(), max_length=64
    )
    normalized_grades: tuple[CatalogFilterValue, ...] = Field(default=(), max_length=64)
    normalized_statement_types: tuple[NormalizedStatementType, ...] = Field(
        default=(), max_length=64
    )
    normalized_subjects: tuple[CatalogFilterValue, ...] = Field(
        default=(), max_length=64
    )
    snapshot_ids: tuple[SnapshotId, ...] = Field(default=(), max_length=64)
    statement_types: tuple[CatalogFilterValue, ...] = Field(default=(), max_length=64)
    subjects: tuple[CatalogFilterValue, ...] = Field(default=(), max_length=64)

    @model_validator(mode="after")
    def validate_common_filters(self) -> Self:
        """Require duplicate-free framework-selection and catalog-filter tuples.

        Returns
        -------
        Self
            The unchanged validated search request.

        Raises
        ------
        ValueError
            If any tuple contains a duplicate exact value.
        """

        collections = (
            ("framework_ids", tuple(str(value) for value in self.framework_ids)),
            ("jurisdictions", self.jurisdictions),
            ("languages", tuple(str(value) for value in self.languages)),
            ("local_grade_labels", self.local_grade_labels),
            ("normalized_grades", self.normalized_grades),
            (
                "normalized_statement_types",
                tuple(value.value for value in self.normalized_statement_types),
            ),
            ("normalized_subjects", self.normalized_subjects),
            ("snapshot_ids", tuple(str(value) for value in self.snapshot_ids)),
            ("statement_types", self.statement_types),
            ("subjects", self.subjects),
        )

        for field_name, values in collections:
            _require_exact_uniqueness(field_name=field_name, values=values)

        return self


class TextStandardsSearchRequest(StandardsSearchRequestBase):
    """Request deterministic package-local lexical standards search."""

    match: TextMatch
    mode: Literal["text"]
    query: SearchQueryText


class ExactCodeStandardsSearchRequest(StandardsSearchRequestBase):
    """Request deterministic profile-governed exact statement-code search."""

    mode: Literal["code_exact"]
    query: CodeQueryText


class PrefixCodeStandardsSearchRequest(StandardsSearchRequestBase):
    """Request deterministic profile-governed statement-code prefix search."""

    mode: Literal["code_prefix"]
    query: CodeQueryText


StandardsSearchRequest: TypeAlias = Annotated[
    ExactCodeStandardsSearchRequest
    | PrefixCodeStandardsSearchRequest
    | TextStandardsSearchRequest,
    Field(discriminator="mode"),
]


class SearchStandardsResult(FrozenSchema):
    """Return one existing search page with exact selected snapshot evidence."""

    effective_scope: PackageSearchScope
    page: SearchPage
    selected_snapshots: tuple[CatalogFrameworkSnapshot, ...] = Field(min_length=1)


class GetStandardRequest(FrozenSchema):
    """Request one exact standard or grouping in one selected package."""

    framework_id: FrameworkId | None = None
    graph_type: GraphType = GraphType.ACADEMIC_STANDARDS
    identifier: StandardIdentifier
    snapshot_id: SnapshotId | None = None

    @model_validator(mode="after")
    def validate_framework_selection(self) -> GetStandardRequest:
        """Require a framework family or exact snapshot selector.

        Returns
        -------
        GetStandardRequest
            The unchanged validated request.

        Raises
        ------
        ValueError
            If neither framework nor snapshot identity is supplied.
        """

        if self.framework_id is None and self.snapshot_id is None:
            raise ValueError("framework_id or snapshot_id is required.")

        return self


class GetStandardResult(FrozenSchema):
    """Return one exact source standard with package and facet evidence."""

    facets: SearchFacetEvidence
    node: StandardNode
    package: CatalogGraphPackage
    source_metadata: CatalogSourceMetadata


class GetStandardContextRequest(FrozenSchema):
    """Request deterministic bounded hierarchy context for one exact standard."""

    ancestor_depth: int = Field(default=16, ge=0, le=64)
    child_depth: int = Field(default=1, ge=0, le=64)
    framework_id: FrameworkId | None = None
    graph_type: GraphType = GraphType.ACADEMIC_STANDARDS
    include_all_root_paths: bool = True
    include_descendants: bool = False
    include_direct_children: bool = True
    include_unresolved: bool = True
    max_nodes: int = Field(default=250, ge=1, le=2_000)
    max_path_node_occurrences: int = Field(default=8_192, ge=1, le=100_000)
    max_paths: int = Field(default=128, ge=1, le=1_000)
    node_id: NodeId
    relationship_types: tuple[CatalogFilterValue, ...] = Field(default=(), max_length=1)
    snapshot_id: SnapshotId | None = None

    @model_validator(mode="after")
    def validate_context_request(self) -> GetStandardContextRequest:
        """Require one framework selector and a duplicate-free relationship tuple.

        Returns
        -------
        GetStandardContextRequest
            The unchanged validated request.

        Raises
        ------
        ValueError
            If framework selection is absent or relationship types repeat.
        """

        if self.framework_id is None and self.snapshot_id is None:
            raise ValueError("framework_id or snapshot_id is required.")

        _require_exact_uniqueness(
            field_name="relationship_types", values=self.relationship_types
        )
        return self


class ContextRelationshipStatus(FrozenSchema):
    """Expose one exact non-empty relationship-resolution status."""

    relationship_id: RelationshipId
    resolution_status: str = Field(min_length=1)


class GetStandardContextResult(FrozenSchema):
    """Return deterministic direct, bounded, and complete-path graph context."""

    ancestors: TraversalResult
    direct_children: DirectNodeRelationshipsResult | None
    direct_parents: DirectNodeRelationshipsResult
    descendants: TraversalResult | None
    relationship_statuses: tuple[ContextRelationshipStatus, ...]
    root_paths: RootPathsResult | None
    standard: GetStandardResult


class LearningComponentStatistics(FrozenSchema):
    """Describe deterministic counts for one package's generated learning components."""

    bridge_span_counts: tuple[IntegerValueCount, ...]
    components_per_standard_counts: tuple[IntegerValueCount, ...]
    multi_standard_component_count: int = Field(ge=0)
    standards_without_components: int = Field(ge=0)
    support_confidence_maximum: float | None = None
    support_confidence_minimum: float | None = None
    tag_vocabulary_size: int = Field(ge=0)
    total_learning_components: int = Field(ge=0)
    total_supports_relationships: int = Field(ge=0)


class GetFrameworkStatisticsRequest(FrozenSchema):
    """Request structural statistics for one exact or unique-current package."""

    framework_id: FrameworkId
    graph_type: GraphType = GraphType.ACADEMIC_STANDARDS
    snapshot_id: SnapshotId | None = None


class FrameworkStatistics(FrozenSchema):
    """Describe deterministic source and normalized counts for one package."""

    canonical_relationship_label_counts: tuple[NullableValueCount, ...]
    code_presence: CodePresenceStatistics
    local_grade_label_counts: tuple[NullableValueCount, ...]
    maximum_structural_depth: int = Field(ge=0)
    minimum_structural_depth_counts: tuple[DepthCount, ...]
    multi_parent: MultiParentStatistics
    node_grade_level_counts: tuple[NullableValueCount, ...]
    normalized_grade_counts: tuple[NullableValueCount, ...]
    normalized_statement_type_counts: tuple[NullableValueCount, ...]
    source_relationship_type_counts: tuple[NullableValueCount, ...]
    statement_type_counts: tuple[NullableValueCount, ...]
    total_framework_nodes: int = Field(ge=0)
    learning_components: LearningComponentStatistics
    total_item_nodes: int = Field(ge=0)
    total_nodes: int = Field(ge=0)
    total_relationships: int = Field(ge=0)
    unresolved_relationships: UnresolvedRelationshipStatistics
    unreachable_node_count: int = Field(ge=0)


class GetFrameworkStatisticsResult(FrozenSchema):
    """Return structural statistics with exact package and source metadata."""

    package: CatalogGraphPackage
    source_metadata: CatalogSourceMetadata
    statistics: FrameworkStatistics


class PackageCapabilityResult(FrozenSchema):
    """Describe implemented capabilities for one accepted package runtime."""

    available_resource_artifacts: tuple[ArtifactName, ...]
    available_resource_kinds: tuple[str, ...]
    implemented_search_modes: tuple[SearchMode, ...]
    package: CatalogGraphPackage
    search_index: PackageSearchIndexMetadata
    source_metadata: CatalogSourceMetadata
    traversal_relationship_type: str = Field(min_length=1)


class GetCapabilitiesResult(FrozenSchema):
    """Describe implemented tools, prompts, resources, and package capabilities."""

    available_graph_types: tuple[GraphType, ...]
    framework_prompt_overlays_optional: bool
    implemented_features: tuple[str, ...]
    packages: tuple[PackageCapabilityResult, ...]
    prompt_config_schema_version: SchemaVersion
    prompt_names: tuple[str, ...]
    resource_representations: tuple[str, ...]
    resource_uri_templates: tuple[str, ...]
    resource_uris: tuple[str, ...]
    server_name: str = Field(min_length=1)
    tool_names: tuple[str, ...]
    unavailable_features: tuple[str, ...]
