"""Typed LP selections and shared bounded evidence tables for stored graph queries."""

# Standard Library
from typing import Annotated, Final, Literal, TypeAlias

# Third Party Library
from pydantic import Field, StrictStr

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
