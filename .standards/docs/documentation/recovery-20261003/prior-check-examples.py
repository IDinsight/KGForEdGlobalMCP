"""Check saved documentation examples and rendered facts without model calls.

This is Documenter evidence, not Tester-owned acceptance coverage.
Run with the existing locked backend environment and an absolute script path.
"""
import asyncio
import base64
import hashlib
import json
import re
import socket
from pathlib import Path
from unittest.mock import patch

from fastmcp import Client
from kgfegmcp.app import create_mcp
from kgfegmcp.bootstrap import bootstrap_application

ROOT = Path(__file__).resolve().parents[3]
CYCLE = "integrate-actual-learning-progressions-20261001T162834Z-142f2df1"
OUT = ROOT / ".standards/docs/documentation" / (CYCLE + "-example-results.json")


def sha(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


async def check():
    """Execute saved guide inputs against the actual local MCP adapters."""
    state = bootstrap_application()
    guide = ROOT / "docs/guides/progression.md"
    examples = re.findall(r"```json\n(.*?)\n```", guide.read_text(), re.S)
    assert len(examples) == 5
    names = ["search_learning_progressions", "get_learning_progression",
             "get_standard_progressions", "traverse_learning_progressions",
             "get_learning_progression_paths"]
    evidence = {"guideSha256": sha(guide), "tools": [], "prompts": [],
                "resources": [], "catalog": []}
    with patch("kgfegmcp.app.bootstrap_application", return_value=state):
        async with Client(create_mcp()) as client:
            tools = await client.list_tools()
            prompts = await client.list_prompts()
            templates = await client.list_resource_templates()
            fixed = await client.list_resources()
            assert (len(tools), len(prompts), len(templates), len(fixed)) == (17, 9, 14, 1)
            evidence["inventory"] = {"tools": sorted(t.name for t in tools),
                                      "prompts": sorted(p.name for p in prompts),
                                      "templates": sorted(t.name for t in templates)}
            replacements = {}
            for name, text in zip(names, examples):
                for key, value in replacements.items():
                    text = text.replace(key, value)
                args = json.loads(text)
                result = await client.call_tool(name, args)
                assert not result.is_error
                data = result.structured_content
                if name == names[0]:
                    row = data["relationships"][0]
                    edge = row["relationship"]
                    identity = data["metadata"]["package"]["packageIdentity"]
                    replacements = {"<returned-snapshot-id>": identity["snapshotId"],
                                    "<returned-relationship-id>": edge["relationshipId"],
                                    "<returned-source-node-id>": edge["sourceNodeId"],
                                    "<returned-target-node-id>": edge["targetNodeId"]}
                evidence["tools"].append({"name": name, "arguments": args,
                                          "relationships": len(data["relationships"]),
                                          "resultSha256": "sha256:" + hashlib.sha256(
                                              json.dumps(data, sort_keys=True).encode()).hexdigest()})
            for uri in [row["relationshipUri"], row["provenanceUri"],
                        data["metadata"]["summaryUri"], data["metadata"]["validationUri"],
                        data["metadata"]["unresolvedUri"]]:
                result = await client.read_resource(uri)
                assert result
                evidence["resources"].append({"uri": uri, "contentSha256": "sha256:" +
                    hashlib.sha256(result[0].text.encode() if hasattr(result[0], "text")
                                   else base64.b64decode(result[0].blob)).hexdigest()})
            route = {"framework_id": "nigeria-nerdc-mathematics-primary-1-3", "output_language": "en"}
            cases = [
                ("learning_progression_teaching_sequence", {**route, "focus_mode": "topic",
                 "topic_or_standard": "fractions", "local_grade_labels":
                 '["PRIMARY ONE", "PRIMARY TWO", "PRIMARY THREE"]'}),
                ("learning_progression_support_plan", {**route, "identifier": json.dumps(
                 {"identifierType": "node_id", "nodeId": edge["targetNodeId"]}),
                 "local_context": "Learners explain the whole but confuse equal-sized parts."}),
                ("learning_progression_curriculum_review", {**route,
                 "local_grade_labels": '["PRIMARY ONE"]', "endpoint_scope": "either"})]
            for name, args in cases:
                result = await client.get_prompt(name, args)
                assert result.meta["promptVersion"] == "1.3.0"
                message = result.messages[0].content.text
                assert "[LLM-INFERRED / GENERATED]" in message
                assert identity["snapshotId"] in message
                evidence["prompts"].append({"name": name, "arguments": args,
                   "messageSha256": "sha256:" + hashlib.sha256(message.encode()).hexdigest()})

    # Independently compare each displayed row to the current manifest, not just totals.
    catalog = (ROOT / "docs/data/framework-catalog.md").read_text()
    table = catalog.split("## Catalog summary", 1)[1].split("Across the six manifests", 1)[0]
    rows = [line for line in table.splitlines() if line.startswith("| ")][2:8]
    manifests = sorted((ROOT / "data/graph_packages").glob("*/*/package_manifest.json"))
    assert len(rows) == len(manifests) == 6
    expected_labels = ["Ghana English Language", "Ghana Mathematics", "CBSE Science",
                       "Tamil Nadu Mathematics", "Nigeria Mathematics", "Rwanda Mathematics"]
    for row, path, label in zip(rows, manifests, expected_labels):
        m = json.loads(path.read_text())
        cells = [v.strip() for v in row.strip("|").split("|")]
        assert cells[0] == label
        c = m["counts"]
        expected = [c["itemNodes"], c["relationships"] - c["supportsRelationships"] -
                    c["buildsTowardsRelationships"] - c["relatesToRelationships"],
                    c["learningComponentNodes"], c["supportsRelationships"],
                    c["buildsTowardsRelationships"], c["relatesToRelationships"], c["relationships"]]
        assert [int(v) for v in cells[7:]] == expected
        assert m["snapshotId"] in catalog
        assert m["manifestVersion"] == "1.1" and m["deliverySchemaVersion"] == "1.2"
        evidence["catalog"].append({"frameworkId": m["frameworkId"], "snapshotId": m["snapshotId"],
                                    "manifestSha256": sha(path), "rowVerified": True})
    # Inspect generated HTML table/section structure without altering source assets.
    from html.parser import HTMLParser
    from urllib.parse import unquote, urlsplit

    class Markup(HTMLParser):
        """Collect local links, IDs and table row counts from generated HTML."""
        def __init__(self, text):
            super().__init__()
            self.ids = set()
            self.links = []
            self.tables = []
            self.current = None
            self.tbody = False
            self.feed(text)

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if "id" in attrs:
                self.ids.add(attrs["id"])
            if tag == "a" and "href" in attrs:
                self.links.append(attrs["href"])
            if tag == "table":
                self.current = {"text": "", "rows": 0}
            if tag == "tbody":
                self.tbody = True
            if tag == "tr" and self.current is not None and self.tbody:
                self.current["rows"] += 1

        def handle_endtag(self, tag):
            if tag == "tbody":
                self.tbody = False
            if tag == "table" and self.current is not None:
                self.tables.append(self.current)
                self.current = None

        def handle_data(self, value):
            if self.current is not None:
                self.current["text"] += value

    site = Path("/tmp/kgfegmcp-documenter-site").resolve()
    pages = {p: Markup(p.read_text()) for p in site.rglob("*.html")}
    table = next(t for t in pages[site / "reference/resources.html"].tables
                 if "URI template" in t["text"])
    assert table["rows"] == 14
    checked_links = 0
    for page, parsed in pages.items():
        for href in parsed.links:
            url = urlsplit(href)
            if url.scheme or url.netloc:
                continue
            target = ((site / unquote(url.path.removeprefix("/KGForEdGlobalMCP/"))).resolve()
                      if url.path.startswith("/KGForEdGlobalMCP/") else
                      (page.parent / unquote(url.path)).resolve() if url.path else page)
            if target.is_dir():
                target /= "index.html"
            assert target.exists(), (page, href, "missing local target")
            if url.fragment and target in pages:
                assert unquote(url.fragment) in pages[target].ids, (page, href, "missing anchor")
            checked_links += 1
    evidence["renderedLocalLinks"] = checked_links
    evidence["renderedPages"] = len(pages)
    evidence["renderedResourceTemplateRows"] = 14
    evidence["status"] = "passed"
    OUT.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "passed", "toolExamples": 5, "promptExamples": 3,
                      "resourceReads": 5, "catalogRows": 6, "renderedResourceTemplateRows": 14,
                      "receipt": str(OUT), "receiptSha256": sha(OUT)}))


if __name__ == "__main__":
    with patch.object(socket.socket, "connect", side_effect=AssertionError("Network forbidden")):
        asyncio.run(check())
