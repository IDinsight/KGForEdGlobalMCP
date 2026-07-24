"""This module defines immutable contracts for generic MCP prompt workflows.

The models in this module describe prompt names and parameters, optional versioned
framework-local prompt guidance, loaded prompt-configuration evidence, and rendered
prompt results. Framework-local configuration is selected by exact curriculum-profile
identity and may modify only declared soft-guidance sections.

These contracts are curriculum-agnostic. They do not access the filesystem, resolve
catalog packages, enforce rights, search standards, traverse graphs, render FastMCP
messages, or register MCP components.
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
from kgfegmcp.domain.identifiers import (
    FrameworkId,
    GraphPackageId,
    ProfileId,
    ProfileVersion,
    SchemaVersion,
    Sha256Digest,
    SnapshotId,
)
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
PROMPT_VERSION: Final[str] = "1.0.0"
MAX_PROMPT_CONFIG_BYTES: Final[int] = 64 * 1_024
MAX_RENDERED_PROMPT_BYTES: Final[int] = 64 * 1_024


class PromptName(StrEnum):
    """Identify one explicitly registered generic server-level prompt."""

    INFERRED_PROGRESSION_HYPOTHESIS = "inferred_progression_hypothesis"
    STUDENT_HANDBOOK_SECTION = "student_handbook_section"
    STUDENT_STUDY_SUPPORT = "student_study_support"
    TEACHER_GUIDE_DRAFT = "teacher_guide_draft"


PROMPT_NAMES: Final[tuple[str, ...]] = (
    PromptName.STUDENT_STUDY_SUPPORT.value,
    PromptName.TEACHER_GUIDE_DRAFT.value,
    PromptName.STUDENT_HANDBOOK_SECTION.value,
    PromptName.INFERRED_PROGRESSION_HYPOTHESIS.value,
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


class PromptOverlays(FrozenSchema):
    """Group optional framework-local guidance by exact generic prompt name."""

    inferred_progression_hypothesis: InferredProgressionHypothesisGuidance | None = None
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
