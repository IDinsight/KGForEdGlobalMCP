"""This module loads graph packages through established manifests, profiles, checksums,
and decoders.

The loader is the package-integrity boundary. It accepts only candidates produced by
the graph-package repository, parses the existing manifest model, resolves one exact
versioned profile, verifies every declared artifact from packaged bytes, rejects
undeclared or unsafe tree content, recomputes immutable snapshot identity, and decodes
delivery JSONL exclusively through the PR 2 decoder.

This module does not validate graph topology or profile hierarchy semantics, persist
validation status, build graph indexes, repair artifacts, or expose traversal APIs.
Those responsibilities remain in their dedicated layers.
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
from kgfegmcp.profiles.repository import ProfileRepository

_ARTIFACT_NAME_ADAPTER: TypeAdapter[ArtifactName] = TypeAdapter(ArtifactName)
_MANIFEST_LOGICAL_NAME: Final[str] = "packageManifest"
_SNAPSHOT_VERSION_TOKEN_ADAPTER: TypeAdapter[SnapshotVersionToken] = TypeAdapter(
    SnapshotVersionToken
)


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

        try:
            manifest_object = _parse_json_object(manifest_bytes)
            manifest = GraphPackageManifest.model_validate(manifest_object)
        except (UnicodeDecodeError, ValueError, ValidationError) as error:
            details: dict[str, object] = {
                "manifest_path": str(manifest_path),
                "reason": str(error),
            }
            finding_code = "manifest_invalid"
            finding_message = (
                "The package manifest does not satisfy its established contract."
            )

            if isinstance(error, ValidationError):
                validation_errors = error.errors(include_input=False, include_url=False)
                details["validation_errors"] = validation_errors
                error_fields = {
                    str(validation_error["loc"][0])
                    for validation_error in validation_errors
                    if validation_error.get("loc")
                }
                version_findings = (
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

                for field_names, code, message in version_findings:
                    if not field_names.intersection(error_fields):
                        continue

                    finding_code = code
                    finding_message = message
                    break

                raw_package_revision = (
                    manifest_object.get("packageRevision")
                    if "packageRevision" in manifest_object
                    else manifest_object.get("package_revision")
                )

                if (
                    finding_code == "manifest_invalid"
                    and raw_package_revision is not None
                    and raw_package_revision != SUPPORTED_PACKAGE_REVISION
                ):
                    finding_code = "package_revision_unsupported"
                    finding_message = "The package revision is unsupported by PR 4."

            findings.append(
                _finding(
                    artifact_name=_ARTIFACT_NAME_ADAPTER.validate_python(
                        _MANIFEST_LOGICAL_NAME
                    ),
                    code=finding_code,
                    details=details,
                    message=finding_message,
                )
            )
            return None, manifest_bytes, findings

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
                            graph_type.value
                            for graph_type in manifest.included_graph_types
                        )
                    },
                    message="The package includes graph types unsupported by PR 4 validation.",
                )
            )

        return manifest, manifest_bytes, findings

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

        try:
            discovered_candidate = self.repository.candidate(
                framework_id=candidate.framework_id, snapshot_id=candidate.snapshot_id
            )
        except PackageValidationError as error:
            return GraphPackageLoadResult(
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
            return GraphPackageLoadResult(
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

        candidate = discovered_candidate
        candidate_finding = _validate_candidate_location(candidate)

        if candidate_finding is not None:
            return GraphPackageLoadResult(
                candidate=candidate, findings=(candidate_finding,)
            )

        manifest, manifest_bytes, findings = self._load_manifest(candidate)

        if manifest is None or manifest_bytes is None:
            return GraphPackageLoadResult(
                candidate=candidate,
                findings=tuple(findings),
                manifest=manifest,
                manifest_bytes=manifest_bytes,
            )

        declared_artifacts = manifest.artifacts.declared_artifacts()
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

        declared_paths = tuple(str(path) for path in declared_artifacts.values())
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

        tree_files, tree_directories, tree_findings = _collect_package_tree(
            candidate.package_path
        )
        findings.extend(tree_findings)
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

        try:
            loaded_profile = self.profile_repository.load(
                profile_id=manifest.profile.profile_id,
                profile_version=manifest.profile.profile_version,
            )
        except ProfileValidationError as error:
            profile_finding_code = "profile_load_failed"
            profile_finding_message = (
                "The manifest-referenced curriculum profile could not be loaded."
            )
            validation_errors = error.details.get("validation_errors")

            if isinstance(validation_errors, list):
                error_fields = {
                    str(validation_error["loc"][0])
                    for validation_error in validation_errors
                    if isinstance(validation_error, Mapping)
                    and validation_error.get("loc")
                }

                if {"profileSchemaVersion", "profile_schema_version"}.intersection(
                    error_fields
                ):
                    profile_finding_code = "profile_schema_version_unsupported"
                    profile_finding_message = (
                        "The curriculum-profile schema version is unsupported."
                    )

            findings.append(
                _finding(
                    code=profile_finding_code,
                    details=dict(error.details),
                    message=profile_finding_message,
                )
            )
            loaded_profile = None

        if (
            loaded_profile is not None
            and loaded_profile.sha256 != manifest.profile.sha256
        ):
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

        artifact_references: list[DeclaredArtifactReference] = []
        actual_checksums: list[Sha256Digest] = []
        artifact_integrity_failed = False

        for logical_name, package_path in declared_artifacts.items():
            artifact_name = _ARTIFACT_NAME_ADAPTER.validate_python(logical_name)
            resolved_path, path_finding = _artifact_path(
                package_path=package_path, package_root=candidate.package_path
            )

            if path_finding is not None:
                findings.append(
                    path_finding.model_copy(update={"artifact_name": artifact_name})
                )
                artifact_integrity_failed = True
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
                artifact_integrity_failed = True
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
                artifact_integrity_failed = True

            actual_checksums.append(actual_sha256)
            artifact_references.append(
                DeclaredArtifactReference(
                    logical_name=artifact_name,
                    package_path=package_path,
                    resolved_path=resolved_path,
                    sha256=actual_sha256,
                    size_bytes=size_bytes,
                )
            )

        if len(actual_checksums) == len(declared_artifacts):
            try:
                content_sha256 = calculate_snapshot_artifact_set_sha256(
                    actual_checksums
                )
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
                artifact_integrity_failed = True
            else:
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
                    artifact_integrity_failed = True

        loaded_report: DetailedValidationReport | None = None
        validation_report_reference = None

        for reference in artifact_references:
            if str(reference.logical_name) == "validationReport":
                validation_report_reference = reference
                break

        if validation_report_reference is not None:
            try:
                report_bytes = _read_regular_file(
                    validation_report_reference.resolved_path
                )
                report_object = _parse_json_object(report_bytes)
                loaded_report = DetailedValidationReport.model_validate(report_object)
            except (OSError, UnicodeDecodeError, ValueError, ValidationError) as error:
                details: dict[str, object] = {
                    "artifact_path": str(validation_report_reference.package_path),
                    "reason": str(error),
                }

                if isinstance(error, ValidationError):
                    details["validation_errors"] = error.errors(
                        include_input=False, include_url=False
                    )

                findings.append(
                    _finding(
                        artifact_name=validation_report_reference.logical_name,
                        code="detailed_validation_report_invalid",
                        details=details,
                        message="The declared detailed validation report is not acceptable.",
                    )
                )

        blocking_codes = {
            finding.code
            for finding in findings
            if finding.code
            in {
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
        }

        if artifact_integrity_failed or blocking_codes or loaded_profile is None:
            return GraphPackageLoadResult(
                candidate=candidate,
                findings=tuple(findings),
                manifest=manifest,
                manifest_bytes=manifest_bytes,
            )

        nodes_reference = next(
            reference
            for reference in artifact_references
            if str(reference.logical_name) == "nodes"
        )
        relationships_reference = next(
            reference
            for reference in artifact_references
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
            return GraphPackageLoadResult(
                candidate=candidate,
                findings=tuple(findings),
                manifest=manifest,
                manifest_bytes=manifest_bytes,
            )

        framework_roots = tuple(
            node for node in decoded_nodes if isinstance(node, FrameworkNode)
        )
        item_nodes = tuple(
            node for node in decoded_nodes if isinstance(node, StandardNode)
        )

        if len(framework_roots) != 1:
            findings.append(
                _finding(
                    artifact_name=nodes_reference.logical_name,
                    code="framework_root_count_invalid",
                    details={"framework_root_count": len(framework_roots)},
                    message="The delivery nodes must contain exactly one framework root.",
                )
            )
            return GraphPackageLoadResult(
                candidate=candidate,
                findings=tuple(findings),
                manifest=manifest,
                manifest_bytes=manifest_bytes,
            )

        loaded_package = LoadedGraphPackage(
            artifacts=tuple(artifact_references),
            framework_root=framework_roots[0],
            item_nodes=item_nodes,
            manifest=manifest,
            manifest_bytes=manifest_bytes,
            manifest_path=candidate.manifest_path,
            package_root=candidate.package_path,
            profile=loaded_profile.profile,
            profile_path=loaded_profile.path,
            profile_sha256=loaded_profile.sha256,
            relationships=relationships,
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

        try:
            with os.scandir(directory) as iterator:
                entries = sorted(iterator, key=lambda entry: entry.name)
        except OSError as error:
            findings.append(
                _finding(
                    code="package_tree_unreadable",
                    details={"directory_path": str(directory), "reason": str(error)},
                    message="Package content could not be enumerated safely.",
                )
            )
            continue

        for entry in entries:
            entry_path = Path(entry.path)
            relative_path = entry_path.relative_to(package_root).as_posix()
            casefold_path = relative_path.casefold()
            previous_path = casefold_entries.get(casefold_path)

            if previous_path is not None and previous_path != relative_path:
                findings.append(
                    _finding(
                        code="package_path_case_collision",
                        details={
                            "first_path": previous_path,
                            "second_path": relative_path,
                        },
                        message="Package content has a case-insensitive path collision.",
                    )
                )
            else:
                casefold_entries[casefold_path] = relative_path

            try:
                is_directory = entry.is_dir(follow_symlinks=False)
                is_file = entry.is_file(follow_symlinks=False)
                is_symlink = entry.is_symlink()
            except OSError as error:
                findings.append(
                    _finding(
                        code="package_entry_unreadable",
                        details={
                            "entry_path": str(entry_path),
                            "reason": str(error),
                        },
                        message=f"Package entry '{relative_path}' could not be inspected safely.",
                    )
                )
                continue

            if is_symlink:
                findings.append(
                    _finding(
                        code="package_symlink_rejected",
                        details={"entry_path": str(entry_path)},
                        message=f"Package entry '{relative_path}' may not be a symbolic link.",
                    )
                )
                continue

            if is_directory:
                directories.add(relative_path)
                pending_directories.append(entry_path)
                continue

            if is_file:
                files.add(relative_path)
                continue

            findings.append(
                _finding(
                    code="package_special_entry_rejected",
                    details={"entry_path": str(entry_path)},
                    message=f"Package entry '{relative_path}' is not a regular file or directory.",
                )
            )

    return files, directories, tuple(findings)


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
