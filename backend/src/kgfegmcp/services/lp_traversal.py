"""Bounded builds-only BFS over accepted original edge references."""

# Future Library
from __future__ import annotations

# Standard Library
from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, TypeAlias, cast

# Package Library
from kgfegmcp.catalog.models import CatalogPackageRuntime
from kgfegmcp.domain.identifiers import NodeId, RelationshipId
from kgfegmcp.errors import ProgressionResultTooLargeError
from kgfegmcp.graph.models import GraphRelationship, StandardNode
from kgfegmcp.services.lp_models import (
    ProgressionMetadata,
    ProgressionRelationshipEvidence,
    ProgressionStandardSummary,
    ProgressionTraversalCounters,
    ProgressionTraversalDirection,
    ProgressionTraversalDistance,
    ProgressionTraversalFrontier,
    TraversalTruncationReason,
    TraverseLearningProgressionsRequest,
    TraverseLearningProgressionsResult,
)

if TYPE_CHECKING:
    # Package Library
    from kgfegmcp.services.learning_progressions import LearningProgressionsService


_REASONS: tuple[TraversalTruncationReason, ...] = (
    "depth_limit",
    "node_limit",
    "edge_limit",
    "work_limit",
    "byte_limit",
)
TraversalAdjacency: TypeAlias = Mapping[
    tuple[ProgressionTraversalDirection, NodeId], tuple[GraphRelationship, ...]
]


@dataclass(frozen=True, slots=True)
class _TraversalContext:
    """Pin one query to its accepted runtime and immutable sorted adjacency.

    Examples
    --------
    >>> context.request.direction
    'downstream'
    """

    adjacency: TraversalAdjacency
    metadata: ProgressionMetadata
    request: TraverseLearningProgressionsRequest
    runtime: CatalogPackageRuntime
    service: LearningProgressionsService


@dataclass(slots=True)
class _TraversalRows:
    """Own finite query-local BFS state without modifying accepted records.

    Examples
    --------
    >>> rows.examined
    0
    """

    depth_examined: int = 0
    depth_limited: dict[NodeId, int] = field(default_factory=dict)
    distances: dict[NodeId, int] = field(default_factory=dict)
    examined: int = 0
    nodes: dict[NodeId, ProgressionStandardSummary] = field(default_factory=dict)
    positions: dict[NodeId, int] = field(default_factory=dict)
    queue: deque[NodeId] = field(default_factory=deque)
    reasons: set[TraversalTruncationReason] = field(default_factory=set)
    relationships: dict[RelationshipId, ProgressionRelationshipEvidence] = field(
        default_factory=dict
    )


def _add_edge(
    *,
    context: _TraversalContext,
    edge: GraphRelationship,
    node_id: NodeId,
    rows: _TraversalRows,
) -> TraversalTruncationReason | None:
    """Admit one original edge only after node, edge and encoded-result checks.

    Parameters
    ----------
    context
        Pinned query and evidence helpers.
    edge
        Examined original builds edge.
    node_id
        Current BFS node.
    rows
        Bounded local evidence and distances.

    Returns
    -------
    TraversalTruncationReason | None
        Blocking budget, or None after admission/deduplication/depth inspection.
    """

    adjacent = (
        edge.source_node_id
        if context.request.direction == "upstream"
        else edge.target_node_id
    )
    is_new = adjacent not in rows.nodes

    # At the depth boundary retain internal merging/cycle edges, but never add nodes.
    if is_new and rows.distances[node_id] == context.request.max_depth:
        rows.depth_limited[node_id] = rows.depth_limited.get(node_id, 0) + 1
        rows.reasons.add("depth_limit")
        return None

    if edge.relationship_id in rows.relationships:
        return None

    if is_new and len(rows.nodes) == context.request.max_nodes:
        return "node_limit"

    if len(rows.relationships) == context.request.max_edges:
        return "edge_limit"

    return _admit_edge(
        adjacent=adjacent, context=context, edge=edge, node_id=node_id, rows=rows
    )


def _admit_edge(
    *,
    adjacent: NodeId,
    context: _TraversalContext,
    edge: GraphRelationship,
    node_id: NodeId,
    rows: _TraversalRows,
) -> TraversalTruncationReason | None:
    """Project one finite entry and reserve its complete final-envelope overhead.

    Parameters
    ----------
    adjacent
        Neighbor endpoint in the requested direction.
    context
        Pinned query and evidence helpers.
    edge
        Original builds edge within node/edge bounds.
    node_id
        Current BFS node.
    rows
        Bounded local tables; speculative entry is removed on a byte stop.

    Returns
    -------
    TraversalTruncationReason | None
        Byte stop, or None after admission.
    """

    is_new = adjacent not in rows.nodes

    if is_new:
        rows.nodes[adjacent] = context.service.standard_summary(
            node=cast(StandardNode, context.runtime.graph_store.nodes_by_id[adjacent]),
            runtime=context.runtime,
        )
        rows.distances[adjacent] = rows.distances[node_id] + 1
        rows.positions[adjacent] = 0

    rows.relationships[edge.relationship_id] = context.service.relationship_evidence(
        relationship=edge, runtime=context.runtime
    )

    try:
        _require_size(
            context=context, result=_result(context=context, reserve=True, rows=rows)
        )
    except ProgressionResultTooLargeError:
        if len(rows.relationships) == 1:
            # Conservative reservation must not reject an actually fitting first entry.
            # Stop here with its exact final frontier, or fail if it too exceeds the
            # shared ceiling. No further work is attempted.
            rows.positions[node_id] += 1
            rows.reasons.add("byte_limit")
            _require_size(
                context=context,
                result=_result(context=context, reserve=False, rows=rows),
            )
            return "byte_limit"

        _require_edge_size(
            adjacent=adjacent, context=context, edge=edge, node_id=node_id, rows=rows
        )
        del rows.relationships[edge.relationship_id]

        if is_new:
            del rows.nodes[adjacent]
            del rows.distances[adjacent]
            del rows.positions[adjacent]

        return "byte_limit"

    if is_new:
        rows.queue.append(adjacent)

    return None


def _examine_node(
    *, context: _TraversalContext, node_id: NodeId, rows: _TraversalRows
) -> bool:
    """Inspect sorted adjacency within fixed work, including depth-frontier checks.

    Parameters
    ----------
    context
        Pinned builds-only adjacency and limits.
    node_id
        Returned node to expand.
    rows
        Local counters, evidence and pending positions.

    Returns
    -------
    bool
        True when this adjacency is completely examined; False on a hard budget.
    """

    edges = context.adjacency.get((context.request.direction, node_id), ())

    while rows.positions[node_id] < len(edges):
        if rows.examined == 5000:
            rows.reasons.add("work_limit")
            return False

        edge = edges[rows.positions[node_id]]
        rows.examined += 1

        if rows.distances[node_id] == context.request.max_depth:
            rows.depth_examined += 1

        reason = _add_edge(context=context, edge=edge, node_id=node_id, rows=rows)

        if reason is not None:
            rows.reasons.add(reason)
            return False

        rows.positions[node_id] += 1

    return True


def _require_edge_size(
    *,
    adjacent: NodeId,
    context: _TraversalContext,
    edge: GraphRelationship,
    node_id: NodeId,
    rows: _TraversalRows,
) -> None:
    """Reject an unreturnable edge before treating overflow as collection truncation.

    Parameters
    ----------
    adjacent
        Neighbor endpoint in the requested direction.
    context
        Shared byte policy and pinned query metadata.
    edge
        Speculative original edge whose complete evidence must fit individually.
    node_id
        Current BFS endpoint.
    rows
        Projected evidence and actual counters before whole-entry rollback.
    """

    # Keep the origin and both endpoints, without earlier unrelated evidence. This
    # exact minimal envelope distinguishes an oversized entry from a full collection;
    # conservative reservation alone must not reject a fitting entry.
    node_ids = dict.fromkeys((next(iter(rows.nodes)), node_id, adjacent))
    single = _TraversalRows(
        depth_examined=rows.depth_examined,
        distances={key: rows.distances[key] for key in node_ids},
        examined=rows.examined,
        nodes={key: rows.nodes[key] for key in node_ids},
        positions={key: int(key == node_id) for key in node_ids},
        reasons={"byte_limit"},
        relationships={edge.relationship_id: rows.relationships[edge.relationship_id]},
    )
    _require_size(
        context=context, result=_result(context=context, reserve=False, rows=single)
    )


def _require_size(
    *, context: _TraversalContext, result: TraverseLearningProgressionsResult
) -> None:
    """Use the shared service encoder for text plus structured-content bytes.

    Parameters
    ----------
    context
        Existing evidence service owning the byte policy.
    result
        Candidate or final complete envelope.
    """

    context.service.require_traversal_result_size(result=result)


def _result(
    *, context: _TraversalContext, reserve: bool, rows: _TraversalRows
) -> TraverseLearningProgressionsResult:
    """Freeze evidence and actual frontier, or conservatively reserve final metadata.

    Parameters
    ----------
    context
        Exact identity and bounded request.
    reserve
        Reserve the largest frontier/counters/reasons for these returned nodes.
    rows
        Finite query-local state.

    Returns
    -------
    TraverseLearningProgressionsResult
        Immutable derived subgraph with exact original generated edges.
    """

    frontier = []
    fully_examined = 0

    for node_id, depth in rows.distances.items():
        count = len(context.adjacency.get((context.request.direction, node_id), ()))

        # Pending includes an inspected edge that a budget prevented admitting.
        pending = count if reserve else count - rows.positions[node_id]
        limited = count if reserve else rows.depth_limited.get(node_id, 0)
        fully_examined += int(rows.positions[node_id] == count)

        if pending or limited:
            frontier.append(
                ProgressionTraversalFrontier(
                    depth=depth,
                    depth_limited_relationship_count=limited,
                    node_id=node_id,
                    pending_relationship_count=pending,
                )
            )

    reasons = (
        _REASONS
        if reserve
        else tuple(reason for reason in _REASONS if reason in rows.reasons)
    )

    # A fitting first entry may consume the byte reservation yet exhaust all adjacency.
    # There is no actual byte truncation when no frontier remains.
    if not reserve and not frontier and reasons == ("byte_limit",):
        reasons = ()

    return TraverseLearningProgressionsResult(
        counters=ProgressionTraversalCounters(
            depth_frontier_examined_relationship_count=(
                5000 if reserve else rows.depth_examined
            ),
            examined_relationship_count=5000 if reserve else rows.examined,
            fully_examined_node_count=250 if reserve else fully_examined,
            returned_node_count=len(rows.nodes),
            returned_relationship_count=len(rows.relationships),
        ),
        distances=tuple(
            ProgressionTraversalDistance(depth=depth, node_id=node_id)
            for node_id, depth in rows.distances.items()
        ),
        frontier=tuple(frontier),
        graph_exhausted=not reasons,
        metadata=context.metadata,
        nodes=tuple(rows.nodes.values()),
        origin_node_id=next(iter(rows.nodes)),
        relationships=tuple(rows.relationships.values()),
        request=context.request,
        scope_complete=not any(reason != "depth_limit" for reason in reasons),
        truncation_reasons=reasons,
    )


def traversal_adjacency(*, runtime: CatalogPackageRuntime) -> TraversalAdjacency:
    """Sort existing builds adjacency once at service construction, never per query.

    Parameters
    ----------
    runtime
        Accepted shared GraphStore with original record instances.

    Returns
    -------
    TraversalAdjacency
        Immutable sorted references; no separate graph store or content copy.
    """

    ordered = {}

    for direction, index in (
        ("downstream", runtime.graph_store.outgoing_by_type_and_node),
        ("upstream", runtime.graph_store.incoming_by_type_and_node),
    ):
        for (label, node_id), edges in index.items():
            if label == "buildsTowards":
                ordered[(cast(ProgressionTraversalDirection, direction), node_id)] = (
                    tuple(sorted(edges, key=lambda edge: edge.relationship_id))
                )

    return MappingProxyType(ordered)


def traversal_result(
    *,
    adjacency: TraversalAdjacency,
    request: TraverseLearningProgressionsRequest,
    runtime: CatalogPackageRuntime,
    service: LearningProgressionsService,
) -> TraverseLearningProgressionsResult:
    """Walk only stored builds edges with bounded BFS and explicit remaining frontier.

    Parameters
    ----------
    adjacency
        Service-construction-time sorted original builds references.
    request
        Validated direction, exact origin and caller bounds.
    runtime
        Already pinned accepted package.
    service
        Existing route, selector, rights and evidence helpers.

    Returns
    -------
    TraverseLearningProgressionsResult
        Deterministic bounded subgraph, distances, counters and completeness.
    """

    origin = service.resolve_standard(identifier=request.identifier, runtime=runtime)
    context = _TraversalContext(
        adjacency=adjacency,
        metadata=service.evidence_metadata(runtime=runtime),
        request=request,
        runtime=runtime,
        service=service,
    )
    rows = _TraversalRows(
        distances={origin.node_id: 0},
        nodes={origin.node_id: service.standard_summary(node=origin, runtime=runtime)},
        positions={origin.node_id: 0},
        queue=deque((origin.node_id,)),
    )

    # Validate the origin envelope; each admitted edge reserves final metadata.
    _require_size(
        context=context, result=_result(context=context, reserve=False, rows=rows)
    )

    while rows.queue:
        node_id = rows.queue.popleft()

        if not _examine_node(context=context, node_id=node_id, rows=rows):
            break

    result = _result(context=context, reserve=False, rows=rows)
    _require_size(context=context, result=result)
    return result
