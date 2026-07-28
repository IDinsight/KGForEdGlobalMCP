"""This package provides shared infrastructure for the canonical read-only FastMCP
tools.

This package is the thin protocol-facing layer between FastMCP and the application's
ordinary services. Its modules receive validated MCP requests, retrieve immutable
lifespan state, call the appropriate service, and return deterministic readable and
structured results. Optional resource links are derived from approved URI constructors
and never affect tool correctness.

This package does not implement catalog routing, package selection, search, filtering,
ranking, code normalization, cursor construction or validation, graph traversal,
statistics, package loading, validation, rights policy, or resource reads.
"""

# Standard Library
import json
import logging

from collections.abc import Mapping
from typing import Any

# Third Party Library
from fastmcp import Context
from fastmcp.tools.base import ToolResult
from mcp.types import ResourceLink, TextContent, ToolAnnotations

# Package Library
from kgfegmcp.bootstrap import AppState
from kgfegmcp.catalog.models import CatalogGraphPackage
from kgfegmcp.domain.identifiers import FrameworkId, SnapshotId
from kgfegmcp.errors import KGFEGMCPError
from kgfegmcp.graph.models import StandardNode
from kgfegmcp.resources.models import ResourceKind
from kgfegmcp.resources.uri import (
    CATALOG_URI,
    framework_uri,
    interpretation_profile_uri,
    manifest_uri,
    standard_provenance_uri,
    standard_uri,
    validation_uri,
)
from kgfegmcp.schemas import FrozenSchema

_LOGGER = logging.getLogger("fastmcp.kgfegmcp.mcp.tools")

READ_ONLY_TOOL_ANNOTATIONS = ToolAnnotations(
    destructiveHint=False, idempotentHint=True, openWorldHint=False, readOnlyHint=True
)


def _log_optional_link_failure(*, error: Exception, operation: str) -> None:
    """Log one optional link failure without exposing it through a tool result.

    Parameters
    ----------
    error
        Exception raised during optional link construction.
    operation
        Name of the operation that failed to construct optional links.
    """

    _LOGGER.warning(
        msg=(
            f"Optional resource-link construction failed without affecting the tool "
            f"result: error_type={type(error).__name__}, operation={operation}."
        )
    )


def build_continuation_text(payload: Mapping[str, object]) -> str:
    """Serialize model-visible continuation data as deterministic compact JSON.

    Cursor values remain opaque transport tokens. Callers must copy validated cursor
    strings into ``payload`` without truncation or transformation so MCP clients can
    pass them back unchanged.

    Parameters
    ----------
    payload
        JSON-serializable continuation state for one tool result.

    Returns
    -------
    str
        Stable model-visible continuation instructions and compact JSON data.
    """

    serialized = json.dumps(
        ensure_ascii=True, obj=payload, separators=(",", ":"), sort_keys=True
    )
    return (
        f"MCP continuation data. Cursor values are opaque; pass them back "
        f"unchanged:\n{serialized}"
    )


def build_resource_link(
    *, description: str, mime_type: str, name: str, title: str, uri: str
) -> ResourceLink:
    """Build one MCP resource link from an approved application URI.

    Parameters
    ----------
    description
        Human-readable explanation of the linked resource.
    mime_type
        Expected MIME type of the linked resource.
    name
        Stable programmatic link name.
    title
        Human-readable link title.
    uri
        URI built by an approved resource constructor.

    Returns
    -------
    ResourceLink
        Protocol content block linking to a readable server resource.
    """

    return ResourceLink(
        description=description,
        mimeType=mime_type,
        name=name,
        title=title,
        type="resource_link",
        uri=uri,
    )


def build_tool_result(
    *,
    additional_text: tuple[str, ...] = (),
    content: str,
    resource_links: tuple[ResourceLink, ...] = (),
    result: FrozenSchema,
) -> ToolResult:
    """Build one deterministic FastMCP result with text and structured evidence.

    Parameters
    ----------
    additional_text
        Optional model-visible text blocks containing protocol compatibility data.
    content
        Deterministic human-readable summary of the complete structured result.
    resource_links
        Optional readable links that remain non-critical to the domain result.
    result
        Immutable Pydantic result model serialized through its public aliases.

    Returns
    -------
    ToolResult
        Text, optional compatibility text, resource links, and structured JSON content.
    """

    ordered_resource_links = tuple(
        sorted(resource_links, key=lambda link: str(link.uri))
    )
    content_blocks = [
        TextContent(text=content, type="text"),
        *(TextContent(text=text, type="text") for text in additional_text),
        *ordered_resource_links,
    ]
    return ToolResult(
        content=content_blocks,
        structured_content=result.model_dump(by_alias=True, mode="json"),
    )


def catalog_resource_links() -> tuple[ResourceLink, ...]:
    """Return the fixed catalog link without making it tool-critical.

    Returns
    -------
    tuple[ResourceLink]
        Single link to the complete accepted package catalog.
    """

    try:
        return (
            build_resource_link(
                description="Read the complete accepted package catalog.",
                mime_type="application/json",
                name="catalog",
                title="Catalog",
                uri=CATALOG_URI,
            ),
        )
    except Exception as error:  # pylint: disable=W0718
        _log_optional_link_failure(error=error, operation="catalog_resource_links")
        return ()


def framework_resource_links(
    *, framework_id: FrameworkId, graph_package_count: int, snapshot_id: SnapshotId
) -> tuple[ResourceLink, ...]:
    """Build links for one framework snapshot without ambiguous package routing.

    Parameters
    ----------
    framework_id
        Exact conceptual framework identifier.
    graph_package_count
        Number of accepted graph packages in the selected snapshot.
    snapshot_id
        Exact immutable snapshot identifier.

    Returns
    -------
    tuple[ResourceLink, ...]
        Framework-family link and package links only when the snapshot is unambiguous.
    """

    try:
        links = [
            build_resource_link(
                description="Read the framework family and every accepted snapshot.",
                mime_type="application/json",
                name="framework",
                title="Framework",
                uri=framework_uri(framework_id),
            )
        ]

        if graph_package_count == 1:
            links.extend(
                (
                    build_resource_link(
                        description="Read exact accepted package-manifest bytes.",
                        mime_type="application/json",
                        name="package_manifest",
                        title="Package Manifest",
                        uri=manifest_uri(
                            framework_id=framework_id, snapshot_id=snapshot_id
                        ),
                    ),
                    build_resource_link(
                        description=(
                            "Read exact retained interpretation-profile bytes."
                        ),
                        mime_type="application/json",
                        name="interpretation_profile",
                        title="Interpretation Profile",
                        uri=interpretation_profile_uri(
                            framework_id=framework_id, snapshot_id=snapshot_id
                        ),
                    ),
                    build_resource_link(
                        description="Read exact accepted validation-report bytes.",
                        mime_type="application/json",
                        name="validation_report",
                        title="Validation Report",
                        uri=validation_uri(
                            framework_id=framework_id, snapshot_id=snapshot_id
                        ),
                    ),
                )
            )

        return tuple(sorted(links, key=lambda link: str(link.uri)))
    except Exception as error:  # pylint: disable=W0718
        _log_optional_link_failure(error=error, operation="framework_resource_links")
        return ()


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


def standard_resource_links(
    *, node: StandardNode, package: CatalogGraphPackage, state: AppState
) -> tuple[ResourceLink, ...]:
    """Build non-critical links for one exact standard result.

    Parameters
    ----------
    node
        Exact standard node returned by the ordinary standards service.
    package
        Exact accepted graph package owning the node.
    state
        Immutable application state providing shared policy and catalog routing.

    Returns
    -------
    tuple[ResourceLink, ...]
        Permitted exact-standard and optional provenance or manifest links.
    """

    identity = package.package_identity

    try:
        state.resource_service.policy.require_resource_access(
            resource_kind=ResourceKind.STANDARD, rights=package.rights
        )
        links = [
            build_resource_link(
                description="Read this exact standard with package and facet evidence.",
                mime_type="application/json",
                name="standard",
                title="Standard",
                uri=standard_uri(
                    framework_id=identity.framework_id,
                    node_id=node.node_id,
                    snapshot_id=identity.snapshot_id,
                ),
            )
        ]

        if package.capabilities.has_detailed_provenance and node.case_identifier_uuid:
            links.append(
                build_resource_link(
                    description="Read this standard's detailed provenance entry.",
                    mime_type="application/json",
                    name="standard_provenance",
                    title="Standard Provenance",
                    uri=standard_provenance_uri(
                        framework_id=identity.framework_id,
                        node_id=node.node_id,
                        snapshot_id=identity.snapshot_id,
                    ),
                )
            )

        snapshot = state.catalog_service.get_framework(
            framework_id=identity.framework_id, snapshot_id=identity.snapshot_id
        )

        if len(snapshot.graph_packages) == 1:
            links.append(
                build_resource_link(
                    description="Read exact accepted package-manifest bytes.",
                    mime_type="application/json",
                    name="package_manifest",
                    title="Package Manifest",
                    uri=manifest_uri(
                        framework_id=identity.framework_id,
                        snapshot_id=identity.snapshot_id,
                    ),
                )
            )
    except KGFEGMCPError:
        return ()
    except Exception as error:  # pylint: disable=W0718
        _log_optional_link_failure(
            error=error,
            operation="standard_resource_links:" f"{identity.graph_package_id}",
        )
        return ()

    return tuple(sorted(links, key=lambda link: str(link.uri)))
