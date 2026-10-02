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
    CatalogProfileFacets,
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
from kgfegmcp.domain.models import RightsPolicy
from kgfegmcp.graph.models import (
    DirectNodeRelationshipsResult,
    FrameworkNode,
    GraphPackageIdentity,
    GraphRelationship,
    LearningComponentNode,
    RootPath,
    RootPathsResult,
    StandardNode,
    TraversalResult,
    TraversalTruncationReason,
)
from kgfegmcp.packages.models import (
    FrameworkCapabilities,
    PackageCounts,
    SnapshotRelation,
)
from kgfegmcp.schemas import FrozenSchema
from kgfegmcp.search.models import (
    CodeQueryText,
    LearningComponentSearchMode,
    LearningComponentSearchPage,
    PackageSearchScope,
    SearchCursor,
    SearchFacetEvidence,
    SearchMode,
    SearchPage,
    SearchQueryText,
    SupportedStandardReference,
    TagQueryText,
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


class PackageReference(FrozenSchema):
    """Identify the package a record comes from and the rights that govern it.

    Counts, capabilities, and profile facets are reported by ``get_framework`` and
    ``get_capabilities``; build metadata and the artifact table are in the package's
    manifest resource.
    """

    package_identity: GraphPackageIdentity
    rights: RightsPolicy


def package_reference(package: CatalogGraphPackage) -> PackageReference:
    """Reduce one accepted catalog package to its identity and rights.

    Parameters
    ----------
    package
        Accepted catalog graph package.

    Returns
    -------
    PackageReference
        Package identity and rights policy.
    """

    return PackageReference(
        package_identity=package.package_identity, rights=package.rights
    )


class PackageSummary(FrozenSchema):
    """Summarise one accepted graph package for framework discovery.

    Build timestamps, schema and manifest versions, and the artifact table are in the
    package's manifest resource.
    """

    capabilities: FrameworkCapabilities
    counts: PackageCounts
    package_identity: GraphPackageIdentity
    profile_facets: CatalogProfileFacets
    rights: RightsPolicy
    validation_status: ValidationStatus


def package_summary(package: CatalogGraphPackage) -> PackageSummary:
    """Summarise one accepted catalog package for framework discovery.

    Parameters
    ----------
    package
        Accepted catalog graph package.

    Returns
    -------
    PackageSummary
        Identity, capabilities, counts, profile facets, rights, and validation status.
    """

    return PackageSummary(
        capabilities=package.capabilities,
        counts=package.counts,
        package_identity=package.package_identity,
        profile_facets=package.profile_facets,
        rights=package.rights,
        validation_status=package.validation.status,
    )


class FrameworkSnapshotSummary(FrozenSchema):
    """Describe one accepted framework snapshot with a summary of each package."""

    available_graph_types: tuple[GraphType, ...] = Field(min_length=1)
    framework_id: FrameworkId
    graph_packages: tuple[PackageSummary, ...] = Field(min_length=1)
    snapshot_id: SnapshotId
    snapshot_relations: tuple[SnapshotRelation, ...] = ()
    source_metadata: CatalogSourceMetadata


def framework_snapshot_summary(
    snapshot: CatalogFrameworkSnapshot,
) -> FrameworkSnapshotSummary:
    """Describe one accepted snapshot with package summaries instead of records.

    Parameters
    ----------
    snapshot
        Accepted catalog framework snapshot.

    Returns
    -------
    FrameworkSnapshotSummary
        Snapshot identity, source metadata, relations, and package summaries.
    """

    return FrameworkSnapshotSummary(
        available_graph_types=snapshot.available_graph_types,
        framework_id=snapshot.framework_id,
        graph_packages=tuple(
            package_summary(package) for package in snapshot.graph_packages
        ),
        snapshot_id=snapshot.snapshot_id,
        snapshot_relations=snapshot.snapshot_relations,
        source_metadata=snapshot.source_metadata,
    )


class PackageSearchCounts(FrozenSchema):
    """Report the search-index counts that show what one package can answer."""

    coded_node_count: int = Field(ge=0)
    learning_component_document_count: int = Field(ge=0)
    lexical_document_count: int = Field(ge=0)
    tag_vocabulary_size: int = Field(ge=0)


class ListFrameworksResult(FrozenSchema):
    """Return one deterministic page of accepted framework snapshots."""

    catalog_sha256: Sha256Digest
    has_more: bool
    items: tuple[FrameworkSnapshotSummary, ...]
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

    framework: FrameworkSnapshotSummary


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
    selected_packages: tuple[GraphPackageIdentity, ...] = Field(min_length=1)


class LearningComponentsSearchRequestBase(FrozenSchema):
    """Define package selection shared by every learning-component search mode.

    These fields select which accepted packages a search touches. They describe the
    package, not the node, so they are identical to standards search. Node facet
    filters are deliberately absent: a learning component carries no grade, subject,
    or statement taxonomy of its own.
    """

    cursor: SearchCursor | None = Field(
        default=None, description=_SEARCH_CURSOR_DESCRIPTION
    )
    framework_ids: tuple[FrameworkId, ...] = Field(default=(), max_length=64)
    jurisdictions: tuple[CatalogFilterValue, ...] = Field(default=(), max_length=64)
    languages: tuple[LanguageTag, ...] = Field(default=(), max_length=64)
    limit: int = Field(
        default=25, description=_CURSOR_BOUND_LIMIT_DESCRIPTION, ge=1, le=100
    )
    snapshot_ids: tuple[SnapshotId, ...] = Field(default=(), max_length=64)
    subjects: tuple[CatalogFilterValue, ...] = Field(default=(), max_length=64)

    @model_validator(mode="after")
    def validate_package_selection(self) -> Self:
        """Require duplicate-free framework-selection and catalog-filter tuples.

        Returns
        -------
        Self
            The unchanged validated request.

        Raises
        ------
        ValueError
            If any selection tuple repeats a value.
        """

        collections = (
            ("framework_ids", tuple(str(value) for value in self.framework_ids)),
            ("jurisdictions", self.jurisdictions),
            ("languages", tuple(str(value) for value in self.languages)),
            ("snapshot_ids", tuple(str(value) for value in self.snapshot_ids)),
            ("subjects", self.subjects),
        )

        for field_name, values in collections:
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} must not contain duplicates.")

        return self


class TextLearningComponentsSearchRequest(LearningComponentsSearchRequestBase):
    """Request deterministic lexical search over learning-component descriptions."""

    match: TextMatch
    mode: Literal["learning_component_text"]
    query: SearchQueryText


class TagLearningComponentsSearchRequest(LearningComponentsSearchRequestBase):
    """Request exact controlled-tag lookup over learning-component tags."""

    mode: Literal["learning_component_tag"]
    query: TagQueryText


class SupportedCodeExactLearningComponentsSearchRequest(
    LearningComponentsSearchRequestBase
):
    """Request components supporting one exact standards statement code."""

    mode: Literal["learning_component_supported_code_exact"]
    query: CodeQueryText


class SupportedCodePrefixLearningComponentsSearchRequest(
    LearningComponentsSearchRequestBase
):
    """Request components supporting a standards statement-code prefix."""

    mode: Literal["learning_component_supported_code_prefix"]
    query: CodeQueryText


LearningComponentsSearchRequest: TypeAlias = Annotated[
    SupportedCodeExactLearningComponentsSearchRequest
    | SupportedCodePrefixLearningComponentsSearchRequest
    | TagLearningComponentsSearchRequest
    | TextLearningComponentsSearchRequest,
    Field(discriminator="mode"),
]


class SearchLearningComponentsResult(FrozenSchema):
    """Return one learning-component search page with exact snapshot evidence."""

    effective_scope: PackageSearchScope
    page: LearningComponentSearchPage
    selected_packages: tuple[GraphPackageIdentity, ...] = Field(min_length=1)


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
    package: PackageReference
    source_metadata: CatalogSourceMetadata


class HierarchyPathStep(FrozenSchema):
    """Name one node on a framework-root-to-standard hierarchy path.

    The node's complete record is one ``get_standard`` call away by ``node_id``. The
    framework root is named by its framework name.
    """

    description: str | None = None
    node_id: NodeId
    statement_code: str | None = None


def hierarchy_path_steps(path: RootPath) -> tuple[HierarchyPathStep, ...]:
    """Name every node of one complete root path, root first.

    Parameters
    ----------
    path
        Complete framework-root-to-node hierarchy path.

    Returns
    -------
    tuple[HierarchyPathStep, ...]
        One step per node carrying its identifier, statement code, and wording.
    """

    return tuple(
        HierarchyPathStep(
            description=(
                node.name if isinstance(node, FrameworkNode) else node.description
            ),
            node_id=node.node_id,
            statement_code=getattr(node, "statement_code", None),
        )
        for node in path.nodes
    )


class SupportedStandardPlacement(FrozenSchema):
    """Locate one supported standard on every root path, without ancestor records."""

    description: str
    grade_levels: tuple[str, ...]
    hierarchy_paths: tuple[tuple[HierarchyPathStep, ...], ...]
    node_id: NodeId
    statement_code: str | None = None
    support_confidence: float | None = None


class SupportedStandard(FrozenSchema):
    """Associate one supported standard with the relationship that declares it."""

    relationship: GraphRelationship
    standard: StandardNode


class GetLearningComponentRequest(FrozenSchema):
    """Request one exact learning component in one selected package."""

    ancestor_depth: int = Field(default=16, ge=0, le=64)
    framework_id: FrameworkId | None = None
    graph_type: GraphType = GraphType.ACADEMIC_STANDARDS
    node_id: NodeId
    snapshot_id: SnapshotId | None = None

    @model_validator(mode="after")
    def validate_framework_selection(self) -> GetLearningComponentRequest:
        """Require a framework family or exact snapshot selector.

        Returns
        -------
        GetLearningComponentRequest
            The unchanged validated request.

        Raises
        ------
        ValueError
            If neither framework nor snapshot identity is supplied.
        """

        if self.framework_id is None and self.snapshot_id is None:
            raise ValueError("framework_id or snapshot_id is required.")

        return self


class GetLearningComponentResult(FrozenSchema):
    """Return one exact learning component with the standards it is placed against."""

    node: LearningComponentNode
    package: PackageReference
    placements: tuple[SupportedStandardPlacement, ...]
    source_metadata: CatalogSourceMetadata


class GetLearningComponentContextRequest(FrozenSchema):
    """Request the standards one learning component supports and their placement."""

    ancestor_depth: int = Field(default=16, ge=0, le=64)
    framework_id: FrameworkId | None = None
    graph_type: GraphType = GraphType.ACADEMIC_STANDARDS
    node_id: NodeId
    snapshot_id: SnapshotId | None = None

    @model_validator(mode="after")
    def validate_framework_selection(self) -> GetLearningComponentContextRequest:
        """Require a framework family or exact snapshot selector.

        Returns
        -------
        GetLearningComponentContextRequest
            The unchanged validated request.

        Raises
        ------
        ValueError
            If neither framework nor snapshot identity is supplied.
        """

        if self.framework_id is None and self.snapshot_id is None:
            raise ValueError("framework_id or snapshot_id is required.")

        return self


class GetLearningComponentContextResult(FrozenSchema):
    """Return the standards one learning component supports and where they sit."""

    node: LearningComponentNode
    package: PackageReference
    placements: tuple[SupportedStandardPlacement, ...]
    source_metadata: CatalogSourceMetadata
    supported_standards: tuple[SupportedStandard, ...]


class GetLearningComponentsForStandardRequest(FrozenSchema):
    """Request every learning component supporting one exact standard."""

    framework_id: FrameworkId | None = None
    graph_type: GraphType = GraphType.ACADEMIC_STANDARDS
    identifier: StandardIdentifier
    snapshot_id: SnapshotId | None = None

    @model_validator(mode="after")
    def validate_framework_selection(self) -> GetLearningComponentsForStandardRequest:
        """Require a framework family or exact snapshot selector.

        Returns
        -------
        GetLearningComponentsForStandardRequest
            The unchanged validated request.

        Raises
        ------
        ValueError
            If neither framework nor snapshot identity is supplied.
        """

        if self.framework_id is None and self.snapshot_id is None:
            raise ValueError("framework_id or snapshot_id is required.")

        return self


class SupportingLearningComponent(FrozenSchema):
    """Associate one supporting component with the relationship that declares it."""

    node: LearningComponentNode
    relationship: GraphRelationship
    supported_standards: tuple[SupportedStandardReference, ...]


class GetLearningComponentsForStandardResult(FrozenSchema):
    """Return every learning component supporting one exact standard."""

    components: tuple[SupportingLearningComponent, ...]
    package: PackageReference
    source_metadata: CatalogSourceMetadata
    standard: StandardNode


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


class ContextNode(FrozenSchema):
    """Describe one node a standard-context result refers to, once per result.

    The complete record, with rights, language, and CASE identity, is one
    ``get_standard`` call away by ``node_id``. The framework root carries its framework
    name as its description.
    """

    description: str | None = None
    grade_level: tuple[str, ...] | None = None
    node_id: NodeId
    node_kind: Literal["framework", "standard"]
    normalized_statement_type: NormalizedStatementType | None = None
    statement_code: str | None = None
    statement_type: str | None = None


class ContextRelationship(FrozenSchema):
    """Describe one hierarchy relationship a standard-context result refers to.

    The complete record is readable through the relationship resource by
    ``relationship_id``.
    """

    relationship_id: RelationshipId
    resolution_status: str | None = None
    source_node_id: NodeId
    target_node_id: NodeId


class ContextNeighbor(FrozenSchema):
    """Point at one direct parent or child and the relationship that links it."""

    node_id: NodeId
    relationship_id: RelationshipId


class ContextNodeDepth(FrozenSchema):
    """Place one traversed node at its depth from the origin."""

    depth: int = Field(ge=0)
    node_id: NodeId


class ContextTraversal(FrozenSchema):
    """Report one bounded ancestor or descendant traversal by node reference."""

    is_complete: bool
    max_depth: int = Field(ge=0)
    max_nodes: int = Field(ge=1)
    nodes: tuple[ContextNodeDepth, ...] = Field(min_length=1)
    relationship_ids: tuple[RelationshipId, ...]
    truncation_reason: TraversalTruncationReason | None = None


class ContextRootPaths(FrozenSchema):
    """Report bounded complete framework-root-to-origin paths as node-ID lists."""

    framework_root_id: NodeId
    is_complete: bool
    max_depth: int = Field(ge=0)
    max_path_node_occurrences: int = Field(ge=1)
    max_paths: int = Field(ge=1)
    paths: tuple[tuple[NodeId, ...], ...]
    truncation_reason: TraversalTruncationReason | None = None


class StandardContextView(FrozenSchema):
    """Return one standard's hierarchy context with each node and relationship once.

    Traversals, neighbours, and root paths refer to ``nodes`` and ``relationships`` by
    identifier, so a node on several of them is described one time.
    """

    ancestors: ContextTraversal
    descendants: ContextTraversal | None
    direct_children: tuple[ContextNeighbor, ...] | None
    direct_parents: tuple[ContextNeighbor, ...]
    nodes: tuple[ContextNode, ...] = Field(min_length=1)
    relationship_statuses: tuple[ContextRelationshipStatus, ...]
    relationship_type: str = Field(min_length=1)
    relationships: tuple[ContextRelationship, ...]
    root_paths: ContextRootPaths | None
    standard: GetStandardResult

    @model_validator(mode="after")
    def validate_references(self) -> Self:
        """Require each table entry once and every reference to resolve in a table.

        Returns
        -------
        Self
            The unchanged internally consistent context view.

        Raises
        ------
        ValueError
            If a table repeats an entry or a section refers to a missing one.
        """

        node_ids = tuple(node.node_id for node in self.nodes)
        relationship_ids = tuple(
            relationship.relationship_id for relationship in self.relationships
        )

        if len(node_ids) != len(set(node_ids)):
            raise ValueError("nodes must list each node once.")

        if len(relationship_ids) != len(set(relationship_ids)):
            raise ValueError("relationships must list each relationship once.")

        neighbors = self.direct_parents + (self.direct_children or ())
        traversals = (
            self.ancestors,
            *((self.descendants,) if self.descendants else ()),
        )
        referenced_nodes = {
            *(neighbor.node_id for neighbor in neighbors),
            *(item.node_id for traversal in traversals for item in traversal.nodes),
            *(
                node_id
                for path in (self.root_paths.paths if self.root_paths else ())
                for node_id in path
            ),
        }
        referenced_relationships = {
            *(neighbor.relationship_id for neighbor in neighbors),
            *(
                relationship_id
                for traversal in traversals
                for relationship_id in traversal.relationship_ids
            ),
        }

        if not referenced_nodes <= set(node_ids):
            raise ValueError("Every referenced node must appear in nodes.")

        if not referenced_relationships <= set(relationship_ids):
            raise ValueError(
                "Every referenced relationship must appear in relationships."
            )

        return self


class LearningComponentStatistics(FrozenSchema):
    """Describe deterministic counts for one package's generated learning components."""

    bridge_span_counts: tuple[IntegerValueCount, ...]
    components_per_standard_counts: tuple[IntegerValueCount, ...]
    multi_standard_component_count: int = Field(ge=0)
    standards_without_components: int = Field(ge=0)
    support_confidence_maximum: float | None = None
    support_confidence_minimum: float | None = None
    supported_statement_types: tuple[str, ...]
    tag_vocabulary_size: int = Field(ge=0)
    total_learning_components: int = Field(ge=0)
    total_supports_relationships: int = Field(ge=0)


class GetFrameworkStatisticsRequest(FrozenSchema):
    """Request structural statistics for one exact or unique-current package."""

    framework_id: FrameworkId
    graph_type: GraphType = GraphType.ACADEMIC_STANDARDS
    snapshot_id: SnapshotId | None = None


class LearningProgressionStatistics(FrozenSchema):
    """Separate stored LP counts from hierarchy and component statistics."""

    builds_towards_relationships: int = Field(ge=0)
    has_learning_progression_provenance: bool
    has_learning_progressions: bool
    relates_to_relationships: int = Field(ge=0)


class FrameworkStatistics(FrozenSchema):
    """Describe deterministic source and normalized counts for one package."""

    canonical_relationship_label_counts: tuple[NullableValueCount, ...]
    code_presence: CodePresenceStatistics
    learning_components: LearningComponentStatistics
    learning_progressions: LearningProgressionStatistics
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
    total_item_nodes: int = Field(ge=0)
    total_nodes: int = Field(ge=0)
    total_relationships: int = Field(ge=0)
    unresolved_relationships: UnresolvedRelationshipStatistics
    unreachable_node_count: int = Field(ge=0)


class GetFrameworkStatisticsResult(FrozenSchema):
    """Return structural statistics with exact package and source metadata."""

    package: PackageReference
    source_metadata: CatalogSourceMetadata
    statistics: FrameworkStatistics


class PackageCapabilityResult(FrozenSchema):
    """Describe implemented capabilities for one accepted package runtime."""

    available_resource_artifacts: tuple[ArtifactName, ...]
    available_resource_kinds: tuple[str, ...]
    implemented_learning_component_search_modes: tuple[LearningComponentSearchMode, ...]
    capabilities: FrameworkCapabilities
    counts: PackageCounts
    implemented_search_modes: tuple[SearchMode, ...]
    included_graph_types: tuple[GraphType, ...]
    package_identity: GraphPackageIdentity
    rights: RightsPolicy
    search_index: PackageSearchCounts
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
