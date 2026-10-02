"""Expose deterministic stored-progression curriculum/teaching/support instructions."""

# Third Party Library
from fastmcp import Context
from fastmcp.prompts import PromptResult

# Package Library
from kgfegmcp.domain.identifiers import FrameworkId
from kgfegmcp.mcp.errors import prompt_error_boundary
from kgfegmcp.mcp.prompts import build_prompt_result
from kgfegmcp.mcp.prompts.arguments import (
    CurriculumReviewEndpointScopeArgument,
    CurriculumReviewFacetValuesArgument,
    CurriculumReviewSelectorsArgument,
    OptionalLanguageTagArgument,
    OptionalPromptLocalContextArgument,
    OptionalSnapshotIdArgument,
    ProgressionLocalGradeLabelsArgument,
    ProgressionNormalizedGradesArgument,
    PromptFocusModeArgument,
    PromptFocusTextArgument,
    PromptStandardIdentifierArgument,
)
from kgfegmcp.mcp.tools import get_app_state
from kgfegmcp.prompts.models import PromptFocusMode


async def learning_progression_curriculum_review(
    *,
    context: Context,
    endpoint_scope: CurriculumReviewEndpointScopeArgument = "either",
    framework_id: FrameworkId,
    local_context: OptionalPromptLocalContextArgument = None,
    local_grade_labels: CurriculumReviewFacetValuesArgument = (),
    normalized_grades: CurriculumReviewFacetValuesArgument = (),
    normalized_statement_types: CurriculumReviewFacetValuesArgument = (),
    output_language: OptionalLanguageTagArgument = None,
    snapshot_id: OptionalSnapshotIdArgument = None,
    standard_identifiers: CurriculumReviewSelectorsArgument = (),
    statement_types: CurriculumReviewFacetValuesArgument = (),
) -> PromptResult:
    """Return bounded curriculum-review instructions with exact evidence citations.

    Parameters
    ----------
    context
        Injected FastMCP context containing shared immutable application state.
    endpoint_scope
        Whole-filter conjunction matching either, both, source or target endpoints.
    framework_id
        Exact conceptual framework identifier.
    local_context
        Optional unverified caller observations, at most 4,000 characters.
    local_grade_labels
        Up to 32 unique source-facing grade values in a JSON array.
    normalized_grades
        Up to 32 unique normalized grade facets in a JSON array.
    normalized_statement_types
        Up to 32 unique normalized statement-type facets in a JSON array.
    output_language
        Optional output language tag.
    snapshot_id
        Optional exact snapshot; omission pins unique-current once.
    standard_identifiers
        Up to 20 exact node/CASE/profile-enabled code selectors in a JSON array.
    statement_types
        Up to 32 unique source statement-type values in a JSON array.

    Returns
    -------
    PromptResult
        One deterministic user-role workflow and exact runtime metadata.
    """

    with prompt_error_boundary("learning_progression_curriculum_review"):
        state = get_app_state(context)
        result = state.prompt_service.learning_progression_curriculum_review(
            endpoint_scope=endpoint_scope,
            framework_id=framework_id,
            local_context=local_context,
            local_grade_labels=local_grade_labels,
            normalized_grades=normalized_grades,
            normalized_statement_types=normalized_statement_types,
            output_language=output_language,
            snapshot_id=snapshot_id,
            standard_identifiers=standard_identifiers,
            statement_types=statement_types,
        )
        return build_prompt_result(result)


async def learning_progression_support_plan(
    *,
    context: Context,
    framework_id: FrameworkId,
    identifier: PromptStandardIdentifierArgument,
    local_context: OptionalPromptLocalContextArgument = None,
    output_language: OptionalLanguageTagArgument = None,
    snapshot_id: OptionalSnapshotIdArgument = None,
) -> PromptResult:
    """Return cited support options with observations separate from suggestions.

    Parameters
    ----------
    context
        Injected FastMCP context containing shared immutable application state.
    framework_id
        Exact conceptual framework identifier.
    identifier
        Exact node/CASE selector supplied as a JSON-object prompt argument.
    local_context
        Optional unverified teacher observations, at most 4,000 characters.
    output_language
        Optional output language tag.
    snapshot_id
        Optional exact snapshot; omission pins unique-current once.

    Returns
    -------
    PromptResult
        One deterministic user-role workflow and exact runtime metadata.
    """

    with prompt_error_boundary("learning_progression_support_plan"):
        state = get_app_state(context)
        result = state.prompt_service.learning_progression_support_plan(
            framework_id=framework_id,
            identifier=identifier,
            local_context=local_context,
            output_language=output_language,
            snapshot_id=snapshot_id,
        )
        return build_prompt_result(result)


async def learning_progression_teaching_sequence(
    *,
    context: Context,
    focus_mode: PromptFocusModeArgument = PromptFocusMode.TOPIC,
    framework_id: FrameworkId,
    local_context: OptionalPromptLocalContextArgument = None,
    local_grade_labels: ProgressionLocalGradeLabelsArgument = (),
    normalized_grades: ProgressionNormalizedGradesArgument = (),
    output_language: OptionalLanguageTagArgument = None,
    snapshot_id: OptionalSnapshotIdArgument = None,
    topic_or_standard: PromptFocusTextArgument,
) -> PromptResult:
    """Return a cited teaching-sequence workflow using bounded stored evidence.

    Parameters
    ----------
    context
        Injected FastMCP context holding the shared immutable application state.
    focus_mode
        Topic or exact identifier namespace; codes require profile support.
    framework_id
        Exact conceptual framework identifier.
    local_context
        Optional untrusted teacher context, at most 4,000 characters.
    local_grade_labels
        Up to 32 unique profile-valid source grade values, sent as a JSON array.
    normalized_grades
        Up to 32 unique normalized retrieval facets, sent as a JSON array.
    output_language
        Optional BCP 47-style output language tag.
    snapshot_id
        Optional exact snapshot; omission pins unique-current once.
    topic_or_standard
        Topic or exact selector text, at most 512 characters.

    Returns
    -------
    PromptResult
        One deterministic user-role message and exact runtime metadata.
    """

    with prompt_error_boundary("learning_progression_teaching_sequence"):
        state = get_app_state(context)
        result = state.prompt_service.learning_progression_teaching_sequence(
            focus_mode=focus_mode,
            framework_id=framework_id,
            local_context=local_context,
            local_grade_labels=local_grade_labels,
            normalized_grades=normalized_grades,
            output_language=output_language,
            snapshot_id=snapshot_id,
            topic_or_standard=topic_or_standard,
        )
        return build_prompt_result(result)
