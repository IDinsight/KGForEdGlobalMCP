"""Build one immutable catalog from safely discovered, read-only validated packages.

``CatalogRepository`` is the PR 6 orchestration boundary. It delegates package
discovery to ``GraphPackageRepository`` and integrity plus semantic acceptance to the
existing ``GraphPackageValidator``. Only terminal ``passed`` packages that still pass
read-only validation become queryable catalog entries.

Each accepted package receives one independent PR 5 ``GraphStore`` after the caller's
required validation gate has been established. Pending, failed, and quarantined
packages remain excluded. Invalid unaccepted packages either fail catalog construction
or are excluded according to the configured invalid-package policy. An accepted
``passed`` package that no longer validates always fails construction.

This module does not scan arbitrary paths, reload profiles independently, recalculate
checksums, decode graph records, repeat semantic validation, persist status, merge graph
namespaces, implement search, or depend on FastMCP.
"""

# Future Library
from __future__ import annotations

# Standard Library
from collections import defaultdict
from dataclasses import dataclass

# Package Library
from kgfegmcp.catalog.models import (
    CatalogFrameworkFamily,
    CatalogFrameworkSnapshot,
    CatalogGraphPackage,
    CatalogLoadResult,
    CatalogPackageRuntime,
    CatalogProfileFacets,
    CatalogResult,
    CatalogSourceMetadata,
    catalog_framework_order_key,
    catalog_graph_package_order_key,
    catalog_runtime_order_key,
    catalog_snapshot_order_key,
)
from kgfegmcp.domain.enums import InvalidPackagePolicy, ValidationStatus
from kgfegmcp.domain.identifiers import FrameworkId, SnapshotId
from kgfegmcp.errors import CatalogError, PackageValidationError
from kgfegmcp.graph.store import GraphStore
from kgfegmcp.packages.models import LoadedGraphPackage
from kgfegmcp.packages.repository import GraphPackageRepository
from kgfegmcp.packages.validator import GraphPackageValidator, PackageValidationOutcome

_TERMINAL_REJECTED_STATUSES = frozenset(
    {ValidationStatus.FAILED, ValidationStatus.QUARANTINED}
)


@dataclass(frozen=True, slots=True)
class CatalogRepository:
    """Coordinate deterministic read-only package validation and catalog assembly."""

    invalid_package_policy: InvalidPackagePolicy
    package_repository: GraphPackageRepository
    validator: GraphPackageValidator

    def __post_init__(self) -> None:
        """Require catalog discovery and validation to share one repository boundary.

        Raises
        ------
        ValueError
            If the catalog repository and validator use different package repositories.
        """

        if self.validator.repository != self.package_repository:
            raise ValueError(
                "The catalog and package validator must share one package repository."
            )

    def _accepted_runtime(
        self, outcome: PackageValidationOutcome
    ) -> CatalogPackageRuntime | None:
        """Return a runtime only for a terminal passed package that revalidates.

        Parameters
        ----------
        outcome
            Read-only validation outcome for one discovered package candidate.

        Returns
        -------
        CatalogPackageRuntime | None
            Independent accepted package runtime, or ``None`` for an excluded package.

        Raises
        ------
        CatalogError
            If a passed package fails revalidation or policy requires invalid packages
            to abort catalog construction.
        """

        result = outcome.result
        observed_status = result.observed_status

        if observed_status is ValidationStatus.PASSED:
            if (
                not result.read_only
                or result.persisted
                or not result.terminal_revalidation
            ):
                raise CatalogError(
                    details={
                        "package_reference": result.package_reference,
                        "persisted": result.persisted,
                        "read_only": result.read_only,
                        "terminal_revalidation": result.terminal_revalidation,
                    },
                    message=(
                        "An accepted graph package did not use the required read-only "
                        "terminal revalidation flow."
                    ),
                )

            if outcome.loaded_package is not None and outcome.result.is_valid:
                if result.effective_status is not ValidationStatus.PASSED:
                    raise CatalogError(
                        details={
                            "effective_status": (
                                result.effective_status.value
                                if result.effective_status is not None
                                else None
                            ),
                            "package_reference": result.package_reference,
                        },
                        message=(
                            "An accepted graph package has an inconsistent effective "
                            "validation status."
                        ),
                    )

                return _build_runtime(outcome.loaded_package)

            raise CatalogError(
                details={
                    "finding_codes": tuple(finding.code for finding in result.findings),
                    "loaded_package_available": outcome.loaded_package is not None,
                    "package_reference": result.package_reference,
                },
                message=(
                    "An accepted graph package failed read-only catalog validation."
                ),
            )

        if observed_status in _TERMINAL_REJECTED_STATUSES:
            return None

        if observed_status is ValidationStatus.PENDING:
            if result.is_valid:
                return None

            if self.invalid_package_policy is InvalidPackagePolicy.QUARANTINE:
                return None

            raise CatalogError(
                details={
                    "finding_codes": tuple(finding.code for finding in result.findings),
                    "package_reference": result.package_reference,
                    "target_status": result.target_status.value,
                },
                message=(
                    "A pending graph package is invalid and catalog construction is "
                    "configured to fail."
                ),
            )

        if observed_status is None:
            raise CatalogError(
                details={
                    "finding_codes": tuple(finding.code for finding in result.findings),
                    "package_reference": result.package_reference,
                },
                message=(
                    "A graph package has no trustworthy validation status and cannot "
                    "be cataloged safely."
                ),
            )

        raise CatalogError(
            details={
                "observed_status": observed_status.value,
                "package_reference": result.package_reference,
            },
            message="A graph package has an unsupported catalog validation state.",
        )

    def load(self) -> CatalogLoadResult:
        """Discover, revalidate, index, and return the complete immutable catalog.

        Returns
        -------
        CatalogLoadResult
            All accepted catalog entries, independent package runtimes, and read-only
            validation evidence in deterministic repository order.

        Raises
        ------
        CatalogError
            If repository discovery fails, an accepted package is invalid, policy
            requires an invalid package to fail, no accepted packages exist, or catalog
            identities and metadata are inconsistent.
        """

        try:
            candidates = self.package_repository.discover()
        except PackageValidationError as error:
            raise CatalogError(
                details={
                    "cause_details": dict(error.details),
                    "cause_error_code": error.error_code,
                },
                message="The graph-package repository could not be cataloged safely.",
            ) from error

        package_runtimes: list[CatalogPackageRuntime] = []
        validation_results = []

        for candidate in candidates:
            try:
                outcome = self.validator.validate_candidate(
                    candidate=candidate,
                    invalid_package_policy=self.invalid_package_policy,
                    read_only=True,
                )
            except PackageValidationError as error:
                raise CatalogError(
                    details={
                        "cause_details": dict(error.details),
                        "cause_error_code": error.error_code,
                        "package_reference": candidate.reference,
                    },
                    message="A graph package could not be validated for the catalog.",
                ) from error

            validation_results.append(outcome.result)
            runtime = self._accepted_runtime(outcome)

            if runtime is not None:
                package_runtimes.append(runtime)

        if not package_runtimes:
            raise CatalogError(
                details={"discovered_package_count": len(candidates)},
                message=(
                    "No terminal passed graph packages are available for the catalog."
                ),
            )

        package_runtimes.sort(key=catalog_runtime_order_key)

        try:
            catalog = _build_catalog(tuple(package_runtimes))
            return CatalogLoadResult(
                catalog=catalog,
                discovered_package_count=len(candidates),
                excluded_package_count=len(candidates) - len(package_runtimes),
                package_runtimes=tuple(package_runtimes),
                validation_results=tuple(validation_results),
            )
        except ValueError as error:
            raise CatalogError(
                details={"reason": str(error)},
                message=(
                    "The accepted graph packages could not form a consistent catalog."
                ),
            ) from error


def _build_catalog(
    package_runtimes: tuple[CatalogPackageRuntime, ...],
) -> CatalogResult:
    """Build framework families and snapshots from accepted package runtimes.

    Parameters
    ----------
    package_runtimes
        Deterministically ordered accepted package runtimes.

    Returns
    -------
    CatalogResult
        Complete immutable catalog.

    Raises
    ------
    ValueError
        If global identities, snapshot routes, metadata, or relations conflict.
    """

    graph_package_ids: set[str] = set()
    route_keys: set[tuple[str, str]] = set()
    snapshot_framework_ids: dict[str, FrameworkId] = {}
    runtimes_by_snapshot: defaultdict[
        tuple[FrameworkId, SnapshotId], list[CatalogPackageRuntime]
    ] = defaultdict(list)

    for runtime in package_runtimes:
        identity = runtime.catalog_package.package_identity
        graph_package_id = str(identity.graph_package_id)
        snapshot_id = str(identity.snapshot_id)
        route_key = snapshot_id, identity.graph_type.value

        if graph_package_id in graph_package_ids:
            raise ValueError(f"Duplicate graph package identifier: {graph_package_id}.")

        if route_key in route_keys:
            raise ValueError(
                "A snapshot has more than one package for the same graph type."
            )

        known_framework_id = snapshot_framework_ids.get(snapshot_id)

        if (
            known_framework_id is not None
            and known_framework_id != identity.framework_id
        ):
            raise ValueError(
                "One snapshot identifier is assigned to multiple framework families."
            )

        graph_package_ids.add(graph_package_id)
        route_keys.add(route_key)
        snapshot_framework_ids[snapshot_id] = identity.framework_id
        runtimes_by_snapshot[(identity.framework_id, identity.snapshot_id)].append(
            runtime
        )

    snapshots_by_framework: defaultdict[FrameworkId, list[CatalogFrameworkSnapshot]] = (
        defaultdict(list)
    )

    snapshot_keys = list(runtimes_by_snapshot)
    snapshot_keys.sort(key=lambda value: (str(value[0]), str(value[1])))

    for snapshot_key in snapshot_keys:
        snapshot_runtimes = runtimes_by_snapshot[snapshot_key]
        snapshot_runtimes.sort(
            key=lambda runtime: catalog_graph_package_order_key(runtime.catalog_package)
        )
        snapshot = _build_snapshot(tuple(snapshot_runtimes))
        snapshots_by_framework[snapshot.framework_id].append(snapshot)

    framework_families: list[CatalogFrameworkFamily] = []

    framework_ids = list(snapshots_by_framework)
    framework_ids.sort(key=str)

    for framework_id in framework_ids:
        snapshots = snapshots_by_framework[framework_id]
        snapshots.sort(key=catalog_snapshot_order_key)
        framework_families.append(
            CatalogFrameworkFamily(
                framework_id=framework_id, snapshots=tuple(snapshots)
            )
        )

    framework_families.sort(key=catalog_framework_order_key)
    snapshot_count = sum(len(framework.snapshots) for framework in framework_families)

    return CatalogResult(
        framework_count=len(framework_families),
        frameworks=tuple(framework_families),
        graph_package_count=len(package_runtimes),
        snapshot_count=snapshot_count,
    )


def _build_runtime(loaded_package: LoadedGraphPackage) -> CatalogPackageRuntime:
    """Build one accepted catalog runtime after the required validation gate.

    Parameters
    ----------
    loaded_package
        Exact loaded package from a valid terminal passed validation outcome.

    Returns
    -------
    CatalogPackageRuntime
        Catalog entry, independent graph store, and retained loaded package.

    Raises
    ------
    CatalogError
        If graph-store or catalog-entry construction encounters an invariant failure.
    """

    try:
        graph_store = GraphStore.from_validated_package(loaded_package)
        manifest = loaded_package.manifest
        framework = manifest.framework
        catalog_package = CatalogGraphPackage(
            capabilities=manifest.capabilities,
            counts=manifest.counts,
            created_at=manifest.created_at,
            delivery_schema_version=manifest.delivery_schema_version,
            included_graph_types=manifest.included_graph_types,
            manifest_version=manifest.manifest_version,
            package_identity=graph_store.package_identity,
            profile_facets=CatalogProfileFacets.from_framework_metadata(framework),
            rights=manifest.rights,
            source_schema_version=manifest.source_schema_version,
            validation=manifest.validation,
        )
        return CatalogPackageRuntime(
            catalog_package=catalog_package,
            graph_store=graph_store,
            loaded_package=loaded_package,
        )
    except (PackageValidationError, ValueError) as error:
        identity = loaded_package.manifest.graph_package_id
        raise CatalogError(
            details={"graph_package_id": str(identity), "reason": str(error)},
            message=("A validated graph package could not be indexed for the catalog."),
        ) from error


def _build_snapshot(
    package_runtimes: tuple[CatalogPackageRuntime, ...],
) -> CatalogFrameworkSnapshot:
    """Build one snapshot from all accepted packages sharing its exact identity.

    Parameters
    ----------
    package_runtimes
        Non-empty deterministic runtimes for one framework and snapshot pair.

    Returns
    -------
    CatalogFrameworkSnapshot
        Immutable snapshot with source metadata and routed graph packages.

    Raises
    ------
    ValueError
        If runtimes disagree on identity, source metadata, or snapshot relations.
    """

    if not package_runtimes:
        raise ValueError("A catalog snapshot requires at least one graph package.")

    first_runtime = package_runtimes[0]
    first_manifest = first_runtime.loaded_package.manifest
    framework_id = first_manifest.framework_id
    snapshot_id = first_manifest.snapshot_id
    source_metadata = CatalogSourceMetadata.from_framework_metadata(
        first_manifest.framework
    )
    snapshot_relations = first_manifest.snapshot_relations
    graph_packages: list[CatalogGraphPackage] = []

    for runtime in package_runtimes:
        manifest = runtime.loaded_package.manifest

        if manifest.framework_id != framework_id or manifest.snapshot_id != snapshot_id:
            raise ValueError(
                "Snapshot package runtimes do not share one exact snapshot identity."
            )

        if (
            CatalogSourceMetadata.from_framework_metadata(manifest.framework)
            != source_metadata
        ):
            raise ValueError(
                "Graph packages for one snapshot have conflicting source metadata."
            )

        if manifest.snapshot_relations != snapshot_relations:
            raise ValueError(
                "Graph packages for one snapshot have conflicting snapshot relations."
            )

        graph_packages.append(runtime.catalog_package)

    graph_packages.sort(key=catalog_graph_package_order_key)
    available_graph_types = [
        graph_package.package_identity.graph_type for graph_package in graph_packages
    ]
    available_graph_types.sort(key=lambda graph_type: graph_type.value)

    return CatalogFrameworkSnapshot(
        available_graph_types=tuple(available_graph_types),
        framework_id=framework_id,
        graph_packages=tuple(graph_packages),
        snapshot_id=snapshot_id,
        snapshot_relations=snapshot_relations,
        source_metadata=source_metadata,
    )
