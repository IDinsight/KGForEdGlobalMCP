# Knowledge Graph for Education Global MCP

<!-- Badges -->
<p align="center">
  <a href="https://github.com/econchick/interrogate">
    <img src="./interrogate_badge.svg" alt="Docstring coverage: interrogate">
  </a>
  &nbsp;
  <a href="https://github.com/pylint-dev/pylint">
    <img src="https://img.shields.io/badge/linting-pylint-yellowgreen" alt="Linting: pylint">
  </a>
</p>

Knowledge Graph for Education Global MCP is a curriculum-agnostic FastMCP server for
exploring curriculum knowledge graphs from countries, states, and educational
organizations. It provides one interface for discovering frameworks, searching academic
standards, navigating curriculum hierarchies, retrieving provenance-aware resources,
and assembling deterministic evidence for cross-framework comparison.

Claude Desktop acts as the reasoning and generation layer. The server remains read-only
and deterministic: it loads accepted graph packages, validates and indexes them, returns
source-grounded evidence, and does not call a server-side LLM.

## Architecture

Each curriculum is retained as an independent, immutable, and versioned graph package.
A shared catalog and common MCP services make the packages searchable through one 
server without flattening them into a single source graph.

This preserves:

- exact framework, snapshot, and package identity;
- source terminology and local grade labels;
- provenance, rights, and validation evidence;
- tree and multi-parent DAG topology; and
- unresolved relationship statuses.

The current implementation focuses on Academic Standards graphs and is designed to
remain configuration-driven rather than curriculum-specific.

## Current MCP surface

The server exposes:

- **13 tools**
- **1 fixed resource**
- **12 resource templates**
- **7 prompts**

### Tools

- `list_frameworks`
- `get_framework`
- `search_standards`
- `get_standard`
- `get_standard_context`
- `search_learning_components`
- `get_learning_component`
- `get_learning_component_context`
- `get_learning_components_for_standard`
- `get_framework_statistics`
- `get_capabilities`
- `compare_framework_evidence`
- `collect_progression_evidence`

### Prompts

- `student_study_support`
- `teacher_guide_draft`
- `student_handbook_section`
- `multigrade_lesson_plan`
- `inferred_progression_hypothesis`
- `administrator_alignment_review`
- `cross_framework_comparison`

`compare_framework_evidence` exposes text matching through flat scalar fields
`matchMode` (`tokens` or `exact_phrase`) and `matchOperator` (`all` or `any`).
Do not send a nested `match` object to this tool. The adapter constructs the existing
typed internal text-match policy before calling the ordinary comparison service.

### Lexical topic discovery

Text search uses exact normalized description tokens or contiguous normalized phrases.
It does not stem words or expand synonyms, so `fraction` and `fractions` are different
queries. For concept discovery, Claude should search the user's original wording first
and may then issue at most three separate conservative alternatives, such as a clear
singular/plural or retrieved local-terminology variant. Every alternative must preserve
the same framework, snapshot, grade, subject, statement-type, grouping, match, and limit
settings. Cross-framework alternatives must be applied symmetrically. Each call retains
its own bounds, scores, `has_more` value, and cursor; a zero-match result does not prove
curriculum absence. Once a relevant branch is found, bounded hierarchy context is
preferred over unlimited synonym generation.

`inferred_progression_hypothesis` accepts `local_grade_labels` and
`normalized_grades` as typed arrays rather than a combined grade string. At the MCP
prompt boundary, enter these complex values as JSON arrays, for example
`["Grade 1", "Grade 2"]`; do not enter comma-separated prose. Its workflow
calls `collect_progression_evidence` once; that tool validates the grade
scope, canonicalizes grade sets in package-declared order, deduplicates standard-item
candidates, balances selection across requested scopes, reports uncovered scopes, and
enforces the requested candidate limit before Claude generates a hypothesis.

## Prerequisites

Install:

- [uv](https://docs.astral.sh/uv/)
- Git
- Python 3.13 through `uv`
- Claude Desktop for local MCP use

None of this is needed to use a hosted deployment; see
[Connect to a hosted server](#connect-to-a-hosted-server).

The project requires Python `>=3.13,<3.14`.

Install the required Python version:

```bash
uv python install 3.13
```

Node.js and npm are needed only when building an optional `.mcpb` distribution.

## Repository setup

Clone the repository and enter its root:

```bash
git clone <repository-url>
cd KGForEdGlobalMCP
```

Create or update the locked backend environment:

```bash
uv --directory backend sync --locked --no-dev
```

The application resolves the repository-level `config/` and `data/` directories from
its installed source layout. Optional `KGFEGMCP_*` environment variables can override
those paths, but are not required for ordinary repository-local commands.

To install development tooling as well:

```bash
uv --directory backend sync --locked --extra dev
```

## Verify the local server

Run the real server through a separate locked STDIO subprocess:

```bash
uv --directory backend run --locked --no-dev kgfegmcp-stdio-smoke
```

The smoke command:

1. starts `python -m kgfegmcp.mcpb_server`;
2. completes an MCP handshake;
3. verifies the exact 13-tool, 1-resource, 12-template, and 7-prompt inventory; and
4. confirms that the subprocess exits cleanly.

A successful run returns a JSON result with `"status": "passed"`.

The server entry point can also be started directly:

```bash
uv --directory backend run --locked --no-dev \
  python -m kgfegmcp.mcpb_server
```

That command is not an interactive shell. It waits for an MCP client and reserves
stdout for protocol traffic.

## Connect Claude Desktop

The confirmed local integration uses Claude Desktop's MCP configuration file:

```text
~/Library/Application Support/Claude/claude_desktop_config.json
```

Find the absolute paths required by Claude Desktop:

```bash
command -v uv
pwd
```

Add the following entry under the existing top-level `mcpServers` object. Replace
`/absolute/path/to/uv` and `/absolute/path/to/repository` with the values from your
machine. Preserve unrelated Claude Desktop settings already present in the file.

```json
{
  "mcpServers": {
    "curriculum-knowledge-graph": {
      "command": "/absolute/path/to/uv",
      "args": [
        "--directory",
        "/absolute/path/to/repository/backend",
        "run",
        "--locked",
        "--no-dev",
        "python",
        "-m",
        "kgfegmcp.mcpb_server"
      ],
      "env": {
        "KGFEGMCP_CONFIG_ROOT": "/absolute/path/to/repository/config",
        "KGFEGMCP_DATA_ROOT": "/absolute/path/to/repository/data",
        "KGFEGMCP_ENV": "local",
        "KGFEGMCP_GRAPH_PACKAGES_ROOT": "/absolute/path/to/repository/data/graph_packages",
        "KGFEGMCP_INVALID_PACKAGE_POLICY": "fail",
        "KGFEGMCP_LOG_LEVEL": "INFO",
        "KGFEGMCP_PROFILE_ROOT": "/absolute/path/to/repository/config/profiles",
        "KGFEGMCP_PROMPT_ROOT": "/absolute/path/to/repository/config/prompts",
        "PATHS_PROJECT_DIR": "/absolute/path/to/repository"
      }
    }
  }
}
```

When the file already contains other keys, replace only the empty `mcpServers` object or
add the `curriculum-knowledge-graph` member to the existing object.

Validate the JSON:

```bash
jq empty "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
```

Fully quit and reopen Claude Desktop:

```bash
osascript -e 'quit app "Claude"'
```

After restart, enable **curriculum-knowledge-graph** under **Connectors** in a new
conversation.

A simple first request is:

```text
Use the curriculum-knowledge-graph connector to list all available frameworks.
```

## Connect to a hosted server

The same server can run as a hosted Streamable HTTP service. Clients then connect to a
URL instead of starting a local process, and nothing is installed on the user's machine:

```text
https://<service-domain>/mcp
```

In Claude, add a custom connector in the connector settings and enter that URL, leaving
authentication empty. In Claude Code:

```bash
claude mcp add --transport http curriculum-knowledge-graph https://<service-domain>/mcp
```

The hosted service is built from the root `Dockerfile`, which bakes `config/` and
`data/graph_packages/` into the image and starts `python -m kgfegmcp.http_server`. The
MCP surface is identical to the local STDIO server. Build and verify it locally with:

```bash
docker build -t kgfegmcp-http:local .
docker run --rm --read-only -e PORT=8000 -p 8000:8000 kgfegmcp-http:local

uv --directory backend run --locked --no-dev kgfegmcp-http-smoke \
  --url http://localhost:8000/mcp
```

See `docs/operations/deployment.md` for the hosting workflow, rollback, and the access
and rights posture of a public endpoint.

## Optional MCPB package

The repository can build a deterministic MCP Bundle containing the locked Python
metadata, source package, profiles, prompt configurations, and accepted graph packages.

Install the official MCPB CLI:

```bash
npm install -g @anthropic-ai/mcpb
```

Build the bundle:

```bash
uv --directory backend run --locked --no-dev kgfegmcp-build-mcpb
```

The default output is:

```text
dist/kgfegmcp-0.1.0.mcpb
```

Retain the exact staging directory for review:

```bash
rm -rf ./dist/kgfegmcp-stage

uv --directory backend run --locked --no-dev kgfegmcp-build-mcpb \
  --stage-output ./dist/kgfegmcp-stage
```

Smoke-test the staged runtime:

```bash
uv --directory backend run --locked --no-dev kgfegmcp-stdio-smoke \
  --bundle-root ./dist/kgfegmcp-stage
```

The bundle does not contain a virtual environment or vendored dependencies. Its runtime
uses locked `uv` project metadata and starts the server with:

```text
python -m kgfegmcp.mcpb_server
```

Claude Desktop custom-extension installation behavior may vary by client build. Manual
registration through `claude_desktop_config.json` is the confirmed local connection
method.

## Useful CLI commands

Show command help:

```bash
uv --directory backend run --locked --no-dev kgfegmcp-stdio-smoke --help
uv --directory backend run --locked --no-dev kgfegmcp-http-smoke --help
uv --directory backend run --locked --no-dev kgfegmcp-build-mcpb --help
uv --directory backend run --locked --no-dev kgfegmcp-build-manifest --help
uv --directory backend run --locked --no-dev kgfegmcp-validate-packages --help
```

## Troubleshooting

### Connector does not appear

Confirm that:

- `command` is the absolute result of `command -v uv`;
- the repository and backend paths are absolute;
- the JSON passes `jq empty`;
- Claude Desktop was fully quit and reopened; and
- the repository STDIO smoke still passes.

Inspect Claude's logs on macOS:

```bash
find "$HOME/Library/Logs/Claude" \
  -maxdepth 1 \
  -type f \
  -iname '*mcp*' \
  -print
```

### `No module named 'mcp.types'`

Always launch the server as a module:

```text
python -m kgfegmcp.mcpb_server
```

Do not execute `src/kgfegmcp/mcpb_server.py` by filesystem path. Direct file execution
can cause the internal `kgfegmcp.mcp` package to shadow the external MCP SDK package.

### Protocol output errors

STDIO stdout is reserved for MCP protocol messages. Application logging must remain on
stderr, and production code should not use uncontrolled `print()` calls.

## Project documentation

- `instructions.md` is the architectural and implementation source of truth.
- `backend/README.md` contains backend-specific operational notes.
- `packaging/mcpb/README.md` describes the MCP Bundle packaging workflow.

## License

See [LICENSE](./LICENSE).
