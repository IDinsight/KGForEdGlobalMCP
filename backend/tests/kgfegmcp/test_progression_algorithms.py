"""Independent bounded traversal and directed simple-path acceptance scenarios."""

# Third Party Library
import pytest

# Package Library
from kgfegmcp.errors import (
    InvalidProgressionRequestError,
    ProgressionResultTooLargeError,
)
from tests.fixtures.progression_fixtures import Topology, assert_envelope_bounds, builds

DIAMOND = [("z", "a", "b"), ("a", "a", "c"), ("b", "b", "t"), ("c", "c", "t")]


def test_traversal_keeps_merging_edges() -> None:
    """Keep both branches in ID-sorted BFS order, excluding other labels."""
    graph = Topology(
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


def test_traversal_keeps_cycle_closure() -> None:
    """Terminate a cycle and retain the closing edge at the depth frontier."""
    result = Topology(builds([("a", "a", "b"), ("b", "b", "c"), ("c", "c", "a")])).walk(
        max_depth=2
    )
    assert len(result.relationships) == 3
    assert result.graph_exhausted and result.scope_complete
    assert result.counters.depth_frontier_examined_relationship_count == 1


@pytest.mark.parametrize(
    "limit,reason,count",
    [("max_nodes", "node_limit", 2), ("max_edges", "edge_limit", 1)],
)
def test_traversal_finite_table_limits(limit: str, reason: str, count: int) -> None:
    """Stop before allocating an excess node or edge and retain a frontier."""
    result = Topology(builds(DIAMOND)).walk(**{limit: count})
    assert result.truncation_reasons == (reason,)
    assert not result.scope_complete and not result.graph_exhausted and result.frontier
    assert (
        len(result.nodes) if limit == "max_nodes" else len(result.relationships)
    ) == count


def test_traversal_depth_frontier_consumes_work() -> None:
    """Count excluded depth edges in the actual fixed examination budget."""
    pairs = [("a", "a", "b")] + [(f"z{i:05}", "b", "c") for i in range(5001)]
    result = Topology(builds(pairs)).walk(max_depth=1)
    assert result.counters.examined_relationship_count == 5000
    assert result.counters.depth_frontier_examined_relationship_count == 4999
    assert result.truncation_reasons == ("depth_limit", "work_limit")
    assert not result.scope_complete and result.frontier


def test_traversal_combination_only_bytes() -> None:
    """Omit the whole fitting second entry when only the combination is large."""
    pairs = [("a", "a", "b"), ("b", "a", "c")]
    text = "😀" * 24000
    for pair in pairs:
        control = Topology(builds([pair], text)).walk()
        assert control.scope_complete and control.graph_exhausted
        assert not control.truncation_reasons
        assert [e.relationship.relationship_id for e in control.relationships] == [
            pair[0]
        ]
        assert_envelope_bounds(control)
    graph = Topology(builds(pairs, text))
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


def test_paths_preserve_alternative_merges() -> None:
    """Retain alternatives sharing a target, sorted by hop count then ID tuple."""
    graph = Topology(builds(DIAMOND))
    result = graph.paths()
    assert [(p.relationship_ids, p.node_ids) for p in result.paths] == [
        (("a", "c"), ("a", "c", "t")),
        (("z", "b"), ("a", "b", "t")),
    ]
    assert result.scope_complete and result.graph_exhausted
    assert result.next_unreturned_path is None
    assert len(result.nodes) == 4 and len(result.relationships) == 4
    assert result.epistemic_status == "deterministic_derived"


def test_paths_cycle_is_per_path() -> None:
    """Exclude repeated nodes without losing valid alternative prefixes."""
    result = Topology(
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


def test_paths_empty_is_success() -> None:
    """A reverse connection is a complete empty search, not a missing record."""
    result = Topology(builds([("a", "t", "a")])).paths()
    assert result.paths == () and result.relationships == ()
    assert result.scope_complete and result.graph_exhausted


def test_paths_identical_endpoints_rejected() -> None:
    """Reject equal resolved endpoints instead of inventing a zero-hop path."""
    with pytest.raises(InvalidProgressionRequestError):
        Topology(builds(DIAMOND)).paths(target="a")


def test_paths_depth_boundary() -> None:
    """Depth-only exclusion is complete within depth but not globally exhausted."""
    result = Topology(builds(DIAMOND)).paths(max_depth=1)
    assert not result.paths and result.scope_complete and not result.graph_exhausted
    assert result.truncation_reasons == ("depth_limit",)
    assert result.frontier.depth_limited_extension_count == 2


def test_paths_count_boundary() -> None:
    """Stop after one complete path while exposing the unexplored alternatives."""
    result = Topology(builds(DIAMOND)).paths(max_paths=1)
    assert [p.relationship_ids for p in result.paths] == [("a", "c")]
    assert result.truncation_reasons == ("path_limit",)
    assert not result.scope_complete and result.frontier.queued_state_count > 0
    assert result.next_unreturned_path is None


def test_paths_work_boundary() -> None:
    """Excluded depth extensions consume bounded work without queue growth."""
    result = Topology(
        builds([("a", "a", "b")] + [(f"z{i:05}", "b", "x") for i in range(5001)]),
    ).paths(max_depth=1)
    assert result.counters.examined_relationship_count == 5000
    assert result.counters.depth_frontier_examined_relationship_count == 4999
    assert result.counters.enqueued_state_count == 2
    assert result.truncation_reasons == ("depth_limit", "work_limit")
    assert not result.scope_complete


def test_paths_cumulative_queue_boundary() -> None:
    """Bound cumulative admission including the start, not only current queue size."""
    result = Topology(builds([(f"e{i:05}", "a", f"n{i}") for i in range(5001)])).paths()
    assert result.counters.enqueued_state_count == 5000
    assert result.counters.examined_relationship_count == 5000
    assert result.truncation_reasons == ("queue_limit",)
    assert not result.scope_complete and not result.graph_exhausted


def test_paths_oversized_entry_rejected() -> None:
    """An unreturnable first path fails and names its ordered relationship IDs."""
    with pytest.raises(ProgressionResultTooLargeError) as failure:
        Topology(builds([("a", "a", "t")], "x" * 1048577)).paths()
    assert failure.value.details["relationship_ids"] == ("a",)
    hint = failure.value.recovery_hint
    assert hint is not None
    assert '["a"]' in hint and "get_learning_progression" in hint
    assert "resource" in hint.lower()


def test_paths_combination_only_bytes() -> None:
    """Roll back the whole second alternative, name it, and drop its evidence."""
    pairs = [("a", "a", "b"), ("b", "b", "t"), ("c", "a", "c"), ("d", "c", "t")]
    text = "😀" * 10000
    for branch in (pairs[:2], pairs[2:]):
        control = Topology(builds(branch, text)).paths()
        assert control.scope_complete and control.graph_exhausted
        assert not control.truncation_reasons
        assert [p.relationship_ids for p in control.paths] == [
            tuple(pair[0] for pair in branch)
        ]
        assert_envelope_bounds(control)
    graph = Topology(builds(pairs, text))
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


def test_paths_later_oversized_alternative_is_partial() -> None:
    """A later path too large even alone stops selection without failing earlier ones."""
    large = builds([("c", "a", "c")], "x" * 1048577)
    # Positive control: the later alternative alone is an unreturnable first path.
    with pytest.raises(ProgressionResultTooLargeError) as failure:
        Topology(builds([("d", "c", "t")]) + large).paths()
    assert failure.value.details["relationship_ids"] == ("c", "d")
    graph = Topology(
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
