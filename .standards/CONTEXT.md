# Project Context

## Project Baseline

- KGForEdGlobalMCP is a read-only Python MCP server (package `kgfegmcp`, version
  0.4.0) that serves curriculum knowledge-graph evidence for six accepted
  framework snapshots through 19 tools, nine prompts, one fixed resource and 14
  resource templates. Release version is tracked in
  `.release-please-manifest.json`, `backend/pyproject.toml` and
  `packaging/mcpb/manifest.json` (all `0.4.0`).
- The server runs locally over STDIO (`python -m kgfegmcp.mcpb_server`, launched
  by Claude Desktop through an absolute `uv` path or from an `.mcpb` bundle) and
  hosted over stateless Streamable HTTP (`python -m kgfegmcp.http_server`, root
  `Dockerfile`, `/health` route). The MCP surface is the same on both transports.
- This cycle is documentation-only: the user has reported new client testing and
  wants testing-status claims in the docs and READMEs brought in line with it.

## Stack and Tooling

- Python backend managed with `uv` (`backend/pyproject.toml`, `backend/uv.lock`).
- Documentation is MkDocs Material (`mkdocs.yml` at the repository root, sources
  in `docs/`, `docs` optional-dependency extra in `backend/pyproject.toml`). The
  site is deployed by `.github/workflows/docs.yml` (`mkdocs gh-deploy`) on push
  to `main` and on release.
- Pre-commit (`.pre-commit-config.yaml`) applies `check-yaml`,
  `end-of-file-fixer`, `trailing-whitespace` and `detect-secrets` repo-wide;
  Python linters apply only to `backend/(src|tests)`. No Markdown linter is
  configured for project docs.

## Structure and Boundaries

- `docs/getting-started/claude-clients.md` — client evidence page: the "What has
  and has not been checked" table, supported-routes table (claude.ai resource
  attachment and prompt visibility cells), known client limits, the Claude
  Desktop walkthrough with its "Run status" note and "Record your results"
  table, and the claude.ai remote acceptance checklist.
- `docs/getting-started/mcp-clients.md` — Claude Desktop on macOS setup, hosted
  connection and custom-connector steps, optional MCPB path, troubleshooting.
- `docs/operations/mcpb.md` — bundle build/smoke steps and the "Claude Desktop
  installation" section (install/enable steps, unverified UI detail, unverified
  same-version removal/reinstall procedure).
- `docs/operations/troubleshooting.md` — Desktop connector and `.mcpb`
  installation troubleshooting.
- `docs/guides/resources.md` — "Client support varies" section on host resource
  support.
- `docs/operations/deployment.md` — hosted deployment contract; uses the
  placeholder `https://<service-domain>/mcp`.
- `README.md`, `backend/README.md`, `packaging/mcpb/README.md` — top-level and
  package READMEs with Claude Desktop, hosted-server and MCPB passages.
- Out of bounds for this cycle per the user's request and the documentation
  contract: `backend/src/`, `backend/tests/`, `packaging/mcpb/manifest.json`,
  `config/`, `data/`, CI and other configuration.

## Commands

- `uv --directory backend run --locked mkdocs build --strict` — strict docs build
  (`docs/development/local-setup.md`). `docs/development/testing.md` gives the
  acceptance form: `uv --directory backend sync --locked --extra docs`, then
  `uv --directory backend run --locked mkdocs build --strict --config-file "$PWD/mkdocs.yml"`
  run from the repository root.
- `uv --directory backend run --locked mkdocs serve` — local docs preview.
- `uv --directory backend run --locked --no-dev kgfegmcp-http-smoke --url https://<service-domain>/mcp`
  — documented hosted-endpoint smoke check.

## Conventions and Constraints

- Existing docs separate evidence classes explicitly: automated server/smoke
  checks, user client observations, and untested items, each with ISO dates
  (`2026-10-07`, `2026-10-03`). The remote checklist asks results to be recorded
  with date, endpoint, connector name, plan type and per-item results, "keeping
  server results, client observations and untested items separate".
- The docs repeatedly state that the manifest's `darwin`/`linux`/`win32`
  declaration is not installation or testing evidence, and that Windows and
  Linux Desktop setup is undocumented and untested.
- Hosted endpoint docs use the placeholder `<service-domain>`; no concrete
  hosted domain appears anywhere in tracked files.
- User constraint for this cycle: edit documentation and READMEs only; do not
  mark anything as tested beyond what the user reported; keep "untested" or
  "unverified" wording for anything the observations do not cover.
- IDinsight organization instructions: no credentials or secrets in outputs;
  professional, accessible tone; avoid AI-sounding prose.

## External Systems and Data

- Hosted service: per explicit user input, a public deployment runs server
  version 0.4.0 at `kg-for-ed-global-mcp.up.railway.app` with path `/mcp`. The
  endpoint is unauthenticated (`docs/operations/deployment.md`). This audit did
  not contact it.
- Claude Desktop (local STDIO or `.mcpb` extension) and claude.ai custom
  connectors (remote, connecting from Anthropic's cloud) are the client surfaces
  the docs describe.

## Testing and Verification Baseline

- Documented, pre-cycle evidence (in `docs/getting-started/claude-clients.md`):
  automated offline tests and STDIO/Streamable HTTP smoke checks of 0.4.0 passed
  locally on 2026-10-07; an unpacked 0.4.0 bundle STDIO smoke passed 2026-10-07;
  walkthrough tool calls replayed in-process on 2026-10-07; a 2026-10-03 user
  observation of an earlier Desktop build (six frameworks, nine prompts, Catalog
  resource attached, resource menu offered only Catalog and could not find a
  progression link).
- New explicit user observations, all 2026-10-08, not yet reflected in docs:
  1. Claude Desktop, server 0.4.0, macOS, through both the checkout
     configuration and the `.mcpb` bundle: connector starts, frameworks listed,
     prompts and resources appear, all workflows tested, no failures observed.
  2. Public deployment verified at `kg-for-ed-global-mcp.up.railway.app`, path
     `/mcp`, running 0.4.0.
  3. claude.ai custom connector: same results as the Claude Desktop testing.
  4. Not tested: Windows and Linux setups.
- Documentation checks available: the strict MkDocs build above. There is no
  automated check of testing-status wording.

## Relevant Existing Behavior

- Claims currently stating 0.4.0 Desktop, bundle or claude.ai use is untested,
  not run, or not checked (user-named locations confirmed present):
  `docs/getting-started/claude-clients.md` lines 16, 18, 19, 21–28, 36, 38,
  71–74, 81, 279–282, 289–291; `docs/getting-started/mcp-clients.md` lines
  45–49, 219–221, 266, 290; `docs/operations/mcpb.md` lines 289–292, 308–311,
  313–315, 336–343, 356; `docs/operations/troubleshooting.md` lines 215,
  374–376; `docs/guides/resources.md` lines 265–268.
- Related README claims: `README.md:187` and `README.md:336-338`,
  `backend/README.md:350-351`, and `packaging/mcpb/README.md:256-261` call manual
  `claude_desktop_config.json` registration "the confirmed local connection
  method" and say custom `.mcpb` installation may vary by build (some builds
  leave **Install** disabled). None of the three READMEs states that 0.4.0 is
  untested.
- `docs/guides/prompts.md:337-344` describes Desktop prompt behavior and the
  `get_workflow_instructions` fallback without a tested/untested claim.
- Items the existing docs mark unverified that the user's observations do not
  explicitly address: same-version bundle removal/reinstall behavior
  (`mcpb.md` 336–343, `mcp-clients.md` 288–290, `claude-clients.md` 79–81), the
  exact extension label and enable control (`mcpb.md` 308–311), the
  organization-managed allowlist route, and `uv` provisioning by the bundle
  (`mcpb.md` "Where does the bundle get uv?").

## Known Unknowns

- Meaning of "all workflows were tested": whether it covers all nine prompt
  workflows, the walkthrough steps 1–13 (including composed answers in steps
  11–13), or both. Affects how the walkthrough results table and the "no
  end-to-end teaching workflow" sentence may be updated. For Scoper to settle.
- Whether "prompts and resources appear" in claude.ai means server resources can
  be attached from the claude.ai interface and prompts are offered in its
  picker, which are the two open questions on `claude-clients.md` lines 36 and
  38.
- Whether the 2026-10-08 Desktop testing changes the 2026-10-03 observation that
  the resource menu listed only Catalog and could not find a progression link.
- How the public deployment was verified (for example `kgfegmcp-http-smoke`,
  connector use, or both), and the Claude Desktop app version, claude.ai plan
  type and connector name used; the remote checklist asks for these.
- Whether the concrete Railway domain should appear in project docs, given the
  current placeholder convention and the deployment page's advice to treat the
  public domain as permanent.

## Evidence

- `.standards/STATE.md` `Active Work.Request` — the user's request, editing
  boundary and 2026-10-08 observations.
- `docs/getting-started/claude-clients.md`, `docs/getting-started/mcp-clients.md`,
  `docs/operations/mcpb.md`, `docs/operations/troubleshooting.md`,
  `docs/guides/resources.md`, `docs/operations/deployment.md` — current claims.
- `README.md`, `backend/README.md`, `packaging/mcpb/README.md` — README claims.
- `mkdocs.yml`, `.github/workflows/docs.yml`, `docs/development/local-setup.md`,
  `docs/development/testing.md` — docs build and deployment.
- `backend/pyproject.toml`, `packaging/mcpb/manifest.json`,
  `.release-please-manifest.json` — version 0.4.0 and declared platforms.
- `backend/src/kgfegmcp/http_server.py` — hosted entry point and `/health` route.
- `git grep -i railway` — no tracked file names the hosted domain.
