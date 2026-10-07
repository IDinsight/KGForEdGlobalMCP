"""DEV-025 get_workflow_instructions parity with native prompts through real MCP."""

# Standard Library
import hashlib
import json

from typing import Any

# Third Party Library
import pytest

from fastmcp import Client
from pydantic import TypeAdapter

# Package Library
from kgfegmcp.app import create_mcp
from kgfegmcp.bootstrap import AppState
from kgfegmcp.prompts.workflow_instructions import WorkflowInstructionsRequest
from tests.fixtures.progression_fixtures import selector

VARIANTS = [
    "learning_progression_teaching_sequence",
    "learning_progression_support_plan",
    "learning_progression_curriculum_review",
    "teacher_guide_draft",
    "student_study_support",
    "student_handbook_section",
    "multigrade_lesson_plan",
]


def arguments(state: AppState, name: str) -> tuple[dict[str, str], dict[str, Any]]:
    """Build equivalent native string arguments and typed tool request values."""
    runtime = state.catalog_load_result.package_runtimes[0]
    identity = runtime.catalog_package.package_identity
    grades = [row.local_label for row in runtime.loaded_package.profile.grade_mappings]
    node = selector(runtime.loaded_package.item_nodes[0].node_id).model_dump(
        by_alias=True, mode="json"
    )
    # Shared non-default caller context and an exact pinned snapshot.
    common: dict[str, Any] = {
        "framework_id": str(identity.framework_id),
        "local_context": "Teacher observation; not measured mastery.",
        "output_language": "fr",
        "snapshot_id": str(identity.snapshot_id),
    }
    specifics: dict[str, dict[str, Any]] = {
        "learning_progression_teaching_sequence": {
            "local_grade_labels": grades[:1],
            "topic_or_standard": "number",
        },
        "learning_progression_support_plan": {"identifier": node},
        "learning_progression_curriculum_review": {
            "endpoint_scope": "source",
            "local_grade_labels": grades[:1],
        },
        "teacher_guide_draft": {
            "available_materials": "Counters and a chalkboard.",
            "grade_or_stage": grades[0],
            "topic_or_standard": "number",
        },
        "student_study_support": {
            "difficulty": "foundational",
            "grade_or_stage": grades[0],
            "practice_count": 3,
            "topic_or_standard": "number",
        },
        "student_handbook_section": {
            "grade_or_stage": grades[0],
            "target_word_count": 300,
            "topic_or_standard": "number",
        },
        "multigrade_lesson_plan": {
            "grades_in_room": grades[:2],
            "lesson_duration_minutes": 60,
            "topic_or_standard": "number",
        },
    }
    values = {**common, **specifics[name]}
    # Native MCP prompts receive every argument as a string; complex values are JSON.
    native = {
        key: value if isinstance(value, str) else json.dumps(value)
        for key, value in values.items()
    }
    camel = {
        "".join(
            part.capitalize() if index else part
            for index, part in enumerate(key.split("_"))
        ): value
        for key, value in values.items()
    }
    return native, {**camel, "workflowName": name}


@pytest.mark.parametrize("name", VARIANTS)
async def test_tool_renders_the_native_prompt_message(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    """Each variant's tool text carries exactly the native message and pinned identity."""
    monkeypatch.setattr("kgfegmcp.app.bootstrap_application", lambda: accepted_state)
    runtime = accepted_state.catalog_load_result.package_runtimes[0]
    identity = runtime.catalog_package.package_identity
    native_arguments, request = arguments(accepted_state, name)
    async with Client(create_mcp()) as client:
        native = await client.get_prompt(name, native_arguments)
        tool = await client.call_tool("get_workflow_instructions", {"request": request})
    payload = json.loads(tool.content[0].text)
    assert payload == tool.structured_content
    message = payload["rendered"]["message"]
    assert message == native.messages[0].content.text
    assert native.meta["promptVersion"] == "1.4.0"
    assert "EVIDENCE ACCESS" in message and "read_evidence" in message
    adapter: TypeAdapter[WorkflowInstructionsRequest] = TypeAdapter(
        WorkflowInstructionsRequest
    )
    expected = adapter.validate_python(request)
    assert payload["effectiveRequest"] == expected.model_dump(
        by_alias=True, mode="json"
    )
    assert payload["package"]["packageIdentity"] == identity.model_dump(
        by_alias=True, mode="json"
    )
    assert payload["profileSha256"] == str(identity.profile_sha256)
    assert (
        payload["manifestSha256"]
        == "sha256:" + hashlib.sha256(runtime.loaded_package.manifest_bytes).hexdigest()
    )


async def test_obsolete_workflow_name_is_rejected(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The removed hypothesis workflow has no alternate instruction route."""
    monkeypatch.setattr("kgfegmcp.app.bootstrap_application", lambda: accepted_state)
    _, request = arguments(accepted_state, "learning_progression_support_plan")
    async with Client(create_mcp()) as client:
        with pytest.raises(Exception) as failure:
            await client.call_tool(
                "get_workflow_instructions",
                {
                    "request": {
                        **request,
                        "workflowName": "inferred_progression_hypothesis",
                    }
                },
            )
    assert "inferred_progression_hypothesis" in str(failure.value)


async def test_oversized_instructions_fail_without_clipping(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Instructions over the envelope ceiling fail explicitly, never partially."""
    monkeypatch.setattr("kgfegmcp.app.bootstrap_application", lambda: accepted_state)
    # Lower only the adapter's character ceiling to reach the boundary with real text.
    monkeypatch.setattr("kgfegmcp.mcp.tools.workflows.MAX_TOOL_RESULT_CHARACTERS", 1000)
    _, request = arguments(accepted_state, "learning_progression_support_plan")
    async with Client(create_mcp()) as client:
        with pytest.raises(Exception) as failure:
            await client.call_tool("get_workflow_instructions", {"request": request})
    assert "workflow_instructions_too_large" in str(failure.value)
    assert "EVIDENCE ACCESS" not in str(failure.value)


async def test_single_type_review_renders_only_that_scan(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """relationship_types [relatesTo] reaches both routes and keeps one scan."""
    monkeypatch.setattr("kgfegmcp.app.bootstrap_application", lambda: accepted_state)
    name = "learning_progression_curriculum_review"
    native_arguments, request = arguments(accepted_state, name)
    native_arguments["relationship_types"] = json.dumps(["relatesTo"])
    request["relationshipTypes"] = ["relatesTo"]
    async with Client(create_mcp()) as client:
        native = await client.get_prompt(name, native_arguments)
        tool = await client.call_tool("get_workflow_instructions", {"request": request})
    payload = json.loads(tool.content[0].text)
    message = payload["rendered"]["message"]
    assert message == native.messages[0].content.text
    assert payload["effectiveRequest"]["relationshipTypes"] == ["relatesTo"]
    scans = [
        json.loads(line)["request"]
        for line in message.splitlines()
        if line.startswith('{"request":') and "relationshipTypes" in line
    ]
    assert [scan["relationshipTypes"] for scan in scans] == [["relatesTo"]]
    assert "- relatesTo scan:" in message and "- buildsTowards scan:" not in message
