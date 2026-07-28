"""This module derives curriculum-agnostic structural statistics for one framework
package.

This module provides ``FrameworkStatisticsService``, which reads one accepted package
through the existing catalog, graph, traversal, and facet-evidence boundaries. It
calculates deterministic counts for nodes, relationships, codes, source and normalized
facets, hierarchy depths, parent counts, multi-parent targets, and unresolved
relationship statuses.

Source-authored values and normalized values are counted separately. Structural depth
means graph distance from the framework root and is not treated as educational level,
difficulty, progression, or instructional sequence.

The service does not modify graph data, select a preferred parent, infer mastery,
equivalence, prerequisites, or curriculum progression, or use source export order as an
instructional ordering signal.
"""

# Standard Library
from collections import Counter
from dataclasses import dataclass

# Package Library
from kgfegmcp.catalog.service import CatalogService
from kgfegmcp.errors import CatalogError, PackageValidationError
from kgfegmcp.graph.traversal import GraphTraversal
from kgfegmcp.search.service import SearchService
from kgfegmcp.services.models import (
    CodePresenceStatistics,
    DepthCount,
    FrameworkStatistics,
    GetFrameworkStatisticsRequest,
    GetFrameworkStatisticsResult,
    MultiParentStatistics,
    NullableValueCount,
    ParentCountBucket,
    UnresolvedRelationshipStatistics,
)


def _nullable_value_order_key(value: str | None) -> tuple[int, str]:
    """Return a deterministic ordering key for optional exact values.

    Parameters
    ----------
    value
        Exact source or normalized value, or ``None`` when absent.

    Returns
    -------
    tuple[int, str]
        Non-null values first in lexical order, followed by the absent bucket.
    """

    return (1, "") if value is None else (0, value)


def _to_nullable_counts(counter: Counter[str | None]) -> tuple[NullableValueCount, ...]:
    """Convert one optional-value counter to deterministic immutable result models.

    Parameters
    ----------
    counter
        Exact source or normalized value counts.

    Returns
    -------
    tuple[NullableValueCount, ...]
        Counts ordered lexically with the absent bucket last.
    """

    return tuple(
        NullableValueCount(count=counter[value], value=value)
        for value in sorted(counter, key=_nullable_value_order_key)
    )


@dataclass(frozen=True, slots=True)
class FrameworkStatisticsService:
    """Derive deterministic structural counts from one accepted package runtime."""

    catalog_service: CatalogService
    search_service: SearchService

    def get_framework_statistics(  # pylint: disable=R0915
        self, request: GetFrameworkStatisticsRequest
    ) -> GetFrameworkStatisticsResult:
        """Return structural and facet counts for one selected framework package.

        Parameters
        ----------
        request
            Exact framework family, optional snapshot, and graph type selection.

        Returns
        -------
        GetFrameworkStatisticsResult
            Exact source metadata, package identity, and deterministic counts.

        Raises
        ------
        CatalogError
            If accepted catalog counts disagree with retained runtime records.
        PackageValidationError
            If the accepted hierarchy cannot be traversed completely from its root.
        """

        snapshot = self.catalog_service.get_framework(
            framework_id=request.framework_id, snapshot_id=request.snapshot_id
        )
        package = self.catalog_service.get_graph_package(
            framework_id=request.framework_id,
            graph_type=request.graph_type,
            snapshot_id=snapshot.snapshot_id,
        )
        loaded_package = self.catalog_service.get_loaded_package(
            framework_id=request.framework_id,
            graph_type=request.graph_type,
            snapshot_id=snapshot.snapshot_id,
        )
        store = self.catalog_service.get_graph_store(
            framework_id=request.framework_id,
            graph_type=request.graph_type,
            snapshot_id=snapshot.snapshot_id,
        )
        total_framework_nodes = package.counts.framework_nodes
        total_item_nodes = len(loaded_package.item_nodes)
        total_nodes = total_framework_nodes + total_item_nodes
        total_relationships = len(loaded_package.relationships)

        if (
            package.counts.item_nodes != total_item_nodes
            or package.counts.relationships != total_relationships
            or len(store.nodes_by_id) != total_nodes
            or len(store.relationships_by_id) != total_relationships
        ):
            raise CatalogError(
                details={
                    "graph_package_id": str(package.package_identity.graph_package_id)
                },
                message=(
                    "Accepted catalog counts disagree with the retained package runtime."
                ),
            )

        statement_type_counts: Counter[str | None] = Counter()
        normalized_statement_type_counts: Counter[str | None] = Counter()
        node_grade_level_counts: Counter[str | None] = Counter()
        local_grade_label_counts: Counter[str | None] = Counter()
        normalized_grade_counts: Counter[str | None] = Counter()
        coded_item_count = 0

        for node in loaded_package.item_nodes:
            statement_type_counts[node.statement_type] += 1
            normalized_statement_type_counts[
                (
                    node.normalized_statement_type.value
                    if node.normalized_statement_type is not None
                    else None
                )
            ] += 1

            if node.statement_code is not None:
                coded_item_count += 1

            if node.grade_level:
                node_grade_level_counts.update(node.grade_level)
            else:
                node_grade_level_counts[None] += 1

            facets = self.search_service.get_node_facet_evidence(
                graph_package_id=package.package_identity.graph_package_id,
                node_id=node.node_id,
            )

            if facets.resolved_local_grade_labels:
                local_grade_label_counts.update(facets.resolved_local_grade_labels)
            else:
                local_grade_label_counts[None] += 1

            if facets.normalized_grades:
                normalized_grade_counts.update(facets.normalized_grades)
            else:
                normalized_grade_counts[None] += 1

        canonical_relationship_label_counts: Counter[str | None] = Counter()
        source_relationship_type_counts: Counter[str | None] = Counter()
        resolution_status_counts: Counter[str | None] = Counter()

        for relationship in loaded_package.relationships:
            canonical_relationship_label_counts[relationship.label] += 1
            source_relationship_type_counts[relationship.relationship_type] += 1
            resolution_status_counts[relationship.resolution_status] += 1

        relationship_type = store.hierarchy_relationship_type
        parent_count_counts: Counter[int] = Counter()

        for node in loaded_package.item_nodes:
            parent_count = len(
                store.incoming_by_type_and_node.get(
                    (relationship_type, node.node_id), ()
                )
            )
            parent_count_counts[parent_count] += 1

        multi_parent_target_count = sum(
            node_count
            for parent_count, node_count in parent_count_counts.items()
            if parent_count > 1
        )
        maximum_parent_count = max(parent_count_counts, default=0)
        traversal = GraphTraversal(store=store).descendants(
            max_depth=max(total_nodes - 1, 0),
            max_nodes=max(total_nodes, 1),
            node_id=store.framework_root_id,
            relationship_type=relationship_type,
        )

        if not traversal.is_complete:
            raise PackageValidationError(
                details={
                    "graph_package_id": str(package.package_identity.graph_package_id),
                    "truncation_reason": (
                        traversal.truncation_reason.value
                        if traversal.truncation_reason is not None
                        else None
                    ),
                },
                message=(
                    "The accepted package hierarchy could not be traversed completely."
                ),
            )

        depth_counts: Counter[int] = Counter(
            traversal_node.depth for traversal_node in traversal.nodes
        )
        maximum_structural_depth = max(depth_counts, default=0)
        unreachable_node_count = total_nodes - len(traversal.nodes)
        unresolved_count = sum(
            count
            for status, count in resolution_status_counts.items()
            if status is not None
        )
        resolved_count = resolution_status_counts.get(None, 0)
        statistics = FrameworkStatistics(
            canonical_relationship_label_counts=_to_nullable_counts(
                canonical_relationship_label_counts
            ),
            code_presence=CodePresenceStatistics(
                coded_item_count=coded_item_count,
                uncoded_item_count=total_item_nodes - coded_item_count,
            ),
            local_grade_label_counts=_to_nullable_counts(local_grade_label_counts),
            maximum_structural_depth=maximum_structural_depth,
            minimum_structural_depth_counts=tuple(
                DepthCount(depth=depth, node_count=depth_counts[depth])
                for depth in sorted(depth_counts)
            ),
            multi_parent=MultiParentStatistics(
                maximum_parent_count=maximum_parent_count,
                parent_count_distribution=tuple(
                    ParentCountBucket(
                        node_count=parent_count_counts[parent_count],
                        parent_count=parent_count,
                    )
                    for parent_count in sorted(parent_count_counts)
                ),
                target_count=multi_parent_target_count,
            ),
            node_grade_level_counts=_to_nullable_counts(node_grade_level_counts),
            normalized_grade_counts=_to_nullable_counts(normalized_grade_counts),
            normalized_statement_type_counts=_to_nullable_counts(
                normalized_statement_type_counts
            ),
            source_relationship_type_counts=_to_nullable_counts(
                source_relationship_type_counts
            ),
            statement_type_counts=_to_nullable_counts(statement_type_counts),
            total_framework_nodes=total_framework_nodes,
            total_item_nodes=total_item_nodes,
            total_nodes=total_nodes,
            total_relationships=total_relationships,
            unreachable_node_count=unreachable_node_count,
            unresolved_relationships=UnresolvedRelationshipStatistics(
                resolved_count=resolved_count,
                status_counts=_to_nullable_counts(resolution_status_counts),
                unresolved_count=unresolved_count,
            ),
        )
        return GetFrameworkStatisticsResult(
            package=package,
            source_metadata=snapshot.source_metadata,
            statistics=statistics,
        )
