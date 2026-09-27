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
from dataclasses import dataclass
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
from kgfegmcp.graph.models import GraphPackageIdentity, StandardNode
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
from kgfegmcp.search.models import SearchMatchedField, SearchScore, SearchWarning

_LOGGER = logging.getLogger("fastmcp.kgfegmcp.mcp.tools")

READ_ONLY_TOOL_ANNOTATIONS = ToolAnnotations(
    destructiveHint=False, idempotentHint=True, openWorldHint=False, readOnlyHint=True
)


def log_optional_link_failure(*, error: Exception, operation: str) -> None:
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
        f"MCP continuation data. Submit each nextRequest unchanged to the "
        f"continuationTool; cursor values are opaque:\n{serialized}"
    )


def catalog_package(
    identity: GraphPackageIdentity, state: AppState
) -> CatalogGraphPackage:
    """Return the accepted catalog package a result names.

    Results carry only a package's identity and rights; resource-link policy also
    needs its capabilities, so the adapter reads the accepted package once.

    Parameters
    ----------
    identity
        Exact graph-package identity reported by a result.
    state
        Immutable application state created by the FastMCP lifespan.

    Returns
    -------
    CatalogGraphPackage
        The accepted package with capabilities, counts, and rights.
    """

    return state.catalog_service.get_graph_package(
        framework_id=identity.framework_id,
        graph_type=identity.graph_type,
        snapshot_id=identity.snapshot_id,
    )


def build_request_continuation_text(
    *,
    cursor_field: str,
    has_more: bool,
    next_cursor: str | None,
    request: FrozenSchema,
    tool_name: str,
) -> str | None:
    """Build model-visible replay data for the next page of a paginated result.

    The returned ``nextRequest`` is the complete replay request with only the opaque
    cursor replaced. Fields left at their defaults are omitted because the tool fills
    them identically, so the replayed request selects exactly the same page sequence.

    Parameters
    ----------
    cursor_field
        Public request-field alias that carries the opaque continuation cursor.
    has_more
        Whether another deterministic page is available.
    next_cursor
        Opaque cursor for the next page, or ``None`` when pagination is complete.
    request
        Complete validated request that produced the current page.
    tool_name
        Public MCP tool name that accepts the replay request.

    Returns
    -------
    str | None
        Instructions and compact JSON containing ``nextRequest``, or ``None`` on the
        last page.

    Raises
    ------
    ValueError
        If continuation state is inconsistent or the request lacks ``cursor_field``.
    """

    if has_more != (next_cursor is not None):
        raise ValueError("has_more and next_cursor must agree.")

    if cursor_field not in request.model_dump(by_alias=True, mode="json"):
        raise ValueError(
            f"The continuation request does not define cursor field {cursor_field!r}."
        )

    if next_cursor is None:
        return None

    next_request: dict[str, Any] = request.model_dump(
        by_alias=True, exclude_defaults=True, mode="json"
    )
    next_request[cursor_field] = next_cursor
    serialized = json.dumps(
        ensure_ascii=True,
        obj={"continuationTool": tool_name, "nextRequest": next_request},
        separators=(",", ":"),
        sort_keys=True,
    )
    return (
        f"MCP continuation data. Submit nextRequest unchanged as the next "
        f"{tool_name} request; only its opaque cursor differs:\n{serialized}"
    )


@dataclass(frozen=True, slots=True)
class SharedHitLines:
    """Carry the hit lines a search page states once instead of on every hit.

    A line that differs between hits is ``None`` here and is printed per hit.
    """

    match: str | None
    multi_package: bool
    score: str | None
    subject: str | None = None


def shared_line(lines: tuple[str, ...]) -> str | None:
    """Return the one rendered line every hit shares.

    Parameters
    ----------
    lines
        One rendered line per hit, in page order.

    Returns
    -------
    str | None
        The shared line, or ``None`` when hits differ or the page is empty.
    """

    distinct = tuple(dict.fromkeys(lines))
    return distinct[0] if len(distinct) == 1 else None


def shared_hit_header_lines(shared: SharedHitLines) -> list[str]:
    """Render the per-hit lines a page states once in its header.

    Parameters
    ----------
    shared
        Lines every hit on the page shares.

    Returns
    -------
    list[str]
        Header lines for the shared subject, match, and score, when present.
    """

    lines: list[str] = []

    if shared.subject is not None:
        lines.append(f"Subject (every hit): {shared.subject}")

    if shared.match is not None:
        lines.append(f"Matched (every hit): {shared.match}")

    if shared.score is not None:
        lines.append(f"Score (every hit): {shared.score}")

    return lines


def format_matched_fields(fields: tuple[SearchMatchedField, ...]) -> str:
    """Render the matched fields of one hit on one line.

    Parameters
    ----------
    fields
        Exact matched-field evidence of one hit.

    Returns
    -------
    str
        Field, matched terms, and phrase flag per field.
    """

    return "; ".join(
        f"{field.field.value} | terms: {', '.join(field.matched_terms)} | "
        f"phrase: {str(field.phrase_matched).lower()}"
        for field in fields
    )


def format_score(score: SearchScore) -> str:
    """Render one deterministic search score on one line.

    Parameters
    ----------
    score
        Exact integer score and its algorithm.

    Returns
    -------
    str
        Value, algorithm, term coverage, and phrase flag.
    """

    return (
        f"value={score.value}, algorithm={score.algorithm.value}, "
        f"matched_terms={score.matched_term_count}/{score.query_term_count}, "
        f"phrase_matched={str(score.phrase_matched).lower()}"
    )


def page_warning_lines(warnings: tuple[SearchWarning, ...]) -> list[str]:
    """Render package-level search warnings, or one line saying there are none.

    Parameters
    ----------
    warnings
        Package-level warnings of one search page.

    Returns
    -------
    list[str]
        Warning lines naming code, package, optional node, and message.
    """

    if not warnings:
        return ["Page warnings: none"]

    return [
        "Page warnings:",
        *(
            f"- {warning.code.value} | package={warning.graph_package_id} | "
            f"node={warning.node_id or 'none'} | {warning.message}"
            for warning in warnings
        ),
    ]


def hit_warning_legend(warnings: tuple[SearchWarning, ...]) -> list[str]:
    """Render each distinct hit-warning message once for the whole page.

    Hits list only their warning codes; the message behind each code is stated here.

    Parameters
    ----------
    warnings
        Every hit-level warning on the page, in hit order.

    Returns
    -------
    list[str]
        Heading and one line per distinct code and message, or nothing.
    """

    meanings = tuple(
        dict.fromkeys(
            f"- {warning.code.value}: {warning.message}" for warning in warnings
        )
    )
    return ["Hit warning meanings:", *meanings] if meanings else []


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
        log_optional_link_failure(error=error, operation="catalog_resource_links")
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
        log_optional_link_failure(error=error, operation="framework_resource_links")
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
        log_optional_link_failure(
            error=error,
            operation="standard_resource_links:" f"{identity.graph_package_id}",
        )
        return ()

    return tuple(sorted(links, key=lambda link: str(link.uri)))
