# Local installation

This page describes the repository-local installation and runtime contract in more
detail than the [Quickstart](index.md).

The backend is a Python 3.13 FastMCP application managed with `uv`. Runtime configuration
and graph data remain at the repository level rather than being copied into the Python
source tree during local development.

## Repository layout

The main runtime paths are:

```text
KGForEdGlobalMCP/
├── backend/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── fastmcp.json
│   └── src/
│       └── kgfegmcp/
├── config/
│   ├── profiles/
│   └── prompts/
├── data/
│   └── graph_packages/
├── packaging/
│   └── mcpb/
└── docs/
```

The application code is generic. Framework-specific semantics and accepted curriculum 
data are supplied through the repository-level `config/` and `data/` directories.

## Install prerequisites

### Install `uv`

Install `uv` using the method appropriate for your platform, then confirm it is on your
`PATH`:

```bash
command -v uv
uv --version
```

### Install Python 3.13

The project declares:

```text
Python >=3.13,<3.14
```

Install a compatible interpreter through `uv`:

```bash
uv python install 3.13
```

Using `uv` for the interpreter and dependency environment keeps local execution aligned
with the locked project metadata.

## Synchronize dependencies

From the repository root, install runtime dependencies only:

```bash
uv --directory backend sync --locked --no-dev
```

For development work, include the optional development dependency group:

```bash
uv --directory backend sync --locked --extra dev
```

The project does not require manually activating a virtual environment when commands are
invoked through `uv`.

## Runtime configuration

`BackendSettings` reads application-owned settings from the process environment. The
ordinary repository layout works without manually exporting every path when the checkout
structure is intact.

The most relevant settings are:

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

A fully explicit repository-local configuration looks like:

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

These explicit paths are especially useful when a desktop MCP host launches the server
outside your interactive shell.

!!! note "No implicit project .env loading"
    Application settings come from constructor values and the process environment. A
    development shell may use tools such as `direnv`, but the Python application does not
    rely on discovering and parsing a repository `.env` file.

## Verify package loading and MCP startup

The preferred installation acceptance check is the STDIO smoke command:

```bash
uv --directory backend run --locked --no-dev kgfegmcp-stdio-smoke
```

It launches the real server in a separate STDIO subprocess and verifies the public MCP
surface. A passing result establishes successful Python import and checks that the 
application can build accepted runtime state and complete an MCP handshake.

If you need package validation independently, inspect the validator CLI:

```bash
uv --directory backend run --locked --no-dev \
  kgfegmcp-validate-packages --help
```

The package validator checks manifests, profiles, checksums, declared artifacts,
identifiers, counts, capabilities, rights metadata, endpoints, and hierarchy topology
before packages enter the accepted runtime catalog.

## Start the server directly

You can launch the protocol-only server with:

```bash
uv --directory backend run --locked --no-dev \
  python -m kgfegmcp.mcpb_server
```

This command intentionally appears to wait. It is not an interactive shell or HTTP
server; it is waiting for an MCP client over STDIO.

!!! warning "STDOUT is protocol traffic"
    The STDIO transport reserves stdout for MCP JSON-RPC messages. Application logging
    must remain on stderr.

## Use the module launcher directly

Always use:

```text
python -m kgfegmcp.mcpb_server
```

Do not use:

```text
python src/kgfegmcp/mcpb_server.py
```

Direct file execution can place `src/kgfegmcp` at the front of `sys.path`. Because the
project contains an internal package named `kgfegmcp.mcp`, that path ordering can shadow
the external MCP SDK package named `mcp` and produce errors such as:

```text
No module named 'mcp.types'
```

## Useful local commands

Inspect the four installed project CLIs:

```bash
uv --directory backend run --locked --no-dev kgfegmcp-stdio-smoke --help
uv --directory backend run --locked --no-dev kgfegmcp-build-mcpb --help
uv --directory backend run --locked --no-dev kgfegmcp-build-manifest --help
uv --directory backend run --locked --no-dev kgfegmcp-validate-packages --help
```

Maintainers with the development dependencies installed can also run the repository's
optional quality commands, including Ruff, Black, isort, Pylint, and mypy. The complete
acceptance and development workflow is documented under [Development](../development/index.md).

## Optional MCPB tooling

Node.js, npm, and the official MCPB CLI are required only when building the optional
bundle:

```bash
npm install -g @anthropic-ai/mcpb
```

The normal local STDIO workflow does not require them. See
[MCPB packaging](../operations/mcpb.md) for bundle construction and staged-runtime
acceptance.

## Installation troubleshooting

### `kgfegmcp-stdio-smoke` reports `Connection closed`

First synchronize the locked runtime again:

```bash
uv --directory backend sync --locked --no-dev
uv --directory backend run --locked --no-dev kgfegmcp-stdio-smoke
```

If the failure remains, inspect the child-process traceback. Common causes include an
incorrect launch mode, invalid repository path overrides, missing graph-package inputs,
or a dependency environment that is not synchronized with the lock file.

### `No module named 'mcp.types'`

Confirm that every launch surface uses the module form:

```text
python -m kgfegmcp.mcpb_server
```

### The server starts but appears idle

That is expected when the module is started manually. The process waits for MCP protocol
messages over STDIO. Use `kgfegmcp-stdio-smoke` to test it without a desktop client.

---

**Next:** [Connect an MCP client](mcp-clients.md)
