"""Page authorized native resource content for tool-only clients.

``read_evidence_window`` accepts exactly the Catalog URI and the fourteen native
``kgfegmcp://`` resource templates. It validates and decodes each identifier segment
once, calls the matching ``ResourceService`` method directly (so rights, artifact
allowlists, safe reads and native size limits apply unchanged), and then returns one
deterministic UTF-8 window of the complete authorized document with stateless,
checksum-bound continuation. It never reads files, opens a client or reapplies a
separate policy.
"""

# Future Library
from __future__ import annotations

# Standard Library
import base64
import hashlib
import json
import re

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Annotated, Any, Final, Literal, cast
from urllib.parse import unquote

# Third Party Library
from pydantic import Field, StrictInt, TypeAdapter, ValidationError

# Package Library
from kgfegmcp.domain.identifiers import (
    ArtifactName,
    FrameworkId,
    NodeId,
    RelationshipId,
    Sha256Digest,
    SnapshotId,
)
from kgfegmcp.errors import (
    EvidenceResultTooLargeError,
    InvalidCursorError,
    InvalidEvidenceUriError,
    UnsupportedEvidenceFormatError,
)
from kgfegmcp.packages.checksums import calculate_bytes_sha256
from kgfegmcp.resources.evidence_models import (
    EvidencePage,
    ReadEvidenceRequest,
    ReadEvidenceResult,
)
from kgfegmcp.resources.models import ResourceDocument, ResourceMetadata
from kgfegmcp.resources.service import ResourceService
from kgfegmcp.schemas import FrozenSchema
from kgfegmcp.tool_results import (
    MAX_TOOL_RESULT_BYTES,
    MAX_TOOL_RESULT_CHARACTERS,
    canonical_result_text,
    text_result_envelope,
    tool_result_size,
)

_ARTIFACT_NAME: Final[TypeAdapter[ArtifactName]] = TypeAdapter(ArtifactName)
_FRAMEWORK_ID: Final[TypeAdapter[FrameworkId]] = TypeAdapter(FrameworkId)
_NODE_ID: Final[TypeAdapter[NodeId]] = TypeAdapter(NodeId)
_RELATIONSHIP_ID: Final[TypeAdapter[RelationshipId]] = TypeAdapter(RelationshipId)
_SNAPSHOT_ID: Final[TypeAdapter[SnapshotId]] = TypeAdapter(SnapshotId)

_PREFIX: Final[str] = "kgfegmcp://"

# RFC 3986 path-segment characters: unreserved, sub-delims, ":", "@" or an escape.
_SEGMENT_RE: Final[re.Pattern[str]] = re.compile(
    r"(?:[A-Za-z0-9\-._~!$&'()*+,;=:@]|%[0-9A-Fa-f]{2})+"
)

_Reader = Callable[[ResourceService], ResourceDocument]

# Snapshot-level documents: .../snapshot/{snapshot_id}/<leaf>.
_SNAPSHOT_READERS: Final[Mapping[str, str]] = {
    "interpretation-profile": "interpretation_profile",
    "learning-progressions": "learning_progressions",
    "manifest": "manifest",
    "unresolved": "unresolved",
    "validation": "validation",
}

# Identified documents: .../snapshot/{snapshot_id}/<kind>/{identifier}[/<leaf>].
_IDENTIFIED_READERS: Final[Mapping[tuple[str, str | None], tuple[str, str]]] = {
    ("artifact", None): ("artifact", "artifact_name"),
    ("learning-component", "provenance"): (
        "learning_component_provenance",
        "node_id",
    ),
    ("learning-component", None): ("learning_component", "node_id"),
    ("relationship", "provenance"): ("relationship_provenance", "relationship_id"),
    ("relationship", None): ("relationship", "relationship_id"),
    ("standard", "learning-components"): ("standard_learning_components", "node_id"),
    ("standard", "provenance"): ("standard_provenance", "node_id"),
    ("standard", None): ("standard", "node_id"),
}

_IDENTIFIER_ADAPTERS: Final[Mapping[str, TypeAdapter[Any]]] = {
    "artifact_name": _ARTIFACT_NAME,
    "node_id": _NODE_ID,
    "relationship_id": _RELATIONSHIP_ID,
}


class _CursorState(FrozenSchema):
    """Bind the next UTF-8 boundary to exact resource and request identity."""

    canonical_uri: str
    content_sha256: Sha256Digest
    cursor_kind: Literal["evidence_v1"] = "evidence_v1"
    max_content_bytes: Annotated[StrictInt, Field(ge=1)]
    metadata_sha256: Sha256Digest
    position: Annotated[StrictInt, Field(ge=1)]
    version: Annotated[StrictInt, Field(ge=1, le=1)] = 1


class _SignedCursorState(_CursorState):
    """Retain the canonical payload checksum under existing cursor conventions."""

    payload_sha256: Sha256Digest


@dataclass(frozen=True, slots=True)
class _Window:
    """Pin one authorized document's bytes and identity for window selection."""

    data: bytes
    metadata: ResourceMetadata
    metadata_sha256: Sha256Digest
    request: ReadEvidenceRequest


def _boundary_before(*, data: bytes, position: int) -> int:
    """Move back to the nearest UTF-8 scalar boundary at or before a byte offset.

    Parameters
    ----------
    data
        Complete valid UTF-8 bytes.
    position
        Candidate end offset, at most ``len(data)``.

    Returns
    -------
    int
        Largest offset not inside a multi-byte scalar.
    """

    # Continuation bytes have the bit pattern 10xxxxxx.
    while 0 < position < len(data) and data[position] & 0xC0 == 0x80:
        position -= 1

    return position


def _canonical_hash(payload: object) -> Sha256Digest:
    """Hash compact sorted public JSON using the established cursor convention.

    Parameters
    ----------
    payload
        JSON-compatible identity data.

    Returns
    -------
    Sha256Digest
        Qualified deterministic SHA-256.
    """

    encoded = json.dumps(
        ensure_ascii=False, obj=payload, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return cast(Sha256Digest, "sha256:" + hashlib.sha256(encoded).hexdigest())


def _cursor_position(*, window: _Window) -> int:
    """Validate a continuation against the current authorized document.

    Parameters
    ----------
    window
        Current document bytes, metadata identity and request.

    Returns
    -------
    int
        Verified next window start, or zero for a new read.

    Raises
    ------
    InvalidCursorError
        If shape, checksum, identity, request size, range or boundary is invalid.
    """

    cursor = window.request.cursor

    if cursor is None:
        return 0

    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))

        if base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=") != cursor:
            raise ValueError("Noncanonical cursor encoding")

        state = _SignedCursorState.model_validate(json.loads(raw.decode("utf-8")))
    except (ValidationError, ValueError) as error:
        raise InvalidCursorError(
            message="The evidence continuation cursor is malformed."
        ) from error

    unsigned = state.model_dump(by_alias=True, exclude={"payload_sha256"}, mode="json")
    position = state.position

    if (
        state.payload_sha256 != _canonical_hash(payload=unsigned)
        or state.canonical_uri != window.metadata.canonical_uri
        or state.content_sha256 != window.metadata.content_sha256
        or state.metadata_sha256 != window.metadata_sha256
        or state.max_content_bytes != window.request.max_content_bytes
        or position >= len(window.data)
        or _boundary_before(data=window.data, position=position) != position
    ):
        raise InvalidCursorError(
            message="The evidence cursor does not match this resource or request.",
            recovery_hint=(
                "Restart read_evidence without a cursor, keeping uri and "
                "maxContentBytes unchanged."
            ),
        )

    return position


def _decoded_identifier(*, adapter: TypeAdapter[Any], segment: str) -> Any:
    """Decode one escaped path segment exactly once and validate its identifier type.

    Parameters
    ----------
    adapter
        Existing identifier type for this template position.
    segment
        Raw percent-encoded path segment.

    Returns
    -------
    Any
        Validated typed identifier.

    Raises
    ------
    InvalidEvidenceUriError
        If escaping, decoding or identifier validation fails.
    """

    if not _SEGMENT_RE.fullmatch(segment):
        raise _invalid_uri()

    try:
        decoded = unquote(errors="strict", string=segment)
    except UnicodeDecodeError as error:
        raise _invalid_uri() from error

    # Encoded separators and dot segments would address a different path shape.
    if "/" in decoded or "\\" in decoded or decoded in {".", ".."}:
        raise _invalid_uri()

    try:
        return adapter.validate_python(decoded)
    except ValidationError as error:
        raise _invalid_uri() from error


def _encode_cursor(*, position: int, window: _Window) -> str:
    """Encode the checksum-bound next boundary statelessly.

    Parameters
    ----------
    position
        Next window start, a UTF-8 boundary inside the document.
    window
        Current document identity and request.

    Returns
    -------
    str
        Bounded unpadded base64url continuation.
    """

    state = _CursorState(
        canonical_uri=window.metadata.canonical_uri,
        content_sha256=window.metadata.content_sha256,
        max_content_bytes=window.request.max_content_bytes,
        metadata_sha256=window.metadata_sha256,
        position=position,
    )
    payload = state.model_dump(by_alias=True, mode="json")
    signed = _SignedCursorState(
        **state.model_dump(), payload_sha256=_canonical_hash(payload=payload)
    )
    raw = json.dumps(
        ensure_ascii=False,
        obj=signed.model_dump(by_alias=True, mode="json"),
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _fits(result: ReadEvidenceResult) -> bool:
    """Report whether the complete text and structured envelope fits both ceilings.

    Parameters
    ----------
    result
        Candidate window result.

    Returns
    -------
    bool
        True when both the byte and character ceilings hold.
    """

    size = tool_result_size(
        text_result_envelope(result=result, text=evidence_result_text(result))
    )
    return (
        size.byte_length <= MAX_TOOL_RESULT_BYTES
        and size.character_length <= MAX_TOOL_RESULT_CHARACTERS
    )


def _invalid_uri() -> InvalidEvidenceUriError:
    """Build the stable invalid-URI failure without echoing caller input.

    Returns
    -------
    InvalidEvidenceUriError
        Safe public error naming the supported URI forms.
    """

    return InvalidEvidenceUriError(
        message="The evidence URI is not a supported kgfegmcp resource address.",
        recovery_hint=(
            "Use a resource URI copied unchanged from a tool result, or "
            "kgfegmcp://catalog; queries, fragments, ports and extra segments are "
            "not accepted."
        ),
    )


def _largest_fitting_end(*, first: int, last: int, start: int, window: _Window) -> int:
    """Find the largest Unicode-aligned window end that fits both envelope ceilings.

    Parameters
    ----------
    first
        End of the first scalar; a window ending here is known to fit.
    last
        Aligned end allowed by maxContentBytes.
    start
        Window start boundary.
    window
        Current document bytes, identity and request.

    Returns
    -------
    int
        Exclusive window end between ``first`` and ``last``.
    """

    if _fits(_result(end=last, start=start, window=window)):
        return last

    # Invariant: an aligned end at ``low`` fits and one at ``high`` does not. Window
    # size grows with the end offset, so the search is monotonic.
    low, high = first, last

    while high - low > 1:
        middle = (low + high) // 2
        aligned = _boundary_before(data=window.data, position=middle)

        if _fits(_result(end=aligned, start=start, window=window)):
            low = middle
        else:
            high = middle

    return _boundary_before(data=window.data, position=low)


def _result(*, end: int, start: int, window: _Window) -> ReadEvidenceResult:
    """Build one window result with its real continuation.

    Parameters
    ----------
    end
        Exclusive UTF-8 boundary ending the window.
    start
        UTF-8 boundary starting the window.
    window
        Current document bytes, identity and request.

    Returns
    -------
    ReadEvidenceResult
        Faithful content window, offsets, hashes and continuation.
    """

    total = len(window.data)
    chunk = window.data[start:end]
    next_cursor = _encode_cursor(position=end, window=window) if end < total else None
    return ReadEvidenceResult(
        content=chunk.decode("utf-8"),
        content_status="full" if start == 0 and end == total else "partial",
        metadata=window.metadata,
        page=EvidencePage(
            chunk_sha256=calculate_bytes_sha256(chunk),
            end_byte_exclusive=end,
            is_complete=end == total,
            max_content_bytes=window.request.max_content_bytes,
            next_cursor=next_cursor,
            next_request=(
                window.request.model_copy(update={"cursor": next_cursor})
                if next_cursor is not None
                else None
            ),
            returned_bytes=end - start,
            start_byte=start,
            total_bytes=total,
        ),
    )


def _route(uri: str) -> _Reader:
    """Match exactly one native resource template and bind validated identifiers.

    Parameters
    ----------
    uri
        Caller-supplied resource URI.

    Returns
    -------
    _Reader
        Direct ResourceService call for the matched template.

    Raises
    ------
    InvalidEvidenceUriError
        If the URI is not exactly one supported template.
    """

    if not uri.startswith(_PREFIX) or "?" in uri or "#" in uri:
        raise _invalid_uri()

    if uri == _PREFIX + "catalog":
        return lambda service: service.catalog()

    # The authority must be exactly "framework": userinfo or ports never match.
    segments = uri[len(_PREFIX) :].split("/")

    if segments[0] != "framework" or len(segments) < 2:
        raise _invalid_uri()

    framework_id = _decoded_identifier(adapter=_FRAMEWORK_ID, segment=segments[1])

    if len(segments) == 2:
        return lambda service: service.framework(framework_id)

    if len(segments) < 5 or segments[2] != "snapshot":
        raise _invalid_uri()

    snapshot_id = _decoded_identifier(adapter=_SNAPSHOT_ID, segment=segments[3])
    return _snapshot_route(
        framework_id=framework_id, rest=segments[4:], snapshot_id=snapshot_id
    )


def _snapshot_route(
    *, framework_id: FrameworkId, rest: list[str], snapshot_id: SnapshotId
) -> _Reader:
    """Match the snapshot-scoped remainder of a native resource template.

    Parameters
    ----------
    framework_id
        Validated exact framework identifier.
    rest
        Raw path segments after the snapshot segment.
    snapshot_id
        Validated exact snapshot identifier; never replaced by a current snapshot.

    Returns
    -------
    _Reader
        Direct ResourceService call for the matched template.

    Raises
    ------
    InvalidEvidenceUriError
        If the remainder is not exactly one supported template.
    """

    pinned = {"framework_id": framework_id, "snapshot_id": snapshot_id}

    if len(rest) == 1 and rest[0] in _SNAPSHOT_READERS:
        method = _SNAPSHOT_READERS[rest[0]]
        return lambda service: getattr(service, method)(**pinned)

    if len(rest) not in {2, 3}:
        raise _invalid_uri()

    leaf = rest[2] if len(rest) == 3 else None
    reader = _IDENTIFIED_READERS.get((rest[0], leaf))

    if reader is None:
        raise _invalid_uri()

    method, parameter = reader
    identifier = _decoded_identifier(
        adapter=_IDENTIFIER_ADAPTERS[parameter], segment=rest[1]
    )
    return lambda service: getattr(service, method)(**pinned, **{parameter: identifier})


def _utf8_window(document: ResourceDocument, request: ReadEvidenceRequest) -> _Window:
    """Require UTF-8 content and pin the authorized document's exact identity.

    Parameters
    ----------
    document
        Complete authorized native resource document.
    request
        Validated tool request.

    Returns
    -------
    _Window
        Exact bytes, unchanged metadata and its identity hash.

    Raises
    ------
    UnsupportedEvidenceFormatError
        If the authorized bytes are not valid UTF-8 text.
    """

    data = (
        document.content.encode("utf-8")
        if isinstance(document.content, str)
        else document.content
    )

    try:
        data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise UnsupportedEvidenceFormatError(
            message="This resource is not UTF-8 text and cannot be paged as evidence.",
            recovery_hint="Read it through the native resource instead.",
        ) from error

    return _Window(
        data=data,
        metadata=document.metadata,
        metadata_sha256=_canonical_hash(
            payload=document.metadata.model_dump(by_alias=True, mode="json")
        ),
        request=request,
    )


def evidence_result_text(result: ReadEvidenceResult) -> str:
    """Mirror the complete bounded evidence result as canonical ordinary JSON.

    Parameters
    ----------
    result
        Typed evidence window result.

    Returns
    -------
    str
        JSON text whose parsed value equals the aliased structured result.
    """

    return canonical_result_text(result)


def read_evidence_window(
    *, request: ReadEvidenceRequest, resource_service: ResourceService
) -> ReadEvidenceResult:
    """Return one deterministic window of a complete authorized native resource.

    Parameters
    ----------
    request
        URI, window size and optional continuation cursor.
    resource_service
        Shared native resource service; its policy and limits apply unchanged.

    Returns
    -------
    ReadEvidenceResult
        Largest Unicode-aligned window within maxContentBytes and both envelope
        ceilings, with exact offsets, hashes and continuation.

    Raises
    ------
    EvidenceResultTooLargeError
        If not even the next Unicode scalar can be returned.

    Examples
    --------
    >>> result = read_evidence_window(
    ...     request=ReadEvidenceRequest(uri="kgfegmcp://catalog"),
    ...     resource_service=state.resource_service,
    ... )
    >>> result.page.start_byte
    0
    """

    # Native authorization and limits run on every call, including continuations.
    window = _utf8_window(_route(request.uri)(resource_service), request)
    start = _cursor_position(window=window)
    total = len(window.data)

    if not total:
        return _result(end=0, start=0, window=window)

    # The Unicode scalar starting at ``start`` ends at the next boundary after it.
    first = start + 1

    while first < total and window.data[first] & 0xC0 == 0x80:
        first += 1

    end = _boundary_before(
        data=window.data, position=min(start + request.max_content_bytes, total)
    )

    if end < first or not _fits(_result(end=first, start=start, window=window)):
        raise EvidenceResultTooLargeError(
            message="The next evidence character cannot fit in one tool result.",
            recovery_hint=(
                "Increase maxContentBytes, or read the resource natively under its "
                "rights and size limits."
            ),
        )

    return _result(
        end=_largest_fitting_end(first=first, last=end, start=start, window=window),
        start=start,
        window=window,
    )


def require_evidence_result_size(envelope: Mapping[str, object]) -> None:
    """Enforce both ceilings on the actual emitted tool envelope.

    Parameters
    ----------
    envelope
        Actual adapter envelope including text, structured content and metadata.

    Raises
    ------
    EvidenceResultTooLargeError
        If the emitted envelope exceeds either ceiling.
    """

    size = tool_result_size(envelope)

    if (
        size.byte_length > MAX_TOOL_RESULT_BYTES
        or size.character_length > MAX_TOOL_RESULT_CHARACTERS
    ):
        raise EvidenceResultTooLargeError(
            details={
                "actual_bytes": size.byte_length,
                "actual_characters": size.character_length,
            },
            message="The evidence window exceeds the tool envelope ceiling.",
            recovery_hint="Retry with a smaller maxContentBytes.",
        )
