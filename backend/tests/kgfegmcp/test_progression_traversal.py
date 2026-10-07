"""Offline traversal byte-boundary regression checks using retained evidence shapes."""

# Standard Library
import socket

from typing import Any

# Third Party Library
import pytest

# Package Library
from kgfegmcp.bootstrap import AppState, bootstrap_application
from kgfegmcp.catalog.models import CatalogPackageRuntime
from kgfegmcp.errors import ProgressionResultTooLargeError
from kgfegmcp.graph.models import GraphRelationship
from kgfegmcp.services.learning_progressions import LearningProgressionsService
from kgfegmcp.services.lp_models import (
    MAX_PROGRESSION_RESULT_BYTES,
    ProgressionRelationshipEvidence,
    TraverseLearningProgressionsRequest,
)
from kgfegmcp.services.models import NodeIdStandardIdentifier


@pytest.fixture(scope="module")
def application() -> AppState:
    """Load actual accepted local packages once; no producer or model is called."""
    return bootstrap_application()


@pytest.fixture(autouse=True)
def deny_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail any attempted network connection, including model or paid-service calls."""

    def reject(*_args: Any, **_kwargs: Any) -> None:
        """Reject rather than silently substituting a live service."""
        raise AssertionError("Network connections are forbidden in offline tests.")

    monkeypatch.setattr(socket.socket, "connect", reject)
    monkeypatch.setattr(socket.socket, "connect_ex", reject)


@pytest.mark.parametrize("oversized_position", [0, 1], ids=["first", "later"])
def test_individually_oversized_traversal_entry_is_an_error(
    application: AppState,
    monkeypatch: pytest.MonkeyPatch,
    oversized_position: int,
) -> None:
    """Reject an unreturnable edge even when earlier evidence fits the response.

    Supply synthetic large projected content at the evidence boundary without
    changing an accepted record, source file or production byte ceiling. The real
    traversal and encoder execute. This tests response behavior, not acceptance
    of a synthetic package. Two distinct placement cases consume two scenarios.
    """
    runtime = application.catalog_load_result.package_runtimes[0]
    service = application.learning_progressions_service
    origin, candidates = next(
        (node_id, edges)
        for (label, node_id), edges in sorted(
            runtime.graph_store.outgoing_by_type_and_node.items()
        )
        if label == "buildsTowards" and len(edges) >= 2
    )
    edges = tuple(sorted(candidates, key=lambda edge: edge.relationship_id)[:2])
    oversized_id = edges[oversized_position].relationship_id
    original = LearningProgressionsService.relationship_evidence

    def project(
        *, relationship: GraphRelationship, runtime: CatalogPackageRuntime
    ) -> ProgressionRelationshipEvidence:
        """Preserve the real evidence contract while injecting one large field."""
        result = original(relationship=relationship, runtime=runtime)
        if relationship.relationship_id == oversized_id:
            # GraphRelationship has no attribution-length restriction. A complete
            # entry with this ASCII field alone already exceeds the whole envelope.
            large = relationship.model_copy(
                update={
                    "attribution_statement": "x" * (MAX_PROGRESSION_RESULT_BYTES + 1)
                }
            )
            result = result.model_copy(update={"relationship": large})
        return result

    monkeypatch.setattr(
        LearningProgressionsService, "relationship_evidence", staticmethod(project)
    )
    identity = runtime.catalog_package.package_identity
    request = TraverseLearningProgressionsRequest(
        framework_id=identity.framework_id,
        identifier=NodeIdStandardIdentifier(identifier_type="node_id", node_id=origin),
        max_depth=1,
        snapshot_id=identity.snapshot_id,
    )
    with pytest.raises(ProgressionResultTooLargeError) as failure:
        observed = service.traverse_learning_progressions(request=request)
        pytest.fail(
            "An individually oversized edge was silently omitted: "
            f"returned={observed.counters.returned_relationship_count}, "
            f"examined={observed.counters.examined_relationship_count}, "
            f"reasons={observed.truncation_reasons}, "
            f"scope_complete={observed.scope_complete}."
        )
    assert failure.value.error_code == "progression_result_too_large"
    assert failure.value.recovery_hint is not None
    assert "resource" in failure.value.recovery_hint.lower()
