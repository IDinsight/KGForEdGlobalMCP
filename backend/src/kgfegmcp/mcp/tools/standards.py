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
    build_continuation_text,
    build_tool_result,
    get_app_state,
    result_schema,
    standard_resource_links,
)
from kgfegmcp.search.models import ExactPackageSearchScope, SearchMode
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
        SearchFacetEvidence,
        SearchHit,
        SearchMatchedField,
        SearchWarning,
    )


_LEXICAL_SEARCH_SEMANTICS = (
    "Lexical semantics: text mode matches exact normalized description tokens or "
    "a contiguous normalized phrase. It performs no stemming, lemmatization, "
    "fuzzy matching, or synonym expansion."
)
_LEXICAL_ZERO_RESULT_GUIDANCE = (
    "Recovery hint: preserve the original query, then consider a small number of "
    "conservative inflectional, orthographic, or retrieved local-terminology "
    "variants under the same filters. Zero matches establish only that this exact "
    "query did not match the retained descriptions; they do not establish "
    "curriculum absence."
)
_SEARCH_INTERPRETATION = (
    "Search hits are deterministic retrieval candidates. Lexical or code matches, "
    "normalized grades, grade order, and hierarchy placement do not by themselves "
    "establish official equivalence, learner mastery, prerequisites, instructional "
    "progression, or difficulty."
)
_STANDARD_INTERPRETATION = (
    "This record is source-backed curriculum evidence. Its presence or structural "
    "placement does not by itself establish learner mastery, prerequisites, "
    "instructional progression, difficulty, or official equivalence."
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


def _format_matched_field(field: SearchMatchedField) -> str:
    """Format one exact source field that produced a deterministic search match.

    Parameters
    ----------
    field
        Exact field, matched terms, phrase flag, and retained source value.

    Returns
    -------
    str
        Stable compact match-evidence line.
    """

    source_value = _truncate_display_text(
        limit=240, value=_collapse_whitespace(field.source_value)
    )
    return (
        f"{field.field.value} | matched_terms="
        f"{_format_values(tuple(field.matched_terms))} | "
        f"phrase_matched={_format_boolean(field.phrase_matched)} | "
        f"source_value={source_value}"
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


def _format_search_hit(*, hit: SearchHit, index: int) -> list[str]:
    """Format one deterministic search hit with its complete practical evidence.

    Parameters
    ----------
    hit
        Exact source node, package identity, facets, score, and match evidence.
    index
        One-based display position within the returned page.

    Returns
    -------
    list[str]
        Stable line-oriented search-hit evidence.
    """

    node = hit.node
    description = _truncate_display_text(
        limit=240, value=_collapse_whitespace(node.description or "[no description]")
    )
    lines = [
        f"{index}. Standard: {node.statement_code or '[uncoded]'}",
        f"   Node ID: {node.node_id}",
        f"   Package: {hit.package_identity.graph_package_id}",
        f"   Framework ID: {hit.package_identity.framework_id}",
        f"   Snapshot ID: {hit.package_identity.snapshot_id}",
        f"   Description: {description}",
    ]
    lines.extend(f"   {line}" for line in _format_facets(hit.facets))
    lines.extend(
        (
            f"   Retrieval method: {hit.retrieval_method.value}",
            f"   Epistemic status: {hit.epistemic_status}",
            (
                f"   Score: "
                f"value={hit.score.value}, algorithm={hit.score.algorithm.value}, "
                f"matched_terms={hit.score.matched_term_count}/"
                f"{hit.score.query_term_count}, "
                f"phrase_matched={_format_boolean(hit.score.phrase_matched)}"
            ),
            f"   Matched terms: {_format_values(tuple(hit.matched_terms))}",
            "   Matched fields:",
        )
    )
    lines.extend(f"   - {_format_matched_field(field)}" for field in hit.matched_fields)

    if hit.code_match is not None:
        lines.extend(
            (
                (
                    f"   Code match: "
                    f"authored={hit.code_match.authored_code}, "
                    f"normalized={hit.code_match.normalized_code}, "
                    f"type={hit.code_match.code_type}"
                ),
                f"   Code scopes returned: {len(hit.code_match.scopes)}",
                (
                    f"   Parent-code derivations returned: "
                    f"{len(hit.code_match.parent_derivations)}"
                ),
            )
        )

    if hit.warnings:
        lines.append("   Hit warnings:")
        lines.extend(f"   - {_format_warning(warning)}" for warning in hit.warnings)
    else:
        lines.append("   Hit warnings: none")

    return lines


def _format_search_result(result: SearchStandardsResult) -> str:
    """Format one standards search page as deterministic readable evidence.

    Parameters
    ----------
    result
        Complete search result including selected snapshots and package-local hits.

    Returns
    -------
    str
        Stable summary of packages, hits, facets, matches, warnings, and cursor state.
    """

    scope = result.effective_scope
    graph_types = (
        (scope.graph_type,)
        if isinstance(scope, ExactPackageSearchScope)
        else scope.graph_types
    )
    package_ids = tuple(
        dict.fromkeys(
            str(package.package_identity.graph_package_id)
            for snapshot in result.selected_snapshots
            for package in snapshot.graph_packages
            if package.package_identity.graph_type in graph_types
        )
    )
    lines = [
        f"Search mode: {result.page.mode.value}",
        f"Selected packages: {_format_values(package_ids)}",
        f"Returned hits: {result.page.returned_count}",
        f"Has more: {_format_boolean(result.page.has_more)}",
    ]

    if result.page.mode is SearchMode.TEXT:
        lines.append(_LEXICAL_SEARCH_SEMANTICS)

        if result.page.returned_count == 0:
            lines.append(_LEXICAL_ZERO_RESULT_GUIDANCE)

    lines.extend(("", f"Interpretation: {_SEARCH_INTERPRETATION}"))

    for index, hit in enumerate(result.page.hits, start=1):
        lines.extend(("", *_format_search_hit(hit=hit, index=index)))

    lines.extend(("", f"Page warnings: {len(result.page.warnings)}"))

    if result.page.warnings:
        lines.extend(
            f"- {_format_warning(warning)}" for warning in result.page.warnings
        )
    else:
        lines.append("- none")

    lines.append("Continuation data: see the following MCP continuation block.")
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


def _format_warning(warning: SearchWarning) -> str:
    """Format one deterministic search warning with exact package provenance.

    Parameters
    ----------
    warning
        Capability or data-evidence warning produced by the search service.

    Returns
    -------
    str
        Stable warning code, package, optional node, and message.
    """

    return (
        f"{warning.code.value} | package="
        f"{warning.package_identity.graph_package_id} | "
        f"node={_format_optional_value(warning.node_id)} | {warning.message}"
    )


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
            node=result.node, package=result.package, state=state
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
            "Search accepted standards using deterministic lexical, exact-code, or "
            "prefix-code indexes. Text mode matches exact normalized description "
            "tokens or contiguous normalized phrases and performs no stemming or "
            "synonym expansion. For concept discovery, search the caller's original "
            "wording first; when recall is visibly narrow, make a small number of "
            "separate conservative variant calls with the same filters. Return exact "
            "source nodes, package provenance, local and normalized facets, matched "
            "fields and terms, warnings, epistemic status, and established cursor "
            "evidence without progression inference. A zero-match page does not "
            "establish curriculum absence."
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
        Discriminated text, exact-code, or prefix-code search request.
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
        continuation_text = build_continuation_text(
            {
                "continuationTool": "search_standards",
                "cursorField": "cursor",
                "hasMore": result.page.has_more,
                "nextCursor": (
                    result.page.next_cursor.root
                    if result.page.next_cursor is not None
                    else None
                ),
            }
        )
        return build_tool_result(
            additional_text=(continuation_text,),
            content=_format_search_result(result),
            result=result,
        )
