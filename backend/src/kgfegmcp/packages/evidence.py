"""Accept a runtime-only package against its archived full evidence.

This is the evidence tier of package validation. It runs only inside package
acceptance, after the runtime tier has passed. It verifies every archived file against
the evidence archive record, assembles an in-memory ``FullEvidenceView``, runs the full
LP checks on it, and requires every slim runtime artifact to equal its deterministic
derivation from the evidence and every projection to equal the runtime tier's.
"""

# Standard Library
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, TypeVar

# Third Party Library
from pydantic import ValidationError

# Package Library
from kgfegmcp.domain.identifiers import Sha256Digest
from kgfegmcp.errors import EvidenceArchiveUnavailableError, ManifestBuildError
from kgfegmcp.packages.checksums import calculate_bytes_sha256, calculate_file_sha256
from kgfegmcp.packages.evidence_models import (
    EVIDENCE_ARCHIVE_LOCATION,
    EvidenceArchiveEntry,
    EvidenceArchiveRecord,
    FullEvidenceView,
    SlimEntityProvenance,
    SlimLearningComponentProvenance,
)
from kgfegmcp.packages.lp_models import LearningProgressionEvidence
from kgfegmcp.packages.lp_validation import validate_learning_progression_evidence
from kgfegmcp.packages.models import (
    EVIDENCE_ARCHIVE_RECORD_NAME,
    FULL_EVIDENCE_LEARNING_PROGRESSION_ARTIFACT_NAMES,
    LP_PROVENANCE_SHARD_NAMES,
    DeclaredArtifactReference,
    LoadedGraphPackage,
    PackageValidationFinding,
)
from kgfegmcp.packages.normalization_sources import read_json_object
from kgfegmcp.packages.slim import (
    SLIM_ARTIFACT_PATHS,
    SLIM_SOURCE_NAMES,
    derive_slim_artifacts,
    evidence_archive_record_bytes,
)

# Full-evidence files whose bytes the checks read; others are only checksummed.
_READ_NAMES: Final[frozenset[str]] = frozenset(
    {
        *FULL_EVIDENCE_LEARNING_PROGRESSION_ARTIFACT_NAMES,
        *LP_PROVENANCE_SHARD_NAMES,
        *SLIM_SOURCE_NAMES,
        "nodes",
        "relationships",
    }
)
_SlimEntityDocumentT = TypeVar(
    "_SlimEntityDocumentT", SlimEntityProvenance, SlimLearningComponentProvenance
)


@dataclass(frozen=True, slots=True)
class _EvidenceFile:
    """Locate one full-evidence file for verification."""

    entry: EvidenceArchiveEntry
    name: str
    path: Path


@dataclass(frozen=True, slots=True)
class _VerifiedEvidence:
    """Hold checksum-verified full-evidence references and the bytes checks read."""

    contents: dict[str, bytes]
    findings: tuple[PackageValidationFinding, ...]
    references: tuple[DeclaredArtifactReference, ...]


def _archive_unavailable(
    *, framework_id: str, missing: Sequence[str], unreadable: Sequence[str]
) -> EvidenceArchiveUnavailableError:
    """Build the error for archived evidence that is absent or cannot be read.

    Parameters
    ----------
    framework_id
        Owning framework.
    missing
        Repository-relative local paths of absent archived files.
    unreadable
        Logical names of full-evidence files that exist but cannot be read.

    Returns
    -------
    EvidenceArchiveUnavailableError
        Error that stops acceptance without persisting a status transition.
    """

    return EvidenceArchiveUnavailableError(
        details={
            "archive_location": EVIDENCE_ARCHIVE_LOCATION,
            "framework_id": framework_id,
            "missing_count": len(missing),
            "missing_local_paths": list(missing[:20]),
            "unreadable_artifacts": list(unreadable[:20]),
            "unreadable_count": len(unreadable),
        },
        message="Archived evidence needed for acceptance is missing or unreadable.",
        recovery_hint=(
            "Restore the input set from the evidence archive and make its files "
            "readable, check it with kgfegmcp-verify-evidence-archive, then validate "
            "again."
        ),
    )


def _coverage_findings(
    package: LoadedGraphPackage,
) -> tuple[PackageValidationFinding, ...]:
    """Require slim entity provenance to cover exactly the delivered entities.

    Every delivered standard with a CASE UUID must have exactly one slim AS entry and
    every learning component exactly one slim LC entry, with no extras.

    Parameters
    ----------
    package
        Runtime-only package with decoded delivery.

    Returns
    -------
    tuple[PackageValidationFinding, ...]
        One ``slim_entity_coverage_mismatch`` finding per document that does not
        parse or does not cover exactly the delivered entities.
    """

    findings: list[PackageValidationFinding] = []
    standards = package.artifact("entityProvenance")

    if standards is not None:
        document = _slim_entity_document(
            model=SlimEntityProvenance, reference=standards
        )
        expected = {
            str(node.case_identifier_uuid)
            for node in package.item_nodes
            if node.case_identifier_uuid is not None
        }

        # A document that does not parse cannot show coverage; the derivation check
        # reports its byte difference separately.
        if document is None or set(document.items) != expected:
            findings.append(
                _finding(code="slim_entity_coverage_mismatch", name="entityProvenance")
            )

    components = package.artifact("learningComponentProvenance")

    if components is not None:
        lc_document = _slim_entity_document(
            model=SlimLearningComponentProvenance, reference=components
        )

        if lc_document is None or set(lc_document.learning_components) != {
            str(node.node_id) for node in package.learning_component_nodes
        }:
            findings.append(
                _finding(
                    code="slim_entity_coverage_mismatch",
                    name="learningComponentProvenance",
                )
            )

    return tuple(findings)


def _derivation_findings(
    *,
    contents: Mapping[str, bytes],
    package: LoadedGraphPackage,
    record: EvidenceArchiveRecord,
    record_bytes: bytes,
) -> tuple[PackageValidationFinding, ...]:
    """Require every slim artifact and the record to equal their derivations.

    Parameters
    ----------
    contents
        Verified full-evidence bytes.
    package
        Runtime-only package.
    record
        Parsed evidence archive record.
    record_bytes
        Exact declared record bytes.

    Returns
    -------
    tuple[PackageValidationFinding, ...]
        One ``slim_derivation_mismatch`` finding per differing artifact.
    """

    try:
        derived = derive_slim_artifacts(contents)
    except ManifestBuildError:
        return (_finding(code="slim_derivation_mismatch", name=None),)

    declared = {
        str(reference.logical_name)
        for reference in package.artifacts
        if str(reference.logical_name) in SLIM_ARTIFACT_PATHS
    }
    findings = [
        _finding(code="slim_derivation_mismatch", name=name)
        for name in sorted(declared ^ set(derived))
    ]

    for name in sorted(declared & set(derived)):
        reference = package.artifact(name)

        if reference is None or reference.resolved_path.read_bytes() != derived[name]:
            findings.append(_finding(code="slim_derivation_mismatch", name=name))

    expected_record = evidence_archive_record_bytes(
        evidence_artifacts=record.evidence_artifacts, framework_id=record.framework_id
    )

    if expected_record != record_bytes:
        findings.append(
            _finding(code="slim_derivation_mismatch", name=EVIDENCE_ARCHIVE_RECORD_NAME)
        )

    return tuple(findings)


def _evidence_files(
    *,
    package: LoadedGraphPackage,
    project_dir: Path,
    record: EvidenceArchiveRecord,
) -> tuple[_EvidenceFile, ...]:
    """Locate every full-evidence file and require archived ones to be present.

    Carried files are read from the package; archive-only files from their
    repository-relative local paths.

    Parameters
    ----------
    package
        Runtime-only package.
    project_dir
        Repository root that local paths are relative to.
    record
        Parsed evidence archive record.

    Returns
    -------
    tuple[_EvidenceFile, ...]
        Every full-evidence file, ordered by logical name.

    Raises
    ------
    EvidenceArchiveUnavailableError
        If any archive-only file is absent, so acceptance cannot conclude.
    """

    files: list[_EvidenceFile] = []
    missing: list[str] = []

    for name, entry in sorted(record.evidence_artifacts.items()):
        reference = package.artifact(name) if entry.runtime else None
        path = (
            reference.resolved_path
            if reference is not None
            else project_dir / str(entry.local_path)
        )

        if not path.is_file():
            missing.append(str(entry.local_path))

        files.append(_EvidenceFile(entry=entry, name=name, path=path))

    if missing:
        raise _archive_unavailable(
            framework_id=str(record.framework_id), missing=missing, unreadable=()
        )

    return tuple(files)


def _finding(*, code: str, name: str | None) -> PackageValidationFinding:
    """Build one blocking evidence-tier finding.

    Parameters
    ----------
    code
        Stable finding code.
    name
        Affected logical artifact name, when known.

    Returns
    -------
    PackageValidationFinding
        Error-severity finding.
    """

    return PackageValidationFinding(
        artifact_name=name,
        code=code,
        message="Archived evidence fails an independent package acceptance check.",
    )


def _measure(evidence_file: _EvidenceFile) -> tuple[bytes | None, Sha256Digest, int]:
    """Read or stream one full-evidence file and return its bytes, hash and size.

    Parameters
    ----------
    evidence_file
        Located full-evidence file.

    Returns
    -------
    tuple[bytes | None, Sha256Digest, int]
        The bytes when the checks read this file (``None`` when it is only
        checksummed), its SHA-256 and its size.

    Raises
    ------
    OSError
        If the file cannot be read.
    """

    if evidence_file.name in _READ_NAMES:
        content = evidence_file.path.read_bytes()
        return content, calculate_bytes_sha256(content), len(content)

    return (
        None,
        calculate_file_sha256(evidence_file.path),
        evidence_file.path.stat().st_size,
    )


def _slim_entity_document(
    *, model: type[_SlimEntityDocumentT], reference: DeclaredArtifactReference
) -> _SlimEntityDocumentT | None:
    """Parse one slim entity provenance document for the coverage check.

    The runtime tier only checksums these documents, so a malformed one is first
    parsed here and must become a finding rather than an exception.

    Parameters
    ----------
    model
        Slim contract the document must satisfy.
    reference
        Declared slim ``entityProvenance`` or ``learningComponentProvenance``.

    Returns
    -------
    _SlimEntityDocumentT | None
        The parsed document, or ``None`` when it is not a JSON object matching its
        slim contract.
    """

    try:
        return model.model_validate(
            read_json_object(
                data=reference.resolved_path.read_bytes(),
                label=str(reference.logical_name),
            )
        )
    except (ManifestBuildError, ValidationError):
        return None


def _verify_files(
    *, files: tuple[_EvidenceFile, ...], framework_id: str
) -> _VerifiedEvidence:
    """Check each full-evidence file's size and SHA-256 against the record.

    Parameters
    ----------
    files
        Located full-evidence files.
    framework_id
        Owning framework, for the unavailable-archive error.

    Returns
    -------
    _VerifiedEvidence
        Verified references, the bytes the checks read, and mismatch findings.

    Raises
    ------
    EvidenceArchiveUnavailableError
        If any file exists but cannot be read, so acceptance cannot conclude.
    """

    contents: dict[str, bytes] = {}
    findings: list[PackageValidationFinding] = []
    references: list[DeclaredArtifactReference] = []
    unreadable: list[str] = []

    for evidence_file in files:
        try:
            content, sha256, size_bytes = _measure(evidence_file)
        except OSError:
            unreadable.append(evidence_file.name)
            continue

        if content is not None:
            contents[evidence_file.name] = content

        entry = evidence_file.entry

        if sha256 != entry.sha256 or size_bytes != entry.size_bytes:
            findings.append(
                _finding(
                    code="evidence_archive_checksum_mismatch", name=evidence_file.name
                )
            )

        references.append(
            DeclaredArtifactReference(
                logical_name=evidence_file.name,
                package_path=entry.package_path,
                resolved_path=evidence_file.path,
                sha256=sha256,
                size_bytes=size_bytes,
            )
        )

    if unreadable:
        raise _archive_unavailable(
            framework_id=framework_id, missing=(), unreadable=unreadable
        )

    return _VerifiedEvidence(
        contents=contents, findings=tuple(findings), references=tuple(references)
    )


def _view(
    *,
    contents: Mapping[str, bytes],
    package: LoadedGraphPackage,
    references: tuple[DeclaredArtifactReference, ...],
) -> FullEvidenceView:
    """Assemble the in-memory full-evidence view from verified evidence.

    Parameters
    ----------
    contents
        Verified bytes the full LP checks read.
    package
        Runtime-only package supplying decoded delivery and counts.
    references
        Verified full-evidence references.

    Returns
    -------
    FullEvidenceView
        View in the full-evidence namespace; never persisted.
    """

    manifest = package.manifest
    return FullEvidenceView(
        artifacts=references,
        builds_towards_relationships=manifest.counts.builds_towards_relationships,
        contents=contents,
        framework_id=manifest.framework_id,
        framework_root=package.framework_root,
        included_graph_types=manifest.included_graph_types,
        item_nodes=package.item_nodes,
        relates_to_relationships=manifest.counts.relates_to_relationships,
        relationships=package.relationships,
    )


@dataclass(frozen=True, slots=True)
class EvidenceVerifier:
    """Verify runtime-only packages against archived evidence under one repository."""

    project_dir: Path

    def verify(
        self,
        *,
        captured_contents: Mapping[str, bytes],
        package: LoadedGraphPackage,
        runtime_evidence: LearningProgressionEvidence | None,
    ) -> tuple[PackageValidationFinding, ...]:
        """Run the evidence tier for one package that passed the runtime tier.

        Parameters
        ----------
        captured_contents
            Loader-verified runtime bytes, including the evidence archive record.
        package
            Runtime-only package that passed the runtime tier.
        runtime_evidence
            Projections the runtime tier built from the slim artifacts.

        Returns
        -------
        tuple[PackageValidationFinding, ...]
            Blocking findings; empty when the archived evidence fully supports the
            package.

        Raises
        ------
        EvidenceArchiveUnavailableError
            If any archive-only file is absent.

        Examples
        --------
        >>> EvidenceVerifier(project_dir=repo).verify(
        ...     captured_contents=verified_bytes,
        ...     package=runtime_package,
        ...     runtime_evidence=projections,
        ... )
        ()
        """

        record_bytes = captured_contents[EVIDENCE_ARCHIVE_RECORD_NAME]

        try:
            record = EvidenceArchiveRecord.model_validate(
                read_json_object(data=record_bytes, label="evidence record")
            )
        except (ManifestBuildError, ValidationError):
            return (_finding(code="evidence_record_shape", name=None),)

        verified = _verify_files(
            files=_evidence_files(
                package=package, project_dir=self.project_dir, record=record
            ),
            framework_id=str(record.framework_id),
        )

        if verified.findings:
            return verified.findings

        full_evidence, lp_findings = validate_learning_progression_evidence(
            view=_view(
                contents=verified.contents,
                package=package,
                references=verified.references,
            )
        )

        if lp_findings:
            return lp_findings

        findings = [
            *_derivation_findings(
                contents=verified.contents,
                package=package,
                record=record,
                record_bytes=record_bytes,
            ),
            *_coverage_findings(package),
        ]

        if full_evidence != runtime_evidence:
            findings.append(_finding(code="slim_projection_mismatch", name=None))

        return tuple(findings)
