"""Provide shared FastMCP adapters for read-only resources.

The helpers in this package convert ordinary resource documents into explicit FastMCP
resource results and retrieve the immutable lifespan state. They do not route catalog
requests, select packages, enforce rights, read artifacts, or serialize domain models.
"""

# Third Party Library
from fastmcp import Context
from fastmcp.resources import ResourceContent, ResourceResult

# Package Library
from kgfegmcp.bootstrap import AppState
from kgfegmcp.resources.models import ResourceDocument


def build_resource_result(document: ResourceDocument) -> ResourceResult:
    """Convert one ordinary resource document into an explicit FastMCP result.

    Parameters
    ----------
    document
        Exact raw or deterministic derived resource returned by ``ResourceService``.

    Returns
    -------
    ResourceResult
        One content item with exact MIME type and public resource metadata.
    """

    metadata = document.metadata.model_dump(by_alias=True, mode="json")
    content = ResourceContent(
        content=document.content, meta=metadata, mime_type=document.metadata.mime_type
    )
    return ResourceResult(contents=[content], meta=metadata)


def get_resource_state(context: Context) -> AppState:
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


__all__ = ["build_resource_result", "get_resource_state"]
