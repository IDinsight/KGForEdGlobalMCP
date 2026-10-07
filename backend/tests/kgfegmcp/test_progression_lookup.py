"""Reused DEV-012 exact identity and typed lookup failure assertions."""

# Standard Library
import hashlib

from dataclasses import replace
from pathlib import Path

# Third Party Library
import pytest

# Package Library
from kgfegmcp.bootstrap import AppState
from kgfegmcp.catalog.service import CatalogService
from kgfegmcp.errors import (
    CapabilityUnavailableError,
    KGFEGMCPError,
    LearningProgressionNotFoundError,
    ResourceAccessDeniedError,
    StandardNotFoundError,
)
from kgfegmcp.graph.models import StandardNode
from kgfegmcp.services.lp_models import GetLearningProgressionRequest
from kgfegmcp.services.models import (
    CaseUriStandardIdentifier,
    CaseUuidStandardIdentifier,
    StandardIdentifier,
)
from tests.fixtures.progression_fixtures import selector

# Independent oracle for the Frame 2 compact metadata contract, sorted by name.
DERIVATION_ARTIFACTS = [
    "learningProgressionProvenance",
    "learningProgressionProvenanceIndex",
    "nodes",
    "relationships",
]


@pytest.mark.lp_dataset
def test_every_exact_edge_preserves_accepted_evidence(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exhaustively repeat original edge/hash/judgment/excerpt identity assertions."""
    service = accepted_state.learning_progressions_service
    count = 0

    def reject(*_args: object, **_kwargs: object) -> None:
        """Fail any exact-query attempt to reopen accepted source bytes."""
        pytest.fail("Exact query reopened a source artifact")

    monkeypatch.setattr(Path, "open", reject)
    monkeypatch.setattr(Path, "read_bytes", reject)
    for runtime in accepted_state.catalog_load_result.package_runtimes:
        identity = runtime.catalog_package.package_identity
        # Results list only their derivation artifacts; the manifest binds the rest.
        expected_hashes = sorted(
            (ref.logical_name, ref.sha256)
            for ref in runtime.loaded_package.artifacts
            if ref.logical_name in DERIVATION_ARTIFACTS
        )
        assert [name for name, _ in expected_hashes] == DERIVATION_ARTIFACTS
        assert len(runtime.loaded_package.artifacts) > len(DERIVATION_ARTIFACTS)
        for edge in runtime.loaded_package.relationships:
            if edge.label not in {"buildsTowards", "relatesTo"}:
                continue
            result = service.get_learning_progression(
                request=GetLearningProgressionRequest(
                    framework_id=identity.framework_id,
                    snapshot_id=identity.snapshot_id,
                    relationship_id=edge.relationship_id,
                )
            )
            actual = result.relationships[0]
            assert (
                actual.relationship is edge
                and actual.epistemic_status == "llm_inferred"
            )
            assert result.metadata.package.package_identity == identity
            assert (
                result.metadata.manifest_sha256
                == "sha256:"
                + hashlib.sha256(runtime.loaded_package.manifest_bytes).hexdigest()
            )
            assert [
                (ref.logical_name, ref.sha256) for ref in result.metadata.artifacts
            ] == expected_hashes
            route = result.metadata.manifest_uri.removesuffix("/manifest")
            assert [ref.uri for ref in result.metadata.artifacts] == [
                f"{route}/artifact/{name}" for name in DERIVATION_ARTIFACTS
            ]
            assert "manifestUri" in result.metadata.artifact_inventory_notice
            assert [node.node_id for node in result.nodes] == [
                edge.source_node_id,
                edge.target_node_id,
            ]
            for summary in result.nodes:
                original = runtime.graph_store.nodes_by_id[summary.node_id]
                # LP endpoints are standards; this also narrows the node union.
                assert isinstance(original, StandardNode)
                assert summary.case_identifier_uuid == original.case_identifier_uuid
                assert summary.case_identifier_uri == original.case_identifier_uri
                assert summary.statement_excerpt == (
                    original.description[:2048]
                    if original.description is not None
                    else None
                )
                assert summary.statement_excerpted == (
                    original.description is not None
                    and len(original.description) > 2048
                )
                assert (
                    summary.facets
                    == accepted_state.search_service.get_node_facet_evidence(
                        graph_package_id=identity.graph_package_id,
                        node_id=original.node_id,
                    )
                )
            evidence = runtime.loaded_package.learning_progression_evidence
            assert evidence
            judgment = next(
                row
                for row in evidence.judgments
                if row.relationship_id == edge.relationship_id
            )
            assert actual.judgment.model_dump(
                exclude={"confidence_notice"}
            ) == judgment.model_dump(exclude={"confidence_notice"})
            assert "calibrated probability" in actual.judgment.confidence_notice
            count += 1
    assert count == 8080


@pytest.mark.lp_dataset
@pytest.mark.parametrize(
    "kind", ["missing", "non_lp", "missing_standard", "unavailable", "denied"]
)
def test_reused_exact_failure_distinctions(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    """Retain distinct missing, unavailable and denied public error contracts."""
    runtime = accepted_state.catalog_load_result.package_runtimes[0]
    service = accepted_state.learning_progressions_service
    edge = next(
        e for e in runtime.loaded_package.relationships if e.label == "buildsTowards"
    )
    request = GetLearningProgressionRequest(
        framework_id=runtime.catalog_package.package_identity.framework_id,
        relationship_id=edge.relationship_id,
    )
    if kind == "missing_standard":
        with pytest.raises(StandardNotFoundError):
            service.resolve_standard(
                identifier=selector("missing-node"), runtime=runtime
            )
        return
    if kind in {"missing", "non_lp"}:
        absent = (
            "missing-edge"
            if kind == "missing"
            else next(
                e.relationship_id
                for e in runtime.loaded_package.relationships
                if e.label not in {"buildsTowards", "relatesTo"}
            )
        )
        with pytest.raises(LearningProgressionNotFoundError):
            service.get_learning_progression(
                request=request.model_copy(update={"relationship_id": absent})
            )
        return
    if kind == "unavailable":
        projected = replace(
            runtime,
            loaded_package=runtime.loaded_package.model_copy(
                update={"learning_progression_evidence": None}
            ),
        )
        expected: type[KGFEGMCPError] = CapabilityUnavailableError
    else:
        rights = runtime.catalog_package.rights.model_copy(
            update={"allow_full_text": False}
        )
        package = runtime.catalog_package.model_copy(update={"rights": rights})
        projected = replace(
            runtime,
            catalog_package=package,
            loaded_package=runtime.loaded_package.model_copy(
                update={
                    "manifest": runtime.loaded_package.manifest.model_copy(
                        update={"rights": rights}
                    )
                }
            ),
        )
        expected = ResourceAccessDeniedError
    monkeypatch.setattr(
        CatalogService, "get_package_runtime", lambda *_args, **_kwargs: projected
    )
    with pytest.raises(expected):
        service.get_learning_progression(request=request)


def test_reused_selector_namespaces(accepted_state: AppState) -> None:
    """Node/CASE UUID/CASE URI resolve the same original standard in each package."""
    for runtime in accepted_state.catalog_load_result.package_runtimes:
        node = runtime.loaded_package.item_nodes[0]
        identifiers: list[StandardIdentifier] = [
            selector(node.node_id),
            CaseUuidStandardIdentifier(
                identifier_type="case_identifier_uuid",
                case_identifier_uuid=node.case_identifier_uuid,
            ),
            CaseUriStandardIdentifier(
                identifier_type="case_identifier_uri",
                case_identifier_uri=node.case_identifier_uri,
            ),
        ]
        for identifier in identifiers:
            assert (
                accepted_state.learning_progressions_service.resolve_standard(
                    identifier=identifier, runtime=runtime
                )
                is node
            )
