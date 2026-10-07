"""Render seven native prompt workflows for tool-only clients.

``get_workflow_instructions`` accepts one typed request discriminated by
``workflowName``. Each variant has exactly the inputs, defaults and constraints of
its native prompt and is passed to the same ordinary ``PromptService`` renderer, so
native and tool invocations return identical messages for identical validated
requests. The result adds the pinned package, profile and manifest identity of the
rendered snapshot. Nothing here executes the workflow or calls a model.
"""

# Future Library
from __future__ import annotations

# Standard Library
import hashlib

from typing import TYPE_CHECKING, Annotated, Literal, TypeAlias, cast

# Third Party Library
from pydantic import Field

# Package Library
from kgfegmcp.domain.identifiers import (
    FrameworkId,
    LanguageTag,
    Sha256Digest,
    SnapshotId,
)
from kgfegmcp.prompts.learning_progressions import (
    LearningProgressionCurriculumReviewRequest,
    LearningProgressionSupportPlanRequest,
)
from kgfegmcp.prompts.models import (
    HandbookWordCount,
    LearningProgressionTeachingSequenceRequest,
    LessonDurationMinutes,
    MultigradeGradesInRoom,
    PracticeCount,
    PromptFocusMode,
    PromptFocusText,
    PromptGradeOrStage,
    PromptLearnerContext,
    PromptLocalContext,
    PromptMaterials,
    PromptRenderResult,
    StudyDifficulty,
)
from kgfegmcp.schemas import FrozenSchema
from kgfegmcp.services.models import PackageReference, package_reference

if TYPE_CHECKING:
    # Package Library
    from kgfegmcp.prompts.service import PromptService


class _FocusWorkflowRequest(FrozenSchema):
    """Share the native focus, route and caller-context inputs of AS/LC workflows."""

    focus_mode: PromptFocusMode = PromptFocusMode.TOPIC
    framework_id: FrameworkId
    local_context: PromptLocalContext | None = None
    output_language: LanguageTag | None = None
    snapshot_id: SnapshotId | None = None
    topic_or_standard: PromptFocusText


class CurriculumReviewInstructionsRequest(LearningProgressionCurriculumReviewRequest):
    """Request learning_progression_curriculum_review instructions."""

    workflow_name: Literal["learning_progression_curriculum_review"]


class MultigradeLessonPlanInstructionsRequest(_FocusWorkflowRequest):
    """Request multigrade_lesson_plan instructions with native defaults."""

    grades_in_room: MultigradeGradesInRoom
    learner_context: PromptLearnerContext | None = None
    lesson_duration_minutes: LessonDurationMinutes = 45
    workflow_name: Literal["multigrade_lesson_plan"]


class StudentHandbookSectionInstructionsRequest(_FocusWorkflowRequest):
    """Request student_handbook_section instructions with native defaults."""

    grade_or_stage: PromptGradeOrStage
    target_word_count: HandbookWordCount = 500
    workflow_name: Literal["student_handbook_section"]


class StudentStudySupportInstructionsRequest(_FocusWorkflowRequest):
    """Request student_study_support instructions with native defaults."""

    difficulty: StudyDifficulty = StudyDifficulty.ON_LEVEL
    grade_or_stage: PromptGradeOrStage
    practice_count: PracticeCount = 5
    workflow_name: Literal["student_study_support"]


class SupportPlanInstructionsRequest(LearningProgressionSupportPlanRequest):
    """Request learning_progression_support_plan instructions."""

    workflow_name: Literal["learning_progression_support_plan"]


class TeacherGuideDraftInstructionsRequest(_FocusWorkflowRequest):
    """Request teacher_guide_draft instructions with native defaults."""

    available_materials: PromptMaterials | None = None
    grade_or_stage: PromptGradeOrStage
    learner_context: PromptLearnerContext | None = None
    lesson_duration_minutes: LessonDurationMinutes = 45
    workflow_name: Literal["teacher_guide_draft"]


class TeachingSequenceInstructionsRequest(LearningProgressionTeachingSequenceRequest):
    """Request learning_progression_teaching_sequence instructions."""

    workflow_name: Literal["learning_progression_teaching_sequence"]


WorkflowInstructionsRequest: TypeAlias = Annotated[
    CurriculumReviewInstructionsRequest
    | MultigradeLessonPlanInstructionsRequest
    | StudentHandbookSectionInstructionsRequest
    | StudentStudySupportInstructionsRequest
    | SupportPlanInstructionsRequest
    | TeacherGuideDraftInstructionsRequest
    | TeachingSequenceInstructionsRequest,
    Field(discriminator="workflow_name"),
]


class WorkflowInstructionsResult(FrozenSchema):
    """Return complete rendered instructions with their pinned exact identity."""

    effective_request: WorkflowInstructionsRequest
    instructions_notice: str = (
        "rendered.message holds the complete workflow instructions, identical to the "
        "native prompt of the same name. The server has not run them: the client "
        "performs each listed tool call and evidence read, then composes the cited "
        "output. No cursor or partial instruction text is ever returned."
    )
    manifest_sha256: Sha256Digest
    package: PackageReference
    profile_sha256: Sha256Digest
    rendered: PromptRenderResult


def render_workflow_instructions(
    *, prompt_service: PromptService, request: WorkflowInstructionsRequest
) -> WorkflowInstructionsResult:
    """Render one workflow through the same renderer as its native prompt.

    Parameters
    ----------
    prompt_service
        Shared prompt service; rights, configuration and rendered-size policy apply.
    request
        One validated typed workflow variant, defaults applied.

    Returns
    -------
    WorkflowInstructionsResult
        Rendered result plus the package, profile and manifest identity of the
        exact runtime the renderer selected.

    Examples
    --------
    >>> result = render_workflow_instructions(
    ...     prompt_service=state.prompt_service,
    ...     request=SupportPlanInstructionsRequest(
    ...         framework_id="framework-a",
    ...         identifier=node_selector,
    ...         workflow_name="learning_progression_support_plan",
    ...     ),
    ... )
    >>> result.rendered.prompt_name
    <PromptName.LEARNING_PROGRESSION_SUPPORT_PLAN: 'learning_progression_support_plan'>
    """

    # Variant field names equal the renderer's keyword arguments; pass typed values.
    arguments = {
        name: getattr(request, name)
        for name in type(request).model_fields
        if name != "workflow_name"
    }
    rendered: PromptRenderResult = getattr(prompt_service, request.workflow_name)(
        **arguments
    )
    runtime = prompt_service.catalog_service.get_package_runtime(
        rendered.graph_package_id
    )
    return WorkflowInstructionsResult(
        effective_request=request,
        manifest_sha256=cast(
            Sha256Digest,
            "sha256:"
            + hashlib.sha256(runtime.loaded_package.manifest_bytes).hexdigest(),
        ),
        package=package_reference(package=runtime.catalog_package),
        profile_sha256=runtime.catalog_package.package_identity.profile_sha256,
        rendered=rendered,
    )
