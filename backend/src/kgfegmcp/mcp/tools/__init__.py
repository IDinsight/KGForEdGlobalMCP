"""This package provides shared infrastructure for the canonical read-only FastMCP
tools.

This package is the thin protocol-facing layer between FastMCP and the application's
ordinary services. Its modules receive validated MCP requests, retrieve the immutable
application state created by the server lifespan, call the appropriate service, and
return deterministic human-readable and structured results.

The shared helpers in this module define the common read-only tool annotations,
retrieve and validate lifespan application state, generate result schemas, and build
FastMCP results containing both text and structured evidence.

This package does not implement catalog routing, package selection, search, filtering,
ranking, code normalization, cursor handling, graph traversal, statistics, package
loading, or validation. Those responsibilities remain in the ordinary application
services and domain modules.
"""

# Standard Library
from typing import Any

# Third Party Library
from fastmcp import Context
from fastmcp.tools.base import ToolResult
from mcp.types import ToolAnnotations

# Package Library
from kgfegmcp.bootstrap import AppState
from kgfegmcp.schemas import FrozenSchema

READ_ONLY_TOOL_ANNOTATIONS = ToolAnnotations(
    destructiveHint=False, idempotentHint=True, openWorldHint=False, readOnlyHint=True
)


def build_tool_result(*, content: str, result: FrozenSchema) -> ToolResult:
    """Build one deterministic FastMCP result with text and structured evidence.

    Parameters
    ----------
    content
        Deterministic human-readable summary of the complete structured result.
    result
        Immutable Pydantic result model serialized through its public aliases.

    Returns
    -------
    ToolResult
        FastMCP result containing both text content and structured JSON content.
    """

    return ToolResult(
        content=content,
        structured_content=result.model_dump(by_alias=True, mode="json"),
    )


def get_app_state(context: Context) -> AppState:
    """Return the exact immutable application state from the FastMCP lifespan.

    Parameters
    ----------
    context
        Injected FastMCP request context.

    Returns
    -------
    AppState
        Application state constructed once by ``app_lifespan``.

    Raises
    ------
    RuntimeError
        If the expected state is absent or has an unexpected runtime type.
    """

    try:
        state = context.lifespan_context["state"]
    except KeyError as error:
        raise RuntimeError(
            "FastMCP lifespan context does not contain application state."
        ) from error

    if not isinstance(state, AppState):
        raise RuntimeError("FastMCP lifespan state is not an AppState instance.")

    return state


def result_schema(model: type[FrozenSchema]) -> dict[str, Any]:
    """Generate the exact serialization schema registered for one tool result.

    Parameters
    ----------
    model
        Immutable Pydantic result model exposed by the tool.

    Returns
    -------
    dict[str, Any]
        Complete JSON schema using the models' public camel-case aliases.
    """

    return model.model_json_schema(by_alias=True, mode="serialization")
