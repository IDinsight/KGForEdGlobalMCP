"""Complete original provenance, safe summaries and explicit rights/byte refusals."""

# Standard Library
import hashlib
import json

from dataclasses import replace
from types import SimpleNamespace
from typing import Any

# Third Party Library
import pytest

# Package Library
from kgfegmcp.bootstrap import AppState
from kgfegmcp.errors import ResourceAccessDeniedError, ResourceNotFoundError
from kgfegmcp.resources.lp import partition_name
from kgfegmcp.resources.policy import ResourcePolicy
from kgfegmcp.resources.repository import ResourceRepository
from kgfegmcp.resources.service import ResourceService


def route(runtime: Any) -> dict[str, str]:
    """Pin the exact immutable framework/snapshot pair."""
    identity = runtime.catalog_package.package_identity
    return {"framework_id": identity.framework_id, "snapshot_id": identity.snapshot_id}


def test_original_per_edge_trace_and_hashes(accepted_state: AppState) -> None:
    """Six-package samples preserve complete original entries and independent hashes."""
    for runtime in accepted_state.catalog_load_result.package_runtimes:
        edge = next(
            e
            for e in runtime.loaded_package.relationships
            if e.label == "buildsTowards"
        )
        document = accepted_state.resource_service.relationship_provenance(
            **route(runtime), relationship_id=edge.relationship_id
        )
        original = runtime.loaded_package.artifact("learningProgressionProvenance")
        assert original
        entry = json.loads(original.resolved_path.read_bytes())[edge.relationship_id]
        payload = json.loads(document.content)
        assert (
            payload["provenance"] == entry
            and payload["epistemicStatus"] == "llm_inferred"
        )
        content = (
            document.content.encode()
            if isinstance(document.content, str)
            else document.content
        )
        assert (
            document.metadata.content_sha256
            == "sha256:" + hashlib.sha256(content).hexdigest()
        )
        references = {r.logical_name: r for r in document.metadata.source_artifacts}
        assert references["learningProgressionProvenance"].sha256 == original.sha256
        assert partition_name(edge.relationship_id) in references
        assert (
            "learningProgressionProvenanceIndex" in references
            and "relationships" in references
        )
        assert "not a mandatory prerequisite" in payload["semanticNotice"]


def test_summary_is_safe_public_projection(accepted_state: AppState) -> None:
    """Coverage/warnings remain explicit without source prompts or private paths."""
    for runtime in accepted_state.catalog_load_result.package_runtimes:
        document = accepted_state.resource_service.learning_progressions(
            **route(runtime)
        )
        payload = json.loads(document.content)
        assert (
            payload["buildsTowardsRelationships"]
            == runtime.loaded_package.manifest.counts.builds_towards_relationships
        )
        assert (
            payload["relatesToRelationships"]
            == runtime.loaded_package.manifest.counts.relates_to_relationships
        )
        assert payload["pedagogicalCorrectnessEstablished"] is False
        assert payload["semanticValidationPerformed"] is False
        assert "/Users/" not in str(document.content) and "producer_prompt" not in str(
            document.content
        )
        if "india-cbse" in runtime.catalog_package.package_identity.framework_id:
            assert payload["needsReviewClaims"] > 0


def test_bulk_is_denied_independently(accepted_state: AppState) -> None:
    """Actual reviewed full-text packages still refuse their bulk LP maps."""
    runtime = accepted_state.catalog_load_result.package_runtimes[0]
    assert runtime.catalog_package.rights.allow_full_text
    assert not runtime.catalog_package.rights.allow_bulk_resource
    with pytest.raises(ResourceAccessDeniedError):
        accepted_state.resource_service.artifact(
            **route(runtime), artifact_name="learningProgressionProvenance"
        )


def test_full_text_denial_precedes_reads(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A content refusal cannot fall back to reading the original map or partition."""
    runtime = accepted_state.catalog_load_result.package_runtimes[0]
    rights = runtime.catalog_package.rights.model_copy(
        update={"allow_full_text": False}
    )
    denied = SimpleNamespace(
        catalog_package=runtime.catalog_package.model_copy(update={"rights": rights}),
        graph_store=runtime.graph_store,
        loaded_package=runtime.loaded_package,
    )
    monkeypatch.setattr(
        ResourceService, "_package_runtime", lambda *_args, **_kwargs: denied
    )

    def reject(*_args: Any, **_kwargs: Any) -> None:
        """Prove no source read occurs after the denied rights decision."""
        pytest.fail("Denied provenance attempted an artifact read")

    monkeypatch.setattr(ResourceRepository, "read_artifact", reject)
    edge = next(
        e for e in runtime.loaded_package.relationships if e.label == "buildsTowards"
    )
    with pytest.raises(ResourceAccessDeniedError):
        accepted_state.resource_service.relationship_provenance(
            **route(runtime), relationship_id=edge.relationship_id
        )


def test_source_bytes_refused(accepted_state: AppState) -> None:
    """A lower operator source ceiling gives an explicit refusal of an exact entry."""
    runtime = accepted_state.catalog_load_result.package_runtimes[0]
    policy = ResourcePolicy(max_resource_bytes=1, max_resource_source_bytes=1)
    service = replace(
        accepted_state.resource_service,
        policy=policy,
        repository=ResourceRepository(policy=policy),
    )
    edge = next(
        e for e in runtime.loaded_package.relationships if e.label == "buildsTowards"
    )
    with pytest.raises(ResourceAccessDeniedError) as failure:
        service.relationship_provenance(
            **route(runtime), relationship_id=edge.relationship_id
        )
    assert "read limit" in failure.value.message


def test_final_bytes_refused() -> None:
    """Final content has an independent byte bound even when the source fits."""
    policy = ResourcePolicy(max_resource_bytes=8, max_resource_source_bytes=32)
    policy.require_source_size(9)
    with pytest.raises(ResourceAccessDeniedError):
        policy.require_return_size(9)


def test_unknown_artifact_cannot_use_prefix_policy(accepted_state: AppState) -> None:
    """An arbitrary shard-like name is outside the closed safe artifact contract."""
    runtime = accepted_state.catalog_load_result.package_runtimes[0]
    with pytest.raises(ResourceNotFoundError):
        accepted_state.resource_service.policy.artifact_decision(
            logical_name="learningProgressionProvenanceShard99",
            rights=runtime.catalog_package.rights,
        )


def test_resource_checksum_refusal(accepted_state: AppState, tmp_path: Any) -> None:
    """A changed isolated source cannot be read using accepted checksum evidence."""
    package = accepted_state.catalog_load_result.package_runtimes[0].loaded_package
    original = package.artifact("learningProgressionProvenanceIndex")
    assert original
    path = tmp_path / "changed.json"
    path.write_bytes(b"{}")
    altered = original.model_copy(update={"resolved_path": path})
    replacement = package.model_copy(
        update={
            "artifacts": tuple(
                altered if ref is original else ref for ref in package.artifacts
            )
        }
    )
    with pytest.raises(ResourceNotFoundError):
        accepted_state.resource_service.repository.read_artifact(
            loaded_package=replacement, logical_name=original.logical_name
        )
