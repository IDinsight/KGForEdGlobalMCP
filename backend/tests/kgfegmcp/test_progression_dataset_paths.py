"""Acceptance checks requiring the complete six-package LP dataset."""

# Standard Library
from collections import defaultdict, deque

# Third Party Library
import pytest

# Package Library
from kgfegmcp.bootstrap import AppState
from kgfegmcp.services.lp_models import GetLearningProgressionPathsRequest
from tests.fixtures.progression_fixtures import assert_envelope_bounds, selector


@pytest.mark.lp_dataset
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
