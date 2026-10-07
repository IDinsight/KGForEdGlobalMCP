"""Expose native prompt workflows to tool-only clients through one thin tool."""

# Future Library
from __future__ import annotations

# Standard Library
from typing import TYPE_CHECKING

# Third Party Library
from fastmcp import Context
from fastmcp.tools.base import ToolResult
from mcp.types import CallToolResult

# Package Library
from kgfegmcp.errors import WorkflowInstructionsTooLargeError
from kgfegmcp.mcp.errors import tool_error_boundary
from kgfegmcp.mcp.tools import (
    READ_ONLY_TOOL_ANNOTATIONS,
    build_tool_result,
    get_app_state,
    result_schema,
)
from kgfegmcp.prompts.workflow_instructions import (
    WorkflowInstructionsRequest,
    WorkflowInstructionsResult,
    render_workflow_instructions,
)
from kgfegmcp.tool_results import (
    MAX_TOOL_RESULT_BYTES,
    MAX_TOOL_RESULT_CHARACTERS,
    canonical_result_text,
    tool_result_size,
)

if TYPE_CHECKING:
    # Third Party Library
    from fastmcp import FastMCP

    # Package Library
    from kgfegmcp.bootstrap import AppState


def _require_size(envelope: dict[str, object]) -> None:
    """Fail explicitly rather than clip instructions that exceed either ceiling.

    Parameters
    ----------
    envelope
        Actual emitted tool envelope.

    Raises
    ------
    WorkflowInstructionsTooLargeError
        If the complete envelope exceeds the byte or character ceiling.
    """

    size = tool_result_size(envelope)

    if (
        size.byte_length > MAX_TOOL_RESULT_BYTES
        or size.character_length > MAX_TOOL_RESULT_CHARACTERS
    ):
        raise WorkflowInstructionsTooLargeError(
            details={
                "actual_bytes": size.byte_length,
                "actual_characters": size.character_length,
            },
            message="The complete workflow instructions exceed the tool result ceiling.",
            recovery_hint=(
                "Use the native prompt of the same name, or shorten caller-supplied "
                "context such as localContext."
            ),
        )


async def get_workflow_instructions(
    *, context: Context, request: WorkflowInstructionsRequest
) -> ToolResult:
    """Return the complete instructions of one native workflow.

    Parameters
    ----------
    context
        Injected immutable application state.
    request
        Typed workflow variant selected by workflowName.

    Returns
    -------
    ToolResult
        Canonical JSON text and structured content within both envelope ceilings.
    """

    with tool_error_boundary("get_workflow_instructions"):
        result = render_workflow_instructions(
            prompt_service=get_app_state(context).prompt_service, request=request
        )
        tool_result = build_tool_result(
            content=canonical_result_text(result), result=result
        )
        emitted = CallToolResult(
            _meta=tool_result.meta,
            content=tool_result.content,
            isError=tool_result.is_error,
            structuredContent=tool_result.structured_content,
        )
        _require_size(emitted.model_dump(by_alias=True, exclude_none=True, mode="json"))
        return tool_result


def register_workflow_tools(server: FastMCP[dict[str, AppState]]) -> None:
    """Register the workflow-instructions tool with its exact variant schemas.

    Parameters
    ----------
    server
        Application server receiving the approved adapter.
    """

    server.tool(
        annotations=READ_ONLY_TOOL_ANNOTATIONS,
        description=(
            "Get the complete instructions of one native prompt workflow for clients "
            "that only use tools. request.workflowName selects one of: "
            "learning_progression_teaching_sequence, "
            "learning_progression_support_plan, "
            "learning_progression_curriculum_review, teacher_guide_draft, "
            "student_study_support, student_handbook_section, multigrade_lesson_plan. "
            "The other fields are that prompt's arguments in camelCase with the same "
            "defaults; send arrays and selector objects as JSON values. The server "
            "does not run the workflow: follow rendered.message."
        ),
        name="get_workflow_instructions",
        output_schema=result_schema(WorkflowInstructionsResult),
        title="Get Workflow Instructions",
    )(get_workflow_instructions)
