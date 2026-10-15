"""Independent bounded traversal and directed simple-path acceptance scenarios."""

# Standard Library
import json

from collections import defaultdict, deque
from typing import Any

# Third Party Library
import pytest

# Package Library
from kgfegmcp.bootstrap import AppState
from kgfegmcp.catalog.models import CatalogPackageRuntime
from kgfegmcp.errors import (
    InvalidProgressionRequestError,
    PackageValidationError,
)
from kgfegmcp.services.learning_progressions import progression_result_text
from kgfegmcp.services.lp_models import GetLearningProgressionPathsRequest
from tests.fixtures.progression_fixtures import (
    Topology,
    assert_path_invariants,
    baseline_paths,
    builds,
    rehydrated,
    selector,
)

CAPS = "south-africa-dbe-caps-english-home-language-grades-r-3"
DIAMOND = [("z", "a", "b"), ("a", "a", "c"), ("b", "b", "t"), ("c", "c", "t")]
# Connected CAPS pairs pinned from the accepted package by an independent BFS:
# shortest hop count, source node ID, target node ID.
CAPS_PAIRS = [
    (1, "0016a784-a3f2-57fa-91df-66d7d8eb4511", "0e2d7bb6-fd9f-52ce-9515-a6727097d016"),
    (8, "0016a784-a3f2-57fa-91df-66d7d8eb4511", "097e4c4a-8636-5312-8f7c-ce1fb2407cee"),
    (
        11,
        "0016a784-a3f2-57fa-91df-66d7d8eb4511",
        "2ccbf220-bf16-55ff-863b-f4230e268cd5",
    ),
    (
        12,
        "10deec8d-3bd4-58b8-a24b-5532996f103a",
        "ec9afa8e-5995-545b-9193-8ce046df0778",
    ),
]
CAPS_THIRTEEN_HOP = (
    "10deec8d-3bd4-58b8-a24b-5532996f103a",
    "2ccbf220-bf16-55ff-863b-f4230e268cd5",
)
ORIGINAL_FRAMEWORKS = 6


def assert_envelope_bounds(result: Any) -> None:
    """Independently measure complete text and structured evidence under both ceilings."""
    text = progression_result_text(result=result)
    structured = result.model_dump(by_alias=True, mode="json")
    assert json.loads(text) == structured
    serialized = json.dumps(
        {
            "_meta": None,
            "content": [{"text": text, "type": "text"}],
            "isError": False,
            "structuredContent": structured,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    assert len(serialized) <= 100000
    assert len(serialized.encode("utf-8")) <= 1048576


def caps_runtime(state: AppState) -> CatalogPackageRuntime:
    """Return the accepted CAPS package runtime.

    Parameters
    ----------
    state
        Application state bootstrapped from the accepted packages.

    Returns
    -------
    CatalogPackageRuntime
        The CAPS runtime.
    """

    return next(
        runtime
        for runtime in state.catalog_load_result.package_runtimes
        if runtime.catalog_package.package_identity.framework_id == CAPS
    )


def path_request(
    runtime: CatalogPackageRuntime,
    source: str,
    target: str,
    *,
    max_depth: int,
    max_paths: int = 3,
) -> GetLearningProgressionPathsRequest:
    """Pin one path request to an accepted package.

    Parameters
    ----------
    runtime
        Accepted package runtime.
    source
        Source node ID.
    target
        Target node ID.
    max_depth
        Requested maximum hop count.
    max_paths
        Requested maximum number of paths; the tool default when omitted.

    Returns
    -------
    GetLearningProgressionPathsRequest
        Request for the package's exact framework and snapshot.
    """

    identity = runtime.catalog_package.package_identity
    return GetLearningProgressionPathsRequest(
        framework_id=identity.framework_id,
        max_depth=max_depth,
        max_paths=max_paths,
        snapshot_id=identity.snapshot_id,
        source_identifier=selector(source),
        target_identifier=selector(target),
    )


def per_edge(
    pairs: list[tuple[str, str, str]], text: str
) -> list[tuple[str, str, str, str, str]]:
    """Make builds edges whose large attribution differs per edge, so it never lifts.

    Parameters
    ----------
    pairs
        Relationship ID, source and target of each edge.
    text
        Shared large prefix of every attribution.

    Returns
    -------
    list[tuple[str, str, str, str, str]]
        Topology edge specifications.
    """

    return [
        (identifier, source, target, "buildsTowards", f"{text} {identifier}")
        for identifier, source, target in pairs
    ]


def test_traversal_keeps_merging_edges(accepted_state: AppState) -> None:
    """Keep both branches in ID-sorted BFS order, excluding other labels."""
    graph = Topology(
        accepted_state,
        builds(DIAMOND)
        + [
            ("r", "a", "x", "relatesTo", ""),
            ("h", "a", "x", "hasChild", ""),
            ("s", "a", "x", "supports", ""),
        ],
    )
    result = graph.walk()
    assert [e.relationship.relationship_id for e in result.relationships] == [
        "a",
        "z",
        "c",
        "b",
    ]
    assert {d.node_id: d.depth for d in result.distances} == {
        "a": 0,
        "c": 1,
        "b": 1,
        "t": 2,
    }
    assert result.graph_exhausted and result.scope_complete
    assert all(
        e.relationship == graph.edges[e.relationship.relationship_id]
        for e in rehydrated(result)
    )


def test_traversal_keeps_cycle_closure(accepted_state: AppState) -> None:
    """Terminate a cycle and retain the closing edge at the depth frontier."""
    result = Topology(
        accepted_state, builds([("a", "a", "b"), ("b", "b", "c"), ("c", "c", "a")])
    ).walk(max_depth=2)
    assert len(result.relationships) == 3
    assert result.graph_exhausted and result.scope_complete
    assert result.counters.depth_frontier_examined_relationship_count == 1


@pytest.mark.parametrize(
    "limit,reason,count",
    [("max_nodes", "node_limit", 2), ("max_edges", "edge_limit", 1)],
)
def test_traversal_finite_table_limits(
    accepted_state: AppState, limit: str, reason: str, count: int
) -> None:
    """Stop before allocating an excess node or edge and retain a frontier."""
    result = Topology(accepted_state, builds(DIAMOND)).walk(**{limit: count})
    assert result.truncation_reasons == (reason,)
    assert not result.scope_complete and not result.graph_exhausted and result.frontier
    assert (
        len(result.nodes) if limit == "max_nodes" else len(result.relationships)
    ) == count


def test_traversal_depth_frontier_consumes_work(accepted_state: AppState) -> None:
    """Count excluded depth edges in the actual fixed examination budget."""
    pairs = [("a", "a", "b")] + [(f"z{i:05}", "b", "c") for i in range(5001)]
    result = Topology(accepted_state, builds(pairs)).walk(max_depth=1)
    assert result.counters.examined_relationship_count == 5000
    assert result.counters.depth_frontier_examined_relationship_count == 4999
    assert result.truncation_reasons == ("depth_limit", "work_limit")
    assert not result.scope_complete and result.frontier


def test_traversal_combination_only_bytes(accepted_state: AppState) -> None:
    """Omit the whole fitting second entry when only the combination is large."""
    pairs = [("a", "a", "b"), ("b", "a", "c")]
    # A per-edge attribution stays in every entry, so only the combination is large.
    text = "😀" * 30000
    for pair in pairs:
        control = Topology(accepted_state, per_edge([pair], text)).walk()
        assert control.scope_complete and control.graph_exhausted
        assert not control.truncation_reasons
        assert [e.relationship.relationship_id for e in control.relationships] == [
            pair[0]
        ]
        assert_envelope_bounds(control)
    graph = Topology(accepted_state, per_edge(pairs, text))
    result = graph.walk()
    assert result.truncation_reasons == ("byte_limit",)
    assert [e.relationship.relationship_id for e in result.relationships] == ["a"]
    assert rehydrated(result)[0].relationship == graph.edges["a"]
    assert {n.node_id for n in result.nodes} == {"a", "b"}
    assert {d.node_id: d.depth for d in result.distances} == {"a": 0, "b": 1}
    assert result.counters.examined_relationship_count == 2
    assert result.counters.returned_relationship_count == 1
    assert result.counters.returned_node_count == 2
    assert not result.scope_complete and not result.graph_exhausted and result.frontier
    assert graph.require_traversal_result_size(result=result) <= 1048576
    assert_envelope_bounds(result)


def test_paths_preserve_alternative_merges(accepted_state: AppState) -> None:
    """Retain alternatives sharing a target, sorted by hop count then ID tuple."""
    graph = Topology(accepted_state, builds(DIAMOND))
    result = graph.paths()
    assert [(p.relationship_ids, p.node_ids) for p in result.paths] == [
        (("a", "c"), ("a", "c", "t")),
        (("z", "b"), ("a", "b", "t")),
    ]
    assert result.scope_complete and result.graph_exhausted
    assert result.next_unreturned_path is None
    assert len(result.nodes) == 4 and len(result.relationships) == 4
    assert result.epistemic_status == "deterministic_derived"


def test_paths_cycle_fails_explicitly(accepted_state: AppState) -> None:
    """A directed cycle reaching the target fails instead of silently missing paths."""
    graph = Topology(
        accepted_state,
        builds(
            [
                ("a", "a", "b"),
                ("b", "b", "c"),
                ("c", "c", "a"),
                ("d", "c", "t"),
                ("z", "a", "t"),
            ]
        ),
    )
    with pytest.raises(PackageValidationError) as failure:
        graph.paths()
    assert failure.value.details == {"target_node_id": "t", "unsettled_node_count": 3}
    assert "directed cycle" in failure.value.message


def test_paths_empty_is_success(accepted_state: AppState) -> None:
    """A reverse connection is a complete empty search, not a missing record."""
    result = Topology(accepted_state, builds([("a", "t", "a")])).paths()
    assert result.paths == () and result.relationships == ()
    assert result.scope_complete and result.graph_exhausted


def test_paths_identical_endpoints_rejected(accepted_state: AppState) -> None:
    """Reject equal resolved endpoints instead of inventing a zero-hop path."""
    with pytest.raises(InvalidProgressionRequestError):
        Topology(accepted_state, builds(DIAMOND)).paths(target="a")


def test_paths_depth_boundary(accepted_state: AppState) -> None:
    """Depth-only exclusion is complete within depth but not globally exhausted."""
    result = Topology(accepted_state, builds(DIAMOND + [("y", "a", "t")])).paths(
        max_depth=1
    )
    assert [p.relationship_ids for p in result.paths] == [("y",)]
    assert result.scope_complete and not result.graph_exhausted
    assert result.truncation_reasons == ("depth_limit",)
    # Edges a and z reach the target only in more hops than remain.
    assert result.frontier.depth_limited_extension_count == 2
    assert result.counters.depth_frontier_examined_relationship_count == 2


def test_paths_count_boundary(accepted_state: AppState) -> None:
    """Stop after one complete path while exposing the unexplored alternatives."""
    result = Topology(accepted_state, builds(DIAMOND)).paths(max_paths=1)
    assert [p.relationship_ids for p in result.paths] == [("a", "c")]
    assert result.truncation_reasons == ("path_limit",)
    assert not result.scope_complete and result.frontier.queued_state_count > 0
    assert result.next_unreturned_path is None


def test_paths_work_boundary(accepted_state: AppState) -> None:
    """The backward pass from the target consumes the fixed inspection budget."""
    result = Topology(
        accepted_state,
        builds([("a", "a", "t")] + [(f"z{i:05}", f"p{i}", "t") for i in range(5001)]),
    ).paths()
    assert result.counters.examined_relationship_count == 5000
    assert result.counters.enqueued_state_count == 1
    assert result.frontier.pending_adjacency_count == 2
    assert result.truncation_reasons == ("work_limit",)
    assert not result.paths and result.next_unreturned_path is None
    assert not result.scope_complete and not result.graph_exhausted


def test_paths_cumulative_state_accounting(accepted_state: AppState) -> None:
    """Count the start and every created partial path; a finished search holds none.

    Every partial path the exact-length search creates completes a path, so with at
    most 20 paths the 5,000-state ceiling is a bound rather than a reachable stop.
    """
    result = Topology(accepted_state, builds(DIAMOND)).paths()
    # Start, a->c, a->c->t, a->b, a->b->t; four backward and four forward inspections.
    assert result.counters.enqueued_state_count == 5
    assert result.counters.peak_queue_state_count == 2
    assert result.counters.examined_relationship_count == 8
    assert result.frontier.queued_state_count == 0
    assert result.frontier.pending_adjacency_count == 0
    assert not result.truncation_reasons and result.graph_exhausted


def test_paths_oversized_first_path_returns_ids(accepted_state: AppState) -> None:
    """An unreturnable first path is a normal IDs-only result, not an error."""
    graph = Topology(accepted_state, builds([("a", "a", "t")], "x" * 1048577))
    result = graph.paths()
    assert result.paths == () and result.relationships == ()
    assert result.shared_relationship_evidence.model_dump(exclude_none=True) == {}
    assert [n.node_id for n in result.nodes] == ["a", "t"]
    unreturned = result.next_unreturned_path
    assert unreturned is not None
    assert (unreturned.node_ids, unreturned.relationship_ids) == (("a", "t"), ("a",))
    assert result.truncation_reasons == ("byte_limit",)
    assert not result.scope_complete and not result.graph_exhausted
    assert graph.require_paths_result_size(result=result) <= 1048576
    assert_envelope_bounds(result)


def test_paths_combination_only_bytes(accepted_state: AppState) -> None:
    """Roll back the whole second alternative, name it, and drop its evidence."""
    pairs = [("a", "a", "b"), ("b", "b", "t"), ("c", "a", "c"), ("d", "c", "t")]
    # A per-edge attribution stays in every entry, so only the combination is large.
    text = "😀" * 15000
    for branch in (pairs[:2], pairs[2:]):
        control = Topology(accepted_state, per_edge(branch, text)).paths()
        assert control.scope_complete and control.graph_exhausted
        assert not control.truncation_reasons
        assert [p.relationship_ids for p in control.paths] == [
            tuple(pair[0] for pair in branch)
        ]
        assert_envelope_bounds(control)
    graph = Topology(accepted_state, per_edge(pairs, text))
    result = graph.paths()
    assert [p.relationship_ids for p in result.paths] == [("a", "b")]
    assert {n.node_id for n in result.nodes} == {"a", "b", "t"}
    assert {e.relationship.relationship_id for e in result.relationships} == {"a", "b"}
    assert all(
        e.relationship == graph.edges[e.relationship.relationship_id]
        for e in rehydrated(result)
    )
    assert result.truncation_reasons == ("byte_limit",)
    # Four backward inspections from the target, then a, b, c and d forward.
    assert result.counters.examined_relationship_count == 8
    assert result.counters.returned_path_count == 1
    assert not result.scope_complete and not result.graph_exhausted
    assert result.frontier.queued_state_count > 0
    unreturned = result.next_unreturned_path
    assert unreturned is not None
    assert (unreturned.node_ids, unreturned.relationship_ids) == (
        ("a", "c", "t"),
        ("c", "d"),
    )
    assert graph.require_paths_result_size(result=result) <= 1048576
    assert_envelope_bounds(result)


def test_paths_later_oversized_alternative_is_partial(accepted_state: AppState) -> None:
    """A later path too large even alone stops selection without failing earlier ones."""
    large = builds([("c", "a", "c")], "x" * 1048577)
    # Positive control: the later alternative alone is an unreturnable first path.
    alone = Topology(accepted_state, builds([("d", "c", "t")]) + large).paths()
    assert alone.paths == () and alone.truncation_reasons == ("byte_limit",)
    assert alone.next_unreturned_path is not None
    assert alone.next_unreturned_path.relationship_ids == ("c", "d")
    graph = Topology(
        accepted_state,
        builds([("a", "a", "b"), ("b", "b", "t"), ("d", "c", "t")]) + large,
    )
    result = graph.paths()
    assert [p.relationship_ids for p in result.paths] == [("a", "b")]
    unreturned = result.next_unreturned_path
    assert unreturned is not None
    assert (unreturned.node_ids, unreturned.relationship_ids) == (
        ("a", "c", "t"),
        ("c", "d"),
    )
    assert {e.relationship.relationship_id for e in result.relationships} == {"a", "b"}
    assert {n.node_id for n in result.nodes} == {"a", "b", "t"}
    assert result.truncation_reasons == ("byte_limit",)
    assert not result.scope_complete and not result.graph_exhausted
    assert result.frontier.queued_state_count > 0
    assert_envelope_bounds(result)


def test_paths_unlifted_field_rolls_back_later_path(accepted_state: AppState) -> None:
    """A later path whose evidence un-lifts a large shared field is rolled back whole."""
    text = "😀" * 20000
    pairs = [("a", "a", "b"), ("b", "b", "t"), ("c", "a", "c"), ("d", "c", "t")]
    # Positive control: one attribution shared by all four edges lifts once and fits.
    control = Topology(accepted_state, builds(pairs, text)).paths()
    assert [p.relationship_ids for p in control.paths] == [("a", "b"), ("c", "d")]
    assert control.shared_relationship_evidence.relationship is not None
    assert control.shared_relationship_evidence.relationship.attribution_statement == (
        text
    )
    assert not control.truncation_reasons
    assert_envelope_bounds(control)
    # A different attribution on the second path would repeat the text in every entry.
    graph = Topology(accepted_state, builds(pairs[:2], text) + builds(pairs[2:]))
    result = graph.paths()
    assert [p.relationship_ids for p in result.paths] == [("a", "b")]
    assert result.shared_relationship_evidence.relationship is not None
    assert result.shared_relationship_evidence.relationship.attribution_statement == (
        text
    )
    assert all(
        e.relationship.attribution_statement is None for e in result.relationships
    )
    unreturned = result.next_unreturned_path
    assert unreturned is not None and unreturned.relationship_ids == ("c", "d")
    assert result.truncation_reasons == ("byte_limit",)
    assert_envelope_bounds(result)


def test_paths_match_baseline_enumerator(accepted_state: AppState) -> None:
    """Wherever the baseline enumerator is complete, the same paths come back in order.

    A deterministic sample covers connected and unconnected pairs on all seven packages
    with ``max_depth`` cycling 1-12 and ``max_paths`` cycling 1-20. The reference copy
    does not model output-size stops, so a result that stops on ``byte_limit`` must
    hold a prefix of the reference paths and name the next one.
    """
    service = accepted_state.learning_progressions_service
    compared = with_paths = 0
    for runtime in accepted_state.catalog_load_result.package_runtimes:
        downstream: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for edge in sorted(
            runtime.loaded_package.relationships, key=lambda e: e.relationship_id
        ):
            if edge.label == "buildsTowards":
                downstream[edge.source_node_id].append(
                    (edge.relationship_id, edge.target_node_id)
                )
        nodes = sorted({n for e in downstream.values() for _, n in e} | set(downstream))
        requests = []
        for source in sorted(downstream)[::5][:15]:
            reachable = {source}
            frontier = [source]
            while frontier:
                heads = {h for n in frontier for _, h in downstream.get(n, [])}
                frontier = sorted(heads - reachable)
                reachable |= heads
            connected = sorted(reachable - {source})
            # Up to five spread connected targets plus one unconnected target.
            requests += [(source, t) for t in connected[:: len(connected) // 5 + 1]]
            requests += [(source, t) for t in nodes if t not in reachable][:1]
        for index, (source, target) in enumerate(requests):
            request = path_request(
                runtime,
                source,
                target,
                max_depth=index % 12 + 1,
                max_paths=index % 20 + 1,
            )
            result = service.get_learning_progression_paths(request=request)
            assert_path_invariants(
                request=request, result=result, runtime=runtime, service=service
            )
            expected, reasons = baseline_paths(
                downstream=downstream,
                max_depth=request.max_depth,
                max_paths=request.max_paths,
                source=source,
                target=target,
            )
            if reasons:
                continue
            found = [(p.relationship_ids, p.node_ids) for p in result.paths]
            if result.truncation_reasons:
                # A kept last path or a rolled-back named one; either way a prefix.
                assert result.truncation_reasons == ("byte_limit",)
                unreturned = result.next_unreturned_path
                if unreturned is None:
                    assert len(found) < len(expected)
                else:
                    found.append((unreturned.relationship_ids, unreturned.node_ids))
                assert found == expected[: len(found)]
            else:
                assert found == expected
            compared += 1
            with_paths += bool(expected)
    # Deterministic sample size: 296 complete reference results, 210 with paths.
    assert compared >= 250 and with_paths >= 150


def test_paths_caps_long_connections_return_shortest(
    accepted_state: AppState,
) -> None:
    """Pinned CAPS pairs of 1 to 12 hops return their complete shortest path first."""
    runtime = caps_runtime(accepted_state)
    service = accepted_state.learning_progressions_service
    for hops, source, target in CAPS_PAIRS:
        for max_depth in (hops, 16):
            request = path_request(runtime, source, target, max_depth=max_depth)
            result = service.get_learning_progression_paths(request=request)
            assert result.paths and len(result.paths[0].relationship_ids) == hops
            assert not {"work_limit", "queue_limit"} & set(result.truncation_reasons)
            assert_path_invariants(
                request=request, result=result, runtime=runtime, service=service
            )
            assert_envelope_bounds(result)


def test_paths_caps_thirteen_hops_identified_by_ids(accepted_state: AppState) -> None:
    """A CAPS 13-hop shortest path too large even compacted is named by its IDs."""
    runtime = caps_runtime(accepted_state)
    service = accepted_state.learning_progressions_service
    source, target = CAPS_THIRTEEN_HOP
    for max_depth in (13, 16):
        request = path_request(runtime, source, target, max_depth=max_depth)
        result = service.get_learning_progression_paths(request=request)
        assert result.paths == () and result.relationships == ()
        assert result.shared_relationship_evidence.model_dump(exclude_none=True) == {}
        assert [n.node_id for n in result.nodes] == [source, target]
        unreturned = result.next_unreturned_path
        assert unreturned is not None and len(unreturned.relationship_ids) == 13
        assert "byte_limit" in result.truncation_reasons
        assert not {"work_limit", "queue_limit"} & set(result.truncation_reasons)
        assert_path_invariants(
            request=request, result=result, runtime=runtime, service=service
        )
        assert_envelope_bounds(result)


def test_paths_every_real_shortest_connection_fits(accepted_state: AppState) -> None:
    """Each connected original-package pair returns its complete shortest path."""
    service = accepted_state.learning_progressions_service
    lengths: dict[int, int] = defaultdict(int)
    # CAPS is excluded by design (too slow exhaustively); it has a pinned sample.
    originals = [
        runtime
        for runtime in accepted_state.catalog_load_result.package_runtimes
        if runtime.catalog_package.package_identity.framework_id != CAPS
    ]
    assert len(originals) == ORIGINAL_FRAMEWORKS
    for runtime in originals:
        identity = runtime.catalog_package.package_identity
        downstream: dict[str, list[str]] = defaultdict(list)
        for edge in runtime.loaded_package.relationships:
            if edge.label == "buildsTowards":
                downstream[edge.source_node_id].append(edge.target_node_id)
        # Independent BFS oracle over original accepted edges, not service adjacency.
        for source in sorted(downstream):
            distance = {source: 0}
            queue = deque([source])
            while queue:
                node = queue.popleft()
                for following in downstream[node]:
                    if following not in distance:
                        distance[following] = distance[node] + 1
                        queue.append(following)
            for target, hops in sorted(distance.items()):
                if not hops:
                    continue
                result = service.get_learning_progression_paths(
                    request=GetLearningProgressionPathsRequest(
                        framework_id=identity.framework_id,
                        snapshot_id=identity.snapshot_id,
                        source_identifier=selector(source),
                        target_identifier=selector(target),
                        max_depth=hops,
                        max_paths=1,
                    )
                )
                assert len(result.paths) == 1
                path = result.paths[0]
                assert len(path.relationship_ids) == hops
                assert (path.node_ids[0], path.node_ids[-1]) == (source, target)
                assert {
                    e.relationship.relationship_id for e in result.relationships
                } == set(path.relationship_ids)
                assert_envelope_bounds(result)
                lengths[hops] += 1
    # Accepted packages are immutable: 6522 connected pairs, longest shortest path 8.
    assert sum(lengths.values()) == 6522 and max(lengths) == 8
