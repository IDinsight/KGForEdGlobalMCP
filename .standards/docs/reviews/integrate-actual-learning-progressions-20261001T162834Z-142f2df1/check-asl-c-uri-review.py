"""Reviewer diagnostic: where AS/LC tools expose evidence links (AC-029, F-001).

Independent supporting evidence for IMPLEMENTATION review, not formal Tester
verification. Calls get_framework, get_standard, get_learning_component and
get_learning_components_for_standard for the Nigeria diagnostic target through the
real in-memory FastMCP app (network blocked), collects every kgfegmcp:// URI they
return, and records whether each appears in ordinary text, structuredContent or only
resource_link blocks. Exit 1 (failures) lists tools whose links are resource_link-only.
"""

# Standard Library
import asyncio
import json
import socket
import sys

from collections import Counter
from typing import Any

# Third Party Library
from fastmcp import Client

# Package Library
import kgfegmcp.app as app_module

from kgfegmcp.app import create_mcp
from kgfegmcp.bootstrap import bootstrap_application

NIGERIA = "nigeria-nerdc-mathematics-primary-1-3"
SNAPSHOT = "nigeria-nerdc-mathematics-primary-1-3@undated+bc5e769ed26f"
TARGET = "e399b510-48bb-58ee-abda-61460a5a853b"
COMPONENT = "20507dfe-4d56-575c-b7ea-33b1f9072300"


def _reject(*_args: Any, **_kwargs: Any) -> None:
    raise AssertionError("network connection attempted")


def _uris(value: Any, found: set[str]) -> None:
    """Collect kgfegmcp URIs recursively."""
    if isinstance(value, str) and value.startswith("kgfegmcp://"):
        found.add(value)
    elif isinstance(value, dict):
        for item in value.values():
            _uris(item, found)
    elif isinstance(value, list):
        for item in value:
            _uris(item, found)


async def main() -> dict[str, Any]:
    socket.socket.connect = _reject  # type: ignore[method-assign]
    state = bootstrap_application()
    app_module.bootstrap_application = lambda: state
    selector = {"identifierType": "node_id", "nodeId": TARGET}
    route = {"frameworkId": NIGERIA, "snapshotId": SNAPSHOT}
    calls = {
        "get_framework": route,
        "get_standard": {**route, "graphType": "academic_standards", "identifier": selector},
        "get_learning_components_for_standard": {
            **route,
            "graphType": "academic_standards",
            "identifier": selector,
        },
    }
    exposure: dict[str, dict[str, Any]] = {}
    calls["get_learning_component"] = {
        **route,
        "graphType": "academic_standards",
        "nodeId": COMPONENT,
    }
    async with Client(create_mcp()) as client:
        for name, request in calls.items():
            result = await client.call_tool_mcp(name, {"request": request})
            text = " ".join(
                getattr(block, "text", "") for block in result.content if block.type == "text"
            )
            structured: set[str] = set()
            _uris(result.structuredContent, structured)
            linked = sorted(
                str(block.uri) for block in result.content if block.type == "resource_link"
            )
            exposure[name] = {
                "isError": bool(result.isError),
                "resourceLinkUris": linked,
                "structuredUris": sorted(structured),
                "textUris": sorted(u for u in linked if u in text),
            }
    # Established defect signature: links exist only as resource_link blocks.
    resource_link_only = {
        name: not row["textUris"] and not row["structuredUris"] and bool(row["resourceLinkUris"])
        for name, row in exposure.items()
    }
    return {
        "exposure": exposure,
        "failures": [n for n, only in resource_link_only.items() if only],
        "resourceLinkOnly": resource_link_only,
    }


if __name__ == "__main__":
    output = asyncio.run(main())
    print(json.dumps(output, indent=2, sort_keys=True))
    sys.exit(1 if output["failures"] else 0)
