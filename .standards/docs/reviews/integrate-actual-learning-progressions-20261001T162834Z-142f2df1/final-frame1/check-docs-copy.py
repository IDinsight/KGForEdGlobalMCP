"""Check the style-reworked documentation (0.4.0) against the real local server.

Copied from frame1-rework-20261007/check-docs.py; updated for plain-language wording and
adds a scan for development-history terms in public docs.

Derived from client-access-20261006/check-docs.py. Adds the rework facts: included graph
types and LP counts in discovery text and the graphTypes filter, component citation
handles, per-kind direct calls, per-type curriculum-review scans, the D1 walkthrough
corrections (window counts tied to window size, LP versus hierarchy unresolved records,
classroom note), stale-wording absence and shipped README equality with the candidate.

Documenter evidence only, not Tester-owned acceptance coverage. It executes the saved
guide, access-tool and Claude Desktop walkthrough examples through an in-process FastMCP
client (sockets blocked, no model calls), asserts each documented expectation against
actual results, checks that the documented numbers appear in the saved pages, verifies
inventory lists, prompt facts and the catalog table, and validates rendered local links.

Usage (from the repository root, locked backend environment):
    uv --directory backend run --locked --offline --no-sync python <abs-path-to-this-file> <site-dir>
"""
import asyncio
import zipfile
import hashlib
import json
import re
import socket
import sys
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch
from urllib.parse import quote, unquote, urlsplit

from fastmcp import Client
from kgfegmcp.app import create_mcp
from kgfegmcp.bootstrap import bootstrap_application

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent / "check-docs-copy-results.json"
SITE = Path(sys.argv[1]).resolve()

FW = "nigeria-nerdc-mathematics-primary-1-3"
SNAP = "nigeria-nerdc-mathematics-primary-1-3@undated+bc5e769ed26f"
REL = "0129f5d5-42fd-52cb-bcf2-ec07c47103e7"
TGT = "e399b510-48bb-58ee-abda-61460a5a853b"
SRC = "12b603df-b6f0-50b3-914d-5d655a2dbaf1"
GFW = "ghana-nacca-primary-mathematics-basic-4-6"
GSNAP = "ghana-nacca-primary-mathematics-basic-4-6@2019+0b768f7cfaf9"
NOTE = "Learners can count to 9 but often write 6 and 9 the wrong way round."
SUPPORT = "5f89e75a-70c5-5260-b325-31fcba940574"
CANDIDATE = ROOT / "data/source_artifacts/learning_progressions/frame1-rework-dev022/kgfegmcp-0.4.0-frame1-rework.mcpb"
BASE = f"kgfegmcp://framework/{FW}/snapshot/{quote(SNAP, safe='')}"
TOOLS = sorted([
    "compare_framework_evidence", "get_capabilities", "get_framework",
    "get_framework_statistics", "get_learning_component", "get_learning_component_context",
    "get_learning_components_for_standard", "get_learning_progression",
    "get_learning_progression_paths", "get_standard", "get_standard_context",
    "get_standard_progressions", "get_workflow_instructions", "list_frameworks",
    "read_evidence", "search_learning_components", "search_learning_progressions",
    "search_standards", "traverse_learning_progressions"])
SEVEN = ["learning_progression_teaching_sequence", "learning_progression_support_plan",
         "learning_progression_curriculum_review", "teacher_guide_draft",
         "student_study_support", "student_handbook_section", "multigrade_lesson_plan"]


def sha(data):
    """Hash bytes or text for the receipt."""
    if isinstance(data, str):
        data = data.encode()
    return "sha256:" + hashlib.sha256(data).hexdigest()


def doc(path):
    """Read a saved documentation page."""
    return (ROOT / path).read_text()


def need(page, *phrases):
    """Require each documented phrase to be present in the saved page."""
    text = " ".join(doc(page).split())
    for phrase in phrases:
        assert " ".join(phrase.split()) in text, (page, phrase)


def listed(text, start, stop):
    """Collect backticked or bare identifiers listed between two headings."""
    section = text.split(start, 1)[1].split(stop, 1)[0]
    return sorted(set(re.findall(r"^[-\s]*`?([a-z_]+)`?\s*$", section, re.M)) - {""})


class Client2:
    """Small helper around one in-process client returning parsed text results."""

    def __init__(self, client):
        self.c = client
        self.calls = 0

    async def call(self, name, args):
        """Call a tool and parse its text block; return (data or error text, result)."""
        self.calls += 1
        result = await self.c.call_tool(name, args, raise_on_error=False)
        text = result.content[0].text
        if result.is_error:
            return text, result
        return (json.loads(text) if text.startswith("{") else text), result

    async def read_all(self, uri, max_bytes=None):
        """Read a resource through read_evidence by replaying text-only nextRequest.

        ``max_bytes`` None omits maxContentBytes so the server default window applies.
        """
        request = {"request": {"uri": uri}}
        if max_bytes is not None:
            request["request"]["maxContentBytes"] = max_bytes
        windows, parts, statuses = 0, [], []
        while True:
            data, result = await self.call("read_evidence", request)
            if isinstance(data, str):
                return {"error": data}
            assert data == result.structured_content
            windows += 1
            parts.append(data["content"])
            statuses.append(data["contentStatus"])
            if data["page"]["isComplete"]:
                content = "".join(parts)
                assert sha(content) == data["metadata"]["contentSha256"]
                return {"windows": windows, "bytes": data["page"]["totalBytes"],
                        "statuses": statuses, "content": content,
                        "canonicalUri": data["metadata"]["canonicalUri"],
                        "sha": data["metadata"]["contentSha256"]}
            request = {"request": data["page"]["nextRequest"]}


async def check():
    """Execute every documented example and expectation."""
    state = bootstrap_application()
    ev = {"walkthrough": {}, "guide": [], "access": {}, "prompts": {}, "inventory": {}}
    with patch("kgfegmcp.app.bootstrap_application", return_value=state):
        async with Client(create_mcp()) as raw:
            c = Client2(raw)
            tools = sorted(t.name for t in await raw.list_tools())
            prompts = sorted(p.name for p in await raw.list_prompts())
            templates = await raw.list_resource_templates()
            fixed = await raw.list_resources()
            assert tools == TOOLS and len(prompts) == 9 and len(templates) == 14 and len(fixed) == 1
            ev["inventory"] = {"tools": tools, "prompts": prompts, "templates": len(templates)}
            # Documented tool lists equal the registered names.
            assert listed(doc("README.md"), "### Tools", "### Prompts") == TOOLS
            assert listed(doc("docs/index.md"), "### Tools", "### Prompts") == TOOLS
            assert listed(doc("backend/README.md"), "### Tools", "### Prompts") == TOOLS
            assert sorted(re.findall(r"^\| `([a-z_]+)`", doc("docs/reference/index.md").split(
                "## Tool inventory", 1)[1].split("## Input naming", 1)[0], re.M)) == TOOLS
            for page in ["README.md", "backend/README.md", "docs/index.md",
                         "docs/reference/index.md", "docs/getting-started/index.md",
                         "packaging/mcpb/README.md", "docs/operations/cli.md"]:
                assert re.search(r"\b19\b", doc(page)), page

            # Walkthrough step 1.
            data, result = await c.call("list_frameworks", {"request": {}})
            assert "Framework snapshots: 6 of 6" in data and SNAP in data
            snaps = re.findall(r"^Snapshot ID: (\S+)$", data, re.M)
            assert len(snaps) == 6
            assert data.count("Routing graph types: academic_standards\n") == 6
            assert data.count("Included graph types: academic_standards, learning_components, learning_progressions\n") == 6
            assert data.count("learning_progressions=available") == 6
            assert re.search(rf"^- {re.escape(SNAP)}--\S+ \|.*learning_progressions=available \| builds_towards=189 \| relates_to=297 \|", data, re.M)
            assert re.search(rf"^- {re.escape(GSNAP)}--\S+ \|.*builds_towards=299 \| relates_to=300 \|", data, re.M)
            assert "Graph types:" not in data.replace("Routing graph types:", "").replace("Included graph types:", "")
            filtered, _ = await c.call("list_frameworks", {"request": {"graphTypes": ["learning_progressions"]}})
            assert re.findall(r"^Snapshot ID: (\S+)$", filtered, re.M) == snaps
            caps, _ = await c.call("get_capabilities", {})
            assert "Routing graph types: academic_standards\n" in caps
            assert "Included graph types: academic_standards, learning_components, learning_progressions\n" in caps
            assert caps.count("    hasLearningProgressions: true") == 6
            gfw, _ = await c.call("get_framework", {"request": {"frameworkId": FW, "snapshotId": SNAP}})
            assert "  Learning progressions: true" in gfw and "  LP provenance: true" in gfw
            assert "learning_progressions[builds_towards=189, relates_to=297]" in gfw
            need("docs/getting-started/claude-clients.md", "`builds_towards=189` and `relates_to=297`",
                 "`Routing graph types: academic_standards`",
                 "`Included graph types: academic_standards, learning_components, learning_progressions`",
                 "graphTypes [\"learning_progressions\"]", "`hasLearningProgressions: true`",
                 "shows a single `Graph types:` line")
            need("docs/guides/framework-discovery.md", "learning_progressions=available | builds_towards=189 | relates_to=297",
                 "Routing graph types: academic_standards",
                 "Included graph types: academic_standards, learning_components, learning_progressions")
            disc = re.findall(r"```json\n(.*?)\n```", doc("docs/guides/framework-discovery.md"), re.S)
            lp_filter = [b for b in disc if "learning_progressions" in b]
            assert len(lp_filter) == 1
            out, _ = await c.call("list_frameworks", json.loads(lp_filter[0]))
            assert re.findall(r"^Snapshot ID: (\S+)$", out, re.M) == snaps
            ev["discovery"] = {"snapshots": snaps, "lpFilterSnapshots": len(snaps)}
            assert "Resources: 1 fixed, 14 templates" in caps
            for name in TOOLS:
                assert name in caps
            # Step 2 uses the inline JSON saved in the page.
            page = doc("docs/getting-started/claude-clients.md")
            inline = re.findall(r"`(\{\"request\":.*?\}\})`", page)
            assert len(inline) == 4, inline
            exact, result = await c.call("get_learning_progression", json.loads(inline[0]))
            assert [b.type for b in result.content] == ["text"]
            assert exact == result.structured_content
            row = exact["relationships"][0]
            j = row["judgment"]
            assert row["relationship"]["relationshipType"] == "buildsTowards"
            assert row["relationship"]["sourceNodeId"] == SRC
            assert row["relationship"]["targetNodeId"] == TGT
            assert j["confidence"] == 0.72 and j["warningCount"] == 9
            assert len(j["warningExcerpts"]) == 5 and j["warningsOmitted"] and j["rationaleExcerpted"]
            statements = {n["nodeId"]: n["statementExcerpt"] for n in exact["nodes"]}
            assert statements[SRC] == "Pupils should be able to: write correctly number 1-5;"
            assert "No continuation is offered" in exact["continuationNotice"]
            assert [a["logicalName"] for a in exact["metadata"]["artifacts"]] == [
                "learningProgressionProvenance", "learningProgressionProvenanceIndex",
                "nodes", "relationships"]
            assert exact["metadata"]["limits"]["maxResultCharacters"] == 100000
            need("docs/getting-started/claude-clients.md", "`judgment.confidence` 0.72",
                 "`warningCount` 9, five `warningExcerpts`")
            # Step 3.
            direct, _ = await c.call("get_standard_progressions", {"request": {
                "frameworkId": FW, "snapshotId": SNAP, "connectionKind": "all", "limit": 25,
                "identifier": {"identifierType": "node_id", "nodeId": TGT}}})
            kinds = [x["connectionKind"] for x in direct["connections"]]
            incoming = sorted((x["relationshipId"][:8], x["sourceMatch"]["nodeId"][:8])
                              for x in direct["connections"] if x["connectionKind"] == "incoming_builds")
            assert len(kinds) == 8 and kinds.count("related") == 6
            assert incoming == [("0129f5d5", "12b603df"), ("c0155efa", "c4885674")]
            assert direct["page"]["isComplete"] and direct["page"]["nextCursor"] is None
            per_kind = {}
            for kind in ("outgoing_builds", "incoming_builds", "related"):
                got, _ = await c.call("get_standard_progressions", {"request": {
                    "frameworkId": FW, "snapshotId": SNAP, "connectionKind": kind, "limit": 25,
                    "identifier": {"identifierType": "node_id", "nodeId": TGT}}})
                assert got["page"]["isComplete"] and got["page"]["nextCursor"] is None
                assert {x["connectionKind"] for x in got["connections"]} <= {kind}
                per_kind[kind] = sorted(x["relationshipId"][:8] for x in got["connections"])
            assert per_kind["outgoing_builds"] == [] and per_kind["incoming_builds"] == ["0129f5d5", "c0155efa"]
            assert len(per_kind["related"]) == 6
            need("docs/getting-started/claude-clients.md", "Expected: no `outgoing_builds`; two `incoming_builds`",
                 "and six `related`", "returns the same eight connections here in one page")
            # Step 4: inline search request and cursor replay.
            request = json.loads(inline[1])
            pages, ids, first = 0, [], None
            while True:
                data, _ = await c.call("search_learning_progressions", request)
                p = data["page"]
                pages += 1
                ids += [x["relationship"]["relationshipId"] for x in data["relationships"]]
                if first is None:
                    first = p
                    assert p["returnedCount"] == 7 and p["stoppingReason"] == "byte_limit"
                    assert not p["isComplete"] and p["nextCursor"] and p["nextRequest"]
                    assert p["nextRequest"]["cursor"] == p["nextCursor"]
                if not p["nextCursor"]:
                    break
                request = {"request": p["nextRequest"]}
            assert pages == 27 and len(ids) == len(set(ids)) == 189
            need("docs/getting-started/claude-clients.md", "27 pages and 189 distinct")
            need("docs/reference/progression-tool.md", "189 stored `buildsTowards` edges arrive in 27 pages of seven")
            # Step 5.
            trav, _ = await c.call("traverse_learning_progressions", {"request": {
                "frameworkId": FW, "snapshotId": SNAP, "direction": "upstream",
                "identifier": {"identifierType": "node_id", "nodeId": TGT},
                "maxDepth": 3, "maxNodes": 20, "maxEdges": 30}})
            assert len(trav["nodes"]) == 5 and len(trav["relationships"]) == 5
            assert trav["scopeComplete"] and trav["graphExhausted"]
            assert trav["frontier"] == [] and trav["truncationReasons"] == []
            # Step 6.
            paths, _ = await c.call("get_learning_progression_paths", {"request": {
                "frameworkId": FW, "snapshotId": SNAP, "maxDepth": 3, "maxPaths": 3,
                "sourceIdentifier": {"identifierType": "node_id", "nodeId": "ec0c6a6d-0a48-5aa8-bdfe-72260dd3b559"},
                "targetIdentifier": {"identifierType": "node_id", "nodeId": TGT}}})
            assert [[r[:8] for r in x["relationshipIds"]] for x in paths["paths"]] == [
                ["41ec8cba", "c0155efa"], ["7fc3c0e1", "0129f5d5"]]
            assert paths["scopeComplete"] and not paths["graphExhausted"]
            assert paths["truncationReasons"] == ["depth_limit"] and paths["nextUnreturnedPath"] is None
            # Step 7.
            prov = await c.read_all(row["provenanceUri"])
            assert (await c.read_all(row["provenanceUri"], 16384))["windows"] == 1
            assert prov["windows"] == 1 and prov["bytes"] == 12275 and prov["statuses"] == ["full"]
            body = json.loads(prov["content"])
            assert body["relationshipId"] == REL and "provenance" in body
            assert (await c.read_all(row["provenanceUri"], 4096))["windows"] == 3
            # Step 8.
            lcs, _ = await c.call("get_learning_components_for_standard", {"request": {
                "frameworkId": FW, "snapshotId": SNAP,
                "identifier": {"identifierType": "node_id", "nodeId": TGT}}})
            assert "Supporting learning components: 1" in lcs
            assert "20507dfe-4d56-575c-b7ea-33b1f9072300" in lcs and "Support confidence: 0.97" in lcs
            assert "Write correctly the numbers 6 to 9" in lcs
            assert f"   Support relationship ID: {SUPPORT}" in lcs
            assert "   Direction: component -> standard" in lcs
            handles = dict(re.findall(r"^\s*(Standard URI|Standard learning components URI|Support relationship URI|Component URI|Component provenance URI): (kgfegmcp://\S+)$", lcs, re.M))
            assert len(handles) == 5, handles
            support_read = await c.read_all(handles["Support relationship URI"])
            assert support_read["windows"] == 1 and support_read["bytes"] == 1049
            assert json.loads(support_read["content"])["relationshipType"] == "supports"
            comp_prov = await c.read_all(handles["Component provenance URI"])
            assert comp_prov["windows"] == 1 and comp_prov["bytes"] == 541
            need("docs/getting-started/claude-clients.md", f"Support relationship ID: {SUPPORT}",
                 "`Direction: component -> standard`", "(1,049, 541 and 3,077 bytes)")
            ref = doc("docs/reference/learning-component-tools.md")
            for label in ["Standard URI", "Standard learning components URI", "Support relationship ID",
                          "Support relationship URI", "Component URI", "Component provenance URI", SUPPORT,
                          "not readable under package rights", "component -> standard"]:
                assert label in ref, label
            for suffix, size in [(f"/standard/{TGT}/provenance", 3077),
                                 ("/learning-component/20507dfe-4d56-575c-b7ea-33b1f9072300/provenance", 541)]:
                uri = BASE + suffix
                # The standard link is written in the page; the component link now comes
                # from the tool text (asserted equal to the handle above).
                assert uri in page if "/standard/" in suffix else uri == handles["Component provenance URI"]
                read = await c.read_all(uri)
                assert read["windows"] == 1 and read["bytes"] == size
            # Step 9.
            summary = await c.read_all(exact["metadata"]["summaryUri"])
            assert summary["bytes"] == 4577 and summary["windows"] == 1
            assert exact["metadata"]["unresolvedUri"].endswith("/artifact/learningProgressionUnresolved")
            assert exact["metadata"]["validationUri"].endswith("/artifact/learningProgressionValidation")
            validation = await c.read_all(exact["metadata"]["validationUri"])
            assert validation["windows"] == 1 and validation["bytes"] == 1806
            lp_unres = await c.read_all(exact["metadata"]["unresolvedUri"])
            assert lp_unres["windows"] == 1 and lp_unres["bytes"] == 214
            body9 = json.loads(lp_unres["content"])
            assert body9["claims"] == [] and body9["total_needs_review"] == 0
            step9 = page.split("### 9.", 1)[1].split("### 9a.", 1)[0]
            assert "/unresolved" not in step9
            (cbse_uri,) = re.findall(r"^(kgfegmcp://\S+)$", step9, re.M)
            cbse = await c.read_all(cbse_uri)
            assert cbse["windows"] == 1 and json.loads(cbse["content"])["needsReviewClaims"] == 1
            need("docs/getting-started/claude-clients.md", "progression validation report is 1,806 bytes",
                 "unresolved record (214 bytes)", "`total_needs_review` 0")
            step9a = page.split("### 9a.", 1)[1].split("### 10.", 1)[0]
            (ghana_uri,) = set(re.findall(r"`(kgfegmcp://[^`]+)`", step9a))
            assert ghana_uri.endswith("/unresolved")
            ghana = await c.read_all(ghana_uri)
            assert ghana["windows"] == 3 and ghana["bytes"] == 42831 and ghana["statuses"][0] == "partial"
            assert (await c.read_all(ghana_uri, 16384))["windows"] == 3
            assert (await c.read_all(ghana_uri, 4096))["windows"] == 11
            assert "not** progression evidence" in step9a and "standards-hierarchy report" in step9a
            need("docs/getting-started/claude-clients.md", "default window size of 16,384 bytes",
                 "with `\"maxContentBytes\":4096` the same record takes 11")
            # Step 10.
            bulk = next(a["uri"] for a in exact["metadata"]["artifacts"]
                        if a["logicalName"] == "learningProgressionProvenance")
            denied = await c.read_all(bulk)
            assert denied["error"].startswith("resource_access_denied")
            # Steps 11-12: native prompt and the inline workflow request render identically.
            native = await raw.get_prompt("learning_progression_support_plan", {
                "framework_id": FW, "snapshot_id": SNAP,
                "identifier": json.dumps({"identifierType": "node_id", "nodeId": TGT}),
                "local_context": NOTE,
                "output_language": "en"})
            message = native.messages[0].content.text
            wf, _ = await c.call("get_workflow_instructions", json.loads(inline[2]))
            assert wf["rendered"]["message"] == message
            assert wf["rendered"]["promptVersion"] == "1.4.0" == native.meta["promptVersion"]
            assert "EVIDENCE ACCESS" in message and "EVIDENCE LINKS" in message
            assert "at most 32 read_evidence windows" in message
            assert "has not run them" in wf["instructionsNotice"]
            assert "page of 25" not in message and "incoming builds are incomplete for the target" in message
            assert "related concepts are incomplete for the target" in message
            need("docs/getting-started/claude-clients.md", f"`local_context` `{NOTE}`",
                 "support relationship `5f89e75a…`")
            # Step 13: per-type curriculum review on Ghana BASIC 5.
            review, _ = await c.call("get_workflow_instructions", json.loads(inline[3]))
            rmsg = review["rendered"]["message"]
            assert "- buildsTowards scan:" in rmsg and "- relatesTo scan:" in rmsg
            assert "3 pages of 25" not in rmsg and "at most 75" not in rmsg
            scans = [json.loads(x) for x in re.findall(r'^(\{"request".*\})$', rmsg, re.M) if '"relationshipTypes"' in x]
            assert [x["request"]["relationshipTypes"] for x in scans] == [["buildsTowards"], ["relatesTo"]]
            scan_ev = {}
            for req in scans:
                kind = req["request"]["relationshipTypes"][0]
                pages_seen = []
                for _ in range(3):
                    got, _ = await c.call("search_learning_progressions", req)
                    pages_seen.append((got["page"]["returnedCount"], got["page"]["stoppingReason"]))
                    assert {r["relationship"]["relationshipType"] for r in got["relationships"]} == {kind}
                    req = {"request": got["page"]["nextRequest"]}
                assert pages_seen == [(7, "byte_limit")] * 3 and got["page"]["nextCursor"]
                scan_ev[kind] = pages_seen
            _, gres = await c.call("get_framework_statistics", {"request": {"frameworkId": GFW}})
            glp = gres.structured_content["statistics"]["learningProgressions"]
            assert (glp["buildsTowardsRelationships"], glp["relatesToRelationships"]) == (299, 300)
            only, _ = await c.call("get_workflow_instructions", {"request": {**json.loads(inline[3])["request"], "relationshipTypes": ["relatesTo"]}})
            omsg = only["rendered"]["message"]
            assert "- relatesTo scan:" in omsg and "- buildsTowards scan:" not in omsg
            native_only = await raw.get_prompt("learning_progression_curriculum_review", {
                "framework_id": GFW, "snapshot_id": GSNAP, "local_grade_labels": json.dumps(["BASIC 5"]),
                "endpoint_scope": "either", "output_language": "en",
                "relationship_types": json.dumps(["relatesTo"])})
            assert native_only.messages[0].content.text == omsg
            need("docs/getting-started/claude-clients.md", "reviews 21 links of each type",
                 "stores 299 `buildsTowards` and 300", "`relationship_types` `[\"relatesTo\"]`")
            ev["curriculumReview"] = {"scans": scan_ev, "messageSha256": sha(rmsg), "relatesToOnlySha256": sha(omsg)}
            for incoming_id in ("0129f5d5", "c0155efa"):
                assert incoming_id in json.dumps(direct)
            ev["walkthrough"] = {"searchPages": pages, "searchEdges": len(ids),
                                 "provenanceSha256": prov["sha"], "workflowMessageSha256": sha(message),
                                 "nativeEqualsTool": True, "status": "passed"}
            need("docs/getting-started/claude-clients.md", "12,275 bytes",
                 "Nigeria summary (4,577 bytes)", "42,831 bytes")

            # Access-tool reference examples and measured statements.
            access = doc("docs/reference/access-tools.md")
            blocks = re.findall(r"```json\n(.*?)\n```", access, re.S)
            assert len(blocks) == 2
            first_read, _ = await c.call("read_evidence", json.loads(blocks[0]))
            assert first_read["metadata"]["resourceKind"] == "relationship_provenance"
            wf2, _ = await c.call("get_workflow_instructions", json.loads(blocks[1]))
            assert wf2["rendered"]["message"] == message
            manifest = await c.read_all(BASE + "/manifest")
            assert manifest["windows"] == 2 and manifest["bytes"] == 22348
            lower = BASE.replace("%2B", "%2b") + "/manifest"
            canon = await c.read_all(lower)
            access_ev = {"lowercaseEscapeCanonical": canon.get("canonicalUri")}
            if "error" not in canon:
                assert canon["canonicalUri"] == BASE + "/manifest"
            template, _ = await c.call("read_evidence", {"request": {"uri": BASE + "/standard/{nodeId}"}})
            assert template.startswith("invalid_evidence_uri")
            for bad in ["kgfegmcp://catalog?x=1", "kgfegmcp://catalog#a", BASE + "//manifest",
                        BASE.replace("/snapshot/", "/snapshot/%2F") + "/manifest"]:
                out, _ = await c.call("read_evidence", {"request": {"uri": bad}})
                assert out.startswith("invalid_evidence_uri"), (bad, out)
            missing, _ = await c.call("read_evidence", {"request": {"uri": BASE + "/standard/00000000-0000-0000-0000-000000000000"}})
            access_ev["missingStandard"] = missing.split(":", 1)[0]
            assert access_ev["missingStandard"] == "standard_not_found"
            need("docs/reference/access-tools.md", "`resource_not_found`, `standard_not_found`")
            too_big, _ = await c.call("read_evidence", {"request": {"uri": "kgfegmcp://catalog", "maxContentBytes": 40000}})
            assert "32768" in too_big
            bad_wf, _ = await c.call("get_workflow_instructions", {"request": {"workflowName": "administrator_alignment_review", "frameworkId": FW}})
            assert isinstance(bad_wf, str) and "validation" in bad_wf.lower()
            extra, _ = await c.call("get_workflow_instructions", {"request": {**json.loads(blocks[1])["request"], "unexpected": 1}})
            assert isinstance(extra, str)
            ev["access"] = access_ev
            need("docs/reference/access-tools.md", "default window of 16,384 bytes",
                 "manifest (22,348 bytes) needs two", "42,831 bytes) needs three",
                 "`maxContentBytes` 4,096 the same report needs 11", "`learningProgressionUnresolved`")

            # Progression guide JSON examples, with returned-ID substitution.
            guide = doc("docs/guides/progression.md")
            examples = re.findall(r"```json\n(.*?)\n```", guide, re.S)
            assert len(examples) == 6
            names = ["search_learning_progressions", "get_learning_progression",
                     "get_standard_progressions", "traverse_learning_progressions",
                     "get_learning_progression_paths", "read_evidence"]
            replacements = {}
            for name, text in zip(names, examples):
                for key, value in replacements.items():
                    text = text.replace(key, value)
                data, result = await c.call(name, json.loads(text))
                assert isinstance(data, dict), (name, data)
                assert data == result.structured_content
                if name == names[0]:
                    edge = data["relationships"][0]
                    replacements = {
                        "<returned-snapshot-id>": data["metadata"]["package"]["packageIdentity"]["snapshotId"],
                        "<returned-relationship-id>": edge["relationship"]["relationshipId"],
                        "<returned-source-node-id>": edge["relationship"]["sourceNodeId"],
                        "<returned-target-node-id>": edge["relationship"]["targetNodeId"],
                        "<returned-provenance-uri>": edge["provenanceUri"]}
                ev["guide"].append({"tool": name, "resultSha256": sha(json.dumps(data, sort_keys=True))})

            # Prompt facts: native/tool parity for the seven, sections, versions.
            seven_args = {
                "learning_progression_teaching_sequence": {"framework_id": FW, "topic_or_standard": "fractions"},
                "learning_progression_support_plan": {"framework_id": FW, "identifier": json.dumps({"identifierType": "node_id", "nodeId": TGT})},
                "learning_progression_curriculum_review": {"framework_id": FW},
                "teacher_guide_draft": {"framework_id": FW, "topic_or_standard": "fractions", "grade_or_stage": "PRIMARY ONE"},
                "student_study_support": {"framework_id": FW, "topic_or_standard": "fractions", "grade_or_stage": "PRIMARY ONE"},
                "student_handbook_section": {"framework_id": FW, "topic_or_standard": "fractions", "grade_or_stage": "PRIMARY ONE"},
                "multigrade_lesson_plan": {"framework_id": FW, "topic_or_standard": "fractions", "grades_in_room": json.dumps(["PRIMARY ONE", "PRIMARY TWO"])}}
            camel = lambda k: re.sub(r"_([a-z])", lambda m: m.group(1).upper(), k)
            for name in SEVEN:
                args = seven_args[name]
                native = await raw.get_prompt(name, args)
                text = native.messages[0].content.text
                req = {"workflowName": name}
                for key, value in args.items():
                    req[camel(key)] = json.loads(value) if key in ("identifier", "grades_in_room") else value
                tool, _ = await c.call("get_workflow_instructions", {"request": req})
                assert isinstance(tool, dict), (name, tool)
                assert tool["rendered"]["message"] == text, name
                assert "EVIDENCE ACCESS" in text and "EVIDENCE LINKS" in text
                assert native.meta["promptVersion"] == "1.4.0"
                ev["prompts"][name] = sha(text)
                assert "page of 25" not in text and '"connectionKind": "all"' not in text, name
                if name in ("learning_progression_teaching_sequence", "teacher_guide_draft",
                            "student_study_support", "student_handbook_section", "multigrade_lesson_plan"):
                    assert all(f"- {k}:" in text for k in ("outgoing_builds", "incoming_builds", "related")), name
            need("docs/reference/prompts.md", "All prompts are registered at prompt version `1.4.0`.")
            need("docs/guides/prompts.md", "version is `1.4.0`.")

    # Stale rework wording is absent from maintained documentation.
    stale = ["one page of 25", "pages of 25", "at most 75", "equal-sized parts", "one direct page of 25",
             # Development history and internal process terms do not belong in public docs.
             "rebuilt", "first 0.4.0", "first build", "rework", "this release", "fixed in 0.4.0",
             "Version 0.4.0 fixes", "used to list", "obsolete candidate-collection",
             "size-limited", "maximum requested", "requested maximum", "own budget"]
    files = [ROOT / "README.md", ROOT / "backend/README.md", ROOT / "packaging/mcpb/README.md",
             *sorted((ROOT / "docs").rglob("*.md"))]
    for path in files:
        text = path.read_text()
        for phrase in stale:
            assert phrase not in text, (path, phrase)
    # Shipped README in the retained candidate equals the working backend README.
    with zipfile.ZipFile(CANDIDATE) as archive:
        shipped = archive.read("README.md")
    assert shipped == (ROOT / "backend/README.md").read_bytes()
    ev["candidate"] = {"sha256": sha(CANDIDATE.read_bytes()), "readmeSha256": sha(shipped)}

    # Catalog table still agrees with manifests (reused parsing approach).
    catalog = doc("docs/data/framework-catalog.md")
    manifests = sorted((ROOT / "data/graph_packages").glob("*/*/package_manifest.json"))
    assert len(manifests) == 6
    for path in manifests:
        assert json.loads(path.read_text())["snapshotId"] in catalog
    need("docs/data/prompt-configs.md", "always registers the nine generic prompts")

    # Rendered site: new pages present, local links and anchors resolve.
    class Markup(HTMLParser):
        """Collect IDs and local links from generated HTML."""
        def __init__(self, text):
            super().__init__()
            self.ids, self.links = set(), []
            self.feed(text)

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if "id" in attrs:
                self.ids.add(attrs["id"])
            if tag == "a" and "href" in attrs:
                self.links.append(attrs["href"])

    pages = {p: Markup(p.read_text()) for p in SITE.rglob("*.html")}
    for required in ["getting-started/claude-clients.html", "reference/access-tools.html"]:
        assert SITE / required in pages, required
    checked = 0
    for page_path, parsed in pages.items():
        for href in parsed.links:
            url = urlsplit(href)
            if url.scheme or url.netloc:
                continue
            target = ((SITE / unquote(url.path.removeprefix("/KGForEdGlobalMCP/"))).resolve()
                      if url.path.startswith("/KGForEdGlobalMCP/") else
                      (page_path.parent / unquote(url.path)).resolve() if url.path else page_path)
            if target.is_dir():
                target /= "index.html"
            assert target.exists(), (page_path, href)
            if url.fragment and target in pages:
                assert unquote(url.fragment) in pages[target].ids, (page_path, href)
            checked += 1
    ev["renderedPages"] = len(pages)
    ev["renderedLocalLinks"] = checked
    ev["toolCalls"] = c.calls
    ev["savedPageSha256"] = {p: sha((ROOT / p).read_bytes()) for p in [
        "docs/getting-started/claude-clients.md", "docs/reference/access-tools.md",
        "docs/guides/progression.md", "docs/reference/progression-tool.md",
        "docs/guides/framework-discovery.md", "docs/reference/framework-tools.md",
        "docs/reference/learning-component-tools.md", "docs/reference/prompts.md",
        "docs/guides/prompts.md"]}
    ev["status"] = "passed"
    OUT.write_text(json.dumps(ev, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "passed", "toolCalls": c.calls, "renderedPages": len(pages),
                      "renderedLocalLinks": checked, "access": ev["access"],
                      "receiptSha256": sha(OUT.read_bytes())}))


if __name__ == "__main__":
    with patch.object(socket.socket, "connect", side_effect=AssertionError("Network forbidden")):
        asyncio.run(check())
