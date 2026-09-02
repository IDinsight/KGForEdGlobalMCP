"""This module defines immutable graph-package manifest, loading, and validation
contracts.

This module defines the validated contracts that describe one versioned graph package.
The models represent aspects such as framework metadata, package capabilities,
package-relative artifact paths, artifact checksums, expected graph counts, validation
state, curriculum-profile references, snapshot-family relations, rights policy, and
package identity.

Cross-field validation ensures that framework, snapshot, and graph-package identities
agree; every declared artifact has exactly one checksum; graph types are declared
consistently; timestamps are timezone-aware; and snapshot relations are unique and do
not reference the snapshot itself.

The module also defines the small supported detailed-validation-report contract, safe
declared-artifact references, immutable package-integrity observations and snapshots,
the frozen loaded-package aggregate, and structured validation findings and results. It
does not parse JSONL records, expose a reusable graph store, repair source data, or
modify package artifacts.
"""

# Standard Library
from collections.abc import Mapping
from datetime import date, datetime
from pathlib import Path
from typing import Annotated, Final, Literal, Self, cast

# Third Party Library
from pydantic import (
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    StrictStr,
    StringConstraints,
    field_validator,
    model_validator,
)

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
from kgfegmcp.graph.models import (
    FrameworkNode,
    GraphRelationship,
    LearningComponentNode,
    StandardNode,
)
from kgfegmcp.profiles.models import CurriculumProfile
from kgfegmcp.schemas import FrozenSchema

ADDITIONAL_COUNT_CODED_ITEMS: Final[str] = "codedItems"
ADDITIONAL_COUNT_MULTI_PARENT_TARGETS: Final[str] = "multiParentTargets"
ADDITIONAL_COUNT_UNRESOLVED_RELATIONSHIPS: Final[str] = "unresolvedRelationships"
DELIVERY_REPORT_COUNT_FRAMEWORK_NODES: Final[str] = "learning_commons_framework_nodes"
DELIVERY_REPORT_COUNT_ITEM_NODES: Final[str] = "learning_commons_item_nodes"
DELIVERY_REPORT_COUNT_LEARNING_COMPONENT_NODES: Final[str] = (
    "learning_commons_learning_component_nodes"
)
DELIVERY_REPORT_COUNT_SUPPORTS_RELATIONSHIPS: Final[str] = (
    "learning_commons_supports_relationships"
)
DELIVERY_REPORT_COUNT_RELATIONSHIPS: Final[str] = "learning_commons_relationships"
DELIVERY_REPORT_COUNT_UNRESOLVED_RELATIONSHIPS: Final[str] = (
    "learning_commons_unresolved_fallback_relationships"
)
DELIVERY_SCHEMA_VERSION: Final[SchemaVersion] = cast(SchemaVersion, "1.1")
SUPPORTED_INCLUDED_GRAPH_TYPES: Final[tuple[GraphType, ...]] = (
    GraphType.ACADEMIC_STANDARDS,
    GraphType.LEARNING_COMPONENTS,
)
MANIFEST_VERSION: Final[ManifestVersion] = cast(ManifestVersion, "1.0")
REQUIRED_ADDITIONAL_COUNT_NAMES: Final[frozenset[str]] = frozenset(
    {
        ADDITIONAL_COUNT_CODED_ITEMS,
        ADDITIONAL_COUNT_MULTI_PARENT_TARGETS,
        ADDITIONAL_COUNT_UNRESOLVED_RELATIONSHIPS,
    }
)
REQUIRED_DELIVERY_REPORT_COUNT_NAMES: Final[frozenset[str]] = frozenset(
    {
        DELIVERY_REPORT_COUNT_FRAMEWORK_NODES,
        DELIVERY_REPORT_COUNT_ITEM_NODES,
        DELIVERY_REPORT_COUNT_RELATIONSHIPS,
        DELIVERY_REPORT_COUNT_UNRESOLVED_RELATIONSHIPS,
    }
)
SOURCE_SCHEMA_VERSION: Final[SchemaVersion] = cast(SchemaVersion, "1.0")
SUPPORTED_PACKAGE_REVISION: Final[int] = 1

FindingCode = Annotated[
    str,
    StringConstraints(max_length=120, min_length=1, pattern=r"^[a-z][a-z0-9_]*$"),
]
NonNegativeStrictInt = Annotated[StrictInt, Field(ge=0)]


class ArtifactIntegrityObservation(FrozenSchema):
    """Record the exact load-time state observed for one declared artifact."""

    finding_code: FindingCode | None = None
    finding_signature: str | None = Field(default=None, min_length=1)
    logical_name: ArtifactName
    package_path: ArtifactPath
    sha256: Sha256Digest | None = None
    size_bytes: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_observation(self) -> Self:
        """Require successful observations to carry checksum and size together.

        Returns
        -------
        Self
            Consistent artifact-integrity observation.

        Raises
        ------
        ValueError
            If success or failure fields are internally inconsistent.
        """

        has_failure = (
            self.finding_code is not None and self.finding_signature is not None
        )
        has_verified_values = self.sha256 is not None and self.size_bytes is not None

        if not has_failure and not has_verified_values:
            raise ValueError(
                "Artifact observations require either failure or verified values."
            )

        if has_failure and has_verified_values:
            raise ValueError(
                "Failed artifact observations may not declare verified values."
            )

        if (self.finding_code is None) != (self.finding_signature is None):
            raise ValueError(
                "Artifact failure code and signature must be declared together."
            )

        return self


class DeclaredArtifactReference(FrozenSchema):
    """Associate one declared artifact with its safe resolved package location."""

    logical_name: ArtifactName
    package_path: ArtifactPath
    resolved_path: Path = Field(exclude=True, repr=False)
    sha256: Sha256Digest
    size_bytes: int = Field(ge=0)


class DetailedValidationReport(FrozenSchema):
    """Represent the supported detailed ``as_validation_report.json`` contract."""

    errors: tuple[object, ...]
    learning_commons_export_schema_version: object | None = None
    object_counts: dict[StrictStr, NonNegativeStrictInt]
    passed: StrictBool
    validation_checks: tuple[StrictStr, ...]

    model_config = ConfigDict(extra="allow", frozen=True)

    @model_validator(mode="before")
    @classmethod
    def require_top_level_object(cls, value: object) -> object:
        """Require the detailed report to decode to one top-level JSON object.

        Parameters
        ----------
        value
            Decoded JSON value.

        Returns
        -------
        object
            The unchanged report mapping.

        Raises
        ------
        ValueError
            If the report does not decode to an object.
        """

        if not isinstance(value, Mapping):
            raise ValueError("The detailed validation report must be a JSON object.")

        return value

    @field_validator("errors", mode="before")
    @classmethod
    def require_errors_list(cls, value: object) -> object:
        """Require the upstream ``errors`` member to be a JSON array.

        Parameters
        ----------
        value
            Decoded upstream member value.

        Returns
        -------
        object
            The unchanged list for normal Pydantic tuple conversion.

        Raises
        ------
        ValueError
            If the member is not a list.
        """

        if not isinstance(value, list):
            raise ValueError("errors must be a list.")

        return value

    @field_validator("object_counts", mode="before")
    @classmethod
    def require_object_counts_object(cls, value: object) -> object:
        """Require ``object_counts`` to be a JSON object.

        Parameters
        ----------
        value
            Decoded upstream member value.

        Returns
        -------
        object
            The unchanged mapping for normal field validation.

        Raises
        ------
        ValueError
            If the member is not a dictionary.
        """

        if not isinstance(value, dict):
            raise ValueError("object_counts must be an object.")

        return value

    @field_validator("validation_checks", mode="before")
    @classmethod
    def require_validation_checks_list(cls, value: object) -> object:
        """Require ``validation_checks`` to be a JSON array.

        Parameters
        ----------
        value
            Decoded upstream member value.

        Returns
        -------
        object
            The unchanged list for normal Pydantic tuple conversion.

        Raises
        ------
        ValueError
            If the member is not a list.
        """

        if not isinstance(value, list):
            raise ValueError("validation_checks must be a list.")

        return value

    @model_validator(mode="after")
    def validate_report(self) -> Self:
        """Validate the supported report acceptance contract.

        Returns
        -------
        Self
            The fully validated detailed report.

        Raises
        ------
        ValueError
            If the report did not pass, contains errors, omits required counts, or has
            blank or duplicate validation-check names.
        """

        if self.passed is not True:
            raise ValueError("passed must be the exact boolean true.")

        if self.errors:
            raise ValueError("errors must be empty for an accepted validation report.")

        if not self.validation_checks:
            raise ValueError("validation_checks must contain at least one check.")

        if any(not value.strip() for value in self.validation_checks):
            raise ValueError("validation_checks values must be non-blank strings.")

        if len(self.validation_checks) != len(set(self.validation_checks)):
            raise ValueError("validation_checks values must be unique.")

        missing_counts = REQUIRED_DELIVERY_REPORT_COUNT_NAMES - set(self.object_counts)

        if missing_counts:
            formatted_counts = ", ".join(sorted(missing_counts))
            raise ValueError(
                f"object_counts is missing required graph counts: {formatted_counts}."
            )

        return self


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
    learning_component_dedup_groups: ArtifactPath | None = None
    learning_component_provenance: ArtifactPath | None = None
    learning_component_summary: ArtifactPath | None = None
    learning_components_bundle: ArtifactPath | None = None
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
            "learningComponentDedupGroups",
            "learningComponentProvenance",
            "learningComponentSummary",
            "learningComponentsBundle",
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
            "learningComponentDedupGroups": self.learning_component_dedup_groups,
            "learningComponentProvenance": self.learning_component_provenance,
            "learningComponentSummary": self.learning_component_summary,
            "learningComponentsBundle": self.learning_components_bundle,
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
    """Record declared graph counts and exact version-1 additional counts."""

    additional_counts: dict[str, NonNegativeStrictInt]
    framework_nodes: int = Field(default=1, ge=1, le=1)
    item_nodes: int = Field(ge=0)
    learning_component_nodes: int = Field(ge=0)
    relationships: int = Field(ge=0)
    supports_relationships: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_additional_counts(self) -> Self:
        """Validate exact version-1 additional count names and values.

        Returns
        -------
        Self
            Validated package counts.

        Raises
        ------
        ValueError
            If count names differ from the supported version-1 contract or a value is
            negative.
        """

        actual_names = set(self.additional_counts)

        if actual_names != REQUIRED_ADDITIONAL_COUNT_NAMES:
            missing_names = sorted(REQUIRED_ADDITIONAL_COUNT_NAMES - actual_names)
            unexpected_names = sorted(actual_names - REQUIRED_ADDITIONAL_COUNT_NAMES)
            raise ValueError(
                f"additional_counts must contain exactly the supported keys; "
                f"missing={missing_names}, unexpected={unexpected_names}."
            )

        return self


class PackageIntegritySnapshot(FrozenSchema):
    """Capture the exact package and profile state accepted during one load."""

    artifact_observations: tuple[ArtifactIntegrityObservation, ...]
    manifest_bytes: bytes = Field(exclude=True, repr=False)
    package_directories: tuple[str, ...]
    package_files: tuple[str, ...]
    package_tree_signature: tuple[str, ...]
    profile_finding_signature: tuple[str, ...] = ()
    profile_sha256: Sha256Digest | None = None


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


class PackageValidationFinding(FrozenSchema):
    """Describe one stable package-validation error or warning."""

    artifact_name: ArtifactName | None = None
    code: FindingCode
    details: dict[str, object] = Field(default_factory=dict, exclude=True, repr=False)
    message: str = Field(min_length=1)
    record_id: str | None = None
    severity: Literal["error", "warning"] = "error"
    source_export_order: int | None = Field(default=None, ge=1)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        """Require safe finding text without surrounding whitespace.

        Parameters
        ----------
        value
            Public finding message.

        Returns
        -------
        str
            The unchanged public message.

        Raises
        ------
        ValueError
            If the message contains surrounding whitespace.
        """

        if value != value.strip():
            raise ValueError("Finding messages may not contain surrounding whitespace.")

        return value


class PackageValidationResult(FrozenSchema):
    """Return one package validation outcome and any controlled status transition."""

    effective_status: ValidationStatus | None = None
    findings: tuple[PackageValidationFinding, ...]
    framework_id: FrameworkId | None = None
    graph_package_id: GraphPackageId | None = None
    is_valid: bool
    observed_status: ValidationStatus | None = None
    package_reference: str = Field(min_length=1)
    persisted: bool = False
    profile_id: ProfileId | None = None
    profile_version: ProfileVersion | None = None
    read_only: bool
    snapshot_id: SnapshotId | None = None
    target_status: ValidationStatus
    terminal_revalidation: bool = False
    validated_at: datetime | None = None

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        """Validate consistency among findings, status, and persistence metadata.

        Returns
        -------
        Self
            The consistent validation result.

        Raises
        ------
        ValueError
            If validity conflicts with findings or persistence metadata is invalid.
        """

        _require_valid_target_status(self)
        _require_persistence_consistency(self)
        _require_terminal_consistency(self)

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
    manifest_version: ManifestVersion = MANIFEST_VERSION
    package_revision: int = Field(default=SUPPORTED_PACKAGE_REVISION, ge=1)
    profile: ProfileReference
    rights: RightsPolicy
    snapshot_id: SnapshotId
    snapshot_relations: tuple[SnapshotRelation, ...] = ()
    source_schema_version: SchemaVersion
    validation: PackageValidation

    @field_validator("delivery_schema_version")
    @classmethod
    def validate_delivery_schema_version(cls, value: SchemaVersion) -> SchemaVersion:
        """Require the exact repository-supported delivery schema version.

        Parameters
        ----------
        value
            Declared delivery schema version.

        Returns
        -------
        SchemaVersion
            The unchanged supported schema version.

        Raises
        ------
        ValueError
            If the manifest declares an unsupported delivery schema version.
        """

        if value != DELIVERY_SCHEMA_VERSION:
            raise ValueError(
                f"delivery_schema_version must equal {DELIVERY_SCHEMA_VERSION}."
            )

        return value

    @field_validator("manifest_version")
    @classmethod
    def validate_manifest_version(cls, value: ManifestVersion) -> ManifestVersion:
        """Require the exact repository-supported manifest version.

        Parameters
        ----------
        value
            Declared manifest version.

        Returns
        -------
        ManifestVersion
            The unchanged supported manifest version.

        Raises
        ------
        ValueError
            If the manifest declares an unsupported manifest version.
        """

        if value != MANIFEST_VERSION:
            raise ValueError(f"manifest_version must equal {MANIFEST_VERSION}.")

        return value

    @field_validator("source_schema_version")
    @classmethod
    def validate_source_schema_version(cls, value: SchemaVersion) -> SchemaVersion:
        """Require the exact repository-supported source schema version.

        Parameters
        ----------
        value
            Declared detailed-source schema version.

        Returns
        -------
        SchemaVersion
            The unchanged supported schema version.

        Raises
        ------
        ValueError
            If the manifest declares an unsupported source schema version.
        """

        if value != SOURCE_SCHEMA_VERSION:
            raise ValueError(
                f"source_schema_version must equal {SOURCE_SCHEMA_VERSION}."
            )

        return value

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


class LoadedGraphPackage(FrozenSchema):
    """Hold one safely loaded immutable graph-package aggregate for validation."""

    artifacts: tuple[DeclaredArtifactReference, ...]
    framework_root: FrameworkNode
    item_nodes: tuple[StandardNode, ...]
    learning_component_nodes: tuple[LearningComponentNode, ...]
    manifest: GraphPackageManifest
    manifest_bytes: bytes = Field(exclude=True, repr=False)
    manifest_path: Path = Field(exclude=True, repr=False)
    package_root: Path = Field(exclude=True, repr=False)
    profile: CurriculumProfile
    profile_bytes: bytes = Field(exclude=True, repr=False)
    profile_path: Path = Field(exclude=True, repr=False)
    profile_sha256: Sha256Digest
    relationships: tuple[GraphRelationship, ...]
    validation_report: DetailedValidationReport | None = None

    def artifact(self, logical_name: str) -> DeclaredArtifactReference | None:
        """Return a declared artifact reference by logical manifest name.

        Parameters
        ----------
        logical_name
            Public artifact name used by the manifest.

        Returns
        -------
        DeclaredArtifactReference | None
            Matching safe artifact reference, or ``None`` when undeclared.
        """

        for artifact in self.artifacts:
            if str(artifact.logical_name) == logical_name:
                return artifact

        return None


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


def _require_persistence_consistency(result: PackageValidationResult) -> None:
    """Require persistence metadata to agree with the observed transition.

    A persisted result must originate from pending status, reach its target status,
    avoid persisting alongside a terminal revalidation, and record a validation
    timestamp. A non-persisted result must retain its observed effective status. A
    read-only result may never be persisted.

    Parameters
    ----------
    result
        Validation result whose persistence metadata is checked.

    Raises
    ------
    ValueError
        If persistence metadata is internally inconsistent.
    """

    if result.persisted and result.read_only:
        raise ValueError("A read-only validation result may not be persisted.")

    if not result.persisted:
        if result.effective_status is not result.observed_status:
            raise ValueError(
                "A non-persisted result must retain its observed effective status."
            )
        return

    if result.observed_status is not ValidationStatus.PENDING:
        raise ValueError(
            "A persisted validation result must originate from pending status."
        )

    if result.effective_status is not result.target_status:
        raise ValueError("A persisted validation result must reach its target status.")

    if result.terminal_revalidation:
        raise ValueError(
            "A terminal revalidation result may not persist another transition."
        )

    if result.validated_at is None:
        raise ValueError("Persisted validation results require validated_at.")


def _require_terminal_consistency(result: PackageValidationResult) -> None:
    """Require terminal-status flags and the timestamp to agree.

    The terminal-revalidation flag must reflect whether the observed status is
    terminal, and such revalidation must be read-only. A terminal effective status
    requires a timestamp, while a pending or unavailable effective status must not
    declare one.

    Parameters
    ----------
    result
        Validation result whose terminal-status flags are checked.

    Raises
    ------
    ValueError
        If terminal-status flags or the timestamp are inconsistent.
    """

    terminal_statuses = {
        ValidationStatus.FAILED,
        ValidationStatus.PASSED,
        ValidationStatus.QUARANTINED,
    }

    if result.terminal_revalidation != (result.observed_status in terminal_statuses):
        raise ValueError(
            "terminal_revalidation must reflect an observed terminal status."
        )

    if result.terminal_revalidation and not result.read_only:
        raise ValueError("Terminal revalidation must be read-only.")

    if result.effective_status in terminal_statuses and result.validated_at is None:
        raise ValueError("Effective terminal statuses require validated_at.")

    if (
        result.effective_status in {None, ValidationStatus.PENDING}
        and result.validated_at is not None
    ):
        raise ValueError(
            "Pending or unavailable effective status may not declare validated_at."
        )


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


def _require_valid_target_status(result: PackageValidationResult) -> None:
    """Require the target status to agree with result validity and findings.

    A result is valid exactly when it has no error findings. The target status must be
    terminal, must be passed for a valid result, and must be failed or quarantined for
    an invalid result.

    Parameters
    ----------
    result
        Validation result whose validity and target status are checked.

    Raises
    ------
    ValueError
        If validity conflicts with findings or the target status.
    """

    has_errors = any(finding.severity == "error" for finding in result.findings)

    if result.is_valid == has_errors:
        raise ValueError("is_valid must be true exactly when no error findings exist.")

    if result.target_status is ValidationStatus.PENDING:
        raise ValueError("target_status must be terminal.")

    if result.is_valid and result.target_status is not ValidationStatus.PASSED:
        raise ValueError("A valid result must target passed status.")

    if not result.is_valid and result.target_status not in {
        ValidationStatus.FAILED,
        ValidationStatus.QUARANTINED,
    }:
        raise ValueError("An invalid result must target failed or quarantined status.")
