"""Stored LP pagination, exact adjacency, endpoint filtering and byte boundaries."""

# Standard Library
from typing import Any

# Third Party Library
import pytest

# Package Library
from kgfegmcp.bootstrap import AppState
from kgfegmcp.catalog.models import CatalogPackageRuntime
from kgfegmcp.errors import InvalidCursorError, ProgressionResultTooLargeError
from kgfegmcp.graph.models import GraphRelationship
from kgfegmcp.search.service import SearchService
from kgfegmcp.services.learning_progressions import LearningProgressionsService
from kgfegmcp.services.lp_discovery import collection_result
from kgfegmcp.services.lp_models import (
    GetStandardProgressionsRequest,
    SearchLearningProgressionsRequest,
)
from tests.fixtures.progression_fixtures import selector


def ordered(runtime: CatalogPackageRuntime) -> tuple[GraphRelationship, ...]:
    """Build an independent label/ID oracle from original accepted records."""
    return tuple(
        sorted(
            (
                e
                for e in runtime.loaded_package.relationships
                if e.label in {"buildsTowards", "relatesTo"}
            ),
            key=lambda e: (e.label, e.relationship_id),
        )
    )


def pages(service: Any, request: Any, method: str) -> tuple[list[str], Any]:
    """Follow unchanged requests, bounding continuation and forbidding duplicates."""
    found: list[str] = []
    cursors: set[str] = set()
    result = None
    for _ in range(400):
        result = getattr(service, method)(request=request)
        found.extend(e.relationship.relationship_id for e in result.relationships)
        assert result.page.returned_count == len(result.relationships) <= request.limit
        assert result.page.examined_count <= 5000
        assert result.page.has_more == (result.page.next_cursor is not None)
        assert result.page.is_complete == (not result.page.has_more)
        if result.page.next_cursor is None:
            assert len(found) == len(set(found))
            return found, result
        assert result.page.next_cursor not in cursors
        cursors.add(result.page.next_cursor)
        request = request.model_copy(update={"cursor": result.page.next_cursor})
    pytest.fail("Continuation did not terminate within the bounded accepted dataset.")


def test_complete_pagination_matches_original_edges(accepted_state: AppState) -> None:
    """Bounded six-package generation verifies one exhaustive ordered-ID property."""
    total = 0
    for runtime in accepted_state.catalog_load_result.package_runtimes:
        identity = runtime.catalog_package.package_identity
        request = SearchLearningProgressionsRequest(
            framework_id=identity.framework_id,
            snapshot_id=identity.snapshot_id,
            limit=100,
        )
        found, result = pages(
            accepted_state.learning_progressions_service,
            request,
            "search_learning_progressions",
        )
        assert found == [e.relationship_id for e in ordered(runtime)]
        assert (
            result.metadata.stored_builds_towards_count
            == runtime.loaded_package.manifest.counts.builds_towards_relationships
        )
        assert (
            result.metadata.stored_relates_to_count
            == runtime.loaded_package.manifest.counts.relates_to_relationships
        )
        total += len(found)
    assert total == 8080


@pytest.mark.parametrize("kind", ["incoming_builds", "outgoing_builds", "related"])
def test_direct_adjacency_matches_original_records(
    accepted_state: AppState, kind: str
) -> None:
    """Each connection kind has its own oracle, preserving canonical orientation."""
    for runtime in accepted_state.catalog_load_result.package_runtimes:
        edges = ordered(runtime)
        edge = next(
            e
            for e in edges
            if e.label == ("relatesTo" if kind == "related" else "buildsTowards")
        )
        node = edge.target_node_id if kind == "incoming_builds" else edge.source_node_id
        request = GetStandardProgressionsRequest(
            framework_id=runtime.catalog_package.package_identity.framework_id,
            identifier=selector(node),
            connection_kind=kind,
            limit=100,
        )
        found, result = pages(
            accepted_state.learning_progressions_service,
            request,
            "get_standard_progressions",
        )
        expected = [
            e.relationship_id
            for e in edges
            if (
                kind == "incoming_builds"
                and e.label == "buildsTowards"
                and e.target_node_id == node
            )
            or (
                kind == "outgoing_builds"
                and e.label == "buildsTowards"
                and e.source_node_id == node
            )
            or (
                kind == "related"
                and e.label == "relatesTo"
                and node in (e.source_node_id, e.target_node_id)
            )
        ]
        assert found == expected and edge.relationship_id in found
        assert all(
            e.relationship
            == runtime.graph_store.relationships_by_id[e.relationship.relationship_id]
            for e in result.relationships
        )


@pytest.mark.parametrize("scope", ["either", "both", "source", "target"])
def test_endpoint_scope_exact_selection(accepted_state: AppState, scope: str) -> None:
    """Each scope evaluates exact membership on the specified endpoints."""
    for runtime in accepted_state.catalog_load_result.package_runtimes:
        edges = ordered(runtime)
        selected = edges[0].source_node_id
        request = SearchLearningProgressionsRequest(
            framework_id=runtime.catalog_package.package_identity.framework_id,
            standard_identifiers=(selector(selected),),
            endpoint_scope=scope,
            limit=100,
        )
        found, _ = pages(
            accepted_state.learning_progressions_service,
            request,
            "search_learning_progressions",
        )

        def match(edge: GraphRelationship) -> bool:
            """Evaluate the selected endpoint predicate independently."""
            source, target = (
                edge.source_node_id == selected,
                edge.target_node_id == selected,
            )
            return {
                "either": source or target,
                "both": source and target,
                "source": source,
                "target": target,
            }[scope]

        assert found == [e.relationship_id for e in edges if match(e)]


def test_facets_cannot_mix_across_endpoints(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A grade from source cannot combine with a statement type from target."""
    runtime = accepted_state.catalog_load_result.package_runtimes[0]
    identity = runtime.catalog_package.package_identity
    edge = ordered(runtime)[0]
    evidence = accepted_state.search_service.get_node_facet_evidence(
        graph_package_id=identity.graph_package_id, node_id=edge.source_node_id
    )
    grades = tuple(
        dict.fromkeys(
            v
            for row in runtime.loaded_package.profile.grade_mappings
            for v in row.normalized_grades
        )
    )
    types = tuple(
        row.source_statement_type
        for row in runtime.loaded_package.profile.statement_types
    )
    assert len(grades) >= 2 and len(types) >= 2

    def facets(*, graph_package_id: Any, node_id: str) -> Any:
        """Supply individually valid but opposite-endpoint facet evidence."""
        index = int(node_id != edge.source_node_id)
        return evidence.model_copy(
            update={
                "normalized_grades": (grades[index],),
                "statement_type": types[index],
            }
        )

    monkeypatch.setattr(SearchService, "get_node_facet_evidence", staticmethod(facets))
    request = SearchLearningProgressionsRequest(
        framework_id=identity.framework_id,
        normalized_grades=(grades[0],),
        statement_types=(types[1],),
    )
    result = collection_result(
        candidates=(edge,),
        request=request,
        runtime=runtime,
        service=accepted_state.learning_progressions_service,
    )
    assert (
        not result.relationships
        and result.page.is_complete
        and result.page.total_matching_count == 0
    )


def test_cursor_binds_the_normalized_request(accepted_state: AppState) -> None:
    """Bounded mutation generation checks one request-integrity property."""
    runtime = accepted_state.catalog_load_result.package_runtimes[0]
    service = accepted_state.learning_progressions_service
    request = SearchLearningProgressionsRequest(
        framework_id=runtime.catalog_package.package_identity.framework_id, limit=1
    )
    first = service.search_learning_progressions(request=request)
    assert first.page.next_cursor
    mutations: list[dict[str, Any]] = [
        {"limit": 2},
        {"endpoint_scope": "both"},
        {"relationship_types": ("relatesTo",)},
        {"standard_identifiers": (selector(ordered(runtime)[0].source_node_id),)},
        {"cursor": "bad!"},
    ]
    for update in mutations:
        with pytest.raises(InvalidCursorError):
            service.search_learning_progressions(
                request=request.model_copy(
                    update={"cursor": first.page.next_cursor, **update}
                )
            )
    repeat = service.search_learning_progressions(request=request)
    assert repeat == first


def test_zero_match_work_page_makes_progress(accepted_state: AppState) -> None:
    """Continuation advances examined nonmatches and preserves unknown totals."""
    runtime = accepted_state.catalog_load_result.package_runtimes[0]
    edges = ordered(runtime)
    build = next(e for e in edges if e.label == "buildsTowards")
    related = next(e for e in edges if e.label == "relatesTo")
    candidates = tuple(
        build.model_copy(update={"relationship_id": f"e{i:05}"}) for i in range(5001)
    ) + (related,)
    request = SearchLearningProgressionsRequest(
        framework_id=runtime.catalog_package.package_identity.framework_id,
        relationship_types=("relatesTo",),
    )
    first = collection_result(
        candidates=candidates,
        request=request,
        runtime=runtime,
        service=accepted_state.learning_progressions_service,
    )
    assert not first.relationships and first.page.examined_count == 5000
    assert first.page.stopping_reason == "work_limit" and first.page.next_cursor
    assert first.page.total_matching_count is None
    last = collection_result(
        candidates=candidates,
        request=request.model_copy(update={"cursor": first.page.next_cursor}),
        runtime=runtime,
        service=accepted_state.learning_progressions_service,
    )
    assert last.page.examined_count == 2 and last.page.is_complete
    assert [e.relationship.relationship_id for e in last.relationships] == [
        related.relationship_id
    ]
    assert last.page.total_matching_count is None


def project_large(monkeypatch: pytest.MonkeyPatch, size: int) -> None:
    """Inject projected content while preserving original accepted graph records."""
    original = LearningProgressionsService.relationship_evidence

    def project(
        *, relationship: GraphRelationship, runtime: CatalogPackageRuntime
    ) -> Any:
        """Retain real judgment/routing while testing the actual UTF-8 byte ceiling."""
        item = original(relationship=relationship, runtime=runtime)
        return item.model_copy(
            update={
                "relationship": relationship.model_copy(
                    update={"attribution_statement": "x" * size}
                )
            }
        )

    monkeypatch.setattr(
        LearningProgressionsService, "relationship_evidence", staticmethod(project)
    )


def test_discovery_oversized_entry_rejected(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An individually unreturnable collection entry requires resource recovery."""
    project_large(monkeypatch, 1048577)
    runtime = accepted_state.catalog_load_result.package_runtimes[0]
    with pytest.raises(ProgressionResultTooLargeError) as failure:
        accepted_state.learning_progressions_service.search_learning_progressions(
            request=SearchLearningProgressionsRequest(
                framework_id=runtime.catalog_package.package_identity.framework_id
            )
        )
    assert "resource" in failure.value.recovery_hint.lower()


def test_discovery_combination_bytes_preserve_continuation(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Byte overflow resumes at the whole omitted entry without skipping IDs."""
    project_large(monkeypatch, 600000)
    runtime = accepted_state.catalog_load_result.package_runtimes[0]
    candidates = ordered(runtime)[:3]
    request = SearchLearningProgressionsRequest(
        framework_id=runtime.catalog_package.package_identity.framework_id, limit=100
    )
    found: list[str] = []
    reasons: list[str | None] = []
    for _ in range(3):
        result = collection_result(
            candidates=candidates,
            request=request,
            runtime=runtime,
            service=accepted_state.learning_progressions_service,
        )
        found.extend(e.relationship.relationship_id for e in result.relationships)
        reasons.append(result.page.stopping_reason)
        assert (
            accepted_state.learning_progressions_service.require_collection_result_size(
                result=result
            )
            <= 1048576
        )
        if result.page.next_cursor is None:
            break
        request = request.model_copy(update={"cursor": result.page.next_cursor})
    assert found == [e.relationship_id for e in candidates]
    assert reasons == ["byte_limit", "byte_limit", None]


@pytest.mark.parametrize("kind", ["checksum", "range", "stale"])
def test_reused_cursor_integrity_boundaries(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    """Retain DEV-013 checksum, correctly signed range and stale-manifest rejection."""
    # Standard Library
    import base64
    import hashlib
    import json

    runtime = accepted_state.catalog_load_result.package_runtimes[0]
    service = accepted_state.learning_progressions_service
    request = SearchLearningProgressionsRequest(
        framework_id=runtime.catalog_package.package_identity.framework_id, limit=1
    )
    first = service.search_learning_progressions(request=request)
    cursor = first.page.next_cursor
    assert cursor
    if kind == "stale":
        metadata = first.metadata.model_copy(
            update={"manifest_sha256": "sha256:" + "0" * 64}
        )
        monkeypatch.setattr(
            LearningProgressionsService,
            "evidence_metadata",
            lambda *_args, **_kwargs: metadata,
        )
    else:
        payload = json.loads(
            base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
        )
        payload["position"] = len(ordered(runtime))
        if kind == "range":
            unsigned = {
                key: value for key, value in payload.items() if key != "payloadSha256"
            }
            payload["payloadSha256"] = (
                "sha256:"
                + hashlib.sha256(
                    json.dumps(
                        unsigned,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    ).encode()
                ).hexdigest()
            )
        cursor = (
            base64.urlsafe_b64encode(
                json.dumps(
                    payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
                ).encode()
            )
            .decode()
            .rstrip("=")
        )
    with pytest.raises(InvalidCursorError):
        service.search_learning_progressions(
            request=request.model_copy(update={"cursor": cursor})
        )


def test_reused_profile_code_and_grade_facets(accepted_state: AppState) -> None:
    """Repeat DEV-013 profile-valid code/grade filter equivalence against real nodes."""
    # Package Library
    from kgfegmcp.domain.enums import CodeAvailability
    from kgfegmcp.errors import AmbiguousGraphNodeError, CapabilityUnavailableError
    from kgfegmcp.services.lp_models import StatementCodeStandardIdentifier

    service = accepted_state.learning_progressions_service
    for runtime in accepted_state.catalog_load_result.package_runtimes:
        identity = runtime.catalog_package.package_identity
        if runtime.catalog_package.capabilities.code_search is CodeAvailability.NONE:
            with pytest.raises(CapabilityUnavailableError):
                service.search_learning_progressions(
                    request=SearchLearningProgressionsRequest(
                        framework_id=identity.framework_id,
                        standard_identifiers=(
                            StatementCodeStandardIdentifier(
                                identifier_type="statement_code",
                                statement_code="example",
                            ),
                        ),
                    )
                )
        else:
            for node in runtime.loaded_package.item_nodes:
                if not node.statement_code:
                    continue
                identifier = StatementCodeStandardIdentifier(
                    identifier_type="statement_code", statement_code=node.statement_code
                )
                try:
                    selected = service.resolve_standard(
                        identifier=identifier, runtime=runtime
                    )
                except AmbiguousGraphNodeError:
                    continue
                reference = service.search_learning_progressions(
                    request=SearchLearningProgressionsRequest(
                        framework_id=identity.framework_id,
                        standard_identifiers=(selector(selected.node_id),),
                    )
                )
                actual = service.search_learning_progressions(
                    request=SearchLearningProgressionsRequest(
                        framework_id=identity.framework_id,
                        standard_identifiers=(identifier,),
                    )
                )
                assert (
                    actual.relationships == reference.relationships
                    and actual.connections == reference.connections
                )
                break
            else:
                pytest.fail("Coded profile had no unambiguous stored selector")
        edge = ordered(runtime)[0]
        facet = accepted_state.search_service.get_node_facet_evidence(
            graph_package_id=identity.graph_package_id, node_id=edge.source_node_id
        )
        mapping = next(
            row
            for row in runtime.loaded_package.profile.grade_mappings
            if row.local_label in facet.resolved_local_grade_labels
        )
        request = SearchLearningProgressionsRequest(
            framework_id=identity.framework_id,
            endpoint_scope="source",
            local_grade_labels=(mapping.local_label,),
            limit=100,
        )
        found, _ = pages(service, request, "search_learning_progressions")
        expected = [
            candidate.relationship_id
            for candidate in ordered(runtime)
            if mapping.local_label
            in accepted_state.search_service.get_node_facet_evidence(
                graph_package_id=identity.graph_package_id,
                node_id=candidate.source_node_id,
            ).resolved_local_grade_labels
        ]
        assert found == expected
        if mapping.aliases:
            aliases, _ = pages(
                service,
                request.model_copy(
                    update={"local_grade_labels": (mapping.aliases[0],)}
                ),
                "search_learning_progressions",
            )
            assert aliases == found
