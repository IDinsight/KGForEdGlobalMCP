"""Reviewer recheck of F-001/F-002: AS/LC evidence links from client-visible text.

Independent supporting evidence for IMPLEMENTATION review, not formal Tester
verification. Drives the real ``create_mcp`` app through an in-memory FastMCP client
with network connections blocked; no model or paid service is used.

For every accepted package and all seven affected workflows it:

1. renders the workflow through ``get_workflow_instructions`` and the native prompt,
   requiring identical messages, an EVIDENCE LINKS block identical across the seven
   workflows, and both size ceilings;
2. reads a standard's Node ID from ``get_standard`` text and a supporting
   learning-component ID from ``get_learning_components_for_standard`` text (only
   ordinary text is consulted);
3. substitutes them into every per-record template, then reads each fixed link and
   each substituted link completely through ``read_evidence`` by replaying text-only
   ``nextRequest``; joined bytes must equal the native resources/read bytes and
   ``metadata.contentSha256``, and ``metadata.canonicalUri`` must equal the link;
4. checks that an unreplaced ``{nodeId}`` template fails explicitly.

Usage (repository root)::

    uv --directory backend run --locked --offline --no-sync python \
        ../.standards/docs/reviews/<cycle>/check-evidence-links-review.py
"""

# Standard Library
import asyncio
import base64
import hashlib
import json
import socket
import sys

from typing import Any

# Third Party Library
from fastmcp import Client

# Package Library
import kgfegmcp.app as app_module

from kgfegmcp.app import create_mcp
from kgfegmcp.bootstrap import bootstrap_application

MAX_CHARS = 100_000
MAX_BYTES = 1_048_576
FAILURES: list[str] = []


def _reject(*_args: Any, **_kwargs: Any) -> None:
    raise AssertionError("network connection attempted")


def check(condition: bool, label: str) -> None:
    if not condition:
        FAILURES.append(label)


def links_block(message: str) -> dict[str, str]:
    """Parse '- Label: kgfegmcp://...' lines after the EVIDENCE LINKS heading."""
    if "EVIDENCE LINKS" not in message:
        return {}
    block = message[message.index("EVIDENCE LINKS") :]
    rows: dict[str, str] = {}
    for line in block.splitlines():
        if line.startswith("- ") and ": kgfegmcp://" in line:
            label, _, uri = line[2:].partition(": ")
            rows[label] = uri.strip()
        elif rows and not line.startswith(("- ", "Per-record", "Learning progression rel")):
            break
    return rows


def text_value(text: str, prefix: str) -> str | None:
    """Return the value of the first line starting with prefix, if any."""
    for line in text.splitlines():
        if line.strip().startswith(prefix):
            return line.split(":", 1)[1].strip()
    return None


async def read_full(client: Client, uri: str) -> dict[str, Any]:
    """Read one link completely via text-only nextRequest replay."""
    request: dict[str, Any] | None = {"maxContentBytes": 16384, "uri": uri}
    parts: list[str] = []
    payload: dict[str, Any] = {}
    windows = 0
    while request is not None:
        raw = await client.call_tool_mcp("read_evidence", {"request": request})
        text = raw.content[0].text
        if raw.isError:
            return {"error": text.split(":", 1)[0]}
        payload = json.loads(text)
        check(payload == raw.structuredContent, f"text != structured for {uri}")
        parts.append(payload["content"])
        windows += 1
        request = payload["page"]["nextRequest"]
        if windows > 64:
            return {"error": "window bound exceeded"}
    content = "".join(parts).encode("utf-8")
    native = (await client.read_resource(uri))[0]
    blob = getattr(native, "blob", None)
    native_bytes = base64.b64decode(blob) if blob is not None else native.text.encode()
    digest = "sha256:" + hashlib.sha256(content).hexdigest()
    check(content == native_bytes, f"bytes differ from native: {uri}")
    check(digest == payload["metadata"]["contentSha256"], f"hash mismatch: {uri}")
    check(payload["metadata"]["canonicalUri"] == uri, f"link not canonical: {uri}")
    return {"bytes": len(content), "windows": windows}


async def main() -> dict[str, Any]:
    socket.socket.connect = _reject  # type: ignore[method-assign]
    state = bootstrap_application()
    app_module.bootstrap_application = lambda: state
    out: dict[str, Any] = {}
    async with Client(create_mcp()) as client:
        for runtime in sorted(
            state.catalog_load_result.package_runtimes,
            key=lambda r: str(r.catalog_package.package_identity.framework_id),
        ):
            identity = runtime.catalog_package.package_identity
            framework = str(identity.framework_id)
            snapshot = str(identity.snapshot_id)
            package = runtime.loaded_package
            grades = [g.local_label for g in package.profile.grade_mappings]
            # Oracle choice only: a standard with at least one supporting component.
            supported = sorted(
                {
                    r.target_node_id
                    for r in package.relationships
                    if r.label == "supports"
                }
            )
            target = supported[0]
            selector = {"identifierType": "node_id", "nodeId": target}
            route = {"frameworkId": framework, "snapshotId": snapshot}
            workflows: dict[str, dict[str, Any]] = {
                "learning_progression_teaching_sequence": {"topicOrStandard": "number"},
                "learning_progression_support_plan": {"identifier": selector},
                "learning_progression_curriculum_review": {},
                "teacher_guide_draft": {
                    "gradeOrStage": grades[0],
                    "topicOrStandard": "number",
                },
                "student_study_support": {
                    "gradeOrStage": grades[0],
                    "topicOrStandard": "number",
                },
                "student_handbook_section": {
                    "gradeOrStage": grades[0],
                    "topicOrStandard": "number",
                },
                "multigrade_lesson_plan": {
                    "gradesInRoom": grades[:2],
                    "topicOrStandard": "number",
                },
            }
            blocks: list[dict[str, str]] = []
            sizes: list[int] = []
            for name, extra in workflows.items():
                raw = await client.call_tool_mcp(
                    "get_workflow_instructions",
                    {"request": {**route, **extra, "workflowName": name}},
                )
                if raw.isError:
                    FAILURES.append(f"{framework} {name}: {raw.content[0].text[:160]}")
                    continue
                payload = json.loads(raw.content[0].text)
                wire = raw.model_dump_json(by_alias=True, exclude_none=True)
                sizes.append(len(wire))
                check(
                    len(wire) <= MAX_CHARS and len(wire.encode()) <= MAX_BYTES,
                    f"{framework} {name}: envelope over ceiling",
                )
                message = payload["rendered"]["message"]
                native_args = {
                    "".join(
                        "_" + ch.lower() if ch.isupper() else ch for ch in key
                    ): value if isinstance(value, str) else json.dumps(value)
                    for key, value in {**route, **extra}.items()
                }
                native = await client.get_prompt(name, native_args)
                check(
                    native.messages[0].content.text == message,
                    f"{framework} {name}: native/tool messages differ",
                )
                check(
                    len(message.encode()) <= 64 * 1024,
                    f"{framework} {name}: message over 64 KiB",
                )
                blocks.append(links_block(message))
            check(
                len(blocks) == 7 and all(b == blocks[0] for b in blocks),
                f"{framework}: EVIDENCE LINKS differ across workflows",
            )
            links = blocks[0] if blocks else {}
            expected = {
                "Manifest",
                "Interpretation profile",
                "Validation report",
                "Unresolved items",
                "Learning progression summary",
                "Standard",
                "Standard provenance",
                "Standard learning components",
                "Learning component",
                "Learning component provenance",
            }
            check(set(links) == expected, f"{framework}: link labels {sorted(links)}")

            # IDs taken only from ordinary tool text.
            standard_text = (
                await client.call_tool_mcp(
                    "get_standard",
                    {"request": {**route, "graphType": "academic_standards",
                                 "identifier": selector}},
                )
            ).content[0].text
            components_text = (
                await client.call_tool_mcp(
                    "get_learning_components_for_standard",
                    {"request": {**route, "graphType": "academic_standards",
                                 "identifier": selector}},
                )
            ).content[0].text
            node_id = text_value(standard_text, "Node ID:")
            component_id = text_value(components_text, "1. Learning component:")
            check(node_id == target, f"{framework}: Node ID not visible in text")
            check(component_id is not None, f"{framework}: LC ID not visible in text")
            reads: dict[str, Any] = {}
            for label, uri in sorted(links.items()):
                if "{nodeId}" in uri:
                    ident = component_id if label.startswith("Learning component") else node_id
                    uri = uri.replace("{nodeId}", ident or "")
                result = await read_full(client, uri)
                reads[label] = result
                check("error" not in result, f"{framework} {label}: {result}")
            # Unreplaced template fails explicitly rather than reading anything.
            raw = await client.call_tool_mcp(
                "read_evidence", {"request": {"uri": links.get("Standard provenance", "")}}
            )
            unreplaced = raw.content[0].text.split(":", 1)[0] if raw.isError else "READ"
            check(unreplaced == "invalid_evidence_uri", f"{framework}: unreplaced template")
            out[framework] = {
                "componentId": component_id,
                "maxInstructionEnvelopeChars": max(sizes) if sizes else None,
                "nodeId": node_id,
                "reads": reads,
                "unreplacedTemplate": unreplaced,
            }
    out["failures"] = FAILURES
    return out


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
    except Exception as error:  # record harness/runtime failure explicitly
        result = {"exception": f"{type(error).__name__}: {error}", "failures": FAILURES + ["raised"]}
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    sys.exit(1 if result["failures"] else 0)
