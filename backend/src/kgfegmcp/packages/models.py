"""This module contains Pydantic models for immutable curriculum graph-package
manifests.

This module defines the validated contracts that describe one versioned graph package.
The models represent aspects such as framework metadata, package capabilities,
package-relative artifact paths, artifact checksums, expected graph counts, validation
state, curriculum-profile references, snapshot-family relations, rights policy, and
package identity.

Cross-field validation ensures that framework, snapshot, and graph-package identities
agree; every declared artifact has exactly one checksum; graph types are declared
consistently; timestamps are timezone-aware; and snapshot relations are unique and do
not reference the snapshot itself.

These models describe and validate package metadata only. They do not parse JSONL graph
records, traverse graphs, interpret curriculum terminology, repair source data, or
modify source artifacts. Loaders, checksum verification, and graph validation services
consume these immutable contracts at the package boundary.
"""

# Standard Library
from datetime import date, datetime
from pathlib import Path
from typing import Final, Literal, Self, cast

# Third Party Library
from pydantic import Field, field_validator, model_validator

# Package Library
from kgfegmcp.domain.enums import (
    CodeAvailability,
    GraphType,
    SnapshotRelationType,
    SubjectMappingStatus,
    ValidationStatus,
)
from kgfegmcp.domain.identifiers import (
    ArtifactName,
    ArtifactPath,
    FrameworkId,
    GraphPackageId,
    LanguageTag,
    ManifestVersion,
    ProfileId,
    ProfileVersion,
    SchemaVersion,
    Sha256Digest,
    SnapshotId,
    SnapshotVersionToken,
    build_versioned_graph_package_id,
)
from kgfegmcp.domain.models import RightsPolicy
from kgfegmcp.schemas import FrozenSchema

DELIVERY_SCHEMA_VERSION: Final[SchemaVersion] = cast(typ=SchemaVersion, val="1.0")
SOURCE_SCHEMA_VERSION: Final[SchemaVersion] = cast(typ=SchemaVersion, val="1.0")


def _require_timezone_aware(*, field_name: str, value: datetime) -> None:
    """Require a datetime value to include an effective UTC offset.

    Parameters
    ----------
    field_name
        Field name used in the validation error.
    value
        Datetime to validate.

    Raises
    ------
    ValueError
        If the datetime is naive or has no effective UTC offset.
    """

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware.")


def _require_unique(*, field_name: str, values: tuple[str, ...]) -> None:
    """Require a tuple of strings to contain no duplicates.

    Parameters
    ----------
    field_name
        Field name used in the validation error.
    values
        String values to validate.

    Raises
    ------
    ValueError
        If duplicate values are present.
    """

    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must not contain duplicates.")


class FrameworkCapabilities(FrozenSchema):
    """Declare query and artifact capabilities for one framework snapshot."""

    code_search: CodeAvailability
    has_detailed_provenance: bool = False
    has_official_activities: bool = False
    has_official_assessment_guidance: bool = False
    has_unresolved_relationships: bool = False
    multi_parent: bool = False
    text_search: bool = True


class FrameworkMetadata(FrozenSchema):
    """Describe source-faithful and normalized framework metadata."""

    adoption_status: str | None = None
    is_current: bool
    issuing_authority: str | None = None
    jurisdiction: str = Field(min_length=1)
    jurisdiction_type: str | None = None
    languages: tuple[LanguageTag, ...] = Field(min_length=1)
    local_grades_or_stages: tuple[str, ...]
    local_subject: str = Field(min_length=1)
    name: str = Field(min_length=1)
    normalized_grades: tuple[str, ...]
    normalized_subjects: tuple[str, ...]
    provider: str | None = None
    source_document_sha256: Sha256Digest | None = None
    source_publication_date: date | None = None
    source_version: str | None = None
    subject_mapping_note: str | None = None
    subject_mapping_status: SubjectMappingStatus

    @model_validator(mode="after")
    def validate_metadata(self) -> Self:
        """Validate collection uniqueness and subject-mapping state.

        Returns
        -------
        Self
            Validated framework metadata.

        Raises
        ------
        ValueError
            If collection values are duplicated or subject mapping fields conflict.
        """

        for field_name, values in (
            ("languages", tuple(str(value) for value in self.languages)),
            ("local_grades_or_stages", self.local_grades_or_stages),
            ("normalized_grades", self.normalized_grades),
            ("normalized_subjects", self.normalized_subjects),
        ):
            _require_unique(field_name=field_name, values=values)

        if (
            self.subject_mapping_status is SubjectMappingStatus.UNREVIEWED
            and self.normalized_subjects
        ):
            raise ValueError(
                "Unreviewed subject mappings may not declare normalized subjects."
            )

        if (
            self.subject_mapping_status is not SubjectMappingStatus.UNREVIEWED
            and not self.normalized_subjects
        ):
            raise ValueError(
                "Reviewed subject mappings must declare normalized subjects."
            )

        if (
            self.subject_mapping_status is SubjectMappingStatus.OTHER
            and not self.subject_mapping_note
        ):
            raise ValueError("Other subject mappings require subject_mapping_note.")

        return self


class PackageArtifacts(FrozenSchema):
    """Declare immutable package-relative artifact paths."""

    academic_standards_bundle: ArtifactPath | None = None
    additional_artifacts: dict[ArtifactName, ArtifactPath] = Field(default_factory=dict)
    entity_provenance: ArtifactPath | None = None
    nodes: ArtifactPath
    relationships: ArtifactPath
    relationships_has_child: ArtifactPath | None = None
    standards_framework: ArtifactPath | None = None
    standards_framework_items: ArtifactPath | None = None
    unresolved_items: ArtifactPath | None = None
    validation_report: ArtifactPath | None = None

    @model_validator(mode="after")
    def validate_artifacts(self) -> Self:
        """Validate artifact-name and path uniqueness.

        Returns
        -------
        Self
            Validated artifact declaration.

        Raises
        ------
        ValueError
            If an additional name is reserved or two names resolve to one path.
        """

        reserved_names = {
            "academicStandardsBundle",
            "entityProvenance",
            "nodes",
            "relationships",
            "relationshipsHasChild",
            "standardsFramework",
            "standardsFrameworkItems",
            "unresolvedItems",
            "validationReport",
        }
        conflicting_names = reserved_names.intersection(
            str(name) for name in self.additional_artifacts
        )

        if conflicting_names:
            formatted_names = ", ".join(sorted(conflicting_names))
            raise ValueError(
                f"additional_artifacts uses reserved names: {formatted_names}."
            )

        paths = tuple(str(path) for path in self.declared_artifacts().values())
        _require_unique(field_name="artifact paths", values=paths)
        return self

    def declared_artifacts(self) -> dict[str, ArtifactPath]:
        """Return every declared artifact by its public manifest name.

        Returns
        -------
        dict[str, ArtifactPath]
            Deterministically ordered artifact-name to path mapping.
        """

        artifacts: dict[str, ArtifactPath] = {
            "nodes": self.nodes,
            "relationships": self.relationships,
        }
        optional_artifacts = {
            "academicStandardsBundle": self.academic_standards_bundle,
            "entityProvenance": self.entity_provenance,
            "relationshipsHasChild": self.relationships_has_child,
            "standardsFramework": self.standards_framework,
            "standardsFrameworkItems": self.standards_framework_items,
            "unresolvedItems": self.unresolved_items,
            "validationReport": self.validation_report,
        }
        artifacts.update(
            {
                name: path
                for name, path in optional_artifacts.items()
                if path is not None
            }
        )
        artifacts.update(
            {
                str(name): path
                for name, path in sorted(
                    self.additional_artifacts.items(),
                    key=lambda item: str(item[0]),
                )
            }
        )
        return artifacts


class PackageCounts(FrozenSchema):
    """Record declared graph and optional artifact counts."""

    additional_counts: dict[str, int] = Field(default_factory=dict)
    framework_nodes: int = Field(default=1, ge=1, le=1)
    item_nodes: int = Field(ge=0)
    relationships: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_additional_counts(self) -> Self:
        """Validate optional count names and values.

        Returns
        -------
        Self
            Validated package counts.

        Raises
        ------
        ValueError
            If an additional count name is blank or a value is negative.
        """

        for name, value in self.additional_counts.items():
            if not name.strip():
                raise ValueError("additional_counts keys must be non-empty.")

            if value < 0:
                raise ValueError("additional_counts values must be non-negative.")

        return self


class PackageValidation(FrozenSchema):
    """Record deterministic package-validation state."""

    status: ValidationStatus
    validated_at: datetime | None = None

    @model_validator(mode="after")
    def validate_timestamp(self) -> Self:
        """Validate timestamp requirements for terminal statuses.

        Returns
        -------
        Self
            Validated package-validation record.

        Raises
        ------
        ValueError
            If a terminal status lacks a timestamp or a timestamp is naive.
        """

        terminal_statuses = {
            ValidationStatus.FAILED,
            ValidationStatus.PASSED,
            ValidationStatus.QUARANTINED,
        }

        if self.status in terminal_statuses and self.validated_at is None:
            raise ValueError("Terminal validation statuses require validated_at.")

        if self.status is ValidationStatus.PENDING and self.validated_at is not None:
            raise ValueError("Pending validation status may not declare validated_at.")

        if self.validated_at is not None:
            _require_timezone_aware(field_name="validated_at", value=self.validated_at)

        return self


class ProfileReference(FrozenSchema):
    """Reference one immutable curriculum interpretation profile."""

    profile_id: ProfileId
    profile_version: ProfileVersion
    sha256: Sha256Digest


class SnapshotRelation(FrozenSchema):
    """Describe an operator-supplied relationship to another snapshot."""

    evidence: str | None = None
    relation_type: SnapshotRelationType
    target_snapshot_id: SnapshotId


class GraphPackageManifest(FrozenSchema):
    """Describe one immutable, validated graph package."""

    artifacts: PackageArtifacts
    capabilities: FrameworkCapabilities
    checksums: dict[ArtifactPath, Sha256Digest]
    counts: PackageCounts
    created_at: datetime
    delivery_schema_version: SchemaVersion
    framework: FrameworkMetadata
    framework_id: FrameworkId
    graph_package_id: GraphPackageId
    graph_type: GraphType
    included_graph_types: tuple[GraphType, ...] = Field(min_length=1)
    manifest_version: ManifestVersion = cast(ManifestVersion, "1.0")
    package_revision: int = Field(default=1, ge=1)
    profile: ProfileReference
    rights: RightsPolicy
    snapshot_id: SnapshotId
    snapshot_relations: tuple[SnapshotRelation, ...] = ()
    source_schema_version: SchemaVersion
    validation: PackageValidation

    @model_validator(mode="after")
    def validate_manifest(self) -> Self:
        """Validate manifest identities, artifacts, relations, and timestamps.

        Returns
        -------
        Self
            Fully validated package manifest.

        Raises
        ------
        ValueError
            If package identities, checksums, graph types, or relations conflict.
        """

        _require_timezone_aware(field_name="created_at", value=self.created_at)

        snapshot_framework_id = str(self.snapshot_id).partition("@")[0]

        if snapshot_framework_id != str(self.framework_id):
            raise ValueError("snapshot_id must be namespaced by framework_id.")

        expected_versioned_package_id = build_versioned_graph_package_id(
            graph_type=self.graph_type,
            package_revision=self.package_revision,
            snapshot_id=self.snapshot_id,
        )
        initial_package_id = str(self.snapshot_id)
        supplied_package_id = str(self.graph_package_id)
        allowed_package_ids = {initial_package_id, str(expected_versioned_package_id)}

        if supplied_package_id not in allowed_package_ids:
            raise ValueError(
                "graph_package_id must equal snapshot_id or the graph-type package ID."
            )

        if supplied_package_id == initial_package_id:
            if self.package_revision != 1:
                raise ValueError(
                    "A graph_package_id equal to snapshot_id requires package_revision=1."
                )

            if self.included_graph_types != (self.graph_type,):
                raise ValueError(
                    "An initial graph_package_id may include only its primary graph_type."
                )

        if self.graph_type not in self.included_graph_types:
            raise ValueError("included_graph_types must contain graph_type.")

        _require_unique(
            field_name="included_graph_types",
            values=tuple(value.value for value in self.included_graph_types),
        )

        declared_paths = {
            str(path) for path in self.artifacts.declared_artifacts().values()
        }
        checksum_paths = {str(path) for path in self.checksums}

        if checksum_paths != declared_paths:
            missing_paths = sorted(declared_paths - checksum_paths)
            unexpected_paths = sorted(checksum_paths - declared_paths)
            raise ValueError(
                f"checksums must cover exactly the declared artifact paths; "
                f"missing={missing_paths}, unexpected={unexpected_paths}."
            )

        relation_keys = tuple(
            (relation.relation_type.value, str(relation.target_snapshot_id))
            for relation in self.snapshot_relations
        )

        if len(relation_keys) != len(set(relation_keys)):
            raise ValueError("snapshot_relations must not contain duplicates.")

        if any(
            relation.target_snapshot_id == self.snapshot_id
            for relation in self.snapshot_relations
        ):
            raise ValueError("A snapshot may not relate to itself.")

        return self


class PackageBuildResult(FrozenSchema):
    """Return the deterministic result of creating or proposing one package."""

    created_at_is_provisional: bool = False
    manifest: GraphPackageManifest
    manifest_path: Path
    outcome: Literal["created", "dry_run", "existing_identical"]
    package_path: Path
    warnings: tuple[str, ...] = ()


class PackageBuildSpec(FrozenSchema):
    """Describe operator-supplied inputs for one deterministic package build."""

    additional_artifacts: dict[ArtifactName, Path] = Field(default_factory=dict)
    detailed_artifacts: tuple[Path, ...] = ()
    detailed_artifacts_directory: Path | None = None
    jurisdiction_type: str = Field(min_length=1)
    nodes: Path
    output_root: Path
    package_revision: Literal[1] = 1
    profile_id: ProfileId
    profile_version: ProfileVersion
    relationships: Path
    snapshot_relations: tuple[SnapshotRelation, ...] = ()
    source_document: Path | None = None
    source_publication_date: date | None = None
    version_token: SnapshotVersionToken

    @field_validator("jurisdiction_type")
    @classmethod
    def validate_jurisdiction_type(cls, value: str) -> str:
        """Require a non-empty jurisdiction type without surrounding whitespace.

        Parameters
        ----------
        value
            Operator-supplied jurisdiction type.

        Returns
        -------
        str
            The unchanged validated jurisdiction type.

        Raises
        ------
        ValueError
            If the value is blank or contains surrounding whitespace.
        """

        if value != value.strip():
            raise ValueError(
                "jurisdiction_type may not contain surrounding whitespace."
            )

        if not value:
            raise ValueError("jurisdiction_type must be non-empty.")

        return value

    @model_validator(mode="after")
    def validate_detailed_artifact_inputs(self) -> Self:
        """Reject ambiguous detailed-artifact discovery inputs.

        Returns
        -------
        Self
            The validated build specification.

        Raises
        ------
        ValueError
            If both a detailed-artifact directory and explicit files are supplied.
        """

        if self.detailed_artifacts_directory is not None and self.detailed_artifacts:
            raise ValueError(
                "detailed_artifacts_directory and detailed_artifacts are mutually exclusive."
            )

        logical_names = tuple(
            str(name).casefold() for name in self.additional_artifacts
        )

        if len(logical_names) != len(set(logical_names)):
            raise ValueError(
                "additional_artifacts logical names must be case-insensitively unique."
            )

        return self
