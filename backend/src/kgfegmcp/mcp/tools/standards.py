"""This module exposes canonical standards search and exact lookup as FastMCP tools.

This module implements and registers the ``search_standards`` and ``get_standard`` MCP
tools. The adapters retrieve immutable application state, construct the ordinary
framework and standards services, delegate the requested operation, and return
deterministic human-readable evidence alongside the complete structured result.

The module may format or truncate text for display, but it does not select packages,
normalize codes, tokenize text, apply filters, rank results, construct, decode, or
validate search cursors, resolve identifier namespaces, inspect graph stores, or
calculate facet evidence. Those responsibilities remain in the existing framework,
standards, search, catalog, and graph services.
"""

# Future Library
from __future__ import annotations

# Standard Library
from typing import TYPE_CHECKING

# Third Party Library
from fastmcp import Context
from fastmcp.tools.base import ToolResult

# Package Library
from kgfegmcp.mcp.errors import tool_error_boundary
from kgfegmcp.mcp.tools import (
    READ_ONLY_TOOL_ANNOTATIONS,
    SharedHitLines,
    build_request_continuation_text,
    build_tool_result,
    catalog_package,
    format_matched_fields,
    format_score,
    get_app_state,
    hit_warning_legend,
    page_warning_lines,
    result_schema,
    shared_hit_header_lines,
    shared_line,
    standard_resource_links,
)
from kgfegmcp.search.models import SearchMode
from kgfegmcp.services.frameworks import FrameworkService
from kgfegmcp.services.models import (
    GetStandardRequest,
    GetStandardResult,
    SearchStandardsResult,
    StandardsSearchRequest,
)
from kgfegmcp.services.standards import StandardsService

if TYPE_CHECKING:
    # Third Party Library
    from fastmcp import FastMCP

    # Package Library
    from kgfegmcp.bootstrap import AppState
    from kgfegmcp.search.models import (
        CodeMatchEvidence,
        SearchFacetEvidence,
        SearchHit,
    )


_LEXICAL_ZERO_RESULT_GUIDANCE = (
    "Recovery hint: preserve the original query, then consider a small number of "
    "conservative inflectional, orthographic, or retrieved local-terminology "
    "variants under the same filters. Zero matches establish only that this exact "
    "query did not match the retained descriptions; they do not establish "
    "curriculum absence."
)
_SEARCH_INTERPRETATION = (
    "Hits are retrieval candidates; a match, grade, or placement does not by itself "
    "establish equivalence, mastery, prerequisites, progression, or difficulty."
)
_STANDARD_INTERPRETATION = (
    "Source-backed curriculum evidence; its presence or placement does not by itself "
    "establish mastery, prerequisites, progression, difficulty, or equivalence."
)


def _collapse_whitespace(value: str) -> str:
    """Collapse whitespace for deterministic human-readable summaries only.

    Parameters
    ----------
    value
        Exact source text retained unchanged in the structured result.

    Returns
    -------
    str
        Single-line display text without modifying structured source evidence.
    """

    return " ".join(value.split())


def _format_boolean(value: bool) -> str:
    """Format one boolean as deterministic lower-case text.

    Parameters
    ----------
    value
        Boolean value to format.

    Returns
    -------
    str
        ``true`` or ``false``.
    """

    return str(value).lower()


def _format_facets(facets: SearchFacetEvidence) -> list[str]:
    """Format source and normalized facet evidence without changing either form.

    Parameters
    ----------
    facets
        Package-local source and normalized facets calculated by the search service.

    Returns
    -------
    list[str]
        Stable line-oriented facet evidence.
    """

    return [
        f"Statement type: {_format_optional_value(facets.statement_type)}",
        (
            f"Normalized statement type: "
            f"{_format_optional_value(facets.normalized_statement_type)}"
        ),
        (
            f"Resolved local grade labels: "
            f"{_format_values(tuple(facets.resolved_local_grade_labels))}"
        ),
        f"Node grade levels: {_format_values(tuple(facets.node_grade_levels))}",
        f"Normalized grades: {_format_values(tuple(facets.normalized_grades))}",
        f"Local subject: {_format_optional_value(facets.local_subject)}",
        (f"Normalized subjects: {_format_values(tuple(facets.normalized_subjects))}"),
    ]


def _format_code_match(code_match: CodeMatchEvidence) -> str:
    """Render the code evidence of one code-mode hit on one line.

    Parameters
    ----------
    code_match
        Authored and normalized code, code type, scopes, and parent derivations.

    Returns
    -------
    str
        Compact code-match evidence naming any code scope, such as a Class.
    """

    text = (
        f"{code_match.authored_code} ({code_match.code_type}), normalized "
        f"{code_match.normalized_code}"
    )

    if code_match.scopes:
        scopes = "; ".join(
            scope.scope_node.description or str(scope.scope_node.node_id)
            for scope in code_match.scopes
        )
        text += f", scope {scopes}"

    if code_match.parent_derivations:
        text += f", parent derivations {len(code_match.parent_derivations)}"

    return text


def _format_grade(facets: SearchFacetEvidence) -> str:
    """Render local, normalized, and differing node grade evidence on one line.

    Parameters
    ----------
    facets
        Package-local source and normalized facets of one hit.

    Returns
    -------
    str
        Local grade labels with normalized grades, plus node grades when they differ.
    """

    grade = (
        f"{_format_values(tuple(facets.resolved_local_grade_labels))} "
        f"(normalized: {_format_values(tuple(facets.normalized_grades))}"
    )

    if tuple(facets.node_grade_levels) != tuple(facets.normalized_grades):
        grade += f"; node: {_format_values(tuple(facets.node_grade_levels))}"

    return f"{grade})"


def _format_subject(facets: SearchFacetEvidence) -> str:
    """Render the local and normalized subject of one hit.

    Parameters
    ----------
    facets
        Package-local source and normalized facets of one hit.

    Returns
    -------
    str
        Local subject with normalized subjects.
    """

    return (
        f"{_format_optional_value(facets.local_subject)} "
        f"(normalized: {_format_values(tuple(facets.normalized_subjects))})"
    )


def _format_optional_value(value: object | None) -> str:
    """Format one optional value without inventing missing metadata.

    Parameters
    ----------
    value
        Source or package value that may be absent.

    Returns
    -------
    str
        Exact string representation or ``none`` when the value is absent.
    """

    return "none" if value is None else str(value)


def _format_search_hit(
    *, hit: SearchHit, index: int, shared: SharedHitLines
) -> list[str]:
    """Format one search hit, leaving out the lines its page states once.

    Parameters
    ----------
    hit
        Node projection, facets, match evidence, score, and warnings of one hit.
    index
        One-based display position within the returned page.
    shared
        Lines every hit on the page shares, already printed in the page header.

    Returns
    -------
    list[str]
        Stable line-oriented search-hit evidence.
    """

    node = hit.node
    description = _truncate_display_text(
        limit=240, value=_collapse_whitespace(node.description or "[no description]")
    )
    statement_type = (
        f"{_format_optional_value(hit.facets.statement_type)} "
        f"({_format_optional_value(hit.facets.normalized_statement_type)})"
    )
    lines = [
        f"{index}. Standard: {node.statement_code or '[uncoded]'} | "
        f"Node ID: {node.node_id}",
        f"   Description: {description}",
        f"   Type: {statement_type} | Grade: {_format_grade(hit.facets)}",
    ]

    if shared.subject is None:
        lines.append(f"   Subject: {_format_subject(hit.facets)}")

    if shared.match is None:
        lines.append(f"   Matched: {format_matched_fields(hit.matched_fields)}")

    if shared.score is None:
        lines.append(f"   Score: {format_score(hit.score)}")

    if hit.code_match is not None:
        lines.append(f"   Code match: {_format_code_match(hit.code_match)}")

    if shared.multi_package:
        lines.append(f"   Package: {hit.graph_package_id}")

    if hit.warnings:
        codes = tuple(warning.code.value for warning in hit.warnings)
        lines.append(f"   Hit warnings: {_format_values(codes)}")

    return lines


def _format_search_result(result: SearchStandardsResult) -> str:
    """Format one standards search page as deterministic readable evidence.

    Package identity, retrieval method, and epistemic status hold for the whole page
    and are stated once; so is any subject, match, or score every hit shares.

    Parameters
    ----------
    result
        Complete search result including the selected packages and their hits.

    Returns
    -------
    str
        Stable summary of packages, hits, facets, matches, warnings, and cursor state.
    """

    page = result.page
    package_ids = tuple(
        str(identity.graph_package_id) for identity in result.selected_packages
    )
    shared = SharedHitLines(
        match=shared_line(
            tuple(format_matched_fields(hit.matched_fields) for hit in page.hits)
        ),
        multi_package=len(package_ids) > 1,
        score=shared_line(tuple(format_score(hit.score) for hit in page.hits)),
        subject=shared_line(tuple(_format_subject(hit.facets) for hit in page.hits)),
    )
    lines = [
        f"Search mode: {page.mode.value} | Epistemic status: {page.epistemic_status}",
        f"Selected packages: {_format_values(package_ids)}",
        f"Returned hits: {page.returned_count} | "
        f"Has more: {_format_boolean(page.has_more)}",
        *shared_hit_header_lines(shared),
    ]

    if page.mode is SearchMode.TEXT and page.returned_count == 0:
        lines.append(_LEXICAL_ZERO_RESULT_GUIDANCE)

    lines.append(f"Interpretation: {_SEARCH_INTERPRETATION}")

    for index, hit in enumerate(page.hits, start=1):
        lines.extend(("", *_format_search_hit(hit=hit, index=index, shared=shared)))

    lines.extend(
        (
            "",
            *page_warning_lines(page.warnings),
            *hit_warning_legend(
                tuple(warning for hit in page.hits for warning in hit.warnings)
            ),
        )
    )

    if page.has_more:
        lines.append("Continuation: see the MCP continuation block below.")

    return "\n".join(lines)


def _format_standard(result: GetStandardResult) -> str:
    """Format one exact standard record as deterministic readable evidence.

    Parameters
    ----------
    result
        Complete standard lookup result with package, source, and facet evidence.

    Returns
    -------
    str
        Stable source-facing evidence without altering exact structured values.
    """

    node = result.node
    identity = result.package.package_identity
    source_metadata = result.source_metadata
    lines = [
        f"Standard: {node.statement_code or '[uncoded]'}",
        f"Node ID: {node.node_id}",
        f"CASE UUID: {node.case_identifier_uuid or 'none'}",
        f"CASE URI: {node.case_identifier_uri or 'none'}",
        f"Framework ID: {identity.framework_id}",
        f"Snapshot ID: {identity.snapshot_id}",
        f"Package: {identity.graph_package_id}",
        f"Graph type: {identity.graph_type.value}",
        f"Profile: {identity.profile_id}@{identity.profile_version}",
        *_format_facets(result.facets),
        f"Node language: {_format_optional_value(node.in_language)}",
        f"Framework languages: {_format_values(tuple(source_metadata.languages))}",
        (
            f"Issuing authority: "
            f"{_format_optional_value(source_metadata.issuing_authority)}"
        ),
        f"Adoption status: {_format_optional_value(source_metadata.adoption_status)}",
        f"Node author: {_format_optional_value(node.author)}",
        f"Node provider: {_format_optional_value(node.provider)}",
        f"Node attribution: {_format_optional_value(node.attribution_statement)}",
        f"Package attribution: {result.package.rights.attribution_statement}",
        f"Node license: {_format_optional_value(node.license)}",
        f"Package source license: {result.package.rights.source_license}",
        "Description:",
        node.description or "[no description]",
        "",
        f"Interpretation: {_STANDARD_INTERPRETATION}",
    ]
    return "\n".join(lines)


def _format_values(values: tuple[object, ...]) -> str:
    """Format one ordered tuple while preserving its source order.

    Parameters
    ----------
    values
        Ordered values to render.

    Returns
    -------
    str
        Comma-separated exact values or ``none`` for an empty tuple.
    """

    return ", ".join(str(value) for value in values) or "none"


def _standards_service(state: AppState) -> StandardsService:
    """Construct one stateless standards orchestrator over retained application data.

    Parameters
    ----------
    state
        Immutable application state created by the FastMCP lifespan.

    Returns
    -------
    StandardsService
        Stateless ordinary service delegating to retained domain services.
    """

    framework_service = FrameworkService(catalog_service=state.catalog_service)
    return StandardsService(
        catalog_service=state.catalog_service,
        framework_service=framework_service,
        search_service=state.search_service,
    )


def _truncate_display_text(*, limit: int, value: str) -> str:
    """Truncate display-only text deterministically at a Unicode character limit.

    Parameters
    ----------
    limit
        Maximum number of characters in the display string.
    value
        Whitespace-collapsed display text.

    Returns
    -------
    str
        Original value when short enough, otherwise an ellipsis-terminated prefix.
    """

    if len(value) <= limit:
        return value

    return f"{value[: max(limit - 1, 0)]}…"


async def get_standard(request: GetStandardRequest, context: Context) -> ToolResult:
    """Return one exact package-local standard through an explicit identifier namespace.

    Parameters
    ----------
    request
        Exact framework or snapshot route and typed standard identifier.
    context
        Injected FastMCP request context containing immutable application state.

    Returns
    -------
    ToolResult
        Human-readable summary and complete ``GetStandardResult`` evidence.
    """

    with tool_error_boundary("get_standard"):
        state = get_app_state(context)
        result = _standards_service(state).get_standard(request)
        resource_links = standard_resource_links(
            node=result.node,
            package=catalog_package(result.package.package_identity, state),
            state=state,
        )
        return build_tool_result(
            content=_format_standard(result),
            resource_links=resource_links,
            result=result,
        )


def register_standard_tools(server: FastMCP[dict[str, AppState]]) -> None:
    """Register canonical standards search and exact lookup tools.

    Parameters
    ----------
    server
        FastMCP server receiving explicitly approved read-only tools.
    """

    server.tool(
        annotations=READ_ONLY_TOOL_ANNOTATIONS,
        description=(
            "Search accepted standards with package-governed modes. A request variant "
            "present in this generic schema may be unavailable for the selected "
            "package; inspect get_capabilities packages[].implementedSearchModes "
            "before using code_exact or code_prefix. Text mode matches exact "
            "normalized description tokens or contiguous normalized phrases and "
            "performs no stemming or synonym expansion. For concept discovery, search "
            "the caller's original wording first; when recall is visibly narrow, make "
            "a small number of separate conservative variant calls with the same filters. "
            "Each hit gives the node ID, statement code, source wording, local and "
            "normalized facets, matched fields, score, and hit warnings, without "
            "progression inference; package identity, retrieval method, and epistemic "
            "status are stated once per page, and the complete record is one "
            "get_standard call away. For continuation, submit the provided nextRequest "
            "unchanged; only its opaque cursor differs from the previous request. A "
            "zero-match page does not establish curriculum absence."
        ),
        name="search_standards",
        output_schema=result_schema(SearchStandardsResult),
        title="Search Standards",
    )(search_standards)
    server.tool(
        annotations=READ_ONLY_TOOL_ANNOTATIONS,
        description=(
            "Return one exact standard by node ID, CASE UUID, or CASE URI with source "
            "wording, statement type, local and normalized grades, language, "
            "attribution, license, and immutable package provenance."
        ),
        name="get_standard",
        output_schema=result_schema(GetStandardResult),
        title="Get Standard",
    )(get_standard)


async def search_standards(
    request: StandardsSearchRequest, context: Context
) -> ToolResult:
    """Search standards through existing package-local indexes and cursor semantics.

    Parameters
    ----------
    request
        Discriminated server-level text, exact-code, or prefix-code request shape.
        Package-specific mode availability remains governed by the selected profile and
        is reported by ``get_capabilities``.
    context
        Injected FastMCP request context containing immutable application state.

    Returns
    -------
    ToolResult
        Human-readable summary and complete ``SearchStandardsResult`` evidence.
    """

    with tool_error_boundary("search_standards"):
        state = get_app_state(context)
        result = _standards_service(state).search_standards(request)
        continuation_text = build_request_continuation_text(
            cursor_field="cursor",
            has_more=result.page.has_more,
            next_cursor=(
                result.page.next_cursor.root
                if result.page.next_cursor is not None
                else None
            ),
            request=request,
            tool_name="search_standards",
        )
        return build_tool_result(
            additional_text=(
                (continuation_text,) if continuation_text is not None else ()
            ),
            content=_format_search_result(result),
            result=result,
        )
