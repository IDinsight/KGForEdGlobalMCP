"""Contracts for runtime-only package evidence: the archive record and slim artifacts.

A runtime-only (manifest ``1.2``) package declares slim derivations of its bulky
provenance plus one evidence archive record. The record binds the complete legacy
evidence set by logical name, legacy package path, size and SHA-256, and names the
repository-relative input-set path where each archived file is kept locally.
"""

# Standard Library
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

# Third Party Library
from pydantic import ConfigDict, Field, StrictBool, StrictStr

# Package Library
from kgfegmcp.domain.enums import GraphType
from kgfegmcp.domain.identifiers import (
    ArtifactPath,
    CaseIdentifierUuid,
    FrameworkId,
    Sha256Digest,
)
from kgfegmcp.graph.models import FrameworkNode, GraphRelationship, StandardNode
from kgfegmcp.packages.lp_models import (
    Judgment,
    RawHash,
    SourceEvidence,
    SourceFramework,
)
from kgfegmcp.packages.models import DeclaredArtifactReference, NonNegativeStrictInt
from kgfegmcp.packages.normalization_models import ProvenancePartition
from kgfegmcp.schemas import FrozenSchema

EVIDENCE_ARCHIVE_LOCATION: Literal["IDinsight Google Drive"] = "IDinsight Google Drive"
REMOVED_ENTITY_ITEM_FIELDS: tuple[Literal["candidate_source_refs"]] = (
    "candidate_source_refs",
)
REMOVED_LP_RECORD_FIELDS: tuple[
    Literal["claim.candidate.admissible_decisions"],
    Literal["claim.candidate.evidence"],
    Literal["claim.provenance.producer_judgment"],
] = (
    "claim.candidate.admissible_decisions",
    "claim.candidate.evidence",
    "claim.provenance.producer_judgment",
)


# Evidence archive record; the record follows its entry and location dependencies.
class EvidenceArchiveEntry(FrozenSchema):
    """Bind one legacy evidence artifact to its exact bytes and local input path."""

    local_path: ArtifactPath
    package_path: ArtifactPath
    runtime: StrictBool
    sha256: Sha256Digest
    size_bytes: NonNegativeStrictInt


class EvidenceArchiveLocation(FrozenSchema):
    """Name the fixed archive location without a folder link or credentials."""

    location: Literal["IDinsight Google Drive"] = EVIDENCE_ARCHIVE_LOCATION


class EvidenceArchiveRecord(FrozenSchema):
    """Declare the complete legacy evidence set bound to one runtime-only package."""

    archive: EvidenceArchiveLocation = Field(default_factory=EvidenceArchiveLocation)
    evidence_artifacts: dict[StrictStr, EvidenceArchiveEntry] = Field(min_length=1)
    format_version: Literal["1.0"] = "1.0"
    framework_id: FrameworkId


# Slim per-edge LP provenance; types follow their dependencies.
class SlimCandidate(SourceEvidence):
    """Keep candidate identity and warnings after evidence text is archived."""

    first_sfi_uuid: CaseIdentifierUuid
    pair_id: StrictStr
    second_sfi_uuid: CaseIdentifierUuid
    warnings: tuple[StrictStr, ...]


class SlimTrace(SourceEvidence):
    """Keep checker outcome and trace hashes without the duplicate producer judgment."""

    checker_checkpoint_content_hash: RawHash
    checker_outcome: Literal["accepted", "corrected"]
    checker_prompt_content_hash: RawHash
    checker_verdict_content_hash: RawHash
    execution_content_hash: RawHash
    judgment_content_hash: RawHash
    producer_checkpoint_content_hash: RawHash
    producer_prompt_content_hash: RawHash
    producer_response_content_hash: RawHash
    request_content_hash: RawHash
    request_id: StrictStr
    response_checkpoint_content_hash: RawHash
    response_content_hash: RawHash


class SlimClaim(SourceEvidence):
    """Keep the final judgment, endpoints and trace of one claim."""

    candidate: SlimCandidate
    judgment: Judgment
    provenance: SlimTrace
    source_sfi_uuid: CaseIdentifierUuid | None
    target_sfi_uuid: CaseIdentifierUuid | None


class SlimProvenance(SourceEvidence):
    """Parse one slim per-edge record: the original entry minus the removed fields."""

    approved_by: StrictStr
    attribution_statement_template: StrictStr
    candidate_artifact_byte_hashes: dict[StrictStr, RawHash]
    candidate_pairs_content_hash: RawHash
    candidate_summary_content_hash: RawHash
    claim: SlimClaim
    config_content_hash: RawHash
    doc_key: RawHash
    effective_lp_config_content_hash: RawHash
    final_claims_content_hash: RawHash
    model_configuration: dict[str, object]
    model_configuration_content_hash: RawHash
    model_settings: dict[str, object]
    model_settings_content_hash: RawHash
    original_entry_sha256: Sha256Digest
    relationship_identity_key: StrictStr
    requests_content_hash: RawHash
    source_framework: SourceFramework
    upstream_content_hash: RawHash


class SlimLearningProgressionProvenanceIndex(FrozenSchema):
    """Bind slim partitions to the archived original map and original index."""

    format_version: Literal["2.0"] = "2.0"
    original_provenance_index_sha256: Sha256Digest
    original_provenance_sha256: Sha256Digest
    partition_algorithm: Literal["SHA256(UTF8(relationship_id))[0] modulo 64"] = (
        "SHA256(UTF8(relationship_id))[0] modulo 64"
    )
    partition_count: Literal[64] = 64
    partitions: dict[str, ProvenancePartition]
    record_format_version: Literal["1.0"] = "1.0"
    removed_fields: tuple[StrictStr, ...] = REMOVED_LP_RECORD_FIELDS


# Slim entity provenance documents.
class SlimEntityProvenance(FrozenSchema):
    """Describe slim standards provenance keyed by CASE UUID."""

    format_version: Literal["1.0"] = "1.0"
    items: dict[StrictStr, dict[str, object]]
    original_sha256: Sha256Digest
    removed_item_fields: tuple[StrictStr, ...] = REMOVED_ENTITY_ITEM_FIELDS
    source_document: dict[str, object]


class SlimLearningComponentProvenance(FrozenSchema):
    """Describe slim learning-component provenance keyed by outer node ID."""

    format_version: Literal["1.0"] = "1.0"
    learning_components: dict[StrictStr, dict[str, object]] = Field(
        alias="learning_components"
    )
    original_sha256: Sha256Digest
    source_document: dict[str, object]

    model_config = ConfigDict(populate_by_name=True)


# In-memory acceptance view; never persisted.
@dataclass(frozen=True, slots=True)
class FullEvidenceView:
    """Present the complete full-evidence set plus decoded delivery for acceptance.

    Artifacts carry their full-evidence logical names and package paths, with
    checksums verified against the evidence archive record. ``contents`` holds the
    exact bytes of the artifacts the full LP checks read.
    """

    artifacts: tuple[DeclaredArtifactReference, ...]
    builds_towards_relationships: int
    contents: Mapping[str, bytes]
    framework_id: FrameworkId
    framework_root: FrameworkNode
    included_graph_types: tuple[GraphType, ...]
    item_nodes: tuple[StandardNode, ...]
    relates_to_relationships: int
    relationships: tuple[GraphRelationship, ...]

    def artifact(self, logical_name: str) -> DeclaredArtifactReference | None:
        """Return one full-evidence artifact reference by logical name.

        Parameters
        ----------
        logical_name
            Full-evidence logical name.

        Returns
        -------
        DeclaredArtifactReference | None
            The matching reference, or ``None`` when absent.
        """

        return next(
            (
                reference
                for reference in self.artifacts
                if str(reference.logical_name) == logical_name
            ),
            None,
        )
