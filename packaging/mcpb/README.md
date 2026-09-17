# MCP Bundle packaging

This directory contains the MCPB manifest template, packaging exclusions, and operator
notes for the local Curriculum Knowledge Graph MCP Server distribution.

The committed files in this directory are packaging inputs, not a complete installable
bundle. The packaging CLI assembles a clean staging root from the accepted repository
runtime, delegates validation and archive creation to the official `mcpb` command, and
then independently verifies the completed archive.

## What the bundle contains

The staged MCPB runtime includes:

- the generic `kgfegmcp` Python source package;
- `pyproject.toml` and the locked `uv.lock`;
- `backend/fastmcp.json`;
- all six versioned curriculum profiles;
- all six framework-local prompt configurations;
- all six accepted immutable graph packages; and
- the MCPB `manifest.json`.

The bundle does not contain:

- a virtual environment;
- vendored Python dependencies;
- `__pycache__` directories or `.pyc` files;
- local caches, logs, or build output;
- Git or other repository metadata; or
- arbitrary files outside the approved staging contract.

The implementation remains curriculum-agnostic. Packaging copies the accepted runtime
inputs without introducing curriculum-specific Python behavior.

## Runtime contract

The manifest uses the MCPB 0.4 UV runtime:

```json
{
  "manifest_version": "0.4",
  "server": {
    "type": "uv"
  }
}
```

The packaged server starts through the Python module entry point:

```text
python -m kgfegmcp.mcpb_server
```

Do not change this to a filesystem invocation such as:

```text
python src/kgfegmcp/mcpb_server.py
```

Executing the file directly can place `src/kgfegmcp` at the front of `sys.path` and
cause the internal `kgfegmcp.mcp` package to shadow the external MCP SDK package named
`mcp`.

Python compatibility is enforced by `pyproject.toml` and `uv.lock`. The MCPB manifest
does not declare a separate host-system Python runtime requirement because the UV runtime
manages the project environment.

## Prerequisites

Install:

- `uv`;
- Node.js and npm; and
- the official MCPB CLI.

Install the MCPB CLI:

```bash
npm install -g @anthropic-ai/mcpb
```

Confirm both commands are available:

```bash
command -v uv
command -v mcpb
```

## Build the bundle

Run from the repository root:

```bash
uv --directory backend run --locked --no-dev kgfegmcp-build-mcpb
```

The default output is:

```text
dist/kgfegmcp-0.1.0.mcpb
```

The command:

1. validates the project and manifest contract;
2. assembles a clean temporary staging directory;
3. copies the approved source, configuration, profile, prompt, and package files;
4. rejects symlinks, unsafe paths, special filesystem entries, and unexpected files;
5. runs the official MCPB validation and packing commands;
6. reopens the generated archive; and
7. confirms that every archive member matches the staged source byte for byte.

## Choose a different output path

```bash
uv --directory backend run --locked --no-dev kgfegmcp-build-mcpb   --output ./dist/review-build.mcpb
```

The output path must not be inside the staging directory.

## Retain the staging directory

By default, the temporary staging directory is removed after a successful build. Retain
it when reviewing the exact packaged filesystem or running staged-runtime acceptance:

```bash
rm -rf ./dist/kgfegmcp-stage

uv --directory backend run --locked --no-dev kgfegmcp-build-mcpb   --stage-output ./dist/kgfegmcp-stage
```

The requested staging directory must either not exist or be completely empty.

A retained stage has this general shape:

```text
dist/kgfegmcp-stage/
├── README.md
├── fastmcp.json
├── manifest.json
├── pyproject.toml
├── uv.lock
├── config/
│   ├── profiles/
│   └── prompts/
├── data/
│   └── graph_packages/
└── src/
    └── kgfegmcp/
```

## Smoke-test the repository runtime

Before packaging, verify the ordinary locked runtime:

```bash
uv --directory backend run --locked --no-dev kgfegmcp-stdio-smoke
```

This starts the real server in a separate STDIO subprocess, completes the MCP handshake,
and verifies the exact public inventory:

- 13 tools;
- 1 fixed resource;
- 12 resource templates; and
- 7 prompts.

A successful command returns a JSON result with `"status": "passed"`. The inventory
includes the deterministic `collect_progression_evidence` tool used by the
`inferred_progression_hypothesis` prompt to enforce multi-grade candidate limits.

## Smoke-test the staged runtime

After retaining a stage:

```bash
uv --directory backend run --locked --no-dev kgfegmcp-stdio-smoke   --bundle-root ./dist/kgfegmcp-stage
```

This verifies that the packaged filesystem layout can start independently of the normal
repository layout and exposes the same approved MCP inventory.

## Recommended acceptance sequence

Run these commands from the repository root:

```bash
uv --directory backend run --locked --no-dev   kgfegmcp-build-mcpb --help

uv --directory backend run --locked --no-dev   kgfegmcp-stdio-smoke --help

uv --directory backend run --locked --no-dev   kgfegmcp-stdio-smoke

rm -rf ./dist/kgfegmcp-stage

uv --directory backend run --locked --no-dev   kgfegmcp-build-mcpb --stage-output ./dist/kgfegmcp-stage

uv --directory backend run --locked --no-dev   kgfegmcp-stdio-smoke --bundle-root ./dist/kgfegmcp-stage

unzip -t ./dist/kgfegmcp-0.1.0.mcpb
```

The completed local acceptance baseline is:

1. both CLI help commands load;
2. the repository STDIO smoke passes;
3. the MCPB archive builds;
4. the retained stage is complete;
5. the staged-runtime STDIO smoke passes; and
6. the generated archive passes ZIP integrity inspection.

## Use a custom MCPB executable

When `mcpb` is not on `PATH`, or when testing a specific installation:

```bash
uv --directory backend run --locked --no-dev kgfegmcp-build-mcpb   --mcpb-command /absolute/path/to/mcpb
```

This option can be combined with `--output` and `--stage-output`.

## Inspect the generated archive

List archive members:

```bash
unzip -l ./dist/kgfegmcp-0.1.0.mcpb
```

Read the packaged manifest:

```bash
unzip -p ./dist/kgfegmcp-0.1.0.mcpb manifest.json | jq .
```

Confirm the module launcher:

```bash
unzip -p ./dist/kgfegmcp-0.1.0.mcpb manifest.json   | jq '.server'
```

Confirm ZIP integrity:

```bash
unzip -t ./dist/kgfegmcp-0.1.0.mcpb
```

## Claude Desktop

The `.mcpb` file is intended for Claude Desktop's custom-extension installation flow.
Installation behavior can vary by Claude Desktop build. Some builds recognize a valid
bundle but leave the **Install** button disabled during client-side prerequisite checks.

The confirmed local-development connection method is manual registration through:

```text
~/Library/Application Support/Claude/claude_desktop_config.json
```

That configuration launches the same accepted entry point through the repository's
locked `uv` environment:

```text
uv --directory <repository>/backend run --locked --no-dev   python -m kgfegmcp.mcpb_server
```

See the root [`README.md`](../../README.md) for the complete Claude Desktop configuration,
validation, restart, and connector-enablement instructions.

The MCPB artifact remains useful for deterministic packaging, review, distribution, and
future one-click installation when supported by the active client build.

## Packaging safety guarantees

The build command rejects or detects:

- missing required source or runtime files;
- unexpected staging or archive members;
- duplicate archive entries;
- path traversal and absolute archive paths;
- symbolic links and special filesystem entries;
- virtual environments, caches, and bytecode;
- output paths placed inside the staging root;
- incomplete or non-empty retained-stage destinations;
- manifest and project metadata disagreement;
- source-to-stage byte differences; and
- stage-to-archive byte differences.

Packaging does not alter the source graph packages, profiles, prompt configurations,
search behavior, comparison behavior, graph traversal, resource policy, or application
logic.

## Troubleshooting

### `No module named 'mcp.types'`

Verify that every launch surface uses:

```text
python -m kgfegmcp.mcpb_server
```

A direct filesystem invocation of `mcpb_server.py` can cause package-name shadowing.

### MCPB command not found

Locate the installed executable:

```bash
command -v mcpb
npm prefix -g
```

Then pass the absolute path with `--mcpb-command`.

### Staging directory rejected

Remove the previous stage before rebuilding:

```bash
rm -rf ./dist/kgfegmcp-stage
```

The packaging command intentionally refuses to reuse a non-empty staging directory.

### Claude Desktop does not install the bundle

First confirm that the repository and staged STDIO smoke commands pass. If they do,
treat the problem as a Claude Desktop installation-path issue rather than changing the
server runtime. Use the manual connector configuration documented in the root README.

## Related documentation

- [`../../README.md`](../../README.md): repository setup and Claude Desktop startup
- [`../../backend/README.md`](../../backend/README.md): backend development commands
- [`../../instructions.md`](../../instructions.md): architecture and implementation source of truth
