"""Reviewer diagnostic: replay the documentation claims changed by the Frame 1 and style reworks.

Runs the real create_mcp app through an in-process FastMCP client with sockets blocked
and no model calls. Each documented claim is recorded as pass/fail with the observed
value, so a failed claim is reported rather than hidden. Claims are read from ordinary
tool text where the walkthrough tells a text-only client to read them. Output:
final-frame1-claims-results.json beside this file. Reviewer evidence only; not
Tester-owned acceptance coverage.

Usage (repository root, locked backend environment):
    backend/.venv/bin/python <abs-path-to-this-file>
"""

# Standard Library
import asyncio
import json
import re
import socket

from collections import Counter
from pathlib import Path
from typing import Any
from unittest.mock import patch

# Third Party Library
from fastmcp import Client

# Package Library
from kgfegmcp.app import create_mcp
from kgfegmcp.bootstrap import bootstrap_application

OUT = Path(__file__).resolve().parent / "final-frame1-claims-results.json"
FW = "nigeria-nerdc-mathematics-primary-1-3"
SNAP = "nigeria-nerdc-mathematics-primary-1-3@undated+bc5e769ed26f"
REL = "0129f5d5-42fd-52cb-bcf2-ec07c47103e7"
TGT = "e399b510-48bb-58ee-abda-61460a5a853b"
NODE = {"identifierType": "node_id", "nodeId": TGT}
CONTEXT = "Learners can count to 9 but often write 6 and 9 the wrong way round."
GH_FW = "ghana-nacca-primary-mathematics-basic-4-6"
GH_SNAP = "ghana-nacca-primary-mathematics-basic-4-6@2019+0b768f7cfaf9"
CBSE_SUMMARY = (
    "kgfegmcp://framework/india-cbse-science-learning-framework-classes-9-10/snapshot/"
    "india-cbse-science-learning-framework-classes-9-10%40undated%2B576740bed2d1/"
    "learning-progressions"
)
GH_UNRESOLVED = (
    "kgfegmcp://framework/ghana-nacca-primary-mathematics-basic-4-6/snapshot/"
    "ghana-nacca-primary-mathematics-basic-4-6%402019%2B0b768f7cfaf9/unresolved"
)
STD_PROV = (
    "kgfegmcp://framework/nigeria-nerdc-mathematics-primary-1-3/snapshot/"
    "nigeria-nerdc-mathematics-primary-1-3%40undated%2Bbc5e769ed26f/standard/"
    "e399b510-48bb-58ee-abda-61460a5a853b/provenance"
)
INCLUDED = "Included graph types: academic_standards, learning_components, learning_progressions"
RESULTS: list[dict[str, Any]] = []


def record(claim: str, ok: bool, observed: Any = None) -> None:
    """Keep every claim outcome, passing or not."""

    RESULTS.append({"claim": claim, "pass": bool(ok), "observed": observed})


def text_of(result: Any) -> str:
    """Return the first ordinary text block of a tool result."""

    return result.content[0].text


async def call(client: Client, name: str, args: dict[str, Any]) -> tuple[Any, Any]:
    """Call one tool; return parsed text (JSON when possible) and the raw result."""

    result = await client.call_tool(name, args, raise_on_error=False)
    text = text_of(result)
    if result.is_error or not text.startswith("{"):
        return text, result
    return json.loads(text), result


async def read_all(client: Client, uri: str, size: int | None = None) -> dict[str, Any]:
    """Replay read_evidence page.nextRequest from ordinary text until complete."""

    request: dict[str, Any] = {"uri": uri}
    if size is not None:
        request["maxContentBytes"] = size
    parts, windows, statuses = [], 0, []
    while True:
        data, _ = await call(client, "read_evidence", {"request": request})
        if isinstance(data, str):
            return {"error": data[:200]}
        windows += 1
        parts.append(data["content"])
        statuses.append(data["contentStatus"])
        if data["page"]["isComplete"]:
            content = "".join(parts)
            return {
                "windows": windows,
                "bytes": len(content.encode("utf-8")),
                "content": content,
                "statuses": statuses,
                "maxContentBytes": data["page"]["maxContentBytes"],
            }
        request = data["page"]["nextRequest"]


def requests_in(message: str) -> list[dict[str, Any]]:
    """Extract rendered single-line tool requests from a workflow message."""

    return [
        json.loads(line)["request"]
        for line in message.splitlines()
        if line.startswith('{"request":')
    ]


async def step1(client: Client, state: Any) -> None:
    """Discovery text, LP filter and capabilities (walkthrough step 1, discovery guide)."""

    stats: dict[str, tuple[int, int]] = {}
    for runtime in state.catalog_load_result.package_runtimes:
        identity = runtime.catalog_package.package_identity
        labels = Counter(r.label for r in runtime.loaded_package.relationships)
        stats[str(identity.snapshot_id)] = (labels["buildsTowards"], labels["relatesTo"])

    listing, _ = await call(client, "list_frameworks", {"request": {}})
    blocks = [b for b in listing.split("\n\nFramework: ")[0:]]
    snapshot_ids = re.findall(r"^Snapshot ID: (\S+)$", listing, flags=re.M)
    record("step1: six snapshots listed", len(snapshot_ids) == 6, snapshot_ids)
    record("step1: Nigeria snapshot listed", SNAP in snapshot_ids)
    record(
        "step1: every snapshot has routing academic_standards and the three included types",
        listing.count("Routing graph types: academic_standards\n") == 6
        and listing.count(INCLUDED + "\n") == 6,
        [listing.count("Routing graph types: academic_standards"), listing.count(INCLUDED)],
    )
    record(
        "before-you-start: current text has no single 'Graph types:' line",
        not re.search(r"^Graph types:", listing, flags=re.M),
    )
    package_lines = [line for line in listing.splitlines() if line.startswith("- ") and "| graph_type=" in line]
    line_ok = []
    for line in package_lines:
        snap = line[2:].split("--academic-standards")[0]
        builds, relates = stats[snap]
        line_ok.append(
            line.endswith(
                f"| learning_progressions=available | builds_towards={builds} | "
                f"relates_to={relates} | validation=passed"
            )
        )
    record("step1/framework-tools: each package line ends with LP availability, stored counts, validation",
           len(package_lines) == 6 and all(line_ok), package_lines)
    record("step1: Nigeria builds_towards=189, relates_to=297", stats[SNAP] == (189, 297), stats[SNAP])
    record("progression guide: Ghana Mathematics stores 299 buildsTowards and 300 relatesTo",
           stats[GH_SNAP] == (299, 300), stats[GH_SNAP])

    filtered, raw = await call(client, "list_frameworks", {"request": {"graphTypes": ["learning_progressions"]}})
    filtered_ids = re.findall(r"^Snapshot ID: (\S+)$", filtered, flags=re.M)
    record("step1/discovery guide: graphTypes [learning_progressions] returns the same six snapshots",
           sorted(filtered_ids) == sorted(snapshot_ids), filtered_ids)
    items = raw.structured_content["items"]
    record("framework-tools: snapshot items carry routing availableGraphTypes and includedGraphTypes",
           all(i["availableGraphTypes"] == ["academic_standards"]
               and i["includedGraphTypes"] == ["academic_standards", "learning_components", "learning_progressions"]
               for i in items),
           [(i["availableGraphTypes"], i["includedGraphTypes"]) for i in items])

    caps, _ = await call(client, "get_capabilities", {})
    tools = re.search(r"^Tools: (.+)$", caps, flags=re.M).group(1).split(", ")
    prompts = re.search(r"^Prompts: (.+)$", caps, flags=re.M).group(1).split(", ")
    record("step1: capabilities text lists 19 tools incl. read_evidence/get_workflow_instructions",
           len(tools) == 19 and "read_evidence" in tools and "get_workflow_instructions" in tools, len(tools))
    record("step1: capabilities text lists nine prompts", len(prompts) == 9, len(prompts))
    record("step1: capabilities text says Resources: 1 fixed, 14 templates", "Resources: 1 fixed, 14 templates" in caps)
    record("step1: capabilities Included graph types lists all three", f"\n{INCLUDED}\n" in caps)
    lp_blocks = re.findall(
        r"Learning progressions:\n\s+hasLearningProgressions: (\w+)\n\s+hasLearningProgressionProvenance: (\w+)\n"
        r"\s+buildsTowards: (\d+)\n\s+relatesTo: (\d+)",
        caps,
    )
    record("step1/framework-tools: six capabilities LP blocks, all true, counts equal stored edges",
           len(lp_blocks) == 6
           and all(b[0] == "true" and b[1] == "true" for b in lp_blocks)
           and sorted((int(b[2]), int(b[3])) for b in lp_blocks) == sorted(stats.values()),
           lp_blocks)

    framework, _ = await call(client, "get_framework", {"request": {"frameworkId": FW, "snapshotId": SNAP}})
    record("discovery guide: get_framework text has included types, LP and LP provenance flags and LP counts",
           INCLUDED in framework and "Learning progressions: true" in framework
           and "LP provenance: true" in framework
           and "learning_progressions[builds_towards=189, relates_to=297]" in framework)


async def step3(client: Client, state: Any) -> None:
    """Per-kind direct calls and the all-page ordering claim (step 3, progression guide)."""

    got: dict[str, Any] = {}
    for kind in ("outgoing_builds", "incoming_builds", "related"):
        data, _ = await call(client, "get_standard_progressions", {"request": {
            "frameworkId": FW, "snapshotId": SNAP, "identifier": NODE, "connectionKind": kind, "limit": 25}})
        got[kind] = {
            "ids": [c["relationshipId"] for c in data["connections"]],
            "sources": [c.get("sourceNodeId") for c in data["connections"]],
            "complete": data["page"]["isComplete"],
            "cursor": data["page"]["nextCursor"],
        }
    record("step3: no outgoing_builds", got["outgoing_builds"]["ids"] == [], got["outgoing_builds"])
    inc = got["incoming_builds"]["ids"]
    record("step3: two incoming_builds 0129f5d5… and c0155efa…",
           len(inc) == 2 and any(i.startswith("0129f5d5") for i in inc) and any(i.startswith("c0155efa") for i in inc), inc)
    record("step3: six related", len(got["related"]["ids"]) == 6, len(got["related"]["ids"]))
    record("step3: each per-kind page complete with no cursor",
           all(v["complete"] and v["cursor"] is None for v in got.values()))
    data, _ = await call(client, "get_standard_progressions", {"request": {
        "frameworkId": FW, "snapshotId": SNAP, "identifier": NODE, "connectionKind": "all", "limit": 25}})
    record("step3: connectionKind all returns the same eight in one page",
           sorted(c["relationshipId"] for c in data["connections"]) == sorted(sum((v["ids"] for v in got.values()), []))
           and data["page"]["isComplete"] and data["page"]["nextCursor"] is None,
           data["page"]["returnedCount"])
    kinds = [c["connectionKind"] for c in data["connections"]]
    first_related = kinds.index("related") if "related" in kinds else len(kinds)
    record("step3/progression guide: an all page lists builds before related links",
           all(k != "related" for k in kinds[:first_related]) and all(k == "related" for k in kinds[first_related:]),
           kinds)

    # Data scan for the "can stop before any related link appears" statement: the
    # largest direct-builds degree of any standard that also has related links.
    worst: tuple[int, int, str, str] = (0, 0, "", "")
    for runtime in state.catalog_load_result.package_runtimes:
        builds, relates = Counter(), Counter()
        for r in runtime.loaded_package.relationships:
            for node in (str(r.source_node_id), str(r.target_node_id)):
                if r.label == "buildsTowards":
                    builds[node] += 1
                elif r.label == "relatesTo":
                    relates[node] += 1
        for node, count in builds.items():
            if relates[node] and count > worst[0]:
                worst = (count, relates[node], node, str(runtime.catalog_package.package_identity.snapshot_id))
    if worst[0]:
        count, related_count, node, snap = worst
        fw = snap.split("@")[0]
        page, _ = await call(client, "get_standard_progressions", {"request": {
            "frameworkId": fw, "snapshotId": snap,
            "identifier": {"identifierType": "node_id", "nodeId": node}, "connectionKind": "all", "limit": 25}})
        page_kinds = Counter(c["connectionKind"] for c in page["connections"])
        record("progression guide (informative): all page on the standard with most direct builds that also has related links",
               True,
               {"snapshot": snap, "node": node, "storedBuilds": count, "storedRelated": related_count,
                "allPageKinds": dict(page_kinds), "stoppingReason": page["page"]["stoppingReason"]})


async def step8(client: Client) -> None:
    """Component citation text and the three evidence reads (step 8, LC reference)."""

    text, _ = await call(client, "get_learning_components_for_standard", {"request": {
        "frameworkId": FW, "snapshotId": SNAP, "identifier": NODE}})
    record("step8: one supporting component 20507dfe…, confidence 0.97, model-generated label",
           "Supporting learning components: 1" in text
           and "Learning component: 20507dfe-4d56-575c-b7ea-33b1f9072300" in text
           and "Support confidence: 0.97" in text and "Model-generated decomposition" in text)
    fields = dict(re.findall(r"^\s*(Standard URI|Standard learning components URI|Support relationship ID|"
                             r"Support relationship URI|Direction|Component URI|Component provenance URI): (.+)$",
                             text, flags=re.M))
    record("step8/LC reference: text prints all citation fields",
           len(fields) == 7 and fields["Support relationship ID"] == "5f89e75a-70c5-5260-b325-31fcba940574"
           and fields["Direction"] == "component -> standard", fields)
    support = await read_all(client, fields["Support relationship URI"])
    provenance = await read_all(client, fields["Component provenance URI"])
    standard = await read_all(client, STD_PROV)
    record("step8: three reads complete in one window each: 1,049, 541, 3,077 bytes",
           [support.get("windows"), provenance.get("windows"), standard.get("windows")] == [1, 1, 1]
           and [support.get("bytes"), provenance.get("bytes"), standard.get("bytes")] == [1049, 541, 3077],
           [(support.get("windows"), support.get("bytes")), (provenance.get("windows"), provenance.get("bytes")),
            (standard.get("windows"), standard.get("bytes"))])
    relationship = json.loads(support["content"])
    record("step8: support record is a supports relationship from the component to the standard",
           "supports" in json.dumps(relationship)
           and "20507dfe-4d56-575c-b7ea-33b1f9072300" in json.dumps(relationship)
           and TGT in json.dumps(relationship),
           {k: relationship.get(k) for k in list(relationship)[:8]})


async def step9(client: Client) -> None:
    """Progression coverage records and the separate hierarchy report (steps 9 and 9a)."""

    edge, _ = await call(client, "get_learning_progression", {"request": {
        "frameworkId": FW, "snapshotId": SNAP, "relationshipId": REL}})
    meta = edge["metadata"]
    summary = await read_all(client, meta["summaryUri"])
    validation = await read_all(client, meta["validationUri"])
    unresolved = await read_all(client, meta["unresolvedUri"])
    record("step9: summary 4,577, validation 1,806, LP unresolved 214 bytes, each one window",
           [summary.get("bytes"), validation.get("bytes"), unresolved.get("bytes")] == [4577, 1806, 214]
           and [summary.get("windows"), validation.get("windows"), unresolved.get("windows")] == [1, 1, 1],
           [(summary.get("bytes"), summary.get("windows")), (validation.get("bytes"), validation.get("windows")),
            (unresolved.get("bytes"), unresolved.get("windows"))])
    lp_unresolved = json.loads(unresolved["content"])
    record("step9: Nigeria LP unresolved record has empty claims and total_needs_review 0",
           lp_unresolved.get("claims") == [] and lp_unresolved.get("total_needs_review") == 0,
           {k: v for k, v in lp_unresolved.items() if k in ("claims", "total_needs_review")})
    record("access-tools: metadata.unresolvedUri is not the /unresolved hierarchy report",
           not meta["unresolvedUri"].endswith("/unresolved"), meta["unresolvedUri"])
    summary_text = summary["content"].lower()
    record("step9: Nigeria summary says validation is structural only",
           "structural" in summary_text, None)
    cbse = await read_all(client, CBSE_SUMMARY)
    record("step9: CBSE summary reports one needs_review claim, one window",
           cbse.get("windows") == 1 and re.search(r'"(needs_review|total_needs_review|needs_review_claims)"\s*:\s*1\b', cbse["content"]) is not None,
           re.findall(r'"[a-z_]*needs_review[a-z_]*"\s*:\s*[^,}\]]+', cbse["content"])[:6])
    default = await read_all(client, GH_UNRESOLVED)
    small = await read_all(client, GH_UNRESOLVED, 4096)
    record("step9a/access-tools: Ghana hierarchy report 42,831 bytes in 3 windows at default 16,384",
           default.get("bytes") == 42831 and default.get("windows") == 3 and default.get("maxContentBytes") == 16384
           and default["statuses"][:-1] == ["partial", "partial"],
           {k: default.get(k) for k in ("bytes", "windows", "maxContentBytes", "statuses")})
    record("step9a/access-tools: same report takes 11 windows at maxContentBytes 4096",
           small.get("windows") == 11 and small.get("bytes") == 42831, {k: small.get(k) for k in ("bytes", "windows")})
    hierarchy = json.loads(default["content"])
    record("step9a: /unresolved is the standards-hierarchy report (no LP claim fields)",
           "claims" not in hierarchy and "total_needs_review" not in hierarchy,
           sorted(hierarchy)[:12] if isinstance(hierarchy, dict) else type(hierarchy).__name__)
    manifest = await read_all(client, meta["manifestUri"])
    provenance = await read_all(client, edge["relationship"]["provenanceUri"]) if "provenanceUri" in edge.get("relationship", {}) else {}
    record("access-tools: Nigeria manifest 22,348 bytes in two default windows",
           manifest.get("bytes") == 22348 and manifest.get("windows") == 2, (manifest.get("bytes"), manifest.get("windows")))
    if provenance:
        record("access-tools: diagnostic relationship provenance 12,275 bytes in one window",
               provenance.get("bytes") == 12275 and provenance.get("windows") == 1,
               (provenance.get("bytes"), provenance.get("windows")))


async def workflows(client: Client, state: Any) -> None:
    """Steps 11-13 and the prompt reference wording for per-kind and per-type calls."""

    native_args = {
        "framework_id": FW, "snapshot_id": SNAP, "identifier": json.dumps(NODE),
        "local_context": CONTEXT, "output_language": "en"}
    native = await client.get_prompt("learning_progression_support_plan", native_args)
    message = native.messages[0].content.text
    tool, _ = await call(client, "get_workflow_instructions", {"request": {
        "workflowName": "learning_progression_support_plan", "frameworkId": FW, "snapshotId": SNAP,
        "identifier": NODE, "localContext": CONTEXT, "outputLanguage": "en"}})
    record("step12: rendered.message equals native support-plan prompt with the new note",
           tool["rendered"]["message"] == message and CONTEXT in message)
    record("step11: support plan shows version 1.4.0, EVIDENCE ACCESS and EVIDENCE LINKS",
           "1.4.0" in message and "EVIDENCE ACCESS" in message and "EVIDENCE LINKS" in message)
    direct = [r for r in requests_in(message) if "connectionKind" in r]
    record("prompts reference: support plan reads incoming_builds and related in two calls, limit 25",
           [r["connectionKind"] for r in direct] == ["incoming_builds", "related"]
           and all(r["limit"] == 25 and "cursor" not in r for r in direct),
           [(r["connectionKind"], r.get("limit")) for r in direct])
    record("prompts reference: support plan says do not follow nextCursor and reports incomplete kinds",
           message.count("do not follow nextCursor") >= 2 and "page of 25" not in message)

    teaching = await client.get_prompt("learning_progression_teaching_sequence", {
        "framework_id": FW, "snapshot_id": SNAP, "topic_or_standard": "count", "output_language": "en"})
    teaching_message = teaching.messages[0].content.text
    kinds = [r["connectionKind"] for r in requests_in(teaching_message) if "connectionKind" in r]
    record("prompts reference: teaching sequence uses outgoing_builds, incoming_builds, related",
           kinds == ["outgoing_builds", "incoming_builds", "related"] and "nine" in teaching_message.lower()
           or kinds == ["outgoing_builds", "incoming_builds", "related"] and "9 " in teaching_message,
           {"kinds": kinds, "nineMentioned": bool(re.search(r"\b(9|nine)\b", teaching_message))})

    review_request = {
        "workflowName": "learning_progression_curriculum_review", "frameworkId": GH_FW, "snapshotId": GH_SNAP,
        "localGradeLabels": ["BASIC 5"], "endpointScope": "either", "outputLanguage": "en"}
    review, _ = await call(client, "get_workflow_instructions", {"request": review_request})
    review_message = review["rendered"]["message"]
    record("step13: rendered step 3 lists a buildsTowards scan and a relatesTo scan, at most 3 pages each",
           "- buildsTowards scan:" in review_message and "- relatesTo scan:" in review_message
           and "at most 3 pages" in review_message)
    record("step13: up to five per type in the inspection rule",
           "select up to 5 per type" in review_message)
    labels = {}
    for runtime in state.catalog_load_result.package_runtimes:
        if str(runtime.catalog_package.package_identity.snapshot_id) == GH_SNAP:
            labels = {r.relationship_id: r.label for r in runtime.loaded_package.relationships}
    scans = [r for r in requests_in(review_message) if "relationshipTypes" in r]
    outcome = {}
    for scan in scans:
        current, pages = dict(scan), []
        for _ in range(3):
            data, _ = await call(client, "search_learning_progressions", {"request": current})
            pages.append(data["page"])
            types = {labels[i["relationship"]["relationshipId"]] for i in data["relationships"]}
            if types - set(scan["relationshipTypes"]):
                outcome.setdefault("mixed", []).append(scan["relationshipTypes"])
            if data["page"]["nextCursor"] is None:
                break
            current = {**scan, "cursor": data["page"]["nextCursor"]}
        outcome[scan["relationshipTypes"][0]] = {
            "returned": [p["returnedCount"] for p in pages],
            "stopping": [p["stoppingReason"] for p in pages],
            "cursorLeft": pages[-1]["nextCursor"] is not None,
        }
    record("step13: each scan returns 7 per page with byte_limit, 21 per type, cursor left after page 3",
           "mixed" not in outcome
           and all(outcome.get(t, {}).get("returned") == [7, 7, 7]
                   and outcome[t]["stopping"] == ["byte_limit"] * 3 and outcome[t]["cursorLeft"]
                   for t in ("buildsTowards", "relatesTo")),
           outcome)

    single, _ = await call(client, "get_workflow_instructions", {"request": {**review_request, "relationshipTypes": ["relatesTo"]}})
    native_single = await client.get_prompt("learning_progression_curriculum_review", {
        "framework_id": GH_FW, "snapshot_id": GH_SNAP, "local_grade_labels": json.dumps(["BASIC 5"]),
        "endpoint_scope": "either", "output_language": "en", "relationship_types": json.dumps(["relatesTo"])})
    single_scans = [r["relationshipTypes"] for r in requests_in(single["rendered"]["message"]) if "relationshipTypes" in r]
    record("step13: relationshipTypes [relatesTo] gives a single relatesTo scan; native relationship_types equal",
           single_scans == [["relatesTo"]] and native_single.messages[0].content.text == single["rendered"]["message"],
           single_scans)
    empty = await client.get_prompt("learning_progression_curriculum_review", {
        "framework_id": GH_FW, "snapshot_id": GH_SNAP, "relationship_types": "[]"})
    empty_scans = [r["relationshipTypes"] for r in requests_in(empty.messages[0].content.text) if "relationshipTypes" in r]
    record("prompts reference: relationship_types empty JSON array means both types",
           empty_scans == [["buildsTowards"], ["relatesTo"]], empty_scans)

    # The four existing teaching/study workflows: three one-page calls per standard.
    legacy: dict[str, Any] = {}
    for name, args in {
        "teacher_guide_draft": {"topic_or_standard": "count", "grade_or_stage": "PRIMARY ONE"},
        "student_study_support": {"topic_or_standard": "count", "grade_or_stage": "PRIMARY ONE"},
        "student_handbook_section": {"topic_or_standard": "count", "grade_or_stage": "PRIMARY ONE"},
        "multigrade_lesson_plan": {"topic_or_standard": "count",
                                   "grades_in_room": json.dumps(["PRIMARY ONE", "PRIMARY TWO"])},
    }.items():
        try:
            prompt = await client.get_prompt(name, {"framework_id": FW, "snapshot_id": SNAP, **args})
        except Exception as error:  # pylint: disable=W0718
            legacy[name] = f"render failed: {str(error)[:160]}"
            continue
        msg = prompt.messages[0].content.text
        legacy[name] = {
            "kinds": [r["connectionKind"] for r in requests_in(msg) if "connectionKind" in r],
            "allKind": '"connectionKind":"all"' in msg,
            "pageOf25": "page of 25" in msg,
        }
    record("prompt guide: four existing workflows request each connection kind separately",
           all(isinstance(v, dict) and v["kinds"] == ["outgoing_builds", "incoming_builds", "related"]
               and not v["allKind"] and not v["pageOf25"] for v in legacy.values()),
           legacy)


async def check() -> None:
    """Run each claim group against the real app."""

    state = bootstrap_application()
    with patch("kgfegmcp.app.bootstrap_application", return_value=state):
        async with Client(create_mcp()) as client:
            for group in (step1(client, state), step3(client, state), step8(client), step9(client),
                          workflows(client, state)):
                try:
                    await group
                except Exception as error:  # pylint: disable=W0718
                    record(f"harness: claim group raised {type(error).__name__}", False, str(error)[:400])

    failed = [r["claim"] for r in RESULTS if not r["pass"]]
    OUT.write_text(json.dumps({"results": RESULTS, "failed": failed}, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(json.dumps({"checks": len(RESULTS), "failed": failed}, indent=1))


if __name__ == "__main__":
    with patch.object(socket.socket, "connect", side_effect=AssertionError("Network forbidden")):
        asyncio.run(check())
