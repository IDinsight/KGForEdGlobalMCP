"""This module provides deterministic bounded traversal over one immutable graph store.

Traversal operates only on indexes already built from a successfully validated loaded
package. Ancestor and descendant results include the origin at depth zero, preserve
minimum edge depth, include every selected-type relationship induced by the bounded
returned node set, and expose deterministic size truncation. Root-path traversal
returns only complete framework-root-to-origin paths and preserves every valid DAG
branch without selecting a preferred parent.

The implementation uses explicit cycle guards as a defensive invariant check. It does
not revalidate package acceptance, infer instructional sequence, repair graph records,
load artifacts, perform search, or cross package boundaries.
"""

# Future Library
from __future__ import annotations

# Standard Library
from dataclasses import dataclass

# Package Library
from kgfegmcp.domain.identifiers import NodeId, RelationshipId
from kgfegmcp.errors import PackageValidationError
from kgfegmcp.graph.models import (
    GraphNodeRecord,
    GraphRelationship,
    GraphTraversalDirection,
    RootPath,
    RootPathsResult,
    TraversalNode,
    TraversalResult,
    TraversalTruncationReason,
    graph_node_order_key,
    graph_relationship_order_key,
)
from kgfegmcp.graph.store import GraphStore


def _adjacent_node_id(
    *, direction: GraphTraversalDirection, relationship: GraphRelationship
) -> NodeId:
    """Return the next node identifier for one traversal direction.

    Parameters
    ----------
    direction
        Ancestor or descendant traversal direction.
    relationship
        Exact source-to-target relationship being followed.

    Returns
    -------
    NodeId
        Source endpoint for ancestor traversal or target endpoint for descendant
        traversal.
    """

    if direction is GraphTraversalDirection.ANCESTORS:
        return relationship.source_node_id

    return relationship.target_node_id


def _raise_cycle(
    *, node_id: NodeId, relationship: GraphRelationship, relationship_type: str
) -> None:
    """Raise a stable invariant error for a cycle encountered during traversal.

    Parameters
    ----------
    node_id
        Active-path node that would be entered again.
    relationship
        Exact relationship that closes the detected cycle.
    relationship_type
        Selected canonical relationship label.

    Raises
    ------
    PackageValidationError
        Always raised because a successfully validated package must be acyclic for the
        selected hierarchy traversal.
    """

    raise PackageValidationError(
        details={
            "node_id": str(node_id),
            "relationship_id": str(relationship.relationship_id),
            "relationship_type": relationship_type,
        },
        message="The graph contains a directed cycle and cannot be traversed safely.",
    )


def _validate_node_traversal_limits(*, max_depth: int, max_nodes: int) -> None:
    """Validate ancestor and descendant traversal bounds.

    Parameters
    ----------
    max_depth
        Maximum number of selected relationships from the origin.
    max_nodes
        Maximum unique returned nodes, including the origin.

    Raises
    ------
    ValueError
        If depth is negative or the node bound cannot include the origin.
    """

    if max_depth < 0:
        raise ValueError("max_depth must be greater than or equal to zero.")

    if max_nodes < 1:
        raise ValueError("max_nodes must be greater than or equal to one.")


def _validate_root_path_limits(
    *, max_depth: int, max_path_node_occurrences: int, max_paths: int
) -> None:
    """Validate complete root-path traversal bounds.

    Parameters
    ----------
    max_depth
        Maximum relationship count in one complete returned path.
    max_path_node_occurrences
        Maximum sum of node counts across complete returned paths.
    max_paths
        Maximum number of complete returned paths.

    Raises
    ------
    ValueError
        If depth is negative or either output-size bound is less than one.
    """

    if max_depth < 0:
        raise ValueError("max_depth must be greater than or equal to zero.")

    if max_path_node_occurrences < 1:
        raise ValueError(
            "max_path_node_occurrences must be greater than or equal to one."
        )

    if max_paths < 1:
        raise ValueError("max_paths must be greater than or equal to one.")


@dataclass(frozen=True, slots=True)
class GraphTraversal:
    """Execute deterministic DAG-aware traversal against one graph store."""

    store: GraphStore

    def _bounded_ancestor_node_ids(
        self, *, max_depth: int, node_id: NodeId, relationship_type: str
    ) -> frozenset[NodeId]:
        """Collect unique nodes that can reach an origin within a depth boundary.

        Parameters
        ----------
        max_depth
            Maximum incoming relationship distance from the origin.
        node_id
            Outer identifier of the origin node.
        relationship_type
            Exact selected canonical relationship label.

        Returns
        -------
        frozenset[NodeId]
            Origin and every ancestor reachable within the requested depth.

        Raises
        ------
        PackageValidationError
            If a relationship endpoint is unavailable despite the successful
            package-validation construction precondition.
        """

        visited_node_ids: set[NodeId] = {node_id}
        frontier: tuple[NodeId, ...] = (node_id,)

        for _depth_index in range(max_depth):
            next_frontier: dict[NodeId, GraphNodeRecord] = {}

            for current_node_id in frontier:
                relationships = self._relationships_for(
                    direction=GraphTraversalDirection.ANCESTORS,
                    node_id=current_node_id,
                    relationship_type=relationship_type,
                )

                for relationship in relationships:
                    parent_node_id = relationship.source_node_id

                    if parent_node_id in visited_node_ids:
                        continue

                    parent_node = self.store._require_relationship_endpoint(
                        node_id=parent_node_id,
                        relationship_id=relationship.relationship_id,
                    )
                    next_frontier[parent_node_id] = parent_node

            if not next_frontier:
                break

            ordered_nodes_list = list(next_frontier.values())
            ordered_nodes_list.sort(key=graph_node_order_key)
            ordered_nodes = tuple(ordered_nodes_list)
            frontier = tuple(node.node_id for node in ordered_nodes)
            visited_node_ids.update(frontier)

        return frozenset(visited_node_ids)

    def _eligible_root_path_relationships(
        self,
        *,
        ancestor_node_ids: frozenset[NodeId],
        node_id: NodeId,
        relationship_type: str,
    ) -> tuple[GraphRelationship, ...]:
        """Return ordered outgoing edges that remain inside the ancestor subgraph.

        Parameters
        ----------
        ancestor_node_ids
            Nodes known to reach the requested origin within the depth boundary.
        node_id
            Current path node.
        relationship_type
            Exact selected canonical relationship label.

        Returns
        -------
        tuple[GraphRelationship, ...]
            Deterministically ordered eligible outgoing relationships.
        """

        relationships = self._relationships_for(
            direction=GraphTraversalDirection.DESCENDANTS,
            node_id=node_id,
            relationship_type=relationship_type,
        )
        return tuple(
            relationship
            for relationship in relationships
            if relationship.target_node_id in ancestor_node_ids
        )

    def _guard_relationship_subgraph_against_cycles(
        self,
        *,
        node_ids: frozenset[NodeId],
        relationship_type: str,
        relationships: tuple[GraphRelationship, ...],
    ) -> None:
        """Detect directed cycles in one bounded induced relationship subgraph.

        The guard inspects only nodes and complete relationships included by the
        current bounded operation. It is a defensive traversal invariant, not a repeat
        of package validation.

        Parameters
        ----------
        node_ids
            Unique nodes included by the bounded operation.
        relationship_type
            Exact selected canonical relationship label.
        relationships
            Selected-type relationships whose endpoints are both included nodes.

        Raises
        ------
        PackageValidationError
            If a deterministic depth-first walk encounters an active-path back edge.
        """

        outgoing_relationships: dict[NodeId, list[GraphRelationship]] = {}

        for relationship in relationships:
            source_relationships = outgoing_relationships.get(
                relationship.source_node_id
            )

            if source_relationships is None:
                source_relationships = []
                outgoing_relationships[relationship.source_node_id] = (
                    source_relationships
                )

            source_relationships.append(relationship)

        node_state: dict[NodeId, int] = {}

        ordered_node_ids = list(node_ids)
        ordered_node_ids.sort(key=str)

        for start_node_id in ordered_node_ids:
            start_state = node_state.get(start_node_id)

            if start_state is not None and start_state != 0:
                continue

            node_state[start_node_id] = 1
            stack: list[tuple[NodeId, int]] = [(start_node_id, 0)]

            while stack:
                current_node_id, next_relationship_index = stack[-1]
                current_relationships = outgoing_relationships.get(current_node_id)

                if current_relationships is None:
                    current_relationships = []

                if next_relationship_index >= len(current_relationships):
                    node_state[current_node_id] = 2
                    stack.pop()
                    continue

                relationship = current_relationships[next_relationship_index]
                stack[-1] = current_node_id, next_relationship_index + 1
                target_node_id = relationship.target_node_id
                target_state = node_state.get(target_node_id)

                if target_state is None:
                    target_state = 0

                if target_state == 1:
                    _raise_cycle(
                        node_id=target_node_id,
                        relationship=relationship,
                        relationship_type=relationship_type,
                    )

                if target_state == 2:
                    continue

                node_state[target_node_id] = 1
                stack.append((target_node_id, 0))

    def _induced_relationships(
        self,
        *,
        direction: GraphTraversalDirection,
        node_ids: frozenset[NodeId],
        relationship_type: str,
    ) -> tuple[GraphRelationship, ...]:
        """Return every selected-type relationship induced by returned nodes.

        Parameters
        ----------
        direction
            Ancestor or descendant traversal direction used to select adjacency.
        node_ids
            Complete bounded returned node set, including the origin.
        relationship_type
            Exact selected canonical relationship label.

        Returns
        -------
        tuple[GraphRelationship, ...]
            Every relevant relationship whose endpoints are both returned, ordered by
            source export order and relationship ID.
        """

        relationships_by_id: dict[RelationshipId, GraphRelationship] = {}

        for node_id in node_ids:
            relationships = self._relationships_for(
                direction=direction,
                node_id=node_id,
                relationship_type=relationship_type,
            )

            for relationship in relationships:
                if (
                    relationship.source_node_id in node_ids
                    and relationship.target_node_id in node_ids
                ):
                    relationships_by_id[relationship.relationship_id] = relationship

        ordered_relationships = list(relationships_by_id.values())
        ordered_relationships.sort(key=graph_relationship_order_key)
        return tuple(ordered_relationships)

    def _relationships_for(
        self,
        *,
        direction: GraphTraversalDirection,
        node_id: NodeId,
        relationship_type: str,
    ) -> tuple[GraphRelationship, ...]:
        """Return one immutable adjacency tuple for a traversal direction.

        Parameters
        ----------
        direction
            Ancestor traversal selects incoming edges; descendant traversal selects
            outgoing edges.
        node_id
            Current outer node identifier.
        relationship_type
            Exact selected canonical relationship label.

        Returns
        -------
        tuple[GraphRelationship, ...]
            Deterministically ordered relationships, or an empty tuple.
        """

        adjacency_key = relationship_type, node_id

        if direction is GraphTraversalDirection.ANCESTORS:
            relationships = self.store.incoming_by_type_and_node.get(adjacency_key)
        else:
            relationships = self.store.outgoing_by_type_and_node.get(adjacency_key)

        if relationships is None:
            return ()

        return relationships

    def _traverse(
        self,
        *,
        direction: GraphTraversalDirection,
        max_depth: int,
        max_nodes: int,
        node_id: NodeId,
        relationship_type: str | None,
    ) -> TraversalResult:
        """Execute one deterministic bounded ancestor or descendant traversal.

        Parameters
        ----------
        direction
            Ancestor or descendant traversal direction.
        max_depth
            Maximum relationship distance from the origin.
        max_nodes
            Maximum unique returned nodes, including the origin.
        node_id
            Outer identifier of the origin node.
        relationship_type
            Explicit canonical label or ``None`` for the profile hierarchy label.

        Returns
        -------
        TraversalResult
            Deterministic bounded node and induced-relationship result.

        Raises
        ------
        GraphNodeNotFoundError
            If the origin node is unavailable.
        PackageValidationError
            If a relationship endpoint is unavailable despite the successful
            package-validation construction precondition, or if a directed cycle is
            encountered within the requested depth boundary.
        ValueError
            If a bound is invalid or an explicit relationship type is blank.
        """

        _validate_node_traversal_limits(max_depth=max_depth, max_nodes=max_nodes)
        origin_node = self.store._require_node(node_id)
        selected_relationship_type = self.store._select_relationship_type(
            relationship_type
        )
        depth_by_node_id: dict[NodeId, int] = {origin_node.node_id: 0}
        ordered_nodes: list[GraphNodeRecord] = [origin_node]
        frontier: tuple[NodeId, ...] = (origin_node.node_id,)
        truncation_reason: TraversalTruncationReason | None = None

        for depth_index in range(max_depth):
            depth = depth_index + 1
            candidate_nodes: dict[NodeId, GraphNodeRecord] = {}

            for current_node_id in frontier:
                relationships = self._relationships_for(
                    direction=direction,
                    node_id=current_node_id,
                    relationship_type=selected_relationship_type,
                )

                for relationship in relationships:
                    adjacent_node_id = _adjacent_node_id(
                        direction=direction, relationship=relationship
                    )

                    if adjacent_node_id in depth_by_node_id:
                        continue

                    adjacent_node = self.store._require_relationship_endpoint(
                        node_id=adjacent_node_id,
                        relationship_id=relationship.relationship_id,
                    )
                    candidate_nodes[adjacent_node_id] = adjacent_node

            if not candidate_nodes:
                break

            ordered_candidate_list = list(candidate_nodes.values())
            ordered_candidate_list.sort(key=graph_node_order_key)
            ordered_candidates = tuple(ordered_candidate_list)
            remaining_capacity = max_nodes - len(ordered_nodes)

            if len(ordered_candidates) > remaining_capacity:
                included_candidates = ordered_candidates[:remaining_capacity]
                truncation_reason = TraversalTruncationReason.MAX_NODES
            else:
                included_candidates = ordered_candidates

            for candidate_node in included_candidates:
                depth_by_node_id[candidate_node.node_id] = depth
                ordered_nodes.append(candidate_node)

            frontier = tuple(node.node_id for node in included_candidates)

            if truncation_reason is not None:
                break

        returned_node_ids = frozenset(depth_by_node_id)
        traversal_nodes = tuple(
            TraversalNode(depth=depth_by_node_id[node.node_id], node=node)
            for node in ordered_nodes
        )
        relationships = self._induced_relationships(
            direction=direction,
            node_ids=returned_node_ids,
            relationship_type=selected_relationship_type,
        )
        self._guard_relationship_subgraph_against_cycles(
            node_ids=returned_node_ids,
            relationship_type=selected_relationship_type,
            relationships=relationships,
        )
        return TraversalResult(
            direction=direction,
            is_complete=truncation_reason is None,
            max_depth=max_depth,
            max_nodes=max_nodes,
            nodes=traversal_nodes,
            origin_node_id=origin_node.node_id,
            package_identity=self.store.package_identity,
            relationship_type=selected_relationship_type,
            relationships=relationships,
            truncation_reason=truncation_reason,
        )

    def all_root_paths(
        self,
        *,
        max_depth: int,
        max_path_node_occurrences: int,
        max_paths: int,
        node_id: NodeId,
        relationship_type: str | None = None,
    ) -> RootPathsResult:
        """Return bounded complete paths from the framework root to one node.

        Paths are generated in lexicographic root-to-origin relationship order. Only
        complete paths are returned. When the next complete path would exceed both size
        bounds, ``max_paths`` takes deterministic precedence as the reported truncation
        reason.

        A depth boundary defines which complete paths are requested and does not make
        the result incomplete. ``is_complete`` becomes false only when ``max_paths`` or
        ``max_path_node_occurrences`` prevents returning the next complete path within
        that boundary.

        Parameters
        ----------
        max_depth
            Maximum relationship count in one requested root path.
        max_path_node_occurrences
            Maximum sum of node counts across complete returned paths.
        max_paths
            Maximum number of complete returned paths.
        node_id
            Outer identifier of the path origin node.
        relationship_type
            Exact canonical relationship label. When omitted, use the selected
            profile's hierarchy relationship type.

        Returns
        -------
        RootPathsResult
            Complete deterministically ordered root paths and explicit truncation state.

        Raises
        ------
        GraphNodeNotFoundError
            If the origin node is unavailable.
        PackageValidationError
            If the framework root or a relationship endpoint is unavailable despite the
            successful package-validation construction precondition, or if a directed
            cycle is encountered within the requested path boundary.
        ValueError
            If a bound is invalid or an explicit relationship type is blank.
        """

        _validate_root_path_limits(
            max_depth=max_depth,
            max_path_node_occurrences=max_path_node_occurrences,
            max_paths=max_paths,
        )
        origin_node = self.store._require_node(node_id)
        root_node = self.store._require_framework_root()
        selected_relationship_type = self.store._select_relationship_type(
            relationship_type
        )
        ancestor_node_ids = self._bounded_ancestor_node_ids(
            max_depth=max_depth,
            node_id=origin_node.node_id,
            relationship_type=selected_relationship_type,
        )
        ancestor_relationships = self._induced_relationships(
            direction=GraphTraversalDirection.ANCESTORS,
            node_ids=ancestor_node_ids,
            relationship_type=selected_relationship_type,
        )
        self._guard_relationship_subgraph_against_cycles(
            node_ids=ancestor_node_ids,
            relationship_type=selected_relationship_type,
            relationships=ancestor_relationships,
        )

        if origin_node.node_id == root_node.node_id:
            root_path = RootPath(nodes=(root_node,), relationships=())
            return RootPathsResult(
                framework_root_id=self.store.framework_root_id,
                is_complete=True,
                max_depth=max_depth,
                max_path_node_occurrences=max_path_node_occurrences,
                max_paths=max_paths,
                origin_node_id=origin_node.node_id,
                package_identity=self.store.package_identity,
                paths=(root_path,),
                relationship_type=selected_relationship_type,
                truncation_reason=None,
            )

        if self.store.framework_root_id not in ancestor_node_ids:
            return RootPathsResult(
                framework_root_id=self.store.framework_root_id,
                is_complete=True,
                max_depth=max_depth,
                max_path_node_occurrences=max_path_node_occurrences,
                max_paths=max_paths,
                origin_node_id=origin_node.node_id,
                package_identity=self.store.package_identity,
                paths=(),
                relationship_type=selected_relationship_type,
                truncation_reason=None,
            )

        initial_relationships = self._eligible_root_path_relationships(
            ancestor_node_ids=ancestor_node_ids,
            node_id=root_node.node_id,
            relationship_type=selected_relationship_type,
        )
        stack: list[tuple[NodeId, tuple[GraphRelationship, ...], int]] = [
            (root_node.node_id, initial_relationships, 0)
        ]
        active_node_ids: set[NodeId] = {root_node.node_id}
        path_nodes: list[GraphNodeRecord] = [root_node]
        path_relationships: list[GraphRelationship] = []
        paths: list[RootPath] = []
        path_node_occurrences = 0
        truncation_reason: TraversalTruncationReason | None = None

        while stack:
            current_node_id, relationships, next_relationship_index = stack[-1]

            if current_node_id == origin_node.node_id:
                candidate_path = RootPath(
                    nodes=tuple(path_nodes), relationships=tuple(path_relationships)
                )

                if len(paths) >= max_paths:
                    truncation_reason = TraversalTruncationReason.MAX_PATHS
                    break

                candidate_occurrences = path_node_occurrences + len(path_nodes)

                if candidate_occurrences > max_path_node_occurrences:
                    truncation_reason = (
                        TraversalTruncationReason.MAX_PATH_NODE_OCCURRENCES
                    )
                    break

                paths.append(candidate_path)
                path_node_occurrences = candidate_occurrences
                stack.pop()
                popped_node = path_nodes.pop()
                active_node_ids.remove(popped_node.node_id)

                if path_relationships:
                    path_relationships.pop()

                continue

            if len(path_relationships) >= max_depth or next_relationship_index >= len(
                relationships
            ):
                stack.pop()
                popped_node = path_nodes.pop()
                active_node_ids.remove(popped_node.node_id)

                if path_relationships:
                    path_relationships.pop()

                continue

            relationship = relationships[next_relationship_index]
            stack[-1] = (
                current_node_id,
                relationships,
                next_relationship_index + 1,
            )
            target_node_id = relationship.target_node_id

            if target_node_id in active_node_ids:
                _raise_cycle(
                    node_id=target_node_id,
                    relationship=relationship,
                    relationship_type=selected_relationship_type,
                )

            target_node = self.store._require_relationship_endpoint(
                node_id=target_node_id, relationship_id=relationship.relationship_id
            )
            active_node_ids.add(target_node_id)
            path_nodes.append(target_node)
            path_relationships.append(relationship)
            next_relationships = self._eligible_root_path_relationships(
                ancestor_node_ids=ancestor_node_ids,
                node_id=target_node_id,
                relationship_type=selected_relationship_type,
            )
            stack.append((target_node_id, next_relationships, 0))

        return RootPathsResult(
            framework_root_id=self.store.framework_root_id,
            is_complete=truncation_reason is None,
            max_depth=max_depth,
            max_path_node_occurrences=max_path_node_occurrences,
            max_paths=max_paths,
            origin_node_id=origin_node.node_id,
            package_identity=self.store.package_identity,
            paths=tuple(paths),
            relationship_type=selected_relationship_type,
            truncation_reason=truncation_reason,
        )

    def ancestors(
        self,
        *,
        max_depth: int,
        max_nodes: int,
        node_id: NodeId,
        relationship_type: str | None = None,
    ) -> TraversalResult:
        """Return a deterministic bounded ancestor traversal including the origin.

        Parameters
        ----------
        max_depth
            Maximum incoming relationship distance from the origin.
        max_nodes
            Maximum unique returned nodes, including the origin.
        node_id
            Outer identifier of the origin node.
        relationship_type
            Exact canonical relationship label. When omitted, use the selected
            profile's hierarchy relationship type.

        Returns
        -------
        TraversalResult
            Origin, bounded ancestors, induced relationships, and truncation state.

        Raises
        ------
        GraphNodeNotFoundError
            If the origin node is unavailable.
        PackageValidationError
            If a relationship endpoint is unavailable despite the successful
            package-validation construction precondition, or if a directed cycle is
            encountered within the requested depth boundary.
        ValueError
            If a bound is invalid or an explicit relationship type is blank.
        """

        return self._traverse(
            direction=GraphTraversalDirection.ANCESTORS,
            max_depth=max_depth,
            max_nodes=max_nodes,
            node_id=node_id,
            relationship_type=relationship_type,
        )

    def descendants(
        self,
        *,
        max_depth: int,
        max_nodes: int,
        node_id: NodeId,
        relationship_type: str | None = None,
    ) -> TraversalResult:
        """Return a deterministic bounded descendant traversal including the origin.

        Parameters
        ----------
        max_depth
            Maximum outgoing relationship distance from the origin.
        max_nodes
            Maximum unique returned nodes, including the origin.
        node_id
            Outer identifier of the origin node.
        relationship_type
            Exact canonical relationship label. When omitted, use the selected
            profile's hierarchy relationship type.

        Returns
        -------
        TraversalResult
            Origin, bounded descendants, induced relationships, and truncation state.

        Raises
        ------
        GraphNodeNotFoundError
            If the origin node is unavailable.
        PackageValidationError
            If a relationship endpoint is unavailable despite the successful
            package-validation construction precondition, or if a directed cycle is
            encountered within the requested depth boundary.
        ValueError
            If a bound is invalid or an explicit relationship type is blank.
        """

        return self._traverse(
            direction=GraphTraversalDirection.DESCENDANTS,
            max_depth=max_depth,
            max_nodes=max_nodes,
            node_id=node_id,
            relationship_type=relationship_type,
        )
