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
from collections import Counter, defaultdict, deque
from dataclasses import dataclass

# Package Library
from kgfegmcp.catalog.service import CatalogService
from kgfegmcp.domain.identifiers import NodeId
from kgfegmcp.errors import CatalogError, PackageValidationError
from kgfegmcp.graph.traversal import GraphTraversal
from kgfegmcp.packages.models import LoadedGraphPackage
from kgfegmcp.packages.wire import DELIVERY_SCHEMA_1_1_SUPPORTS_RELATIONSHIP_TYPE
from kgfegmcp.search.normalizers import normalize_facet_value
from kgfegmcp.search.service import SearchService
from kgfegmcp.services.models import (
    CodePresenceStatistics,
    DepthCount,
    FrameworkStatistics,
    GetFrameworkStatisticsRequest,
    GetFrameworkStatisticsResult,
    IntegerValueCount,
    LearningComponentStatistics,
    MultiParentStatistics,
    NullableValueCount,
    ParentCountBucket,
    UnresolvedRelationshipStatistics,
)


def _connected_node_count(
    *, loaded_package: LoadedGraphPackage, root_node_id: NodeId
) -> int:
    """Count nodes connected to the framework root by any declared relationship.

    Relationships are followed in both directions, so a learning component reached
    through one standard also reaches every other standard it supports.

    Parameters
    ----------
    loaded_package
        Accepted package aggregate retaining decoded nodes and relationships.
    root_node_id
        Outer identifier of the single framework root.

    Returns
    -------
    int
        Number of distinct nodes connected to the framework root.
    """

    neighbors: dict[NodeId, list[NodeId]] = defaultdict(list)

    for relationship in loaded_package.relationships:
        neighbors[relationship.source_node_id].append(relationship.target_node_id)
        neighbors[relationship.target_node_id].append(relationship.source_node_id)

    connected: set[NodeId] = {root_node_id}
    pending: deque[NodeId] = deque([root_node_id])

    while pending:
        for neighbor_id in neighbors[pending.popleft()]:
            if neighbor_id in connected:
                continue

            connected.add(neighbor_id)
            pending.append(neighbor_id)

    return len(connected)


def _hierarchy_relationship_counts(
    loaded_package: LoadedGraphPackage,
) -> tuple[Counter[str | None], Counter[str | None], Counter[str | None]]:
    """Count labels, source types, and resolution statuses of hierarchy relationships.

    Parameters
    ----------
    loaded_package
        Accepted package aggregate retaining decoded nodes and relationships.

    Returns
    -------
    tuple[Counter[str | None], Counter[str | None], Counter[str | None]]
        Canonical label counts, source relationship-type counts, and resolution-status
        counts over the standards hierarchy only; ``supports`` edges are excluded and
        reported in the learning-component block instead.
    """

    canonical_label_counts: Counter[str | None] = Counter()
    source_type_counts: Counter[str | None] = Counter()
    resolution_status_counts: Counter[str | None] = Counter()

    for relationship in loaded_package.relationships:
        if relationship.label == DELIVERY_SCHEMA_1_1_SUPPORTS_RELATIONSHIP_TYPE:
            continue

        canonical_label_counts[relationship.label] += 1
        source_type_counts[relationship.relationship_type] += 1
        resolution_status_counts[relationship.resolution_status] += 1

    return canonical_label_counts, source_type_counts, resolution_status_counts


def _learning_component_statistics(
    *, loaded_package: LoadedGraphPackage
) -> LearningComponentStatistics:
    """Derive deterministic learning-component counts from one accepted package.

    Parameters
    ----------
    loaded_package
        Accepted package aggregate retaining decoded learning components.

    Returns
    -------
    LearningComponentStatistics
        Deterministic counts describing the package's generated components.
    """

    components = loaded_package.learning_component_nodes
    supports = tuple(
        relationship
        for relationship in loaded_package.relationships
        if relationship.label == DELIVERY_SCHEMA_1_1_SUPPORTS_RELATIONSHIP_TYPE
    )
    components_per_standard: Counter[NodeId] = Counter(
        relationship.target_node_id for relationship in supports
    )
    standards_per_component: Counter[NodeId] = Counter(
        relationship.source_node_id for relationship in supports
    )
    confidences = tuple(
        relationship.support_confidence
        for relationship in supports
        if relationship.support_confidence is not None
    )
    # Coverage is measured over the statement types the pipeline actually decomposed,
    # so grouping headings and untargeted node types never count as gaps.
    item_nodes_by_id = {node.node_id: node for node in loaded_package.item_nodes}
    supported_statement_types = tuple(
        sorted(
            {
                item_nodes_by_id[node_id].statement_type or ""
                for node_id in components_per_standard
                if node_id in item_nodes_by_id
            }
        )
    )
    per_standard_distribution: Counter[int] = Counter(
        components_per_standard[node.node_id]
        for node in loaded_package.item_nodes
        if (node.statement_type or "") in supported_statement_types
    )
    bridge_span_distribution: Counter[int] = Counter(
        span for span in standards_per_component.values() if span > 1
    )
    tag_keys = {
        normalize_facet_value(tag) for node in components for tag in node.tags or ()
    }

    return LearningComponentStatistics(
        bridge_span_counts=_to_integer_counts(bridge_span_distribution),
        components_per_standard_counts=_to_integer_counts(per_standard_distribution),
        multi_standard_component_count=sum(bridge_span_distribution.values()),
        standards_without_components=per_standard_distribution.get(0, 0),
        support_confidence_maximum=max(confidences, default=None),
        support_confidence_minimum=min(confidences, default=None),
        supported_statement_types=supported_statement_types,
        tag_vocabulary_size=len(tag_keys - {""}),
        total_learning_components=len(components),
        total_supports_relationships=len(supports),
    )


def _to_integer_counts(counter: Counter[int]) -> tuple[IntegerValueCount, ...]:
    """Return one deterministic ascending integer distribution.

    Parameters
    ----------
    counter
        Counted integer distribution values.

    Returns
    -------
    tuple[IntegerValueCount, ...]
        Distribution entries ordered by ascending value.
    """

    return tuple(
        IntegerValueCount(count=count, value=value)
        for value, count in sorted(counter.items())
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
        total_learning_component_nodes = len(loaded_package.learning_component_nodes)
        total_supports_relationships = sum(
            1
            for relationship in loaded_package.relationships
            if relationship.label == DELIVERY_SCHEMA_1_1_SUPPORTS_RELATIONSHIP_TYPE
        )
        total_nodes = total_framework_nodes + total_item_nodes
        total_relationships = (
            len(loaded_package.relationships) - total_supports_relationships
        )
        total_store_nodes = total_nodes + total_learning_component_nodes
        total_store_relationships = total_relationships + total_supports_relationships

        if (
            package.counts.item_nodes != total_item_nodes
            or package.counts.learning_component_nodes != total_learning_component_nodes
            or package.counts.relationships != total_store_relationships
            or len(store.nodes_by_id) != total_store_nodes
            or len(store.relationships_by_id) != total_store_relationships
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

        (
            canonical_relationship_label_counts,
            source_relationship_type_counts,
            resolution_status_counts,
        ) = _hierarchy_relationship_counts(loaded_package)

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
        unreachable_node_count = total_store_nodes - _connected_node_count(
            loaded_package=loaded_package, root_node_id=store.framework_root_id
        )
        unresolved_count = sum(
            count
            for status, count in resolution_status_counts.items()
            if status is not None
        )
        resolved_count = resolution_status_counts.get(None, 0)
        statistics = FrameworkStatistics(
            learning_components=_learning_component_statistics(
                loaded_package=loaded_package
            ),
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
