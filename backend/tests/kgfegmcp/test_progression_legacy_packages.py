"""LP API behavior on real packages that have not yet received the LP migration."""

# Third Party Library
import pytest

# Package Library
from kgfegmcp.bootstrap import AppState
from kgfegmcp.domain.enums import GraphType
from kgfegmcp.errors import CapabilityUnavailableError
from kgfegmcp.services.lp_models import (
    GetLearningProgressionPathsRequest,
    GetLearningProgressionRequest,
    GetStandardProgressionsRequest,
    SearchLearningProgressionsRequest,
    TraverseLearningProgressionsRequest,
)
from tests.fixtures.progression_fixtures import package_route, selector


def test_legacy_packages_report_lp_unavailable(accepted_state: AppState) -> None:
    """All five LP queries refuse undeclared LPs while legacy packages stay accepted."""
    runtimes = [
        runtime
        for runtime in accepted_state.catalog_load_result.package_runtimes
        if GraphType.LEARNING_PROGRESSIONS
        not in runtime.loaded_package.manifest.included_graph_types
    ]
    if not runtimes:
        pytest.skip("All installed packages have migrated to stored LPs.")
    service = accepted_state.learning_progressions_service
    for runtime in runtimes:
        package = runtime.catalog_package
        assert not package.capabilities.has_learning_progressions
        assert not package.capabilities.has_learning_progression_provenance
        assert package.counts.builds_towards_relationships == 0
        assert package.counts.relates_to_relationships == 0
        assert runtime.loaded_package.learning_progression_evidence is None
        route = package_route(runtime)
        source, target = runtime.loaded_package.item_nodes[:2]
        requests = {
            "get_learning_progression": GetLearningProgressionRequest(
                **route, relationship_id="absent-lp-edge"
            ),
            "get_standard_progressions": GetStandardProgressionsRequest(
                **route, identifier=selector(source.node_id)
            ),
            "search_learning_progressions": SearchLearningProgressionsRequest(**route),
            "traverse_learning_progressions": TraverseLearningProgressionsRequest(
                **route, identifier=selector(source.node_id)
            ),
            "get_learning_progression_paths": GetLearningProgressionPathsRequest(
                **route,
                source_identifier=selector(source.node_id),
                target_identifier=selector(target.node_id),
            ),
        }
        for operation, request in requests.items():
            with pytest.raises(CapabilityUnavailableError) as failure:
                getattr(service, operation)(request=request)
            assert failure.value.error_code == "capability_unavailable"
