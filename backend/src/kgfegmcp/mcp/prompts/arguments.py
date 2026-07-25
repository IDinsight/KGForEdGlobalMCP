"""This module defines shared client-visible argument metadata for MCP prompts.

The aliases add static guidance to FastMCP prompt schemas without embedding any
framework-specific capability decisions. Runtime profile policy remains authoritative
because one public prompt must serve coded, partially coded, and uncoded frameworks.
"""

# Standard Library
from typing import Annotated

# Third Party Library
from pydantic import Field

# Package Library
from kgfegmcp.prompts.models import PromptFocusMode, PromptFocusText

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

__all__ = ["PromptFocusModeArgument", "PromptFocusTextArgument"]
