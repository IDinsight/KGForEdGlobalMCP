"""Typed LP selections and shared bounded evidence tables for stored graph queries."""

# Standard Library
from typing import Annotated, Final, Literal, TypeAlias

# Third Party Library
from pydantic import Field, StrictInt, StrictStr

# Package Library
from kgfegmcp.domain.identifiers import (
    ArtifactName,
    CaseIdentifierUri,
    CaseIdentifierUuid,
    FrameworkId,
    NodeId,
    RelationshipId,
    Sha256Digest,
    SnapshotId,
)
from kgfegmcp.graph.models import GraphRelationship
from kgfegmcp.packages.lp_models import CoverageProjection, JudgmentProjection
from kgfegmcp.schemas import FrozenSchema
from kgfegmcp.search.models import SearchFacetEvidence
from kgfegmcp.services.models import (
    CaseUriStandardIdentifier,
    CaseUuidStandardIdentifier,
    NodeIdStandardIdentifier,
    PackageReference,
)

MAX_PROGRESSION_RESULT_BYTES: Final[int] = 1024 * 1024
MAX_STATEMENT_EXCERPT_CHARACTERS: Final[int] = 2048


# Selector dependencies precede their discriminated union.
class StatementCodeStandardIdentifier(FrozenSchema):
    """Select a standard through its profile-enabled exact authored code.

    Examples
    --------
    >>> selector = StatementCodeStandardIdentifier(
    ...     identifier_type="statement_code", statement_code="B1.1"
    ... )
    """

    identifier_type: Literal["statement_code"]
    statement_code: Annotated[StrictStr, Field(max_length=512, min_length=1)]


ProgressionStandardIdentifier: TypeAlias = Annotated[
    CaseUriStandardIdentifier
    | CaseUuidStandardIdentifier
    | NodeIdStandardIdentifier
    | StatementCodeStandardIdentifier,
    Field(discriminator="identifier_type"),
]


class GetLearningProgressionRequest(FrozenSchema):
    """Pin one framework and optionally a snapshot for exact stored LP lookup.

    Examples
    --------
    >>> GetLearningProgressionRequest(framework_id="curriculum", relationship_id="edge")
    """

    framework_id: FrameworkId
    relationship_id: RelationshipId
    snapshot_id: SnapshotId | None = None


# Metadata dependencies are declared before their containing schema.
class ProgressionArtifactIdentity(FrozenSchema):
    """Expose an accepted artifact hash and resource URI without private file paths.

    Examples
    --------
    >>> identity.sha256  # Accepted source byte identity.
    """

    logical_name: ArtifactName
    sha256: Sha256Digest
    uri: str


class ProgressionLimits(FrozenSchema):
    """Report fixed service ceilings independently of caller-selected query limits.

    Examples
    --------
    >>> ProgressionLimits().max_result_bytes
    1048576
    """

    max_result_bytes: Literal[1048576] = MAX_PROGRESSION_RESULT_BYTES  # type: ignore[assignment]
    max_statement_excerpt_characters: Literal[2048] = MAX_STATEMENT_EXCERPT_CHARACTERS  # type: ignore[assignment]


class ProgressionMetadata(FrozenSchema):
    """Carry exact identity, retained coverage and generated-evidence notices.

    Examples
    --------
    >>> metadata.package.package_identity.snapshot_id
    """

    artifacts: tuple[ProgressionArtifactIdentity, ...]
    coverage: CoverageProjection
    generated_origin_notice: str = (
        "IDinsight model-generated relationships are not publisher endorsement "
        "or certified pedagogy."
    )
    limits: ProgressionLimits = Field(default_factory=ProgressionLimits)
    manifest_sha256: Sha256Digest
    manifest_uri: str
    package: PackageReference
    semantic_notice: str = (
        "buildsTowards describes support for success, not a mandatory prerequisite. "
        "relatesTo is a conceptual or skill link without sequence or dependency; "
        "source and target retain the stored canonical orientation. "
        "Structural acceptance does not establish pedagogical correctness."
    )
    stored_builds_towards_count: Annotated[StrictInt, Field(ge=0)]
    stored_relates_to_count: Annotated[StrictInt, Field(ge=0)]
    summary_uri: str
    unresolved_uri: str
    validation_uri: str


# Evidence table rows precede the result models that contain them.
class ProgressionRelationshipEvidence(FrozenSchema):
    """Keep the original generated edge and bounded accepted judgment together.

    Examples
    --------
    >>> evidence.relationship.relationship_id == evidence.judgment.relationship_id
    True
    """

    epistemic_status: Literal["llm_inferred"] = "llm_inferred"
    judgment: JudgmentProjection
    provenance_uri: str
    relationship: GraphRelationship
    relationship_uri: str


class ProgressionStandardSummary(FrozenSchema):
    """Retain endpoint identity and facets with explicitly bounded statement text.

    Examples
    --------
    >>> summary.statement_excerpted  # True when the original wording was shortened.
    """

    case_identifier_uri: CaseIdentifierUri | None
    case_identifier_uuid: CaseIdentifierUuid | None
    facets: SearchFacetEvidence
    node_id: NodeId
    standard_uri: str
    statement_code: str | None
    statement_excerpt: Annotated[str, Field(max_length=2048)] | None
    statement_excerpted: bool
    statement_type: str | None


class ProgressionEvidenceResult(FrozenSchema):
    """Share deduplicated endpoint and original edge tables across LP operations.

    Examples
    --------
    >>> result.metadata.limits.max_result_bytes
    1048576
    """

    metadata: ProgressionMetadata
    nodes: tuple[ProgressionStandardSummary, ...]
    relationships: tuple[ProgressionRelationshipEvidence, ...]


# Result inheritance follows its shared evidence base.
class GetLearningProgressionResult(ProgressionEvidenceResult):
    """Return one exact relationship with its pinned request and evidence tables.

    Examples
    --------
    >>> edge = result.relationships[0].relationship
    >>> edge.relationship_id == result.request.relationship_id
    True
    """

    request: GetLearningProgressionRequest


# Page contract dependencies precede operation-specific requests and results.
ConnectionKind: TypeAlias = Literal[
    "all", "incoming_builds", "outgoing_builds", "related"
]
EndpointScope: TypeAlias = Literal["either", "both", "source", "target"]
FacetValues: TypeAlias = Annotated[
    tuple[Annotated[StrictStr, Field(max_length=512, min_length=1)], ...],
    Field(max_length=32),
]
ProgressionCursor: TypeAlias = Annotated[
    StrictStr, Field(max_length=4096, min_length=1)
]
RelationshipTypes: TypeAlias = Annotated[
    tuple[Literal["buildsTowards", "relatesTo"], ...], Field(max_length=2)
]


class ProgressionFilters(FrozenSchema):
    """Define OR-within, AND-across endpoint facets with bounded arrays.

    Examples
    --------
    >>> filters = ProgressionFilters(normalized_grades=("1",))
    """

    local_grade_labels: FacetValues = ()
    normalized_grades: FacetValues = ()
    normalized_statement_types: FacetValues = ()
    statement_types: FacetValues = ()


class ProgressionPageRequest(FrozenSchema):
    """Bound a direct or discovery page within one exact framework route.

    Examples
    --------
    >>> request.limit
    25
    """

    cursor: ProgressionCursor | None = None
    framework_id: FrameworkId
    limit: Annotated[StrictInt, Field(ge=1, le=100)] = 25
    snapshot_id: SnapshotId | None = None


class GetStandardProgressionsRequest(ProgressionPageRequest):
    """Select incoming/outgoing builds or symmetric related concepts.

    Examples
    --------
    >>> request.connection_kind
    'all'
    """

    connection_kind: ConnectionKind = "all"
    identifier: ProgressionStandardIdentifier


class SearchLearningProgressionsRequest(ProgressionPageRequest, ProgressionFilters):
    """Select stored edges with conjunctions applied to explicit endpoint scopes.

    Examples
    --------
    >>> request.endpoint_scope
    'either'
    """

    endpoint_scope: EndpointScope = "either"
    relationship_types: RelationshipTypes = ()
    standard_identifiers: Annotated[
        tuple[ProgressionStandardIdentifier, ...], Field(max_length=20)
    ] = ()


ProgressionCollectionRequest: TypeAlias = (
    GetStandardProgressionsRequest | SearchLearningProgressionsRequest
)


class ProgressionEndpointMatch(ProgressionFilters):
    """Report the matched requested facet values separately for each endpoint.

    Examples
    --------
    >>> match.matches  # All populated criteria hold on this endpoint.
    True
    """

    matches: bool
    node_id: NodeId
    selected_standard: bool


class ProgressionConnection(FrozenSchema):
    """Name a stored edge's direct meaning and endpoint filter evidence.

    Examples
    --------
    >>> connection.connection_kind  # Relative to the selected direct standard.
    'incoming_builds'
    """

    connection_kind: Literal["incoming_builds", "outgoing_builds", "related"] | None
    relationship_id: RelationshipId
    source_match: ProgressionEndpointMatch
    target_match: ProgressionEndpointMatch


class ProgressionPage(FrozenSchema):
    """Distinguish one returned page from exhaustive selection counts.

    Examples
    --------
    >>> page.is_complete == (page.next_cursor is None)
    True
    """

    candidate_count: Annotated[StrictInt, Field(ge=0)]
    examined_count: Annotated[StrictInt, Field(ge=0, le=5000)]
    has_more: bool
    is_complete: bool
    max_examined_relationships: Literal[5000] = 5000
    next_cursor: ProgressionCursor | None
    returned_count: Annotated[StrictInt, Field(ge=0, le=100)]
    stopping_reason: Literal["byte_limit", "page_limit", "work_limit"] | None
    total_matching_count: Annotated[StrictInt, Field(ge=0)] | None


class ProgressionCollectionResult(ProgressionEvidenceResult):
    """Share bounded deduplicated tables, normalized filters and page continuation.

    Examples
    --------
    >>> result.page.returned_count == len(result.relationships)
    True
    """

    connections: tuple[ProgressionConnection, ...]
    endpoint_scope: EndpointScope
    filters: ProgressionFilters
    page: ProgressionPage
    request: ProgressionCollectionRequest
    resolved_standard_node_ids: tuple[NodeId, ...]
