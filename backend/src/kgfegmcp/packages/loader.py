"""This module loads graph packages through established manifests, profiles, checksums,
and decoders.

This module converts a safely discovered package candidate into an immutable loaded
package aggregate. It parses the package through the existing ``GraphPackageManifest``,
resolves the exact versioned curriculum profile, verifies the profile checksum, and
safely resolves every delivery, detailed, and additional artifact declared by the
manifest.

The loader verifies exact packaged-byte checksums, rejects missing, undeclared, or
unsafe package content, and confirms that the verified artifact set reproduces the
manifest snapshot identity. Delivery artifacts are decoded exclusively through the
existing graph-record decoder. When declared, the supported detailed validation report
is parsed into its PR 4 report model; other detailed artifacts are preserved without
introducing new artifact schemas.

Loading produces structured findings instead of repairing files or changing package
state. This module does not enforce graph topology, reachability, profile parent rules,
capabilities, or package-wide semantic correctness. It also does not persist validation
status, build reusable graph indexes, or expose traversal services.
"""

# Future Library
from __future__ import annotations

# Standard Library
import json
import os
import stat

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Final

# Third Party Library
from pydantic import TypeAdapter, ValidationError

# Package Library
from kgfegmcp.domain.enums import GraphType
from kgfegmcp.domain.identifiers import (
    ArtifactName,
    ArtifactPath,
    Sha256Digest,
    SnapshotVersionToken,
    build_snapshot_id,
)
from kgfegmcp.errors import (
    DeliveryPropertyDecodingError,
    JSONLParsingError,
    PackageValidationError,
    ProfileValidationError,
)
from kgfegmcp.graph.models import FrameworkNode, StandardNode
from kgfegmcp.packages.checksums import (
    calculate_file_sha256,
    calculate_snapshot_artifact_set_sha256,
)
from kgfegmcp.packages.decoder import (
    iter_decoded_nodes,
    iter_decoded_relationships,
)
from kgfegmcp.packages.models import (
    SUPPORTED_PACKAGE_REVISION,
    DeclaredArtifactReference,
    DetailedValidationReport,
    GraphPackageManifest,
    LoadedGraphPackage,
    PackageValidationFinding,
)
from kgfegmcp.packages.repository import (
    PACKAGE_MANIFEST_FILENAME,
    GraphPackageCandidate,
    GraphPackageRepository,
)
from kgfegmcp.profiles.loader import LoadedProfile
from kgfegmcp.profiles.repository import ProfileRepository

_ARTIFACT_NAME_ADAPTER: TypeAdapter[ArtifactName] = TypeAdapter(ArtifactName)
_BLOCKING_FINDING_CODES: Final[frozenset[str]] = frozenset(
    {
        "artifact_manifest_collision",
        "artifact_name_case_collision",
        "artifact_path_case_collision",
        "artifact_symlink_rejected",
        "artifact_missing",
        "artifact_path_escape",
        "artifact_unreadable",
        "artifact_not_regular_file",
        "graph_type_unsupported",
        "included_graph_types_unsupported",
        "manifest_framework_directory_mismatch",
        "manifest_snapshot_directory_mismatch",
        "package_declared_file_missing",
        "package_entry_unreadable",
        "package_candidate_changed",
        "package_candidate_identity_mismatch",
        "package_candidate_symlink_rejected",
        "package_candidate_unavailable",
        "package_path_case_collision",
        "package_revision_unsupported",
        "package_special_entry_rejected",
        "package_symlink_rejected",
        "package_tree_unreadable",
        "package_undeclared_directory",
        "package_undeclared_file",
        "profile_checksum_mismatch",
        "profile_load_failed",
        "snapshot_checksum_identity_mismatch",
        "snapshot_identity_unverifiable",
    }
)
_MANIFEST_LOGICAL_NAME: Final[str] = "packageManifest"
_MANIFEST_VERSION_FINDINGS: Final[tuple[tuple[frozenset[str], str, str], ...]] = (
    (
        frozenset({"manifestVersion", "manifest_version"}),
        "manifest_version_unsupported",
        "The package manifest version is unsupported.",
    ),
    (
        frozenset({"sourceSchemaVersion", "source_schema_version"}),
        "source_schema_version_unsupported",
        "The package source schema version is unsupported.",
    ),
    (
        frozenset({"deliverySchemaVersion", "delivery_schema_version"}),
        "delivery_schema_version_unsupported",
        "The package delivery schema version is unsupported.",
    ),
)
_SNAPSHOT_VERSION_TOKEN_ADAPTER: TypeAdapter[SnapshotVersionToken] = TypeAdapter(
    SnapshotVersionToken
)


@dataclass(frozen=True, slots=True)
class _ArtifactVerificationResult:
    """Hold declared-artifact verification references, checksums, and findings."""

    checksums: list[Sha256Digest]
    findings: list[PackageValidationFinding]
    integrity_failed: bool
    references: list[DeclaredArtifactReference]


@dataclass(frozen=True, slots=True)
class _ClassifiedTreeEntry:
    """Hold the classification outcome for one enumerated package-tree entry."""

    descend_path: Path | None = None
    directory_path: str | None = None
    file_path: str | None = None
    finding: PackageValidationFinding | None = None


@dataclass(frozen=True, slots=True)
class _DecodedDelivery:
    """Hold the decoded delivery graph split into its framework root and members."""

    framework_root: FrameworkNode
    item_nodes: tuple[StandardNode, ...]
    relationships: tuple[object, ...]


@dataclass(frozen=True, slots=True)
class GraphPackageLoader:
    """Verify and decode package candidates without persisting validation state."""

    profile_repository: ProfileRepository
    repository: GraphPackageRepository

    def _load_manifest(
        self, candidate: GraphPackageCandidate
    ) -> tuple[
        GraphPackageManifest | None, bytes | None, list[PackageValidationFinding]
    ]:
        """Read and validate one existing package manifest.

        Parameters
        ----------
        candidate
            Safely discovered package candidate.

        Returns
        -------
        tuple[GraphPackageManifest | None, bytes | None, list[PackageValidationFinding]]
            Manifest model, exact bytes, and any load findings.
        """

        manifest_path = candidate.manifest_path
        findings: list[PackageValidationFinding] = []

        if manifest_path.is_symlink():
            findings.append(
                _finding(
                    artifact_name=_ARTIFACT_NAME_ADAPTER.validate_python(
                        _MANIFEST_LOGICAL_NAME
                    ),
                    code="manifest_symlink_rejected",
                    details={"manifest_path": str(manifest_path)},
                    message="The package manifest may not be a symbolic link.",
                )
            )
            return None, None, findings

        try:
            manifest_bytes = _read_regular_file(manifest_path)
        except (OSError, ValueError) as error:
            findings.append(
                _finding(
                    artifact_name=_ARTIFACT_NAME_ADAPTER.validate_python(
                        _MANIFEST_LOGICAL_NAME
                    ),
                    code="manifest_unreadable",
                    details={"manifest_path": str(manifest_path), "reason": str(error)},
                    message="The package manifest is missing or unreadable.",
                )
            )
            return None, None, findings

        manifest_object: dict[str, object] | None = None

        try:
            manifest_object = _parse_json_object(manifest_bytes)
            manifest = GraphPackageManifest.model_validate(manifest_object)
        except (ValueError, ValidationError) as error:
            findings.append(
                _manifest_error_finding(
                    error=error,
                    manifest_object=manifest_object,
                    manifest_path=manifest_path,
                )
            )
            return None, manifest_bytes, findings

        findings.extend(
            _manifest_semantic_findings(candidate=candidate, manifest=manifest)
        )
        return manifest, manifest_bytes, findings

    def _load_profile(
        self, *, manifest: GraphPackageManifest
    ) -> tuple[LoadedProfile | None, list[PackageValidationFinding]]:
        """Load and checksum the manifest-referenced curriculum profile.

        Parameters
        ----------
        manifest
            Validated manifest naming the required profile and its checksum.

        Returns
        -------
        tuple[LoadedProfile | None, list[PackageValidationFinding]]
            The loaded profile when available and any profile-stage findings.
        """

        findings: list[PackageValidationFinding] = []

        try:
            loaded_profile = self.profile_repository.load(
                profile_id=manifest.profile.profile_id,
                profile_version=manifest.profile.profile_version,
            )
        except ProfileValidationError as error:
            findings.append(_profile_load_finding(error))
            return None, findings

        if loaded_profile.sha256 != manifest.profile.sha256:
            findings.append(
                _finding(
                    code="profile_checksum_mismatch",
                    details={
                        "actual_sha256": str(loaded_profile.sha256),
                        "expected_sha256": str(manifest.profile.sha256),
                        "profile_path": str(loaded_profile.path),
                    },
                    message="The exact curriculum-profile checksum does not match the manifest.",
                )
            )

        return loaded_profile, findings

    def _resolve_candidate(
        self, candidate: GraphPackageCandidate
    ) -> tuple[GraphPackageCandidate, GraphPackageLoadResult | None]:
        """Rediscover and revalidate a candidate before any content is read.

        Parameters
        ----------
        candidate
            Caller-supplied package candidate.

        Returns
        -------
        tuple[GraphPackageCandidate, GraphPackageLoadResult | None]
            The repository-confirmed candidate and ``None`` when loading may proceed,
            or the original candidate and a finished blocking result.
        """

        try:
            discovered_candidate = self.repository.candidate(
                framework_id=candidate.framework_id, snapshot_id=candidate.snapshot_id
            )
        except PackageValidationError as error:
            return candidate, GraphPackageLoadResult(
                candidate=candidate,
                findings=(
                    _finding(
                        code="package_candidate_not_discoverable",
                        details=dict(error.details),
                        message="The package candidate is not safely discoverable beneath the configured root.",
                    ),
                ),
            )

        if discovered_candidate.package_path != candidate.package_path:
            return candidate, GraphPackageLoadResult(
                candidate=candidate,
                findings=(
                    _finding(
                        code="package_candidate_outside_repository",
                        details={
                            "candidate_path": str(candidate.package_path),
                            "discovered_path": str(discovered_candidate.package_path),
                        },
                        message="The package candidate does not match its configured repository location.",
                    ),
                ),
            )

        candidate_finding = _validate_candidate_location(discovered_candidate)

        if candidate_finding is not None:
            return discovered_candidate, GraphPackageLoadResult(
                candidate=discovered_candidate, findings=(candidate_finding,)
            )

        return discovered_candidate, None

    def load(self, candidate: GraphPackageCandidate) -> GraphPackageLoadResult:
        """Load one candidate through all package-integrity boundaries.

        Parameters
        ----------
        candidate
            Safely discovered package candidate.

        Returns
        -------
        GraphPackageLoadResult
            Exact manifest context, structured findings, and an immutable loaded
            package when integrity and decoding permit assembly.
        """

        candidate, early_result = self._resolve_candidate(candidate)

        if early_result is not None:
            return early_result

        manifest, manifest_bytes, findings = self._load_manifest(candidate)

        if manifest is None or manifest_bytes is None:
            return _blocked_result(
                candidate=candidate,
                findings=findings,
                manifest=manifest,
                manifest_bytes=manifest_bytes,
            )

        declared_artifacts = manifest.artifacts.declared_artifacts()
        declared_paths = tuple(str(path) for path in declared_artifacts.values())
        findings.extend(
            _artifact_declaration_findings(
                declared_artifacts=declared_artifacts, declared_paths=declared_paths
            )
        )
        findings.extend(
            _package_tree_findings(
                declared_paths=declared_paths, package_root=candidate.package_path
            )
        )

        loaded_profile, profile_findings = self._load_profile(manifest=manifest)
        findings.extend(profile_findings)

        verification = _verify_declared_artifacts(
            candidate=candidate,
            declared_artifacts=declared_artifacts,
            manifest=manifest,
        )
        findings.extend(verification.findings)
        artifact_references = verification.references
        artifact_integrity_failed = verification.integrity_failed

        if len(verification.checksums) == len(declared_artifacts):
            snapshot_findings, snapshot_failed = _snapshot_identity_findings(
                candidate=candidate, checksums=verification.checksums, manifest=manifest
            )
            findings.extend(snapshot_findings)
            artifact_integrity_failed = artifact_integrity_failed or snapshot_failed

        loaded_report, report_findings = _validation_report(artifact_references)
        findings.extend(report_findings)

        if (
            artifact_integrity_failed
            or any(finding.code in _BLOCKING_FINDING_CODES for finding in findings)
            or loaded_profile is None
        ):
            return _blocked_result(
                candidate=candidate,
                findings=findings,
                manifest=manifest,
                manifest_bytes=manifest_bytes,
            )

        delivery, delivery_findings = _decode_delivery(artifact_references)
        findings.extend(delivery_findings)

        if delivery is None:
            return _blocked_result(
                candidate=candidate,
                findings=findings,
                manifest=manifest,
                manifest_bytes=manifest_bytes,
            )

        loaded_package = LoadedGraphPackage(
            artifacts=tuple(artifact_references),
            framework_root=delivery.framework_root,
            item_nodes=delivery.item_nodes,
            manifest=manifest,
            manifest_bytes=manifest_bytes,
            manifest_path=candidate.manifest_path,
            package_root=candidate.package_path,
            profile=loaded_profile.profile,
            profile_path=loaded_profile.path,
            profile_sha256=loaded_profile.sha256,
            relationships=delivery.relationships,
            validation_report=loaded_report,
        )
        return GraphPackageLoadResult(
            candidate=candidate,
            findings=tuple(findings),
            loaded_package=loaded_package,
            manifest=manifest,
            manifest_bytes=manifest_bytes,
        )


@dataclass(frozen=True, slots=True)
class GraphPackageLoadResult:
    """Return package integrity findings and any successfully loaded aggregate."""

    candidate: GraphPackageCandidate
    findings: tuple[PackageValidationFinding, ...]
    loaded_package: LoadedGraphPackage | None = None
    manifest: GraphPackageManifest | None = None
    manifest_bytes: bytes | None = None


def _artifact_declaration_findings(
    *, declared_artifacts: Mapping[str, ArtifactPath], declared_paths: tuple[str, ...]
) -> list[PackageValidationFinding]:
    """Detect case collisions and manifest overlap among declared artifacts.

    Parameters
    ----------
    declared_artifacts
        Mapping of logical artifact names to their package-relative paths.
    declared_paths
        String forms of the declared artifact paths, in declaration order.

    Returns
    -------
    list[PackageValidationFinding]
        Findings for name collisions, path collisions, and manifest overlap.
    """

    findings: list[PackageValidationFinding] = []
    logical_names = tuple(declared_artifacts)
    logical_names_casefolded = tuple(name.casefold() for name in logical_names)

    if len(logical_names_casefolded) != len(set(logical_names_casefolded)):
        findings.append(
            _finding(
                code="artifact_name_case_collision",
                details={"artifact_names": logical_names},
                message="Declared artifact names have a case-insensitive collision.",
            )
        )

    declared_paths_casefolded = tuple(path.casefold() for path in declared_paths)

    if len(declared_paths_casefolded) != len(set(declared_paths_casefolded)):
        findings.append(
            _finding(
                code="artifact_path_case_collision",
                details={"artifact_paths": declared_paths},
                message="Declared artifact paths have a case-insensitive collision.",
            )
        )

    if PACKAGE_MANIFEST_FILENAME.casefold() in set(declared_paths_casefolded):
        findings.append(
            _finding(
                code="artifact_manifest_collision",
                details={"artifact_paths": declared_paths},
                message="A declared artifact collides with the package manifest path.",
            )
        )

    return findings


def _artifact_path(
    *, package_root: Path, package_path: ArtifactPath
) -> tuple[Path | None, PackageValidationFinding | None]:
    """Resolve one declared artifact beneath the package root without symlinks.

    Parameters
    ----------
    package_root
        Safely discovered package root.
    package_path
        Validated package-relative POSIX artifact path.

    Returns
    -------
    tuple[Path | None, PackageValidationFinding | None]
        Safe resolved file path or one structured failure.
    """

    descendant = package_root

    for part in PurePosixPath(str(package_path)).parts:
        descendant = descendant / part

        if descendant.is_symlink():
            return None, _finding(
                code="artifact_symlink_rejected",
                details={
                    "artifact_path": str(package_path),
                    "entry_path": str(descendant),
                },
                message=f"Declared artifact '{package_path}' may not traverse a symbolic link.",
            )

    try:
        resolved_path = descendant.resolve(strict=True)
    except OSError as error:
        return None, _finding(
            code="artifact_missing",
            details={
                "artifact_path": str(package_path),
                "entry_path": str(descendant),
                "reason": str(error),
            },
            message=f"Declared artifact '{package_path}' is missing or unreadable.",
        )

    if not resolved_path.is_relative_to(package_root):
        return None, _finding(
            code="artifact_path_escape",
            details={
                "artifact_path": str(package_path),
                "resolved_path": str(resolved_path),
            },
            message=f"Declared artifact '{package_path}' escapes the package root.",
        )

    try:
        file_stat = resolved_path.stat(follow_symlinks=False)
    except OSError as error:
        return None, _finding(
            code="artifact_unreadable",
            details={
                "artifact_path": str(package_path),
                "reason": str(error),
                "resolved_path": str(resolved_path),
            },
            message=f"Declared artifact '{package_path}' could not be inspected.",
        )

    if not stat.S_ISREG(file_stat.st_mode):
        return None, _finding(
            code="artifact_not_regular_file",
            details={
                "artifact_path": str(package_path),
                "resolved_path": str(resolved_path),
            },
            message=f"Declared artifact '{package_path}' is not a regular file.",
        )

    return resolved_path, None


def _blocked_result(
    *,
    candidate: GraphPackageCandidate,
    findings: list[PackageValidationFinding],
    manifest: GraphPackageManifest | None,
    manifest_bytes: bytes | None,
) -> GraphPackageLoadResult:
    """Build a blocking load result that carries manifest context but no package.

    Parameters
    ----------
    candidate
        Repository-confirmed package candidate.
    findings
        Accumulated findings explaining why assembly was blocked.
    manifest
        Validated manifest when one was parsed, otherwise ``None``.
    manifest_bytes
        Exact manifest bytes when the manifest was read, otherwise ``None``.

    Returns
    -------
    GraphPackageLoadResult
        Result with frozen findings and no loaded package.
    """

    return GraphPackageLoadResult(
        candidate=candidate,
        findings=tuple(findings),
        manifest=manifest,
        manifest_bytes=manifest_bytes,
    )


def _case_collision_finding(
    *, casefold_entries: dict[str, str], relative_path: str
) -> PackageValidationFinding | None:
    """Record one package-relative path and report a case-insensitive collision.

    Parameters
    ----------
    casefold_entries
        Mutable mapping of casefolded paths to their first-seen original path.
    relative_path
        Package-relative POSIX path of the current entry.

    Returns
    -------
    PackageValidationFinding | None
        One collision finding when a differently-cased sibling already exists,
        otherwise ``None``.
    """

    casefold_path = relative_path.casefold()
    previous_path = casefold_entries.get(casefold_path)

    if previous_path is not None and previous_path != relative_path:
        return _finding(
            code="package_path_case_collision",
            details={"first_path": previous_path, "second_path": relative_path},
            message="Package content has a case-insensitive path collision.",
        )

    casefold_entries[casefold_path] = relative_path
    return None


def _classify_tree_entry(
    *, entry: os.DirEntry[str], relative_path: str
) -> _ClassifiedTreeEntry:
    """Classify one directory entry as a file, directory, or rejected entry.

    Parameters
    ----------
    entry
        Directory entry produced by ``os.scandir``.
    relative_path
        Package-relative POSIX path of the entry.

    Returns
    -------
    _ClassifiedTreeEntry
        Classification carrying at most one populated destination or finding.
    """

    entry_path = Path(entry.path)

    try:
        is_directory = entry.is_dir(follow_symlinks=False)
        is_file = entry.is_file(follow_symlinks=False)
        is_symlink = entry.is_symlink()
    except OSError as error:
        return _ClassifiedTreeEntry(
            finding=_finding(
                code="package_entry_unreadable",
                details={"entry_path": str(entry_path), "reason": str(error)},
                message=f"Package entry '{relative_path}' could not be inspected safely.",
            )
        )

    if is_symlink:
        return _ClassifiedTreeEntry(
            finding=_finding(
                code="package_symlink_rejected",
                details={"entry_path": str(entry_path)},
                message=f"Package entry '{relative_path}' may not be a symbolic link.",
            )
        )

    if is_directory:
        return _ClassifiedTreeEntry(
            descend_path=entry_path, directory_path=relative_path
        )

    if is_file:
        return _ClassifiedTreeEntry(file_path=relative_path)

    return _ClassifiedTreeEntry(
        finding=_finding(
            code="package_special_entry_rejected",
            details={"entry_path": str(entry_path)},
            message=f"Package entry '{relative_path}' is not a regular file or directory.",
        )
    )


def _collect_package_tree(
    package_root: Path,
) -> tuple[set[str], set[str], tuple[PackageValidationFinding, ...]]:
    """Enumerate a package tree without following symbolic links.

    Parameters
    ----------
    package_root
        Safely discovered package root.

    Returns
    -------
    tuple[set[str], set[str], tuple[PackageValidationFinding, ...]]
        Regular files, regular directories, and unsafe-entry findings.
    """

    directories: set[str] = set()
    files: set[str] = set()
    findings: list[PackageValidationFinding] = []
    pending_directories = [package_root]
    casefold_entries: dict[str, str] = {}

    while pending_directories:
        directory = pending_directories.pop()
        entries, scan_finding = _scan_directory(directory)

        if scan_finding is not None:
            findings.append(scan_finding)
            continue

        for entry in entries:
            relative_path = Path(entry.path).relative_to(package_root).as_posix()
            collision_finding = _case_collision_finding(
                casefold_entries=casefold_entries, relative_path=relative_path
            )

            if collision_finding is not None:
                findings.append(collision_finding)

            classified = _classify_tree_entry(entry=entry, relative_path=relative_path)

            if classified.finding is not None:
                findings.append(classified.finding)

            if classified.directory_path is not None:
                directories.add(classified.directory_path)

            if classified.descend_path is not None:
                pending_directories.append(classified.descend_path)

            if classified.file_path is not None:
                files.add(classified.file_path)

    return files, directories, tuple(findings)


def _decode_delivery(
    references: list[DeclaredArtifactReference],
) -> tuple[_DecodedDelivery | None, list[PackageValidationFinding]]:
    """Decode delivery nodes and relationships and isolate the framework root.

    Parameters
    ----------
    references
        Verified declared-artifact references including nodes and relationships.

    Returns
    -------
    tuple[_DecodedDelivery | None, list[PackageValidationFinding]]
        The decoded delivery when acceptable and any decoding-stage findings.
    """

    findings: list[PackageValidationFinding] = []
    nodes_reference = next(
        reference for reference in references if str(reference.logical_name) == "nodes"
    )
    relationships_reference = next(
        reference
        for reference in references
        if str(reference.logical_name) == "relationships"
    )

    try:
        decoded_nodes = tuple(iter_decoded_nodes(nodes_reference.resolved_path))
        relationships = tuple(
            iter_decoded_relationships(relationships_reference.resolved_path)
        )
    except (DeliveryPropertyDecodingError, JSONLParsingError) as error:
        findings.append(
            _finding(
                code=error.error_code,
                details=dict(error.details),
                message=error.message,
            )
        )
        return None, findings

    framework_roots = tuple(
        node for node in decoded_nodes if isinstance(node, FrameworkNode)
    )
    item_nodes = tuple(node for node in decoded_nodes if isinstance(node, StandardNode))

    if len(framework_roots) != 1:
        findings.append(
            _finding(
                artifact_name=nodes_reference.logical_name,
                code="framework_root_count_invalid",
                details={"framework_root_count": len(framework_roots)},
                message="The delivery nodes must contain exactly one framework root.",
            )
        )
        return None, findings

    return (
        _DecodedDelivery(
            framework_root=framework_roots[0],
            item_nodes=item_nodes,
            relationships=relationships,
        ),
        findings,
    )


def _expected_directories(expected_files: set[str]) -> set[str]:
    """Derive every directory required by the expected package files.

    Parameters
    ----------
    expected_files
        Package-relative expected file paths.

    Returns
    -------
    set[str]
        Package-relative ancestor directories.
    """

    directories: set[str] = set()

    for file_path in expected_files:
        parent = PurePosixPath(file_path).parent

        while str(parent) != ".":
            directories.add(parent.as_posix())
            parent = parent.parent

    return directories


def _finding(
    *,
    artifact_name: ArtifactName | None = None,
    code: str,
    details: dict[str, object] | None = None,
    message: str,
    record_id: str | None = None,
    source_export_order: int | None = None,
) -> PackageValidationFinding:
    """Construct one error finding with safe public and private diagnostic fields.

    Parameters
    ----------
    artifact_name
        Optional logical artifact name.
    code
        Stable machine-readable finding code.
    details
        Optional private diagnostic values, including internal paths.
    message
        Safe public message.
    record_id
        Optional source record identifier.
    source_export_order
        Optional one-based source order.

    Returns
    -------
    PackageValidationFinding
        Immutable error finding.
    """

    return PackageValidationFinding(
        artifact_name=artifact_name,
        code=code,
        details=details or {},
        message=message,
        record_id=record_id,
        severity="error",
        source_export_order=source_export_order,
    )


def _manifest_error_finding(
    *,
    error: ValueError | ValidationError,
    manifest_object: dict[str, object] | None,
    manifest_path: Path,
) -> PackageValidationFinding:
    """Build one finding describing why a manifest failed to parse or validate.

    Parameters
    ----------
    error
        Parsing or schema-validation error raised while loading the manifest.
    manifest_object
        Parsed manifest object when JSON decoding succeeded, otherwise ``None``.
    manifest_path
        Filesystem path of the manifest under inspection.

    Returns
    -------
    PackageValidationFinding
        Error finding with the most specific available code and message.
    """

    details: dict[str, object] = {
        "manifest_path": str(manifest_path),
        "reason": str(error),
    }
    finding_code = "manifest_invalid"
    finding_message = "The package manifest does not satisfy its established contract."

    if isinstance(error, ValidationError):
        validation_errors = error.errors(include_input=False, include_url=False)
        details["validation_errors"] = validation_errors
        error_fields = {
            str(validation_error["loc"][0])
            for validation_error in validation_errors
            if validation_error.get("loc")
        }

        for field_names, code, message in _MANIFEST_VERSION_FINDINGS:
            if field_names.intersection(error_fields):
                finding_code = code
                finding_message = message
                break

        raw_package_revision = _raw_package_revision(manifest_object)

        if (
            finding_code == "manifest_invalid"
            and raw_package_revision is not None
            and raw_package_revision != SUPPORTED_PACKAGE_REVISION
        ):
            finding_code = "package_revision_unsupported"
            finding_message = "The package revision is unsupported by PR 4."

    return _finding(
        artifact_name=_ARTIFACT_NAME_ADAPTER.validate_python(_MANIFEST_LOGICAL_NAME),
        code=finding_code,
        details=details,
        message=finding_message,
    )


def _manifest_semantic_findings(
    *, candidate: GraphPackageCandidate, manifest: GraphPackageManifest
) -> list[PackageValidationFinding]:
    """Check a validated manifest against directory identity.

    Parameters
    ----------
    candidate
        Safely discovered package candidate the manifest was read from.
    manifest
        Successfully validated manifest model.

    Returns
    -------
    list[PackageValidationFinding]
        Zero or more findings for identity mismatches and unsupported content.
    """

    findings: list[PackageValidationFinding] = []

    if manifest.framework_id != candidate.framework_id:
        findings.append(
            _finding(
                code="manifest_framework_directory_mismatch",
                details={
                    "directory_framework_id": str(candidate.framework_id),
                    "manifest_framework_id": str(manifest.framework_id),
                },
                message="The manifest framework ID disagrees with its package directory.",
            )
        )

    if manifest.snapshot_id != candidate.snapshot_id:
        findings.append(
            _finding(
                code="manifest_snapshot_directory_mismatch",
                details={
                    "directory_snapshot_id": str(candidate.snapshot_id),
                    "manifest_snapshot_id": str(manifest.snapshot_id),
                },
                message="The manifest snapshot ID disagrees with its package directory.",
            )
        )

    if manifest.package_revision != SUPPORTED_PACKAGE_REVISION:
        findings.append(
            _finding(
                code="package_revision_unsupported",
                details={"package_revision": manifest.package_revision},
                message=(
                    f"Package revision {manifest.package_revision} is not supported by "
                    f"this package loader."
                ),
            )
        )

    if manifest.graph_type is not GraphType.ACADEMIC_STANDARDS:
        findings.append(
            _finding(
                code="graph_type_unsupported",
                details={"graph_type": manifest.graph_type.value},
                message="The package graph type is not supported by PR 4 validation.",
            )
        )

    if manifest.included_graph_types != (GraphType.ACADEMIC_STANDARDS,):
        findings.append(
            _finding(
                code="included_graph_types_unsupported",
                details={
                    "included_graph_types": tuple(
                        graph_type.value for graph_type in manifest.included_graph_types
                    )
                },
                message="The package includes graph types unsupported by PR 4 validation.",
            )
        )

    return findings


def _package_tree_findings(
    *, declared_paths: tuple[str, ...], package_root: Path
) -> list[PackageValidationFinding]:
    """Enumerate the package tree and diff it against declared expectations.

    Parameters
    ----------
    declared_paths
        String forms of the declared artifact paths.
    package_root
        Safely discovered package root.

    Returns
    -------
    list[PackageValidationFinding]
        Tree-enumeration findings plus missing, undeclared, and extra-directory
        findings.
    """

    tree_files, tree_directories, tree_findings = _collect_package_tree(package_root)
    findings: list[PackageValidationFinding] = list(tree_findings)
    expected_files = {PACKAGE_MANIFEST_FILENAME, *declared_paths}
    expected_directories = _expected_directories(expected_files)

    for missing_path in sorted(expected_files - tree_files):
        findings.append(
            _finding(
                code="package_declared_file_missing",
                details={"package_path": missing_path},
                message=f"Expected package file '{missing_path}' is missing.",
            )
        )

    for unexpected_path in sorted(tree_files - expected_files):
        findings.append(
            _finding(
                code="package_undeclared_file",
                details={"package_path": unexpected_path},
                message=f"Package file '{unexpected_path}' is not declared.",
            )
        )

    for unexpected_directory in sorted(tree_directories - expected_directories):
        findings.append(
            _finding(
                code="package_undeclared_directory",
                details={"package_path": unexpected_directory},
                message=f"Package directory '{unexpected_directory}' is not required by declared content.",
            )
        )

    return findings


def _parse_json_object(value: bytes) -> dict[str, object]:
    """Decode UTF-8 JSON into one duplicate-free top-level object.

    Parameters
    ----------
    value
        Exact JSON file bytes.

    Returns
    -------
    dict[str, object]
        Parsed object.

    Raises
    ------
    ValueError
        If JSON is malformed, contains duplicate keys, or is not an object.
    """

    decoded = value.decode("utf-8")
    parsed = json.loads(object_pairs_hook=_reject_duplicate_json_keys, s=decoded)

    if not isinstance(parsed, dict):
        raise ValueError("The JSON document must contain a top-level object.")

    return parsed


def _profile_load_finding(error: ProfileValidationError) -> PackageValidationFinding:
    """Translate a profile-load failure into one package validation finding.

    Parameters
    ----------
    error
        Failure raised while loading the manifest-referenced profile.

    Returns
    -------
    PackageValidationFinding
        Finding distinguishing an unsupported schema version from a generic load
        failure.
    """

    finding_code = "profile_load_failed"
    finding_message = "The manifest-referenced curriculum profile could not be loaded."
    validation_errors = error.details.get("validation_errors")

    if isinstance(validation_errors, list):
        error_fields = {
            str(validation_error["loc"][0])
            for validation_error in validation_errors
            if isinstance(validation_error, Mapping) and validation_error.get("loc")
        }

        if {"profileSchemaVersion", "profile_schema_version"}.intersection(
            error_fields
        ):
            finding_code = "profile_schema_version_unsupported"
            finding_message = "The curriculum-profile schema version is unsupported."

    return _finding(
        code=finding_code, details=dict(error.details), message=finding_message
    )


def _raw_package_revision(manifest_object: dict[str, object] | None) -> object:
    """Read the raw package-revision value from a parsed manifest object.

    Parameters
    ----------
    manifest_object
        Parsed manifest object, or ``None`` when JSON decoding failed.

    Returns
    -------
    object
        Raw revision under either the camelCase or snake_case member name, or
        ``None`` when neither member is present.
    """

    if manifest_object is None:
        return None

    if "packageRevision" in manifest_object:
        return manifest_object.get("packageRevision")

    return manifest_object.get("package_revision")


def _read_regular_file(path: Path) -> bytes:
    """Read exact bytes without following a final symbolic link.

    Parameters
    ----------
    path
        Selected package file.

    Returns
    -------
    bytes
        Exact file bytes.

    Raises
    ------
    OSError
        If the file cannot be opened or read.
    ValueError
        If the selected entry is not a regular file.
    """

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(flags=flags, path=path)

    try:
        file_stat = os.fstat(descriptor)

        if not stat.S_ISREG(file_stat.st_mode):
            raise ValueError("The selected package entry is not a regular file.")

        chunks: list[bytes] = []

        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)

        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Build one JSON object while rejecting duplicate member names.

    Parameters
    ----------
    pairs
        Ordered key-value pairs supplied by ``json.loads``.

    Returns
    -------
    dict[str, object]
        Object with unique keys.

    Raises
    ------
    ValueError
        If any JSON member name occurs more than once.
    """

    result: dict[str, object] = {}

    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON member name: {key}.")

        result[key] = value

    return result


def _scan_directory(
    directory: Path,
) -> tuple[list[os.DirEntry[str]], PackageValidationFinding | None]:
    """Enumerate one directory's entries in stable order without following links.

    Parameters
    ----------
    directory
        Directory whose immediate entries are enumerated.

    Returns
    -------
    tuple[list[os.DirEntry[str]], PackageValidationFinding | None]
        Name-sorted entries and one enumeration finding when scanning fails.
    """

    try:
        with os.scandir(directory) as iterator:
            return sorted(iterator, key=lambda entry: entry.name), None
    except OSError as error:
        return [], _finding(
            code="package_tree_unreadable",
            details={"directory_path": str(directory), "reason": str(error)},
            message="Package content could not be enumerated safely.",
        )


def _snapshot_identity_findings(
    *,
    candidate: GraphPackageCandidate,
    checksums: list[Sha256Digest],
    manifest: GraphPackageManifest,
) -> tuple[list[PackageValidationFinding], bool]:
    """Recompute snapshot identity from artifact checksums and compare it.

    Parameters
    ----------
    candidate
        Safely discovered package candidate, used for diagnostic context.
    checksums
        Exact per-artifact checksums in declaration order.
    manifest
        Validated manifest carrying the expected snapshot identity.

    Returns
    -------
    tuple[list[PackageValidationFinding], bool]
        Snapshot-stage findings and whether integrity verification failed.
    """

    findings: list[PackageValidationFinding] = []

    try:
        content_sha256 = calculate_snapshot_artifact_set_sha256(checksums)
        version_token = _snapshot_version_token(str(manifest.snapshot_id))
        expected_snapshot_id = build_snapshot_id(
            content_sha256=content_sha256,
            framework_id=manifest.framework_id,
            version_token=version_token,
        )
    except ValueError as error:
        findings.append(
            _finding(
                code="snapshot_identity_unverifiable",
                details={
                    "package_reference": candidate.reference,
                    "reason": str(error),
                },
                message="The package snapshot identity could not be recomputed.",
            )
        )
        return findings, True

    if expected_snapshot_id != manifest.snapshot_id:
        findings.append(
            _finding(
                code="snapshot_checksum_identity_mismatch",
                details={
                    "actual_snapshot_id": str(expected_snapshot_id),
                    "manifest_snapshot_id": str(manifest.snapshot_id),
                },
                message="The artifact-set checksum does not reproduce the manifest snapshot ID.",
            )
        )
        return findings, True

    return findings, False


def _snapshot_version_token(snapshot_id: str) -> SnapshotVersionToken:
    """Extract and validate the existing snapshot version token.

    Parameters
    ----------
    snapshot_id
        Established immutable snapshot identifier.

    Returns
    -------
    SnapshotVersionToken
        Validated token between ``@`` and the final ``+`` hash delimiter.
    """

    identity_without_hash, separator, _ = snapshot_id.rpartition("+")

    if not separator:
        raise ValueError("Snapshot identity has no content-hash delimiter.")

    _, namespace_separator, version_token = identity_without_hash.partition("@")

    if not namespace_separator:
        raise ValueError("Snapshot identity has no framework namespace delimiter.")

    return _SNAPSHOT_VERSION_TOKEN_ADAPTER.validate_python(version_token)


def _validate_candidate_location(
    candidate: GraphPackageCandidate,
) -> PackageValidationFinding | None:
    """Recheck that a discovered package candidate still names one real directory.

    The repository performs the authoritative root-confined discovery. This loader
    preflight detects a candidate that was fabricated, renamed, or replaced by a
    symbolic link between discovery and loading.

    Parameters
    ----------
    candidate
        Candidate returned by the graph-package repository.

    Returns
    -------
    PackageValidationFinding | None
        One blocking finding when the candidate is no longer trustworthy, otherwise
        ``None``.
    """

    package_path = candidate.package_path

    if (
        not package_path.is_absolute()
        or package_path.name != str(candidate.snapshot_id)
        or package_path.parent.name != str(candidate.framework_id)
    ):
        return _finding(
            code="package_candidate_identity_mismatch",
            details={
                "framework_id": str(candidate.framework_id),
                "package_path": str(package_path),
                "snapshot_id": str(candidate.snapshot_id),
            },
            message="The package candidate does not use the established repository layout.",
        )

    if package_path.is_symlink():
        return _finding(
            code="package_candidate_symlink_rejected",
            details={"package_path": str(package_path)},
            message="The package candidate may not be a symbolic link.",
        )

    try:
        resolved_path = package_path.resolve(strict=True)
    except OSError as error:
        return _finding(
            code="package_candidate_unavailable",
            details={"package_path": str(package_path), "reason": str(error)},
            message="The package candidate is unavailable.",
        )

    if resolved_path != package_path or not resolved_path.is_dir():
        return _finding(
            code="package_candidate_changed",
            details={
                "package_path": str(package_path),
                "resolved_path": str(resolved_path),
            },
            message="The package candidate changed after repository discovery.",
        )

    return None


def _validation_report(
    references: list[DeclaredArtifactReference],
) -> tuple[DetailedValidationReport | None, list[PackageValidationFinding]]:
    """Read and validate the optional declared detailed validation report.

    Parameters
    ----------
    references
        Verified declared-artifact references, optionally including the report.

    Returns
    -------
    tuple[DetailedValidationReport | None, list[PackageValidationFinding]]
        The parsed report when present and acceptable and any report findings.
    """

    findings: list[PackageValidationFinding] = []
    report_reference = next(
        (
            reference
            for reference in references
            if str(reference.logical_name) == "validationReport"
        ),
        None,
    )

    if report_reference is None:
        return None, findings

    try:
        report_bytes = _read_regular_file(report_reference.resolved_path)
        report_object = _parse_json_object(report_bytes)
        loaded_report = DetailedValidationReport.model_validate(report_object)
    except (OSError, ValueError, ValidationError) as error:
        details: dict[str, object] = {
            "artifact_path": str(report_reference.package_path),
            "reason": str(error),
        }

        if isinstance(error, ValidationError):
            details["validation_errors"] = error.errors(
                include_input=False, include_url=False
            )

        findings.append(
            _finding(
                artifact_name=report_reference.logical_name,
                code="detailed_validation_report_invalid",
                details=details,
                message="The declared detailed validation report is not acceptable.",
            )
        )
        return None, findings

    return loaded_report, findings


def _verify_declared_artifacts(
    *,
    candidate: GraphPackageCandidate,
    declared_artifacts: Mapping[str, ArtifactPath],
    manifest: GraphPackageManifest,
) -> _ArtifactVerificationResult:
    """Resolve, checksum, and reference every declared artifact from bytes.

    Parameters
    ----------
    candidate
        Safely discovered package candidate providing the package root.
    declared_artifacts
        Mapping of logical artifact names to package-relative paths.
    manifest
        Validated manifest carrying the expected per-artifact checksums.

    Returns
    -------
    _ArtifactVerificationResult
        Collected references, checksums, findings, and the integrity flag.
    """

    references: list[DeclaredArtifactReference] = []
    checksums: list[Sha256Digest] = []
    findings: list[PackageValidationFinding] = []
    integrity_failed = False

    for logical_name, package_path in declared_artifacts.items():
        artifact_name = _ARTIFACT_NAME_ADAPTER.validate_python(logical_name)
        resolved_path, path_finding = _artifact_path(
            package_path=package_path, package_root=candidate.package_path
        )

        if path_finding is not None:
            findings.append(
                path_finding.model_copy(update={"artifact_name": artifact_name})
            )
            integrity_failed = True
            continue

        assert resolved_path is not None

        try:
            actual_sha256 = calculate_file_sha256(resolved_path)
            size_bytes = resolved_path.stat(follow_symlinks=False).st_size
        except OSError as error:
            findings.append(
                _finding(
                    artifact_name=artifact_name,
                    code="artifact_checksum_unreadable",
                    details={
                        "artifact_path": str(package_path),
                        "resolved_path": str(resolved_path),
                        "reason": str(error),
                    },
                    message=f"Declared artifact '{package_path}' could not be checksummed.",
                )
            )
            integrity_failed = True
            continue

        expected_sha256 = manifest.checksums[package_path]

        if actual_sha256 != expected_sha256:
            findings.append(
                _finding(
                    artifact_name=artifact_name,
                    code="artifact_checksum_mismatch",
                    details={
                        "actual_sha256": str(actual_sha256),
                        "artifact_path": str(package_path),
                        "expected_sha256": str(expected_sha256),
                    },
                    message=f"Declared artifact '{package_path}' does not match its exact-byte checksum.",
                )
            )
            integrity_failed = True

        checksums.append(actual_sha256)
        references.append(
            DeclaredArtifactReference(
                logical_name=artifact_name,
                package_path=package_path,
                resolved_path=resolved_path,
                sha256=actual_sha256,
                size_bytes=size_bytes,
            )
        )

    return _ArtifactVerificationResult(
        checksums=checksums,
        findings=findings,
        integrity_failed=integrity_failed,
        references=references,
    )
