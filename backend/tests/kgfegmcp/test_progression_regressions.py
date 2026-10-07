"""Reused established AS/LC preservation checks, independently executed by Tester."""

# Standard Library
import json

from collections import Counter
from pathlib import Path

# Package Library
from kgfegmcp.bootstrap import AppState
from kgfegmcp.services.comparison_models import TextFrameworkComparisonRequest
from kgfegmcp.services.models import (
    GetFrameworkStatisticsRequest,
    GetLearningComponentContextRequest,
    GetLearningComponentRequest,
    GetLearningComponentsForStandardRequest,
    GetStandardContextRequest,
    GetStandardRequest,
    TextLearningComponentsSearchRequest,
    TextStandardsSearchRequest,
)
from kgfegmcp.services.statistics import FrameworkStatisticsService
from tests.fixtures.progression_fixtures import selector, semantic_baseline


def test_six_package_standards_components_preserved(accepted_state: AppState) -> None:
    """Repeat unchanged DEV-017 preservation assertions against current packages."""
    baseline = json.loads(
        (
            Path(__file__).resolve().parents[1] / "fixtures/progression_baseline.json"
        ).read_text()
    )
    standards = accepted_state.comparison_service.standards_service
    components = accepted_state.resource_service.learning_component_service
    for runtime in accepted_state.catalog_load_result.package_runtimes:
        identity = runtime.catalog_package.package_identity
        args = dict(
            framework_id=identity.framework_id, snapshot_id=identity.snapshot_id
        )
        build = next(
            e
            for e in runtime.loaded_package.relationships
            if e.label == "buildsTowards"
        )
        selected = selector(build.source_node_id)
        standard = standards.get_standard(
            GetStandardRequest(identifier=selected, **args)
        )
        context = standards.get_standard_context(
            GetStandardContextRequest(node_id=build.source_node_id, **args)
        )
        assert standard.node is runtime.graph_store.nodes_by_id[build.source_node_id]
        assert all(
            e.relationship_type == "hasChild" for e in context.ancestors.relationships
        )
        supports = components.get_learning_components_for_standard(
            GetLearningComponentsForStandardRequest(identifier=selected, **args)
        )
        assert all(
            c.relationship.label == "supports"
            and c.relationship.target_node_id == build.source_node_id
            for c in supports.components
        )
        component = runtime.loaded_package.learning_component_nodes[0]
        assert (
            components.get_learning_component(
                GetLearningComponentRequest(node_id=component.node_id, **args)
            ).node
            is component
        )
        assert (
            components.get_learning_component_context(
                GetLearningComponentContextRequest(node_id=component.node_id, **args)
            )
            is not None
        )
        labels = Counter(e.label for e in runtime.loaded_package.relationships)
        stats = (
            FrameworkStatisticsService(
                catalog_service=accepted_state.catalog_service,
                search_service=accepted_state.search_service,
            )
            .get_framework_statistics(GetFrameworkStatisticsRequest(**args))
            .statistics
        )
        assert stats.total_relationships == labels["hasChild"]
        assert (
            stats.learning_components.total_supports_relationships == labels["supports"]
        )
        assert (
            stats.learning_progressions.builds_towards_relationships
            == labels["buildsTowards"]
        )
        assert (
            stats.learning_progressions.relates_to_relationships == labels["relatesTo"]
        )
        assert all(
            row.value == "hasChild" for row in stats.canonical_relationship_label_counts
        )
        # Meaning, not bytes: identity/text and hierarchy/support edges equal the
        # pre-change package; repackaging or appended LP edges do not matter.
        old = baseline[str(identity.framework_id)]
        nodes, edges = runtime.loaded_package.artifact(
            "nodes"
        ), runtime.loaded_package.artifact("relationships")
        assert nodes and edges
        current = semantic_baseline(
            [
                json.loads(line)
                for line in nodes.resolved_path.read_text().splitlines()
                if line
            ],
            [
                json.loads(line)
                for line in edges.resolved_path.read_text().splitlines()
                if line
            ],
        )
        assert current == {
            key: value for key, value in old.items() if key != "originalSnapshotId"
        }
        assert (
            standards.search_standards(
                TextStandardsSearchRequest(
                    mode="text",
                    match={"matchMode": "tokens", "operator": "any"},
                    query="a",
                    framework_ids=(identity.framework_id,),
                    limit=2,
                )
            )
            is not None
        )
        assert (
            components.search_learning_components(
                TextLearningComponentsSearchRequest(
                    mode="learning_component_text",
                    match={"matchMode": "tokens", "operator": "any"},
                    query="a",
                    framework_ids=(identity.framework_id,),
                    limit=2,
                )
            )
            is not None
        )


def test_existing_comparison_is_usable(accepted_state: AppState) -> None:
    """Repeat the unchanged cross-framework comparison regression through its service."""
    request = TextFrameworkComparisonRequest(
        framework_ids=tuple(
            r.catalog_package.package_identity.framework_id
            for r in accepted_state.catalog_load_result.package_runtimes[:2]
        ),
        mode="text",
        match={"matchMode": "tokens", "operator": "any"},
        query="number",
        max_matches_per_framework=2,
    )
    assert (
        accepted_state.comparison_service.compare_framework_evidence(request)
        is not None
    )
