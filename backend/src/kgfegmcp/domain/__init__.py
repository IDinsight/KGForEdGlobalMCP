"""This package contains framework-independent domain vocabulary and core curriculum
graph models.

This package defines the shared concepts used throughout the application, including
stable enumerations, validated identifier types, and semantic models for framework
snapshots, standards, relationships, rights, provenance, and result status.

The domain layer is independent of FastMCP, filesystem layouts, JSONL wire encoding,
search backends, and individual curricula. It preserves source terminology,
identifiers, immutable snapshot identity, uncertainty, and multi-parent graph topology
while providing consistent contracts for package, profile, catalog, graph, search,
resource, and MCP layers.

Curriculum-specific semantics belong in versioned interpretation profiles.
Transport-specific behavior belongs in the MCP layer, and package loading or storage
behavior belongs in their respective infrastructure packages.
"""

# Package Library
from kgfegmcp.domain.enums import (
    CodeAvailability,
    DerivativeGenerationPolicy,
    EpistemicStatus,
    GraphType,
    InvalidPackagePolicy,
    NormalizedStatementType,
    RightsReviewStatus,
    SnapshotRelationType,
    SubjectMappingStatus,
    ValidationStatus,
)
from kgfegmcp.domain.identifiers import (
    ArtifactName,
    ArtifactPath,
    CaseIdentifierUri,
    CaseIdentifierUuid,
    FrameworkId,
    GraphPackageId,
    LanguageTag,
    ManifestVersion,
    NodeId,
    ProfileId,
    ProfileVersion,
    RelationshipId,
    SchemaVersion,
    Sha256Digest,
    SnapshotId,
    SnapshotVersionToken,
    build_initial_graph_package_id,
    build_snapshot_id,
    build_versioned_graph_package_id,
)
from kgfegmcp.domain.models import RightsPolicy, SubjectVocabulary

__all__ = [
    "ArtifactName",
    "ArtifactPath",
    "CaseIdentifierUri",
    "CaseIdentifierUuid",
    "CodeAvailability",
    "DerivativeGenerationPolicy",
    "EpistemicStatus",
    "FrameworkId",
    "GraphPackageId",
    "GraphType",
    "InvalidPackagePolicy",
    "LanguageTag",
    "ManifestVersion",
    "NodeId",
    "NormalizedStatementType",
    "ProfileId",
    "ProfileVersion",
    "RelationshipId",
    "RightsPolicy",
    "RightsReviewStatus",
    "SchemaVersion",
    "Sha256Digest",
    "SnapshotId",
    "SnapshotRelationType",
    "SnapshotVersionToken",
    "SubjectMappingStatus",
    "SubjectVocabulary",
    "ValidationStatus",
    "build_initial_graph_package_id",
    "build_snapshot_id",
    "build_versioned_graph_package_id",
]
