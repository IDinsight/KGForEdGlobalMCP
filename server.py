"""One-tool MCP server: find_standard_statement over the converted country graphs.

Matches the hosted Learning Commons server's behavior (captures in fixtures/),
with two deliberate deviations, both about search modes our data can't honor:
jurisdiction is required (no sensible default exists here), and code search
against a codeless country errors instead of returning a misleading empty list.

Uses the low-level MCP server because FastMCP prefixes every error with
"Error executing tool ...", and the contract requires bare sentences.

Run: python server.py [manifest.json]     (stdio transport)
"""

import asyncio
import json
import sys
from pathlib import Path

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from kg import Registry

_LOCAL = Path(__file__).resolve().parent / "data" / "manifest.json"
_DEV = Path(__file__).resolve().parent.parent / "examples" / "kgs" / "manifest.json"
DEFAULT_MANIFEST = _LOCAL if _LOCAL.exists() else _DEV

registry = Registry(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_MANIFEST)
server = Server("curriculum-standards")

def _coverage(g):
    grades = sorted({int(x) for v in g.grades.values() for x in v})
    span = f"grades {grades[0]}-{grades[-1]}" if grades else "grades unknown"
    codes = "statement codes available" if g.has_codes else "no statement codes — use keywords"
    return f"{g.subject}, {span}, {codes}"


_juris = ", ".join(f"'{j}' ({_coverage(g)})" for j, g in registry.graphs.items())

DESCRIPTION = f"""Find education standards, by ONE of two modes — provide exactly one of:
  - `code`: an exact statementCode OR a code prefix (e.g. 'B5.1.1.3' for that standard and everything beneath it). Matches the code itself or any code starting with it plus '.'. Case-insensitive.
  - `keywords`: standards whose description matches ANY of these words by stem (case-insensitive, whole-word — e.g. 'fraction' also matches 'fractions'; use when you know a topic but not a code).
The modes are not combined: if both are given, `code` wins.

`jurisdiction` is required. Frameworks in this deployment: {_juris}. Each framework contains ONLY what is listed here — topics outside these grades and subjects (e.g. secondary-school material) are not in this data, so do not search for them.

Results carry `gradeLevels` (year of primary, e.g. ["5"]) — use them to pick the right grade's standard when a topic repeats across grades. Each standard includes a `subStandards` array with its direct children when it has any."""

TOOL = types.Tool(
    name="find_standard_statement",
    description=DESCRIPTION,
    inputSchema={
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Exact statementCode or a code prefix."},
            "keywords": {"type": "array", "items": {"type": "string"},
                         "description": "Topic words; any-of, stemmed whole-word match on descriptions."},
            "jurisdiction": {"type": "string",
                             "description": "Required. One of: " + ", ".join(f"'{j}'" for j in registry.graphs) + "."},
            "academicSubject": {"type": "string",
                                "description": "Optional. One of: 'Mathematics', 'English Language Arts', 'Science', 'Social Studies', 'Other'."},
        },
    },
)


@server.list_tools()
async def list_tools():
    return [TOOL]


@server.call_tool()
async def call_tool(name, arguments):
    result = registry.find_standard_statement(
        code=arguments.get("code"),
        keywords=arguments.get("keywords"),
        jurisdiction=arguments.get("jurisdiction"),
        academic_subject=arguments.get("academicSubject"),
    )
    return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]


async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
