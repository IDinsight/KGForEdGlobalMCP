"""Real in-process MCP prompt retrieval and reused public error boundary checks."""

# Third Party Library
import pytest

from fastmcp import Client

# Package Library
from kgfegmcp.app import create_mcp
from kgfegmcp.bootstrap import AppState
from kgfegmcp.errors import ProgressionResultTooLargeError, ResourceAccessDeniedError
from kgfegmcp.services.learning_progressions import LearningProgressionsService
from kgfegmcp.services.lp_models import (
    GetLearningProgressionPathsRequest,
    GetLearningProgressionRequest,
    GetStandardProgressionsRequest,
    SearchLearningProgressionsRequest,
    TraverseLearningProgressionsRequest,
)
from tests.fixtures.progression_fixtures import selector


@pytest.mark.parametrize(
    "name",
    [
        "learning_progression_teaching_sequence",
        "learning_progression_support_plan",
        "learning_progression_curriculum_review",
    ],
)
async def test_new_prompt_protocol_retrieval(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    """The registered client-invocable workflow returns pinned generated-evidence text."""
    monkeypatch.setattr("kgfegmcp.app.bootstrap_application", lambda: accepted_state)
    runtime = accepted_state.catalog_load_result.package_runtimes[0]
    identity = runtime.catalog_package.package_identity
    arguments = {
        "framework_id": str(identity.framework_id),
        "snapshot_id": str(identity.snapshot_id),
    }
    if name.endswith("teaching_sequence"):
        arguments["topic_or_standard"] = "mathematics"
    elif name.endswith("support_plan"):
        # Standard Library
        import json

        arguments["identifier"] = json.dumps(
            selector(runtime.loaded_package.item_nodes[0].node_id).model_dump(
                by_alias=True, mode="json"
            )
        )
    async with Client(create_mcp()) as client:
        result = await client.get_prompt(name, arguments)
    assert (
        result.messages
        and "[LLM-INFERRED / GENERATED]" in result.messages[0].content.text
    )
    assert result.meta["snapshotId"] == str(identity.snapshot_id)
    assert result.meta["promptVersion"] == "1.3.0"


async def test_reused_mcp_error_and_removed_surface_contracts(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Repeat DEV-017 schema, typed refusal, private-error masking and obsolete refusal."""
    monkeypatch.setattr("kgfegmcp.app.bootstrap_application", lambda: accepted_state)
    runtime = accepted_state.catalog_load_result.package_runtimes[0]
    identity = runtime.catalog_package.package_identity
    edge = next(
        e for e in runtime.loaded_package.relationships if e.label == "buildsTowards"
    )
    route = {"framework_id": identity.framework_id, "snapshot_id": identity.snapshot_id}
    source, target = selector(edge.source_node_id), selector(edge.target_node_id)
    samples = {
        "get_learning_progression": GetLearningProgressionRequest(
            **route, relationship_id=edge.relationship_id
        ),
        "get_standard_progressions": GetStandardProgressionsRequest(
            **route, identifier=source
        ),
        "search_learning_progressions": SearchLearningProgressionsRequest(**route),
        "traverse_learning_progressions": TraverseLearningProgressionsRequest(
            **route, identifier=source
        ),
        "get_learning_progression_paths": GetLearningProgressionPathsRequest(
            **route, source_identifier=source, target_identifier=target
        ),
    }
    async with Client(create_mcp()) as client:
        assert len(await client.list_tools()) == 17
        assert len(await client.list_prompts()) == 9
        for name, request in samples.items():
            payload = request.model_dump(by_alias=True, mode="json")
            with pytest.raises(Exception):
                await client.call_tool(
                    name, {"request": {**payload, "extra": "forbidden"}}
                )
            missing = dict(payload)
            missing.pop("frameworkId")
            with pytest.raises(Exception):
                await client.call_tool(name, {"request": missing})
            for error, code in [
                (RuntimeError("SECRET /Users/private"), "internal_error"),
                (
                    ResourceAccessDeniedError(message="Denied retained content"),
                    "resource_access_denied",
                ),
                (
                    ProgressionResultTooLargeError(message="Oversized whole entry"),
                    "progression_result_too_large",
                ),
            ]:
                with monkeypatch.context() as isolated:

                    def reject(*_args: object, **_kwargs: object) -> None:
                        """Supply a controlled service-boundary fault without source mutation."""
                        raise error

                    isolated.setattr(LearningProgressionsService, name, reject)
                    with pytest.raises(Exception) as failure:
                        await client.call_tool(name, {"request": payload})
                    assert code in str(failure.value)
                    assert "SECRET" not in str(failure.value) and "/Users/" not in str(
                        failure.value
                    )
        with pytest.raises(Exception):
            await client.call_tool("collect_progression_evidence", {})
        with pytest.raises(Exception):
            await client.get_prompt("inferred_progression_hypothesis", {})
