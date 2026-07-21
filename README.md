# edu-kg MCP server

A minimal MCP server that lets an AI model look up official curriculum standards
for Ghana, Nigeria, and Rwanda, using the same tool contract as the Learning
Commons (CZI) hosted Knowledge Graph service: one `find_standard_statement`
tool with identical inputs, response fields, result cap, and error sentences.
A client written against the Learning Commons MCP works against this server
unchanged.

This replaces the earlier TypeScript server in `frontend/`. It is
deliberately small: the three graphs load into memory at startup (~30 MB,
~0.1 s) and queries answer in well under a millisecond.

## Quickstart

    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    python3 -m pytest test_contract.py -v        # 14 tests, ~1 s
    python3 server.py                             # stdio MCP server (finds data/ on its own)

To use it from Claude Code:

    claude mcp add curriculum-standards -- python3 /path/to/edu-kg-mcp/server.py

Or in any MCP client config:

    {"mcpServers": {"curriculum-standards": {"command": "python3",
      "args": ["/path/to/edu-kg-mcp/server.py"]}}}

A different data directory can be passed as an argument (`server.py my/manifest.json`);
the tests honor a `KG_MANIFEST` env var the same way.

## The tool contract

`find_standard_statement` takes exactly one of:

- `code` — an exact statement code or prefix (Ghana only; matches on a dot
  boundary, so `B5.1.1.3` returns itself and `B5.1.1.3.*`).
- `keywords` — a list of topic words; a standard matches if any word matches a
  word in its description by stem ("fraction" matches "fractions").

Plus `jurisdiction` (required: 'Ghana', 'Nigeria', or 'Rwanda') and an optional
`academicSubject`. Responses carry at most 25 results, each with:
academicSubject, caseIdentifierUUID, description, gradeLevels, jurisdiction,
statementCode, and subStandards (direct children) when present.

Two deliberate deviations from the hosted Learning Commons behavior, both
because of what this data is:

1. `jurisdiction` is required. The hosted service defaults to Common Core;
   there is no sensible default across three national curricula.
2. A code search against Nigeria or Rwanda (which have no statement codes)
   returns the error "Statement codes are not available for {country}; search
   with keywords instead." rather than a misleading empty list.

Everything else matches the hosted service, verified against recordings.

## What is in `fixtures/`

Recorded request/response pairs captured from the live Learning Commons MCP
server (July 2026): successful searches, empty results, and every error case.
The contract tests compare this server's behavior against these recordings
directly, so "matches the hosted service" is a tested claim, not an aspiration.

## Data

`data/` holds the three converted graphs plus `manifest.json` (the catalog the
server loads). `source_bundles/` holds the original pipeline exports,
untouched. `convert_bundle.py` turns a bundle into a graph:

    python3 convert_bundle.py source_bundles/academic_standards_kg_bundle_ghana_math.json
    python3 convert_bundle.py --manifest data     # regenerate the catalog

The converter makes four changes, all documented in code: reshapes the bundle
into the node/relationship graph format, copies grades down from grade-level
ancestors (most items ship with empty grade fields), normalizes grade labels
("PRIMARY: THREE" -> "3", originals kept in `local_grade_label`), and recovers
grades from statement codes for the 14 Ghana standards whose parent links were
unresolved in extraction. Descriptions, codes, and tree structure are never
altered.

## Known data notes

- Ghana has 14 standards attached directly to the framework root because their
  parent sub-strands were lost during document extraction; the pipeline's own
  relationship metadata (`llm_reason`) names each missing parent.
- Nigeria contains duplicate objectives (identical text) both across grades
  and within one grade; Rwanda has within-grade duplicate pairs as well.
- Only Ghana's standards carry statement codes.
- Descriptions carry some transcription noise from extraction ("difeferent",
  "corectlyfrom", "substraction" — mostly Rwanda, ~1% of items). Quotes served by
  this server reproduce the noise faithfully; see FINDINGS.md for the full note.
