"""Independent bounded traversal and directed simple-path acceptance scenarios."""

# Standard Library
import json

from collections import defaultdict, deque
from typing import Any

# Third Party Library
import pytest

# Package Library
from kgfegmcp.bootstrap import AppState
from kgfegmcp.errors import (
    InvalidProgressionRequestError,
    ProgressionResultTooLargeError,
)
from kgfegmcp.services.learning_progressions import progression_result_text
from kgfegmcp.services.lp_models import GetLearningProgressionPathsRequest
from tests.fixtures.progression_fixtures import Topology, builds, selector

DIAMOND = [("z", "a", "b"), ("a", "a", "c"), ("b", "b", "t"), ("c", "c", "t")]


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
        e.relationship is graph.edges[e.relationship.relationship_id]
        for e in result.relationships
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
    text = "😀" * 20000
    for pair in pairs:
        control = Topology(accepted_state, builds([pair], text)).walk()
        assert control.scope_complete and control.graph_exhausted
        assert not control.truncation_reasons
        assert [e.relationship.relationship_id for e in control.relationships] == [
            pair[0]
        ]
        assert_envelope_bounds(control)
    graph = Topology(accepted_state, builds(pairs, text))
    result = graph.walk()
    assert result.truncation_reasons == ("byte_limit",)
    assert [e.relationship.relationship_id for e in result.relationships] == ["a"]
    assert result.relationships[0].relationship is graph.edges["a"]
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


def test_paths_cycle_is_per_path(accepted_state: AppState) -> None:
    """Exclude repeated nodes without losing valid alternative prefixes."""
    result = Topology(
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
    ).paths()
    assert [p.relationship_ids for p in result.paths] == [("z",), ("a", "b", "d")]
    assert all(len(p.node_ids) == len(set(p.node_ids)) for p in result.paths)
    assert result.graph_exhausted


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
    result = Topology(accepted_state, builds(DIAMOND)).paths(max_depth=1)
    assert not result.paths and result.scope_complete and not result.graph_exhausted
    assert result.truncation_reasons == ("depth_limit",)
    assert result.frontier.depth_limited_extension_count == 2


def test_paths_count_boundary(accepted_state: AppState) -> None:
    """Stop after one complete path while exposing the unexplored alternatives."""
    result = Topology(accepted_state, builds(DIAMOND)).paths(max_paths=1)
    assert [p.relationship_ids for p in result.paths] == [("a", "c")]
    assert result.truncation_reasons == ("path_limit",)
    assert not result.scope_complete and result.frontier.queued_state_count > 0
    assert result.next_unreturned_path is None


def test_paths_work_boundary(accepted_state: AppState) -> None:
    """Excluded depth extensions consume bounded work without queue growth."""
    result = Topology(
        accepted_state,
        builds([("a", "a", "b")] + [(f"z{i:05}", "b", "x") for i in range(5001)]),
    ).paths(max_depth=1)
    assert result.counters.examined_relationship_count == 5000
    assert result.counters.depth_frontier_examined_relationship_count == 4999
    assert result.counters.enqueued_state_count == 2
    assert result.truncation_reasons == ("depth_limit", "work_limit")
    assert not result.scope_complete


def test_paths_cumulative_queue_boundary(accepted_state: AppState) -> None:
    """Bound cumulative admission including the start, not only current queue size."""
    result = Topology(
        accepted_state, builds([(f"e{i:05}", "a", f"n{i}") for i in range(5001)])
    ).paths()
    assert result.counters.enqueued_state_count == 5000
    assert result.counters.examined_relationship_count == 5000
    assert result.truncation_reasons == ("queue_limit",)
    assert not result.scope_complete and not result.graph_exhausted


def test_paths_oversized_entry_rejected(accepted_state: AppState) -> None:
    """An unreturnable first path fails and names its ordered relationship IDs."""
    with pytest.raises(ProgressionResultTooLargeError) as failure:
        Topology(accepted_state, builds([("a", "a", "t")], "x" * 1048577)).paths()
    assert failure.value.details["relationship_ids"] == ("a",)
    hint = failure.value.recovery_hint
    assert '["a"]' in hint and "get_learning_progression" in hint
    assert "resource" in hint.lower()


def test_paths_combination_only_bytes(accepted_state: AppState) -> None:
    """Roll back the whole second alternative, name it, and drop its evidence."""
    pairs = [("a", "a", "b"), ("b", "b", "t"), ("c", "a", "c"), ("d", "c", "t")]
    text = "😀" * 10000
    for branch in (pairs[:2], pairs[2:]):
        control = Topology(accepted_state, builds(branch, text)).paths()
        assert control.scope_complete and control.graph_exhausted
        assert not control.truncation_reasons
        assert [p.relationship_ids for p in control.paths] == [
            tuple(pair[0] for pair in branch)
        ]
        assert_envelope_bounds(control)
    graph = Topology(accepted_state, builds(pairs, text))
    result = graph.paths()
    assert [p.relationship_ids for p in result.paths] == [("a", "b")]
    assert {n.node_id for n in result.nodes} == {"a", "b", "t"}
    assert {e.relationship.relationship_id for e in result.relationships} == {"a", "b"}
    assert all(
        e.relationship is graph.edges[e.relationship.relationship_id]
        for e in result.relationships
    )
    assert result.truncation_reasons == ("byte_limit",)
    assert result.counters.examined_relationship_count == 4
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
    with pytest.raises(ProgressionResultTooLargeError) as failure:
        Topology(accepted_state, builds([("d", "c", "t")]) + large).paths()
    assert failure.value.details["relationship_ids"] == ("c", "d")
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


def test_paths_every_real_shortest_connection_fits(accepted_state: AppState) -> None:
    """Each connected stored pair returns its complete shortest path in one result."""
    service = accepted_state.learning_progressions_service
    lengths: dict[int, int] = defaultdict(int)
    for runtime in accepted_state.catalog_load_result.package_runtimes:
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
