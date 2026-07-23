"""This module provides deterministic in-memory catalog selection and graph-store
routing.

The catalog service is the read-only query boundary for an already constructed catalog.
It builds immutable indexes over framework families, snapshots, graph packages, loaded
packages, and graph stores so callers can resolve catalog entries without accessing the
filesystem or repeating package validation.

The service supports two snapshot-selection modes:

* an exact snapshot ID selects that snapshot only when it belongs to the requested
    framework family;
* an omitted snapshot ID selects the single snapshot explicitly marked as current for
    that framework.

The service does not guess when selection is unclear. A missing framework, snapshot, or
current snapshot produces a not-found error. More than one current snapshot produces an
ambiguity error. A valid snapshot that does not contain the requested graph type
produces a capability-unavailable error.

After selection, the service routes the caller to the catalog metadata, validated
loaded package, or independent per-package graph store associated with the selected
graph package. It never searches another package as a fallback and never creates global
node, relationship, or traversal indexes across packages.

This module performs no package discovery, file loading, validation, graph-store
construction, settings loading, logging initialization, semantic inference, lexical
search, cross-package traversal, or FastMCP application startup.
"""

# Future Library
from __future__ import annotations

# Standard Library
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

# Package Library
from kgfegmcp.catalog.models import (
    CatalogFrameworkFamily,
    CatalogFrameworkSnapshot,
    CatalogGraphPackage,
    CatalogLoadResult,
    CatalogPackageRuntime,
    CatalogResult,
)
from kgfegmcp.domain.enums import GraphType
from kgfegmcp.domain.identifiers import FrameworkId, GraphPackageId, SnapshotId
from kgfegmcp.errors import (
    AmbiguousFrameworkError,
    CapabilityUnavailableError,
    CatalogError,
    FrameworkNotFoundError,
)
from kgfegmcp.graph.store import GraphStore
from kgfegmcp.packages.models import LoadedGraphPackage

SnapshotGraphTypeKey = tuple[SnapshotId, GraphType]


@dataclass(frozen=True, slots=True)
class _CatalogIndexes:
    """Hold the mutable catalog-derived indexes produced during construction.

    Attributes
    ----------
    current_snapshots_by_framework_id
        Per-framework tuples of source-declared current snapshots.
    families_by_framework_id
        Exact framework families keyed by their framework identifier.
    graph_packages_by_id
        Catalog graph packages keyed by their exact graph-package identifier.
    graph_packages_by_snapshot_and_graph_type
        Catalog graph packages keyed by their snapshot and graph-type route.
    snapshots_by_framework_id
        Per-framework tuples of every accepted snapshot.
    snapshots_by_id
        Exact snapshots keyed by their immutable snapshot identifier.
    """

    current_snapshots_by_framework_id: dict[
        FrameworkId, tuple[CatalogFrameworkSnapshot, ...]
    ]
    families_by_framework_id: dict[FrameworkId, CatalogFrameworkFamily]
    graph_packages_by_id: dict[GraphPackageId, CatalogGraphPackage]
    graph_packages_by_snapshot_and_graph_type: dict[
        SnapshotGraphTypeKey, CatalogGraphPackage
    ]
    snapshots_by_framework_id: dict[FrameworkId, tuple[CatalogFrameworkSnapshot, ...]]
    snapshots_by_id: dict[SnapshotId, CatalogFrameworkSnapshot]


@dataclass(frozen=True, slots=True)
class _RuntimeIndexes:
    """Hold the mutable runtime-derived indexes produced during construction.

    Attributes
    ----------
    runtimes_by_graph_package_id
        Package runtimes keyed by their exact graph-package identifier.
    runtimes_by_snapshot_and_graph_type
        Package runtimes keyed by their snapshot and graph-type route.
    """

    runtimes_by_graph_package_id: dict[GraphPackageId, CatalogPackageRuntime]
    runtimes_by_snapshot_and_graph_type: dict[
        SnapshotGraphTypeKey, CatalogPackageRuntime
    ]


@dataclass(frozen=True, slots=True)
class CatalogService:
    """Route exact framework and graph-package selections through immutable indexes."""

    load_result: CatalogLoadResult

    _current_snapshots_by_framework_id: Mapping[
        FrameworkId, tuple[CatalogFrameworkSnapshot, ...]
    ] = field(repr=False)
    _families_by_framework_id: Mapping[FrameworkId, CatalogFrameworkFamily] = field(
        repr=False
    )
    _graph_packages_by_id: Mapping[GraphPackageId, CatalogGraphPackage] = field(
        repr=False
    )
    _graph_packages_by_snapshot_and_graph_type: Mapping[
        SnapshotGraphTypeKey, CatalogGraphPackage
    ] = field(repr=False)
    _runtimes_by_snapshot_and_graph_type: Mapping[
        SnapshotGraphTypeKey, CatalogPackageRuntime
    ] = field(repr=False)
    _snapshots_by_framework_id: Mapping[
        FrameworkId, tuple[CatalogFrameworkSnapshot, ...]
    ] = field(repr=False)
    _snapshots_by_id: Mapping[SnapshotId, CatalogFrameworkSnapshot] = field(repr=False)
    _runtimes_by_graph_package_id: Mapping[GraphPackageId, CatalogPackageRuntime] = (
        field(repr=False)
    )

    @classmethod
    def from_load_result(cls, load_result: CatalogLoadResult) -> CatalogService:
        """Build immutable selection and runtime indexes from one complete load.

        Parameters
        ----------
        load_result
            All-or-nothing catalog load returned by ``CatalogRepository``.

        Returns
        -------
        CatalogService
            Pure in-memory catalog selection and graph-store routing service.

        Raises
        ------
        CatalogError
            If any catalog or runtime identity would overwrite another index entry.
        """

        catalog_indexes = _build_catalog_indexes(load_result=load_result)
        runtime_indexes = _build_runtime_indexes(
            graph_packages_by_id=catalog_indexes.graph_packages_by_id,
            load_result=load_result,
        )
        _verify_graph_package_correspondence(
            graph_packages_by_id=catalog_indexes.graph_packages_by_id,
            runtimes_by_graph_package_id=(runtime_indexes.runtimes_by_graph_package_id),
        )

        return cls(
            _current_snapshots_by_framework_id=MappingProxyType(
                catalog_indexes.current_snapshots_by_framework_id
            ),
            _families_by_framework_id=MappingProxyType(
                catalog_indexes.families_by_framework_id
            ),
            _graph_packages_by_id=MappingProxyType(
                catalog_indexes.graph_packages_by_id
            ),
            _graph_packages_by_snapshot_and_graph_type=MappingProxyType(
                catalog_indexes.graph_packages_by_snapshot_and_graph_type
            ),
            _runtimes_by_graph_package_id=MappingProxyType(
                runtime_indexes.runtimes_by_graph_package_id
            ),
            _runtimes_by_snapshot_and_graph_type=MappingProxyType(
                runtime_indexes.runtimes_by_snapshot_and_graph_type
            ),
            _snapshots_by_framework_id=MappingProxyType(
                catalog_indexes.snapshots_by_framework_id
            ),
            _snapshots_by_id=MappingProxyType(catalog_indexes.snapshots_by_id),
            load_result=load_result,
        )

    @property
    def catalog(self) -> CatalogResult:
        """Return the complete immutable public catalog result.

        Returns
        -------
        CatalogResult
            Deterministically ordered framework families and snapshots.
        """

        return self.load_result.catalog

    def _select_runtime(
        self,
        *,
        framework_id: FrameworkId,
        graph_type: GraphType,
        snapshot_id: SnapshotId | None,
    ) -> CatalogPackageRuntime:
        """Select one exact package runtime after deterministic snapshot selection.

        Parameters
        ----------
        framework_id
            Exact conceptual framework identifier.
        graph_type
            Exact primary graph type required by the caller.
        snapshot_id
            Exact immutable snapshot or ``None`` for unique-current selection.

        Returns
        -------
        CatalogPackageRuntime
            Independent loaded package and graph store for the selected route.

        Raises
        ------
        AmbiguousFrameworkError
            If omitted snapshot selection finds several current snapshots.
        CapabilityUnavailableError
            If the selected snapshot has no package for the requested graph type.
        FrameworkNotFoundError
            If the framework or selected snapshot is unavailable.
        """

        snapshot = self._select_snapshot(
            framework_id=framework_id, snapshot_id=snapshot_id
        )
        route_key = snapshot.snapshot_id, graph_type
        runtime = self._runtimes_by_snapshot_and_graph_type.get(route_key)

        if runtime is None:
            raise CapabilityUnavailableError(
                details={
                    "available_graph_types": tuple(
                        value.value for value in snapshot.available_graph_types
                    ),
                    "framework_id": str(framework_id),
                    "graph_type": graph_type.value,
                    "snapshot_id": str(snapshot.snapshot_id),
                },
                message=(
                    "The selected framework snapshot does not provide the requested "
                    "graph type."
                ),
            )

        return runtime

    def _select_snapshot(
        self, *, framework_id: FrameworkId, snapshot_id: SnapshotId | None
    ) -> CatalogFrameworkSnapshot:
        """Select an exact snapshot or the one unique current snapshot for a family.

        Parameters
        ----------
        framework_id
            Exact conceptual framework identifier.
        snapshot_id
            Exact immutable snapshot identifier or ``None`` for current selection.

        Returns
        -------
        CatalogFrameworkSnapshot
            Selected exact immutable snapshot.

        Raises
        ------
        AmbiguousFrameworkError
            If more than one current snapshot exists for the framework.
        FrameworkNotFoundError
            If the framework, exact snapshot, or unique current snapshot is unavailable.
        """

        family = self._families_by_framework_id.get(framework_id)

        if family is None:
            raise FrameworkNotFoundError(
                details={"framework_id": str(framework_id)},
                message=(
                    "No catalog framework matched the requested framework identifier."
                ),
            )

        if snapshot_id is not None:
            snapshot = self._snapshots_by_id.get(snapshot_id)

            if snapshot is None or snapshot.framework_id != framework_id:
                raise FrameworkNotFoundError(
                    details={
                        "framework_id": str(framework_id),
                        "snapshot_id": str(snapshot_id),
                    },
                    message="The requested framework snapshot is unavailable.",
                )

            return snapshot

        current_snapshots = self._current_snapshots_by_framework_id.get(framework_id)

        if current_snapshots is None or not current_snapshots:
            raise FrameworkNotFoundError(
                details={
                    "available_snapshot_ids": tuple(
                        str(snapshot.snapshot_id) for snapshot in family.snapshots
                    ),
                    "framework_id": str(framework_id),
                },
                message=(
                    "The framework has no current snapshot; specify an exact snapshot "
                    "identifier."
                ),
            )

        if len(current_snapshots) > 1:
            raise AmbiguousFrameworkError(
                details={
                    "candidate_snapshot_ids": tuple(
                        str(snapshot.snapshot_id) for snapshot in current_snapshots
                    ),
                    "framework_id": str(framework_id),
                },
                message=(
                    "The framework has multiple current snapshots; specify an exact "
                    "snapshot identifier."
                ),
            )

        return current_snapshots[0]

    def get_framework(
        self, *, framework_id: FrameworkId, snapshot_id: SnapshotId | None = None
    ) -> CatalogFrameworkSnapshot:
        """Return one exact snapshot or the framework's unique current snapshot.

        Parameters
        ----------
        framework_id
            Exact conceptual framework identifier.
        snapshot_id
            Optional exact immutable snapshot identifier.

        Returns
        -------
        CatalogFrameworkSnapshot
            Selected source metadata, graph availability, and package entries.

        Raises
        ------
        AmbiguousFrameworkError
            If omitted snapshot selection finds several current snapshots.
        FrameworkNotFoundError
            If the framework or selected snapshot is unavailable.
        """

        return self._select_snapshot(framework_id=framework_id, snapshot_id=snapshot_id)

    def get_graph_package(
        self,
        *,
        framework_id: FrameworkId,
        graph_type: GraphType,
        snapshot_id: SnapshotId | None = None,
    ) -> CatalogGraphPackage:
        """Return metadata for one routed graph package.

        Parameters
        ----------
        framework_id
            Exact conceptual framework identifier.
        graph_type
            Exact primary graph type required by the caller.
        snapshot_id
            Optional exact immutable snapshot identifier.

        Returns
        -------
        CatalogGraphPackage
            Queryable package metadata and exact package identity.

        Raises
        ------
        AmbiguousFrameworkError
            If omitted snapshot selection finds several current snapshots.
        CapabilityUnavailableError
            If the selected snapshot lacks the requested graph type.
        FrameworkNotFoundError
            If the framework or selected snapshot is unavailable.
        """

        runtime = self._select_runtime(
            framework_id=framework_id, graph_type=graph_type, snapshot_id=snapshot_id
        )
        return runtime.catalog_package

    def get_graph_store(
        self,
        *,
        framework_id: FrameworkId,
        graph_type: GraphType,
        snapshot_id: SnapshotId | None = None,
    ) -> GraphStore:
        """Return the independent graph store for one routed graph package.

        Parameters
        ----------
        framework_id
            Exact conceptual framework identifier.
        graph_type
            Exact primary graph type required by the caller.
        snapshot_id
            Optional exact immutable snapshot identifier.

        Returns
        -------
        GraphStore
            Existing per-package PR 5 store; no graph namespace is merged.

        Raises
        ------
        AmbiguousFrameworkError
            If omitted snapshot selection finds several current snapshots.
        CapabilityUnavailableError
            If the selected snapshot lacks the requested graph type.
        FrameworkNotFoundError
            If the framework or selected snapshot is unavailable.
        """

        runtime = self._select_runtime(
            framework_id=framework_id, graph_type=graph_type, snapshot_id=snapshot_id
        )
        return runtime.graph_store

    def get_loaded_package(
        self,
        *,
        framework_id: FrameworkId,
        graph_type: GraphType,
        snapshot_id: SnapshotId | None = None,
    ) -> LoadedGraphPackage:
        """Return the retained validated loaded package for one routed graph package.

        Parameters
        ----------
        framework_id
            Exact conceptual framework identifier.
        graph_type
            Exact primary graph type required by the caller.
        snapshot_id
            Optional exact immutable snapshot identifier.

        Returns
        -------
        LoadedGraphPackage
            Exact already-loaded immutable aggregate used to build the graph store.

        Raises
        ------
        AmbiguousFrameworkError
            If omitted snapshot selection finds several current snapshots.
        CapabilityUnavailableError
            If the selected snapshot lacks the requested graph type.
        FrameworkNotFoundError
            If the framework or selected snapshot is unavailable.
        """

        runtime = self._select_runtime(
            framework_id=framework_id, graph_type=graph_type, snapshot_id=snapshot_id
        )
        return runtime.loaded_package

    def list_frameworks(self) -> CatalogResult:
        """Return the complete deterministic catalog without filtering or pagination.

        Returns
        -------
        CatalogResult
            Every accepted framework family, snapshot, and graph package.
        """

        return self.catalog


def _build_catalog_indexes(load_result: CatalogLoadResult) -> _CatalogIndexes:
    """Build every catalog-derived index from one complete load.

    Parameters
    ----------
    load_result
        All-or-nothing catalog load returned by ``CatalogRepository``.

    Returns
    -------
    _CatalogIndexes
        Framework, snapshot, graph-package, and route indexes.

    Raises
    ------
    CatalogError
        If any framework, snapshot, package, or route identity is duplicated.
    """

    indexes = _CatalogIndexes(
        current_snapshots_by_framework_id={},
        families_by_framework_id={},
        graph_packages_by_id={},
        graph_packages_by_snapshot_and_graph_type={},
        snapshots_by_framework_id={},
        snapshots_by_id={},
    )

    for family in load_result.catalog.frameworks:
        if family.framework_id in indexes.families_by_framework_id:
            _raise_index_conflict(
                identifier=str(family.framework_id), index_name="framework"
            )

        indexes.families_by_framework_id[family.framework_id] = family
        indexes.snapshots_by_framework_id[family.framework_id] = family.snapshots
        indexes.current_snapshots_by_framework_id[family.framework_id] = tuple(
            snapshot
            for snapshot in family.snapshots
            if snapshot.source_metadata.is_current
        )

        for snapshot in family.snapshots:
            if snapshot.snapshot_id in indexes.snapshots_by_id:
                _raise_index_conflict(
                    identifier=str(snapshot.snapshot_id), index_name="snapshot"
                )

            indexes.snapshots_by_id[snapshot.snapshot_id] = snapshot
            _index_snapshot(
                graph_packages_by_id=indexes.graph_packages_by_id,
                graph_packages_by_snapshot_and_graph_type=(
                    indexes.graph_packages_by_snapshot_and_graph_type
                ),
                snapshot=snapshot,
            )

    return indexes


def _build_runtime_indexes(
    *,
    graph_packages_by_id: dict[GraphPackageId, CatalogGraphPackage],
    load_result: CatalogLoadResult,
) -> _RuntimeIndexes:
    """Build every runtime-derived index from one complete load.

    Parameters
    ----------
    graph_packages_by_id
        Catalog graph packages used to confirm each runtime corresponds.
    load_result
        All-or-nothing catalog load returned by ``CatalogRepository``.

    Returns
    -------
    _RuntimeIndexes
        Runtime indexes keyed by graph-package identity and snapshot route.

    Raises
    ------
    CatalogError
        If a runtime identity or route is duplicated, or a runtime has no corresponding
        catalog graph package.
    """

    indexes = _RuntimeIndexes(
        runtimes_by_graph_package_id={}, runtimes_by_snapshot_and_graph_type={}
    )

    for runtime in load_result.package_runtimes:
        identity = runtime.catalog_package.package_identity
        route_key = identity.snapshot_id, identity.graph_type

        if identity.graph_package_id in indexes.runtimes_by_graph_package_id:
            _raise_index_conflict(
                identifier=str(identity.graph_package_id),
                index_name="graph-package runtime",
            )

        if route_key in indexes.runtimes_by_snapshot_and_graph_type:
            _raise_index_conflict(
                identifier=f"{identity.snapshot_id}/{identity.graph_type.value}",
                index_name="runtime graph-type route",
            )

        if identity.graph_package_id not in graph_packages_by_id:
            raise CatalogError(
                details={"graph_package_id": str(identity.graph_package_id)},
                message=(
                    "A package runtime has no corresponding catalog graph package."
                ),
            )

        indexes.runtimes_by_graph_package_id[identity.graph_package_id] = runtime
        indexes.runtimes_by_snapshot_and_graph_type[route_key] = runtime

    return indexes


def _index_snapshot(
    *,
    graph_packages_by_id: dict[GraphPackageId, CatalogGraphPackage],
    graph_packages_by_snapshot_and_graph_type: dict[
        SnapshotGraphTypeKey, CatalogGraphPackage
    ],
    snapshot: CatalogFrameworkSnapshot,
) -> None:
    """Index one snapshot's graph packages by identity and snapshot route.

    Parameters
    ----------
    graph_packages_by_id
        Accumulating package index mutated with each accepted package.
    graph_packages_by_snapshot_and_graph_type
        Accumulating route index mutated with each accepted package.
    snapshot
        Exact immutable snapshot whose graph packages are indexed.

    Raises
    ------
    CatalogError
        If a graph-package identity or snapshot route would be overwritten.
    """

    for graph_package in snapshot.graph_packages:
        identity = graph_package.package_identity
        route_key = snapshot.snapshot_id, identity.graph_type

        if identity.graph_package_id in graph_packages_by_id:
            _raise_index_conflict(
                identifier=str(identity.graph_package_id), index_name="graph package"
            )

        if route_key in graph_packages_by_snapshot_and_graph_type:
            _raise_index_conflict(
                identifier=(f"{snapshot.snapshot_id}/{identity.graph_type.value}"),
                index_name="snapshot graph-type route",
            )

        graph_packages_by_id[identity.graph_package_id] = graph_package
        graph_packages_by_snapshot_and_graph_type[route_key] = graph_package


def _raise_index_conflict(*, identifier: str, index_name: str) -> None:
    """Raise one stable catalog error for an attempted duplicate index key.

    Parameters
    ----------
    identifier
        Exact conflicting identifier or route representation.
    index_name
        Logical index whose key would be overwritten.

    Raises
    ------
    CatalogError
        Always raised with private deterministic conflict details.
    """

    raise CatalogError(
        details={"identifier": identifier, "index_name": index_name},
        message="Catalog construction encountered a duplicate identity or route.",
    )


def _verify_graph_package_correspondence(
    *,
    graph_packages_by_id: dict[GraphPackageId, CatalogGraphPackage],
    runtimes_by_graph_package_id: dict[GraphPackageId, CatalogPackageRuntime],
) -> None:
    """Confirm catalog graph packages and runtime graph stores correspond exactly.

    Parameters
    ----------
    graph_packages_by_id
        Catalog graph packages keyed by their exact graph-package identifier.
    runtimes_by_graph_package_id
        Package runtimes keyed by their exact graph-package identifier.

    Raises
    ------
    CatalogError
        If the two graph-package identifier sets are not identical.
    """

    if set(runtimes_by_graph_package_id) != set(graph_packages_by_id):
        raise CatalogError(
            details={
                "catalog_graph_package_ids": tuple(
                    sorted(str(value) for value in graph_packages_by_id)
                ),
                "runtime_graph_package_ids": tuple(
                    sorted(str(value) for value in runtimes_by_graph_package_id)
                ),
            },
            message=(
                "Catalog graph packages and runtime graph stores do not correspond."
            ),
        )
