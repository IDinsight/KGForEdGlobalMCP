"""This module defines immutable contracts for read-only resource delivery.

The models in this module describe resource kinds, raw and derived representations,
source-checksum evidence, public identity metadata, detailed standard provenance, and
the final content returned by ``ResourceService``. They distinguish exact accepted
source bytes from deterministic generated JSON and never expose local filesystem paths.

This module contains data contracts only. It does not route catalog requests, evaluate
rights, select packages or artifacts, access files, register FastMCP components, or
contain curriculum-specific behavior.
"""

# Future Library
from __future__ import annotations

# Standard Library
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

# Third Party Library
from pydantic import Field

# Package Library
from kgfegmcp.domain.enums import GraphType
from kgfegmcp.domain.identifiers import (
    CaseIdentifierUuid,
    FrameworkId,
    GraphPackageId,
    NodeId,
    ProfileId,
    ProfileVersion,
    RelationshipId,
    Sha256Digest,
    SnapshotId,
)
from kgfegmcp.schemas import FrozenSchema


class ResourceKind(StrEnum):
    """Identify one closed read-only MCP resource family."""

    ARTIFACT = "artifact"
    CATALOG = "catalog"
    FRAMEWORK = "framework"
    INTERPRETATION_PROFILE = "interpretation_profile"
    LEARNING_COMPONENT = "learning_component"
    LEARNING_COMPONENT_PROVENANCE = "learning_component_provenance"
    LEARNING_PROGRESSIONS = "learning_progressions"
    MANIFEST = "manifest"
    RELATIONSHIP = "relationship"
    RELATIONSHIP_PROVENANCE = "relationship_provenance"
    STANDARD = "standard"
    STANDARD_LEARNING_COMPONENTS = "standard_learning_components"
    STANDARD_PROVENANCE = "standard_provenance"
    UNRESOLVED = "unresolved"
    VALIDATION = "validation"


class ResourceRepresentation(StrEnum):
    """Describe source-exact or deterministically derived resource content."""

    DETERMINISTIC_DERIVED = "deterministic_derived"
    RAW_SOURCE = "raw_source"


class ResourceSourceEvidence(FrozenSchema):
    """Describe one exact source byte sequence supporting a resource response."""

    graph_package_id: GraphPackageId | None = None
    logical_name: str = Field(min_length=1)
    sha256: Sha256Digest
    size_bytes: int = Field(ge=0)


class ResourceMetadata(FrozenSchema):
    """Describe resource identity, representation, content, and source evidence."""

    byte_length: int = Field(ge=0)
    canonical_uri: str = Field(min_length=1)
    content_sha256: Sha256Digest
    framework_id: FrameworkId | None = None
    graph_package_id: GraphPackageId | None = None
    graph_type: GraphType | None = None
    mime_type: str = Field(min_length=1)
    profile_id: ProfileId | None = None
    profile_sha256: Sha256Digest | None = None
    profile_version: ProfileVersion | None = None
    representation: ResourceRepresentation
    resource_kind: ResourceKind
    snapshot_id: SnapshotId | None = None
    source_artifacts: tuple[ResourceSourceEvidence, ...] = ()


class LearningComponentProvenanceResult(FrozenSchema):
    """Return one learning component's provenance entry and its source attribution.

    The entry is served from slim runtime provenance; ``archived_provenance_sha256``
    identifies the archived full provenance document it was derived from.
    """

    archived_provenance_sha256: Sha256Digest
    attribution_statement: str
    node_id: NodeId
    provenance: dict[str, object]
    source_document: dict[str, object]


class LearningProgressionNotices(FrozenSchema):
    """Disclose stored generated origin and semantics without copying source prompts."""

    confidence_notice: str = (
        "Confidence is a model judgment, not a calibrated probability of learner "
        "success or validated pedagogical correctness."
    )
    coverage_notice: str = (
        "Candidate selection is not exhaustive. Missing edges do not establish "
        "absence of a pedagogical connection. Passed validation covers structural "
        "and process integrity only. Warning totals do not erase per-edge warnings."
    )
    generated_origin_notice: str = (
        "IDinsight model-generated relationships are not publisher endorsement "
        "or certified pedagogy."
    )
    semantic_notice: str = (
        "buildsTowards describes support for success, not a mandatory prerequisite. "
        "relatesTo is a conceptual or skill link without sequence or dependency. "
        "Stored direction and canonical endpoint orientation remain unchanged."
    )


class LearningProgressionArtifactLink(FrozenSchema):
    """Link exact retained LP artifacts without filesystem or producer paths."""

    logical_name: str
    sha256: Sha256Digest
    uri: str


class LearningProgressionSummaryResult(LearningProgressionNotices):
    """Expose only allowlisted counts and eligibility metadata, never rich evidence."""

    artifacts: tuple[LearningProgressionArtifactLink, ...]
    builds_towards_relationships: int = Field(ge=0)
    eligible_sfis_per_relationship: tuple[tuple[str, int], ...] | None
    has_learning_progression_provenance: bool
    has_learning_progressions: bool
    needs_review_claims: int | None
    no_relation_claims: int | None
    object_counts: dict[str, int | None]
    pedagogical_correctness_established: bool | None
    relates_to_relationships: int = Field(ge=0)
    relationship_warning_count: int | None
    relationships_with_warnings_count: int | None
    semantic_validation_performed: bool | None
    total_sfis_considered: int | None
    total_sfis_eligible: int | None
    total_sfis_excluded: int | None
    unresolved_warning_pairs: int | None
    validation_passed: bool | None
    validation_warning_count: int | None


class RelationshipProvenanceResult(LearningProgressionNotices):
    """Return one LP edge's slim provenance with explicit generated origin.

    The record keeps the identity, endpoints, final judgment (decision, direction,
    confidence, full rationale and warnings), checker outcome, model identity,
    attribution and content hashes. Candidate evidence text, admissible decisions
    and the duplicate producer judgment stay in the archive; the record's
    ``original_entry_sha256`` and ``archived_provenance_sha256`` link it there.
    """

    archived_provenance_sha256: Sha256Digest
    epistemic_status: Literal["llm_inferred"] = "llm_inferred"
    provenance: dict[str, object]
    relationship_id: RelationshipId


class StandardProvenanceResult(FrozenSchema):
    """Return one exact standard's provenance entry and its source attribution.

    The entry is served from slim runtime provenance without candidate source
    references; ``archived_provenance_sha256`` identifies the archived full
    provenance document it was derived from.
    """

    archived_provenance_sha256: Sha256Digest
    attribution_statement: str
    case_identifier_uuid: CaseIdentifierUuid
    node_id: NodeId
    provenance: dict[str, object]
    source_document: dict[str, object]


@dataclass(frozen=True, slots=True)
class ResourceDocument:
    """Carry one resource payload and its exact protocol-facing metadata.

    Attributes
    ----------
    content
        Exact raw bytes or deterministic UTF-8 JSON text.
    metadata
        Identity, checksum, MIME, representation, and source evidence.
    """

    content: str | bytes
    metadata: ResourceMetadata
