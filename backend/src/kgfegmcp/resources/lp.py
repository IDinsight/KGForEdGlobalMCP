"""Resolve accepted LP evidence and allowlist safe public summary metadata."""

# Standard Library
import hashlib

# Package Library
from kgfegmcp.domain.identifiers import RelationshipId
from kgfegmcp.errors import ManifestBuildError, ResourceNotFoundError
from kgfegmcp.packages.lp_models import Summary
from kgfegmcp.packages.models import DeclaredArtifactReference, LoadedGraphPackage
from kgfegmcp.packages.normalization_models import LearningProgressionProvenanceIndex
from kgfegmcp.packages.normalization_sources import read_json_object
from kgfegmcp.resources.models import (
    LearningProgressionArtifactLink,
    LearningProgressionSummaryResult,
)
from kgfegmcp.resources.repository import ResourceRepository
from kgfegmcp.resources.uri import artifact_uri

_COUNT_NAMES = (
    "accepted_claims",
    "builds_towards_claims",
    "builds_towards_relationships",
    "candidate_pairs",
    "final_claims",
    "generation_failure_attempts",
    "identifier_collisions",
    "needs_review_claims",
    "no_relation_claims",
    "nonpublishing_claims",
    "relates_to_claims",
    "relates_to_relationships",
    "relationship_provenance",
    "relationships",
    "requests",
    "resolved_failure_attempts",
    "unresolved_failed_pairs",
    "unresolved_warning_pairs",
)
LP_PARTITION_NAMES = tuple(
    f"learningProgressionProvenanceShard{number:02d}" for number in range(64)
)
LP_ARTIFACT_NAMES = (
    "learningProgressionBuildsTowards",
    "learningProgressionFinalClaims",
    "learningProgressionNormalization",
    "learningProgressionProvenance",
    "learningProgressionProvenanceIndex",
    "learningProgressionRelatesTo",
    "learningProgressionSummary",
    "learningProgressionUnresolved",
    "learningProgressionValidation",
)


def partition_name(relationship_id: RelationshipId) -> str:
    """Calculate the fixed accepted index slot without accepting paths or buckets.

    Parameters
    ----------
    relationship_id
        Exact accepted LP identifier.

    Returns
    -------
    str
        One canonical logical partition name.
    """

    number = hashlib.sha256(relationship_id.encode("utf-8")).digest()[0] % 64
    return LP_PARTITION_NAMES[number]


def summary_result(
    *, loaded_package: LoadedGraphPackage, repository: ResourceRepository
) -> tuple[LearningProgressionSummaryResult, tuple[DeclaredArtifactReference, ...]]:
    """Project only known numeric counts and accepted eligibility denominators.

    Parameters
    ----------
    loaded_package
        Accepted package and immutable bounded coverage projection.
    repository
        Shared checksum/source-limit boundary for original generation summary bytes.

    Returns
    -------
    tuple[LearningProgressionSummaryResult, tuple[DeclaredArtifactReference, ...]]
        Public metadata and its original summary evidence when LP is available.
    """

    evidence = loaded_package.learning_progression_evidence
    coverage = evidence.coverage if evidence else None
    summary = None
    sources: tuple[DeclaredArtifactReference, ...] = ()

    if evidence is not None:
        content, reference = repository.read_artifact(
            loaded_package=loaded_package, logical_name="learningProgressionSummary"
        )

        try:
            summary = Summary.model_validate(
                read_json_object(data=content, label="LP summary")
            )
        except (ManifestBuildError, ValueError) as error:
            raise ResourceNotFoundError(
                message="The accepted LP summary is unavailable."
            ) from error

        sources = (reference,)

    identity = loaded_package.manifest
    artifacts = tuple(
        LearningProgressionArtifactLink(
            logical_name=str(reference.logical_name),
            sha256=reference.sha256,
            uri=artifact_uri(
                artifact_name=reference.logical_name,
                framework_id=identity.framework_id,
                snapshot_id=identity.snapshot_id,
            ),
        )
        for reference in sorted(
            loaded_package.artifacts, key=lambda value: value.logical_name
        )
        if reference.logical_name in LP_ARTIFACT_NAMES
    )
    return (
        LearningProgressionSummaryResult(
            artifacts=artifacts,
            builds_towards_relationships=loaded_package.manifest.counts.builds_towards_relationships,
            eligible_sfis_per_relationship=(
                tuple(
                    (label, count)
                    for label, count in coverage.eligible_sfis_per_relationship
                    if label in {"buildsTowards", "relatesTo"}
                )
                if coverage and coverage.eligible_sfis_per_relationship is not None
                else None
            ),
            has_learning_progression_provenance=loaded_package.manifest.capabilities.has_learning_progression_provenance,
            has_learning_progressions=loaded_package.manifest.capabilities.has_learning_progressions,
            needs_review_claims=coverage.needs_review_claims if coverage else None,
            no_relation_claims=coverage.no_relation_claims if coverage else None,
            object_counts={
                name: summary.object_counts.get(name) if summary else None
                for name in _COUNT_NAMES
            },
            pedagogical_correctness_established=False if evidence else None,
            relates_to_relationships=loaded_package.manifest.counts.relates_to_relationships,
            relationship_warning_count=(
                sum(row.warning_count for row in evidence.judgments)
                if evidence
                else None
            ),
            relationships_with_warnings_count=(
                sum(row.warning_count > 0 for row in evidence.judgments)
                if evidence
                else None
            ),
            semantic_validation_performed=False if evidence else None,
            total_sfis_considered=coverage.total_sfis_considered if coverage else None,
            total_sfis_eligible=coverage.total_sfis_eligible if coverage else None,
            total_sfis_excluded=coverage.total_sfis_excluded if coverage else None,
            unresolved_warning_pairs=(
                coverage.unresolved_warning_pairs if coverage else None
            ),
            validation_passed=summary.validation_report_passed if summary else None,
            validation_warning_count=(
                coverage.validation_warning_count if coverage else None
            ),
        ),
        sources,
    )


def validated_partition_index(
    *, loaded_package: LoadedGraphPackage, repository: ResourceRepository
) -> tuple[LearningProgressionProvenanceIndex, DeclaredArtifactReference]:
    """Verify exact index membership and hash/path agreement with accepted declarations.

    Parameters
    ----------
    loaded_package
        Accepted LP package whose original-map hash is already known.
    repository
        Existing checksum and source-read limit boundary.

    Returns
    -------
    tuple[LearningProgressionProvenanceIndex, DeclaredArtifactReference]
        Verified fixed mapping and exact index byte evidence, without reading the map.

    Raises
    ------
    ResourceNotFoundError
        If index membership or original/partition identity is missing or inconsistent.
    """

    content, reference = repository.read_artifact(
        loaded_package=loaded_package, logical_name="learningProgressionProvenanceIndex"
    )

    try:
        index = LearningProgressionProvenanceIndex.model_validate(
            read_json_object(data=content, label="LP provenance index")
        )
    except (ManifestBuildError, ValueError) as error:
        raise ResourceNotFoundError(
            message="The accepted LP provenance index is unavailable."
        ) from error

    original = repository.artifact_reference(
        loaded_package=loaded_package, logical_name="learningProgressionProvenance"
    )

    if (
        set(index.partitions) != set(LP_PARTITION_NAMES)
        or index.original_provenance_sha256 != original.sha256
    ):
        raise ResourceNotFoundError(
            message="The LP index does not match accepted evidence."
        )

    for number, name in enumerate(LP_PARTITION_NAMES):
        partition = index.partitions[name]
        declared = repository.artifact_reference(
            loaded_package=loaded_package, logical_name=name
        )

        if (
            partition.sha256 != declared.sha256
            or partition.artifact_path != declared.package_path
            or str(partition.artifact_path)
            != f"additional/lp_relationship_provenance_shard_{number:02d}.json"
        ):
            raise ResourceNotFoundError(
                message="The LP partition declaration is inconsistent."
            )

    return index, reference
