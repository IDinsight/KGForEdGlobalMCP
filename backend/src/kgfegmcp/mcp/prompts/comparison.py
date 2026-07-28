"""This module exposes the general cross-framework comparison workflow as a FastMCP
prompt.

This module provides the protocol-facing ``cross_framework_comparison`` prompt for
exploratory review across multiple selected frameworks. The prompt accepts concrete
typed parameters, obtains the lifespan-owned application state, delegates deterministic
multi-package prompt construction to the ordinary ``PromptService``, and converts the
rendered result into a FastMCP ``PromptResult``.

The prompt prepares instructions for a client-side language model; it does not retrieve
or compare standards evidence directly. The generated workflow directs the client to
use ``compare_framework_evidence`` and keeps every selected framework's package
identity, profile, rights, provenance, terminology, and optional local guidance inside
that framework's own comparison section.

This module is a thin MCP adapter. It performs no search, graph traversal, ranking,
framework merging, equivalence inference, mapping, persistence, source-package
mutation, server-side LLM invocation, or MCP sampling. Retrieved similarities remain
candidate evidence, and any cross-framework synthesis remains explicitly LLM-inferred.
"""

# Third Party Library
from fastmcp import Context
from fastmcp.prompts import PromptResult

# Package Library
from kgfegmcp.mcp.errors import prompt_error_boundary
from kgfegmcp.mcp.prompts import build_multi_context_prompt_result
from kgfegmcp.mcp.prompts.arguments import (
    ComparisonFrameworkIdsArgument,
    ComparisonGradeFiltersArgument,
    ComparisonMatchLimitArgument,
    ComparisonSearchModeArgument,
    ComparisonSnapshotIdsArgument,
    IncludeContextPathsArgument,
    OptionalLanguageTagArgument,
    OptionalPromptLocalContextArgument,
    PromptFocusTextArgument,
)
from kgfegmcp.mcp.tools import get_app_state
from kgfegmcp.prompts.models import ComparisonSearchMode


async def cross_framework_comparison(
    *,
    context: Context,
    framework_ids: ComparisonFrameworkIdsArgument,
    include_context_paths: IncludeContextPathsArgument = True,
    local_context: OptionalPromptLocalContextArgument = None,
    local_grade_labels: ComparisonGradeFiltersArgument = (),
    matches_per_framework: ComparisonMatchLimitArgument = 5,
    normalized_grades: ComparisonGradeFiltersArgument = (),
    output_language: OptionalLanguageTagArgument = None,
    search_mode: ComparisonSearchModeArgument = ComparisonSearchMode.TEXT,
    snapshot_ids: ComparisonSnapshotIdsArgument = (),
    topic_or_query: PromptFocusTextArgument,
) -> PromptResult:
    """Return an exploratory evidence-grounded cross-framework workflow.

    Parameters
    ----------
    context
        Injected FastMCP request context containing immutable application state.
    framework_ids
        Two through eight distinct conceptual framework identifiers.
    include_context_paths
        Whether the comparison call requests bounded hierarchy paths.
    local_context
        Optional untrusted local nuance.
    local_grade_labels
        Shared exact local grade or stage filters.
    matches_per_framework
        Independent package-local candidate quota, from one through ten.
    normalized_grades
        Shared normalized retrieval-facet filters.
    output_language
        Optional BCP 47-style output language tag.
    search_mode
        Text, exact-code, or code-prefix comparison mode.
    snapshot_ids
        Optional exact snapshots, with at most one per selected framework.
    topic_or_query
        Topic text or code query used for evidence retrieval.

    Returns
    -------
    PromptResult
        One deterministic user-role prompt with all exact package audit metadata.
    """

    with prompt_error_boundary("cross_framework_comparison"):
        state = get_app_state(context)
        result = state.prompt_service.cross_framework_comparison(
            framework_ids=framework_ids,
            include_context_paths=include_context_paths,
            local_context=local_context,
            local_grade_labels=local_grade_labels,
            matches_per_framework=matches_per_framework,
            normalized_grades=normalized_grades,
            output_language=output_language,
            search_mode=search_mode,
            snapshot_ids=snapshot_ids,
            topic_or_query=topic_or_query,
        )
        return build_multi_context_prompt_result(result)
