# Local development

This page describes a repository-local development environment for the Python backend
and documentation site.

## Prerequisites

The backend declares:

- Python `>=3.13,<3.14`;
- `uv` for interpreter and locked dependency management; and
- FastMCP `3.4.4` as a pinned runtime dependency.

Install Python 3.13 through `uv`:

```bash
uv python install 3.13
```

Node.js/npm is only required for building an MCPB distribution with the official MCPB
CLI.

## Synchronize the backend

From the repository root, install runtime plus development dependencies:

```bash
uv --directory backend sync --locked --extra dev
```

To install the documentation dependencies in the same environment as well:

```bash
uv --directory backend sync --locked --extra dev --extra docs
```

The project does not require manually activating a virtual environment when commands are
run through `uv`.

!!! note "The lockfile is part of the development contract"
    Repository commands use `--locked`, and the MCPB build stages `uv.lock`. If
    `backend/uv.lock` is missing from a checkout, restore or intentionally regenerate it
    before treating the environment as reproducible.

## Repository-local configuration

For the ordinary repository layout, the backend can derive `config/` and `data/` from
the project root. Explicit environment variables are useful when launching from desktop
clients, testing alternate fixture roots, or isolating package experiments.

A complete local override looks like:

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

`BackendSettings` reads process environment values; the Python application does not
automatically discover a repository `.env` file.

For exact configuration behavior, see [Environment variables](../operations/configuration.md).

## Verify imports before protocol testing

A fast syntax/import sanity check is useful before launching the MCP server:

```bash
uv --directory backend run --locked python -m compileall src/kgfegmcp
```

The repository's ordinary server entry point is module based:

```bash
uv --directory backend run --locked --no-dev \
  python -m kgfegmcp.mcpb_server
```

Do **not** execute:

```text
python backend/src/kgfegmcp/mcpb_server.py
```

Direct filesystem execution can put `src/kgfegmcp` at the front of `sys.path`, allowing
the internal `kgfegmcp.mcp` package to shadow the external MCP SDK package named `mcp`.

The server is not an interactive shell. It waits for an MCP client and reserves stdout
for protocol traffic.

## Run the repository STDIO smoke

Use the smoke command as the quickest end-to-end backend verification:

```bash
uv --directory backend run --locked --no-dev kgfegmcp-stdio-smoke
```

It launches the actual module entry point in a separate process, completes the MCP
handshake, verifies the fixed inventory, reads representative resources, and requires a
clean shutdown.

See [Testing and acceptance](testing.md) for the full acceptance sequence.

## Development quality tools

The `dev` extra includes Black, Ruff, isort, pylint, mypy, pytest and related testing
plugins, interrogate, pre-commit, and detect-secrets.

The backend README lists these optional quality commands:

```bash
uv --directory backend run --locked ruff check .
uv --directory backend run --locked black --check .
uv --directory backend run --locked isort --check-only .
uv --directory backend run --locked pylint src/kgfegmcp
uv --directory backend run --locked mypy src/kgfegmcp
```

`backend/pyproject.toml` additionally configures:

- Black and Ruff at line length 88;
- Ruff for Python 3.13;
- mypy with `disallow_untyped_defs = true` and the Pydantic plugin;
- interrogate at 100% docstring coverage, excluding `__init__.py`; and
- pytest with asyncio auto mode and `tests/` as the test root.

When changing formatting, prefer running the formatter intentionally rather than
hand-editing around formatter output:

```bash
uv --directory backend run --locked black .
uv --directory backend run --locked isort .
```

Then rerun the corresponding check commands.

## Tests

The project configuration expects tests beneath `backend/tests/`:

```bash
uv --directory backend run --locked pytest
```

For coverage:

```bash
uv --directory backend run --locked pytest --cov=kgfegmcp --cov-report=term-missing
```

The supplied repository snapshot used to prepare these docs did not contain the
`backend/tests/` directory, although `pyproject.toml` and the backend README both define
it as part of the intended layout. In a checkout without tests, do not treat a missing
test suite as a passing test run; rely on the available static, package-validation, and
STDIO acceptance checks and record the gap explicitly.

## Work with temporary package fixtures

The six repository graph packages are terminal positive baselines. Do not modify them in
place to test invalid or destructive package behavior.

Instead:

1. copy the relevant package/profile inputs to a temporary root;
2. point `KGFEGMCP_GRAPH_PACKAGES_ROOT` and, if needed, `KGFEGMCP_PROFILE_ROOT` at the
   temporary fixture tree;
3. exercise the validator or bootstrap behavior there; and
4. discard the fixture after the test.

This keeps accepted package bytes and checksums meaningful.

## Build the documentation locally

After installing the `docs` extra, run MkDocs from the repository root:

```bash
uv --directory backend run --locked mkdocs serve
```

For a strict build:

```bash
uv --directory backend run --locked mkdocs build --strict
```

The current MkDocs configuration also enables the `panzoom` plugin for Mermaid diagrams,
so new diagrams should use ordinary fenced Mermaid blocks rather than custom HTML
wrappers. The `docs` optional-dependency list in the supplied backend project metadata
does not yet name the package that provides `panzoom`; make sure that plugin dependency
is added to the locked documentation environment before relying on the commands above.

## Optional MCPB development loop

Install the external MCPB CLI when working on packaging:

```bash
npm install -g @anthropic-ai/mcpb
```

Retain a staging tree and smoke that exact tree:

```bash
rm -rf ./dist/kgfegmcp-stage

uv --directory backend run --locked --no-dev kgfegmcp-build-mcpb \
  --stage-output ./dist/kgfegmcp-stage

uv --directory backend run --locked --no-dev kgfegmcp-stdio-smoke \
  --bundle-root ./dist/kgfegmcp-stage
```

See [MCPB packaging](../operations/mcpb.md) for the distribution contract.

## Logging while developing STDIO

Avoid uncontrolled `print()` calls in runtime paths. STDIO stdout belongs to MCP
JSON-RPC traffic. Application and FastMCP diagnostics must remain on stderr.

If a smoke test reports a closed connection, inspect the child-process stderr/traceback
before changing protocol code; startup configuration or package validation is often the
actual failure.

## Suggested local loop

```text
edit
  -> targeted tests/static checks
  -> package validation if data/config changed
  -> kgfegmcp-stdio-smoke
  -> mkdocs build --strict if docs changed
  -> MCPB stage + stage smoke if packaging changed
```

---

**Next:** [Add or update a framework](framework-package.md)
