"""Bounded breadth-first simple paths over immutable builds adjacency."""

# Future Library
from __future__ import annotations

# Standard Library
import json

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
class PathIdBound:
    """Longest JSON-encoded builds relationship and endpoint IDs in one package.

    Reserving a worst-case nextUnreturnedPath from these real IDs keeps emission
    within the size budget without charging the 1,024-character type maxima.
    """

    node_id: NodeId
    relationship_id: RelationshipId


@dataclass(frozen=True, slots=True)
class _PathContext:
    """Pin shared evidence helpers and original adjacency to one exact route."""

    adjacency: TraversalAdjacency
    id_bound: PathIdBound | None
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
    next_unreturned: ProgressionPath | None = None
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
    """Admit a completed path and reserve final counter/frontier envelope size.

    Parameters
    ----------
    context
        Pinned runtime and shared byte/character evidence policy.
    rows
        Bounded local evidence tables and counters.
    state
        Completed target path; never expanded further.

    Returns
    -------
    bool
        True after admission; False on a whole-path output-size stop.
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
        _stop_on_size(
            context=context,
            previous_edges=previous_edges,
            previous_nodes=previous_nodes,
            rows=rows,
            state=state,
        )
        return False

    return True


def _encoded_cost(value: str) -> tuple[int, int]:
    """Measure one ID as emitted inside the text mirror within the tool envelope.

    Parameters
    ----------
    value
        Original node or relationship identifier.

    Returns
    -------
    tuple[int, int]
        UTF-8 bytes then characters of the doubly JSON-encoded value, its most
        expensive emitted form; ordinary accepted IDs are ASCII so both agree.
    """

    encoded = json.dumps(json.dumps(value, ensure_ascii=False), ensure_ascii=False)
    return len(encoded.encode("utf-8")), len(encoded)


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


def _first_path_error(
    *, error: ProgressionResultTooLargeError, state: _PathState
) -> ProgressionResultTooLargeError:
    """Name the unreturnable first path so clients can inspect its stored edges.

    Parameters
    ----------
    error
        Shared size failure for the complete first-path envelope.
    state
        First completed path, which no request with these endpoints can return.

    Returns
    -------
    ProgressionResultTooLargeError
        Same failure with the path's ordered relationship IDs in details and hint.
    """

    relationship_ids = [str(edge.relationship_id) for edge in state.edges]
    return ProgressionResultTooLargeError(
        details={**error.details, "relationship_ids": tuple(relationship_ids)},
        message=error.message,
        recovery_hint=(
            "The first connecting path does not fit. Its ordered relationship IDs "
            f"are {json.dumps(relationship_ids, ensure_ascii=False)}; inspect each "
            f"with get_learning_progression. {error.recovery_hint or ''}"
        ),
    )


def _require_size(*, context: _PathContext, reserve: bool, rows: _PathRows) -> None:
    """Measure the shared tool envelope with actual or worst-case final metadata.

    Parameters
    ----------
    context
        Existing service encoder for both complete-envelope ceilings.
    reserve
        Reserve counter/frontier/reason growth before more work occurs.
    rows
        Current finite output tables and search state.
    """

    context.service.require_paths_result_size(
        result=_result(context=context, reserve=reserve, rows=rows)
    )


def _reserved_path(*, context: _PathContext) -> ProgressionPath | None:
    """Build the largest ID-only path this request could later report as unreturned.

    Parameters
    ----------
    context
        Requested depth and the package's longest real builds IDs.

    Returns
    -------
    ProgressionPath | None
        Worst-case nextUnreturnedPath, or None when the package has no builds edges.
    """

    if context.id_bound is None:
        return None

    return ProgressionPath(
        node_ids=(context.id_bound.node_id,) * (context.request.max_depth + 1),
        relationship_ids=(context.id_bound.relationship_id,)
        * context.request.max_depth,
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
        next_unreturned_path=(
            _reserved_path(context=context) if reserve else rows.next_unreturned
        ),
        nodes=tuple(rows.nodes.values()),
        paths=tuple(rows.paths),
        relationships=tuple(rows.relationships.values()),
        request=context.request,
        scope_complete=not any(reason != "depth_limit" for reason in reasons),
        source_node_id=context.source,
        target_node_id=context.target,
        truncation_reasons=reasons,
    )


def _stop_on_size(
    *,
    context: _PathContext,
    previous_edges: set[RelationshipId],
    previous_nodes: set[NodeId],
    rows: _PathRows,
    state: _PathState,
) -> None:
    """Keep a fitting path, or roll back a later one and name it, then stop.

    Parameters
    ----------
    context
        Shared encoder and pinned route.
    previous_edges
        Relationship-table keys before this path's speculative evidence.
    previous_nodes
        Node-table keys before this path's speculative evidence.
    rows
        Evidence tables including the path that failed conservative reservation.
    state
        Completed path that failed reservation.

    Raises
    ------
    ProgressionResultTooLargeError
        If the first path cannot fit, with its ordered relationship IDs.
    """

    # Reservation is conservative; keep the path if the actual final envelope fits.
    # No room is then guaranteed for another path, so selection stops either way.
    byte_reason: set[PathTruncationReason] = {"byte_limit"} if rows.queue else set()
    stop_reasons = rows.reasons | byte_reason

    try:
        _require_size(
            context=context, reserve=False, rows=replace(rows, reasons=stop_reasons)
        )
    except ProgressionResultTooLargeError as error:
        if len(rows.paths) == 1:
            raise _first_path_error(error=error, state=state) from error

        # Earlier paths passed reservation, which covered this outcome's final
        # counters, reasons and a worst-case nextUnreturnedPath.
        rows.paths.pop()
        rows.nodes = {
            key: value for key, value in rows.nodes.items() if key in previous_nodes
        }
        rows.relationships = {
            key: value
            for key, value in rows.relationships.items()
            if key in previous_edges
        }
        rows.next_unreturned = ProgressionPath(
            node_ids=state.node_ids,
            relationship_ids=tuple(edge.relationship_id for edge in state.edges),
        )

        # The stopped path stays counted in the queued frontier.
        rows.queue.appendleft(state)
        rows.reasons.add("byte_limit")
        return

    rows.reasons = stop_reasons


def path_id_bound(*, adjacency: TraversalAdjacency) -> PathIdBound | None:
    """Select one package's longest builds IDs once, outside query work.

    Parameters
    ----------
    adjacency
        Immutable builds-only adjacency for one accepted package.

    Returns
    -------
    PathIdBound | None
        Longest emitted node and relationship IDs, or None without builds edges.
    """

    edges = tuple(
        edge
        for (direction, _), entries in adjacency.items()
        if direction == "downstream"
        for edge in entries
    )

    if not edges:
        return None

    return PathIdBound(
        node_id=max(
            (
                node
                for edge in edges
                for node in (edge.source_node_id, edge.target_node_id)
            ),
            key=_encoded_cost,
        ),
        relationship_id=max(
            (edge.relationship_id for edge in edges), key=_encoded_cost
        ),
    )


def paths_result(
    *,
    adjacency: TraversalAdjacency,
    id_bound: PathIdBound | None = None,
    request: GetLearningProgressionPathsRequest,
    runtime: CatalogPackageRuntime,
    service: LearningProgressionsService,
) -> GetLearningProgressionPathsResult:
    """Enumerate breadth-first per-path states, preserving directed alternatives.

    Parameters
    ----------
    adjacency
        DEV-014 immutable builds-only sorted original references.
    id_bound
        Precomputed longest package IDs; derived from adjacency when omitted.
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
        id_bound=(
            id_bound if id_bound is not None else path_id_bound(adjacency=adjacency)
        ),
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
