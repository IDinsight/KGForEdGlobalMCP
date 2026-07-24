"""This module defines immutable contracts for read-only resource delivery.

The models distinguish raw accepted source bytes from deterministic derived JSON, carry
exact package and profile identity, and expose checksum evidence without revealing
local filesystem paths. They contain no catalog routing, rights decisions, file access,
FastMCP registration, or curriculum-specific behavior.
"""

# Future Library
from __future__ import annotations

# Standard Library
from dataclasses import dataclass
from enum import StrEnum

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
    MANIFEST = "manifest"
    RELATIONSHIP = "relationship"
    STANDARD = "standard"
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


class StandardProvenanceResult(FrozenSchema):
    """Return one exact standard's accepted detailed provenance entry."""

    case_identifier_uuid: CaseIdentifierUuid
    node_id: NodeId
    provenance: dict[str, object]


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
