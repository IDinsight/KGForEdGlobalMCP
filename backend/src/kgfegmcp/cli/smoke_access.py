"""Check text-only evidence and workflow access through any connected transport.

Tool-only clients read ordinary text, not structured content. These checks parse every
tool result from its text block alone, require it to equal the structured content, and
then follow real continuation requests copied from that text: LP discovery pages and
``read_evidence`` windows. They read representative full provenance and LP reports
through ``read_evidence``, compare them with native resource reads, compare
``get_workflow_instructions`` with native prompts, and require stable typed failures.
It is a protocol check, not domain acceptance.
"""

# Future Library
from __future__ import annotations

# Standard Library
import base64
import hashlib
import json
import re

from typing import Any, Final, cast

# Third Party Library
from fastmcp import Client

# Package Library
from kgfegmcp.domain.identifiers import FrameworkId, NodeId, SnapshotId
from kgfegmcp.tool_results import MAX_TOOL_RESULT_BYTES, MAX_TOOL_RESULT_CHARACTERS

_DIAGNOSTIC_EDGE_ID: Final[str] = "0129f5d5-42fd-52cb-bcf2-ec07c47103e7"
_DIAGNOSTIC_FRAMEWORK_ID: Final[FrameworkId] = cast(
    FrameworkId, "nigeria-nerdc-mathematics-primary-1-3"
)
_DIAGNOSTIC_SNAPSHOT_ID: Final[SnapshotId] = cast(
    SnapshotId, "nigeria-nerdc-mathematics-primary-1-3@undated+bc5e769ed26f"
)
_DIAGNOSTIC_TARGET_ID: Final[NodeId] = cast(
    NodeId, "e399b510-48bb-58ee-abda-61460a5a853b"
)

# Accepted LP reports with stored review/warning evidence that must stay visible.
_REPORT_EXPECTATIONS: Final[tuple[tuple[str, str, str, int], ...]] = (
    (
        "india-cbse-science-learning-framework-classes-9-10",
        "india-cbse-science-learning-framework-classes-9-10@undated+576740bed2d1",
        "needsReviewClaims",
        1,
    ),
    (
        "ghana-nacca-primary-mathematics-basic-4-6",
        "ghana-nacca-primary-mathematics-basic-4-6@2019+0b768f7cfaf9",
        "unresolvedWarningPairs",
        141,
    ),
    (
        "ghana-nacca-primary-english-language-basic-1-3",
        "ghana-nacca-primary-english-language-basic-1-3@2019+e00c5329a507",
        "unresolvedWarningPairs",
        10,
    ),
)

_EVIDENCE_WINDOW_BYTES: Final[int] = 4096
_MAX_WINDOWS: Final[int] = 64
_MAX_PAGES: Final[int] = 3


async def _call_text(
    *, client: Client, name: str, request: object
) -> tuple[dict[str, Any], int]:
    """Call one tool and parse its ordinary text independently of structured content.

    Parameters
    ----------
    client
        Connected transport client.
    name
        Tool name.
    request
        Nested request body.

    Returns
    -------
    tuple[dict[str, Any], int]
        Result parsed from text, and the serialized tool-result character count.

    Raises
    ------
    RuntimeError
        If the call fails, text is not JSON, or text differs from structured content.
    """

    result = await client.call_tool_mcp(name=name, arguments={"request": request})
    text = str(getattr(result.content[0], "text", "")) if result.content else ""

    if result.isError:
        raise RuntimeError(f"Access smoke tool failed: {name}: {text[:200]}")

    parsed = json.loads(text)

    if parsed != result.structuredContent:
        raise RuntimeError(f"Ordinary text differs from structured content: {name}.")

    serialized = result.model_dump_json(by_alias=True, exclude_none=True)

    if (
        len(serialized) > MAX_TOOL_RESULT_CHARACTERS
        or len(serialized.encode("utf-8")) > MAX_TOOL_RESULT_BYTES
    ):
        raise RuntimeError(f"Tool result exceeds the envelope ceilings: {name}.")

    return parsed, len(serialized)


async def _expect_error(
    *, client: Client, code: str, name: str, request: object
) -> None:
    """Require one explicit typed failure in ordinary text.

    Parameters
    ----------
    client
        Connected transport client.
    code
        Expected stable error code.
    name
        Tool name.
    request
        Invalid or denied request body.

    Raises
    ------
    RuntimeError
        If the call succeeds or reports a different error.
    """

    result = await client.call_tool_mcp(name=name, arguments={"request": request})

    if not result.isError or code not in str(result.content):
        raise RuntimeError(f"Expected {code} from {name}.")


async def _read_evidence(*, client: Client, uri: str) -> dict[str, object]:
    """Read one resource completely by replaying text-only nextRequest values.

    Parameters
    ----------
    client
        Connected transport client.
    uri
        Exact native resource URI.

    Returns
    -------
    dict[str, object]
        Window count, byte count, content hash and largest result size.

    Raises
    ------
    RuntimeError
        If windows are not contiguous, repeat a cursor, exceed the bound, or do not
        reproduce the native resource content and its hash.
    """

    request: object = {"maxContentBytes": _EVIDENCE_WINDOW_BYTES, "uri": uri}
    joined = b""
    cursors: set[str] = set()
    largest = 0
    parsed: dict[str, Any] = {}

    for _ in range(_MAX_WINDOWS):
        parsed, size = await _call_text(
            client=client, name="read_evidence", request=request
        )
        largest = max(largest, size)
        page = parsed["page"]

        if page["startByte"] != len(joined):
            raise RuntimeError(f"Evidence windows are not contiguous: {uri}.")

        joined += parsed["content"].encode("utf-8")

        if page["isComplete"]:
            break

        if page["nextCursor"] in cursors:
            raise RuntimeError(f"Evidence cursor repeated: {uri}.")

        cursors.add(page["nextCursor"])
        request = page["nextRequest"]
    else:
        raise RuntimeError(f"Evidence did not complete within the window bound: {uri}.")

    digest = "sha256:" + hashlib.sha256(joined).hexdigest()
    native = (await client.read_resource(uri))[0]

    # Raw source artifacts arrive as base64 blobs, derived documents as text.
    blob = getattr(native, "blob", None)
    native_bytes = (
        base64.b64decode(blob)
        if blob is not None
        else str(getattr(native, "text", "")).encode("utf-8")
    )

    if digest != parsed["metadata"]["contentSha256"] or native_bytes != joined:
        raise RuntimeError(f"Evidence windows differ from the native resource: {uri}.")

    return {
        "bytes": len(joined),
        "contentSha256": digest,
        "largestResultCharacters": largest,
        "uri": uri,
        "windows": len(cursors) + 1,
    }


async def _replay_search(client: Client) -> dict[str, object]:
    """Follow real LP discovery continuation copied from ordinary text.

    Parameters
    ----------
    client
        Connected transport client.

    Returns
    -------
    dict[str, object]
        Pages read and distinct relationship count.

    Raises
    ------
    RuntimeError
        If a replayed page repeats an edge or a cursor.
    """

    request: object = {
        "frameworkId": _DIAGNOSTIC_FRAMEWORK_ID,
        "limit": 5,
        "relationshipTypes": ["buildsTowards"],
        "snapshotId": _DIAGNOSTIC_SNAPSHOT_ID,
    }
    seen: list[str] = []
    cursors: set[str] = set()
    pages = 0

    for _ in range(_MAX_PAGES):
        pages += 1
        parsed, _size = await _call_text(
            client=client, name="search_learning_progressions", request=request
        )
        seen.extend(
            str(item["relationship"]["relationshipId"])
            for item in parsed["relationships"]
        )
        cursor = parsed["page"]["nextCursor"]

        if cursor is None:
            break

        if cursor in cursors:
            raise RuntimeError("LP discovery cursor repeated.")

        cursors.add(cursor)
        request = parsed["page"]["nextRequest"]

    if len(seen) != len(set(seen)) or len(seen) < 2:
        raise RuntimeError("LP discovery replay lost or repeated stored edges.")

    return {"edges": len(seen), "pages": pages}


async def _workflow_parity(client: Client) -> dict[str, int]:
    """Require tool-rendered workflow instructions to equal native prompt messages.

    Parameters
    ----------
    client
        Connected transport client.

    Returns
    -------
    dict[str, int]
        Rendered message length per checked workflow.

    Raises
    ------
    RuntimeError
        If a tool-rendered message differs from its native prompt.
    """

    target = {"identifierType": "node_id", "nodeId": _DIAGNOSTIC_TARGET_ID}
    cases = (
        (
            "learning_progression_support_plan",
            {"frameworkId": _DIAGNOSTIC_FRAMEWORK_ID, "identifier": target},
            {
                "framework_id": _DIAGNOSTIC_FRAMEWORK_ID,
                "identifier": json.dumps(target),
            },
        ),
        (
            "teacher_guide_draft",
            {
                "frameworkId": _DIAGNOSTIC_FRAMEWORK_ID,
                "gradeOrStage": "1",
                "topicOrStandard": "number",
            },
            {
                "framework_id": _DIAGNOSTIC_FRAMEWORK_ID,
                "grade_or_stage": "1",
                "topic_or_standard": "number",
            },
        ),
    )
    lengths: dict[str, int] = {}

    for name, request, arguments in cases:
        parsed, _size = await _call_text(
            client=client,
            name="get_workflow_instructions",
            request={"workflowName": name, **request},
        )
        native = await client.get_prompt(name, arguments)
        message = getattr(native.messages[0].content, "text", None)

        if parsed["rendered"]["message"] != message:
            raise RuntimeError(f"Workflow instructions differ from native: {name}.")

        lengths[name] = len(message.encode("utf-8"))

    return lengths


async def _plain_text(*, client: Client, name: str, request: object) -> str:
    """Return the ordinary text of a human-readable AS/LC tool result.

    Parameters
    ----------
    client
        Connected transport client.
    name
        Tool name.
    request
        Nested request body.

    Returns
    -------
    str
        First text block, exactly as a text-only client sees it.

    Raises
    ------
    RuntimeError
        If the call fails.
    """

    result = await client.call_tool_mcp(name=name, arguments={"request": request})
    text = str(getattr(result.content[0], "text", "")) if result.content else ""

    if result.isError:
        raise RuntimeError(f"Access smoke tool failed: {name}: {text[:200]}")

    return text


def _text_match(*, label: str, pattern: str, text: str) -> str:
    """Extract one value a text-only client would read from tool or prompt text.

    Parameters
    ----------
    label
        Human-readable name for error reporting.
    pattern
        Regular expression with one capture group.
    text
        Ordinary text.

    Returns
    -------
    str
        Captured value.

    Raises
    ------
    RuntimeError
        If the text does not show the value.
    """

    match = re.search(pattern, text, re.MULTILINE)

    if match is None:
        raise RuntimeError(f"Tool-only text does not show {label}.")

    return match.group(1)


async def _text_evidence_links(client: Client) -> dict[str, str]:
    """Build AS/LC evidence URIs only from instructions and ordinary tool text.

    Parameters
    ----------
    client
        Connected transport client.

    Returns
    -------
    dict[str, str]
        Exact URIs a text-only client can read, keyed by evidence family.
    """

    target = {"identifierType": "node_id", "nodeId": _DIAGNOSTIC_TARGET_ID}
    route = {"frameworkId": _DIAGNOSTIC_FRAMEWORK_ID, "identifier": target}
    instructions, _size = await _call_text(
        client=client,
        name="get_workflow_instructions",
        request={**route, "workflowName": "learning_progression_support_plan"},
    )
    message = str(instructions["rendered"]["message"])
    links = dict(
        re.findall(
            r"^- ([A-Za-z ]+): (kgfegmcp://\S+)$",
            message[message.index("EVIDENCE LINKS") :],
            re.MULTILINE,
        )
    )
    node_id = _text_match(
        label="the standard Node ID",
        pattern=r"^Node ID: (\S+)$",
        text=await _plain_text(client=client, name="get_standard", request=route),
    )
    component_id = _text_match(
        label="a learning-component ID",
        pattern=r"Learning component: (\S+)",
        text=await _plain_text(
            client=client, name="get_learning_components_for_standard", request=route
        ),
    )
    return {
        "interpretationProfile": links["Interpretation profile"],
        "learningComponentProvenance": links["Learning component provenance"].replace(
            "{nodeId}", component_id
        ),
        "standardProvenance": links["Standard provenance"].replace("{nodeId}", node_id),
        "unresolved": links["Unresolved items"],
        "validation": links["Validation report"],
    }


async def verify_client_access(client: Client) -> dict[str, object]:
    """Verify text-only LP, evidence and workflow access on one connected server.

    Every evidence URI is taken from ordinary tool text or rendered instructions,
    never from server-side constructors, so the check follows a tool-only client.

    Parameters
    ----------
    client
        Connected MCP client that has completed the protocol handshake.

    Returns
    -------
    dict[str, object]
        Deterministic summaries of every access check.

    Raises
    ------
    RuntimeError
        If any text-only, continuation, evidence, parity or typed-failure check fails.
    """

    exact, _size = await _call_text(
        client=client,
        name="get_learning_progression",
        request={
            "frameworkId": _DIAGNOSTIC_FRAMEWORK_ID,
            "relationshipId": _DIAGNOSTIC_EDGE_ID,
            "snapshotId": _DIAGNOSTIC_SNAPSHOT_ID,
        },
    )
    text_links = await _text_evidence_links(client)
    uris = [str(exact["relationships"][0]["provenanceUri"]), *text_links.values()]
    reports: dict[str, object] = {}

    for framework_id, snapshot_id, field, expected in _REPORT_EXPECTATIONS:
        page, _size = await _call_text(
            client=client,
            name="search_learning_progressions",
            request={
                "frameworkId": framework_id,
                "limit": 1,
                "snapshotId": snapshot_id,
            },
        )
        metadata = page["metadata"]
        uris.extend(
            (
                metadata["summaryUri"],
                metadata["validationUri"],
                metadata["unresolvedUri"],
            )
        )
        summary, _size = await _call_text(
            client=client, name="read_evidence", request={"uri": metadata["summaryUri"]}
        )

        if json.loads(summary["content"])[field] != expected:
            raise RuntimeError(f"LP report lost stored {field}: {framework_id}.")

        reports[framework_id] = {field: expected}

    evidence = [await _read_evidence(client=client, uri=uri) for uri in uris]
    await _expect_error(
        client=client,
        code="invalid_evidence_uri",
        name="read_evidence",
        request={"uri": "kgfegmcp://framework/x?y"},
    )
    # The bulk "nodes" artifact link comes from LP metadata text and is policy-denied.
    nodes_uri = next(
        item["uri"]
        for item in exact["metadata"]["artifacts"]
        if item["logicalName"] == "nodes"
    )
    await _expect_error(
        client=client,
        code="resource_access_denied",
        name="read_evidence",
        request={"uri": nodes_uri},
    )
    await _expect_error(
        client=client,
        code="Input validation error",
        name="get_workflow_instructions",
        request={"workflowName": "inferred_progression_hypothesis"},
    )
    return {
        "diagnosticEdge": _DIAGNOSTIC_EDGE_ID,
        "evidence": evidence,
        "reports": reports,
        "search": await _replay_search(client),
        "textEvidenceLinks": sorted(text_links),
        "typedFailures": 3,
        "workflowMessageBytes": await _workflow_parity(client),
    }
