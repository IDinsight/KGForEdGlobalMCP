"""AC-033 ordinary-text consumption of the five LP tools through real MCP calls."""

# Standard Library
import json

from typing import Any

# Third Party Library
import pytest

from fastmcp import Client
from mcp.types import TextContent

# Package Library
from kgfegmcp.app import create_mcp
from kgfegmcp.bootstrap import AppState

# Architecture diagnostic identities plus a real multi-path Tamil Nadu pair.
NIGERIA = "nigeria-nerdc-mathematics-primary-1-3"
TAMIL_NADU = "india-tamil-nadu-tnscert-mathematics-classes-1-5"
EDGE = "0129f5d5-42fd-52cb-bcf2-ec07c47103e7"
TARGET = "e399b510-48bb-58ee-abda-61460a5a853b"
PATH_SOURCE = "b536c540-4b5d-5255-81e9-b061abfd42c6"
PATH_TARGET = "4061ea8e-a99e-5043-a2d4-b6a0e537dd6f"


def route(state: AppState, framework: str) -> dict[str, str]:
    """Return the exact framework/snapshot route of one accepted package."""
    identity = next(
        runtime.catalog_package.package_identity
        for runtime in state.catalog_load_result.package_runtimes
        if runtime.catalog_package.package_identity.framework_id == framework
    )
    return {
        "frameworkId": str(identity.framework_id),
        "snapshotId": str(identity.snapshot_id),
    }


def node(node_id: str) -> dict[str, str]:
    """Select one exact standard by node ID."""
    return {"identifierType": "node_id", "nodeId": node_id}


async def call(client: Client, name: str, request: dict[str, Any]) -> dict[str, Any]:
    """Parse only the ordinary text block; assess structuredContent separately."""
    result = await client.call_tool(name, {"request": request})
    block = result.content[0]
    assert isinstance(block, TextContent)
    payload: dict[str, Any] = json.loads(block.text)
    assert payload == result.structured_content
    return payload


def assert_evidence(payload: dict[str, Any]) -> None:
    """Every returned edge carries identity, judgment, notices and evidence links."""
    assert payload["relationships"]
    nodes = {item["nodeId"]: item for item in payload["nodes"]}
    for item in payload["relationships"]:
        edge = item["relationship"]
        assert edge["label"] in {"buildsTowards", "relatesTo"}
        assert {edge["sourceNodeId"], edge["targetNodeId"]} <= set(nodes)
        assert item["epistemicStatus"] == "llm_inferred"
        assert item["provenanceUri"].endswith(
            f"/relationship/{edge['relationshipId']}/provenance"
        )
        assert "calibrated probability" in item["judgment"]["confidenceNotice"]
        judgment = item["judgment"]
        # Bounded excerpts are labeled; the provenance URI links the full record.
        assert 0 <= judgment["confidence"] <= 1 and judgment["rationaleExcerpt"]
        assert judgment["warningCount"] >= len(judgment["warningExcerpts"])
        assert isinstance(judgment["rationaleExcerpted"], bool)
        assert isinstance(judgment["warningsExcerpted"], bool)
    assert all(entry["statementExcerpt"] for entry in nodes.values())
    metadata = payload["metadata"]
    assert metadata["package"]["packageIdentity"]["snapshotId"]
    assert metadata["manifestSha256"].startswith("sha256:")
    assert "mandatory prerequisite" in metadata["semanticNotice"]
    assert metadata["generatedOriginNotice"]


@pytest.mark.lp_dataset
@pytest.mark.parametrize(
    "operation",
    ["exact", "direct", "search", "traverse", "paths"],
)
async def test_ordinary_text_carries_the_complete_result(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    """A text-only client can inspect each operation's evidence and completeness."""
    monkeypatch.setattr("kgfegmcp.app.bootstrap_application", lambda: accepted_state)
    nigeria = route(accepted_state, NIGERIA)
    async with Client(create_mcp()) as client:
        if operation == "exact":
            payload = await call(
                client, "get_learning_progression", {**nigeria, "relationshipId": EDGE}
            )
            assert_evidence(payload)
            assert [
                e["relationship"]["relationshipId"] for e in payload["relationships"]
            ] == [EDGE]
        elif operation == "direct":
            payload = await call(
                client,
                "get_standard_progressions",
                {**nigeria, "identifier": node(TARGET)},
            )
            assert_evidence(payload)
            assert EDGE in {
                e["relationship"]["relationshipId"] for e in payload["relationships"]
            }
            assert payload["page"]["isComplete"] == (
                payload["page"]["nextCursor"] is None
            )
        elif operation == "search":
            first = await call(
                client, "search_learning_progressions", {**nigeria, "limit": 2}
            )
            assert_evidence(first)
            page = first["page"]
            # Replay the actual cursor copied from text; no entry repeats.
            assert (
                page["hasMore"] and page["nextRequest"]["cursor"] == page["nextCursor"]
            )
            second = await call(
                client, "search_learning_progressions", page["nextRequest"]
            )
            assert_evidence(second)
            ids = [
                e["relationship"]["relationshipId"]
                for payload in (first, second)
                for e in payload["relationships"]
            ]
            assert len(ids) == len(set(ids)) == 4
            assert "nextRequest" in first["continuationNotice"]
        elif operation == "traverse":
            payload = await call(
                client,
                "traverse_learning_progressions",
                {**nigeria, "direction": "upstream", "identifier": node(TARGET)},
            )
            assert_evidence(payload)
            assert payload["originNodeId"] == TARGET
            assert {d["nodeId"] for d in payload["distances"]} >= {TARGET}
            assert isinstance(payload["scopeComplete"], bool)
            assert (
                "No continuation"
                in payload["continuationNotice"] + payload["traversalNotice"]
            )
        else:
            payload = await call(
                client,
                "get_learning_progression_paths",
                {
                    **route(accepted_state, TAMIL_NADU),
                    "sourceIdentifier": node(PATH_SOURCE),
                    "targetIdentifier": node(PATH_TARGET),
                },
            )
            assert_evidence(payload)
            hops = [len(path["relationshipIds"]) for path in payload["paths"]]
            assert hops == sorted(hops) and hops[0] == 2
            table = {
                e["relationship"]["relationshipId"] for e in payload["relationships"]
            }
            assert all(
                set(path["relationshipIds"]) <= table for path in payload["paths"]
            )
            assert payload["truncationReasons"] == ["path_limit"]
            assert (
                not payload["scopeComplete"] and payload["nextUnreturnedPath"] is None
            )
            assert "No continuation" in payload["pathNotice"]
