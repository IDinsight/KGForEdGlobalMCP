"""Reviewer diagnostic for the client-access rework (AC-028..AC-031, AC-033/034).

Independent supporting evidence for IMPLEMENTATION review, not formal Tester
verification. It drives the real ``create_mcp`` application through an in-memory
FastMCP client with network connections blocked; no model or paid service is used.

Checks (each records actual observations in the JSON printed to stdout):

1. Inventory: 19 tools, 9 prompts, 1 fixed resource, 14 templates.
2. Text-only consumption: every successful tool call's ordinary text block parses to
   exactly its structuredContent; the actual wire CallToolResult (compact JSON) and the
   conservative (default-separator) serialization both stay within 1 MiB and 100,000
   code points.
3. Full discovery replay through text nextRequest for all six packages at limit 100,
   compared with an independent oracle of stored LP edges (no loss, no duplicates).
4. Full direct-connection replay for the highest-degree standard of each package,
   compared with an independent incoming/outgoing/relates oracle.
5. Traversal at maximum bounds and paths at maximum bounds for the longest real
   shortest-path pair of each package: hops are stored buildsTowards edges in the
   stored direction; paths are contiguous, ordered and within ceilings.
6. Every kgfegmcp:// URI returned by LP results is usable by read_evidence (readable
   or explicitly denied; never invalid_evidence_uri/internal_error).
7. Full text-only reads of diagnostic evidence equal native resources/read bytes.
8. Adversarial URIs and tampered cursors fail with stable typed codes.
9. get_workflow_instructions equals native prompt messages for array-bearing inputs;
   unaffected/unknown workflows are rejected.

Usage (repository root, offline locked environment)::

    uv --directory backend run --locked --offline --no-sync python \
        ../.standards/docs/reviews/<cycle>/check-client-access-review.py
"""

# Standard Library
import asyncio
import base64
import hashlib
import json
import socket
import sys
import time

from collections import Counter, defaultdict, deque
from typing import Any
from urllib.parse import quote

# Third Party Library
from fastmcp import Client

# Package Library
from kgfegmcp.app import create_mcp
from kgfegmcp.bootstrap import bootstrap_application

MAX_BYTES = 1_048_576
MAX_CHARS = 100_000
LP_LABELS = {"buildsTowards", "relatesTo"}
NIGERIA = "nigeria-nerdc-mathematics-primary-1-3"
NIGERIA_SNAPSHOT = "nigeria-nerdc-mathematics-primary-1-3@undated+bc5e769ed26f"
EDGE = "0129f5d5-42fd-52cb-bcf2-ec07c47103e7"
TARGET = "e399b510-48bb-58ee-abda-61460a5a853b"


def _block_network() -> None:
    """Reject any socket connection attempted by the diagnostic."""

    def reject(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("network connection attempted")

    socket.socket.connect = reject  # type: ignore[method-assign]
    socket.socket.connect_ex = reject  # type: ignore[method-assign]


class Recorder:
    """Accumulate failures, maxima and counters."""

    def __init__(self) -> None:
        self.failures: list[str] = []
        self.calls: Counter[str] = Counter()
        self.max_wire: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        self.max_conservative: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        self.uris: set[str] = set()

    def check(self, condition: bool, label: str) -> None:
        if not condition:
            self.failures.append(label)


REC = Recorder()


def _collect_uris(value: Any) -> None:
    """Gather every kgfegmcp URI string from a payload."""
    if isinstance(value, str) and value.startswith("kgfegmcp://"):
        REC.uris.add(value)
    elif isinstance(value, dict):
        for item in value.values():
            _collect_uris(item)
    elif isinstance(value, list):
        for item in value:
            _collect_uris(item)


async def call(client: Client, name: str, request: dict[str, Any]) -> dict[str, Any]:
    """Call a tool; return parsed text for success or {'error': text} for failure."""
    REC.calls[name] += 1
    raw = await client.call_tool_mcp(name, {"request": request})
    text = raw.content[0].text if raw.content else ""
    if raw.isError:
        return {"error": text}
    wire = raw.model_dump_json(by_alias=True, exclude_none=True)
    conservative = json.dumps(
        raw.model_dump(by_alias=True, exclude_none=True, mode="json"),
        ensure_ascii=False,
        sort_keys=True,
    )
    for store, serialized in ((REC.max_wire, wire), (REC.max_conservative, conservative)):
        size = store[name]
        size[0] = max(size[0], len(serialized.encode("utf-8")))
        size[1] = max(size[1], len(serialized))
    REC.check(
        len(conservative) <= MAX_CHARS and len(conservative.encode()) <= MAX_BYTES,
        f"{name}: envelope over ceiling ({len(conservative)} chars)",
    )
    REC.check(len(raw.content) == 1, f"{name}: expected one text block")
    payload = json.loads(text)
    REC.check(payload == raw.structuredContent, f"{name}: text != structuredContent")
    _collect_uris(payload)
    return payload


def lp_edges(runtime: Any) -> list[Any]:
    """Independent oracle: stored LP edges straight from the accepted package."""
    return [e for e in runtime.loaded_package.relationships if e.label in LP_LABELS]


def node_selector(node_id: str) -> dict[str, str]:
    return {"identifierType": "node_id", "nodeId": node_id}


async def replay(
    client: Client, name: str, request: dict[str, Any], bound: int
) -> tuple[list[str], int, Counter[str]]:
    """Follow text nextRequest until complete; forbid loops beyond the bound."""
    found: list[str] = []
    reasons: Counter[str] = Counter()
    pages = 0
    while True:
        pages += 1
        payload = await call(client, name, request)
        if "error" in payload:
            REC.failures.append(f"{name} replay error: {payload['error'][:200]}")
            break
        page = payload["page"]
        reasons[page["stoppingReason"] or "none"] += 1
        found.extend(e["relationship"]["relationshipId"] for e in payload["relationships"])
        REC.check(
            page["isComplete"] == (page["nextCursor"] is None),
            f"{name}: isComplete/nextCursor mismatch",
        )
        if page["nextCursor"] is None:
            REC.check(page["nextRequest"] is None, f"{name}: stray nextRequest")
            break
        REC.check(
            page["nextRequest"]["cursor"] == page["nextCursor"],
            f"{name}: nextRequest cursor differs",
        )
        REC.check(
            bool(payload["relationships"]) or page["examinedCount"] > 0,
            f"{name}: zero-progress page",
        )
        request = page["nextRequest"]
        if pages > bound:
            REC.failures.append(f"{name}: replay exceeded bound {bound}")
            break
    return found, pages, reasons


def shortest_longest_pair(edges: list[Any]) -> tuple[str, str, int]:
    """Find a connected ordered pair with the longest shortest builds path."""
    adjacency: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        if edge.label == "buildsTowards":
            adjacency[edge.source_node_id].append(edge.target_node_id)
    best = ("", "", 0)
    for source in sorted(adjacency):
        distance = {source: 0}
        queue = deque([source])
        while queue:
            current = queue.popleft()
            for nxt in adjacency.get(current, ()):
                if nxt not in distance:
                    distance[nxt] = distance[current] + 1
                    queue.append(nxt)
        for target, hops in sorted(distance.items()):
            if hops > best[2]:
                best = (source, target, hops)
    return best


async def main() -> dict[str, Any]:
    _block_network()
    state = bootstrap_application()
    runtimes = {
        str(r.catalog_package.package_identity.framework_id): r
        for r in state.catalog_load_result.package_runtimes
    }
    out: dict[str, Any] = {"packages": {}}
    import kgfegmcp.app as app_module

    app_module.bootstrap_application = lambda: state  # reuse the bootstrapped state
    async with Client(create_mcp()) as client:
        tools = await client.list_tools()
        prompts = await client.list_prompts()
        resources = await client.list_resources()
        templates = await client.list_resource_templates()
        out["inventory"] = [len(tools), len(prompts), len(resources), len(templates)]
        REC.check(out["inventory"] == [19, 9, 1, 14], "inventory mismatch")

        # Exact diagnostic edge, text only.
        route = {"frameworkId": NIGERIA, "snapshotId": NIGERIA_SNAPSHOT}
        exact = await call(
            client, "get_learning_progression", {**route, "relationshipId": EDGE}
        )
        edge = exact["relationships"][0]
        out["exact"] = {
            "label": edge["relationship"]["label"],
            "endpoints": [
                edge["relationship"]["sourceNodeId"],
                edge["relationship"]["targetNodeId"],
            ],
            "confidence": edge["judgment"]["confidence"],
            "warningCount": edge["judgment"]["warningCount"],
            "nodeStatementsPresent": all(n["statementExcerpt"] for n in exact["nodes"]),
            "noContinuationNotice": "No continuation" in exact["continuationNotice"],
            "artifacts": [a["logicalName"] for a in exact["metadata"]["artifacts"]],
        }
        REC.check(out["exact"]["noContinuationNotice"], "exact lacks no-continuation")

        for framework, runtime in sorted(runtimes.items()):
            identity = runtime.catalog_package.package_identity
            route = {"frameworkId": framework, "snapshotId": str(identity.snapshot_id)}
            edges = lp_edges(runtime)
            oracle = {e.relationship_id for e in edges}
            record: dict[str, Any] = {"storedEdges": len(edges)}
            started = time.monotonic()

            # 3. Full discovery replay at the maximum page limit.
            found, pages, reasons = await replay(
                client,
                "search_learning_progressions",
                {**route, "limit": 100},
                bound=len(edges) + 5,
            )
            record["discovery"] = {
                "pages": pages,
                "returned": len(found),
                "unique": len(set(found)),
                "equalsOracle": set(found) == oracle,
                "stoppingReasons": dict(reasons),
                "seconds": round(time.monotonic() - started, 1),
            }
            REC.check(len(found) == len(set(found)), f"{framework}: discovery dup")
            REC.check(set(found) == oracle, f"{framework}: discovery != oracle")

            # 4. Direct replay for the highest-degree standard.
            degree: Counter[str] = Counter()
            for e in edges:
                degree[e.source_node_id] += 1
                degree[e.target_node_id] += 1
            hub, hub_degree = sorted(degree.items(), key=lambda kv: (-kv[1], kv[0]))[0]
            direct_oracle = {
                e.relationship_id
                for e in edges
                if hub in (e.source_node_id, e.target_node_id)
            }
            found, pages, reasons = await replay(
                client,
                "get_standard_progressions",
                {**route, "identifier": node_selector(hub), "limit": 100},
                bound=hub_degree + 5,
            )
            record["direct"] = {
                "hub": hub,
                "degree": hub_degree,
                "pages": pages,
                "equalsOracle": set(found) == direct_oracle
                and len(found) == len(direct_oracle),
                "stoppingReasons": dict(reasons),
            }
            REC.check(record["direct"]["equalsOracle"], f"{framework}: direct != oracle")

            # 5a. Traversal at maximum bounds from the highest out-degree node.
            stored = {e.relationship_id: e for e in edges}
            out_degree = Counter(
                e.source_node_id for e in edges if e.label == "buildsTowards"
            )
            origin = sorted(out_degree.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
            traversal = {}
            for direction in ("downstream", "upstream"):
                payload = await call(
                    client,
                    "traverse_learning_progressions",
                    {
                        **route,
                        "direction": direction,
                        "identifier": node_selector(origin),
                        "maxDepth": 12,
                        "maxEdges": 100,
                        "maxNodes": 250,
                    },
                )
                ok = all(
                    item["relationship"]["label"] == "buildsTowards"
                    and stored[item["relationship"]["relationshipId"]].source_node_id
                    == item["relationship"]["sourceNodeId"]
                    for item in payload["relationships"]
                )
                REC.check(ok, f"{framework}: traversal hop not stored builds")
                traversal[direction] = {
                    "edges": len(payload["relationships"]),
                    "truncation": payload["truncationReasons"],
                    "scopeComplete": payload["scopeComplete"],
                }
            record["traversal"] = traversal

            # 5b. Paths at maximum bounds for the longest real shortest pair.
            source, target, hops = shortest_longest_pair(edges)
            payload = await call(
                client,
                "get_learning_progression_paths",
                {
                    **route,
                    "maxDepth": 12,
                    "maxPaths": 20,
                    "sourceIdentifier": node_selector(source),
                    "targetIdentifier": node_selector(target),
                },
            )
            if "error" in payload:
                record["paths"] = {"hops": hops, "error": payload["error"][:300]}
                REC.failures.append(f"{framework}: paths error")
            else:
                table = {
                    i["relationship"]["relationshipId"]: i["relationship"]
                    for i in payload["relationships"]
                }
                lengths = [len(p["relationshipIds"]) for p in payload["paths"]]
                contiguous = True
                for path in payload["paths"]:
                    chain = [table[r] for r in path["relationshipIds"]]
                    contiguous &= chain[0]["sourceNodeId"] == source
                    contiguous &= chain[-1]["targetNodeId"] == target
                    contiguous &= all(
                        a["targetNodeId"] == b["sourceNodeId"]
                        for a, b in zip(chain, chain[1:])
                    )
                    contiguous &= all(c["label"] == "buildsTowards" for c in chain)
                stop = payload["nextUnreturnedPath"]
                REC.check(contiguous, f"{framework}: noncontiguous path")
                REC.check(lengths == sorted(lengths), f"{framework}: path order")
                REC.check(
                    bool(lengths) and lengths[0] == hops, f"{framework}: shortest missing"
                )
                REC.check(
                    (stop is not None) == ("byte_limit" in payload["truncationReasons"])
                    or "byte_limit" not in payload["truncationReasons"],
                    f"{framework}: nextUnreturnedPath/byte_limit mismatch",
                )
                if stop is not None:
                    REC.check(
                        not set(stop["relationshipIds"]) <= set(table)
                        or stop["relationshipIds"] not in [
                            p["relationshipIds"] for p in payload["paths"]
                        ],
                        f"{framework}: stopped path was returned",
                    )
                record["paths"] = {
                    "shortestHops": hops,
                    "returnedPathLengths": lengths,
                    "truncation": payload["truncationReasons"],
                    "nextUnreturnedPath": stop is not None,
                }

            # Complete empty result: an exact standard with no stored LP edge.
            isolated = next(
                (
                    n.node_id
                    for n in runtime.loaded_package.item_nodes
                    if n.node_id not in degree
                ),
                None,
            )
            if isolated is not None:
                payload = await call(
                    client,
                    "get_standard_progressions",
                    {**route, "identifier": node_selector(isolated)},
                )
                record["emptyComplete"] = (
                    not payload["relationships"]
                    and payload["page"]["isComplete"]
                    and payload["page"]["nextCursor"] is None
                )
                REC.check(record["emptyComplete"], f"{framework}: empty not complete")
            out["packages"][framework] = record
            PARTIAL[framework] = record

        # 6. URI usability through read_evidence (first window only).
        outcomes: Counter[str] = Counter()
        kinds: dict[str, Counter[str]] = defaultdict(Counter)
        for uri in sorted(REC.uris):
            payload = await call(client, "read_evidence", {"uri": uri})
            outcome = (
                payload["error"].split(":", 1)[0] if "error" in payload else "readable"
            )
            outcomes[outcome] += 1
            tail = uri.rsplit("/snapshot/", 1)[-1].split("/")
            kind = "/".join(p for i, p in enumerate(tail) if i in (1, 3)) or tail[0]
            kinds[kind][outcome] += 1
        out["uriUsability"] = {
            "uniqueUris": len(REC.uris),
            "outcomes": dict(outcomes),
            "byKind": {k: dict(v) for k, v in sorted(kinds.items())},
        }
        REC.check(
            not ({"invalid_evidence_uri", "internal_error"} & set(outcomes)),
            "returned URI not usable by read_evidence",
        )

        # 7. Full text-only reads equal native resource bytes.
        async def full_read(uri: str) -> dict[str, Any]:
            request: dict[str, Any] | None = {"maxContentBytes": 4096, "uri": uri}
            chunks: list[str] = []
            metadata: dict[str, Any] = {}
            windows = 0
            while request is not None:
                payload = await call(client, "read_evidence", request)
                if "error" in payload:
                    return {"error": payload["error"].split(":", 1)[0]}
                windows += 1
                chunks.append(payload["content"])
                metadata = payload["metadata"]
                request = payload["page"]["nextRequest"]
            content = "".join(chunks)
            native = (await client.read_resource(metadata["canonicalUri"]))[0]
            # Raw source artifacts arrive as base64 blobs, derived documents as text.
            blob = getattr(native, "blob", None)
            native_bytes = (
                base64.b64decode(blob) if blob is not None else native.text.encode()
            )
            digest = "sha256:" + hashlib.sha256(content.encode()).hexdigest()
            REC.check(
                content.encode() == native_bytes, f"full read differs from native: {uri}"
            )
            REC.check(digest == metadata["contentSha256"], f"hash mismatch: {uri}")
            return {"windows": windows, "bytes": len(content.encode()), "content": content}

        base = f"kgfegmcp://framework/{NIGERIA}/snapshot/{quote(NIGERIA_SNAPSHOT, safe='')}"
        reads: dict[str, Any] = {}
        provenance = await full_read(f"{base}/relationship/{EDGE}/provenance")
        record_json = json.loads(provenance["content"])
        flat = json.dumps(record_json)
        reads["edgeProvenance"] = {
            "windows": provenance["windows"],
            "bytes": provenance["bytes"],
            "topKeys": sorted(record_json)[:20],
            "mentions": {
                key: key in flat
                for key in ("rationale", "warnings", "confidence", "checker", "producer")
            },
        }
        for label, path in (
            ("targetStandard", f"/standard/{TARGET}"),
            ("targetProvenance", f"/standard/{TARGET}/provenance"),
            ("targetComponents", f"/standard/{TARGET}/learning-components"),
            ("validation", "/validation"),
            ("unresolved", "/unresolved"),
            ("lpSummary", "/learning-progressions"),
            ("manifest", "/manifest"),
        ):
            result = await full_read(base + path)
            reads[label] = {k: v for k, v in result.items() if k != "content"}
            if label == "targetComponents" and "content" in result:
                listed = json.loads(result["content"])
                text = json.dumps(listed)
                component = next(
                    (
                        n.node_id
                        for n in runtimes[
                            NIGERIA
                        ].loaded_package.learning_component_nodes
                        if n.node_id in text
                    ),
                    None,
                )
                reads["componentFound"] = component is not None
                REC.check(component is not None, "no supporting LC found")
                if component:
                    for suffix in ("", "/provenance"):
                        lc = await full_read(f"{base}/learning-component/{component}{suffix}")
                        reads[f"component{suffix or ''}"] = {
                            k: v for k, v in lc.items() if k != "content"
                        }
        cbse = runtimes["india-cbse-science-learning-framework-classes-9-10"]
        cbse_base = (
            "kgfegmcp://framework/india-cbse-science-learning-framework-classes-9-10/"
            f"snapshot/{quote(str(cbse.catalog_package.package_identity.snapshot_id), safe='')}"
        )
        summary = await full_read(cbse_base + "/learning-progressions")
        reads["cbseSummaryNeedsReview"] = "needsReview" in summary.get("content", "")
        out["fullReads"] = reads

        # 8. Adversarial URIs and tampered cursors.
        snap = quote(NIGERIA_SNAPSHOT, safe="")
        adversarial = [
            "KGFEGMCP://catalog",
            "kgfegmcp://catalog/",
            "kgfegmcp:///catalog",
            "kgfegmcp://framework//snapshot/x/manifest",
            f"kgfegmcp://framework/{NIGERIA}/snapshot/{snap}/manifest/",
            f"kgfegmcp://framework/{NIGERIA}/snapshot/{snap}//manifest",
            f"kgfegmcp://framework/{NIGERIA}/snapshot/{snap}/artifact/%2e%2e",
            f"kgfegmcp://framework/{NIGERIA}/snapshot/{snap}/artifact/..%2Fmanifest",
            f"kgfegmcp://framework/{NIGERIA}/snapshot/{snap}/artifact/a%5Cb",
            f"kgfegmcp://framework/{NIGERIA}/snapshot/{snap}/standard/{TARGET}/extra",
            f"kgfegmcp://framework/{NIGERIA}/snapshot/{snap}/standard/{TARGET}%00",
            f"kgfegmcp://framework/{NIGERIA}/snapshot/{snap}/relationship/%FF",
            f"kgfegmcp://framework/{NIGERIA}:443/snapshot/{snap}/manifest",
            f"kgfegmcp://user@framework/{NIGERIA}/snapshot/{snap}/manifest",
            f"kgfegmcp://framework/{NIGERIA}/snapshot/{snap}/manifest?x=1",
            "file:///etc/passwd",
            f"kgfegmcp://framework/{NIGERIA}/snapshot/{snap}/artifact/%252e%252e",
        ]
        adversarial_out = {}
        for uri in adversarial:
            payload = await call(client, "read_evidence", {"uri": uri})
            code = payload["error"].split(":", 1)[0] if "error" in payload else "READ"
            adversarial_out[uri] = code
            REC.check(code in {"invalid_evidence_uri", "resource_not_found",
                               "framework_not_found"}, f"adversarial accepted: {uri}")
        out["adversarialUris"] = adversarial_out
        # Noncanonical but valid escape normalizes to the canonical URI.
        spelled = f"kgfegmcp://framework/%6E{NIGERIA[1:]}/snapshot/{snap}/manifest"
        payload = await call(client, "read_evidence", {"uri": spelled})
        out["noncanonicalCanonicalized"] = (
            "error" not in payload
            and payload["metadata"]["canonicalUri"] == f"{base}/manifest"
        )
        REC.check(out["noncanonicalCanonicalized"], "noncanonical spelling")
        # Bulk original provenance map stays denied through read_evidence.
        payload = await call(
            client,
            "read_evidence",
            {"uri": f"{base}/artifact/learningProgressionProvenance"},
        )
        out["bulkDenied"] = payload.get("error", "READ").split(":", 1)[0]
        REC.check(out["bulkDenied"] == "resource_access_denied", "bulk not denied")
        # Cursor tampering.
        first = await call(
            client,
            "read_evidence",
            {"maxContentBytes": 1024, "uri": f"{base}/relationship/{EDGE}/provenance"},
        )
        cursor = first["page"]["nextCursor"]
        raw = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
        raw["position"] = raw["position"] + 1
        forged = base64.urlsafe_b64encode(
            json.dumps(raw, separators=(",", ":"), sort_keys=True).encode()
        ).decode().rstrip("=")
        tamper = {
            "forgedPosition": {"cursor": forged, "maxContentBytes": 1024,
                               "uri": f"{base}/relationship/{EDGE}/provenance"},
            "otherSize": {"cursor": cursor, "maxContentBytes": 2048,
                          "uri": f"{base}/relationship/{EDGE}/provenance"},
            "otherUri": {"cursor": cursor, "maxContentBytes": 1024,
                         "uri": f"{base}/standard/{TARGET}/provenance"},
        }
        tamper_out = {}
        for label, request in tamper.items():
            payload = await call(client, "read_evidence", request)
            tamper_out[label] = payload.get("error", "READ").split(":", 1)[0]
            REC.check(tamper_out[label] == "invalid_cursor", f"cursor tamper {label}")
        # LP cursor replay with altered limit.
        page = await call(client, "search_learning_progressions",
                          {"frameworkId": NIGERIA, "limit": 5})
        altered = {**page["page"]["nextRequest"], "limit": 6}
        payload = await call(client, "search_learning_progressions", altered)
        tamper_out["lpAlteredLimit"] = payload.get("error", "READ").split(":", 1)[0]
        REC.check(tamper_out["lpAlteredLimit"] == "invalid_cursor", "LP cursor limit")
        out["cursorTamper"] = tamper_out

        # 9. Workflow parity for array-bearing inputs and rejected variants.
        nigeria = runtimes[NIGERIA]
        grades = [g.local_label for g in nigeria.loaded_package.profile.grade_mappings]
        selectors = [node_selector(TARGET)]
        cases = {
            "learning_progression_curriculum_review": {
                "endpoint_scope": "both",
                "local_grade_labels": grades[:2],
                "standard_identifiers": selectors,
            },
            "multigrade_lesson_plan": {
                "grades_in_room": grades[:2],
                "topic_or_standard": "addition",
            },
            "learning_progression_support_plan": {
                "identifier": node_selector(TARGET),
                "local_context": "Learners count on fingers; ünïcode note.",
            },
        }
        parity = {}
        for name, specific in cases.items():
            values = {"framework_id": NIGERIA, "snapshot_id": NIGERIA_SNAPSHOT, **specific}
            native_args = {
                k: v if isinstance(v, str) else json.dumps(v) for k, v in values.items()
            }
            camel = {
                "".join(p.capitalize() if i else p for i, p in enumerate(k.split("_"))): v
                for k, v in values.items()
            }
            native = await client.get_prompt(name, native_args)
            tool = await call(
                client, "get_workflow_instructions", {**camel, "workflowName": name}
            )
            same = (
                "error" not in tool
                and tool["rendered"]["message"] == native.messages[0].content.text
            )
            parity[name] = same
            REC.check(same, f"workflow parity {name}")
        for name in ("administrator_alignment_review", "cross_framework_comparison",
                     "inferred_progression_hypothesis"):
            try:
                result = await client.call_tool_mcp(
                    "get_workflow_instructions",
                    {"request": {"frameworkId": NIGERIA, "workflowName": name}},
                )
                parity[f"rejected:{name}"] = bool(result.isError)
            except Exception:  # validation errors may raise before a result
                parity[f"rejected:{name}"] = True
            REC.check(parity[f"rejected:{name}"], f"workflow {name} accepted")
        out["workflowParity"] = parity

    out["calls"] = dict(REC.calls)
    out["maxWireBytesChars"] = {k: v for k, v in sorted(REC.max_wire.items())}
    out["maxConservativeBytesChars"] = {
        k: v for k, v in sorted(REC.max_conservative.items())
    }
    out["failures"] = REC.failures
    return out


PARTIAL: dict[str, Any] = {}


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
    except Exception as error:  # report harness/runtime failure with partial data
        result = {
            "exception": f"{type(error).__name__}: {error}",
            "failures": [*REC.failures, "diagnostic raised"],
            "partial": PARTIAL,
        }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    sys.exit(1 if result["failures"] else 0)
