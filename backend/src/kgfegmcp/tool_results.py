"""Encode bounded ordinary tool results without depending on MCP transports."""

# Standard Library
import json

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, Literal

# Package Library
from kgfegmcp.schemas import FrozenSchema

MAX_TOOL_RESULT_BYTES: Final[int] = 1024 * 1024
MAX_TOOL_RESULT_CHARACTERS: Final[int] = 100_000


class ToolResultLimits(FrozenSchema):
    """Describe the fixed ceilings for the complete serialized tool envelope."""

    max_result_bytes: Literal[1048576] = 1048576
    max_result_characters: Literal[100000] = 100000


@dataclass(frozen=True, slots=True)
class ToolResultSize:
    """Measure JSON escaping and overhead in bytes and Unicode code points."""

    byte_length: int
    character_length: int


def canonical_result_text(result: FrozenSchema) -> str:
    """Serialize one validated public result with its complete aliased fields.

    Parameters
    ----------
    result
        Validated result whose field aliases define the structured public contract.

    Returns
    -------
    str
        Canonical compact JSON, preserving Unicode and original array order.
    """

    return json.dumps(
        allow_nan=False,
        ensure_ascii=False,
        obj=result.model_dump(by_alias=True, mode="json"),
        separators=(",", ":"),
        sort_keys=True,
    )


def text_result_envelope(
    *, result: FrozenSchema, text: str | tuple[str, ...]
) -> dict[str, object]:
    """Reserve the full text/structured envelope before candidate admission.

    Parameters
    ----------
    result
        Complete validated public result.
    text
        Single text block or every text block intended for emission.

    Returns
    -------
    dict[str, object]
        Ordinary protocol-shaped envelope including the error flag and metadata slot.

    Notes
    -----
    The null metadata slot and default JSON whitespace conservatively reserve overhead
    omitted by the current compact MCP wire serializer. Adapters also measure their
    actual emitted content and any present metadata before return.
    """

    return {
        "_meta": None,
        "content": [
            {"text": block, "type": "text"}
            for block in ((text,) if isinstance(text, str) else text)
        ],
        "isError": False,
        "structuredContent": result.model_dump(by_alias=True, mode="json"),
    }


def tool_result_size(envelope: Mapping[str, object]) -> ToolResultSize:
    """Measure a complete envelope with conservative JSON serialization overhead.

    Parameters
    ----------
    envelope
        All emitted text, structured data, content blocks, metadata and error flag.

    Returns
    -------
    ToolResultSize
        UTF-8 bytes and Unicode code points including JSON string escaping.

    Notes
    -----
    Default JSON separators reserve whitespace beyond compact wire output. This
    measures the tool result only; JSON-RPC and HTTP framing belong to transports.
    """

    serialized = json.dumps(
        allow_nan=False, ensure_ascii=False, obj=dict(envelope), sort_keys=True
    )
    return ToolResultSize(
        byte_length=len(serialized.encode("utf-8")),
        character_length=len(serialized),
    )
