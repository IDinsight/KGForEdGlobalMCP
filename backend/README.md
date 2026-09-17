# Curriculum Knowledge Graph MCP backend

This package contains the curriculum-agnostic FastMCP application and its ordinary
domain services. It loads immutable graph packages, builds the accepted catalog and
search indexes, exposes deterministic tools, resources, and prompts, and supports local
STDIO execution, hosted Streamable HTTP execution, and MCP Bundle packaging.

The backend remains read-only at runtime. It does not call a server-side LLM, mutate
accepted curriculum packages, or embed curriculum-specific behavior in generic Python
code.

## Runtime contract

The application uses:

- Python `>=3.13,<3.14`;
- standalone `fastmcp==3.4.4`;
- the external MCP Python SDK;
- Pydantic 2;
- `uv` for locked dependency and interpreter management; and
- STDIO as the local transport and stateless Streamable HTTP as the hosted transport.

The fixed MCP inventory is:

- **9 tools**
- **1 fixed resource**
- **9 resource templates**
- **6 prompts**

Application state is constructed once inside the FastMCP lifespan. The accepted graph
packages, catalog service, search service, comparison service, progression-evidence
service, resource service, and prompt service share the same immutable runtime objects.

## Backend layout

Important paths:

```text
backend/
├── pyproject.toml
├── uv.lock
├── fastmcp.json
├── src/
│   └── kgfegmcp/
│       ├── app.py
│       ├── bootstrap.py
│       ├── config.py
│       ├── http_server.py
│       ├── mcpb_server.py
│       ├── catalog/
│       ├── cli/
│       ├── graph/
│       ├── mcp/
│       ├── packages/
│       ├── profiles/
│       ├── prompts/
│       ├── resources/
│       ├── search/
│       └── services/
└── tests/
```

Repository-level runtime inputs remain outside `backend/`:

```text
config/
├── profiles/
└── prompts/

data/
└── graph_packages/
```

## Prerequisites

Install `uv`, then install Python 3.13:

```bash
uv python install 3.13
```

From the repository root, create or update the locked runtime environment:

```bash
uv --directory backend sync --locked --no-dev
```

To include development dependencies:

```bash
uv --directory backend sync --locked --extra dev
```

The project does not require manually activating a virtual environment when commands are
run through `uv`.

## Configuration

`BackendSettings` reads application-owned settings from the process environment.
Development shells may use `direnv`, but Python does not discover or parse a project
`.env` file for application settings.

The ordinary repository layout is resolved from `PATHS_PROJECT_DIR`. The most relevant
variables are:

```text
PATHS_PROJECT_DIR
KGFEGMCP_CONFIG_ROOT
KGFEGMCP_DATA_ROOT
KGFEGMCP_GRAPH_PACKAGES_ROOT
KGFEGMCP_PROFILE_ROOT
KGFEGMCP_PROMPT_ROOT
KGFEGMCP_INVALID_PACKAGE_POLICY
KGFEGMCP_LOG_LEVEL
```

Typical repository-local values are:

```bash
export PATHS_PROJECT_DIR="/absolute/path/to/KGForEdGlobalMCP"
export KGFEGMCP_CONFIG_ROOT="$PATHS_PROJECT_DIR/config"
export KGFEGMCP_DATA_ROOT="$PATHS_PROJECT_DIR/data"
export KGFEGMCP_GRAPH_PACKAGES_ROOT="$PATHS_PROJECT_DIR/data/graph_packages"
export KGFEGMCP_PROFILE_ROOT="$PATHS_PROJECT_DIR/config/profiles"
export KGFEGMCP_PROMPT_ROOT="$PATHS_PROJECT_DIR/config/prompts"
export KGFEGMCP_INVALID_PACKAGE_POLICY="fail"
export KGFEGMCP_LOG_LEVEL="INFO"
```

These overrides are useful for desktop-host configuration. Ordinary repository commands
can use the defaults when the source layout is intact.

## Start the server

The protocol-only packaged entry point is:

```bash
uv --directory backend run --locked --no-dev   python -m kgfegmcp.mcpb_server
```

This is not an interactive shell. The process waits for an MCP client and reserves
stdout for JSON-RPC protocol traffic.

The hosted entry point runs the same `create_mcp` server over stateless Streamable HTTP:

```bash
PORT=8000 uv --directory backend run --locked --no-dev   python -m kgfegmcp.http_server
```

It serves MCP at `/mcp`, binds the port supplied through `PORT` (default `8000`), and
exposes `GET /health`. The root `Dockerfile` starts this entry point. See
`docs/operations/deployment.md`.

Always launch it as a module:

```text
python -m kgfegmcp.mcpb_server
```

Do not execute this filesystem path:

```text
python src/kgfegmcp/mcpb_server.py
```

Direct file execution can place `src/kgfegmcp` at the front of `sys.path`, causing the
internal `kgfegmcp.mcp` package to shadow the external MCP SDK package named `mcp`.

## Repository STDIO smoke

Run the real server through a separate locked subprocess:

```bash
uv --directory backend run --locked --no-dev kgfegmcp-stdio-smoke
```

The command:

1. launches `python -m kgfegmcp.mcpb_server`;
2. completes the MCP initialization handshake;
3. lists tools, prompts, fixed resources, and resource templates;
4. verifies the exact 9/1/9/6 inventory; and
5. requires a clean subprocess shutdown.

A successful run prints deterministic JSON containing:

```json
{
  "bundleRoot": null,
  "fixedResourceCount": 1,
  "promptCount": 6,
  "resourceTemplateCount": 9,
  "status": "passed",
  "toolCount": 9
}
```

Protocol traffic remains on stdout. FastMCP and application logs remain on stderr.

## FastMCP configuration

`backend/fastmcp.json` describes the filesystem factory, no-argument `create_mcp`
entry point, backend working directory, and STDIO transport.

It is a FastMCP server configuration, not a Claude Desktop client configuration. The
invoking `uv run --locked` command owns the Python environment.

## User-facing CLI commands

Installed project scripts include:

```text
kgfegmcp-build-manifest
kgfegmcp-validate-packages
kgfegmcp-build-mcpb
kgfegmcp-stdio-smoke
kgfegmcp-http-smoke
```

Show their command surfaces:

```bash
uv --directory backend run --locked --no-dev   kgfegmcp-build-manifest --help

uv --directory backend run --locked --no-dev   kgfegmcp-validate-packages --help

uv --directory backend run --locked --no-dev   kgfegmcp-build-mcpb --help

uv --directory backend run --locked --no-dev   kgfegmcp-stdio-smoke --help

uv --directory backend run --locked --no-dev   kgfegmcp-http-smoke --help
```

Every new user-facing CLI module must have a matching `[project.scripts]` entry in
`pyproject.toml`.

## Package validation

Inspect the package-validation commands:

```bash
uv --directory backend run --locked --no-dev   kgfegmcp-validate-packages --help
```

The package validator:

- discovers packages beneath the configured graph-package root;
- verifies manifests, profiles, checksums, artifact closure, and snapshot identity;
- decodes accepted delivery records;
- validates identifiers, endpoints, counts, capabilities, rights, and topology;
- preserves valid multi-parent DAG structure; and
- supports read-only revalidation.

The six repository graph packages are the terminal positive baseline. Destructive or
negative lifecycle scenarios should use temporary copies or synthetic packages.

## Build an MCP Bundle

Install the official MCPB CLI:

```bash
npm install -g @anthropic-ai/mcpb
```

Build from the repository root:

```bash
uv --directory backend run --locked --no-dev kgfegmcp-build-mcpb
```

The default output is:

```text
dist/kgfegmcp-0.1.0.mcpb
```

The packaging command stages:

- generic runtime source;
- `pyproject.toml` and `uv.lock`;
- FastMCP configuration;
- all six profiles;
- all six prompt configurations; and
- all six accepted graph packages.

It then runs the official MCPB validation and packing commands and independently verifies
the archive.

The bundle excludes virtual environments, vendored dependencies, caches, bytecode,
build output, and repository metadata.

## Retain and smoke the staged bundle

Retain the exact packaged filesystem:

```bash
rm -rf ./dist/kgfegmcp-stage

uv --directory backend run --locked --no-dev kgfegmcp-build-mcpb   --stage-output ./dist/kgfegmcp-stage
```

Exercise that staged runtime:

```bash
uv --directory backend run --locked --no-dev kgfegmcp-stdio-smoke   --bundle-root ./dist/kgfegmcp-stage
```

The staged smoke confirms that the package includes complete source, configuration, and
data inputs and exposes the same accepted MCP inventory independently of the ordinary
repository layout.

See [`../packaging/mcpb/README.md`](../packaging/mcpb/README.md) for the complete
packaging contract, archive inspection, and troubleshooting workflow.

## Claude Desktop

The confirmed local-development connection uses:

```text
~/Library/Application Support/Claude/claude_desktop_config.json
```

Claude Desktop should launch the backend through the absolute `uv` path and the
module-based server entry point:

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
      ]
    }
  }
}
```

The complete configuration also supplies explicit repository-level config, profile,
prompt, and graph-package paths. See the root [`README.md`](../README.md) for the full
copyable example and restart instructions.

Custom `.mcpb` installation behavior can vary by Claude Desktop build. Manual
`claude_desktop_config.json` registration is the confirmed local connection method.

## Public MCP components

### Tools

```text
list_frameworks
get_framework
search_standards
get_standard
get_standard_context
get_framework_statistics
get_capabilities
compare_framework_evidence
collect_progression_evidence
```

### Prompts

```text
student_study_support
teacher_guide_draft
student_handbook_section
inferred_progression_hypothesis
administrator_alignment_review
cross_framework_comparison
```

The public `compare_framework_evidence` tool uses flat `matchMode` and
`matchOperator` fields for text retrieval. It no longer accepts a public nested `match`
object; the MCP adapter constructs the ordinary typed text-match model internally.

### Lexical query expansion

A single text-search call matches exact normalized description tokens or one contiguous
normalized phrase. It performs no stemming, lemmatization, fuzzy matching, or synonym
expansion. Therefore, these are separate deterministic calls:

```text
fraction
fractions
```

For topic or concept discovery, the client model must execute the caller's original
wording first. If recall is zero or visibly narrow, it may issue at most three separate
conservative alternatives, prioritizing inflectional, orthographic, abbreviation,
operator-approved alias, or retrieved local-terminology variants. Every alternative must
preserve the same framework, snapshot, graph type, grade, subject, statement-type,
grouping, match, and limit settings. Shared cross-framework alternatives must be applied
symmetrically.

Do not merge lexical scores or cursors across calls. Presentation may deduplicate by
`graphPackageId` plus `nodeId`, but it must record every query that retrieved the node.
A zero-match page means only that the exact query did not match retained descriptions
under the supplied filters. After identifying a relevant grouping, use bounded graph
context to recover related items that do not contain any query token.

The progression prompt accepts `local_grade_labels` and `normalized_grades` as
typed arrays. MCP prompt clients serialize these complex values as JSON strings, so
enter JSON arrays such as `["Grade 1", "Grade 2"]`, not a comma-separated
prose string. It renders one direct
`collect_progression_evidence` call. The ordinary progression-evidence service
validates and canonically orders those scopes, excludes grouping nodes from the
candidate count, deduplicates exact standards, applies deterministic grade-balanced
selection, reports requested scopes without retained evidence, and returns no more than
`candidate_limit` retained candidates.

### Resources

The server registers:

- `kgfegmcp://catalog`; and
- nine `kgfegmcp://` resource templates for framework, manifest, validation, unresolved
  evidence, interpretation profile, declared artifacts, standards, provenance, and
  relationships.

## Development rules

Backend changes should preserve these boundaries:

- keep MCP adapters thin;
- keep domain, graph, package, search, prompt, resource, and comparison logic in ordinary
  services;
- do not add curriculum-specific Python branches;
- do not mutate accepted source packages;
- preserve all valid parent edges and unresolved statuses;
- use complete type annotations and accurate docstrings;
- use named arguments for calls with more than one argument;
- keep named arguments alphabetically ordered;
- avoid server-side LLM calls and MCP sampling; and
- reserve STDIO stdout for protocol messages.

The root `instructions.md` is the architecture and implementation source of truth.

## Optional quality commands

Run these from the repository root when requested:

```bash
uv --directory backend run --locked ruff check .
uv --directory backend run --locked black --check .
uv --directory backend run --locked isort --check-only .
uv --directory backend run --locked pylint src/kgfegmcp
uv --directory backend run --locked mypy src/kgfegmcp
```

Automated tests and quality tools may be deferred for a particular implementation unit,
but any deferral should remain explicit.

## Troubleshooting

### `No module named 'mcp.types'`

A filesystem launch was used. Run:

```bash
uv --directory backend run --locked --no-dev   python -m kgfegmcp.mcpb_server
```

### STDIO smoke reports `Connection closed`

Inspect the child-process traceback first. Common causes include:

- a direct filesystem launch instead of the module launcher;
- incorrect repository path environment variables;
- missing or invalid graph-package inputs; or
- a locked dependency environment that has not been synchronized.

Recreate the locked environment and retry:

```bash
uv --directory backend sync --locked --no-dev
uv --directory backend run --locked --no-dev kgfegmcp-stdio-smoke
```

### Claude Desktop does not see the connector

Confirm:

```bash
command -v uv
jq empty "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
```

Then fully quit and reopen Claude Desktop. The `command` field must contain the absolute
`uv` path, and all repository paths must be absolute.

### Logs appear on protocol stdout

Remove uncontrolled `print()` calls. Application logging must use standard-library child
loggers and remain on stderr under FastMCP's logging lifecycle.

## Related documentation

- [`../README.md`](../README.md): project setup and Claude Desktop onboarding
- [`../packaging/mcpb/README.md`](../packaging/mcpb/README.md): MCP Bundle packaging
- [`../instructions.md`](../instructions.md): architecture and implementation source of truth
