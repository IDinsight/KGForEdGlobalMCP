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
from kgfegmcp.tool_results import MAX_TOOL_RESULT_BYTES, ToolResultLimits

MAX_PROGRESSION_RESULT_BYTES: Final[int] = MAX_TOOL_RESULT_BYTES
MAX_STATEMENT_EXCERPT_CHARACTERS: Final[int] = 2048

# LP query results are derived from exactly these accepted artifacts; the manifest hash
# binds the complete inventory, which is not repeated in every result.
PROGRESSION_DERIVATION_ARTIFACT_NAMES: Final[tuple[str, ...]] = (
    "learningProgressionProvenance",
    "learningProgressionProvenanceIndex",
    "nodes",
    "relationships",
)


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
    """Expose an accepted artifact hash and resource URI without private file paths."""

    logical_name: ArtifactName
    sha256: Sha256Digest
    uri: str


class ProgressionLimits(ToolResultLimits):
    """Report fixed service ceilings independently of caller-selected query limits."""

    max_statement_excerpt_characters: Literal[2048] = MAX_STATEMENT_EXCERPT_CHARACTERS  # type: ignore[assignment]


class ProgressionMetadata(FrozenSchema):
    """Carry exact identity, retained coverage and generated-evidence notices."""

    artifact_inventory_notice: str = (
        "artifacts lists only the accepted artifacts this result is derived from. "
        "The manifest at manifestUri, bound by manifestSha256, records every accepted "
        "artifact checksum; read it through native resources or read_evidence."
    )
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
    """Keep the original generated edge and bounded accepted judgment together."""

    epistemic_status: Literal["llm_inferred"] = "llm_inferred"
    judgment: JudgmentProjection
    provenance_uri: str
    relationship: GraphRelationship
    relationship_uri: str


class ProgressionStandardSummary(FrozenSchema):
    """Retain endpoint identity and facets with explicitly bounded statement text."""

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
    """Share deduplicated endpoint and original edge tables across LP operations."""

    continuation_notice: str = (
        "No continuation is offered for this operation. Read full evidence through "
        "read_evidence with the returned standard/provenance URIs under native rights "
        "and limits; content windows do not extend the progression search."
    )
    metadata: ProgressionMetadata
    nodes: tuple[ProgressionStandardSummary, ...]
    relationships: tuple[ProgressionRelationshipEvidence, ...]


# Result inheritance follows its shared evidence base.
class GetLearningProgressionResult(ProgressionEvidenceResult):
    """Return one exact relationship with its pinned request and evidence tables."""

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
    """Define OR-within, AND-across endpoint facets with bounded arrays."""

    local_grade_labels: FacetValues = ()
    normalized_grades: FacetValues = ()
    normalized_statement_types: FacetValues = ()
    statement_types: FacetValues = ()


class ProgressionPageRequest(FrozenSchema):
    """Bound a direct or discovery page within one exact framework route."""

    cursor: ProgressionCursor | None = None
    framework_id: FrameworkId
    limit: Annotated[StrictInt, Field(ge=1, le=100)] = 25
    snapshot_id: SnapshotId | None = None


class GetStandardProgressionsRequest(ProgressionPageRequest):
    """Select incoming/outgoing builds or symmetric related concepts."""

    connection_kind: ConnectionKind = "all"
    identifier: ProgressionStandardIdentifier


class SearchLearningProgressionsRequest(ProgressionPageRequest, ProgressionFilters):
    """Select stored edges with conjunctions applied to explicit endpoint scopes."""

    endpoint_scope: EndpointScope = "either"
    relationship_types: RelationshipTypes = ()
    standard_identifiers: Annotated[
        tuple[ProgressionStandardIdentifier, ...], Field(max_length=20)
    ] = ()


ProgressionCollectionRequest: TypeAlias = (
    GetStandardProgressionsRequest | SearchLearningProgressionsRequest
)


class ProgressionEndpointMatch(ProgressionFilters):
    """Report the matched requested facet values separately for each endpoint."""

    matches: bool
    node_id: NodeId
    selected_standard: bool


class ProgressionConnection(FrozenSchema):
    """Name a stored edge's direct meaning and endpoint filter evidence."""

    connection_kind: Literal["incoming_builds", "outgoing_builds", "related"] | None
    relationship_id: RelationshipId
    source_match: ProgressionEndpointMatch
    target_match: ProgressionEndpointMatch


class ProgressionPage(FrozenSchema):
    """Distinguish one returned page from exhaustive selection counts."""

    candidate_count: Annotated[StrictInt, Field(ge=0)]
    examined_count: Annotated[StrictInt, Field(ge=0, le=5000)]
    has_more: bool
    is_complete: bool
    max_examined_relationships: Literal[5000] = 5000
    next_cursor: ProgressionCursor | None
    next_request: ProgressionCollectionRequest | None = None
    returned_count: Annotated[StrictInt, Field(ge=0, le=100)]
    stopping_reason: Literal["byte_limit", "page_limit", "work_limit"] | None
    total_matching_count: Annotated[StrictInt, Field(ge=0)] | None


class ProgressionCollectionResult(ProgressionEvidenceResult):
    """Share bounded deduplicated tables, normalized filters and page continuation."""

    connections: tuple[ProgressionConnection, ...]
    continuation_notice: str = (
        "If page.nextCursor is present, replay page.nextRequest unchanged; it preserves "
        "the route, filters and limits and sets cursor to that exact value. "
        "The byte_limit stopping reason covers either output ceiling. A returned page is "
        "not the complete selection while a cursor remains. Read full evidence via "
        "read_evidence using the linked standard/provenance URIs under native policy. "
        "Absence of a stored match does not establish absence of a pedagogical "
        "connection."
    )
    endpoint_scope: EndpointScope
    filters: ProgressionFilters
    page: ProgressionPage
    request: ProgressionCollectionRequest
    resolved_standard_node_ids: tuple[NodeId, ...]


# Traversal contract dependencies precede the derived subgraph result.
ProgressionTraversalDirection: TypeAlias = Literal["downstream", "upstream"]
TraversalTruncationReason: TypeAlias = Literal[
    "depth_limit", "node_limit", "edge_limit", "work_limit", "byte_limit"
]


class TraverseLearningProgressionsRequest(FrozenSchema):
    """Select a builds-only reachable subgraph with finite positive bounds."""

    direction: ProgressionTraversalDirection = "downstream"
    framework_id: FrameworkId
    identifier: ProgressionStandardIdentifier
    max_depth: Annotated[StrictInt, Field(ge=1, le=12)] = 8
    max_edges: Annotated[StrictInt, Field(ge=1, le=100)] = 100
    max_nodes: Annotated[StrictInt, Field(ge=1, le=250)] = 100
    snapshot_id: SnapshotId | None = None


class ProgressionTraversalDistance(FrozenSchema):
    """Record minimum builds-edge distance from the selected origin."""

    depth: Annotated[StrictInt, Field(ge=0, le=12)]
    node_id: NodeId


class ProgressionTraversalFrontier(ProgressionTraversalDistance):
    """Report excluded depth edges and pending adjacency at returned nodes."""

    depth_limited_relationship_count: Annotated[StrictInt, Field(ge=0)]
    pending_relationship_count: Annotated[StrictInt, Field(ge=0)]


class ProgressionTraversalCounters(FrozenSchema):
    """Expose actual bounded search effort separately from returned evidence."""

    depth_frontier_examined_relationship_count: Annotated[
        StrictInt, Field(ge=0, le=5000)
    ]
    examined_relationship_count: Annotated[StrictInt, Field(ge=0, le=5000)]
    fully_examined_node_count: Annotated[StrictInt, Field(ge=0, le=250)]
    max_examined_relationships: Literal[5000] = 5000
    returned_node_count: Annotated[StrictInt, Field(ge=1, le=250)]
    returned_relationship_count: Annotated[StrictInt, Field(ge=0, le=100)]


class TraverseLearningProgressionsResult(ProgressionEvidenceResult):
    """Return exact generated edges within a deterministic derived subgraph."""

    counters: ProgressionTraversalCounters
    distances: tuple[ProgressionTraversalDistance, ...]
    epistemic_status: Literal["deterministic_derived"] = "deterministic_derived"
    frontier: tuple[ProgressionTraversalFrontier, ...]
    graph_exhausted: bool
    origin_node_id: NodeId
    request: TraverseLearningProgressionsRequest
    scope_complete: bool
    traversal_notice: str = (
        "Distances are minimum stored buildsTowards hops in the requested direction. "
        "Edges between returned nodes retain their stored orientation, including "
        "branching, merging and cycle-closing edges. This derived subgraph asserts "
        "no new direct relationship or compulsory teaching order. No continuation "
        "is offered; narrow bounded inputs and rerun after truncation. The byte_limit "
        "reason covers either complete-envelope ceiling. Even exhausted "
        "absence means no stored connection, not no pedagogical connection."
    )
    truncation_reasons: tuple[TraversalTruncationReason, ...]


# Path contract dependencies precede their derived result.
PathTruncationReason: TypeAlias = Literal[
    "depth_limit", "path_limit", "work_limit", "queue_limit", "byte_limit"
]


class GetLearningProgressionPathsRequest(FrozenSchema):
    """Select directed simple builds paths between two exact standards."""

    framework_id: FrameworkId
    max_depth: Annotated[StrictInt, Field(ge=1, le=12)] = 6
    max_paths: Annotated[StrictInt, Field(ge=1, le=20)] = 3
    snapshot_id: SnapshotId | None = None
    source_identifier: ProgressionStandardIdentifier
    target_identifier: ProgressionStandardIdentifier


class ProgressionPath(FrozenSchema):
    """Reference ordered original hops and standards in deduplicated evidence tables."""

    node_ids: Annotated[tuple[NodeId, ...], Field(min_length=2, max_length=13)]
    relationship_ids: Annotated[
        tuple[RelationshipId, ...], Field(min_length=1, max_length=12)
    ]


class ProgressionPathCounters(FrozenSchema):
    """Report actual work and cumulative queue admission, including the source state."""

    depth_frontier_examined_relationship_count: Annotated[
        StrictInt, Field(ge=0, le=5000)
    ]
    enqueued_state_count: Annotated[StrictInt, Field(ge=1, le=5000)]
    examined_relationship_count: Annotated[StrictInt, Field(ge=0, le=5000)]
    max_examined_relationships: Literal[5000] = 5000
    max_queue_states: Literal[5000] = 5000
    peak_queue_state_count: Annotated[StrictInt, Field(ge=1, le=5000)]
    returned_path_count: Annotated[StrictInt, Field(ge=0, le=20)]


class ProgressionPathFrontier(FrozenSchema):
    """Expose remaining partial paths and excluded extensions without queue content."""

    depth_limited_extension_count: Annotated[StrictInt, Field(ge=0, le=5000)]
    pending_adjacency_count: Annotated[StrictInt, Field(ge=0)]
    queued_state_count: Annotated[StrictInt, Field(ge=0, le=5000)]


class GetLearningProgressionPathsResult(ProgressionEvidenceResult):
    """Return bounded alternative simple paths with original generated hop evidence."""

    counters: ProgressionPathCounters
    epistemic_status: Literal["deterministic_derived"] = "deterministic_derived"
    frontier: ProgressionPathFrontier
    graph_exhausted: bool
    next_unreturned_path: ProgressionPath | None = None
    path_notice: str = (
        "Paths follow stored buildsTowards edges from source to target, ordered by "
        "hop count then relationship-ID tuple. Completed target paths are terminal. "
        "Exhaustion refers to this simple-path search; requested-depth completeness "
        "does not imply global exhaustion. Derived paths assert no new direct edge "
        "or compulsory teaching order. No continuation is offered. The byte_limit "
        "reason covers either complete-envelope ceiling; later paths may exist "
        "beyond that stop. nextUnreturnedPath, when present, names the next "
        "complete path by IDs only and its edges are not in the tables: inspect "
        "them with get_learning_progression, or narrow maxDepth or maxPaths and "
        "rerun. Even exhausted absence means no stored connection, not no "
        "pedagogical connection."
    )
    paths: tuple[ProgressionPath, ...]
    request: GetLearningProgressionPathsRequest
    scope_complete: bool
    source_node_id: NodeId
    target_node_id: NodeId
    truncation_reasons: tuple[PathTruncationReason, ...]
