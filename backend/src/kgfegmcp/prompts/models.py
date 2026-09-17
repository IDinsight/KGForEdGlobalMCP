"""This module defines typed contracts for generic prompt workflows and local
configuration.

This module declares the prompt names, versions, parameter enums, constrained value
types, framework-local guidance models, prompt-overlay models, loaded configuration
records, immutable configuration registry, and rendered prompt result used by the
ordinary prompt application layer.

The configuration models define the only soft-guidance sections that a framework-local
``prompts.json`` may append to or replace. They also enforce schema version, framework
identity, profile identity, instruction counts, instruction sizes, and cross-field
configuration consistency.

These contracts are curriculum-agnostic. They do not access the filesystem, select
catalog packages, enforce derivative-rights policy, search standards, traverse graphs,
render FastMCP messages, register MCP components, call an LLM, or use MCP sampling.
"""

# Future Library
from __future__ import annotations

# Standard Library
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Final, Self, cast

# Third Party Library
from pydantic import AfterValidator, Field, StringConstraints, model_validator

# Package Library
from kgfegmcp.catalog.models import CatalogSourceMetadata
from kgfegmcp.domain.enums import GraphType
from kgfegmcp.domain.identifiers import (
    FrameworkId,
    GraphPackageId,
    ProfileId,
    ProfileVersion,
    SchemaVersion,
    Sha256Digest,
    SnapshotId,
)
from kgfegmcp.domain.models import RightsPolicy
from kgfegmcp.regexes import KEBAB_CASE_ID_RE, VERSION_TOKEN_RE
from kgfegmcp.schemas import FrozenSchema


def _count_guidance_instructions(model: FrozenSchema | None) -> int:
    """Count instructions contained in one optional guidance aggregate.

    Parameters
    ----------
    model
        Shared or prompt-specific guidance aggregate.

    Returns
    -------
    int
        Number of configured instructions across all non-empty blocks.
    """

    if model is None:
        return 0

    count = 0

    for value in model.__dict__.values():
        if isinstance(value, PromptGuidanceBlock):
            count += len(value.instructions)

    return count


def _require_non_whitespace(value: str) -> str:
    """Require a configured or caller-supplied string to contain visible text.

    Parameters
    ----------
    value
        Validated length-bounded string.

    Returns
    -------
    str
        Unchanged string containing at least one non-whitespace character.

    Raises
    ------
    ValueError
        If the value contains only whitespace.
    """

    if not value.strip():
        raise ValueError("Prompt text must contain non-whitespace characters.")

    return value


def _require_unique_framework_ids(
    values: tuple[FrameworkId, ...],
) -> tuple[FrameworkId, ...]:
    """Require exact framework selectors to be unique.

    Parameters
    ----------
    values
        Validated framework identifiers.

    Returns
    -------
    tuple[FrameworkId, ...]
        Unchanged unique identifiers.

    Raises
    ------
    ValueError
        If an identifier is repeated.
    """

    if len(values) != len(set(values)):
        raise ValueError("framework_ids must not contain duplicate values.")

    return values


def _require_unique_grade_values(values: tuple[str, ...]) -> tuple[str, ...]:
    """Require exact prompt grade or stage filters to be unique.

    Parameters
    ----------
    values
        Validated local or normalized grade values.

    Returns
    -------
    tuple[str, ...]
        Unchanged unique values.

    Raises
    ------
    ValueError
        If a filter value is repeated.
    """

    if len(values) != len(set(values)):
        raise ValueError("Prompt grade filters must not contain duplicate values.")

    return values


def _require_unique_snapshot_ids(
    values: tuple[SnapshotId, ...],
) -> tuple[SnapshotId, ...]:
    """Require exact snapshot selectors to be unique.

    Parameters
    ----------
    values
        Validated snapshot identifiers.

    Returns
    -------
    tuple[SnapshotId, ...]
        Unchanged unique identifiers.

    Raises
    ------
    ValueError
        If an identifier is repeated.
    """

    if len(values) != len(set(values)):
        raise ValueError("snapshot_ids must not contain duplicate values.")

    return values


PromptConfigId = Annotated[
    str, StringConstraints(max_length=200, min_length=3, pattern=KEBAB_CASE_ID_RE)
]
PromptConfigVersion = Annotated[
    str, StringConstraints(max_length=64, min_length=1, pattern=VERSION_TOKEN_RE)
]
HandbookWordCount = Annotated[int, Field(ge=150, le=1_500)]
LessonDurationMinutes = Annotated[int, Field(ge=10, le=240)]
PracticeCount = Annotated[int, Field(ge=1, le=10)]
ProgressionCandidateLimit = Annotated[int, Field(ge=2, le=20)]
PromptFocusText = Annotated[
    str,
    StringConstraints(max_length=512, min_length=1),
    AfterValidator(_require_non_whitespace),
]
PromptGradeOrStage = Annotated[
    str,
    StringConstraints(max_length=128, min_length=1),
    AfterValidator(_require_non_whitespace),
]
ProgressionGradeFilters = Annotated[
    tuple[PromptGradeOrStage, ...],
    Field(max_length=32),
    AfterValidator(_require_unique_grade_values),
]
MultigradeGradesInRoom = Annotated[
    tuple[PromptGradeOrStage, ...],
    Field(max_length=8, min_length=2),
    AfterValidator(_require_unique_grade_values),
]
ComparisonFrameworkIds = Annotated[
    tuple[FrameworkId, ...],
    Field(max_length=8, min_length=2),
    AfterValidator(_require_unique_framework_ids),
]
ComparisonGradeFilters = Annotated[
    tuple[PromptGradeOrStage, ...],
    Field(max_length=64),
    AfterValidator(_require_unique_grade_values),
]
ComparisonMatchLimit = Annotated[int, Field(ge=1, le=10)]
ComparisonSnapshotIds = Annotated[
    tuple[SnapshotId, ...],
    Field(max_length=8),
    AfterValidator(_require_unique_snapshot_ids),
]
PromptLocalContext = Annotated[
    str,
    StringConstraints(max_length=4_000, min_length=1),
    AfterValidator(_require_non_whitespace),
]
PromptMaterials = Annotated[
    str,
    StringConstraints(max_length=2_000, min_length=1),
    AfterValidator(_require_non_whitespace),
]
PromptLearnerContext = Annotated[
    str,
    StringConstraints(max_length=2_000, min_length=1),
    AfterValidator(_require_non_whitespace),
]
PromptInstruction = Annotated[
    str,
    StringConstraints(max_length=1_000, min_length=1),
    AfterValidator(_require_non_whitespace),
]
PROMPT_CONFIG_SCHEMA_VERSION: Final[SchemaVersion] = cast(SchemaVersion, "1.0")
PROMPT_VERSION: Final[str] = "1.1.0"
MAX_PROMPT_CONFIG_BYTES: Final[int] = 64 * 1_024
MAX_RENDERED_PROMPT_BYTES: Final[int] = 64 * 1_024


class PromptName(StrEnum):
    """Identify one explicitly registered generic server-level prompt."""

    ADMINISTRATOR_ALIGNMENT_REVIEW = "administrator_alignment_review"
    CROSS_FRAMEWORK_COMPARISON = "cross_framework_comparison"
    INFERRED_PROGRESSION_HYPOTHESIS = "inferred_progression_hypothesis"
    MULTIGRADE_LESSON_PLAN = "multigrade_lesson_plan"
    STUDENT_HANDBOOK_SECTION = "student_handbook_section"
    STUDENT_STUDY_SUPPORT = "student_study_support"
    TEACHER_GUIDE_DRAFT = "teacher_guide_draft"


PROMPT_NAMES: Final[tuple[str, ...]] = (
    PromptName.STUDENT_STUDY_SUPPORT.value,
    PromptName.TEACHER_GUIDE_DRAFT.value,
    PromptName.STUDENT_HANDBOOK_SECTION.value,
    PromptName.INFERRED_PROGRESSION_HYPOTHESIS.value,
    PromptName.ADMINISTRATOR_ALIGNMENT_REVIEW.value,
    PromptName.CROSS_FRAMEWORK_COMPARISON.value,
    PromptName.MULTIGRADE_LESSON_PLAN.value,
)


class PromptGuidanceMode(StrEnum):
    """Control how one local soft-guidance block combines with server defaults."""

    APPEND = "append"
    REPLACE = "replace"


class PromptFocusMode(StrEnum):
    """Identify how a prompt's topic-or-standard value should be retrieved."""

    CASE_IDENTIFIER_URI = "case_identifier_uri"
    CASE_IDENTIFIER_UUID = "case_identifier_uuid"
    NODE_ID = "node_id"
    STATEMENT_CODE = "statement_code"
    TOPIC = "topic"


class ComparisonSearchMode(StrEnum):
    """Identify the package-local search mode requested by a comparison prompt."""

    CODE_EXACT = "code_exact"
    CODE_PREFIX = "code_prefix"
    TEXT = "text"


class ProgressionDirection(StrEnum):
    """Identify the requested direction of an inferred progression review."""

    BOTH = "both"
    EARLIER_TO_LATER = "earlier_to_later"
    LATER_TO_EARLIER = "later_to_earlier"


class StudyDifficulty(StrEnum):
    """Identify the requested generated study-support difficulty."""

    EXTENSION = "extension"
    FOUNDATIONAL = "foundational"
    ON_LEVEL = "on_level"


class PromptGuidanceBlock(FrozenSchema):
    """Provide bounded local instructions for one declared soft-guidance section."""

    instructions: tuple[PromptInstruction, ...] = Field(max_length=20, min_length=1)
    mode: PromptGuidanceMode = PromptGuidanceMode.APPEND

    @model_validator(mode="after")
    def validate_instructions(self) -> Self:
        """Require exact local instructions to be unique within the block.

        Returns
        -------
        Self
            Validated immutable guidance block.

        Raises
        ------
        ValueError
            If the block repeats an exact instruction.
        """

        if len(self.instructions) != len(set(self.instructions)):
            raise ValueError("Guidance-block instructions must not contain duplicates.")

        return self


class SharedPromptGuidance(FrozenSchema):
    """Define optional framework-local guidance shared by every generic prompt."""

    language_guidance: PromptGuidanceBlock | None = None
    local_context_guidance: PromptGuidanceBlock | None = None
    output_guidance: PromptGuidanceBlock | None = None
    terminology_guidance: PromptGuidanceBlock | None = None
    warning_guidance: PromptGuidanceBlock | None = None


class StudentStudySupportGuidance(FrozenSchema):
    """Define optional soft guidance for the student-study-support workflow."""

    audience_guidance: PromptGuidanceBlock | None = None
    example_guidance: PromptGuidanceBlock | None = None
    explanation_guidance: PromptGuidanceBlock | None = None
    practice_guidance: PromptGuidanceBlock | None = None


class TeacherGuideDraftGuidance(FrozenSchema):
    """Define optional soft guidance for the teacher-guide workflow."""

    assessment_guidance: PromptGuidanceBlock | None = None
    differentiation_guidance: PromptGuidanceBlock | None = None
    lesson_structure_guidance: PromptGuidanceBlock | None = None
    pedagogy_guidance: PromptGuidanceBlock | None = None


class MultigradeLessonPlanGuidance(FrozenSchema):
    """Define optional soft guidance for the experimental multigrade workflow."""

    differentiation_guidance: PromptGuidanceBlock | None = None
    shared_core_guidance: PromptGuidanceBlock | None = None
    classroom_management_guidance: PromptGuidanceBlock | None = None


class StudentHandbookSectionGuidance(FrozenSchema):
    """Define optional soft guidance for the student-handbook workflow."""

    audience_guidance: PromptGuidanceBlock | None = None
    example_guidance: PromptGuidanceBlock | None = None
    explanation_guidance: PromptGuidanceBlock | None = None
    section_structure_guidance: PromptGuidanceBlock | None = None


class InferredProgressionHypothesisGuidance(FrozenSchema):
    """Define optional soft guidance for the inferred-progression workflow."""

    counter_evidence_guidance: PromptGuidanceBlock | None = None
    evidence_guidance: PromptGuidanceBlock | None = None
    inference_guidance: PromptGuidanceBlock | None = None
    sequence_presentation_guidance: PromptGuidanceBlock | None = None


class AdministratorAlignmentReviewGuidance(FrozenSchema):
    """Define optional soft guidance for the administrator comparison workflow."""

    evidence_matrix_guidance: PromptGuidanceBlock | None = None
    governance_guidance: PromptGuidanceBlock | None = None
    risk_framing_guidance: PromptGuidanceBlock | None = None
    review_question_guidance: PromptGuidanceBlock | None = None


class CrossFrameworkComparisonGuidance(FrozenSchema):
    """Define optional soft guidance for the cross-framework comparison workflow."""

    comparison_dimension_guidance: PromptGuidanceBlock | None = None
    synthesis_guidance: PromptGuidanceBlock | None = None
    terminology_guidance: PromptGuidanceBlock | None = None
    uncertainty_guidance: PromptGuidanceBlock | None = None


class PromptOverlays(FrozenSchema):
    """Group optional framework-local guidance by exact generic prompt name."""

    administrator_alignment_review: AdministratorAlignmentReviewGuidance | None = None
    cross_framework_comparison: CrossFrameworkComparisonGuidance | None = None
    inferred_progression_hypothesis: InferredProgressionHypothesisGuidance | None = None
    multigrade_lesson_plan: MultigradeLessonPlanGuidance | None = None
    student_handbook_section: StudentHandbookSectionGuidance | None = None
    student_study_support: StudentStudySupportGuidance | None = None
    teacher_guide_draft: TeacherGuideDraftGuidance | None = None


class FrameworkPromptConfig(FrozenSchema):
    """Define one exact versioned framework-local prompt-guidance document."""

    framework_ids: tuple[FrameworkId, ...] = Field(max_length=64, min_length=1)
    profile_id: ProfileId
    profile_version: ProfileVersion
    prompt_config_id: PromptConfigId
    prompt_config_schema_version: SchemaVersion = PROMPT_CONFIG_SCHEMA_VERSION
    prompt_config_version: PromptConfigVersion
    prompts: PromptOverlays = Field(default_factory=PromptOverlays)
    shared: SharedPromptGuidance = Field(default_factory=SharedPromptGuidance)

    @model_validator(mode="after")
    def validate_configuration(self) -> Self:
        """Validate schema version, framework uniqueness, and instruction limits.

        Returns
        -------
        Self
            Validated immutable framework prompt configuration.

        Raises
        ------
        ValueError
            If the schema is unsupported, framework IDs repeat, no guidance is present,
            or configured instruction counts exceed the approved limits.
        """

        if self.prompt_config_schema_version != PROMPT_CONFIG_SCHEMA_VERSION:
            raise ValueError(
                f"prompt_config_schema_version must equal {PROMPT_CONFIG_SCHEMA_VERSION}."
            )

        framework_ids = tuple(str(value) for value in self.framework_ids)

        if len(framework_ids) != len(set(framework_ids)):
            raise ValueError("framework_ids must not contain duplicates.")

        shared_count = _count_guidance_instructions(self.shared)
        prompt_counts = (
            _count_guidance_instructions(self.prompts.administrator_alignment_review),
            _count_guidance_instructions(self.prompts.cross_framework_comparison),
            _count_guidance_instructions(self.prompts.inferred_progression_hypothesis),
            _count_guidance_instructions(self.prompts.student_handbook_section),
            _count_guidance_instructions(self.prompts.student_study_support),
            _count_guidance_instructions(self.prompts.teacher_guide_draft),
        )

        if shared_count > 40:
            raise ValueError(
                "Shared prompt guidance may contain at most 40 instructions."
            )

        if any(count > 60 for count in prompt_counts):
            raise ValueError(
                "Each prompt-specific guidance section may contain at most 60 instructions."
            )

        if shared_count + sum(prompt_counts) == 0:
            raise ValueError(
                "A framework prompt configuration must contain at least one guidance instruction."
            )

        return self


@dataclass(frozen=True, slots=True)
class LoadedPromptConfig:
    """Retain one validated prompt configuration and its exact-byte evidence."""

    config: FrameworkPromptConfig
    sha256: Sha256Digest
    source_path: Path


@dataclass(frozen=True, slots=True)
class PromptConfigRegistry:
    """Retain deterministic optional prompt configurations by profile identity."""

    configurations: tuple[LoadedPromptConfig, ...] = ()

    def __post_init__(self) -> None:
        """Require unique profile identities and deterministic configuration order.

        Raises
        ------
        ValueError
            If profile identities repeat or configurations are not in canonical order.
        """

        identities = tuple(
            (
                str(configuration.config.profile_id),
                str(configuration.config.profile_version),
            )
            for configuration in self.configurations
        )

        if len(identities) != len(set(identities)):
            raise ValueError(
                "Prompt configurations must have unique profile identities."
            )

        if identities != tuple(sorted(identities)):
            raise ValueError(
                "Prompt configurations must use deterministic profile-identity order."
            )

    def get(
        self, *, profile_id: ProfileId, profile_version: ProfileVersion
    ) -> LoadedPromptConfig | None:
        """Return optional configuration for one exact profile identity.

        Parameters
        ----------
        profile_id
            Exact selected curriculum-profile identifier.
        profile_version
            Exact selected curriculum-profile version.

        Returns
        -------
        LoadedPromptConfig | None
            Matching loaded configuration, or ``None`` when no file was provided.
        """

        for configuration in self.configurations:
            if (
                configuration.config.profile_id == profile_id
                and configuration.config.profile_version == profile_version
            ):
                return configuration

        return None


class PromptContextEvidence(FrozenSchema):
    """Record one exact package context used by a multi-framework prompt."""

    attribution_statement: str = Field(min_length=1)
    framework_id: FrameworkId
    graph_package_id: GraphPackageId
    graph_type: GraphType
    profile_id: ProfileId
    profile_sha256: Sha256Digest
    profile_version: ProfileVersion
    prompt_config_id: PromptConfigId | None = None
    prompt_config_sha256: Sha256Digest | None = None
    prompt_config_version: PromptConfigVersion | None = None
    rights: RightsPolicy
    snapshot_id: SnapshotId
    source_metadata: CatalogSourceMetadata

    @model_validator(mode="after")
    def validate_context_identity(self) -> Self:
        """Require complete optional configuration and exact attribution evidence.

        Returns
        -------
        Self
            Validated immutable context evidence.

        Raises
        ------
        ValueError
            If configuration identity is partial or attribution differs from rights.
        """

        config_values = (
            self.prompt_config_id,
            self.prompt_config_sha256,
            self.prompt_config_version,
        )

        if any(value is None for value in config_values) and any(
            value is not None for value in config_values
        ):
            raise ValueError(
                "Prompt configuration ID, version, and SHA-256 must be present or "
                "absent together."
            )

        if self.attribution_statement != self.rights.attribution_statement:
            raise ValueError("Prompt attribution must match exact package rights.")

        return self


class MultiContextPromptRenderResult(FrozenSchema):
    """Return one deterministic prompt workflow over multiple exact packages."""

    contexts: tuple[PromptContextEvidence, ...] = Field(max_length=8, min_length=2)
    description: str = Field(min_length=1)
    message: str = Field(min_length=1)
    prompt_name: PromptName
    prompt_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_context_order(self) -> Self:
        """Require distinct frameworks and canonical exact-context order.

        Returns
        -------
        Self
            Validated deterministic multi-context prompt result.

        Raises
        ------
        ValueError
            If frameworks repeat or contexts are not canonically ordered.
        """

        framework_ids = tuple(str(context.framework_id) for context in self.contexts)

        if len(framework_ids) != len(set(framework_ids)):
            raise ValueError("Multi-context prompts require distinct framework IDs.")

        context_keys = tuple(
            (
                str(context.framework_id),
                str(context.snapshot_id),
                str(context.graph_package_id),
            )
            for context in self.contexts
        )

        if context_keys != tuple(sorted(context_keys)):
            raise ValueError("Prompt contexts must use canonical identity order.")

        return self


class PromptRenderResult(FrozenSchema):
    """Return one deterministic transport-independent rendered prompt workflow."""

    description: str = Field(min_length=1)
    framework_id: FrameworkId
    graph_package_id: GraphPackageId
    message: str = Field(min_length=1)
    profile_id: ProfileId
    profile_version: ProfileVersion
    prompt_config_id: PromptConfigId | None = None
    prompt_config_sha256: Sha256Digest | None = None
    prompt_config_version: PromptConfigVersion | None = None
    prompt_name: PromptName
    prompt_version: str = Field(min_length=1)
    snapshot_id: SnapshotId

    @model_validator(mode="after")
    def validate_prompt_configuration_identity(self) -> Self:
        """Require optional prompt-configuration metadata to be all present or absent.

        Returns
        -------
        Self
            Validated immutable rendered-prompt result.

        Raises
        ------
        ValueError
            If only part of the optional prompt-configuration identity is present.
        """

        values = (
            self.prompt_config_id,
            self.prompt_config_sha256,
            self.prompt_config_version,
        )

        if any(value is None for value in values) and any(
            value is not None for value in values
        ):
            raise ValueError(
                "Prompt configuration ID, version, and SHA-256 must be present or "
                "absent together."
            )

        return self
