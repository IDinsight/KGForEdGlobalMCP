"""Frame 1 discovery: included graph types and per-package LP availability (AC-019)."""

# Standard Library
from typing import Any

# Third Party Library
import pytest

from fastmcp import Client
from mcp.types import TextContent

# Package Library
from kgfegmcp.app import create_mcp
from kgfegmcp.bootstrap import AppState
from kgfegmcp.mcp.tools.frameworks import _format_package_summary
from kgfegmcp.services.models import ListFrameworksResult

INCLUDED = "academic_standards, learning_components, learning_progressions"


def text(result: Any) -> str:
    """Return the ordinary text block a tool-only client reads."""
    block = result.content[0]
    assert isinstance(block, TextContent)
    return block.text


def snapshot_ids(state: AppState) -> list[str]:
    """List every accepted snapshot independently of discovery output order."""
    return sorted(
        str(runtime.catalog_package.package_identity.snapshot_id)
        for runtime in state.catalog_load_result.package_runtimes
    )


async def stored_lp_counts(client: Client, framework_id: str) -> tuple[int, int]:
    """Read buildsTowards/relatesTo totals from the statistics tool (count source)."""
    result = await client.call_tool(
        "get_framework_statistics", {"request": {"frameworkId": framework_id}}
    )
    assert result.structured_content is not None
    lp = result.structured_content["statistics"]["learningProgressions"]
    assert lp["hasLearningProgressions"] and lp["hasLearningProgressionProvenance"]
    return lp["buildsTowardsRelationships"], lp["relatesToRelationships"]


@pytest.mark.parametrize(
    "graph_types",
    [
        pytest.param(["learning_progressions"], marks=pytest.mark.lp_dataset),
        ["academic_standards"],
        [],
    ],
    ids=["included-lp", "routing-type", "no-filter"],
)
async def test_graph_type_filter_matches_included_types(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch, graph_types: list[str]
) -> None:
    """LP finds all six snapshots; routing and empty filters keep their six results."""
    monkeypatch.setattr("kgfegmcp.app.bootstrap_application", lambda: accepted_state)
    request: dict[str, Any] = {"limit": 2}
    if graph_types:
        request["graphTypes"] = graph_types
    found: list[str] = []
    async with Client(create_mcp()) as client:
        # Replay real cursors so the result is the whole filtered set, not page one.
        for _ in range(5):
            result = await client.call_tool("list_frameworks", {"request": request})
            page = ListFrameworksResult.model_validate(result.structured_content)
            ids = [str(item.snapshot_id) for item in page.items]
            listed = [
                line.split(":", 1)[1].strip()
                for line in text(result).splitlines()
                if line.startswith("Snapshot ID:")
            ]
            assert listed == ids
            found.extend(ids)
            if page.next_cursor is None:
                break
            request = {**request, "cursor": page.next_cursor}
        else:
            pytest.fail("Framework discovery did not finish.")
    assert sorted(found) == snapshot_ids(accepted_state) and len(found) == 6


@pytest.mark.lp_dataset
async def test_list_frameworks_text_shows_lp_availability(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each snapshot prints routing and included types; each package its LP counts."""
    monkeypatch.setattr("kgfegmcp.app.bootstrap_application", lambda: accepted_state)
    async with Client(create_mcp()) as client:
        result = await client.call_tool("list_frameworks", {"request": {}})
        body = text(result)
        page = ListFrameworksResult.model_validate(result.structured_content)
        assert not any(line.startswith("Graph types:") for line in body.splitlines())
        assert body.count("Routing graph types: academic_standards\n") == 6
        assert body.count(f"Included graph types: {INCLUDED}\n") == 6
        for item in page.items:
            assert [value.value for value in item.included_graph_types] == (
                INCLUDED.split(", ")
            )
            builds, relates = await stored_lp_counts(client, str(item.framework_id))
            package_id = item.graph_packages[0].package_identity.graph_package_id
            line = next(row for row in body.splitlines() if f"- {package_id} |" in row)
            assert (
                f"| learning_progressions=available | builds_towards={builds} "
                f"| relates_to={relates} |"
            ) in line


@pytest.mark.lp_dataset
async def test_get_framework_text_shows_package_lp_evidence(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Framework lookup prints included types, LP flags and stored LP counts."""
    monkeypatch.setattr("kgfegmcp.app.bootstrap_application", lambda: accepted_state)
    async with Client(create_mcp()) as client:
        for runtime in accepted_state.catalog_load_result.package_runtimes:
            framework_id = str(runtime.catalog_package.package_identity.framework_id)
            body = text(
                await client.call_tool(
                    "get_framework", {"request": {"frameworkId": framework_id}}
                )
            )
            builds, relates = await stored_lp_counts(client, framework_id)
            assert f"  Included graph types: {INCLUDED}\n" in body
            assert "  Learning progressions: true\n" in body
            assert "  LP provenance: true\n" in body
            assert (
                f"learning_progressions[builds_towards={builds}, relates_to={relates}]"
                in body
            )


@pytest.mark.lp_dataset
async def test_capabilities_text_shows_included_types_and_lp_blocks(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Server and per-package capability text agree with structured LP evidence."""
    monkeypatch.setattr("kgfegmcp.app.bootstrap_application", lambda: accepted_state)
    async with Client(create_mcp()) as client:
        result = await client.call_tool("get_capabilities", {})
        body = text(result)
        structured = result.structured_content
        assert "\nRouting graph types: academic_standards\n" in body
        assert f"\nIncluded graph types: {INCLUDED}\n" in body
        assert structured["includedGraphTypes"] == INCLUDED.split(", ")
        blocks = body.split("- Graph package ID: ")[1:]
        assert len(blocks) == 6
        for block in blocks:
            framework_id = block.split("Framework ID: ", 1)[1].split("\n", 1)[0]
            builds, relates = await stored_lp_counts(client, framework_id)
            assert f"  Included graph types: {INCLUDED}\n" in block
            assert (
                "  Learning progressions:\n"
                "    hasLearningProgressions: true\n"
                "    hasLearningProgressionProvenance: true\n"
                f"    buildsTowards: {builds}\n"
                f"    relatesTo: {relates}"
            ) in block


async def test_undeclared_lp_package_summary_is_unavailable(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A package without declared LP shows unavailable and zeros, never inferred."""
    monkeypatch.setattr("kgfegmcp.app.bootstrap_application", lambda: accepted_state)
    async with Client(create_mcp()) as client:
        result = await client.call_tool("list_frameworks", {"request": {"limit": 1}})
    package = (
        ListFrameworksResult.model_validate(result.structured_content)
        .items[0]
        .graph_packages[0]
    )
    # Model a manifest that declares no LP: flags false and zero stored counts.
    undeclared = package.model_copy(
        update={
            "capabilities": package.capabilities.model_copy(
                update={
                    "has_learning_progressions": False,
                    "has_learning_progression_provenance": False,
                }
            ),
            "counts": package.counts.model_copy(
                update={
                    "builds_towards_relationships": 0,
                    "relates_to_relationships": 0,
                }
            ),
        }
    )
    summary = _format_package_summary(undeclared)
    assert (
        "| learning_progressions=unavailable | builds_towards=0 | relates_to=0 |"
        in summary
    )
    assert "learning_progressions=available" not in summary
