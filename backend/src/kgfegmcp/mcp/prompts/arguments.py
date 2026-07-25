"""This module defines shared client-visible argument metadata for MCP prompt workflows.

The aliases add static FastMCP prompt guidance without embedding framework-specific
capability or grade decisions. Runtime package and profile policy remains authoritative
because the same public prompts serve many coded, partially coded, and uncoded
frameworks with different local grade systems.
"""

# Standard Library
from typing import Annotated

# Third Party Library
from pydantic import Field

# Package Library
from kgfegmcp.prompts.models import (
    ProgressionGradeFilters,
    PromptFocusMode,
    PromptFocusText,
)

ProgressionLocalGradeLabelsArgument = Annotated[
    ProgressionGradeFilters,
    Field(
        description=(
            "Exact source-facing grade or stage labels. MCP prompt clients send "
            "complex arguments as JSON strings, so enter a JSON array such as "
            '["Grade 1", "Grade 2"]. Do not enter a comma-separated '
            "prose string. Values must match the selected framework snapshot."
        )
    ),
]
ProgressionNormalizedGradesArgument = Annotated[
    ProgressionGradeFilters,
    Field(
        description=(
            "Normalized grade retrieval facets. MCP prompt clients send complex "
            "arguments as JSON strings, so enter a JSON array such as "
            '["1", "2"]. Do not enter a comma-separated prose string. '
            "These are retrieval aids and do not establish grade equivalence."
        )
    ),
]
PromptFocusModeArgument = Annotated[
    PromptFocusMode,
    Field(
        description=(
            "How topic_or_standard should be interpreted. Use 'statement_code' only "
            "when the selected framework reports stable statement-code support. Use "
            "'topic' for source-visible titles or labels, 'node_id' for graph node "
            "UUIDs, 'case_identifier_uuid' for CASE UUIDs, or "
            "'case_identifier_uri' for CASE URIs."
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

__all__ = [
    "ProgressionLocalGradeLabelsArgument",
    "ProgressionNormalizedGradesArgument",
    "PromptFocusModeArgument",
    "PromptFocusTextArgument",
]
