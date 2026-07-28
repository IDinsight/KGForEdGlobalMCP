"""This module builds deterministic pending graph packages from approved curriculum
artifacts.

This module coordinates graph-package manifest construction. It resolves and validates
the selected curriculum profile, decodes delivery artifacts through the existing
package decoder, compares overlapping profile and framework metadata, derives counts
and capabilities, and creates the existing GraphPackageManifest model.

The builder preserves source artifact bytes and filenames, calculates exact checksums,
derives snapshot and graph-package identifiers through the existing identifier
contracts, and places artifacts into safe package-relative locations. New packages are
assembled in a verified staging directory and moved atomically into their final
destination without replacing existing content.

An existing package is accepted only when it is an equivalent pending package with
matching package-defining manifest values, declared files, and exact artifact
checksums. Conflicting, malformed, incomplete, terminal, or unexpectedly populated
destinations are rejected.

This module performs only the construction-time checks needed to create a truthful
candidate package. It does not perform complete package validation, graph-wide
validation, package loading, quarantine, traversal, search, catalog, or MCP application
behavior.
"""

# Future Library
from __future__ import annotations

# Standard Library
import errno
import json
import os
import re
import shutil
import sys
import tempfile

from ctypes import CDLL, c_char_p, c_int, c_uint, get_errno
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Final, NoReturn, cast

# Third Party Library
from pydantic import TypeAdapter, ValidationError

# Package Library
from kgfegmcp.config import BackendSettings
from kgfegmcp.domain.enums import CodeAvailability, GraphType, ValidationStatus
from kgfegmcp.domain.identifiers import (
    ArtifactName,
    ArtifactPath,
    FrameworkId,
    GraphPackageId,
    Sha256Digest,
    SnapshotId,
    build_initial_graph_package_id,
    build_snapshot_id,
)
from kgfegmcp.domain.models import RightsPolicy
from kgfegmcp.errors import ManifestBuildError
from kgfegmcp.graph.models import FrameworkNode, StandardNode
from kgfegmcp.packages.checksums import (
    calculate_file_sha256,
    calculate_snapshot_artifact_set_sha256,
)
from kgfegmcp.packages.decoder import iter_decoded_nodes, iter_decoded_relationships
from kgfegmcp.packages.models import (
    ADDITIONAL_COUNT_CODED_ITEMS,
    ADDITIONAL_COUNT_MULTI_PARENT_TARGETS,
    ADDITIONAL_COUNT_UNRESOLVED_RELATIONSHIPS,
    DELIVERY_SCHEMA_VERSION,
    SOURCE_SCHEMA_VERSION,
    FrameworkCapabilities,
    FrameworkMetadata,
    GraphPackageManifest,
    PackageArtifacts,
    PackageBuildResult,
    PackageBuildSpec,
    PackageCounts,
    PackageValidation,
    ProfileReference,
    SnapshotRelation,
)
from kgfegmcp.packages.wire import (
    DELIVERY_SCHEMA_1_0_RELATIONSHIP_STATUS_VOCABULARY,
    DELIVERY_SCHEMA_1_0_UNRESOLVED_RELATIONSHIP_STATUSES,
)
from kgfegmcp.profiles.loader import load_curriculum_profile
from kgfegmcp.profiles.models import CurriculumProfile
from kgfegmcp.regexes import (
    CONTROL_CHARACTER_RE,
    DELIVERY_NODES_BASENAME_RE,
    DELIVERY_RELATIONSHIPS_BASENAME_RE,
    SAFE_AS_ARTIFACT_BASENAME_RE,
)

_MANIFEST_FILENAME: Final[str] = "package_manifest.json"
_RECOGNIZED_DETAILED_ARTIFACTS: Final[dict[str, tuple[str, str]]] = {
    "as_entity_provenance.json": ("entity_provenance", "entityProvenance"),
    "as_kg_bundle.json": ("academic_standards_bundle", "academicStandardsBundle"),
    "as_relationships_has_child.jsonl": (
        "relationships_has_child",
        "relationshipsHasChild",
    ),
    "as_standards_framework.json": ("standards_framework", "standardsFramework"),
    "as_standards_framework_items.jsonl": (
        "standards_framework_items",
        "standardsFrameworkItems",
    ),
    "as_unresolved_items.json": ("unresolved_items", "unresolvedItems"),
    "as_validation_report.json": ("validation_report", "validationReport"),
}
_RECOGNIZED_DETAILED_BASENAMES_CASEFOLDED: Final[frozenset[str]] = frozenset(
    basename.casefold() for basename in _RECOGNIZED_DETAILED_ARTIFACTS
)
_RESERVED_ADDITIONAL_LOGICAL_NAMES: Final[frozenset[str]] = frozenset(
    {
        "academicstandardsbundle",
        "entityprovenance",
        "nodes",
        "relationships",
        "relationshipshaschild",
        "standardsframework",
        "standardsframeworkitems",
        "unresolveditems",
        "validationreport",
    }
)
_ARTIFACT_PATH_ADAPTER: TypeAdapter[ArtifactPath] = TypeAdapter(ArtifactPath)
_AT_FDCWD: Final[int] = -100
_DARWIN_RENAME_EXCL: Final[int] = 0x00000004
_LINUX_RENAME_NOREPLACE: Final[int] = 1


class _ExistingPackage(Exception):
    """Signal that materialization observed an already-present destination.

    This internal control-flow sentinel is raised by materialization helpers when the
    destination appears while the build holds its lock. It is always caught inside
    ``_materialize_package`` and converted into an existing-identical result; it never
    escapes this module.
    """


@dataclass(frozen=True, slots=True)
class _ArtifactSource:
    """Associate one source file with its manifest name, package path, and digest."""

    manifest_name: str
    package_path: ArtifactPath
    sha256: Sha256Digest
    source_path: Path


@dataclass(frozen=True, slots=True)
class _DecodedFacts:
    """Hold construction-time facts derived through the existing decoder."""

    coded_items: int
    framework_nodes: int
    framework_root: FrameworkNode
    item_nodes: int
    multi_parent_targets: int
    relationships: int
    text_items: int
    unresolved_relationships: int


@dataclass(frozen=True, slots=True)
class _FileFingerprint:
    """Record one input path and the exact digest observed during planning."""

    path: Path
    sha256: Sha256Digest


@dataclass(frozen=True, slots=True)
class _NodeFacts:
    """Hold node-derived counts and the single decoded framework root."""

    coded_items: int
    framework_root: FrameworkNode
    item_nodes: int
    text_items: int


@dataclass(frozen=True, slots=True)
class _PackagePlan:
    """Hold all package-defining values except the materialization timestamp."""

    artifact_sources: tuple[_ArtifactSource, ...]
    artifacts: PackageArtifacts
    capabilities: FrameworkCapabilities
    checksums: dict[ArtifactPath, Sha256Digest]
    counts: PackageCounts
    destination: Path
    framework: FrameworkMetadata
    framework_id: FrameworkId
    graph_package_id: GraphPackageId
    profile_fingerprint: _FileFingerprint
    profile_reference: ProfileReference
    rights: RightsPolicy
    snapshot_id: SnapshotId
    snapshot_relations: tuple[SnapshotRelation, ...]
    source_document_fingerprint: _FileFingerprint | None
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _RelationshipFacts:
    """Hold relationship-derived counts and parent-topology evidence."""

    multi_parent_targets: int
    relationships: int
    unresolved_relationships: int


def _acquire_build_lock(*, lock_path: Path, plan: _PackagePlan) -> int:
    """Acquire the exclusive build lock guarding a package destination.

    Parameters
    ----------
    lock_path
        Framework-relative lock file that must be created exclusively.
    plan
        Candidate package plan whose destination the lock guards.

    Returns
    -------
    int
        Open file descriptor for the owned lock file.

    Raises
    ------
    _ExistingPackage
        If the destination already exists, signaling that the caller should return the
        existing-identical result instead of building.
    ManifestBuildError
        If another concurrent build already owns the lock.
    """

    try:
        return os.open(
            flags=os.O_CREAT | os.O_EXCL | os.O_WRONLY, mode=0o600, path=lock_path
        )
    except FileExistsError as error:
        if os.path.lexists(plan.destination):
            raise _ExistingPackage from error

        raise ManifestBuildError(
            details={"lock_path": str(lock_path)},
            message="Another package build is already using this destination.",
        ) from error


def _artifact_path(value: str) -> ArtifactPath:
    """Validate a generated package-relative artifact path.

    Parameters
    ----------
    value
        Candidate POSIX package-relative path.

    Returns
    -------
    ArtifactPath
        Validated artifact path.
    """

    return _ARTIFACT_PATH_ADAPTER.validate_python(value)


def _atomic_rename_no_replace(*, destination: Path, source: Path) -> None:
    """Atomically rename a directory while refusing to replace any destination.

    Parameters
    ----------
    destination
        Final package directory, which must not already exist.
    source
        Fully verified staging directory on the same filesystem.

    Raises
    ------
    FileExistsError
        If the destination already exists.
    OSError
        If the platform cannot provide no-replace rename semantics or the rename
        otherwise fails.
    """

    if sys.platform == "win32":
        os.rename(dst=destination, src=source)
        return

    library = CDLL(name=None, use_errno=True)

    if sys.platform.startswith("linux"):
        rename_function = getattr(library, "renameat2", None)

        if rename_function is None:
            raise OSError("Safe atomic no-replace directory rename is unavailable.")

        rename_function.argtypes = (c_int, c_char_p, c_int, c_char_p, c_uint)
        rename_function.restype = c_int
        result = rename_function(
            _AT_FDCWD,
            os.fsencode(source),
            _AT_FDCWD,
            os.fsencode(destination),
            _LINUX_RENAME_NOREPLACE,
        )
    elif sys.platform == "darwin":
        rename_function = getattr(library, "renamex_np", None)

        if rename_function is None:
            raise OSError("Safe atomic no-replace directory rename is unavailable.")

        rename_function.argtypes = (c_char_p, c_char_p, c_uint)
        rename_function.restype = c_int
        result = rename_function(
            os.fsencode(source), os.fsencode(destination), _DARWIN_RENAME_EXCL
        )
    else:
        raise OSError("Safe atomic no-replace directory rename is unavailable.")

    if result == 0:
        return

    error_number = get_errno()

    if error_number in {errno.EEXIST, errno.ENOTEMPTY}:
        raise FileExistsError(error_number, os.strerror(error_number), destination)

    raise OSError(error_number, os.strerror(error_number), destination)


def _build_error(*, details: dict[str, object], message: str) -> NoReturn:
    """Raise a typed manifest-build error with separated internal details.

    Parameters
    ----------
    details
        Internal diagnostic values that may include local paths.
    message
        Safe actionable public message.

    Raises
    ------
    ManifestBuildError
        Always raised.
    """

    raise ManifestBuildError(details=details, message=message)


def _calculate_file_sha256(path: Path) -> Sha256Digest:
    """Calculate one file checksum and translate I/O failures for the builder.

    Parameters
    ----------
    path
        Artifact, profile, or source-document path to checksum exactly.

    Returns
    -------
    Sha256Digest
        Qualified exact-byte SHA-256 digest.

    Raises
    ------
    ManifestBuildError
        If the selected file cannot be read completely.
    """

    try:
        return calculate_file_sha256(path)
    except OSError as error:
        raise ManifestBuildError(
            details={"file_path": str(path)},
            message=f"Could not checksum file '{path.name}'.",
        ) from error


def _canonical_manifest_bytes(manifest: GraphPackageManifest) -> bytes:
    """Serialize a manifest as deterministic UTF-8 JSON ending in one LF.

    Parameters
    ----------
    manifest
        Validated graph-package manifest.

    Returns
    -------
    bytes
        Stable lower-camel-case JSON bytes.
    """

    payload = manifest.model_dump(by_alias=True, mode="json")
    serialized = json.dumps(ensure_ascii=False, indent=2, obj=payload, sort_keys=True)
    return f"{serialized}\n".encode("utf-8")


def _collect_tree_entries(package_path: Path) -> tuple[set[str], set[str]]:
    """Collect regular files and directories without following package symlinks.

    Parameters
    ----------
    package_path
        Existing or staged package root.

    Returns
    -------
    tuple[set[str], set[str]]
        Package-relative file paths and directory paths.

    Raises
    ------
    ManifestBuildError
        If an entry is unreadable, a symlink, or not a regular file or directory.
    """

    directories: set[str] = set()
    files: set[str] = set()
    pending_directories = [package_path]

    while pending_directories:
        directory = pending_directories.pop()

        try:
            entries = tuple(os.scandir(directory))
        except OSError as error:
            raise ManifestBuildError(
                details={"package_path": str(package_path)},
                message=(
                    "The candidate package directory could not be inspected safely."
                ),
            ) from error

        for entry in entries:
            entry_path = Path(entry.path)
            relative_path = entry_path.relative_to(package_path).as_posix()

            if entry.is_symlink():
                _build_error(
                    details={
                        "entry_path": str(entry_path),
                        "package_path": str(package_path),
                    },
                    message=(
                        f"Package content '{relative_path}' may not be a symbolic link."
                    ),
                )

            if entry.is_dir(follow_symlinks=False):
                directories.add(relative_path)
                pending_directories.append(entry_path)
                continue

            if entry.is_file(follow_symlinks=False):
                files.add(relative_path)
                continue

            _build_error(
                details={
                    "entry_path": str(entry_path),
                    "package_path": str(package_path),
                },
                message=f"Package content '{relative_path}' is not a regular file.",
            )

    return files, directories


def _copy_artifacts(
    *, artifact_sources: tuple[_ArtifactSource, ...], staging_path: Path
) -> None:
    """Copy every declared artifact into staging and verify its exact bytes.

    Parameters
    ----------
    artifact_sources
        Deterministically ordered source artifact declarations.
    staging_path
        Private staging package root.

    Raises
    ------
    ManifestBuildError
        If copying fails or staged bytes do not match the planned checksum.
    """

    for artifact in artifact_sources:
        destination = _package_file_path(
            package_path=staging_path, relative_path=artifact.package_path
        )
        destination.parent.mkdir(exist_ok=True, parents=True)

        try:
            shutil.copyfile(dst=destination, src=artifact.source_path)
        except OSError as error:
            raise ManifestBuildError(
                details={
                    "destination_path": str(destination),
                    "source_path": str(artifact.source_path),
                },
                message=f"Artifact '{artifact.source_path.name}' could not be copied.",
            ) from error

        staged_sha256 = _calculate_file_sha256(destination)

        if staged_sha256 != artifact.sha256:
            _build_error(
                details={
                    "actual_sha256": str(staged_sha256),
                    "artifact_path": str(artifact.package_path),
                    "expected_sha256": str(artifact.sha256),
                    "source_path": str(artifact.source_path),
                },
                message=(
                    f"Artifact '{artifact.source_path.name}' changed while it was being packaged."
                ),
            )


def _create_manifest(
    *, created_at: datetime, plan: _PackagePlan
) -> GraphPackageManifest:
    """Create the established manifest model from package-defining values.

    Parameters
    ----------
    created_at
        Timezone-aware UTC package materialization or dry-run proposal timestamp.
    plan
        Package-defining values derived before timestamp assignment.

    Returns
    -------
    GraphPackageManifest
        Fully Pydantic-validated pending manifest.

    Raises
    ------
    ManifestBuildError
        If the established manifest contract rejects the derived values.
    """

    try:
        return GraphPackageManifest(
            artifacts=plan.artifacts,
            capabilities=plan.capabilities,
            checksums=plan.checksums,
            counts=plan.counts,
            created_at=created_at,
            delivery_schema_version=DELIVERY_SCHEMA_VERSION,
            framework=plan.framework,
            framework_id=plan.framework_id,
            graph_package_id=plan.graph_package_id,
            graph_type=GraphType.ACADEMIC_STANDARDS,
            included_graph_types=(GraphType.ACADEMIC_STANDARDS,),
            package_revision=1,
            profile=plan.profile_reference,
            rights=plan.rights,
            snapshot_id=plan.snapshot_id,
            snapshot_relations=plan.snapshot_relations,
            source_schema_version=SOURCE_SCHEMA_VERSION,
            validation=PackageValidation(
                status=ValidationStatus.PENDING, validated_at=None
            ),
        )
    except ValidationError as error:
        raise ManifestBuildError(
            details={
                "validation_errors": error.errors(
                    include_input=False, include_url=False
                )
            },
            message="The derived package manifest does not satisfy its contract.",
        ) from error


def _decode_facts(
    *, hierarchy_relationship_type: str, nodes_path: Path, relationships_path: Path
) -> _DecodedFacts:
    """Stream delivery artifacts through the existing decoder and derive counts.

    Parameters
    ----------
    hierarchy_relationship_type
        Profile-declared relationship label used for parent topology evidence.
    nodes_path
        Accepted node delivery artifact.
    relationships_path
        Accepted relationship delivery artifact.

    Returns
    -------
    _DecodedFacts
        Root metadata, counts, status evidence, code evidence, and topology facts.

    Raises
    ------
    ManifestBuildError
        If root cardinality or relationship-status vocabulary prevents truthful
        manifest construction.
    """

    node_facts = _scan_node_facts(nodes_path=nodes_path)
    relationship_facts = _scan_relationship_facts(
        hierarchy_relationship_type=hierarchy_relationship_type,
        relationships_path=relationships_path,
    )
    return _DecodedFacts(
        coded_items=node_facts.coded_items,
        framework_nodes=1,
        framework_root=node_facts.framework_root,
        item_nodes=node_facts.item_nodes,
        multi_parent_targets=relationship_facts.multi_parent_targets,
        relationships=relationship_facts.relationships,
        text_items=node_facts.text_items,
        unresolved_relationships=relationship_facts.unresolved_relationships,
    )


def _derive_capabilities(
    *, artifacts: PackageArtifacts, facts: _DecodedFacts, profile: CurriculumProfile
) -> FrameworkCapabilities:
    """Derive manifest capabilities from profile policy and artifact evidence.

    Parameters
    ----------
    artifacts
        Declared delivery and detailed package artifacts.
    facts
        Counts and topology evidence decoded from delivery artifacts.
    profile
        Selected curriculum interpretation profile.

    Returns
    -------
    FrameworkCapabilities
        Conservative evidence-backed package capabilities.

    Raises
    ------
    ManifestBuildError
        If code or hierarchy evidence materially conflicts with profile policy.
    """

    code_search = _derive_code_search_capability(
        coded_items=facts.coded_items,
        item_nodes=facts.item_nodes,
        profile_availability=profile.code_search_policy.availability,
    )

    if facts.multi_parent_targets and not profile.hierarchy.allow_multi_parent:
        _build_error(
            details={
                "multi_parent_targets": facts.multi_parent_targets,
                "profile_id": str(profile.profile_id),
            },
            message=(
                "Decoded hierarchy evidence contains multi-parent targets, but the "
                "selected profile does not permit multi-parent topology."
            ),
        )

    return FrameworkCapabilities(
        code_search=code_search,
        has_detailed_provenance=artifacts.entity_provenance is not None,
        has_official_activities=(
            profile.source_role_capabilities.has_official_activities
        ),
        has_official_assessment_guidance=(
            profile.source_role_capabilities.has_official_assessment_guidance
        ),
        has_unresolved_relationships=facts.unresolved_relationships > 0,
        multi_parent=facts.multi_parent_targets > 0,
        text_search=facts.text_items > 0,
    )


def _derive_code_search_capability(
    *, coded_items: int, item_nodes: int, profile_availability: CodeAvailability
) -> CodeAvailability:
    """Combine profile code policy with actual decoded code coverage.

    Parameters
    ----------
    coded_items
        Number of item nodes carrying a non-blank statement code.
    item_nodes
        Total decoded item-node count.
    profile_availability
        Selected profile's reviewed code availability policy.

    Returns
    -------
    CodeAvailability
        Conservative manifest capability.

    Raises
    ------
    ManifestBuildError
        If the profile overstates or contradicts actual code evidence.
    """

    if coded_items == 0:
        actual_availability = CodeAvailability.NONE
    elif coded_items == item_nodes:
        actual_availability = CodeAvailability.COMPLETE
    else:
        actual_availability = CodeAvailability.PARTIAL

    if profile_availability is CodeAvailability.NONE:
        if actual_availability is not CodeAvailability.NONE:
            _build_error(
                details={
                    "actual_availability": actual_availability.value,
                    "coded_items": coded_items,
                    "item_nodes": item_nodes,
                    "profile_availability": profile_availability.value,
                },
                message=(
                    "Decoded item codes conflict with the selected profile's code "
                    "availability policy."
                ),
            )
        return CodeAvailability.NONE

    if profile_availability is CodeAvailability.COMPLETE:
        if actual_availability is not CodeAvailability.COMPLETE:
            _build_error(
                details={
                    "actual_availability": actual_availability.value,
                    "coded_items": coded_items,
                    "item_nodes": item_nodes,
                    "profile_availability": profile_availability.value,
                },
                message=(
                    "The selected profile declares complete code availability, but "
                    "decoded item evidence is incomplete."
                ),
            )
        return CodeAvailability.COMPLETE

    if actual_availability is CodeAvailability.NONE:
        _build_error(
            details={
                "actual_availability": actual_availability.value,
                "coded_items": coded_items,
                "item_nodes": item_nodes,
                "profile_availability": profile_availability.value,
            },
            message=(
                "The selected profile declares partial code availability, but no "
                "decoded item contains a statement code."
            ),
        )

    return CodeAvailability.PARTIAL


def _derive_framework_metadata(
    *,
    facts: _DecodedFacts,
    profile: CurriculumProfile,
    source_document_sha256: Sha256Digest | None,
    spec: PackageBuildSpec,
) -> tuple[FrameworkMetadata, RightsPolicy]:
    """Combine source-facing root metadata with selected profile policy.

    Parameters
    ----------
    facts
        Decoded framework-root and count evidence.
    profile
        Selected curriculum interpretation profile.
    source_document_sha256
        Optional exact-byte source-document checksum.
    spec
        Operator-supplied build specification.

    Returns
    -------
    tuple[FrameworkMetadata, RightsPolicy]
        Manifest framework metadata and rights policy.

    Raises
    ------
    ManifestBuildError
        If required root metadata is missing or overlaps disagree materially.
    """

    root = facts.framework_root
    attribution_statement = _require_root_text(
        field_name="attributionStatement", value=root.attribution_statement
    )
    jurisdiction = _require_root_text(
        field_name="jurisdiction", value=root.jurisdiction
    )
    local_subject = _require_root_text(
        field_name="academicSubject", value=root.academic_subject
    )
    name = _require_root_text(field_name="name", value=root.name)
    source_license = _require_root_text(field_name="license", value=root.license)

    _require_exact_agreement(
        field_name="local subject",
        profile_value=profile.local_subject,
        root_value=local_subject,
    )
    _require_exact_agreement(
        field_name="source attribution statement",
        profile_value=profile.rights.attribution_statement,
        root_value=attribution_statement,
    )
    _require_exact_agreement(
        field_name="source license",
        profile_value=profile.rights.source_license,
        root_value=source_license,
    )

    profile_languages = tuple(str(value) for value in profile.language_policy.languages)

    if root.in_language is not None and str(root.in_language) not in profile_languages:
        _build_error(
            details={
                "profile_languages": profile_languages,
                "root_language": str(root.in_language),
            },
            message=(
                "The framework-root language is not represented by the selected "
                "profile's language policy."
            ),
        )

    if root.is_current is None:
        _build_error(
            details={"root_node_id": str(root.node_id)},
            message="The decoded framework root does not declare isCurrent.",
        )

    local_grades_or_stages = _ordered_unique(
        tuple(mapping.local_label for mapping in profile.grade_mappings)
        + tuple(mapping.local_label for mapping in profile.education_stage_mappings)
    )
    normalized_grades = _ordered_unique(
        tuple(
            normalized_grade
            for mapping in profile.grade_mappings
            for normalized_grade in mapping.normalized_grades
        )
    )

    try:
        framework = FrameworkMetadata(
            adoption_status=root.adoption_status,
            is_current=root.is_current,
            issuing_authority=root.author,
            jurisdiction=jurisdiction,
            jurisdiction_type=spec.jurisdiction_type,
            languages=profile.language_policy.languages,
            local_grades_or_stages=local_grades_or_stages,
            local_subject=local_subject,
            name=name,
            normalized_grades=normalized_grades,
            normalized_subjects=profile.normalized_subjects,
            provider=root.provider,
            source_document_sha256=source_document_sha256,
            source_publication_date=spec.source_publication_date,
            source_version=str(spec.version_token),
            subject_mapping_note=profile.subject_mapping_note,
            subject_mapping_status=profile.subject_mapping_status,
        )
    except ValidationError as error:
        raise ManifestBuildError(
            details={
                "validation_errors": error.errors(
                    include_input=False, include_url=False
                )
            },
            message="Framework metadata could not be derived from the selected inputs.",
        ) from error

    return framework, profile.rights


def _derive_warnings(profile: CurriculumProfile) -> tuple[str, ...]:
    """Derive operator-visible build warnings from profile disclosures.

    Parameters
    ----------
    profile
        Selected curriculum interpretation profile.

    Returns
    -------
    tuple[str, ...]
        Source-ordered unique required disclosures and anomaly disclosures.
    """

    anomaly_disclosures = tuple(
        anomaly.required_disclosure
        for anomaly in profile.known_source_anomalies
        if anomaly.required_disclosure is not None
    )
    return _ordered_unique(profile.required_disclosures + anomaly_disclosures)


def _discover_detailed_artifacts(
    *, project_dir: Path, spec: PackageBuildSpec
) -> dict[str, Path]:
    """Resolve only recognized detailed artifacts from configured inputs.

    Parameters
    ----------
    project_dir
        Configured repository root for relative path resolution.
    spec
        Build specification containing directory or explicit detailed files.

    Returns
    -------
    dict[str, Path]
        Canonical detailed basename to resolved regular source file.

    Raises
    ------
    ManifestBuildError
        If a detailed input is unsafe, duplicated, unrecognized, or unreadable.
    """

    if spec.detailed_artifacts_directory is not None:
        directory = _resolve_input_path(
            expect_directory=True,
            path=spec.detailed_artifacts_directory,
            project_dir=project_dir,
            role="detailed-artifact directory",
        )
        discovered: dict[str, Path] = {}

        for basename in sorted(_RECOGNIZED_DETAILED_ARTIFACTS):
            candidate = directory / basename

            if not os.path.lexists(candidate):
                continue

            if candidate.is_symlink():
                _build_error(
                    details={"artifact_path": str(candidate)},
                    message=(
                        f"Detailed artifact '{basename}' may not be a symbolic link."
                    ),
                )

            resolved_candidate = candidate.resolve(strict=False)

            if not resolved_candidate.is_relative_to(directory):
                _build_error(
                    details={
                        "artifact_path": str(candidate),
                        "detailed_directory": str(directory),
                    },
                    message=f"Detailed artifact '{basename}' escapes its directory.",
                )

            if not resolved_candidate.is_file():
                _build_error(
                    details={"artifact_path": str(candidate)},
                    message=f"Detailed artifact '{basename}' is not a regular file.",
                )

            discovered[basename] = resolved_candidate

        return discovered

    discovered = {}

    for input_path in spec.detailed_artifacts:
        resolved_path = _resolve_input_file(
            path=input_path, project_dir=project_dir, role="detailed artifact"
        )
        basename = resolved_path.name

        if basename not in _RECOGNIZED_DETAILED_ARTIFACTS:
            _build_error(
                details={"artifact_path": str(resolved_path)},
                message=f"Detailed artifact '{basename}' is not recognized.",
            )

        if basename in discovered:
            _build_error(
                details={
                    "artifact_path": str(resolved_path),
                    "existing_path": str(discovered[basename]),
                },
                message=f"Detailed artifact '{basename}' was declared more than once.",
            )

        discovered[basename] = resolved_path

    return discovered


def _ensure_destination_absent(plan: _PackagePlan) -> None:
    """Require the package destination to remain absent during materialization.

    Parameters
    ----------
    plan
        Candidate package plan whose destination must not yet exist.

    Raises
    ------
    _ExistingPackage
        If the destination already exists, signaling that the caller should return the
        existing-identical result instead of continuing to build.
    """

    if os.path.lexists(plan.destination):
        raise _ExistingPackage


def _expected_directories(expected_files: set[str]) -> set[str]:
    """Return every package-relative ancestor directory required by files.

    Parameters
    ----------
    expected_files
        Package-relative file paths.

    Returns
    -------
    set[str]
        Required package-relative directory paths.
    """

    directories: set[str] = set()

    for file_path in expected_files:
        pure_path = PurePosixPath(file_path)

        for parent in pure_path.parents:
            if str(parent) != ".":
                directories.add(parent.as_posix())

    return directories


def _handle_existing_package(plan: _PackagePlan) -> PackageBuildResult:
    """Validate exact pending-package equivalence without writing any files.

    Parameters
    ----------
    plan
        Candidate package-defining values and destination.

    Returns
    -------
    PackageBuildResult
        Existing identical pending-package outcome.

    Raises
    ------
    ManifestBuildError
        If the destination is terminal, malformed, incomplete, conflicting, or contains
        undeclared content.
    """

    destination = plan.destination

    if destination.is_symlink() or not destination.is_dir():
        _build_error(
            details={"destination": str(destination)},
            message=(
                "The graph-package destination exists but is not a regular directory."
            ),
        )

    manifest_path = destination / _MANIFEST_FILENAME

    if manifest_path.is_symlink() or not manifest_path.is_file():
        _build_error(
            details={"manifest_path": str(manifest_path)},
            message="The existing graph-package destination has no regular manifest.",
        )

    try:
        existing_manifest = GraphPackageManifest.model_validate_json(
            manifest_path.read_bytes()
        )
    except (OSError, ValidationError) as error:
        raise ManifestBuildError(
            details={"manifest_path": str(manifest_path)},
            message="The existing graph-package manifest is unreadable or malformed.",
        ) from error

    if existing_manifest.validation.status is not ValidationStatus.PENDING:
        _build_error(
            details={
                "destination": str(destination),
                "validation_status": existing_manifest.validation.status.value,
            },
            message=(
                "The graph-package destination contains a terminal package and may "
                "not be reused or overwritten."
            ),
        )

    candidate_manifest = _create_manifest(
        created_at=existing_manifest.created_at, plan=plan
    )

    if candidate_manifest != existing_manifest:
        _build_error(
            details={"destination": str(destination)},
            message=(
                "The existing pending package conflicts with the proposed "
                "package-defining manifest fields."
            ),
        )

    _require_exact_package_tree(
        checksums=existing_manifest.checksums, package_path=destination
    )
    _verify_packaged_artifact_checksums(
        checksums=existing_manifest.checksums, package_path=destination
    )
    _verify_input_fingerprints(plan)

    return PackageBuildResult(
        created_at_is_provisional=False,
        manifest=existing_manifest,
        manifest_path=manifest_path,
        outcome="existing_identical",
        package_path=destination,
        warnings=plan.warnings,
    )


def _materialize_package(plan: _PackagePlan) -> PackageBuildResult:
    """Copy, verify, and atomically materialize a new pending package.

    Parameters
    ----------
    plan
        Candidate package plan containing source files and destination.

    Returns
    -------
    PackageBuildResult
        Created or concurrently discovered identical-package outcome.

    Raises
    ------
    ManifestBuildError
        If staging, verification, locking, or atomic materialization fails.
    """

    destination = plan.destination
    framework_directory = _prepare_framework_directory(destination)
    lock_path = framework_directory / f".{plan.snapshot_id}.build.lock"
    lock_descriptor: int | None = None
    staging_path: Path | None = None

    try:
        lock_descriptor = _acquire_build_lock(lock_path=lock_path, plan=plan)
        _ensure_destination_absent(plan)
        staging_path = Path(
            tempfile.mkdtemp(
                dir=framework_directory, prefix=f".{plan.snapshot_id}.staging-"
            )
        )
        manifest = _stage_and_rename(plan=plan, staging_path=staging_path)
        staging_path = None
        return PackageBuildResult(
            created_at_is_provisional=False,
            manifest=manifest,
            manifest_path=destination / _MANIFEST_FILENAME,
            outcome="created",
            package_path=destination,
            warnings=plan.warnings,
        )
    except _ExistingPackage:
        return _handle_existing_package(plan)
    finally:
        if lock_descriptor is not None:
            os.close(lock_descriptor)

        if staging_path is not None:
            shutil.rmtree(ignore_errors=True, path=staging_path)

        if lock_descriptor is not None:
            try:
                lock_path.unlink(missing_ok=True)
            except OSError:
                pass


def _ordered_unique(values: tuple[str, ...]) -> tuple[str, ...]:
    """Preserve first-seen order while removing duplicate string values.

    Parameters
    ----------
    values
        Source-ordered string values.

    Returns
    -------
    tuple[str, ...]
        Values in first-seen order without duplicates.
    """

    return tuple(dict.fromkeys(values))


def _package_file_path(*, package_path: Path, relative_path: ArtifactPath) -> Path:
    """Resolve a validated POSIX artifact path beneath a package root.

    Parameters
    ----------
    package_path
        Package root directory.
    relative_path
        Validated manifest-relative POSIX artifact path.

    Returns
    -------
    Path
        Native filesystem path beneath the package root.
    """

    return package_path.joinpath(*PurePosixPath(str(relative_path)).parts)


def _prepare_artifacts(
    *, project_dir: Path, spec: PackageBuildSpec
) -> tuple[PackageArtifacts, tuple[_ArtifactSource, ...]]:
    """Resolve, validate, checksum, and declare all package artifacts.

    Parameters
    ----------
    project_dir
        Configured repository root for relative path resolution.
    spec
        Operator-supplied package build specification.

    Returns
    -------
    tuple[PackageArtifacts, tuple[_ArtifactSource, ...]]
        Established artifact contract and deterministically ordered source records.

    Raises
    ------
    ManifestBuildError
        If artifact names, sources, destinations, or declarations are unsafe or
        conflicting.
    """

    nodes_path = _resolve_input_file(
        path=spec.nodes, project_dir=project_dir, role="node delivery artifact"
    )
    relationships_path = _resolve_input_file(
        path=spec.relationships,
        project_dir=project_dir,
        role="relationship delivery artifact",
    )
    _require_delivery_basename(
        basename=nodes_path.name,
        pattern=DELIVERY_NODES_BASENAME_RE,
        role="node delivery artifact",
    )
    _require_delivery_basename(
        basename=relationships_path.name,
        pattern=DELIVERY_RELATIONSHIPS_BASENAME_RE,
        role="relationship delivery artifact",
    )

    detailed_paths = _discover_detailed_artifacts(project_dir=project_dir, spec=spec)
    artifact_values: dict[str, object] = {
        "additional_artifacts": {},
        "nodes": _artifact_path(f"delivery/{nodes_path.name}"),
        "relationships": _artifact_path(f"delivery/{relationships_path.name}"),
    }
    source_specs: list[tuple[str, ArtifactPath, Path]] = [
        ("nodes", cast(ArtifactPath, artifact_values["nodes"]), nodes_path),
        (
            "relationships",
            cast(ArtifactPath, artifact_values["relationships"]),
            relationships_path,
        ),
    ]

    for basename, resolved_path in sorted(detailed_paths.items()):
        field_name, manifest_name = _RECOGNIZED_DETAILED_ARTIFACTS[basename]
        package_path = _artifact_path(f"detailed/{basename}")
        artifact_values[field_name] = package_path
        source_specs.append((manifest_name, package_path, resolved_path))

    additional_artifacts: dict[ArtifactName, ArtifactPath] = {}
    selected_reserved_basenames = {
        nodes_path.name.casefold(),
        relationships_path.name.casefold(),
        *(name.casefold() for name in detailed_paths),
    }

    for logical_name, input_path in sorted(
        spec.additional_artifacts.items(),
        key=lambda item: (str(item[0]).casefold(), str(item[0])),
    ):
        normalized_logical_name = str(logical_name).casefold()

        if normalized_logical_name in _RESERVED_ADDITIONAL_LOGICAL_NAMES:
            _build_error(
                details={"logical_name": str(logical_name)},
                message=(
                    f"Additional artifact logical name '{logical_name}' is reserved."
                ),
            )

        resolved_path = _resolve_input_file(
            path=input_path, project_dir=project_dir, role="additional artifact"
        )
        basename = resolved_path.name
        _require_safe_as_basename(basename=basename, role="additional artifact")

        normalized_basename = basename.casefold()

        if (
            normalized_basename in _RECOGNIZED_DETAILED_BASENAMES_CASEFOLDED
            or DELIVERY_NODES_BASENAME_RE.fullmatch(normalized_basename)
            or DELIVERY_RELATIONSHIPS_BASENAME_RE.fullmatch(normalized_basename)
        ):
            _build_error(
                details={
                    "artifact_path": str(resolved_path),
                    "logical_name": str(logical_name),
                },
                message=(
                    f"Artifact '{basename}' must use its dedicated manifest field and "
                    f"cannot be declared as an additional artifact."
                ),
            )

        if basename.casefold() in selected_reserved_basenames:
            _build_error(
                details={
                    "artifact_path": str(resolved_path),
                    "logical_name": str(logical_name),
                },
                message=(
                    f"Additional artifact '{basename}' collides with another "
                    f"package artifact."
                ),
            )

        package_path = _artifact_path(f"additional/{basename}")
        additional_artifacts[logical_name] = package_path
        source_specs.append((str(logical_name), package_path, resolved_path))
        selected_reserved_basenames.add(basename.casefold())

    artifact_values["additional_artifacts"] = additional_artifacts

    try:
        artifacts = PackageArtifacts.model_validate(artifact_values)
    except ValidationError as error:
        raise ManifestBuildError(
            details={
                "validation_errors": error.errors(
                    include_input=False, include_url=False
                )
            },
            message="Artifact declarations do not satisfy the package contract.",
        ) from error

    _require_unique_artifact_sources(source_specs)
    sources = tuple(
        sorted(
            (
                _ArtifactSource(
                    manifest_name=manifest_name,
                    package_path=package_path,
                    sha256=_calculate_file_sha256(source_path),
                    source_path=source_path,
                )
                for manifest_name, package_path, source_path in source_specs
            ),
            key=lambda artifact: str(artifact.package_path),
        )
    )
    return artifacts, sources


def _prepare_framework_directory(destination: Path) -> Path:
    """Create and validate the framework output directory for a destination.

    Parameters
    ----------
    destination
        Final package directory whose parent is the framework output directory.

    Returns
    -------
    Path
        The validated framework output directory.

    Raises
    ------
    ManifestBuildError
        If the directory is a symbolic link, cannot be created, or does not resolve to
        a safe regular directory.
    """

    framework_directory = destination.parent

    if framework_directory.is_symlink():
        _build_error(
            details={"framework_directory": str(framework_directory)},
            message="The framework output directory may not be a symbolic link.",
        )

    try:
        framework_directory.mkdir(exist_ok=True, parents=True)
    except OSError as error:
        raise ManifestBuildError(
            details={"framework_directory": str(framework_directory)},
            message="The framework output directory could not be created.",
        ) from error

    resolved_framework_directory = framework_directory.resolve(strict=False)

    if (
        framework_directory.is_symlink()
        or not framework_directory.is_dir()
        or resolved_framework_directory != framework_directory
    ):
        _build_error(
            details={
                "framework_directory": str(framework_directory),
                "resolved_framework_directory": str(resolved_framework_directory),
            },
            message="The framework output path is not a safe regular directory.",
        )

    return framework_directory


def _prepare_plan(*, settings: BackendSettings, spec: PackageBuildSpec) -> _PackagePlan:
    """Derive all package-defining values before timestamp assignment or writes.

    Parameters
    ----------
    settings
        Validated repository path settings.
    spec
        Operator-supplied package build specification.

    Returns
    -------
    _PackagePlan
        Deterministic package plan ready for dry-run, equivalence, or materialization.

    Raises
    ------
    ManifestBuildError
        If package inputs cannot produce a coherent pending manifest.
    """

    if spec.package_revision != 1:
        _build_error(
            details={"package_revision": spec.package_revision},
            message="Currently supports only packageRevision 1.",
        )

    loaded_profile = load_curriculum_profile(
        profile_id=spec.profile_id,
        profile_root=settings.profile_root,
        profile_version=spec.profile_version,
    )
    profile = loaded_profile.profile

    if len(profile.framework_ids) != 1:
        _build_error(
            details={
                "framework_ids": tuple(str(value) for value in profile.framework_ids),
                "profile_id": str(profile.profile_id),
            },
            message=(
                "Manifest construction requires the selected profile to declare "
                "exactly one frameworkId."
            ),
        )

    framework_id = profile.framework_ids[0]
    artifacts, artifact_sources = _prepare_artifacts(
        project_dir=settings.project_dir, spec=spec
    )
    sources_by_name = {
        artifact.manifest_name: artifact for artifact in artifact_sources
    }
    facts = _decode_facts(
        hierarchy_relationship_type=profile.hierarchy.relationship_type,
        nodes_path=sources_by_name["nodes"].source_path,
        relationships_path=sources_by_name["relationships"].source_path,
    )
    source_document_fingerprint = _prepare_source_document(
        project_dir=settings.project_dir, source_document=spec.source_document
    )
    framework, rights = _derive_framework_metadata(
        facts=facts,
        profile=profile,
        source_document_sha256=(
            None
            if source_document_fingerprint is None
            else source_document_fingerprint.sha256
        ),
        spec=spec,
    )
    capabilities = _derive_capabilities(
        artifacts=artifacts, facts=facts, profile=profile
    )
    checksums = {
        artifact.package_path: artifact.sha256 for artifact in artifact_sources
    }
    artifact_set_sha256 = calculate_snapshot_artifact_set_sha256(
        tuple(checksums.values())
    )
    snapshot_id = build_snapshot_id(
        content_sha256=artifact_set_sha256,
        framework_id=framework_id,
        version_token=spec.version_token,
    )
    graph_package_id = build_initial_graph_package_id(snapshot_id)
    output_root = _resolve_output_root(
        output_root=spec.output_root, project_dir=settings.project_dir
    )
    destination = output_root / str(framework_id) / str(snapshot_id)
    counts = PackageCounts(
        additional_counts={
            ADDITIONAL_COUNT_CODED_ITEMS: facts.coded_items,
            ADDITIONAL_COUNT_MULTI_PARENT_TARGETS: facts.multi_parent_targets,
            ADDITIONAL_COUNT_UNRESOLVED_RELATIONSHIPS: (facts.unresolved_relationships),
        },
        framework_nodes=facts.framework_nodes,
        item_nodes=facts.item_nodes,
        relationships=facts.relationships,
    )
    profile_reference = ProfileReference(
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        sha256=loaded_profile.sha256,
    )
    return _PackagePlan(
        artifact_sources=artifact_sources,
        artifacts=artifacts,
        capabilities=capabilities,
        checksums=checksums,
        counts=counts,
        destination=destination,
        framework=framework,
        framework_id=framework_id,
        graph_package_id=graph_package_id,
        profile_fingerprint=_FileFingerprint(
            path=loaded_profile.path, sha256=loaded_profile.sha256
        ),
        profile_reference=profile_reference,
        rights=rights,
        snapshot_id=snapshot_id,
        snapshot_relations=spec.snapshot_relations,
        source_document_fingerprint=source_document_fingerprint,
        warnings=_derive_warnings(profile),
    )


def _prepare_source_document(
    *, project_dir: Path, source_document: Path | None
) -> _FileFingerprint | None:
    """Resolve and checksum an optional source document without packaging it.

    Parameters
    ----------
    project_dir
        Configured repository root for relative path resolution.
    source_document
        Optional source-document path.

    Returns
    -------
    _FileFingerprint | None
        Exact source-document fingerprint when supplied.
    """

    if source_document is None:
        return None

    resolved_path = _resolve_input_file(
        path=source_document, project_dir=project_dir, role="source document"
    )
    return _FileFingerprint(
        path=resolved_path, sha256=_calculate_file_sha256(resolved_path)
    )


def _require_delivery_basename(
    *, basename: str, pattern: re.Pattern[str], role: str
) -> None:
    """Require one canonical delivery artifact basename.

    Parameters
    ----------
    basename
        Source file basename.
    pattern
        Contract pattern for the delivery artifact role.
    role
        Safe role name used in public errors.

    Raises
    ------
    ManifestBuildError
        If the basename does not satisfy the canonical delivery contract.
    """

    if pattern.fullmatch(basename) is None:
        _build_error(
            details={"basename": basename, "role": role},
            message=f"The {role} must preserve its canonical as_-prefixed filename.",
        )


def _require_exact_agreement(
    *, field_name: str, profile_value: str, root_value: str
) -> None:
    """Require exact agreement for overlapping profile and root values.

    Parameters
    ----------
    field_name
        Safe semantic field label.
    profile_value
        Value declared by the selected profile.
    root_value
        Value decoded from the framework root.

    Raises
    ------
    ManifestBuildError
        If the two authoritative inputs disagree.
    """

    if profile_value != root_value:
        _build_error(
            details={
                "field_name": field_name,
                "profile_value": profile_value,
                "root_value": root_value,
            },
            message=(
                f"The selected profile and decoded framework root disagree on "
                f"{field_name}."
            ),
        )


def _require_exact_package_tree(
    *, checksums: dict[ArtifactPath, Sha256Digest], package_path: Path
) -> None:
    """Require a package tree to contain only its manifest and declared artifacts.

    Parameters
    ----------
    checksums
        Exact declared artifact paths and their checksums.
    package_path
        Existing or staged package directory.

    Raises
    ------
    ManifestBuildError
        If any declared entry is missing or any undeclared entry is present.
    """

    expected_files = {
        _MANIFEST_FILENAME,
        *(str(path) for path in checksums),
    }
    actual_files, actual_directories = _collect_tree_entries(package_path)
    expected_directories = _expected_directories(expected_files)

    if actual_files != expected_files or actual_directories != expected_directories:
        _build_error(
            details={
                "actual_directories": sorted(actual_directories),
                "actual_files": sorted(actual_files),
                "expected_directories": sorted(expected_directories),
                "expected_files": sorted(expected_files),
                "package_path": str(package_path),
            },
            message="The package is incomplete or contains undeclared content.",
        )


def _require_root_text(*, field_name: str, value: str | None) -> str:
    """Require a non-blank source-facing framework-root text value.

    Parameters
    ----------
    field_name
        Original or semantic field name used in diagnostics.
    value
        Decoded optional root value.

    Returns
    -------
    str
        Unchanged non-blank root value.

    Raises
    ------
    ManifestBuildError
        If the root value is omitted or blank.
    """

    if value is None or not value.strip():
        _build_error(
            details={"field_name": field_name, "root_value": value},
            message=f"The decoded framework root must declare {field_name}.",
        )

    return value


def _require_safe_as_basename(*, basename: str, role: str) -> None:
    """Require a safe original ``as_`` JSON or JSONL basename.

    Parameters
    ----------
    basename
        Source artifact basename.
    role
        Safe artifact role used in public errors.

    Raises
    ------
    ManifestBuildError
        If the basename is unsafe or lacks the canonical prefix.
    """

    if (
        CONTROL_CHARACTER_RE.search(basename)
        or ".." in basename
        or SAFE_AS_ARTIFACT_BASENAME_RE.fullmatch(basename) is None
    ):
        _build_error(
            details={"basename": basename, "role": role},
            message=f"The {role} does not have a safe as_-prefixed basename.",
        )


def _require_safe_path_input(*, path: Path, role: str) -> None:
    """Reject blank, control-character, and traversal-bearing input paths.

    Parameters
    ----------
    path
        Operator-supplied path before repository-root resolution.
    role
        Safe path role used in public errors.

    Raises
    ------
    ManifestBuildError
        If the path contains unsafe lexical components.
    """

    raw_path = str(path)

    if (
        raw_path in {"", "."}
        or CONTROL_CHARACTER_RE.search(raw_path)
        or ".." in path.parts
    ):
        _build_error(
            details={"input_path": raw_path, "role": role},
            message=f"The {role} path is unsafe.",
        )


def _require_unique_artifact_sources(
    source_specs: list[tuple[str, ArtifactPath, Path]],
) -> None:
    """Reject repeated files and case-insensitively colliding destinations.

    Parameters
    ----------
    source_specs
        Manifest name, package path, and resolved source path tuples.

    Raises
    ------
    ManifestBuildError
        If two declarations reuse one source file or destination.
    """

    destination_paths: dict[str, str] = {}
    source_identities: dict[tuple[int, int], str] = {}

    for manifest_name, package_path, source_path in source_specs:
        destination_key = str(package_path).casefold()

        if destination_key in destination_paths:
            _build_error(
                details={
                    "artifact_path": str(package_path),
                    "existing_artifact_path": destination_paths[destination_key],
                },
                message=(
                    f"Artifact destination '{package_path}' collides with another "
                    f"declared package path."
                ),
            )

        destination_paths[destination_key] = str(package_path)

        try:
            stat_result = source_path.stat()
        except OSError as error:
            raise ManifestBuildError(
                details={"source_path": str(source_path)},
                message=f"Artifact '{source_path.name}' could not be inspected.",
            ) from error

        source_identity = (stat_result.st_dev, stat_result.st_ino)

        if source_identity in source_identities:
            _build_error(
                details={
                    "existing_manifest_name": source_identities[source_identity],
                    "manifest_name": manifest_name,
                    "source_path": str(source_path),
                },
                message=(
                    f"Artifact '{source_path.name}' repeats a previously declared "
                    f"source file."
                ),
            )

        source_identities[source_identity] = manifest_name


def _resolve_input_file(*, path: Path, project_dir: Path, role: str) -> Path:
    """Resolve a safe input file from an absolute or project-relative path.

    Parameters
    ----------
    path
        Operator-supplied file path.
    project_dir
        Configured repository root for relative paths.
    role
        Safe role used in public errors.

    Returns
    -------
    Path
        Resolved regular file path.

    Raises
    ------
    ManifestBuildError
        If the file is unsafe, missing, a symlink, or escapes the project when supplied
        relatively.
    """

    return _resolve_input_path(
        expect_directory=False, path=path, project_dir=project_dir, role=role
    )


def _resolve_input_path(
    *, expect_directory: bool, path: Path, project_dir: Path, role: str
) -> Path:
    """Resolve and validate one operator-supplied input filesystem path.

    Parameters
    ----------
    expect_directory
        Whether the resolved path must be a directory rather than a file.
    path
        Operator-supplied path.
    project_dir
        Configured repository root for relative paths.
    role
        Safe role used in public errors.

    Returns
    -------
    Path
        Resolved regular file or directory.

    Raises
    ------
    ManifestBuildError
        If resolution is unsafe or the expected filesystem object is unavailable.
    """

    _require_safe_path_input(path=path, role=role)
    expanded_path = path.expanduser()
    was_relative = not expanded_path.is_absolute()
    requested_path = (
        project_dir.expanduser().resolve(strict=False) / expanded_path
        if was_relative
        else expanded_path
    )

    if requested_path.is_symlink():
        _build_error(
            details={"input_path": str(requested_path), "role": role},
            message=f"The {role} may not be a symbolic link.",
        )

    resolved_path = requested_path.resolve(strict=False)
    resolved_project_dir = project_dir.expanduser().resolve(strict=False)

    if was_relative and not resolved_path.is_relative_to(resolved_project_dir):
        _build_error(
            details={"input_path": str(requested_path), "role": role},
            message=f"The relative {role} escapes the configured project root.",
        )

    exists_as_expected = (
        resolved_path.is_dir() if expect_directory else resolved_path.is_file()
    )

    if not exists_as_expected:
        expected_kind = "directory" if expect_directory else "file"
        _build_error(
            details={"input_path": str(resolved_path), "role": role},
            message=f"The {role} is not an available regular {expected_kind}.",
        )

    return resolved_path


def _resolve_output_root(*, output_root: Path, project_dir: Path) -> Path:
    """Resolve a safe absolute package-output root without creating it.

    Parameters
    ----------
    output_root
        Operator-supplied absolute or project-relative package root.
    project_dir
        Configured repository root for relative path resolution.

    Returns
    -------
    Path
        Resolved output root.

    Raises
    ------
    ManifestBuildError
        If the output path is unsafe, a symlink, escapes the project when relative, or
        already exists as a non-directory.
    """

    _require_safe_path_input(path=output_root, role="output root")
    expanded_path = output_root.expanduser()
    was_relative = not expanded_path.is_absolute()
    requested_path = (
        project_dir.expanduser().resolve(strict=False) / expanded_path
        if was_relative
        else expanded_path
    )

    if requested_path.is_symlink():
        _build_error(
            details={"output_root": str(requested_path)},
            message="The output root may not be a symbolic link.",
        )

    resolved_path = requested_path.resolve(strict=False)
    resolved_project_dir = project_dir.expanduser().resolve(strict=False)

    if was_relative and not resolved_path.is_relative_to(resolved_project_dir):
        _build_error(
            details={"output_root": str(requested_path)},
            message="The relative output root escapes the configured project root.",
        )

    if os.path.lexists(resolved_path) and not resolved_path.is_dir():
        _build_error(
            details={"output_root": str(resolved_path)},
            message="The output root exists but is not a regular directory.",
        )

    return resolved_path


def _scan_node_facts(nodes_path: Path) -> _NodeFacts:
    """Stream node artifacts, derive counts, and require a single root.

    Parameters
    ----------
    nodes_path
        Accepted node delivery artifact.

    Returns
    -------
    _NodeFacts
        Node-derived counts and the single decoded framework root.

    Raises
    ------
    ManifestBuildError
        If the artifact does not decode to exactly one framework root.
    """

    coded_items = 0
    framework_roots: list[FrameworkNode] = []
    item_nodes = 0
    text_items = 0

    for node in iter_decoded_nodes(source=nodes_path):
        if isinstance(node, FrameworkNode):
            framework_roots.append(node)
            continue

        if isinstance(node, StandardNode):
            item_nodes += 1

            if node.statement_code is not None and node.statement_code.strip():
                coded_items += 1

            if node.description is not None and node.description.strip():
                text_items += 1

    if len(framework_roots) != 1:
        _build_error(
            details={
                "framework_root_count": len(framework_roots),
                "nodes_path": str(nodes_path),
            },
            message=(
                f"Delivery artifact '{nodes_path.name}' must contain exactly one "
                f"decoded StandardsFramework root."
            ),
        )

    return _NodeFacts(
        coded_items=coded_items,
        framework_root=framework_roots[0],
        item_nodes=item_nodes,
        text_items=text_items,
    )


def _scan_relationship_facts(
    *, hierarchy_relationship_type: str, relationships_path: Path
) -> _RelationshipFacts:
    """Stream relationship artifacts, validate status, and derive topology.

    Parameters
    ----------
    hierarchy_relationship_type
        Profile-declared relationship label used for parent topology evidence.
    relationships_path
        Accepted relationship delivery artifact.

    Returns
    -------
    _RelationshipFacts
        Relationship-derived counts and parent-topology evidence.

    Raises
    ------
    ManifestBuildError
        If any relationship status violates delivery schema 1.0.
    """

    parent_sources: dict[str, set[str]] = {}
    relationship_count = 0
    unresolved_relationships = 0

    for relationship in iter_decoded_relationships(source=relationships_path):
        relationship_count += 1
        resolution_status = relationship.resolution_status

        if resolution_status is not None:
            _validate_relationship_status(
                relationships_path=relationships_path,
                resolution_status=resolution_status,
                source_export_order=relationship.source_export_order,
            )

            if (
                resolution_status
                in DELIVERY_SCHEMA_1_0_UNRESOLVED_RELATIONSHIP_STATUSES
            ):
                unresolved_relationships += 1

        if relationship.label == hierarchy_relationship_type:
            target_key = str(relationship.target_node_id)
            parent_sources.setdefault(target_key, set()).add(
                str(relationship.source_node_id)
            )

    multi_parent_targets = sum(
        len(source_ids) > 1 for source_ids in parent_sources.values()
    )
    return _RelationshipFacts(
        multi_parent_targets=multi_parent_targets,
        relationships=relationship_count,
        unresolved_relationships=unresolved_relationships,
    )


def _stage_and_rename(
    *, plan: _PackagePlan, staging_path: Path
) -> GraphPackageManifest:
    """Populate, verify, and atomically publish a package from staging.

    Copies source artifacts into the staging directory, verifies packaged checksums and
    input fingerprints, stages the verified manifest, and atomically renames staging
    into the final destination. The destination is rechecked before each irreversible
    step so a concurrent build is recognized rather than overwritten.

    Parameters
    ----------
    plan
        Candidate package plan supplying source files, checksums, and destination.
    staging_path
        Existing staging directory on the destination filesystem.

    Returns
    -------
    GraphPackageManifest
        The manifest published into the final destination.

    Raises
    ------
    _ExistingPackage
        If the destination appears before or during atomic materialization.
    ManifestBuildError
        If copying, verification, or atomic materialization fails.
    """

    _copy_artifacts(artifact_sources=plan.artifact_sources, staging_path=staging_path)
    _verify_packaged_artifact_checksums(
        checksums=plan.checksums, package_path=staging_path
    )
    _verify_input_fingerprints(plan)
    _ensure_destination_absent(plan)
    manifest = _stage_verified_package(plan=plan, staging_path=staging_path)
    _ensure_destination_absent(plan)

    try:
        _atomic_rename_no_replace(destination=plan.destination, source=staging_path)
    except OSError as error:
        if os.path.lexists(plan.destination):
            raise _ExistingPackage from error

        raise ManifestBuildError(
            details={
                "destination": str(plan.destination),
                "staging_path": str(staging_path),
            },
            message="The staged package could not be materialized atomically.",
        ) from error

    return manifest


def _stage_verified_package(
    *, plan: _PackagePlan, staging_path: Path
) -> GraphPackageManifest:
    """Create, write, and verify the manifest and artifacts in staging.

    Parameters
    ----------
    plan
        Candidate package plan supplying manifest-defining values.
    staging_path
        Verified staging directory already populated with copied artifacts.

    Returns
    -------
    GraphPackageManifest
        The manifest written into and verified against the staging directory.

    Raises
    ------
    ManifestBuildError
        If the manifest cannot be written completely or any staged artifact, the staged
        tree, or the staged manifest fails verification.
    """

    manifest = _create_manifest(created_at=_utc_now_seconds(), plan=plan)
    staged_manifest_path = staging_path / _MANIFEST_FILENAME
    manifest_bytes = _canonical_manifest_bytes(manifest)

    try:
        with staged_manifest_path.open("xb") as stream:
            written_bytes = stream.write(manifest_bytes)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as error:
        raise ManifestBuildError(
            details={"manifest_path": str(staged_manifest_path)},
            message="The staged package manifest could not be written safely.",
        ) from error

    if written_bytes != len(manifest_bytes):
        _build_error(
            details={
                "actual_byte_count": written_bytes,
                "expected_byte_count": len(manifest_bytes),
                "manifest_path": str(staged_manifest_path),
            },
            message="The staged package manifest was not written completely.",
        )

    _require_exact_package_tree(checksums=manifest.checksums, package_path=staging_path)
    _verify_packaged_artifact_checksums(
        checksums=manifest.checksums, package_path=staging_path
    )
    _verify_staged_manifest(
        expected_manifest=manifest, manifest_path=staged_manifest_path
    )
    _verify_input_fingerprints(plan)
    return manifest


def _utc_now_seconds() -> datetime:
    """Return the current UTC time with deterministic whole-second precision.

    Returns
    -------
    datetime
        Timezone-aware UTC timestamp without fractional seconds.
    """

    return datetime.now(timezone.utc).replace(microsecond=0)


def _validate_relationship_status(
    *, relationships_path: Path, resolution_status: str, source_export_order: int
) -> None:
    """Require one relationship status to satisfy delivery schema 1.0.

    Parameters
    ----------
    relationships_path
        Accepted relationship delivery artifact, used for diagnostics.
    resolution_status
        Non-null status value observed on the relationship.
    source_export_order
        One-based export line number, used for diagnostics.

    Raises
    ------
    ManifestBuildError
        If the status is blank or outside the delivery schema 1.0 vocabulary.
    """

    if not resolution_status.strip():
        _build_error(
            details={
                "line_number": source_export_order,
                "raw_resolution_status": resolution_status,
                "relationships_path": str(relationships_path),
            },
            message=(
                f"Relationship status in '{relationships_path.name}' at line "
                f"{source_export_order} is blank."
            ),
        )

    if resolution_status not in DELIVERY_SCHEMA_1_0_RELATIONSHIP_STATUS_VOCABULARY:
        _build_error(
            details={
                "line_number": source_export_order,
                "raw_resolution_status": resolution_status,
                "relationships_path": str(relationships_path),
            },
            message=(
                f"Relationship status in '{relationships_path.name}' at line "
                f"{source_export_order} is not defined by delivery schema 1.0."
            ),
        )


def _verify_input_fingerprints(plan: _PackagePlan) -> None:
    """Require every planned input to remain unchanged through construction.

    Parameters
    ----------
    plan
        Package plan containing exact-byte fingerprints.

    Raises
    ------
    ManifestBuildError
        If an artifact, profile, or optional source document changes after planning.
    """

    for artifact in plan.artifact_sources:
        actual_sha256 = _calculate_file_sha256(artifact.source_path)

        if actual_sha256 != artifact.sha256:
            _build_error(
                details={
                    "actual_sha256": str(actual_sha256),
                    "expected_sha256": str(artifact.sha256),
                    "source_path": str(artifact.source_path),
                },
                message=(
                    f"Artifact '{artifact.source_path.name}' changed during manifest "
                    f"construction."
                ),
            )

    profile_actual_sha256 = _calculate_file_sha256(plan.profile_fingerprint.path)

    if profile_actual_sha256 != plan.profile_fingerprint.sha256:
        _build_error(
            details={
                "actual_sha256": str(profile_actual_sha256),
                "expected_sha256": str(plan.profile_fingerprint.sha256),
                "profile_path": str(plan.profile_fingerprint.path),
            },
            message="The selected profile changed during manifest construction.",
        )

    if plan.source_document_fingerprint is None:
        return

    source_document_actual_sha256 = _calculate_file_sha256(
        plan.source_document_fingerprint.path
    )

    if source_document_actual_sha256 != plan.source_document_fingerprint.sha256:
        _build_error(
            details={
                "actual_sha256": str(source_document_actual_sha256),
                "expected_sha256": str(plan.source_document_fingerprint.sha256),
                "source_document_path": str(plan.source_document_fingerprint.path),
            },
            message="The source document changed during manifest construction.",
        )


def _verify_packaged_artifact_checksums(
    *, checksums: dict[ArtifactPath, Sha256Digest], package_path: Path
) -> None:
    """Require every packaged artifact to match its declared exact-byte checksum.

    Parameters
    ----------
    checksums
        Declared package-relative artifact checksums.
    package_path
        Existing or staged package directory.

    Raises
    ------
    ManifestBuildError
        If any packaged artifact differs from its declared checksum.
    """

    for artifact_path, expected_sha256 in checksums.items():
        packaged_path = _package_file_path(
            package_path=package_path, relative_path=artifact_path
        )
        actual_sha256 = _calculate_file_sha256(packaged_path)

        if actual_sha256 != expected_sha256:
            _build_error(
                details={
                    "actual_sha256": str(actual_sha256),
                    "artifact_path": str(artifact_path),
                    "expected_sha256": str(expected_sha256),
                    "package_path": str(package_path),
                },
                message=(
                    f"Packaged artifact '{packaged_path.name}' does not match its "
                    f"declared checksum."
                ),
            )


def _verify_staged_manifest(
    *, expected_manifest: GraphPackageManifest, manifest_path: Path
) -> None:
    """Require staged manifest bytes and parsed values to match the candidate.

    Parameters
    ----------
    expected_manifest
        In-memory manifest used to create the staged bytes.
    manifest_path
        Staged manifest path.

    Raises
    ------
    ManifestBuildError
        If the staged manifest is unreadable, noncanonical, or semantically different.
    """

    expected_bytes = _canonical_manifest_bytes(expected_manifest)

    try:
        actual_bytes = manifest_path.read_bytes()
        actual_manifest = GraphPackageManifest.model_validate_json(actual_bytes)
    except (OSError, ValidationError) as error:
        raise ManifestBuildError(
            details={"manifest_path": str(manifest_path)},
            message="The staged package manifest could not be verified.",
        ) from error

    if actual_bytes != expected_bytes or actual_manifest != expected_manifest:
        _build_error(
            details={"manifest_path": str(manifest_path)},
            message="The staged package manifest differs from the candidate manifest.",
        )


def build_graph_package(
    *, dry_run: bool, settings: BackendSettings, spec: PackageBuildSpec
) -> PackageBuildResult:
    """Build, dry-run, or idempotently recognize one pending graph package.

    Parameters
    ----------
    dry_run
        Whether to return a proposed manifest without creating filesystem content.
    settings
        Validated repository and profile path settings.
    spec
        Operator-supplied build specification.

    Returns
    -------
    PackageBuildResult
        Proposed, created, or existing-identical package result.

    Raises
    ------
    ManifestBuildError
        If the package cannot be constructed safely and truthfully.
    """

    plan = _prepare_plan(settings=settings, spec=spec)
    _verify_input_fingerprints(plan)

    if os.path.lexists(plan.destination):
        return _handle_existing_package(plan)

    if dry_run:
        manifest = _create_manifest(created_at=_utc_now_seconds(), plan=plan)
        warning = (
            "createdAt is provisional in dry-run output and may differ when the "
            "package is materialized."
        )
        return PackageBuildResult(
            created_at_is_provisional=True,
            manifest=manifest,
            manifest_path=plan.destination / _MANIFEST_FILENAME,
            outcome="dry_run",
            package_path=plan.destination,
            warnings=(*plan.warnings, warning),
        )

    return _materialize_package(plan)
