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
    LEARNING_COMPONENT = "learning_component"
    LEARNING_COMPONENT_PROVENANCE = "learning_component_provenance"
    MANIFEST = "manifest"
    RELATIONSHIP = "relationship"
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
    """Return one learning component's exact detailed provenance entry."""

    node_id: NodeId
    provenance: dict[str, object]


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
