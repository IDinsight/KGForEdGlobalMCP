"""Validate a runtime-only package from its declared runtime files alone.

This is the runtime tier of package validation. It runs at startup and as the first
stage of every validation, reads only checksum-verified loader bytes, and never opens
an archived evidence file. It binds the runtime files to the evidence archive record,
checks the slim LP index and shards against the delivery edges, and builds the same
judgment and coverage projections that full-evidence acceptance builds.
"""

# Standard Library
import hashlib

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, cast

# Third Party Library
from pydantic import ValidationError

# Package Library
from kgfegmcp.domain.enums import GraphType
from kgfegmcp.domain.identifiers import ArtifactName, Sha256Digest
from kgfegmcp.errors import ManifestBuildError
from kgfegmcp.graph.models import GraphRelationship
from kgfegmcp.packages.evidence_models import (
    EvidenceArchiveEntry,
    EvidenceArchiveRecord,
    SlimLearningProgressionProvenanceIndex,
    SlimProvenance,
)
from kgfegmcp.packages.lp_graph import LP_TYPES
from kgfegmcp.packages.lp_models import (
    JudgmentProjection,
    LearningProgressionEvidence,
    Summary,
    Unresolved,
    ValidationReport,
)
from kgfegmcp.packages.lp_validation import (
    _coverage,
    _EvidenceError,
    _projection,
    _require,
)
from kgfegmcp.packages.models import (
    EVIDENCE_ARCHIVE_RECORD_NAME,
    LP_PROVENANCE_SHARD_NAMES,
    LoadedGraphPackage,
    PackageValidationFinding,
)
from kgfegmcp.packages.normalization_models import NormalizationReceipt
from kgfegmcp.packages.normalization_sources import read_json_object
from kgfegmcp.packages.slim import SLIM_ARTIFACT_PATHS, SLIM_LP_SHARD_PATHS

_NORMALIZATION_NAME: Final[str] = "learningProgressionNormalization"

# Removed slim-record fields as (parent path, field name) pairs.
_REMOVED_RECORD_FIELDS: Final[tuple[tuple[tuple[str, ...], str], ...]] = (
    (("claim", "candidate"), "admissible_decisions"),
    (("claim", "candidate"), "evidence"),
    (("claim", "provenance"), "producer_judgment"),
)


@dataclass(frozen=True, slots=True)
class RuntimeEvidenceResult:
    """Return runtime-tier projections, archived identities and findings."""

    archived_artifact_sha256: dict[ArtifactName, Sha256Digest]
    evidence: LearningProgressionEvidence | None
    findings: tuple[PackageValidationFinding, ...]


@dataclass(frozen=True, slots=True)
class _RuntimeEvidence:
    """Hold parsed runtime evidence for one validation pass only."""

    contents: Mapping[str, bytes]
    package: LoadedGraphPackage
    record: EvidenceArchiveRecord


def _failed(finding: PackageValidationFinding) -> RuntimeEvidenceResult:
    """Return a runtime-tier result for one blocking finding.

    Parameters
    ----------
    finding
        Blocking finding.

    Returns
    -------
    RuntimeEvidenceResult
        Result without projections or archived identities.
    """

    return RuntimeEvidenceResult(
        archived_artifact_sha256={}, evidence=None, findings=(finding,)
    )


def _has_removed_field(raw: Mapping[str, object]) -> bool:
    """Report whether a slim record still carries any archived bulky field.

    Parameters
    ----------
    raw
        One parsed slim per-edge record.

    Returns
    -------
    bool
        ``True`` when any removed field is present.
    """

    for parents, field_name in _REMOVED_RECORD_FIELDS:
        value: object = raw

        for parent in parents:
            value = value.get(parent) if isinstance(value, dict) else None

        if isinstance(value, dict) and field_name in value:
            return True

    return False


def _load_record(
    *, contents: Mapping[str, bytes], package: LoadedGraphPackage
) -> EvidenceArchiveRecord:
    """Parse the declared evidence archive record and bind it to the framework.

    Parameters
    ----------
    contents
        Checksum-verified loader bytes.
    package
        Decoded package being validated.

    Returns
    -------
    EvidenceArchiveRecord
        Strictly parsed record.
    """

    record = EvidenceArchiveRecord.model_validate(
        read_json_object(
            data=contents[EVIDENCE_ARCHIVE_RECORD_NAME], label="evidence record"
        )
    )
    _require(
        code="evidence_record_identity",
        condition=record.framework_id == package.manifest.framework_id,
    )
    return record


def _record_entry(*, name: str, record: EvidenceArchiveRecord) -> EvidenceArchiveEntry:
    """Return one archived entry, rejecting a record that lacks it.

    Parameters
    ----------
    name
        Full-evidence logical name.
    record
        Parsed evidence archive record.

    Returns
    -------
    EvidenceArchiveEntry
        The named entry.
    """

    entry = record.evidence_artifacts.get(name)

    if entry is None:
        raise _EvidenceError(code="evidence_record_runtime_mismatch")

    return entry


def _slim_shard(
    *, evidence: _RuntimeEvidence, number: int, partition_count: int
) -> dict[str, object]:
    """Parse one slim shard strictly and check its placement and record shape.

    Parameters
    ----------
    evidence
        Runtime evidence holding the shard bytes.
    number
        Shard number from zero through 63.
    partition_count
        Entry count the slim index declares for this shard.

    Returns
    -------
    dict[str, object]
        Parsed shard keyed by relationship ID.
    """

    name = LP_PROVENANCE_SHARD_NAMES[number]
    bucket = read_json_object(data=evidence.contents[name], label=name)
    _require(
        code="lp_partition_contents",
        condition=(
            len(bucket) == partition_count
            and all(
                hashlib.sha256(identifier.encode("utf-8")).digest()[0] % 64 == number
                for identifier in bucket
            )
        ),
    )

    for identifier, raw in bucket.items():
        _require(
            code="lp_slim_record_shape",
            condition=isinstance(raw, dict) and not _has_removed_field(raw),
            record_id=identifier,
        )

    return bucket


def _validate_record_agreement(evidence: _RuntimeEvidence) -> None:
    """Require runtime files and record entries to describe the same carried set.

    Every ``runtime: true`` entry must be declared under the same name and path with
    the same SHA-256, every other declared file must be a slim artifact whose full
    form is archived, or the record itself.

    Parameters
    ----------
    evidence
        Runtime evidence with the parsed record.
    """

    declared = {
        str(reference.logical_name): reference
        for reference in evidence.package.artifacts
    }
    entries = evidence.record.evidence_artifacts
    carried = {name for name, entry in entries.items() if entry.runtime}
    slim = set(declared) & set(SLIM_ARTIFACT_PATHS)
    _require(
        code="evidence_record_runtime_mismatch",
        condition=(
            set(declared) - slim - {EVIDENCE_ARCHIVE_RECORD_NAME} == carried
            and all(
                declared[name].package_path == entries[name].package_path
                and declared[name].sha256 == entries[name].sha256
                for name in carried
            )
            and all(name in entries and not entries[name].runtime for name in slim)
        ),
    )


def _validate_slim_index(
    evidence: _RuntimeEvidence,
) -> SlimLearningProgressionProvenanceIndex:
    """Bind the slim LP index to declared shards and to the archived originals.

    Parameters
    ----------
    evidence
        Runtime evidence with the parsed record.

    Returns
    -------
    SlimLearningProgressionProvenanceIndex
        Validated slim index.
    """

    index = SlimLearningProgressionProvenanceIndex.model_validate(
        read_json_object(
            data=evidence.contents["learningProgressionProvenanceIndex"],
            label="slim LP provenance index",
        )
    )
    original = _record_entry(
        name="learningProgressionProvenance", record=evidence.record
    )
    original_index = _record_entry(
        name="learningProgressionProvenanceIndex", record=evidence.record
    )
    _require(
        code="lp_partition_declarations",
        condition=(
            set(index.partitions) == set(LP_PROVENANCE_SHARD_NAMES)
            and index.original_provenance_sha256 == original.sha256
            and index.original_provenance_index_sha256 == original_index.sha256
        ),
    )

    for name in LP_PROVENANCE_SHARD_NAMES:
        partition = index.partitions[name]
        reference = evidence.package.artifact(name)
        _require(
            code="lp_partition_identity",
            condition=(
                reference is not None
                and str(partition.artifact_path) == SLIM_LP_SHARD_PATHS[name]
                and reference.package_path == partition.artifact_path
                and reference.sha256 == partition.sha256
            ),
        )

    return index


def _validate_slim_record(
    *, edge: GraphRelationship, raw: dict[str, object]
) -> SlimProvenance:
    """Require one slim record's identity, endpoints and decision to match its edge.

    Parameters
    ----------
    edge
        Decoded delivery LP relationship.
    raw
        Parsed slim per-edge record.

    Returns
    -------
    SlimProvenance
        The validated slim record.
    """

    record = SlimProvenance.model_validate(raw)
    identity = (
        f"lc:curriculum:{record.doc_key}:relationship:{edge.label}:"
        f"{edge.source_entity_value}:{edge.target_entity_value}"
    )
    _require(
        code="lp_slim_record_mismatch",
        condition=(
            record.claim.judgment.decision == edge.label
            and record.claim.source_sfi_uuid == edge.source_entity_value
            and record.claim.target_sfi_uuid == edge.target_entity_value
            and record.relationship_identity_key == identity
        ),
        record_id=str(edge.relationship_id),
    )
    return record


def _validate_slim_shards(
    *, evidence: _RuntimeEvidence, index: SlimLearningProgressionProvenanceIndex
) -> tuple[JudgmentProjection, ...]:
    """Check every slim record against the delivery edges and project judgments.

    Parameters
    ----------
    evidence
        Runtime evidence holding the shard bytes and decoded delivery.
    index
        Validated slim index.

    Returns
    -------
    tuple[JudgmentProjection, ...]
        Bounded judgments sorted by relationship ID.
    """

    union: dict[str, object] = {}

    for number, name in enumerate(LP_PROVENANCE_SHARD_NAMES):
        union.update(
            _slim_shard(
                evidence=evidence,
                number=number,
                partition_count=index.partitions[name].entry_count,
            )
        )

    edges = {
        str(edge.relationship_id): edge
        for edge in evidence.package.relationships
        if edge.label in LP_TYPES
    }
    _require(code="lp_provenance_ids", condition=set(union) == set(edges))
    projections: list[JudgmentProjection] = []

    for identifier, raw in sorted(union.items()):
        # _slim_shard already required every record to be a JSON object.
        record = _validate_slim_record(
            edge=edges[identifier], raw=cast(dict[str, object], raw)
        )
        projections.append(
            _projection(identifier=identifier, judgment=record.claim.judgment)
        )

    return tuple(projections)


def _validate_learning_progressions(
    evidence: _RuntimeEvidence,
) -> LearningProgressionEvidence:
    """Run the runtime LP checks and build the in-memory projections.

    Parameters
    ----------
    evidence
        Runtime evidence for a package that includes learning progressions.

    Returns
    -------
    LearningProgressionEvidence
        Judgment and coverage projections.
    """

    receipt = NormalizationReceipt.model_validate(
        read_json_object(
            data=evidence.contents[_NORMALIZATION_NAME], label="LP normalization"
        )
    )
    _require(
        code="lp_normalization_output_hashes",
        condition=receipt.output_sha256
        == {
            entry.package_path: entry.sha256
            for name, entry in evidence.record.evidence_artifacts.items()
            if name != _NORMALIZATION_NAME
        },
    )
    index = _validate_slim_index(evidence)
    judgments = _validate_slim_shards(evidence=evidence, index=index)
    Unresolved.model_validate(
        read_json_object(
            data=evidence.contents["learningProgressionUnresolved"],
            label="LP unresolved",
        )
    )
    coverage = _coverage(
        report=ValidationReport.model_validate(
            read_json_object(
                data=evidence.contents["learningProgressionValidation"],
                label="LP validation",
            )
        ),
        summary=Summary.model_validate(
            read_json_object(
                data=evidence.contents["learningProgressionSummary"],
                label="LP summary",
            )
        ),
    )
    return LearningProgressionEvidence(coverage=coverage, judgments=judgments)


def validate_runtime_evidence(
    *, captured_contents: Mapping[str, bytes], package: LoadedGraphPackage
) -> RuntimeEvidenceResult:
    """Validate a runtime-only package and build its LP projections.

    Parameters
    ----------
    captured_contents
        Exact bytes checksum-verified by the loader: the record and, when LP is
        included, the five runtime LP files and the 64 slim shards.
    package
        Decoded immutable runtime-only package.

    Returns
    -------
    RuntimeEvidenceResult
        LP projections (``None`` when the package has no LP), the record's
        archive-only identities (logical name to SHA-256), and safe findings.

    Examples
    --------
    >>> validate_runtime_evidence(
    ...     captured_contents=verified_bytes, package=runtime_package
    ... ).findings
    ()
    """

    try:
        evidence = _RuntimeEvidence(
            contents=captured_contents,
            package=package,
            record=_load_record(contents=captured_contents, package=package),
        )
        _validate_record_agreement(evidence)
        archived = {
            ArtifactName(name): entry.sha256
            for name, entry in sorted(evidence.record.evidence_artifacts.items())
            if not entry.runtime
        }

        if GraphType.LEARNING_PROGRESSIONS not in package.manifest.included_graph_types:
            return RuntimeEvidenceResult(
                archived_artifact_sha256=archived, evidence=None, findings=()
            )

        projection = _validate_learning_progressions(evidence)
    except _EvidenceError as error:
        return _failed(
            PackageValidationFinding(
                code=error.code,
                message="Runtime evidence fails an independent package check.",
                record_id=error.record_id,
            )
        )
    except (KeyError, ManifestBuildError, TypeError, ValidationError, ValueError):
        return _failed(
            PackageValidationFinding(
                code="runtime_evidence_shape",
                message="Required runtime evidence is missing or malformed.",
            )
        )

    return RuntimeEvidenceResult(
        archived_artifact_sha256=archived, evidence=projection, findings=()
    )
