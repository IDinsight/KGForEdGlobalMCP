"""Bounded breadth-first simple paths over immutable builds adjacency."""

# Future Library
from __future__ import annotations

# Standard Library
from collections import deque
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

# Package Library
from kgfegmcp.catalog.models import CatalogPackageRuntime
from kgfegmcp.domain.identifiers import NodeId, RelationshipId
from kgfegmcp.errors import (
    InvalidProgressionRequestError,
    ProgressionResultTooLargeError,
)
from kgfegmcp.graph.models import GraphRelationship
from kgfegmcp.services.lp_models import (
    GetLearningProgressionPathsRequest,
    GetLearningProgressionPathsResult,
    PathTruncationReason,
    ProgressionMetadata,
    ProgressionPath,
    ProgressionPathCounters,
    ProgressionPathFrontier,
    ProgressionRelationshipEvidence,
    ProgressionStandardSummary,
)
from kgfegmcp.services.lp_traversal import TraversalAdjacency
from kgfegmcp.services.models import NodeIdStandardIdentifier

if TYPE_CHECKING:
    # Package Library
    from kgfegmcp.services.learning_progressions import LearningProgressionsService


_REASONS: tuple[PathTruncationReason, ...] = (
    "depth_limit",
    "path_limit",
    "work_limit",
    "queue_limit",
    "byte_limit",
)


@dataclass(frozen=True, slots=True)
class _PathContext:
    """Pin shared evidence helpers and original adjacency to one exact route."""

    adjacency: TraversalAdjacency
    metadata: ProgressionMetadata
    request: GetLearningProgressionPathsRequest
    runtime: CatalogPackageRuntime
    service: LearningProgressionsService
    source: NodeId
    target: NodeId


@dataclass(frozen=True, slots=True)
class _PathState:
    """Keep a bounded partial path with its own visited IDs, preserving merges."""

    edges: tuple[GraphRelationship, ...]
    node_ids: tuple[NodeId, ...]


@dataclass(slots=True)
class _PathRows:
    """Own query-local finite queue, actual counters and deduplicated path evidence."""

    depth_examined: int = 0
    depth_limited: int = 0
    enqueued: int = 1
    examined: int = 0
    nodes: dict[NodeId, ProgressionStandardSummary] = field(default_factory=dict)
    paths: list[ProgressionPath] = field(default_factory=list)
    peak_queue: int = 1
    pending: int = 0
    queue: deque[_PathState] = field(default_factory=deque)
    reasons: set[PathTruncationReason] = field(default_factory=set)
    relationships: dict[RelationshipId, ProgressionRelationshipEvidence] = field(
        default_factory=dict
    )


def _admit_path(*, context: _PathContext, rows: _PathRows, state: _PathState) -> bool:
    """Admit a completed path and reserve final counter/frontier envelope bytes.

    Parameters
    ----------
    context
        Pinned runtime and shared byte/evidence policy.
    rows
        Bounded local evidence tables and counters.
    state
        Completed target path; never expanded further.

    Returns
    -------
    bool
        True after admission; False on a whole-path byte stop.
    """

    previous_nodes = set(rows.nodes)
    previous_edges = set(rows.relationships)

    for node_id in state.node_ids:
        if node_id not in rows.nodes:
            rows.nodes[node_id] = context.service.standard_summary(
                node=context.service.resolve_standard(
                    identifier=NodeIdStandardIdentifier(
                        identifier_type="node_id", node_id=node_id
                    ),
                    runtime=context.runtime,
                ),
                runtime=context.runtime,
            )

    for edge in state.edges:
        if edge.relationship_id not in rows.relationships:
            rows.relationships[edge.relationship_id] = (
                context.service.relationship_evidence(
                    relationship=edge, runtime=context.runtime
                )
            )

    rows.paths.append(
        ProgressionPath(
            node_ids=state.node_ids,
            relationship_ids=tuple(edge.relationship_id for edge in state.edges),
        )
    )

    try:
        _require_size(context=context, reserve=True, rows=rows)
    except ProgressionResultTooLargeError:
        if len(rows.paths) == 1:
            # Reservation must not reject an actually fitting first complete path.
            if rows.queue:
                rows.reasons.add("byte_limit")

            _require_size(context=context, reserve=False, rows=rows)
            return False

        _require_path_size(context=context, rows=rows, state=state)
        rows.paths.pop()
        rows.nodes = {
            key: value for key, value in rows.nodes.items() if key in previous_nodes
        }
        rows.relationships = {
            key: value
            for key, value in rows.relationships.items()
            if key in previous_edges
        }

        # Include the rejected completed state in the unexplored frontier.
        rows.queue.appendleft(state)
        rows.reasons.add("byte_limit")
        return False

    return True


def _expand_state(*, context: _PathContext, rows: _PathRows, state: _PathState) -> bool:
    """Inspect sorted edges with work and cumulative queue checks before admission.

    Parameters
    ----------
    context
        Builds-only immutable adjacency and requested depth.
    rows
        Finite work counters, partial paths and remaining frontier.
    state
        One nonterminal partial path with its per-path visited IDs.

    Returns
    -------
    bool
        True after full inspection; False on a work/queue stop.
    """

    edges = context.adjacency.get(("downstream", state.node_ids[-1]), ())
    at_depth = len(state.edges) == context.request.max_depth
    rows.pending = len(edges)

    for edge in edges:
        if rows.examined == 5000:
            rows.reasons.add("work_limit")
            return False

        rows.examined += 1
        rows.depth_examined += int(at_depth)
        adjacent = edge.target_node_id

        if adjacent in state.node_ids:
            rows.pending -= 1
            continue

        if at_depth:
            rows.depth_limited += 1
            rows.reasons.add("depth_limit")
        else:
            if rows.enqueued == 5000:
                rows.reasons.add("queue_limit")
                return False

            # Bound insertion before allocating another partial path. No global visited
            # set: two prefixes that merge must both be expanded.
            rows.queue.append(
                _PathState(
                    edges=(*state.edges, edge), node_ids=(*state.node_ids, adjacent)
                )
            )
            rows.enqueued += 1
            rows.peak_queue = max(rows.peak_queue, len(rows.queue))

        rows.pending -= 1

    return True


def _require_path_size(
    *, context: _PathContext, rows: _PathRows, state: _PathState
) -> None:
    """Reject an individually oversized path rather than hiding it behind a byte stop.

    Parameters
    ----------
    context
        Shared byte policy and pinned route.
    rows
        Projected path tables and actual final metadata.
    state
        Completed path whose standalone envelope must fit.
    """

    single = replace(
        rows,
        nodes={node_id: rows.nodes[node_id] for node_id in state.node_ids},
        paths=[rows.paths[-1]],
        relationships={
            edge.relationship_id: rows.relationships[edge.relationship_id]
            for edge in state.edges
        },
    )
    _require_size(context=context, reserve=False, rows=single)


def _require_size(*, context: _PathContext, reserve: bool, rows: _PathRows) -> None:
    """Measure the shared tool envelope with actual or worst-case final metadata.

    Parameters
    ----------
    context
        Existing service byte encoder.
    reserve
        Reserve counter/frontier/reason growth before more work occurs.
    rows
        Current finite output tables and search state.
    """

    context.service.require_paths_result_size(
        result=_result(context=context, reserve=reserve, rows=rows)
    )


def _result(
    *, context: _PathContext, reserve: bool, rows: _PathRows
) -> GetLearningProgressionPathsResult:
    """Freeze exact complete-path evidence and scalar remaining-search frontier.

    Parameters
    ----------
    context
        Exact route, source/target and caller bounds.
    reserve
        Use worst-case final metadata under the fixed work/queue ceilings.
    rows
        Actual counters and finite local evidence.

    Returns
    -------
    GetLearningProgressionPathsResult
        Bounded paths, original hops and independent depth/exhaustion claims.
    """

    reasons = (
        _REASONS
        if reserve
        else tuple(reason for reason in _REASONS if reason in rows.reasons)
    )
    return GetLearningProgressionPathsResult(
        counters=ProgressionPathCounters(
            depth_frontier_examined_relationship_count=(
                5000 if reserve else rows.depth_examined
            ),
            enqueued_state_count=5000 if reserve else rows.enqueued,
            examined_relationship_count=5000 if reserve else rows.examined,
            peak_queue_state_count=5000 if reserve else rows.peak_queue,
            returned_path_count=len(rows.paths),
        ),
        frontier=ProgressionPathFrontier(
            depth_limited_extension_count=5000 if reserve else rows.depth_limited,
            pending_adjacency_count=(
                max(5000, len(context.runtime.graph_store.relationships_by_id))
                if reserve
                else rows.pending
            ),
            queued_state_count=5000 if reserve else len(rows.queue),
        ),
        graph_exhausted=not reasons,
        metadata=context.metadata,
        nodes=tuple(rows.nodes.values()),
        paths=tuple(rows.paths),
        relationships=tuple(rows.relationships.values()),
        request=context.request,
        scope_complete=not any(reason != "depth_limit" for reason in reasons),
        source_node_id=context.source,
        target_node_id=context.target,
        truncation_reasons=reasons,
    )


def paths_result(
    *,
    adjacency: TraversalAdjacency,
    request: GetLearningProgressionPathsRequest,
    runtime: CatalogPackageRuntime,
    service: LearningProgressionsService,
) -> GetLearningProgressionPathsResult:
    """Enumerate breadth-first per-path states, preserving directed alternatives.

    Parameters
    ----------
    adjacency
        DEV-014 immutable builds-only sorted original references.
    request
        Exact source/target selectors and bounded depth/path request.
    runtime
        Already pinned accepted package.
    service
        Existing standard selection, rights, evidence and byte helpers.

    Returns
    -------
    GetLearningProgressionPathsResult
        Paths ordered by hop count then relationship-ID tuple.

    Raises
    ------
    InvalidProgressionRequestError
        If both selectors resolve to the same source standard.
    """

    source = service.resolve_standard(
        identifier=request.source_identifier, runtime=runtime
    )
    target = service.resolve_standard(
        identifier=request.target_identifier, runtime=runtime
    )

    if source.node_id == target.node_id:
        raise InvalidProgressionRequestError(
            message="Path endpoints must be different standards."
        )

    context = _PathContext(
        adjacency=adjacency,
        metadata=service.evidence_metadata(runtime=runtime),
        request=request,
        runtime=runtime,
        service=service,
        source=source.node_id,
        target=target.node_id,
    )
    rows = _PathRows(
        nodes={
            source.node_id: service.standard_summary(node=source, runtime=runtime),
            target.node_id: service.standard_summary(node=target, runtime=runtime),
        },
        queue=deque((_PathState(edges=(), node_ids=(source.node_id,)),)),
    )
    _require_size(context=context, reserve=False, rows=rows)

    while rows.queue:
        state = rows.queue.popleft()

        if state.node_ids[-1] == context.target:
            if not _admit_path(context=context, rows=rows, state=state):
                break

            if len(rows.paths) == request.max_paths and rows.queue:
                rows.reasons.add("path_limit")
                break
        elif not _expand_state(context=context, rows=rows, state=state):
            break

    result = _result(context=context, reserve=False, rows=rows)
    service.require_paths_result_size(result=result)
    return result
