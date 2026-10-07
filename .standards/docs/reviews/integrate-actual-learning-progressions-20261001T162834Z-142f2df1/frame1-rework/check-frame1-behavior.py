"""Reviewer diagnostic for the Frame 1 Desktop rework: F1, F2 and F3 behavior.

Independent supporting evidence for IMPLEMENTATION review, not formal Tester
verification. Drives the real ``create_mcp`` app through an in-memory FastMCP
client with network connections blocked; no model or paid service is used. Run
with ``--part discovery`` against both the current and an archived pre-rework
source tree (PYTHONPATH) to compare discovery results; run ``--part all`` against
the current source for every check.

- discovery: list_frameworks for five graphTypes filters (full cursor replay at
  limit 2), structured items with the additive includedGraphTypes keys removed
  (for before/after equality), and on the current source the discovery,
  framework and capabilities text against get_framework_statistics.
- citations: every standard of every package through
  get_learning_components_for_standard (supported and unsupported); text blocks
  against structuredContent, URI constructors, tool/component resource links and
  native reads of every printed Support relationship URI; text-only read_evidence
  replay for the first supported standard per package.
- workflows: curriculum review for four relationship_types selections (native
  prompt versus get_workflow_instructions), executed scans as rendered (own
  cursor, at most three pages), invalid selections, per-kind direct calls in the
  teaching sequence and four legacy workflows executed for each package's
  highest-degree standard against the old single connectionKind all page, and a
  fixed-count wording scan of all rendered workflows.

Usage (repository root)::

    PATHS_PROJECT_DIR=$PWD [PYTHONPATH=<archived src>] backend/.venv/bin/python \
        .standards/docs/reviews/<cycle>/frame1-rework/check-frame1-behavior.py \
        --part all > <receipt>.json
"""

# Standard Library
import argparse
import asyncio
import base64
import hashlib
import json
import re
import socket
import sys

from collections import Counter
from typing import Any

# Third Party Library
from fastmcp import Client

# Package Library
import kgfegmcp
import kgfegmcp.app as app_module

from kgfegmcp.app import create_mcp
from kgfegmcp.bootstrap import bootstrap_application

FAILURES: list[str] = []
FIXED_COUNT = re.compile(
    r"page of 25|pages of 25|three of 25|at most 75|one page of \d+ (?:edges|relationships)"
)


def _reject(*_args: Any, **_kwargs: Any) -> None:
    raise AssertionError("network connection attempted")


def check(condition: bool, label: str) -> None:
    if not condition:
        FAILURES.append(label)


def text(result: Any) -> str:
    return str(getattr(result.content[0], "text", ""))


def links(result: Any) -> list[str]:
    return [str(b.uri) for b in result.content if getattr(b, "type", "") == "resource_link"]


def strip_included(value: Any) -> Any:
    """Remove the additive includedGraphTypes keys at every depth."""
    if isinstance(value, dict):
        return {k: strip_included(v) for k, v in value.items() if k != "includedGraphTypes"}
    if isinstance(value, list):
        return [strip_included(v) for v in value]
    return value


async def discovery(client: Client, state: Any, full: bool) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for label, types in {
        "none": [],
        "academic_standards": ["academic_standards"],
        "learning_progressions": ["learning_progressions"],
        "learning_components": ["learning_components"],
        "lc+lp": ["learning_components", "learning_progressions"],
    }.items():
        request: dict[str, Any] = {"limit": 2}
        if types:
            request["graphTypes"] = types
        ids: list[str] = []
        items: list[Any] = []
        for _ in range(10):
            raw = await client.call_tool_mcp("list_frameworks", {"request": request})
            if raw.isError:
                out[label] = {"error": text(raw)[:300]}
                break
            page = raw.structuredContent
            ids.extend(str(i["snapshotId"]) for i in page["items"])
            items.extend(page["items"])
            if page.get("nextCursor") is None:
                break
            request = {**request, "cursor": page["nextCursor"]}
        else:
            FAILURES.append(f"discovery {label}: did not finish")
        out[label] = {
            "snapshotIds": ids,
            "itemsSha256WithoutIncluded": hashlib.sha256(
                json.dumps(strip_included(items), sort_keys=True).encode()
            ).hexdigest(),
        }

    if not full:
        return out

    # Text checks on the current source only.
    stats: dict[str, tuple[int, int]] = {}
    for runtime in state.catalog_load_result.package_runtimes:
        framework = str(runtime.catalog_package.package_identity.framework_id)
        raw = await client.call_tool_mcp(
            "get_framework_statistics", {"request": {"frameworkId": framework}}
        )
        lp = raw.structuredContent["statistics"]["learningProgressions"]
        stored = Counter(
            r.label
            for r in runtime.loaded_package.relationships
            if r.label in {"buildsTowards", "relatesTo"}
        )
        stats[framework] = (lp["buildsTowardsRelationships"], lp["relatesToRelationships"])
        check(
            stats[framework] == (stored["buildsTowards"], stored["relatesTo"]),
            f"{framework}: statistics differ from stored edges",
        )
    listing = await client.call_tool_mcp("list_frameworks", {"request": {"limit": 100}})
    body = text(listing)
    check("\nGraph types:" not in body, "list_frameworks still prints Graph types:")
    included = "academic_standards, learning_components, learning_progressions"
    check(body.count("Routing graph types: academic_standards\n") == 6, "routing lines")
    check(body.count(f"Included graph types: {included}\n") == 6, "included lines")
    for framework, (builds, relates) in stats.items():
        snapshot_lines = [line for line in body.splitlines() if line.startswith("- ") and " | graph_type=" in line]
        match = [
            line
            for line in snapshot_lines
            if f"learning_progressions=available | builds_towards={builds} | relates_to={relates} |" in line
        ]
        check(bool(match), f"{framework}: list_frameworks LP line")
        fw = text(await client.call_tool_mcp("get_framework", {"request": {"frameworkId": framework}}))
        check(f"  Included graph types: {included}\n" in fw, f"{framework}: get_framework included")
        check("  Learning progressions: true\n" in fw and "  LP provenance: true\n" in fw, f"{framework}: LP flags")
        check(
            f"learning_progressions[builds_towards={builds}, relates_to={relates}]" in fw,
            f"{framework}: get_framework counts",
        )
    caps = await client.call_tool_mcp("get_capabilities", {})
    cap_text = text(caps)
    check("\nRouting graph types: academic_standards\n" in cap_text, "capabilities routing line")
    check(f"\nIncluded graph types: {included}\n" in cap_text, "capabilities included line")
    check(caps.structuredContent["includedGraphTypes"] == included.split(", "), "capabilities structured")
    for framework, (builds, relates) in stats.items():
        block = next((b for b in cap_text.split("- Graph package ID: ")[1:] if f"Framework ID: {framework}\n" in b), "")
        check(
            "  Learning progressions:\n    hasLearningProgressions: true\n"
            "    hasLearningProgressionProvenance: true\n"
            f"    buildsTowards: {builds}\n    relatesTo: {relates}" in block,
            f"{framework}: capabilities LP block",
        )
    out["textChecked"] = {k: list(v) for k, v in stats.items()}
    return out


async def read_text_only(client: Client, uri: str) -> bool:
    request: dict[str, Any] = {"maxContentBytes": 16384, "uri": uri}
    parts: list[str] = []
    for _ in range(200):
        raw = await client.call_tool_mcp("read_evidence", {"request": request})
        if raw.isError:
            return False
        payload = json.loads(text(raw))
        parts.append(payload["content"])
        if payload["page"]["nextCursor"] is None:
            native = (await client.read_resource(uri))[0]
            blob = getattr(native, "blob", None)
            data = base64.b64decode(blob) if blob is not None else native.text.encode()
            return "".join(parts).encode() == data and payload["metadata"][
                "contentSha256"
            ] == "sha256:" + hashlib.sha256(data).hexdigest()
        request = payload["page"]["nextRequest"]
    return False


async def citations(client: Client, state: Any) -> dict[str, Any]:
    from kgfegmcp.resources.uri import (  # pylint: disable=C0415
        learning_component_provenance_uri,
        learning_component_uri,
        relationship_uri,
        standard_learning_components_uri,
        standard_uri,
    )

    summary: dict[str, Any] = {}
    for runtime in state.catalog_load_result.package_runtimes:
        package = runtime.catalog_package
        identity = package.package_identity
        fw, snap = identity.framework_id, identity.snapshot_id
        route = {"frameworkId": str(fw), "snapshotId": str(snap)}
        supports: dict[str, int] = Counter(
            r.target_node_id for r in runtime.loaded_package.relationships if r.label == "supports"
        )
        standards = sorted(str(n.node_id) for n in runtime.loaded_package.item_nodes)
        standard_ids = [s for s in standards if s in {str(k) for k in supports}]
        unsupported = [s for s in standards if s not in {str(k) for k in supports}]
        components = blocks_total = reads = 0
        first_read_done = False
        for node_id in standard_ids + unsupported[:3]:
            raw = await client.call_tool_mcp(
                "get_learning_components_for_standard",
                {"request": {**route, "identifier": {"identifierType": "node_id", "nodeId": node_id}}},
            )
            if raw.isError:
                FAILURES.append(f"{fw} {node_id}: tool error {text(raw)[:120]}")
                continue
            body, structured = text(raw), raw.structuredContent
            header = body.splitlines()
            std_uri = standard_uri(framework_id=fw, node_id=node_id, snapshot_id=snap)
            slc_uri = standard_learning_components_uri(framework_id=fw, node_id=node_id, snapshot_id=snap)
            check(f"Standard URI: {std_uri}" in header, f"{fw} {node_id}: standard URI line")
            check(f"Standard learning components URI: {slc_uri}" in header, f"{fw} {node_id}: SLC URI line")
            check(std_uri in links(raw) and slc_uri in links(raw), f"{fw} {node_id}: header URIs not linked")
            blocks: list[list[str]] = []
            for line in header:
                if line[:1].isdigit() and ". Learning component:" in line:
                    blocks.append([line])
                elif blocks and line.startswith("   "):
                    blocks[-1].append(line)
            check(len(blocks) == len(structured["components"]), f"{fw} {node_id}: block count")
            check(f"Supporting learning components: {len(structured['components'])}" in header, f"{fw} {node_id}: count line")
            blocks_total += len(blocks)
            for block, component in zip(blocks, structured["components"]):
                components += 1
                rel = component["relationship"]
                cid = component["node"]["nodeId"]
                expected = [
                    f"   Support relationship ID: {rel['relationshipId']}",
                    "   Support relationship URI: "
                    + relationship_uri(framework_id=fw, relationship_id=rel["relationshipId"], snapshot_id=snap),
                    "   Direction: component -> standard",
                    "   Component URI: " + learning_component_uri(framework_id=fw, node_id=cid, snapshot_id=snap),
                ]
                if package.capabilities.has_detailed_provenance:
                    expected.append(
                        "   Component provenance URI: "
                        + learning_component_provenance_uri(framework_id=fw, node_id=cid, snapshot_id=snap)
                    )
                check(block[0].endswith(f"Learning component: {cid}"), f"{fw} {node_id}: order")
                check(block[-len(expected):] == expected, f"{fw} {node_id} {cid}: citation lines")
                check(
                    (rel["sourceNodeId"], rel["targetNodeId"], rel["label"]) == (cid, node_id, "supports"),
                    f"{fw} {node_id} {cid}: stored orientation",
                )
                native = await client.read_resource(expected[1].split(": ", 1)[1])
                reads += 1
                check(rel["relationshipId"] in native[0].text, f"{fw} {cid}: relationship read")
                if not first_read_done:
                    for line in expected[1:]:
                        if "URI: " in line:
                            uri = line.split(": ", 1)[1]
                            check(await read_text_only(client, uri), f"{fw}: text-only read {uri}")
                    first_read_done = True
        summary[str(fw)] = {
            "supportedStandards": len(standard_ids),
            "unsupportedChecked": min(3, len(unsupported)),
            "componentBlocks": blocks_total,
            "nativeRelationshipReads": reads,
        }
    return summary


def templates(message: str) -> list[dict[str, Any]]:
    return [json.loads(line)["request"] for line in message.splitlines() if line.startswith('{"request":')]


async def run_pages(client: Client, request: dict[str, Any], tool: str, pages: int) -> list[dict[str, Any]]:
    out, current = [], dict(request)
    for _ in range(pages):
        raw = await client.call_tool_mcp(tool, {"request": current})
        check(not raw.isError, f"{tool} failed: {text(raw)[:160]}")
        if raw.isError:
            break
        out.append(raw.structuredContent)
        cursor = raw.structuredContent["page"]["nextCursor"]
        if cursor is None:
            break
        current = {**request, "cursor": cursor}
    return out


async def workflows(client: Client, state: Any) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for runtime in state.catalog_load_result.package_runtimes:
        identity = runtime.catalog_package.package_identity
        fw = str(identity.framework_id)
        route = {"frameworkId": fw, "snapshotId": str(identity.snapshot_id)}
        native_route = {"framework_id": fw, "snapshot_id": str(identity.snapshot_id)}
        labels = {r.relationship_id: r.label for r in runtime.loaded_package.relationships}
        result: dict[str, Any] = {}
        for selection, expected in {
            "omitted": ["buildsTowards", "relatesTo"],
            "builds": ["buildsTowards"],
            "relates": ["relatesTo"],
            "reversed-both": ["buildsTowards", "relatesTo"],
        }.items():
            types = {"omitted": None, "builds": ["buildsTowards"], "relates": ["relatesTo"], "reversed-both": ["relatesTo", "buildsTowards"]}[selection]
            request = {**route, "workflowName": "learning_progression_curriculum_review"}
            native_args = dict(native_route)
            if types is not None:
                request["relationshipTypes"] = types
                native_args["relationship_types"] = json.dumps(types)
            tool = await client.call_tool_mcp("get_workflow_instructions", {"request": request})
            check(not tool.isError, f"{fw} review {selection}: tool error")
            payload = json.loads(text(tool))
            message = payload["rendered"]["message"]
            native = await client.get_prompt("learning_progression_curriculum_review", native_args)
            check(native.messages[0].content.text == message, f"{fw} review {selection}: native differs")
            scans = [t for t in templates(message) if "relationshipTypes" in t]
            check([s["relationshipTypes"] for s in scans] == [[t] for t in expected], f"{fw} review {selection}: scan order")
            if len(scans) == 2:
                strip = lambda s: {k: v for k, v in s.items() if k != "relationshipTypes"}
                check(strip(scans[0]) == strip(scans[1]), f"{fw} review {selection}: scans differ beyond type")
            check(not FIXED_COUNT.search(message), f"{fw} review {selection}: fixed-count wording")
            per_type: dict[str, Any] = {}
            for scan in scans:
                pages = await run_pages(client, scan, "search_learning_progressions", 3)
                got = [labels[item["relationship"]["relationshipId"]] for p in pages for item in p["relationships"]]
                check(set(got) <= set(scan["relationshipTypes"]), f"{fw} {scan['relationshipTypes']}: mixed types")
                check(bool(got), f"{fw} {scan['relationshipTypes']}: empty scan")
                per_type[scan["relationshipTypes"][0]] = {
                    "pages": len(pages),
                    "returned": len(got),
                    "remainingCursor": pages[-1]["page"]["nextCursor"] is not None if pages else None,
                }
            result[selection] = per_type
        for bad in (["relatesTo", "relatesTo"], ["hasChild"], ["buildsTowards", "relatesTo", "relatesTo"]):
            tool = await client.call_tool_mcp(
                "get_workflow_instructions",
                {"request": {**route, "relationshipTypes": bad, "workflowName": "learning_progression_curriculum_review"}},
            )
            check(tool.isError, f"{fw} review {bad}: accepted")
            try:
                await client.get_prompt(
                    "learning_progression_curriculum_review", {**native_route, "relationship_types": json.dumps(bad)}
                )
                FAILURES.append(f"{fw} native review {bad}: accepted")
            except Exception:  # pylint: disable=W0718
                pass
        blank = await client.get_prompt("learning_progression_curriculum_review", {**native_route, "relationship_types": ""})
        check(
            [s["relationshipTypes"] for s in templates(blank.messages[0].content.text) if "relationshipTypes" in s]
            == [["buildsTowards"], ["relatesTo"]],
            f"{fw}: blank relationship_types not both",
        )

        # Highest-degree standard: compare old single all-kind page with per-kind calls.
        degree = Counter()
        for r in runtime.loaded_package.relationships:
            if r.label in {"buildsTowards", "relatesTo"}:
                degree[str(r.source_node_id)] += 1
                degree[str(r.target_node_id)] += 1
        hub = min(degree, key=lambda k: (-degree[k], k))
        selector = {"identifierType": "node_id", "nodeId": hub}
        old = await client.call_tool_mcp(
            "get_standard_progressions",
            {"request": {**route, "connectionKind": "all", "identifier": selector, "limit": 25}},
        )
        old_kinds = Counter(c["connectionKind"] for c in old.structuredContent["connections"]) if not old.isError else {}
        grades = [g.local_label for g in runtime.loaded_package.profile.grade_mappings]
        direct: dict[str, Any] = {}
        for name, extra in {
            "learning_progression_teaching_sequence": {"topicOrStandard": "number"},
            "teacher_guide_draft": {"gradeOrStage": grades[0], "topicOrStandard": "number"},
            "student_study_support": {"gradeOrStage": grades[0], "topicOrStandard": "number"},
            "student_handbook_section": {"gradeOrStage": grades[0], "topicOrStandard": "number"},
            "multigrade_lesson_plan": {"gradesInRoom": grades[:2], "topicOrStandard": "number"},
            "learning_progression_support_plan": {"identifier": selector},
        }.items():
            raw = await client.call_tool_mcp("get_workflow_instructions", {"request": {**route, **extra, "workflowName": name}})
            message = json.loads(text(raw))["rendered"]["message"]
            check(not FIXED_COUNT.search(message), f"{fw} {name}: fixed-count wording")
            calls = [t for t in templates(message) if "connectionKind" in t]
            kinds = [c["connectionKind"] for c in calls]
            if name == "learning_progression_support_plan":
                check(kinds == ["incoming_builds", "related"], f"{fw} support plan kinds {kinds}")
                check(message.count("limit 25 is the maximum requested") == 2, f"{fw} support plan wording")
            else:
                check(kinds == ["outgoing_builds", "incoming_builds", "related"], f"{fw} {name}: kinds {kinds}")
                check("at most 9" in message, f"{fw} {name}: 9-call cap")
            check(all(c["limit"] == 25 and "cursor" not in c for c in calls), f"{fw} {name}: limit/cursor")
            executed: dict[str, int] = {}
            for call in calls:
                concrete = {**call, "identifier": selector}
                raw_call = await client.call_tool_mcp("get_standard_progressions", {"request": concrete})
                check(not raw_call.isError, f"{fw} {name} {call['connectionKind']}: error")
                if raw_call.isError:
                    continue
                got = {c["connectionKind"] for c in raw_call.structuredContent["connections"]}
                check(got <= {call["connectionKind"]}, f"{fw} {name} {call['connectionKind']}: mixed kinds")
                executed[call["connectionKind"]] = len(raw_call.structuredContent["relationships"])
            direct[name] = executed
        stored_kinds = Counter()
        for r in runtime.loaded_package.relationships:
            if r.label == "buildsTowards" and str(r.source_node_id) == hub:
                stored_kinds["outgoing_builds"] += 1
            elif r.label == "buildsTowards" and str(r.target_node_id) == hub:
                stored_kinds["incoming_builds"] += 1
            elif r.label == "relatesTo" and hub in {str(r.source_node_id), str(r.target_node_id)}:
                stored_kinds["related"] += 1
        summary[fw] = {
            "review": result,
            "hub": hub,
            "hubStoredKinds": dict(stored_kinds),
            "oldAllPageKinds": dict(old_kinds),
            "perKindReturned": direct,
        }
    return summary


async def main(part: str) -> dict[str, Any]:
    socket.socket.connect = _reject  # type: ignore[method-assign]
    state = bootstrap_application()
    app_module.bootstrap_application = lambda: state
    out: dict[str, Any] = {"source": kgfegmcp.__file__}
    async with Client(create_mcp()) as client:
        out["discovery"] = await discovery(client, state, full=part == "all")
        if part == "all":
            out["citations"] = await citations(client, state)
            out["workflows"] = await workflows(client, state)
    out["failures"] = FAILURES
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--part", choices=("discovery", "all"), default="all")
    arguments = parser.parse_args()
    result = asyncio.run(main(arguments.part))
    json.dump(result, sys.stdout, indent=1, sort_keys=True, default=str)
    sys.stdout.write("\n")
    sys.exit(1 if FAILURES else 0)
