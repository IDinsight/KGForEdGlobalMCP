# Project Context

## Project Baseline

- KGForEdGlobalMCP is a read-only, curriculum-agnostic FastMCP server (package
  `kgfegmcp`, version 0.4.0) that exposes six accepted curriculum graph packages to MCP
  hosts. The host does all reasoning; the server calls no LLM.
- Two transports share one MCP surface: local STDIO (launched by an MCP host as a child
  process) and hosted Streamable HTTP at `/mcp`. The fixed public inventory is 19 tools,
  1 fixed resource, 14 resource templates and 9 prompts.
- Local entry point is always `python -m kgfegmcp.mcpb_server`
  (`backend/src/kgfegmcp/mcpb_server.py` only calls `create_mcp().run(transport="stdio")`).
  Running the file by path can let `kgfegmcp.mcp` shadow the external `mcp` SDK
  (`No module named 'mcp.types'`); every doc repeats this warning.
- The repository can build an MCP Bundle (`.mcpb`) for Claude Desktop's custom-extension
  flow. Manual registration in `claude_desktop_config.json` is what the docs call the
  "confirmed" local path; bundle install in Desktop is described as build-dependent.
- Branch `tz6/doc-updates` differs from `main` (`fed4ad4`, the commit the request cites)
  only by STANDARDS installation files and `AGENTS.md`/`CLAUDE.md` additions; `docs/`,
  code, manifest and data are identical to `fed4ad4`.

## Stack and Tooling

- Python `>=3.13,<3.14` (`backend/pyproject.toml`), managed with `uv`; lock file
  `backend/uv.lock` is part of the run and packaging contract (`--locked`).
- Runtime extras: none needed; `dev` extra holds lint/test tools; `docs` extra holds
  MkDocs, mkdocs-material, glightbox, open-in-new-tab and panzoom plugins.
- Docs: MkDocs Material, config at repository-root `mkdocs.yml` with explicit `nav`,
  `use_directory_urls: false`, Mermaid via `pymdownx.superfences`, admonitions
  (`!!! note|warning|important`).
- MCPB tooling (only for building bundles): Node.js, npm, `npm install -g
  @anthropic-ai/mcpb`.

## Structure and Boundaries

- `docs/` — the editing boundary for this cycle. Relevant pages:
  `docs/getting-started/index.md` (Quickstart, prerequisites table),
  `docs/getting-started/local-installation.md`, `docs/getting-started/mcp-clients.md`
  (Claude Desktop on macOS, generic STDIO contract, hosted connection, troubleshooting),
  `docs/getting-started/claude-clients.md` ("What has and has not been checked" table,
  Desktop walkthrough, claude.ai checklist), `docs/operations/mcpb.md` (bundle build;
  "Claude Desktop installation" section), `docs/operations/troubleshooting.md`
  ("Desktop connector does not appear"), `docs/operations/deployment.md`
  ("What the image contains").
- Outside the boundary but carrying overlapping Claude Desktop/MCPB setup text:
  root `README.md` (prerequisites, "Connect Claude Desktop" with the same JSON, `jq` and
  `osascript` steps) and `packaging/mcpb/README.md` (also links a nonexistent
  `instructions.md`). Edits there are not authorized by the current request.
- `packaging/mcpb/manifest.json` — MCPB manifest template (read-only this cycle).
- `backend/src/kgfegmcp/cli/` — CLIs referenced by docs (`stdio_smoke.py`,
  `build_mcpb.py`, `http_smoke.py`, `validate_packages.py`, `build_manifests.py`,
  `prepare_learning_progressions.py`).
- `data/graph_packages/` — accepted packages loaded by the server and staged into the
  bundle. `data/input_artifacts/` — source/preparation inputs; not loaded at runtime,
  not staged into the bundle (`build_mcpb.py` stages only `data/graph_packages`), not in
  the Docker image.
- `config/profiles/`, `config/prompts/` — six versioned profiles and prompt configs.
- `dist/kgfegmcp-0.1.0.mcpb` — a tracked 13 MB bundle from an older version; no 0.4.0
  bundle exists in the checkout. Root `.gitignore` does not ignore `dist/`.

## Commands

- `uv python install 3.13` — install the interpreter (documented).
- `uv --directory backend sync --locked --no-dev` — create the runtime environment
  (`--extra dev` for maintainers).
- `uv --directory backend run --locked --no-dev kgfegmcp-stdio-smoke` — launch the real
  server over STDIO and check the inventory; add `--bundle-root <stage>` for a retained
  stage.
- `uv --directory backend run --locked --no-dev kgfegmcp-build-mcpb` — build
  `dist/kgfegmcp-0.4.0.mcpb`; `--stage-output`, `--output`, `--mcpb-command` options.
- Docs build: from `backend/`, `.venv/bin/mkdocs build --strict --config-file
  ../mkdocs.yml --site-dir <tmp dir>` (needs the `docs` extra). Verified on 2026-10-07:
  builds cleanly in strict mode (only an upstream mkdocs-material 2.0 notice). CI
  (`.github/workflows/docs.yml`) runs `mkdocs gh-deploy` on pushes to `main` without
  `--strict`; there is no PR-time docs check.
- `cd backend && make test` / `make lint` — backend tests and linters (not needed for
  docs-only work).

## Conventions and Constraints

- Request constraints (from `Active Work.Request`): edit only `docs/`; never claim
  something was tested without evidence; Desktop runs of 0.4.0 and bundle installs in
  Desktop are untested; keep the "What has and has not been checked" table accurate;
  external claims about Desktop need an Anthropic source or an "unverified" label.
- Docs voice: plain, second person, short imperative steps, dated evidence statements
  ("Passed locally, 2026-10-07"); separate server evidence from client observations.
- Each getting-started page ends with a `**Next:**` link; new pages must be added to
  `mkdocs.yml` `nav`.
- The checkout Desktop config in `docs/getting-started/mcp-clients.md` must keep: absolute
  `uv` path as `command`; args `--directory <repo>/backend run --locked --no-dev python -m
  kgfegmcp.mcpb_server`; nine `env` entries matching the manifest's `env` block (six
  paths plus `KGFEGMCP_ENV`, `KGFEGMCP_INVALID_PACKAGE_POLICY`, `KGFEGMCP_LOG_LEVEL`).
  The JSON holds eight `/absolute/path/...` placeholders (the `uv` path, the backend
  directory and six env paths). The request's "nine path replacements" matches neither
  count exactly; Scoper should state which count the acceptance check uses.
- Project agent instructions (`AGENTS.md`, `CLAUDE.md`) contain only the STANDARDS block.
- IDinsight org rules apply to generated text: no secrets, natural non-AI-sounding prose.

## External Systems and Data

- Claude Desktop: config file documented only at
  `~/Library/Application Support/Claude/claude_desktop_config.json`; logs at
  `~/Library/Logs/Claude`; restart via `osascript`. All are macOS-only.
- MCPB manifest (`packaging/mcpb/manifest.json`): `manifest_version` `0.4`,
  `server.type` `uv`, `mcp_config.command` bare `uv` with args `run --directory
  ${__dirname} --locked --no-dev python -m kgfegmcp.mcpb_server`, same nine env keys
  rooted at `${__dirname}`, `compatibility.platforms` `darwin`, `linux`, `win32`.
- Hosted deployment: Docker image with `backend/`, `config/`, `data/graph_packages/` only.

## Testing and Verification Baseline

- Backend tests: `backend/tests/` (pytest), run in CI by `.github/workflows/tests.yml`.
- `kgfegmcp-stdio-smoke` passes `--offline` to `uv run`
  (`backend/src/kgfegmcp/cli/stdio_smoke.py` line 137), so it cannot download packages and
  depends on an already-synced environment and uv cache.
- Evidence recorded in `docs/getting-started/claude-clients.md`: 0.4.0 server smoke and
  bundle-stage smoke passed locally 2026-10-07; Desktop 0.4.0 walkthrough not run;
  claude.ai untested.

## Relevant Existing Behavior

- Docs say Desktop shows `Routing graph types:` and `Included graph types:` lines per
  framework in 0.4.0; a single `Graph types:` line means an old copy
  (`claude-clients.md` lines 70-74; `mcpb.md` lines 284-288).
- `docs/operations/mcpb.md` "Claude Desktop installation" says remove an existing
  same-version extension before reinstalling, but gives no install, enable or remove
  steps.
- `jq empty` is the only JSON check offered (`mcp-clients.md` lines 111-113,
  `troubleshooting.md` lines 215-219, root `README.md`); `jq` is not in any
  prerequisites list.
- Typo present: `mcp-clients.md` line 172, "intact Launching".
- No disk-space figure appears in any prerequisites.

## Known Unknowns

- Whether Claude Desktop supplies `uv` for a `server.type: uv` bundle or requires a
  user-installed `uv` on `PATH`. No repository evidence settles it; the docs only say
  "the UV runtime manages the project environment". Needs an external Anthropic/MCPB
  source or must stay a stated unknown.
- Desktop's install, enable and remove steps for custom extensions on any OS. No
  repository evidence.
- Windows and Linux config file and log locations, and whether Desktop on Linux is
  supported. No repository evidence; the manifest's platform list is a declaration, not
  a test.
- Disk measurements on 2026-10-07 in this checkout: tracked files about 1,297 MB
  (`data/graph_packages` 641 MB, `data/input_artifacts` 641 MB), local git pack 281 MB,
  `backend/.venv` 321 MB. That venv may include dev/docs extras, so a runtime-only
  (`--no-dev`) size, uv cache and uv-managed Python sizes, a fresh-clone size, and the
  size of a 0.4.0 `.mcpb` and its installed footprint are not established.

## Evidence

- `.standards/STATE.md` — request, editing boundary and gaps.
- `mkdocs.yml`, `.github/workflows/docs.yml`, `backend/pyproject.toml` — docs build and
  Python constraints.
- `packaging/mcpb/manifest.json`, `packaging/mcpb/README.md`,
  `backend/src/kgfegmcp/cli/build_mcpb.py` — bundle runtime and staged contents.
- `backend/src/kgfegmcp/mcpb_server.py`, `backend/src/kgfegmcp/cli/stdio_smoke.py` —
  entry point and smoke `--offline` launch.
- `docs/getting-started/*.md`, `docs/operations/{mcpb,troubleshooting,deployment}.md`,
  `README.md` — current documentation claims.
- `du -sh`, `git count-objects -vH`, sum of `git ls-files` sizes — disk figures above.
- `mkdocs build --strict` to a temporary site directory — docs build baseline.
- `git diff --stat fed4ad4 HEAD` — branch differs from `main` only in workflow files.
