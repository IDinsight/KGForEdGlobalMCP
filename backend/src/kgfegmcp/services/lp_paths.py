"""Bounded exact-length, target-aware simple paths over immutable builds adjacency.

A backward pass from the target records, for every standard that can reach it, the
exact hop counts that can still finish there. A forward depth-first search then emits
paths length by length in relationship-ID order, extending only edges that can finish at
exactly that length. Accepted packages reject buildsTowards cycles, so every directed
path is simple and these exact lengths are well defined.
"""

# Future Library
from __future__ import annotations

# Standard Library
import json

from collections import defaultdict, deque
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Final

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
# Fixed per-request budgets for inspected relationships and created partial paths.
_SEARCH_BUDGET: Final[int] = 5000


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
    """Keep one bounded partial path from the source."""

    edges: tuple[GraphRelationship, ...]
    node_ids: tuple[NodeId, ...]


@dataclass(slots=True)
class _PathRows:
    """Own query-local counters, live partial paths and deduplicated path evidence.

    ``queue`` holds the partial paths that are still alive: the depth-first prefixes
    from the source state to the path being extended.
    """

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


@dataclass(frozen=True, slots=True)
class _TargetReach:
    """Describe how every standard that can reach the target does so.

    ``lengths`` maps each such standard to a bitmask whose bit ``h`` is set when a
    path of exactly ``h`` hops (at most the requested depth) reaches the target.
    ``longest`` and ``shortest`` are uncapped hop counts to the target.
    """

    lengths: dict[NodeId, int]
    longest: dict[NodeId, int]
    shortest: dict[NodeId, int]


def _admit_path(
    *, context: _PathContext, more: bool, rows: _PathRows, state: _PathState
) -> bool:
    """Admit a completed path and reserve final counter/frontier envelope size.

    Parameters
    ----------
    context
        Pinned runtime and shared byte/character evidence policy.
    more
        Whether another path within the requested depth exists after this one.
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
            more=more,
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


def _enumerate(*, context: _PathContext, reach: _TargetReach, rows: _PathRows) -> None:
    """Emit paths length by length, shortest first, until done or a stop applies.

    Parameters
    ----------
    context
        Requested depth and path count for one exact route.
    reach
        Exact target hop counts from the backward pass.
    rows
        Counters, live partial paths and admitted evidence.

    Examples
    --------
    >>> _enumerate(context=context, reach=reach, rows=rows)
    >>> [len(path.relationship_ids) for path in rows.paths]
    [2, 2, 3]
    """

    source_lengths = reach.lengths.get(context.source, 0)

    for hops in range(1, context.request.max_depth + 1):
        if not source_lengths >> hops & 1:
            continue

        # A set bit guarantees another path of this length exists.
        if len(rows.paths) == context.request.max_paths:
            rows.reasons.add("path_limit")
            return

        if not _search_length(context=context, hops=hops, reach=reach, rows=rows):
            return

    # Finished: nothing remains alive or uninspected.
    rows.queue.clear()
    rows.pending = 0


def _extend(
    *,
    context: _PathContext,
    edge: GraphRelationship,
    hops: int,
    reach: _TargetReach,
    rows: _PathRows,
    state: _PathState,
) -> bool | _PathState | None:
    """Inspect one edge and extend, complete or skip the partial path along it.

    Parameters
    ----------
    context
        Requested path count and shared evidence helpers.
    edge
        Next sorted downstream builds edge of the partial path's last standard.
    hops
        Exact path length being enumerated.
    reach
        Exact target hop counts from the backward pass.
    rows
        Counters, live partial paths and admitted evidence.
    state
        Partial path being extended.

    Returns
    -------
    bool | _PathState | None
        True when a longer partial path was pushed, False when the edge was skipped,
        the completed path when the edge reached the target, and None when a work,
        queue or path stop applies.
    """

    if rows.examined == _SEARCH_BUDGET:
        rows.reasons.add("work_limit")
        return None

    rows.examined += 1
    head = edge.target_node_id
    remaining = hops - len(state.edges) - 1

    if not reach.lengths.get(head, 0) >> remaining & 1:
        # The head reaches the target, but only in more hops than remain.
        if reach.shortest.get(head, remaining) > remaining:
            rows.depth_examined += 1
            rows.depth_limited += 1

        return False

    # The eligible edge guarantees one more path, so stop exactly at max_paths.
    if len(rows.paths) == context.request.max_paths:
        rows.reasons.add("path_limit")
        return None

    if rows.enqueued == _SEARCH_BUDGET:
        rows.reasons.add("queue_limit")
        return None

    rows.enqueued += 1
    child = _PathState(edges=(*state.edges, edge), node_ids=(*state.node_ids, head))

    if remaining:
        rows.queue.append(child)
        rows.peak_queue = max(rows.peak_queue, len(rows.queue))
        return True

    # Only the target has zero hops left, so the child is a complete path.
    rows.pending -= 1
    return child


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


def _has_more(
    *,
    context: _PathContext,
    hops: int,
    indices: list[int],
    reach: _TargetReach,
    rows: _PathRows,
) -> bool:
    """Decide exactly whether another path within the requested depth remains.

    Parameters
    ----------
    context
        Builds-only sorted adjacency and requested depth.
    hops
        Exact path length being enumerated.
    indices
        Next edge index for each live partial path, parallel to ``rows.queue``.
    reach
        Exact target hop counts from the backward pass.
    rows
        Live partial paths from the source state onward.

    Returns
    -------
    bool
        True when an uninspected eligible edge or a longer exact length remains.
    """

    # Any eligible edge still to inspect guarantees a path of this length.
    for state, index in zip(rows.queue, indices):
        remaining = hops - len(state.edges) - 1
        edges = context.adjacency.get(("downstream", state.node_ids[-1]), ())

        if any(
            reach.lengths.get(edge.target_node_id, 0) >> remaining & 1
            for edge in edges[index:]
        ):
            return True

    # Lengths above the requested depth are already masked out of the bitmask.
    return reach.lengths.get(context.source, 0) >> (hops + 1) != 0


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
    budget = _SEARCH_BUDGET
    return GetLearningProgressionPathsResult(
        counters=ProgressionPathCounters(
            depth_frontier_examined_relationship_count=(
                budget if reserve else rows.depth_examined
            ),
            enqueued_state_count=budget if reserve else rows.enqueued,
            examined_relationship_count=budget if reserve else rows.examined,
            peak_queue_state_count=budget if reserve else rows.peak_queue,
            returned_path_count=len(rows.paths),
        ),
        frontier=ProgressionPathFrontier(
            depth_limited_extension_count=budget if reserve else rows.depth_limited,
            pending_adjacency_count=(
                max(budget, len(context.runtime.graph_store.relationships_by_id))
                if reserve
                else rows.pending
            ),
            queued_state_count=budget if reserve else len(rows.queue),
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


def _search_length(
    *, context: _PathContext, hops: int, reach: _TargetReach, rows: _PathRows
) -> bool:
    """Depth-first emit every path of exactly ``hops`` hops in relationship-ID order.

    Parameters
    ----------
    context
        Builds-only sorted adjacency for one exact route.
    hops
        Exact path length to enumerate.
    reach
        Exact target hop counts from the backward pass.
    rows
        Counters, live partial paths (the source state stays first) and evidence.

    Returns
    -------
    bool
        True when every path of this length was admitted; False on any stop.
    """

    # Next edge index for each live partial path, parallel to rows.queue.
    indices = [0]

    while True:
        state = rows.queue[-1]
        edges = context.adjacency.get(("downstream", state.node_ids[-1]), ())

        if indices[-1] == len(edges):
            # The source state stays alive for the next length.
            if len(indices) == 1:
                return True

            indices.pop()
            rows.queue.pop()
            continue

        rows.pending = len(edges) - indices[-1]
        edge = edges[indices[-1]]
        indices[-1] += 1
        outcome = _extend(
            context=context, edge=edge, hops=hops, reach=reach, rows=rows, state=state
        )

        if outcome is None:
            return False

        if isinstance(outcome, _PathState):
            more = _has_more(
                context=context, hops=hops, indices=indices, reach=reach, rows=rows
            )

            # A kept final path needs no stop; any other size stop ends the search.
            if not _admit_path(context=context, more=more, rows=rows, state=outcome):
                return not more and "byte_limit" not in rows.reasons
        elif outcome:
            indices.append(0)


def _stop_on_size(
    *,
    context: _PathContext,
    more: bool,
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
    more
        Whether another path within the requested depth exists after this one.
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
    byte_reason: set[PathTruncationReason] = {"byte_limit"} if more else set()
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


def _target_reach(*, context: _PathContext, rows: _PathRows) -> _TargetReach | None:
    """Walk upstream from the target once and derive exact reachable hop counts.

    Parameters
    ----------
    context
        Builds-only sorted adjacency, target and requested depth.
    rows
        Counters charged with every inspected upstream edge.

    Returns
    -------
    _TargetReach | None
        Hop counts for every standard that reaches the target, or None on a work
        stop.

    Examples
    --------
    >>> reach = _target_reach(context=context, rows=rows)
    >>> bin(reach.lengths[context.target])
    '0b1'
    """

    target = context.target
    predecessors: dict[NodeId, list[NodeId]] = {target: []}
    out_degree: dict[NodeId, int] = defaultdict(int)
    shortest = {target: 0}
    pending = deque((target,))

    # Breadth-first discovery of every ancestor; each upstream edge is inspected once.
    while pending:
        node = pending.popleft()
        edges = context.adjacency.get(("upstream", node), ())

        for index, edge in enumerate(edges):
            if rows.examined == _SEARCH_BUDGET:
                rows.pending = len(edges) - index
                rows.reasons.add("work_limit")
                return None

            rows.examined += 1
            parent = edge.source_node_id
            predecessors[node].append(parent)
            out_degree[parent] += 1

            if parent not in shortest:
                shortest[parent] = shortest[node] + 1
                predecessors[parent] = []
                pending.append(parent)

    # Acyclic, so settle each ancestor after all its successors toward the target.
    mask = (1 << (context.request.max_depth + 1)) - 1
    lengths = {target: 1}
    longest = {target: 0}
    ready = deque((target,))

    while ready:
        node = ready.popleft()

        for parent in predecessors[node]:
            lengths[parent] = lengths.get(parent, 0) | ((lengths[node] << 1) & mask)
            longest[parent] = max(longest.get(parent, 0), longest[node] + 1)
            out_degree[parent] -= 1

            if not out_degree[parent]:
                ready.append(parent)

    rows.pending = 0
    return _TargetReach(lengths=lengths, longest=longest, shortest=shortest)


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
    """Enumerate exact-length target-aware paths, preserving directed alternatives.

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
    reach = _target_reach(context=context, rows=rows)

    if reach is not None:
        # A connection longer than the requested depth exists exactly when this holds.
        if reach.longest.get(context.source, 0) > request.max_depth:
            rows.reasons.add("depth_limit")

        _enumerate(context=context, reach=reach, rows=rows)

    result = _result(context=context, reserve=False, rows=rows)
    service.require_paths_result_size(result=result)
    return result
