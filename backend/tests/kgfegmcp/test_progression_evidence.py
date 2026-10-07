"""DEV-024 read_evidence windows over native resource content, in process and MCP."""

# Standard Library
import base64
import hashlib
import json

from typing import Any

# Third Party Library
import pytest

from fastmcp import Client
from mcp.types import TextContent, TextResourceContents

# Package Library
from kgfegmcp.app import create_mcp
from kgfegmcp.bootstrap import AppState
from kgfegmcp.catalog.models import CatalogPackageRuntime
from kgfegmcp.errors import (
    EvidenceResultTooLargeError,
    InvalidCursorError,
    InvalidEvidenceUriError,
    ResourceAccessDeniedError,
)
from kgfegmcp.resources.evidence import read_evidence_window
from kgfegmcp.resources.evidence_models import ReadEvidenceRequest
from kgfegmcp.resources.models import ResourceDocument
from kgfegmcp.resources.service import ResourceService
from kgfegmcp.resources.uri import (
    artifact_uri,
    relationship_provenance_uri,
    relationship_uri,
)
from kgfegmcp.services.lp_models import GetLearningProgressionRequest
from tests.fixtures.progression_fixtures import (
    artifact_name,
    package_route,
    relationship_id,
)

# Architecture diagnostic contract identities (Nigeria package, exact snapshot).
NIGERIA = "nigeria-nerdc-mathematics-primary-1-3"
EDGE = relationship_id("0129f5d5-42fd-52cb-bcf2-ec07c47103e7")
TARGET = "e399b510-48bb-58ee-abda-61460a5a853b"


def text_block(result: Any) -> TextContent:
    """Return the ordinary text block a tool-only client receives."""
    block = result.content[0]
    assert isinstance(block, TextContent)
    return block


def nigeria(state: AppState) -> CatalogPackageRuntime:
    """Select the accepted diagnostic package by its exact framework."""
    return next(
        runtime
        for runtime in state.catalog_load_result.package_runtimes
        if runtime.catalog_package.package_identity.framework_id == NIGERIA
    )


def provenance(state: AppState) -> tuple[str, ResourceDocument]:
    """Return the constructor URI and native document of the diagnostic edge."""
    route = package_route(nigeria(state))
    return (
        relationship_provenance_uri(**route, relationship_id=EDGE),
        state.resource_service.relationship_provenance(**route, relationship_id=EDGE),
    )


def raw(document: ResourceDocument) -> bytes:
    """Return a native document's exact bytes."""
    content = document.content
    return content if isinstance(content, bytes) else content.encode("utf-8")


def digest(data: bytes) -> str:
    """Hash bytes in the resource metadata convention."""
    return "sha256:" + hashlib.sha256(data).hexdigest()


def test_windows_reassemble_exact_native_bytes(accepted_state: AppState) -> None:
    """Ordered windows reproduce native bytes, hash and metadata without overlap."""
    uri, native = provenance(accepted_state)
    original = raw(native)
    request = ReadEvidenceRequest(uri=uri, max_content_bytes=1000)
    joined = b""
    windows = 0
    # The independent native byte length bounds continuation.
    for _ in range(len(original) // 1000 + 2):
        result = read_evidence_window(
            request=request, resource_service=accepted_state.resource_service
        )
        page = result.page
        chunk = result.content.encode("utf-8")
        assert result.metadata == native.metadata
        assert (page.start_byte, page.end_byte_exclusive) == (
            len(joined),
            len(joined) + len(chunk),
        )
        assert 0 < page.returned_bytes == len(chunk) <= 1000
        assert page.total_bytes == len(original) and page.chunk_sha256 == digest(chunk)
        assert result.content_status == "partial"
        joined += chunk
        windows += 1
        if page.next_cursor is None:
            assert page.is_complete and page.next_request is None
            break
        assert not page.is_complete
        assert page.next_request == request.model_copy(
            update={"cursor": page.next_cursor}
        )
        request = page.next_request
    else:
        pytest.fail("Evidence continuation exceeded its native byte bound.")
    assert windows > 1 and joined == original
    assert digest(joined) == native.metadata.content_sha256
    whole = read_evidence_window(
        request=ReadEvidenceRequest(uri=uri),
        resource_service=accepted_state.resource_service,
    )
    assert whole.content_status == "full" and whole.page.is_complete
    assert whole.content.encode("utf-8") == original


def test_native_denial_is_not_bypassed(accepted_state: AppState) -> None:
    """A natively denied artifact is denied identically through read_evidence."""
    route = package_route(accepted_state.catalog_load_result.package_runtimes[0])
    nodes = artifact_name("nodes")
    with pytest.raises(ResourceAccessDeniedError) as native:
        accepted_state.resource_service.artifact(**route, artifact_name=nodes)
    with pytest.raises(ResourceAccessDeniedError) as paged:
        read_evidence_window(
            request=ReadEvidenceRequest(
                uri=artifact_uri(**route, artifact_name=nodes), max_content_bytes=1
            ),
            resource_service=accepted_state.resource_service,
        )
    assert paged.value.message == native.value.message


def test_continuation_reapplies_native_policy(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A valid cursor cannot outlive a later native denial of the same record."""
    uri, _ = provenance(accepted_state)
    first = read_evidence_window(
        request=ReadEvidenceRequest(uri=uri, max_content_bytes=1000),
        resource_service=accepted_state.resource_service,
    )
    assert first.page.next_request is not None

    def deny(*_args: object, **_kwargs: object) -> None:
        """Model a native rights or size refusal at the service boundary."""
        raise ResourceAccessDeniedError(message="Denied by native policy")

    monkeypatch.setattr(ResourceService, "relationship_provenance", deny)
    with pytest.raises(ResourceAccessDeniedError):
        read_evidence_window(
            request=first.page.next_request,
            resource_service=accepted_state.resource_service,
        )


def test_cursor_is_bound_to_its_record(accepted_state: AppState) -> None:
    """A continuation cursor from one record cannot be replayed on another."""
    uri, _ = provenance(accepted_state)
    first = read_evidence_window(
        request=ReadEvidenceRequest(uri=uri, max_content_bytes=1000),
        resource_service=accepted_state.resource_service,
    )
    identity = nigeria(accepted_state).catalog_package.package_identity
    other = relationship_uri(
        framework_id=identity.framework_id,
        relationship_id=EDGE,
        snapshot_id=identity.snapshot_id,
    )
    with pytest.raises(InvalidCursorError):
        read_evidence_window(
            request=ReadEvidenceRequest(
                cursor=first.page.next_cursor, max_content_bytes=1000, uri=other
            ),
            resource_service=accepted_state.resource_service,
        )


def test_encoded_separator_uri_is_rejected(accepted_state: AppState) -> None:
    """An encoded path separator never reaches a different native route."""
    uri, _ = provenance(accepted_state)
    smuggled = uri.replace(f"relationship/{EDGE}", f"relationship/{EDGE}%2F..")
    with pytest.raises(InvalidEvidenceUriError):
        read_evidence_window(
            request=ReadEvidenceRequest(uri=smuggled),
            resource_service=accepted_state.resource_service,
        )


def test_windows_end_on_unicode_boundaries(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Windows never split a scalar; an indivisible next scalar fails explicitly."""
    catalog = accepted_state.resource_service.catalog()
    text = "a€😀"
    data = text.encode("utf-8")
    document = ResourceDocument(
        content=text,
        metadata=catalog.metadata.model_copy(
            update={"byte_length": len(data), "content_sha256": digest(data)}
        ),
    )
    monkeypatch.setattr(ResourceService, "catalog", lambda _self: document)
    request = ReadEvidenceRequest(uri="kgfegmcp://catalog", max_content_bytes=3)
    seen = []
    for _ in range(2):
        result = read_evidence_window(
            request=request, resource_service=accepted_state.resource_service
        )
        seen.append(result.content)
        assert result.page.next_request is not None
        request = result.page.next_request
    assert seen == ["a", "€"]
    # The 4-byte emoji cannot fit in 3 bytes; no zero-progress cursor is offered.
    with pytest.raises(EvidenceResultTooLargeError):
        read_evidence_window(
            request=request, resource_service=accepted_state.resource_service
        )


def find_provenance_uri(value: Any) -> str:
    """Find the per-edge provenance URI in parsed ordinary LP text."""
    if isinstance(value, str):
        return value if value.endswith(f"/relationship/{EDGE}/provenance") else ""
    items = list(value.values()) if isinstance(value, dict) else value
    for item in items if isinstance(items, list) else []:
        if found := find_provenance_uri(item):
            return found
    return ""


async def test_text_only_replay_matches_native_read(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ordinary text alone yields the URI and windows that equal the native read."""
    monkeypatch.setattr("kgfegmcp.app.bootstrap_application", lambda: accepted_state)
    identity = nigeria(accepted_state).catalog_package.package_identity
    lookup = GetLearningProgressionRequest(
        framework_id=identity.framework_id,
        relationship_id=EDGE,
        snapshot_id=identity.snapshot_id,
    ).model_dump(by_alias=True, mode="json")
    async with Client(create_mcp()) as client:
        exact = await client.call_tool("get_learning_progression", {"request": lookup})
        uri = find_provenance_uri(json.loads(exact.content[0].text))
        assert uri
        native = (await client.read_resource(uri))[0].text
        request: dict[str, Any] = {"maxContentBytes": 4000, "uri": uri}
        parts: list[str] = []
        payload: dict[str, Any] = {}
        for _ in range(len(native.encode("utf-8")) // 4000 + 2):
            result = await client.call_tool("read_evidence", {"request": request})
            payload = json.loads(result.content[0].text)
            assert payload == result.structured_content
            parts.append(payload["content"])
            if payload["page"]["nextCursor"] is None:
                break
            request = payload["page"]["nextRequest"]
        else:
            pytest.fail("Text-only evidence replay did not finish.")
    assert len(parts) > 1 and "".join(parts) == native
    assert digest(native.encode("utf-8")) == payload["metadata"]["contentSha256"]


async def test_mcp_invalid_uri_is_explicit(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unsupported URI returns the stable code in ordinary error text."""
    monkeypatch.setattr("kgfegmcp.app.bootstrap_application", lambda: accepted_state)
    async with Client(create_mcp()) as client:
        with pytest.raises(Exception) as failure:
            await client.call_tool(
                "read_evidence", {"request": {"uri": "kgfegmcp://catalog?all=1"}}
            )
    assert "invalid_evidence_uri" in str(failure.value)


async def test_mcp_rejects_extra_request_fields(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The strict nested request refuses fields outside the evidence contract."""
    monkeypatch.setattr("kgfegmcp.app.bootstrap_application", lambda: accepted_state)
    async with Client(create_mcp()) as client:
        with pytest.raises(Exception) as failure:
            await client.call_tool(
                "read_evidence",
                {"request": {"offset": 0, "uri": "kgfegmcp://catalog"}},
            )
    assert "offset" in str(failure.value)


def evidence_links(message: str) -> dict[str, str]:
    """Parse the rendered EVIDENCE LINKS block into label -> URI or template."""
    block = message[message.index("EVIDENCE LINKS") :]
    return {
        label: uri
        for label, _, uri in (
            line[2:].partition(": ")
            for line in block.splitlines()
            if line.startswith("- ") and ": kgfegmcp://" in line
        )
    }


def text_value(text: str, prefix: str) -> str:
    """Read one labelled value from ordinary AS/LC tool text."""
    return next(
        line.split(":", 1)[1].strip()
        for line in text.splitlines()
        if line.strip().startswith(prefix)
    )


async def test_text_only_client_reads_asl_c_evidence_from_links(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Review F-002: AS/LC evidence is reachable from client-visible text alone."""
    monkeypatch.setattr("kgfegmcp.app.bootstrap_application", lambda: accepted_state)
    identity = nigeria(accepted_state).catalog_package.package_identity
    route = {
        "frameworkId": str(identity.framework_id),
        "snapshotId": str(identity.snapshot_id),
    }
    target = {"identifierType": "node_id", "nodeId": TARGET}
    # Both workflows named by the review's failure case.
    workflows: list[tuple[str, dict[str, Any]]] = [
        ("learning_progression_support_plan", {"identifier": target}),
        (
            "teacher_guide_draft",
            {"gradeOrStage": "PRIMARY ONE", "topicOrStandard": "numbers"},
        ),
    ]
    async with Client(create_mcp()) as client:
        messages = []
        for name, extra in workflows:
            rendered = await client.call_tool(
                "get_workflow_instructions",
                {"request": {**route, **extra, "workflowName": name}},
            )
            messages.append(
                json.loads(text_block(rendered).text)["rendered"]["message"]
            )
        links = evidence_links(messages[0])
        assert links == evidence_links(messages[1])
        standard = text_block(
            await client.call_tool(
                "get_standard", {"request": {**route, "identifier": target}}
            )
        ).text
        components = text_block(
            await client.call_tool(
                "get_learning_components_for_standard",
                {"request": {**route, "identifier": target}},
            )
        ).text
        node_id = text_value(standard, "Node ID:")
        component_id = text_value(components, "1. Learning component:")
        uris = [
            links["Standard provenance"].replace("{nodeId}", node_id),
            links["Learning component"].replace("{nodeId}", component_id),
            links["Learning component provenance"].replace("{nodeId}", component_id),
            links["Interpretation profile"],
            links["Validation report"],
            links["Unresolved items"],
        ]
        for uri in uris:
            native = (await client.read_resource(uri))[0]
            # Native reads return text or base64 blobs; compare original bytes.
            original = (
                native.text.encode("utf-8")
                if isinstance(native, TextResourceContents)
                else base64.b64decode(native.blob)
            )
            request: dict[str, Any] = {"maxContentBytes": 4096, "uri": uri}
            parts: list[str] = []
            payload: dict[str, Any] = {}
            for _ in range(len(original) // 4096 + 2):
                payload = json.loads(
                    text_block(
                        await client.call_tool("read_evidence", {"request": request})
                    ).text
                )
                parts.append(payload["content"])
                if payload["page"]["nextCursor"] is None:
                    break
                request = payload["page"]["nextRequest"]
            else:
                pytest.fail(f"Evidence replay did not finish for {uri}")
            assert "".join(parts).encode("utf-8") == original, uri
            assert digest(original) == payload["metadata"]["contentSha256"]
