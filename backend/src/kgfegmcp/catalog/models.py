"""This module defines immutable metadata and runtime contracts for the package catalog.

This module describes the read-only structures used to represent validated graph
packages in the catalog. The models organize catalog information into four levels:

* a graph package represents one independently queryable package;
* a framework snapshot groups packages belonging to the same exact snapshot;
* a framework family groups snapshots sharing the same exact framework ID;
* a catalog result contains all accepted framework families and packages.

Source-authored metadata is kept separate from normalized profile-derived facets so
callers can distinguish original curriculum terminology from catalog-facing normalized
values.

Runtime contracts associate each catalog package with the exact validated loaded
package and graph store from which it was created. These associations allow later
services to route queries without reloading files, repeating validation, or rebuilding
graph indexes.

The models enforce catalog-wide invariants, including deterministic ordering, identity
consistency, count consistency, package-to-runtime correspondence, and the
all-or-nothing treatment of terminal ``passed`` packages. An observed terminal
``passed`` package cannot be silently treated as excluded when its validation evidence
is incomplete or invalid.

This module performs no filesystem access, package discovery, validation, configuration
loading, logging initialization, graph traversal, or application startup. It defines
contracts only.
"""

# Standard Library
from dataclasses import dataclass
from datetime import date, datetime
from typing import Self

# Third Party Library
from pydantic import Field, model_validator

# Package Library
from kgfegmcp.domain.enums import GraphType, SubjectMappingStatus, ValidationStatus
from kgfegmcp.domain.identifiers import (
    FrameworkId,
    LanguageTag,
    ManifestVersion,
    SchemaVersion,
    Sha256Digest,
    SnapshotId,
)
from kgfegmcp.domain.models import RightsPolicy
from kgfegmcp.graph.models import GraphPackageIdentity
from kgfegmcp.graph.store import GraphStore
from kgfegmcp.packages.models import (
    FrameworkCapabilities,
    FrameworkMetadata,
    LoadedGraphPackage,
    PackageCounts,
    PackageValidation,
    PackageValidationResult,
    SnapshotRelation,
)
from kgfegmcp.schemas import FrozenSchema


def _require_timezone_aware(*, field_name: str, value: datetime) -> None:
    """Require one datetime value to include a usable UTC offset.

    Parameters
    ----------
    field_name
        Logical field name used in the validation message.
    value
        Datetime value to validate.

    Raises
    ------
    ValueError
        If the datetime is naive or has no usable UTC offset.
    """

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware.")


def _require_unique(*, field_name: str, values: tuple[str, ...]) -> None:
    """Require a tuple of string representations to contain no duplicates.

    Parameters
    ----------
    field_name
        Logical collection name used in the validation message.
    values
        String values whose exact uniqueness must be preserved.

    Raises
    ------
    ValueError
        If duplicate values are present.
    """

    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must not contain duplicates.")


class CatalogSourceMetadata(FrozenSchema):
    """Describe source-facing metadata for one immutable framework snapshot."""

    adoption_status: str | None = None
    is_current: bool
    issuing_authority: str | None = None
    jurisdiction: str = Field(min_length=1)
    jurisdiction_type: str | None = None
    languages: tuple[LanguageTag, ...] = Field(min_length=1)
    local_grades_or_stages: tuple[str, ...]
    local_subject: str = Field(min_length=1)
    name: str = Field(min_length=1)
    provider: str | None = None
    source_document_sha256: Sha256Digest | None = None
    source_publication_date: date | None = None
    source_version: str | None = None

    @classmethod
    def from_framework_metadata(cls, framework: FrameworkMetadata) -> Self:
        """Copy source-facing fields from validated framework metadata.

        Parameters
        ----------
        framework
            Validated package-manifest framework metadata.

        Returns
        -------
        Self
            Source-facing catalog metadata with source tuple order preserved.
        """

        return cls(
            adoption_status=framework.adoption_status,
            is_current=framework.is_current,
            issuing_authority=framework.issuing_authority,
            jurisdiction=framework.jurisdiction,
            jurisdiction_type=framework.jurisdiction_type,
            languages=framework.languages,
            local_grades_or_stages=framework.local_grades_or_stages,
            local_subject=framework.local_subject,
            name=framework.name,
            provider=framework.provider,
            source_document_sha256=framework.source_document_sha256,
            source_publication_date=framework.source_publication_date,
            source_version=framework.source_version,
        )

    @model_validator(mode="after")
    def validate_source_metadata(self) -> Self:
        """Validate exact source-facing collection uniqueness.

        Returns
        -------
        Self
            The validated source metadata.

        Raises
        ------
        ValueError
            If languages or local grades contain duplicate exact values.
        """

        _require_unique(
            field_name="languages",
            values=tuple(str(language) for language in self.languages),
        )
        _require_unique(
            field_name="local_grades_or_stages", values=self.local_grades_or_stages
        )
        return self


class CatalogProfileFacets(FrozenSchema):
    """Describe normalized catalog facets validated against one profile version."""

    normalized_grades: tuple[str, ...]
    normalized_subjects: tuple[str, ...]
    subject_mapping_note: str | None = None
    subject_mapping_status: SubjectMappingStatus

    @classmethod
    def from_framework_metadata(cls, framework: FrameworkMetadata) -> Self:
        """Copy normalized profile facets from validated framework metadata.

        Parameters
        ----------
        framework
            Validated package-manifest framework metadata.

        Returns
        -------
        Self
            Profile-derived facets with normalized tuple order preserved.
        """

        return cls(
            normalized_grades=framework.normalized_grades,
            normalized_subjects=framework.normalized_subjects,
            subject_mapping_note=framework.subject_mapping_note,
            subject_mapping_status=framework.subject_mapping_status,
        )

    @model_validator(mode="after")
    def validate_profile_facets(self) -> Self:
        """Validate normalized facet uniqueness and mapping-state consistency.

        Returns
        -------
        Self
            The validated profile-derived facets.

        Raises
        ------
        ValueError
            If values repeat or the subject mapping state conflicts with its fields.
        """

        _require_unique(field_name="normalized_grades", values=self.normalized_grades)
        _require_unique(
            field_name="normalized_subjects", values=self.normalized_subjects
        )

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


class CatalogGraphPackage(FrozenSchema):
    """Describe one terminal passed graph package available through the catalog."""

    capabilities: FrameworkCapabilities
    counts: PackageCounts
    created_at: datetime
    delivery_schema_version: SchemaVersion
    included_graph_types: tuple[GraphType, ...] = Field(min_length=1)
    manifest_version: ManifestVersion
    package_identity: GraphPackageIdentity
    profile_facets: CatalogProfileFacets
    rights: RightsPolicy
    source_schema_version: SchemaVersion
    validation: PackageValidation

    @model_validator(mode="after")
    def validate_graph_package(self) -> Self:
        """Validate accepted status, package graph types, and creation time.

        Returns
        -------
        Self
            The validated queryable graph-package entry.

        Raises
        ------
        ValueError
            If the package is not passed, graph types conflict, or time is naive.
        """

        _require_timezone_aware(field_name="created_at", value=self.created_at)
        _require_unique(
            field_name="included_graph_types",
            values=tuple(graph_type.value for graph_type in self.included_graph_types),
        )

        if self.package_identity.graph_type not in self.included_graph_types:
            raise ValueError(
                "included_graph_types must contain the package's primary graph type."
            )

        if self.validation.status is not ValidationStatus.PASSED:
            raise ValueError("Catalog graph packages must have terminal passed status.")

        return self


class CatalogFrameworkSnapshot(FrozenSchema):
    """Describe one exact immutable source snapshot and its queryable graph packages."""

    available_graph_types: tuple[GraphType, ...] = Field(min_length=1)
    framework_id: FrameworkId
    graph_packages: tuple[CatalogGraphPackage, ...] = Field(min_length=1)
    snapshot_id: SnapshotId
    snapshot_relations: tuple[SnapshotRelation, ...] = ()
    source_metadata: CatalogSourceMetadata

    @model_validator(mode="after")
    def validate_snapshot(self) -> Self:
        """Validate snapshot identity, package membership, availability, and order.

        Returns
        -------
        Self
            The validated immutable framework snapshot.

        Raises
        ------
        ValueError
            If identities conflict, routes repeat, or deterministic order is absent.
        """

        if str(self.snapshot_id).partition("@")[0] != str(self.framework_id):
            raise ValueError("snapshot_id must be namespaced by framework_id.")

        graph_package_ids: list[str] = []
        graph_types: list[GraphType] = []

        for graph_package in self.graph_packages:
            identity = graph_package.package_identity

            if identity.framework_id != self.framework_id:
                raise ValueError(
                    "Every graph package must belong to the snapshot framework."
                )

            if identity.snapshot_id != self.snapshot_id:
                raise ValueError(
                    "Every graph package must belong to the exact catalog snapshot."
                )

            graph_package_ids.append(str(identity.graph_package_id))
            graph_types.append(identity.graph_type)

        _require_unique(
            field_name="graph package identifiers", values=tuple(graph_package_ids)
        )
        _require_unique(
            field_name="routable graph types",
            values=tuple(graph_type.value for graph_type in graph_types),
        )

        expected_graph_types = list(graph_types)
        expected_graph_types.sort(key=lambda graph_type: graph_type.value)

        if self.available_graph_types != tuple(expected_graph_types):
            raise ValueError(
                "available_graph_types must equal the deterministic package graph types."
            )

        ordered_packages = list(self.graph_packages)
        ordered_packages.sort(key=catalog_graph_package_order_key)

        if self.graph_packages != tuple(ordered_packages):
            raise ValueError(
                "Snapshot graph packages must use deterministic catalog order."
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
            raise ValueError("A catalog snapshot may not relate to itself.")

        return self


class CatalogFrameworkFamily(FrozenSchema):
    """Group all installed immutable snapshots of one exact framework family."""

    framework_id: FrameworkId
    snapshots: tuple[CatalogFrameworkSnapshot, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_family(self) -> Self:
        """Validate snapshot membership, uniqueness, and deterministic order.

        Returns
        -------
        Self
            The validated framework family.

        Raises
        ------
        ValueError
            If a snapshot belongs elsewhere, repeats, or is out of order.
        """

        snapshot_ids: list[str] = []

        for snapshot in self.snapshots:
            if snapshot.framework_id != self.framework_id:
                raise ValueError(
                    "Every snapshot must belong to the declared framework family."
                )

            snapshot_ids.append(str(snapshot.snapshot_id))

        _require_unique(field_name="snapshot identifiers", values=tuple(snapshot_ids))
        ordered_snapshots = list(self.snapshots)
        ordered_snapshots.sort(key=catalog_snapshot_order_key)

        if self.snapshots != tuple(ordered_snapshots):
            raise ValueError(
                "Framework snapshots must use deterministic catalog order."
            )

        return self


class CatalogResult(FrozenSchema):
    """Return the complete deterministic catalog of accepted framework packages."""

    framework_count: int = Field(ge=1)
    frameworks: tuple[CatalogFrameworkFamily, ...] = Field(min_length=1)
    graph_package_count: int = Field(ge=1)
    snapshot_count: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_catalog(self) -> Self:
        """Validate catalog counts, global identity uniqueness, and family order.

        Returns
        -------
        Self
            The validated complete catalog result.

        Raises
        ------
        ValueError
            If counts, identities, or deterministic family order disagree.
        """

        expected_framework_count = len(self.frameworks)
        expected_snapshot_count = sum(
            len(framework.snapshots) for framework in self.frameworks
        )
        expected_graph_package_count = sum(
            len(snapshot.graph_packages)
            for framework in self.frameworks
            for snapshot in framework.snapshots
        )

        if self.framework_count != expected_framework_count:
            raise ValueError("framework_count does not match catalog families.")

        if self.snapshot_count != expected_snapshot_count:
            raise ValueError("snapshot_count does not match catalog snapshots.")

        if self.graph_package_count != expected_graph_package_count:
            raise ValueError(
                "graph_package_count does not match catalog graph packages."
            )

        framework_ids = tuple(
            str(framework.framework_id) for framework in self.frameworks
        )
        snapshot_ids = tuple(
            str(snapshot.snapshot_id)
            for framework in self.frameworks
            for snapshot in framework.snapshots
        )
        graph_package_ids = tuple(
            str(graph_package.package_identity.graph_package_id)
            for framework in self.frameworks
            for snapshot in framework.snapshots
            for graph_package in snapshot.graph_packages
        )
        _require_unique(field_name="framework identifiers", values=framework_ids)
        _require_unique(field_name="snapshot identifiers", values=snapshot_ids)
        _require_unique(
            field_name="graph package identifiers", values=graph_package_ids
        )

        ordered_frameworks = list(self.frameworks)
        ordered_frameworks.sort(key=catalog_framework_order_key)

        if self.frameworks != tuple(ordered_frameworks):
            raise ValueError("Catalog families must use deterministic framework order.")

        return self


@dataclass(frozen=True, slots=True)
class _CatalogLoadCorrespondence:
    """Carry the catalog-load lookup maps shared across runtime validation phases.

    Attributes
    ----------
    accepted_results_by_id
        Accepted validation results keyed by their exact graph-package identifier.
    catalog_snapshots_by_id
        Catalog snapshots keyed by their exact snapshot identifier.
    """

    accepted_results_by_id: dict[str, PackageValidationResult]
    catalog_snapshots_by_id: dict[SnapshotId, CatalogFrameworkSnapshot]


@dataclass(frozen=True, slots=True)
class CatalogPackageRuntime:
    """Retain one catalog entry, validated loaded package, and independent store."""

    catalog_package: CatalogGraphPackage
    graph_store: GraphStore
    loaded_package: LoadedGraphPackage

    def __post_init__(self) -> None:
        """Require catalog, loaded-package, and store identities to agree exactly.

        Raises
        ------
        ValueError
            If any runtime identity, metadata, structure, or source record disagrees.
        """

        identity = self.catalog_package.package_identity
        manifest = self.loaded_package.manifest

        if self.graph_store.package_identity != identity:
            raise ValueError(
                "The graph store identity must match its catalog graph package."
            )

        if (
            manifest.framework_id != identity.framework_id
            or manifest.graph_package_id != identity.graph_package_id
            or manifest.graph_type is not identity.graph_type
            or manifest.package_revision != identity.package_revision
            or manifest.snapshot_id != identity.snapshot_id
        ):
            raise ValueError(
                "The loaded package identity must match its catalog graph package."
            )

        if (
            manifest.profile.profile_id != identity.profile_id
            or manifest.profile.profile_version != identity.profile_version
            or manifest.profile.sha256 != identity.profile_sha256
            or self.loaded_package.profile_sha256 != identity.profile_sha256
        ):
            raise ValueError(
                "The loaded profile identity must match its catalog graph package."
            )

        expected_profile_facets = CatalogProfileFacets.from_framework_metadata(
            manifest.framework
        )

        if (
            self.catalog_package.capabilities != manifest.capabilities
            or self.catalog_package.counts != manifest.counts
            or self.catalog_package.created_at != manifest.created_at
            or (
                self.catalog_package.delivery_schema_version
                != manifest.delivery_schema_version
            )
            or (
                self.catalog_package.included_graph_types
                != manifest.included_graph_types
            )
            or self.catalog_package.manifest_version != manifest.manifest_version
            or self.catalog_package.profile_facets != expected_profile_facets
            or self.catalog_package.rights != manifest.rights
            or (
                self.catalog_package.source_schema_version
                != manifest.source_schema_version
            )
            or self.catalog_package.validation != manifest.validation
        ):
            raise ValueError(
                "Catalog package metadata must exactly match its loaded manifest."
            )

        if (
            self.graph_store.framework_root_id
            != self.loaded_package.framework_root.node_id
            or (
                self.graph_store.hierarchy_relationship_type
                != self.loaded_package.profile.hierarchy.relationship_type
            )
            or (
                self.graph_store.items_in_deterministic_source_order
                != self.loaded_package.item_nodes
            )
            or len(self.graph_store.nodes_by_id)
            != len(self.loaded_package.item_nodes) + 1
            or len(self.graph_store.relationships_by_id)
            != len(self.loaded_package.relationships)
        ):
            raise ValueError(
                "The graph store structure must match its loaded graph package."
            )

        if (
            self.graph_store.nodes_by_id.get(self.loaded_package.framework_root.node_id)
            is not self.loaded_package.framework_root
            or any(
                self.graph_store.nodes_by_id.get(node.node_id) is not node
                for node in self.loaded_package.item_nodes
            )
            or any(
                self.graph_store.relationships_by_id.get(relationship.relationship_id)
                is not relationship
                for relationship in self.loaded_package.relationships
            )
        ):
            raise ValueError(
                "The graph store must retain the exact loaded source record instances."
            )


@dataclass(frozen=True, slots=True)
class CatalogLoadResult:
    """Return one all-or-nothing catalog load and its read-only validation evidence."""

    catalog: CatalogResult
    discovered_package_count: int
    excluded_package_count: int
    package_runtimes: tuple[CatalogPackageRuntime, ...]
    validation_results: tuple[PackageValidationResult, ...]

    def __post_init__(self) -> None:
        """Validate catalog-load counts, acceptance evidence, and runtime order.

        Raises
        ------
        ValueError
            If discovery counts, validation outcomes, or accepted runtimes disagree.
        """

        _validate_catalog_load_counts(self)
        _validate_catalog_load_evidence(self)
        correspondence = _validate_catalog_load_correspondence(self)
        _validate_catalog_load_runtime_evidence(
            correspondence=correspondence, load_result=self
        )
        _validate_catalog_load_runtime_order(self)


def _is_accepted_catalog_result(result: PackageValidationResult) -> bool:
    """Return whether validation evidence proves catalog package acceptance.

    Parameters
    ----------
    result
        Read-only package validation result to evaluate.

    Returns
    -------
    bool
        ``True`` only for a valid terminal passed revalidation with exact package
        identity and no persistence.
    """

    return (
        result.effective_status is ValidationStatus.PASSED
        and result.graph_package_id is not None
        and result.is_valid
        and result.observed_status is ValidationStatus.PASSED
        and not result.persisted
        and result.read_only
        and result.terminal_revalidation
    )


def _validate_catalog_load_correspondence(
    load_result: CatalogLoadResult,
) -> _CatalogLoadCorrespondence:
    """Validate catalog-load identifier correspondence and return shared lookup maps.

    Parameters
    ----------
    load_result
        Catalog-load result whose runtime, catalog, and accepted identifiers are
        validated for exact correspondence.

    Returns
    -------
    _CatalogLoadCorrespondence
        Lookup maps reused by later per-runtime validation phases.

    Raises
    ------
    ValueError
        If runtime or accepted identifiers repeat, the runtime identifiers do not
        correspond exactly to the catalog packages or the accepted validation results,
        or the runtime metadata does not equal the public catalog packages.
    """

    catalog_packages_by_id = {
        str(graph_package.package_identity.graph_package_id): graph_package
        for framework in load_result.catalog.frameworks
        for snapshot in framework.snapshots
        for graph_package in snapshot.graph_packages
    }
    catalog_snapshots_by_id = {
        snapshot.snapshot_id: snapshot
        for framework in load_result.catalog.frameworks
        for snapshot in framework.snapshots
    }
    runtime_packages_by_id = {
        str(runtime.catalog_package.package_identity.graph_package_id): (
            runtime.catalog_package
        )
        for runtime in load_result.package_runtimes
    }
    accepted_results = tuple(
        result
        for result in load_result.validation_results
        if _is_accepted_catalog_result(result)
    )
    accepted_results_by_id = {
        str(result.graph_package_id): result for result in accepted_results
    }
    runtime_ids = tuple(runtime_packages_by_id)
    catalog_ids = tuple(catalog_packages_by_id)
    accepted_result_ids = tuple(
        str(result.graph_package_id) for result in accepted_results
    )

    _require_unique(field_name="runtime graph package identifiers", values=runtime_ids)
    _require_unique(
        field_name="accepted validation graph package identifiers",
        values=accepted_result_ids,
    )

    if set(runtime_ids) != set(catalog_ids):
        raise ValueError(
            "Catalog runtimes must correspond exactly to catalog graph packages."
        )

    if set(runtime_ids) != set(accepted_result_ids):
        raise ValueError(
            "Catalog runtimes must correspond exactly to accepted validation results."
        )

    if runtime_packages_by_id != catalog_packages_by_id:
        raise ValueError(
            "Catalog runtime metadata must equal the public catalog packages."
        )

    return _CatalogLoadCorrespondence(
        accepted_results_by_id=accepted_results_by_id,
        catalog_snapshots_by_id=catalog_snapshots_by_id,
    )


def _validate_catalog_load_counts(load_result: CatalogLoadResult) -> None:
    """Validate that catalog-load discovery counts agree with validation evidence.

    Parameters
    ----------
    load_result
        Catalog-load result whose discovery counts are validated.

    Raises
    ------
    ValueError
        If either package count is negative or the discovered count does not equal the
        validation-result count.
    """

    if load_result.discovered_package_count < 0:
        raise ValueError("discovered_package_count must be non-negative.")

    if load_result.excluded_package_count < 0:
        raise ValueError("excluded_package_count must be non-negative.")

    if load_result.discovered_package_count != len(load_result.validation_results):
        raise ValueError(
            "discovered_package_count must equal the validation-result count."
        )


def _validate_catalog_load_evidence(load_result: CatalogLoadResult) -> None:
    """Validate catalog-load validation-result invariants, order, and derived counts.

    Parameters
    ----------
    load_result
        Catalog-load result whose validation evidence and counts are validated.

    Raises
    ------
    ValueError
        If validation evidence is not read-only and non-persisting, an observed passed
        package lacks complete acceptance evidence, references repeat or are out of
        deterministic order, the excluded count is inconsistent, or runtime and catalog
        package counts differ.
    """

    if any(
        not result.read_only or result.persisted
        for result in load_result.validation_results
    ):
        raise ValueError(
            "Catalog validation results must be read-only and non-persisting."
        )

    if any(
        result.observed_status is ValidationStatus.PASSED
        and not _is_accepted_catalog_result(result)
        for result in load_result.validation_results
    ):
        raise ValueError(
            "Observed passed packages must have complete accepted validation evidence."
        )

    package_references = tuple(
        result.package_reference for result in load_result.validation_results
    )
    _require_unique(
        field_name="validation package references", values=package_references
    )

    if package_references != tuple(sorted(package_references)):
        raise ValueError(
            "Catalog validation results must use deterministic repository order."
        )

    expected_excluded_count = load_result.discovered_package_count - len(
        load_result.package_runtimes
    )

    if load_result.excluded_package_count != expected_excluded_count:
        raise ValueError(
            "excluded_package_count does not match discovered and accepted packages."
        )

    if len(load_result.package_runtimes) != load_result.catalog.graph_package_count:
        raise ValueError(
            "Catalog runtime count must equal the catalog graph-package count."
        )


def _validate_catalog_load_runtime_evidence(
    *, correspondence: _CatalogLoadCorrespondence, load_result: CatalogLoadResult
) -> None:
    """Validate that every package runtime matches its evidence and snapshot metadata.

    Parameters
    ----------
    correspondence
        Shared lookup maps produced during identifier-correspondence validation.
    load_result
        Catalog-load result whose package runtimes are validated against their accepted
        validation evidence and catalog snapshot metadata.

    Raises
    ------
    ValueError
        If a runtime's accepted validation evidence or its catalog snapshot metadata
        does not match the runtime.
    """

    for runtime in load_result.package_runtimes:
        identity = runtime.catalog_package.package_identity
        graph_package_id = str(identity.graph_package_id)
        manifest = runtime.loaded_package.manifest
        result = correspondence.accepted_results_by_id[graph_package_id]
        snapshot = correspondence.catalog_snapshots_by_id[identity.snapshot_id]
        expected_source_metadata = CatalogSourceMetadata.from_framework_metadata(
            manifest.framework
        )

        if (
            result.framework_id != identity.framework_id
            or result.graph_package_id != identity.graph_package_id
            or result.profile_id != identity.profile_id
            or result.profile_version != identity.profile_version
            or result.snapshot_id != identity.snapshot_id
            or (result.validated_at != runtime.catalog_package.validation.validated_at)
        ):
            raise ValueError(
                "Accepted validation evidence must match its package runtime."
            )

        if (
            snapshot.framework_id != identity.framework_id
            or snapshot.source_metadata != expected_source_metadata
            or snapshot.snapshot_relations != manifest.snapshot_relations
        ):
            raise ValueError(
                "Catalog snapshot metadata must match every package runtime."
            )


def _validate_catalog_load_runtime_order(load_result: CatalogLoadResult) -> None:
    """Validate that catalog-load package runtimes use deterministic package order.

    Parameters
    ----------
    load_result
        Catalog-load result whose package-runtime order is validated.

    Raises
    ------
    ValueError
        If the package runtimes are not in deterministic package order.
    """

    ordered_runtimes = list(load_result.package_runtimes)
    ordered_runtimes.sort(key=catalog_runtime_order_key)

    if load_result.package_runtimes != tuple(ordered_runtimes):
        raise ValueError("Catalog runtimes must use deterministic package order.")


def catalog_framework_order_key(framework: CatalogFrameworkFamily) -> tuple[str]:
    """Return the deterministic order key for one framework family.

    Parameters
    ----------
    framework
        Catalog framework family to order.

    Returns
    -------
    tuple[str]
        Exact framework identifier.
    """

    return (str(framework.framework_id),)


def catalog_graph_package_order_key(
    graph_package: CatalogGraphPackage,
) -> tuple[str, int, str]:
    """Return the deterministic order key for one catalog graph package.

    Parameters
    ----------
    graph_package
        Queryable graph package to order.

    Returns
    -------
    tuple[str, int, str]
        Graph type, package revision, and exact graph-package identifier.
    """

    identity = graph_package.package_identity
    return (
        identity.graph_type.value,
        identity.package_revision,
        str(identity.graph_package_id),
    )


def catalog_runtime_order_key(
    runtime: CatalogPackageRuntime,
) -> tuple[str, str, str, int, str]:
    """Return the deterministic order key for one accepted package runtime.

    Parameters
    ----------
    runtime
        Accepted package runtime to order.

    Returns
    -------
    tuple[str, str, str, int, str]
        Framework, snapshot, graph type, revision, and graph-package identifiers.
    """

    identity = runtime.catalog_package.package_identity
    return (
        str(identity.framework_id),
        str(identity.snapshot_id),
        identity.graph_type.value,
        identity.package_revision,
        str(identity.graph_package_id),
    )


def catalog_snapshot_order_key(snapshot: CatalogFrameworkSnapshot) -> tuple[str]:
    """Return the deterministic order key for one immutable framework snapshot.

    Parameters
    ----------
    snapshot
        Catalog snapshot to order.

    Returns
    -------
    tuple[str]
        Exact snapshot identifier.
    """

    return (str(snapshot.snapshot_id),)
