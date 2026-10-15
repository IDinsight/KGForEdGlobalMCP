"""Compact shared-place LP results: lifting, rehydration and published schemas."""

# Standard Library
import hashlib
import json

from typing import Any

# Third Party Library
import pytest

from fastmcp import Client

# Package Library
from kgfegmcp.app import create_mcp
from kgfegmcp.bootstrap import AppState
from kgfegmcp.catalog.models import CatalogPackageRuntime
from kgfegmcp.services.lp_compact import compact_relationships, rehydrate_relationships
from kgfegmcp.services.lp_models import (
    GetStandardProgressionsRequest,
    SearchLearningProgressionsRequest,
    TraverseLearningProgressionsRequest,
)
from tests.fixtures.progression_fixtures import (
    assert_compact_form,
    rehydrated,
    selector,
)

# SHA-256 of get_learning_progression's published input schema, output schema and
# description at the cycle baseline f9fdaa2; that tool keeps its full form.
EXACT_LOOKUP_SCHEMA_SHA256 = (
    "8692c83b1d99bf62fe065649d851596840681fe07119e4124dde1c6c7f442d96"
)


def _expected(result: Any, runtime: CatalogPackageRuntime, state: AppState) -> Any:
    """Build the full evidence each entry of a compact result must encode.

    Parameters
    ----------
    result
        Compact progression result.
    runtime
        Accepted package runtime the result came from.
    state
        Application state holding the production service.

    Returns
    -------
    tuple[ProgressionRelationshipEvidence, ...]
        ``relationship_evidence`` for each entry's stored edge, in result order.
    """

    stored = runtime.graph_store.relationships_by_id
    return tuple(
        state.learning_progressions_service.relationship_evidence(
            relationship=stored[entry.relationship.relationship_id], runtime=runtime
        )
        for entry in result.relationships
    )


def test_compact_collection_and_traversal_results(accepted_state: AppState) -> None:
    """Standard progressions, LP search and traversal lift shared evidence losslessly.

    On every package, each result follows the lifting rule and rehydrates to exactly
    the evidence ``relationship_evidence`` builds. The sample includes a mixed
    buildsTowards/relatesTo page, where labels stay per entry, and an empty result,
    whose shared object is ``{}``.
    """
    service = accepted_state.learning_progressions_service
    mixed = empty = 0
    for runtime in accepted_state.catalog_load_result.package_runtimes:
        identity = runtime.catalog_package.package_identity
        route = {
            "framework_id": identity.framework_id,
            "snapshot_id": identity.snapshot_id,
        }
        edges = sorted(
            runtime.loaded_package.relationships, key=lambda e: e.relationship_id
        )
        builds = {e.source_node_id for e in edges if e.label == "buildsTowards"}
        related = {
            n
            for e in edges
            if e.label == "relatesTo"
            for n in (e.source_node_id, e.target_node_id)
        }
        incoming = {e.target_node_id for e in edges if e.label == "buildsTowards"}
        both = sorted(builds & related)[0]
        root = sorted(builds - incoming)[0]
        results = [
            service.get_standard_progressions(
                request=GetStandardProgressionsRequest(
                    **route, identifier=selector(both), limit=100
                )
            ),
            service.search_learning_progressions(
                request=SearchLearningProgressionsRequest(**route, limit=10)
            ),
            service.search_learning_progressions(
                request=SearchLearningProgressionsRequest(
                    **route, standard_identifiers=(selector(both),)
                )
            ),
            service.traverse_learning_progressions(
                request=TraverseLearningProgressionsRequest(
                    **route, identifier=selector(root)
                )
            ),
            service.traverse_learning_progressions(
                request=TraverseLearningProgressionsRequest(
                    **route, direction="upstream", identifier=selector(root)
                )
            ),
        ]
        for result in results:
            expected = _expected(result, runtime, accepted_state)
            assert rehydrated(result) == expected
            assert_compact_form(expected=expected, result=result)
            labels = {e.relationship.label for e in expected}
            mixed += labels == {"buildsTowards", "relatesTo"}
            if not result.relationships:
                shared = result.model_dump(by_alias=True, mode="json")
                assert shared["sharedRelationshipEvidence"] == {}
                empty += 1
    # Every package contributes a mixed page and an empty upstream traversal.
    assert mixed >= 7 and empty == 7


def test_compact_lifting_keeps_differing_and_null_fields(
    accepted_state: AppState,
) -> None:
    """A liftable field that differs or is null on one entry stays per entry."""
    runtime = accepted_state.catalog_load_result.package_runtimes[0]
    service = accepted_state.learning_progressions_service
    builds = [
        e for e in runtime.loaded_package.relationships if e.label == "buildsTowards"
    ][:3]
    full = [
        service.relationship_evidence(relationship=edge, runtime=runtime)
        for edge in builds
    ]
    first, second, third = full
    assert first.relationship.license and first.relationship.author
    # Positive control: unchanged real evidence lifts both fields.
    shared, _ = compact_relationships(relationships=full)
    assert shared.relationship is not None
    assert shared.relationship.license == first.relationship.license
    assert shared.relationship.author == first.relationship.author
    varied = (
        first,
        second.model_copy(
            update={
                "relationship": second.relationship.model_copy(
                    update={"license": "Other licence"}
                )
            }
        ),
        third.model_copy(
            update={
                "relationship": third.relationship.model_copy(update={"author": None})
            }
        ),
    )
    shared, entries = compact_relationships(relationships=varied)
    assert shared.relationship is not None
    assert shared.relationship.license is None and shared.relationship.author is None
    assert [e.relationship.license for e in entries] == [
        first.relationship.license,
        "Other licence",
        first.relationship.license,
    ]
    assert [e.relationship.author for e in entries] == [
        first.relationship.author,
        first.relationship.author,
        None,
    ]
    assert rehydrate_relationships(relationships=entries, shared=shared) == varied
    emitted = [e.model_dump(by_alias=True, mode="json") for e in entries]
    assert "author" not in emitted[2]["relationship"]


async def test_published_progression_schemas(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Compacted tools publish the shared object; only paths take the ceiling of 16.

    The exact lookup's published schemas stay identical to the cycle baseline, and
    traversal keeps its own depth bounds and description.
    """
    monkeypatch.setattr("kgfegmcp.app.bootstrap_application", lambda: accepted_state)
    async with Client(create_mcp()) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}

    # The exact lookup keeps its full form and baseline schema.
    exact = tools["get_learning_progression"]
    digest = hashlib.sha256(
        json.dumps(
            [exact.inputSchema, exact.outputSchema, exact.description],
            sort_keys=True,
        ).encode()
    ).hexdigest()
    assert digest == EXACT_LOOKUP_SCHEMA_SHA256
    assert "sharedRelationshipEvidence" not in exact.outputSchema["properties"]

    # The four compacted tools publish compact entries and the shared object.
    for name in (
        "get_learning_progression_paths",
        "get_standard_progressions",
        "search_learning_progressions",
        "traverse_learning_progressions",
    ):
        output = tools[name].outputSchema
        assert {"relationships", "sharedRelationshipEvidence"} <= set(
            output["required"]
        )
        relationships = output["properties"]["relationships"]
        shared = output["properties"]["sharedRelationshipEvidence"]
        for described in (relationships, shared):
            assert "sharedRelationshipEvidence" in described["description"]
        entry = relationships["items"]
        assert set(entry["required"]) == {
            "judgment",
            "provenanceUri",
            "relationship",
            "relationshipUri",
        }
        assert set(entry["properties"]["relationship"]["required"]) == {
            "relationshipId",
            "sourceExportOrder",
            "sourceNodeId",
            "targetNodeId",
        }

    # The depth ceiling of 16 applies to paths only.
    paths = tools["get_learning_progression_paths"]
    depth = paths.inputSchema["properties"]["request"]["properties"]["maxDepth"]
    assert (depth["minimum"], depth["maximum"], depth["default"]) == (1, 16, 6)
    path = paths.outputSchema["properties"]["paths"]["items"]["properties"]
    assert path["nodeIds"]["maxItems"] == 17
    assert path["relationshipIds"]["maxItems"] == 16
    assert "maxima 16/20" in (paths.description or "")
    walk = tools["traverse_learning_progressions"]
    depth = walk.inputSchema["properties"]["request"]["properties"]["maxDepth"]
    assert (depth["minimum"], depth["maximum"], depth["default"]) == (1, 12, 8)
    assert "maxima 12/250/100" in (walk.description or "")
