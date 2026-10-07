"""Frame 1 citation handles in components-for-standard text (AC-016, AC-029)."""

# Standard Library
import base64
import hashlib
import json

from collections import Counter
from typing import Any

# Third Party Library
import pytest

from fastmcp import Client
from mcp.types import ResourceLink, TextContent, TextResourceContents

# Package Library
from kgfegmcp.app import create_mcp
from kgfegmcp.bootstrap import AppState
from kgfegmcp.catalog.models import CatalogGraphPackage, CatalogPackageRuntime
from kgfegmcp.mcp.tools import learning_components

NOT_READABLE = "not readable under package rights"


def text(result: Any) -> str:
    """Return the ordinary text block a tool-only client reads."""
    block = result.content[0]
    assert isinstance(block, TextContent)
    return block.text


def links(result: Any) -> list[str]:
    """Return the resource-link URIs attached to a tool result."""
    return [
        str(block.uri) for block in result.content if isinstance(block, ResourceLink)
    ]


def labelled(lines: list[str], label: str) -> str:
    """Read the value of one labelled text line."""
    return next(
        line.split(": ", 1)[1] for line in lines if line.strip().startswith(label + ":")
    )


def component_blocks(body: str) -> list[list[str]]:
    """Split the text into one line list per numbered component."""
    blocks: list[list[str]] = []
    for line in body.splitlines():
        if line[:1].isdigit() and ". Learning component:" in line:
            blocks.append([line])
        elif blocks and line.startswith("   "):
            blocks[-1].append(line)
    return blocks


def best_supported(runtime: CatalogPackageRuntime) -> dict[str, Any]:
    """Select the standard with the most stored supports edges (stable tie-break)."""
    counts = Counter(
        edge.target_node_id
        for edge in runtime.loaded_package.relationships
        if edge.label == "supports"
    )
    node_id = min(counts, key=lambda key: (-counts[key], key))
    identity = runtime.catalog_package.package_identity
    return {
        "frameworkId": str(identity.framework_id),
        "identifier": {"identifierType": "node_id", "nodeId": node_id},
        "snapshotId": str(identity.snapshot_id),
    }


async def read_all(client: Client, uri: str) -> tuple[bytes, bytes]:
    """Return native bytes and bytes reassembled from text-only read_evidence."""
    native = (await client.read_resource(uri))[0]
    original = (
        native.text.encode("utf-8")
        if isinstance(native, TextResourceContents)
        else base64.b64decode(native.blob)
    )
    request: dict[str, Any] = {"maxContentBytes": 4096, "uri": uri}
    parts: list[str] = []
    for _ in range(len(original) // 4096 + 2):
        payload = json.loads(
            text(await client.call_tool("read_evidence", {"request": request}))
        )
        parts.append(payload["content"])
        if payload["page"]["nextCursor"] is None:
            assert payload["metadata"]["contentSha256"] == (
                "sha256:" + hashlib.sha256(original).hexdigest()
            )
            return original, "".join(parts).encode("utf-8")
        request = payload["page"]["nextRequest"]
    pytest.fail(f"Evidence replay did not finish for {uri}")


async def test_text_prints_readable_component_citation_handles(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every listed component's IDs/URIs in text match structured data and read."""
    monkeypatch.setattr("kgfegmcp.app.bootstrap_application", lambda: accepted_state)
    async with Client(create_mcp()) as client:
        for runtime in accepted_state.catalog_load_result.package_runtimes:
            request = best_supported(runtime)
            result = await client.call_tool(
                "get_learning_components_for_standard", {"request": request}
            )
            body, structured = text(result), result.structured_content
            header = body.splitlines()
            # Both header URIs are the readable links the tool already attaches.
            assert labelled(header, "Standard URI") in links(result)
            assert labelled(header, "Standard learning components URI") in links(result)
            blocks = component_blocks(body)
            assert len(blocks) == len(structured["components"]) > 1
            for block, component in zip(blocks, structured["components"]):
                relationship = component["relationship"]
                node_id = component["node"]["nodeId"]
                assert block[0].endswith(f"Learning component: {node_id}")
                assert (
                    labelled(block, "Support relationship ID")
                    == relationship["relationshipId"]
                )
                assert (relationship["sourceNodeId"], relationship["targetNodeId"]) == (
                    node_id,
                    request["identifier"]["nodeId"],
                )
                assert labelled(block, "Direction") == "component -> standard"
                component_links = links(
                    await client.call_tool(
                        "get_learning_component",
                        {
                            "request": {
                                **{
                                    k: request[k] for k in ("frameworkId", "snapshotId")
                                },
                                "nodeId": node_id,
                            }
                        },
                    )
                )
                assert labelled(block, "Component URI") in component_links
                declared = runtime.catalog_package.capabilities.has_detailed_provenance
                provenance = [
                    line for line in block if "Component provenance URI" in line
                ]
                assert len(provenance) == int(declared)
                if declared:
                    assert (
                        labelled(block, "Component provenance URI") in component_links
                    )
                uri = labelled(block, "Support relationship URI")
                assert uri.endswith("/relationship/" + relationship["relationshipId"])
                native, replayed = await read_all(client, uri)
                assert replayed == native
                stored = json.loads(native)
                assert relationship["relationshipId"] in json.dumps(stored)


async def test_rights_denied_handles_are_marked_not_dropped(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Denied URI families print a marker while relationship IDs remain citable."""
    monkeypatch.setattr("kgfegmcp.app.bootstrap_application", lambda: accepted_state)
    original = learning_components.catalog_package

    def denied(*args: Any, **kwargs: Any) -> CatalogGraphPackage:
        """Return the exact accepted package with standard resources denied."""
        package = original(*args, **kwargs)
        return package.model_copy(
            update={
                "rights": package.rights.model_copy(
                    update={"allow_standard_resources": False}
                )
            }
        )

    runtime = accepted_state.catalog_load_result.package_runtimes[0]
    request = best_supported(runtime)
    async with Client(create_mcp()) as client:
        permitted = await client.call_tool(
            "get_learning_components_for_standard", {"request": request}
        )
        monkeypatch.setattr(learning_components, "catalog_package", denied)
        refused = await client.call_tool(
            "get_learning_components_for_standard", {"request": request}
        )
    body = text(refused)
    uri_lines = [line for line in body.splitlines() if " URI: " in line]
    assert uri_lines and all(line.endswith(NOT_READABLE) for line in uri_lines)
    assert "kgfegmcp://" not in body
    assert refused.structured_content == permitted.structured_content
    for component in refused.structured_content["components"]:
        assert (
            "Support relationship ID: " + component["relationship"]["relationshipId"]
            in body
        )
    # Only the URI lines differ from the permitted rendering.
    assert [line for line in body.splitlines() if " URI: " not in line] == [
        line for line in text(permitted).splitlines() if " URI: " not in line
    ]
