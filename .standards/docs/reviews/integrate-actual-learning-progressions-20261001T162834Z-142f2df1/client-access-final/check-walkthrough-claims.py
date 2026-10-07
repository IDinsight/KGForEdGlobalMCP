"""Reviewer diagnostic: check walkthrough/reference claims the owner checker does not assert.

Runs the real create_mcp app through an in-process FastMCP client with sockets blocked
and no model calls. Each check is recorded as pass/fail with the observed value, so a
failed claim is reported rather than hidden. Output: walkthrough-claims-results.json
beside this file. Reviewer evidence only; not Tester-owned acceptance coverage.

Usage (repository root, locked backend environment):
    uv --directory backend run --locked --offline --no-sync python <abs-path-to-this-file>
"""

# Standard Library
import asyncio
import json
import socket

from pathlib import Path
from unittest.mock import patch

# Third Party Library
from fastmcp import Client

# Package Library
from kgfegmcp.app import create_mcp
from kgfegmcp.bootstrap import bootstrap_application

OUT = Path(__file__).resolve().parent / "walkthrough-claims-results.json"
FW = "nigeria-nerdc-mathematics-primary-1-3"
SNAP = "nigeria-nerdc-mathematics-primary-1-3@undated+bc5e769ed26f"
REL = "0129f5d5-42fd-52cb-bcf2-ec07c47103e7"
TGT = "e399b510-48bb-58ee-abda-61460a5a853b"
NODE = {"identifierType": "node_id", "nodeId": TGT}
CONTEXT = "Learners explain the whole but confuse equal-sized parts."
RESULTS: list[dict[str, object]] = []


def record(claim: str, ok: bool, observed: object) -> None:
    """Keep every claim outcome, passing or not."""

    RESULTS.append({"claim": claim, "pass": bool(ok), "observed": observed})


async def call(client: Client, name: str, args: dict) -> tuple[object, object]:
    """Call one tool and return parsed ordinary text (JSON when possible) and result."""

    result = await client.call_tool(name, args, raise_on_error=False)
    text = result.content[0].text
    if result.is_error or not text.startswith("{"):
        return text, result
    return json.loads(text), result


async def read_all(client: Client, uri: str, size: int = 16384) -> dict:
    """Replay read_evidence nextRequest from ordinary text until complete."""

    request = {"request": {"uri": uri, "maxContentBytes": size}}
    parts, windows = [], 0
    while True:
        data, _ = await call(client, "read_evidence", request)
        if isinstance(data, str):
            return {"error": data.split(":", 1)[0]}
        windows += 1
        parts.append(data["content"])
        if data["page"]["isComplete"]:
            return {"windows": windows, "content": "".join(parts),
                    "bytes": data["page"]["totalBytes"]}
        request = {"request": data["page"]["nextRequest"]}


async def check() -> None:
    """Run each independent claim check."""

    state = bootstrap_application()
    with patch("kgfegmcp.app.bootstrap_application", return_value=state):
        async with Client(create_mcp()) as client:
            # Step 1: are the counts the walkthrough asks for visible in ordinary text?
            caps, caps_result = await call(client, "get_capabilities", {})
            caps_text = caps if isinstance(caps, str) else json.dumps(caps)
            record("step1: capabilities text names read_evidence and get_workflow_instructions",
                   "read_evidence" in caps_text and "get_workflow_instructions" in caps_text,
                   None)
            prompt_names = sorted(p.name for p in await client.list_prompts())
            record("step1: capabilities text shows a prompt count or all nine prompt names",
                   all(name in caps_text for name in prompt_names) and len(prompt_names) == 9,
                   [line for line in caps_text.splitlines() if "rompt" in line][:5])
            record("step1: capabilities text shows 'Resources: 1 fixed, 14 templates'",
                   "Resources: 1 fixed, 14 templates" in caps_text,
                   [line for line in caps_text.splitlines() if "esource" in line][:5])
            record("step1: capabilities text tool count line",
                   True, [line for line in caps_text.splitlines() if "ool" in line][:5])

            # Step 2: field names and notices in the JSON text.
            exact, exact_result = await call(client, "get_learning_progression", {"request": {
                "frameworkId": FW, "snapshotId": SNAP, "relationshipId": REL}})
            row = exact["relationships"][0]
            nodes = {n["nodeId"]: n for n in exact["nodes"]}
            record("step2: relationshipUri and provenanceUri on the edge row",
                   bool(row.get("relationshipUri")) and bool(row.get("provenanceUri")),
                   sorted(row))
            record("step2: standardUri for both endpoints",
                   all(nodes[k].get("standardUri") for k in nodes) and len(nodes) == 2,
                   {k[:8]: bool(v.get("standardUri")) for k, v in nodes.items()})
            notices = json.dumps(exact["metadata"]).lower()
            record("step2: generated-origin notice present",
                   "generated" in notices or "llm_inferred" in notices,
                   [k for k in exact["metadata"] if "otice" in k])
            record("step2: continuationNotice says no continuation",
                   "no continuation" in exact["continuationNotice"].lower(),
                   exact["continuationNotice"])
            record("step2: judgment confidence notice says model judgment",
                   "model" in json.dumps(row["judgment"]).lower(),
                   [k for k in row["judgment"]])
            record("step2: summaryUri/validationUri/unresolvedUri exist in metadata",
                   all(exact["metadata"].get(k) for k in
                       ("summaryUri", "validationUri", "unresolvedUri")), None)
            record("step2: ordinary text equals structuredContent",
                   exact == exact_result.structured_content, None)

            # Step 3: statement of c4885674.
            direct, _ = await call(client, "get_standard_progressions", {"request": {
                "frameworkId": FW, "snapshotId": SNAP, "connectionKind": "all",
                "identifier": NODE}})
            dnodes = {n["nodeId"][:8]: n["statementExcerpt"] for n in direct["nodes"]}
            record("step3: c4885674 statement mentions 'Count and read correctly from 1-9'",
                   "count and read correctly from 1-9" in dnodes.get("c4885674", "").lower(),
                   dnodes.get("c4885674"))

            # Step 4: page sizes and second page.
            request = {"request": {"frameworkId": FW, "snapshotId": SNAP,
                                   "relationshipTypes": ["buildsTowards"],
                                   "endpointScope": "either", "limit": 25}}
            sizes, pages_ids = [], []
            while True:
                data, _ = await call(client, "search_learning_progressions", request)
                ids = [r["relationship"]["relationshipId"] for r in data["relationships"]]
                sizes.append(len(ids))
                pages_ids.append(ids)
                if not data["page"]["nextCursor"]:
                    break
                request = {"request": data["page"]["nextRequest"]}
            record("step4: second page has seven IDs different from the first",
                   len(pages_ids[1]) == 7 and not set(pages_ids[0]) & set(pages_ids[1]),
                   sizes[:3])
            record("progression reference: 27 pages of seven", sizes == [7] * 27, sizes)

            # Step 5: deepest upstream supports.
            trav, _ = await call(client, "traverse_learning_progressions", {"request": {
                "frameworkId": FW, "snapshotId": SNAP, "direction": "upstream",
                "identifier": NODE, "maxDepth": 3, "maxNodes": 20, "maxEdges": 30}})
            distances = trav.get("distances") or trav.get("nodeDistances")
            tnodes = {n["nodeId"][:8]: n["statementExcerpt"] for n in trav["nodes"]}
            record("step5: traversal node statements (deepest supports)",
                   "ec0c6a6d" in tnodes and "b193d5b5" in tnodes
                   and "count correctly up to 5" in tnodes["ec0c6a6d"].lower()
                   and "sort and classify number of objects" in tnodes["b193d5b5"].lower(),
                   {"statements": tnodes, "distances": distances,
                    "keys": sorted(trav)})

            # Step 6: intermediate nodes of the two paths.
            paths, _ = await call(client, "get_learning_progression_paths", {"request": {
                "frameworkId": FW, "snapshotId": SNAP, "maxDepth": 3, "maxPaths": 3,
                "sourceIdentifier": {"identifierType": "node_id",
                                     "nodeId": "ec0c6a6d-0a48-5aa8-bdfe-72260dd3b559"},
                "targetIdentifier": NODE}})
            middles = [[n[:8] for n in p["nodeIds"]][1:-1] for p in paths["paths"]]
            record("step6: paths go through c4885674 then 12b603df",
                   middles == [["c4885674"], ["12b603df"]], middles)
            record("step6: paths continuationNotice says no continuation",
                   "no continuation" in paths["continuationNotice"].lower(),
                   paths["continuationNotice"])
            record("traversal continuationNotice says no continuation",
                   "no continuation" in trav["continuationNotice"].lower(),
                   trav["continuationNotice"])

            # Step 8: LC labelled as model-generated decomposition.
            lcs, _ = await call(client, "get_learning_components_for_standard", {"request": {
                "frameworkId": FW, "snapshotId": SNAP, "identifier": NODE}})
            record("step8: LC text labels a model-generated decomposition",
                   "generated" in lcs.lower() and "decomposition" in lcs.lower(),
                   [line for line in lcs.splitlines()
                    if "enerat" in line or "ecompos" in line][:6])

            # Step 9: Nigeria summary content and CBSE needs_review exclusion.
            summary = await read_all(client, exact["metadata"]["summaryUri"])
            body = json.loads(summary["content"])
            flat = json.dumps(body).lower()
            record("step9: Nigeria summary has stored counts, eligibility limits, structural-only validation",
                   "buildstowards" in flat and "eligib" in flat and "structural" in flat,
                   sorted(body)[:40])
            cbse_uri = ("kgfegmcp://framework/india-cbse-science-learning-framework-classes-9-10/"
                        "snapshot/india-cbse-science-learning-framework-classes-9-10%40undated"
                        "%2B576740bed2d1/learning-progressions")
            cbse = json.loads((await read_all(client, cbse_uri))["content"])
            record("step9: CBSE summary reports needs_review kept out of accepted edges",
                   cbse.get("needsReviewClaims") == 1
                   and ("accepted" in json.dumps(cbse).lower()),
                   {k: cbse[k] for k in cbse if "eview" in k or "otice" in k})

            # Steps 11-12: rendered support-plan instructions.
            native = await client.get_prompt("learning_progression_support_plan", {
                "framework_id": FW, "snapshot_id": SNAP, "identifier": json.dumps(NODE),
                "local_context": CONTEXT, "output_language": "en"})
            message = native.messages[0].content.text
            for phrase in ("[GENERATED-EVIDENCE / llm_inferred]", "NERDC", "ten",
                           "32", "EVIDENCE ACCESS", "EVIDENCE LINKS", SNAP):
                record(f"step11: rendered message contains {phrase!r}", phrase in message, None)
            lower = message.lower()
            record("step11: observations treated as caller reports, not diagnosis",
                   "diagnos" in lower, [line for line in message.splitlines()
                                        if "diagnos" in line.lower()][:3])
            record("step11: related concepts kept separate from incoming builds",
                   "related" in lower, None)
            workflow, _ = await call(client, "get_workflow_instructions", {"request": {
                "workflowName": "learning_progression_support_plan", "frameworkId": FW,
                "snapshotId": SNAP, "identifier": NODE, "localContext": CONTEXT,
                "outputLanguage": "en"}})
            record("step12: instructionsNotice says the server has not run it",
                   "not run" in workflow["instructionsNotice"].lower(),
                   workflow["instructionsNotice"])
            record("step12: rendered.message equals native message",
                   workflow["rendered"]["message"] == message, None)

            # access-tools error table: unknown snapshot error code.
            bad_snapshot = ("kgfegmcp://framework/nigeria-nerdc-mathematics-primary-1-3/"
                            "snapshot/nigeria-nerdc-mathematics-primary-1-3%40undated%2B000000000000"
                            "/manifest")
            out = await read_all(client, bad_snapshot)
            record("access-tools: unknown snapshot reports framework_not_found",
                   out.get("error") == "framework_not_found", out)

    OUT.write_text(json.dumps({"results": RESULTS,
                               "failed": [r["claim"] for r in RESULTS if not r["pass"]]},
                              indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"checks": len(RESULTS),
                      "failed": [r["claim"] for r in RESULTS if not r["pass"]]}, indent=1))


if __name__ == "__main__":
    with patch.object(socket.socket, "connect", side_effect=AssertionError("Network forbidden")):
        asyncio.run(check())
