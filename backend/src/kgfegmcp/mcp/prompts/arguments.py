"""This module defines shared client-visible argument metadata for MCP prompts.

The aliases provide concrete runtime annotations for FastMCP, document serialized
collection inputs, and normalize client-supplied blank optional values to each public
prompt endpoint's declared default. The normalization is intentionally limited to the
MCP adapter boundary so ordinary prompt models and services retain their strict domain
contracts.

The module contains no framework-, curriculum-, country-, subject-, grade-, or
language-specific behavior. Runtime package and profile policy remains authoritative
because the same public prompts serve coded, partially coded, and uncoded frameworks
with different local grade systems.
"""

# Standard Library
from dataclasses import dataclass
from typing import Annotated

# Third Party Library
from pydantic import BeforeValidator, Field

# Package Library
from kgfegmcp.domain.identifiers import LanguageTag, SnapshotId
from kgfegmcp.prompts.models import (
    ComparisonFrameworkIds,
    ComparisonGradeFilters,
    ComparisonMatchLimit,
    ComparisonSearchMode,
    ComparisonSnapshotIds,
    HandbookWordCount,
    LessonDurationMinutes,
    MultigradeGradesInRoom,
    PracticeCount,
    ProgressionCandidateLimit,
    ProgressionDirection,
    ProgressionGradeFilters,
    PromptFocusMode,
    PromptFocusText,
    PromptGradeOrStage,
    PromptLearnerContext,
    PromptLocalContext,
    PromptMaterials,
    StudyDifficulty,
)


@dataclass(frozen=True, slots=True)
class _BlankPromptArgumentDefault:
    """Replace a blank MCP prompt argument with one immutable endpoint default."""

    default: object

    def __call__(self, value: object) -> object:
        """Return the declared default for null or whitespace-only client input.

        Parameters
        ----------
        value
            Raw value supplied by the MCP client before ordinary type validation.

        Returns
        -------
        object
            The configured endpoint default for null or blank input; otherwise the
            original value for strict validation by the annotated domain type.
        """

        if value is None:
            return self.default

        if isinstance(value, str) and not value.strip():
            return self.default

        return value


ComparisonFrameworkIdsArgument = Annotated[
    ComparisonFrameworkIds,
    Field(
        description=(
            "Two through eight distinct framework identifiers. MCP prompt clients send "
            "complex arguments as JSON strings, so enter a JSON array such as "
            '["framework-a", "framework-b"]. Do not enter a comma-separated prose '
            "string."
        )
    ),
]
ComparisonGradeFiltersArgument = Annotated[
    ComparisonGradeFilters,
    BeforeValidator(_BlankPromptArgumentDefault(default=())),
    Field(
        description=(
            "Shared exact local or normalized grade/stage filters. Enter a JSON array "
            'such as ["Grade 1", "Grade 2"]. Leave blank to apply no grade filter; '
            "these values are retrieval facets and do not establish equivalence."
        )
    ),
]
MultigradeGradesInRoomArgument = Annotated[
    MultigradeGradesInRoom,
    Field(
        description=(
            "Two to eight distinct grades or stages sharing the classroom. MCP prompt "
            "clients send complex arguments as JSON strings, so enter a JSON array such "
            'as ["4", "5", "6"]. Do not enter a comma-separated prose string.'
        )
    ),
]
ComparisonMatchLimitArgument = Annotated[
    ComparisonMatchLimit, BeforeValidator(_BlankPromptArgumentDefault(default=5))
]
ComparisonSearchModeArgument = Annotated[
    ComparisonSearchMode,
    BeforeValidator(_BlankPromptArgumentDefault(default=ComparisonSearchMode.TEXT)),
]
ComparisonSnapshotIdsArgument = Annotated[
    ComparisonSnapshotIds,
    BeforeValidator(_BlankPromptArgumentDefault(default=())),
    Field(
        description=(
            "Optional exact snapshot identifiers, with at most one selected snapshot "
            "per framework. Enter a JSON array. Leave blank to use unique-current "
            "snapshot routing."
        )
    ),
]
HandbookWordCountArgument = Annotated[
    HandbookWordCount, BeforeValidator(_BlankPromptArgumentDefault(default=500))
]
IncludeContextPathsArgument = Annotated[
    bool, BeforeValidator(_BlankPromptArgumentDefault(default=True))
]
LessonDurationMinutesArgument = Annotated[
    LessonDurationMinutes, BeforeValidator(_BlankPromptArgumentDefault(default=45))
]
OptionalLanguageTagArgument = Annotated[
    LanguageTag | None, BeforeValidator(_BlankPromptArgumentDefault(default=None))
]
OptionalPromptGradeOrStageArgument = Annotated[
    PromptGradeOrStage | None,
    BeforeValidator(_BlankPromptArgumentDefault(default=None)),
]
OptionalPromptLearnerContextArgument = Annotated[
    PromptLearnerContext | None,
    BeforeValidator(_BlankPromptArgumentDefault(default=None)),
]
OptionalPromptLocalContextArgument = Annotated[
    PromptLocalContext | None,
    BeforeValidator(_BlankPromptArgumentDefault(default=None)),
]
OptionalPromptMaterialsArgument = Annotated[
    PromptMaterials | None, BeforeValidator(_BlankPromptArgumentDefault(default=None))
]
OptionalSnapshotIdArgument = Annotated[
    SnapshotId | None, BeforeValidator(_BlankPromptArgumentDefault(default=None))
]
PracticeCountArgument = Annotated[
    PracticeCount, BeforeValidator(_BlankPromptArgumentDefault(default=5))
]
ProgressionCandidateLimitArgument = Annotated[
    ProgressionCandidateLimit, BeforeValidator(_BlankPromptArgumentDefault(default=8))
]
ProgressionDirectionArgument = Annotated[
    ProgressionDirection,
    BeforeValidator(_BlankPromptArgumentDefault(default=ProgressionDirection.BOTH)),
]
ProgressionLocalGradeLabelsArgument = Annotated[
    ProgressionGradeFilters,
    BeforeValidator(_BlankPromptArgumentDefault(default=())),
    Field(
        description=(
            "Exact source-facing grade or stage labels. MCP prompt clients send "
            "complex arguments as JSON strings, so enter a JSON array such as "
            '["Grade 1", "Grade 2"]. Do not enter a comma-separated '
            "prose string. Leave blank to apply no local grade filter. Values must "
            "match the selected framework snapshot."
        )
    ),
]
ProgressionNormalizedGradesArgument = Annotated[
    ProgressionGradeFilters,
    BeforeValidator(_BlankPromptArgumentDefault(default=())),
    Field(
        description=(
            "Normalized grade retrieval facets. MCP prompt clients send complex "
            "arguments as JSON strings, so enter a JSON array such as "
            '["1", "2"]. Do not enter a comma-separated prose string. Leave blank '
            "to apply no normalized grade filter. These are retrieval aids and do not "
            "establish grade equivalence."
        )
    ),
]
PromptFocusModeArgument = Annotated[
    PromptFocusMode,
    BeforeValidator(_BlankPromptArgumentDefault(default=PromptFocusMode.TOPIC)),
    Field(
        description=(
            "How topic_or_standard should be interpreted. Use 'statement_code' only "
            "when the selected framework reports stable statement-code support. Use "
            "'topic' for source-visible titles or labels, 'node_id' for graph node "
            "UUIDs, 'case_identifier_uuid' for CASE UUIDs, or "
            "'case_identifier_uri' for CASE URIs. Leave blank to use 'topic'."
        )
    ),
]
PromptFocusTextArgument = Annotated[
    PromptFocusText,
    Field(
        description=(
            "The focus value interpreted according to focus_mode. Enter topic text or "
            "a visible label for 'topic', a stable framework code for "
            "'statement_code', a graph node UUID for 'node_id', or the matching exact "
            "CASE identifier for a CASE mode."
        )
    ),
]
StudyDifficultyArgument = Annotated[
    StudyDifficulty,
    BeforeValidator(_BlankPromptArgumentDefault(default=StudyDifficulty.ON_LEVEL)),
]

__all__ = [
    "ComparisonFrameworkIdsArgument",
    "ComparisonGradeFiltersArgument",
    "ComparisonMatchLimitArgument",
    "ComparisonSearchModeArgument",
    "ComparisonSnapshotIdsArgument",
    "HandbookWordCountArgument",
    "IncludeContextPathsArgument",
    "LessonDurationMinutesArgument",
    "OptionalLanguageTagArgument",
    "MultigradeGradesInRoomArgument",
    "OptionalPromptGradeOrStageArgument",
    "OptionalPromptLearnerContextArgument",
    "OptionalPromptLocalContextArgument",
    "OptionalPromptMaterialsArgument",
    "OptionalSnapshotIdArgument",
    "PracticeCountArgument",
    "ProgressionCandidateLimitArgument",
    "ProgressionDirectionArgument",
    "ProgressionLocalGradeLabelsArgument",
    "ProgressionNormalizedGradesArgument",
    "PromptFocusModeArgument",
    "PromptFocusTextArgument",
    "StudyDifficultyArgument",
]
