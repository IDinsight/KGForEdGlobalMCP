"""Immutable contracts for tool-accessible paged reads of native resource content.

``read_evidence`` returns the complete authorized ``ResourceDocument`` of one native
resource URI in deterministic UTF-8 windows. These models carry the unchanged native
metadata, one faithful content window and its original-byte position, hashes and
stateless continuation. They contain no routing, policy or filesystem behavior.
"""

# Future Library
from __future__ import annotations

# Standard Library
from typing import Annotated, Literal, TypeAlias

# Third Party Library
from pydantic import Field, StrictInt, StrictStr

# Package Library
from kgfegmcp.domain.identifiers import Sha256Digest
from kgfegmcp.resources.models import ResourceMetadata
from kgfegmcp.schemas import FrozenSchema
from kgfegmcp.tool_results import ToolResultLimits

DEFAULT_EVIDENCE_CONTENT_BYTES = 16_384
MAX_EVIDENCE_CONTENT_BYTES = 32_768

EvidenceCursor: TypeAlias = Annotated[StrictStr, Field(max_length=4096, min_length=1)]


class ReadEvidenceRequest(FrozenSchema):
    """Select one native resource URI and one bounded content window.

    Examples
    --------
    >>> ReadEvidenceRequest(uri="kgfegmcp://catalog").max_content_bytes
    16384
    """

    cursor: EvidenceCursor | None = None
    max_content_bytes: Annotated[
        StrictInt, Field(ge=1, le=MAX_EVIDENCE_CONTENT_BYTES)
    ] = DEFAULT_EVIDENCE_CONTENT_BYTES
    uri: Annotated[StrictStr, Field(max_length=4096, min_length=1)]


class EvidencePage(FrozenSchema):
    """Locate one window in the original UTF-8 bytes and give its continuation."""

    chunk_sha256: Sha256Digest
    end_byte_exclusive: Annotated[StrictInt, Field(ge=0)]
    is_complete: bool
    limits: ToolResultLimits = Field(default_factory=ToolResultLimits)
    max_content_bytes: Annotated[StrictInt, Field(ge=1, le=MAX_EVIDENCE_CONTENT_BYTES)]
    next_cursor: EvidenceCursor | None
    next_request: ReadEvidenceRequest | None
    returned_bytes: Annotated[StrictInt, Field(ge=0)]
    start_byte: Annotated[StrictInt, Field(ge=0)]
    total_bytes: Annotated[StrictInt, Field(ge=0)]


class ReadEvidenceResult(FrozenSchema):
    """Return unchanged native metadata with one faithful decoded content window."""

    content: str
    content_status: Literal["full", "partial"]
    evidence_notice: str = (
        "content is a window of the complete authorized resource. contentStatus is "
        "full only when this window is the entire resource. If page.nextCursor is "
        "present, call read_evidence with page.nextRequest unchanged and join the "
        "windows in order; their bytes reproduce metadata.contentSha256. Native "
        "rights and size limits apply to every call; finish the windows before "
        "relying on a partial record."
    )
    metadata: ResourceMetadata
    page: EvidencePage
