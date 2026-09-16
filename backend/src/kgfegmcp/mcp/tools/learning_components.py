"""This module registers read-only learning-component search and lookup tools.

Learning components are model-generated decompositions of published standards. They are
kept separate from standards at every level, so these tools never return a standards
node in place of a component, and never present generated content as source-asserted
curriculum.

The tools in this module search components by description, controlled tag, or the
statement codes of the standards they support, return one exact component, and traverse
the ``supports`` relationship in both directions. They do not validate packages, read
files, build indexes, or infer instructional sequence.
"""

# Future Library
from __future__ import annotations

# Standard Library
from typing import TYPE_CHECKING

# Third Party Library
from fastmcp import Context
from fastmcp.tools.base import ToolResult

# Package Library
from kgfegmcp.errors import KGFEGMCPError
from kgfegmcp.mcp.errors import tool_error_boundary
from kgfegmcp.mcp.tools import (
    READ_ONLY_TOOL_ANNOTATIONS,
    build_request_continuation_text,
    build_resource_link,
    build_tool_result,
    get_app_state,
    log_optional_link_failure,
    result_schema,
    standard_resource_links,
)
from kgfegmcp.resources.models import ResourceKind
from kgfegmcp.resources.uri import (
    learning_component_provenance_uri,
    learning_component_uri,
    standard_learning_components_uri,
)
from kgfegmcp.search.models import ExactPackageSearchScope, LearningComponentSearchMode
from kgfegmcp.services.frameworks import FrameworkService
from kgfegmcp.services.learning_components import LearningComponentService
from kgfegmcp.services.models import (
    GetLearningComponentContextRequest,
    GetLearningComponentContextResult,
    GetLearningComponentRequest,
    GetLearningComponentResult,
    GetLearningComponentsForStandardRequest,
    GetLearningComponentsForStandardResult,
    LearningComponentsSearchRequest,
    SearchLearningComponentsResult,
)

if TYPE_CHECKING:
    # Third Party Library
    from fastmcp import FastMCP
    from mcp.types import ResourceLink

    # Package Library
    from kgfegmcp.bootstrap import AppState
    from kgfegmcp.catalog.models import CatalogGraphPackage
    from kgfegmcp.domain.identifiers import NodeId
    from kgfegmcp.graph.models import LearningComponentNode
    from kgfegmcp.search.models import (
        LearningComponentSearchHit,
        SearchWarning,
        SupportedStandardReference,
    )
    from kgfegmcp.services.models import (
        SupportedStandardPlacement,
        SupportingLearningComponent,
    )


_COMPONENT_INTERPRETATION = (
    "A learning component is model-generated content decomposed from published "
    "standards. It is not source-asserted curriculum. Its wording, tags, and support "
    "confidence do not by themselves establish official equivalence, learner mastery, "
    "prerequisites, instructional progression, or difficulty."
)
_LEXICAL_SEARCH_SEMANTICS = (
    "Lexical semantics: text mode matches exact normalized description tokens or a "
    "contiguous normalized phrase. It performs no stemming, lemmatization, fuzzy "
    "matching, or synonym expansion."
)
_SUPPORTED_CODE_SEMANTICS = (
    "Supported-code semantics: the query matches the statement codes of standards, and "
    "the components supporting those standards are returned. Components attach to the "
    "codes the pipeline decomposed, so an exact query against a parent code returns "
    "nothing when only its children carry components; use the prefix mode instead."
)
_TAG_SEARCH_SEMANTICS = (
    "Tag semantics: a tag is a controlled facet matched whole after normalization, not "
    "tokenized. Partial words do not match."
)
_ZERO_RESULT_GUIDANCE = (
    "Zero matches establish only that this exact query did not match the retained "
    "components. They do not establish that no component covers the concept."
)


def _collapse_whitespace(value: str) -> str:
    """Collapse runs of Unicode whitespace into single spaces for display.

    Parameters
    ----------
    value
        Raw source text.

    Returns
    -------
    str
        Display text with normalized internal spacing.
    """

    return " ".join(value.split())


def _format_boolean(value: bool) -> str:
    """Return one stable lowercase boolean rendering.

    Parameters
    ----------
    value
        Boolean to render.

    Returns
    -------
    str
        ``true`` or ``false``.
    """

    return "true" if value else "false"


def _format_component_context(result: GetLearningComponentContextResult) -> str:
    """Format one component and every standard it supports.

    Parameters
    ----------
    result
        Component, supported standards, placements, and package evidence.

    Returns
    -------
    str
        Stable readable component and supported-standard evidence.
    """

    lines = _component_lines(node=result.node, placements=result.placements)
    lines.extend(("", f"Supported standards: {len(result.supported_standards)}"))

    for supported in result.supported_standards:
        standard = supported.standard
        description = _collapse_whitespace(standard.description or "[no description]")
        lines.extend(
            (
                "",
                f"- Standard: {standard.statement_code or '[uncoded]'}",
                f"  Node ID: {standard.node_id}",
                f"  Statement type: {standard.statement_type or '[none]'}",
                f"  Grade levels: {_format_values(standard.grade_level or ())}",
                f"  Support confidence: "
                f"{_format_confidence(supported.relationship.support_confidence)}",
                f"  Description: {description}",
            )
        )

    lines.extend(
        (
            "",
            f"Package: {result.package.package_identity.graph_package_id}",
            f"Interpretation: {_COMPONENT_INTERPRETATION}",
        )
    )
    return "\n".join(lines)


def _format_component_result(result: GetLearningComponentResult) -> str:
    """Format one exact learning component as deterministic readable evidence.

    Parameters
    ----------
    result
        Component, supported-standard placements, and package evidence.

    Returns
    -------
    str
        Stable readable component evidence.
    """

    lines = _component_lines(node=result.node, placements=result.placements)
    lines.extend(
        (
            "",
            f"Package: {result.package.package_identity.graph_package_id}",
            f"Interpretation: {_COMPONENT_INTERPRETATION}",
        )
    )
    return "\n".join(lines)


def _format_components_for_standard(
    result: GetLearningComponentsForStandardResult,
) -> str:
    """Format every component supporting one exact standard.

    Parameters
    ----------
    result
        Supporting components, the selected standard, and package evidence.

    Returns
    -------
    str
        Stable readable supporting-component evidence.
    """

    standard = result.standard
    lines = [
        f"Standard: {standard.statement_code or '[uncoded]'}",
        f"Node ID: {standard.node_id}",
        f"Description: {_collapse_whitespace(standard.description)}",
        f"Statement type: {standard.statement_type or '[none]'}",
        f"Normalized statement type: {standard.normalized_statement_type or '[none]'}",
        f"Supporting learning components: {len(result.components)}",
    ]

    for index, component in enumerate(result.components, start=1):
        lines.extend(
            (
                "",
                *_supporting_component_lines(
                    component=component, index=index, standard_id=standard.node_id
                ),
            )
        )

    lines.extend(
        (
            "",
            f"Package: {result.package.package_identity.graph_package_id}",
            f"Interpretation: {_COMPONENT_INTERPRETATION}",
        )
    )
    return "\n".join(lines)


def _format_confidence(value: float | None) -> str:
    """Return one stable support-confidence rendering.

    Parameters
    ----------
    value
        Support confidence between zero and one, or ``None``.

    Returns
    -------
    str
        Fixed-precision confidence or ``[none]``.
    """

    return "[none]" if value is None else f"{value:.2f}"


def _format_search_hit(*, hit: LearningComponentSearchHit, index: int) -> list[str]:
    """Format one learning-component search hit with its complete evidence.

    Parameters
    ----------
    hit
        Component, package identity, score, and match evidence.
    index
        One-based display position within the returned page.

    Returns
    -------
    list[str]
        Stable line-oriented search-hit evidence.
    """

    node = hit.node
    description = _collapse_whitespace(node.description)
    lines = [
        f"{index}. Learning component: {node.node_id}",
        f"   Package: {hit.package_identity.graph_package_id}",
        f"   Framework ID: {hit.package_identity.framework_id}",
        f"   Snapshot ID: {hit.package_identity.snapshot_id}",
        f"   Description: {description}",
        f"   Tags: {_format_values(node.tags or ())}",
        f"   Retrieval method: {hit.retrieval_method.value}",
        f"   Epistemic status: {hit.epistemic_status}",
        (
            f"   Score: value={hit.score.value}, "
            f"algorithm={hit.score.algorithm.value}, "
            f"matched_terms={hit.score.matched_term_count}/"
            f"{hit.score.query_term_count}"
        ),
        f"   Matched terms: {_format_values(tuple(hit.matched_terms))}",
    ]

    if hit.matched_codes:
        lines.append(f"   Matched codes: {_format_references(hit.matched_codes)}")

    lines.append(
        f"   Supported standards: {_format_references(hit.supported_standards)}"
    )

    if len(hit.supported_standards) > len(hit.matched_codes) and hit.matched_codes:
        lines.append(
            "   Note: this component also supports standards the query did not match."
        )

    if hit.warnings:
        lines.append("   Hit warnings:")
        lines.extend(f"   - {_format_warning(warning)}" for warning in hit.warnings)
    else:
        lines.append("   Hit warnings: none")

    return lines


def _format_search_result(result: SearchLearningComponentsResult) -> str:
    """Format one learning-component search page as readable evidence.

    Parameters
    ----------
    result
        Search page, effective scope, and selected snapshots.

    Returns
    -------
    str
        Stable summary of packages, hits, matches, warnings, and cursor state.
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
    mode = result.page.mode
    lines = [
        f"Search mode: {mode.value}",
        f"Selected packages: {_format_values(package_ids)}",
        f"Returned hits: {result.page.returned_count}",
        f"Has more: {_format_boolean(result.page.has_more)}",
    ]

    if mode is LearningComponentSearchMode.TEXT:
        lines.append(_LEXICAL_SEARCH_SEMANTICS)
    elif mode is LearningComponentSearchMode.TAG:
        lines.append(_TAG_SEARCH_SEMANTICS)
    else:
        lines.append(_SUPPORTED_CODE_SEMANTICS)

    if result.page.returned_count == 0:
        lines.append(_ZERO_RESULT_GUIDANCE)

    lines.extend(("", f"Interpretation: {_COMPONENT_INTERPRETATION}"))

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


def _format_values(values: tuple[object, ...]) -> str:
    """Return one stable comma-separated rendering of a display tuple.

    Parameters
    ----------
    values
        Display values in established order.

    Returns
    -------
    str
        Comma-separated values or ``[none]``.
    """

    return ", ".join(str(value) for value in values) if values else "[none]"


def _format_warning(warning: SearchWarning) -> str:
    """Format one deterministic package or hit warning.

    Parameters
    ----------
    warning
        Exact warning evidence.

    Returns
    -------
    str
        Stable single-line warning rendering.
    """

    return (
        f"{warning.package_identity.graph_package_id} | "
        f"{warning.code.value} | {warning.message}"
    )


def _component_lines(
    *, node: LearningComponentNode, placements: tuple[SupportedStandardPlacement, ...]
) -> list[str]:
    """Build the shared readable body for one exact learning component.

    Parameters
    ----------
    node
        Exact learning-component node.
    placements
        Hierarchy placement of every standard the component supports.

    Returns
    -------
    list[str]
        Stable line-oriented component evidence.
    """

    lines = [
        f"Learning component: {node.node_id}",
        f"Description: {_collapse_whitespace(node.description)}",
        f"Tags: {_format_values(node.tags or ())}",
        f"Identity key: {node.identity_key or '[none]'}",
        f"Author: {node.author or '[none]'}",
        f"Provider: {node.provider or '[none]'}",
        f"Attribution: {node.attribution_statement or '[none]'}",
        f"License: {node.license or '[none]'}",
        "",
        f"Supported standard placements: {len(placements)}",
    ]

    for placement in placements:
        lines.extend(
            (
                f"- {placement.statement_code or '[uncoded]'} ({placement.node_id})",
                f"  Description: {_collapse_whitespace(placement.description)}",
                f"  Grade levels: {_format_values(placement.grade_levels)}",
                f"  Hierarchy path: {' > '.join(placement.hierarchy_path) or '[none]'}",
                f"  Support confidence: "
                f"{_format_confidence(placement.support_confidence)}",
            )
        )

    return lines


def _learning_component_service(state: AppState) -> LearningComponentService:
    """Construct one stateless learning-component orchestrator over retained data.

    Parameters
    ----------
    state
        Immutable application state created by the FastMCP lifespan.

    Returns
    -------
    LearningComponentService
        Stateless ordinary service delegating to retained domain services.
    """

    return LearningComponentService(
        catalog_service=state.catalog_service,
        framework_service=FrameworkService(catalog_service=state.catalog_service),
        search_service=state.search_service,
    )


def _supported_code_values(
    references: tuple[SupportedStandardReference, ...],
    *,
    already_shown: NodeId | None = None,
) -> tuple[str, ...]:
    """Render supported-standard references as display values.

    Parameters
    ----------
    references
        Supported standards in deterministic relationship order.
    already_shown
        Standard whose wording the caller has already printed once, so it is not
        repeated on every reference to it.

    Returns
    -------
    tuple[str, ...]
        Statement codes or node identifiers with grade levels, support confidence, and
        the standard's own wording, so a hit is readable without a second call.
    """

    values: list[str] = []

    for reference in references:
        value = f"{reference.statement_code or f'[uncoded {reference.node_id}]'}"
        qualifiers: list[str] = []

        if reference.grade_levels:
            qualifiers.append(f"grade {', '.join(reference.grade_levels)}")

        if (
            reference.support_confidence is not None
            and reference.node_id != already_shown
        ):
            qualifiers.append(
                f"confidence {_format_confidence(reference.support_confidence)}"
            )

        if qualifiers:
            value = f"{value} ({', '.join(qualifiers)})"

        if reference.node_id != already_shown:
            description = _collapse_whitespace(reference.description)
            value = f'{value} "{description}"'

        values.append(value)

    return tuple(values)


def _format_references(
    references: tuple[SupportedStandardReference, ...],
    *,
    already_shown: NodeId | None = None,
) -> str:
    """Join rendered supported-standard references with semicolons.

    Parameters
    ----------
    references
        Supported standards in deterministic relationship order.
    already_shown
        Standard whose wording is already printed once in the surrounding output.

    Returns
    -------
    str
        Semicolon-separated references, because descriptions may contain commas, or
        ``[none]``.
    """

    values = _supported_code_values(references, already_shown=already_shown)
    return "; ".join(values) if values else "[none]"


def _supporting_component_lines(
    *, component: SupportingLearningComponent, index: int, standard_id: NodeId
) -> list[str]:
    """Format one component supporting the selected standard.

    Parameters
    ----------
    component
        Component, its supports relationship, and every standard it supports.
    index
        One-based display position.
    standard_id
        The requested standard, whose wording the header already shows.

    Returns
    -------
    list[str]
        Stable line-oriented supporting-component evidence.
    """

    node = component.node
    lines = [
        f"{index}. Learning component: {node.node_id}",
        f"   Description: {_collapse_whitespace(node.description)}",
        f"   Tags: {_format_values(node.tags or ())}",
        f"   Support confidence: "
        f"{_format_confidence(component.relationship.support_confidence)}",
        f"   Supports: "
        f"{_format_references(component.supported_standards, already_shown=standard_id)}",
    ]

    if len(component.supported_standards) > 1:
        lines.append("   Note: this component supports more than one standard.")

    return lines


def _component_resource_links(
    *, node_id: NodeId, package: CatalogGraphPackage, state: AppState
) -> tuple[ResourceLink, ...]:
    """Build non-critical links for one exact learning-component result.

    Parameters
    ----------
    node_id
        Outer identifier of the learning component.
    package
        Exact accepted graph package owning the component.
    state
        Immutable application state providing shared policy.

    Returns
    -------
    tuple[ResourceLink, ...]
        Permitted component and provenance links, or nothing when rights forbid them.
    """

    identity = package.package_identity

    try:
        state.resource_service.policy.require_resource_access(
            resource_kind=ResourceKind.LEARNING_COMPONENT, rights=package.rights
        )
        links = [
            build_resource_link(
                description="Read this exact learning component with its placements.",
                mime_type="application/json",
                name="learning_component",
                title="Learning Component",
                uri=learning_component_uri(
                    framework_id=identity.framework_id,
                    node_id=node_id,
                    snapshot_id=identity.snapshot_id,
                ),
            )
        ]

        if package.capabilities.has_detailed_provenance:
            links.append(
                build_resource_link(
                    description=(
                        "Read this component's generation provenance: source pages, "
                        "generator, and confidence."
                    ),
                    mime_type="application/json",
                    name="learning_component_provenance",
                    title="Learning Component Provenance",
                    uri=learning_component_provenance_uri(
                        framework_id=identity.framework_id,
                        node_id=node_id,
                        snapshot_id=identity.snapshot_id,
                    ),
                )
            )
    except KGFEGMCPError:
        return ()
    except Exception as error:  # pylint: disable=W0718
        log_optional_link_failure(
            error=error,
            operation=f"component_resource_links:{identity.graph_package_id}",
        )
        return ()

    return tuple(sorted(links, key=lambda link: str(link.uri)))


def _standard_components_resource_links(
    *, node_id: NodeId, package: CatalogGraphPackage, state: AppState
) -> tuple[ResourceLink, ...]:
    """Build the link to every component supporting one exact standard.

    Parameters
    ----------
    node_id
        Outer identifier of the standard.
    package
        Exact accepted graph package owning the standard.
    state
        Immutable application state providing shared policy.

    Returns
    -------
    tuple[ResourceLink, ...]
        The permitted supporting-components link, or nothing when rights forbid it.
    """

    identity = package.package_identity

    try:
        state.resource_service.policy.require_resource_access(
            resource_kind=ResourceKind.STANDARD_LEARNING_COMPONENTS,
            rights=package.rights,
        )
        link = build_resource_link(
            description="Read every learning component supporting this standard.",
            mime_type="application/json",
            name="standard_learning_components",
            title="Standard Learning Components",
            uri=standard_learning_components_uri(
                framework_id=identity.framework_id,
                node_id=node_id,
                snapshot_id=identity.snapshot_id,
            ),
        )
    except KGFEGMCPError:
        return ()
    except Exception as error:  # pylint: disable=W0718
        log_optional_link_failure(
            error=error,
            operation=f"standard_components_resource_links:{identity.graph_package_id}",
        )
        return ()

    return (link,)


async def get_learning_component(
    request: GetLearningComponentRequest, context: Context
) -> ToolResult:
    """Return one exact learning component with its supported-standard placements.

    Parameters
    ----------
    request
        Framework selection and the exact learning-component node identifier.
    context
        Injected FastMCP request context containing immutable application state.

    Returns
    -------
    ToolResult
        Human-readable summary and complete ``GetLearningComponentResult`` evidence.
    """

    with tool_error_boundary("get_learning_component"):
        state = get_app_state(context)
        result = _learning_component_service(state).get_learning_component(request)
        return build_tool_result(
            content=_format_component_result(result),
            resource_links=_component_resource_links(
                node_id=result.node.node_id, package=result.package, state=state
            ),
            result=result,
        )


async def get_learning_component_context(
    request: GetLearningComponentContextRequest, context: Context
) -> ToolResult:
    """Return one learning component with every standard it supports.

    Parameters
    ----------
    request
        Framework selection and the exact learning-component node identifier.
    context
        Injected FastMCP request context containing immutable application state.

    Returns
    -------
    ToolResult
        Human-readable summary and complete context evidence.
    """

    with tool_error_boundary("get_learning_component_context"):
        state = get_app_state(context)
        result = _learning_component_service(state).get_learning_component_context(
            request
        )
        return build_tool_result(
            content=_format_component_context(result),
            resource_links=_component_resource_links(
                node_id=result.node.node_id, package=result.package, state=state
            ),
            result=result,
        )


async def get_learning_components_for_standard(
    request: GetLearningComponentsForStandardRequest, context: Context
) -> ToolResult:
    """Return every learning component supporting one exact standard.

    Parameters
    ----------
    request
        Framework selection and the exact standard identifier.
    context
        Injected FastMCP request context containing immutable application state.

    Returns
    -------
    ToolResult
        Human-readable summary and complete supporting-component evidence.
    """

    with tool_error_boundary("get_learning_components_for_standard"):
        state = get_app_state(context)
        result = _learning_component_service(
            state
        ).get_learning_components_for_standard(request)
        return build_tool_result(
            content=_format_components_for_standard(result),
            resource_links=(
                *standard_resource_links(
                    node=result.standard, package=result.package, state=state
                ),
                *_standard_components_resource_links(
                    node_id=result.standard.node_id,
                    package=result.package,
                    state=state,
                ),
            ),
            result=result,
        )


async def search_learning_components(
    request: LearningComponentsSearchRequest, context: Context
) -> ToolResult:
    """Search learning components through package-local indexes and cursor semantics.

    Parameters
    ----------
    request
        Discriminated text, tag, or supported-code request shape. Package-specific mode
        availability is reported by ``get_capabilities``.
    context
        Injected FastMCP request context containing immutable application state.

    Returns
    -------
    ToolResult
        Human-readable summary and complete ``SearchLearningComponentsResult``.
    """

    with tool_error_boundary("search_learning_components"):
        state = get_app_state(context)
        result = _learning_component_service(state).search_learning_components(request)
        continuation_text = build_request_continuation_text(
            cursor_field="cursor",
            has_more=result.page.has_more,
            next_cursor=(
                result.page.next_cursor.root
                if result.page.next_cursor is not None
                else None
            ),
            request=request,
            tool_name="search_learning_components",
        )
        return build_tool_result(
            additional_text=(continuation_text,),
            content=_format_search_result(result),
            result=result,
        )


def register_learning_component_tools(server: FastMCP[dict[str, AppState]]) -> None:
    """Register read-only learning-component search, lookup, and traversal tools.

    Parameters
    ----------
    server
        FastMCP server receiving explicitly approved read-only tools.
    """

    server.tool(
        annotations=READ_ONLY_TOOL_ANNOTATIONS,
        description=(
            "Search model-generated learning components decomposed from published "
            "standards. Modes are learning_component_text over component descriptions, "
            "learning_component_tag over controlled keyword tags matched whole, and "
            "learning_component_supported_code_exact or "
            "learning_component_supported_code_prefix over the statement codes of the "
            "standards a component supports. Inspect get_capabilities "
            "packages[].implementedLearningComponentSearchModes before using a "
            "supported-code mode. Text mode matches exact normalized tokens and "
            "performs no stemming or synonym expansion. Every hit reports every "
            "standard the component supports, not only the matched one, so a component "
            "bridging several standards or grades is visible as such. Results are "
            "generated content and are never source-asserted curriculum. For "
            "continuation, submit the provided nextRequest unchanged."
        ),
        name="search_learning_components",
        output_schema=result_schema(SearchLearningComponentsResult),
        title="Search Learning Components",
    )(search_learning_components)
    server.tool(
        annotations=READ_ONLY_TOOL_ANNOTATIONS,
        description=(
            "Return one exact learning component by node ID with its description, "
            "controlled tags, identity key, attribution, and the hierarchy placement of "
            "every standard it supports. A learning component carries no CASE "
            "identifier, grade level, or statement taxonomy of its own; those belong to "
            "the standards it supports."
        ),
        name="get_learning_component",
        output_schema=result_schema(GetLearningComponentResult),
        title="Get Learning Component",
    )(get_learning_component)
    server.tool(
        annotations=READ_ONLY_TOOL_ANNOTATIONS,
        description=(
            "Return one learning component together with the complete source record of "
            "every standard it supports, including statement type, grade levels, and "
            "support confidence. Use this to traverse from generated content back to "
            "the published curriculum it was decomposed from."
        ),
        name="get_learning_component_context",
        output_schema=result_schema(GetLearningComponentContextResult),
        title="Get Learning Component Context",
    )(get_learning_component_context)
    server.tool(
        annotations=READ_ONLY_TOOL_ANNOTATIONS,
        description=(
            "Return every learning component supporting one exact standard, selected by "
            "node ID, CASE UUID, or CASE URI. Each component reports every standard it "
            "supports, so a component shared across grades is visible as such."
        ),
        name="get_learning_components_for_standard",
        output_schema=result_schema(GetLearningComponentsForStandardResult),
        title="Get Learning Components For Standard",
    )(get_learning_components_for_standard)
