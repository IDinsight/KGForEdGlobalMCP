<!-- STANDARDS
Artifact: ARCHITECTURE
Cycle: document-local-claude-desktop-setup-for-20261008T004926Z-6feb67d3
-->

# Technical Design: local Claude Desktop setup documentation (0.4.0)

## Context

This is a `DOCUMENTATION` cycle. The scope
(`.standards/docs/scope/document-local-claude-desktop-setup-for-20261008T004926Z-6feb67d3.md`)
asks Documenter to close seven gaps in the local Claude Desktop setup docs, editing only
existing files under `docs/`. Nothing here changes behavior. This design records the
existing technical facts each fix must agree with, where they come from, and which
claims the repository cannot support. Facts were re-read from the working tree at
`89c9f4c` on `tz6/doc-updates` on 2026-10-07; `docs/`, code, manifest and data match
`fed4ad4` on `main` (`.standards/CONTEXT.md`).

## Decision

Documenter works from the facts below. Where a fact comes only from an existing guide,
or from outside the repository, it is marked as such. Documenter must cite it, label it
unverified, or name it as a known unknown. Three findings change how the scope's items
should be written:

1. **The outer smoke command syncs the environment itself.** `uv run` creates and
   updates the project environment before it runs a command, unless `--no-sync` is
   passed (uv's documented behavior; not run in this checkout during Architecture).
   Only the child server launch inside the smoke test uses `--offline`. "The smoke test
   fails unless you ran `uv sync` first" is therefore not established for the
   repository smoke. See *Data and Control Flow*. This bears on `AC-010`.
2. **A JSON check without `jq` works with the project's Python.**
   `python -m json.tool <file> > /dev/null` with the project's Python 3.13 exits 0 on
   valid JSON and 1 on invalid JSON. macOS `plutil -lint` does not parse JSON and must
   not be offered. This bears on `AC-007`.
3. **The checkout holds an 11 GB folder that a fresh clone does not.**
   `data/source_artifacts/` is git-ignored (`.gitignore` line 21) and holds about 11 GB
   locally. A plain `du` of the checkout overstates what a reader needs. This bears on
   `AC-006`.

## Acceptance Coverage

- `AC-001`: The repository has no evidence for Desktop's install, enable or remove
  steps for custom extensions (see *Interfaces and Contracts*, Claude Desktop). The
  existing claim in `docs/operations/mcpb.md` lines 284-286, that Desktop "may keep the
  old copy" of a same-version bundle, also has no repository source. Each new step needs
  an external Anthropic or MCPB citation or an "unverified" label.
- `AC-002`: No architectural impact. Satisfaction depends on Documenter asking the user
  and recording the question and outcome.
- `AC-003`: The manifest and builder fix the launch command as a bare `uv` with
  `server.type` `uv`. The repository does not establish whether Desktop supplies `uv`
  (see *Interfaces and Contracts*, Bundle runtime).
- `AC-004`, `AC-005`: Platform facts are under *Interfaces and Contracts*, Operating
  systems: the manifest declares three platforms, nothing checks or tests them, and
  every Desktop-specific instruction in the docs is macOS-only.
- `AC-006`: The disk components and their runtime roles are under *Interfaces and
  Contracts*, Disk footprint. Documenter must take the figures from a fresh measurement.
- `AC-007`: The `jq` uses and the verified alternative are under *Interfaces and
  Contracts*, Config JSON check.
- `AC-008`: The run-on is at `docs/getting-started/mcp-clients.md` line 172:
  ``Use `python -m kgfegmcp.mcpb_server` intact Launching ...``. The intended meaning
  (keep the module launcher; running the file by path can shadow the `mcp` SDK) matches
  `docs/operations/mcpb.md` lines 81-85.
- `AC-009`: The 0.4.0 output strings come from code (see *Interfaces and Contracts*,
  Old-copy signal). The new entry belongs under `## Troubleshooting` in
  `docs/getting-started/mcp-clients.md` (lines 252-283). Its remedy must agree with
  `docs/getting-started/claude-clients.md` lines 70-74 and `docs/operations/mcpb.md`
  lines 284-288.
- `AC-010`: The offline launch and its consequences are under *Data and Control Flow*.
- `AC-011`: The table is `docs/getting-started/claude-clients.md` lines 12-18. Server
  and bundle-stage smoke passes are dated 2026-10-07. Desktop 0.4.0 is "Prepared; not
  yet run in Desktop". No row covers bundle installation in Desktop, and no row names an
  operating system.
- `AC-012`: The checkout launch contract is under *Interfaces and Contracts*, Checkout
  launch contract.
- `AC-013`: The docs build contract is under *Interfaces and Contracts*, Docs build.
- `AC-014`: No architectural impact. Documenter's editing boundary, checked against
  `57f8036` with `git diff --name-only 57f8036 --` while excluding `.standards/`.

## Interfaces and Contracts

### Checkout launch contract (`AC-012`)

- Source of truth: `packaging/mcpb/manifest.json` lines 25-51, which
  `_validate_manifest_server` in `backend/src/kgfegmcp/cli/build_mcpb.py` (about lines
  666-706) enforces exactly. The rules are `server.type == "uv"`,
  `mcp_config.command == "uv"`, fixed args, fixed env, and no other `mcp_config`
  fields.
- Manifest args: `run --directory ${__dirname} --locked --no-dev python -m
  kgfegmcp.mcpb_server`. The checkout JSON (`docs/getting-started/mcp-clients.md`
  lines 73-101) writes `--directory <repo>/backend run --locked --no-dev python -m
  kgfegmcp.mcpb_server`. uv accepts `--directory` before or after `run`, so the two
  are equivalent. The checkout uses `backend/` because that is where `pyproject.toml`
  lives in a checkout, while a bundle has it at the root.
- Env: nine keys. Six are paths: `KGFEGMCP_CONFIG_ROOT` (`config`),
  `KGFEGMCP_DATA_ROOT` (`data`), `KGFEGMCP_GRAPH_PACKAGES_ROOT` (`data/graph_packages`),
  `KGFEGMCP_PROFILE_ROOT` (`config/profiles`), `KGFEGMCP_PROMPT_ROOT`
  (`config/prompts`), and `PATHS_PROJECT_DIR` (the root itself). Three are fixed:
  `KGFEGMCP_ENV=local`, `KGFEGMCP_INVALID_PACKAGE_POLICY=fail`,
  `KGFEGMCP_LOG_LEVEL=INFO`. `${__dirname}` (the bundle root) maps to the repository
  root, not `backend/`. `stdio_smoke.py` `_stdio_environment` builds the same mapping
  from the project root.
- The current JSON matches this contract. Edits near it must not change the command,
  args, key set or fixed values.

### Bundle runtime (`AC-003`, `AC-001`)

- The bundle launches a bare `uv` (`manifest.json` line 38) and the builder rejects any
  other command. The bundle ships no virtual environment: `docs/operations/mcpb.md`
  lines 32-39 and the staging code exclude `.venv` and caches. So whatever runs the
  bundle must find `uv`, and a Python 3.13 environment must be created from
  `pyproject.toml` and `uv.lock` on or before first launch.
- No repository evidence says whether Claude Desktop ships or installs `uv` for
  `server.type: uv`, which `PATH` it uses to resolve a bare `uv`, or whether first
  launch needs network access. `packaging/mcpb/README.md` lines 65-66 ("the UV runtime
  manages the project environment") is about the Python environment, not the `uv`
  binary, and is outside the editing boundary.
  `docs/getting-started/mcp-clients.md` lines 64-65 already warn that desktop apps may
  not inherit the shell `PATH`. That is consistent with the risk, but it was written
  for the checkout config and is not evidence about bundles.
- `uv` and the MCPB CLI are listed as prerequisites for *building* the bundle
  (`docs/operations/mcpb.md` lines 41-58). That says nothing about installing it.
- A statement that Desktop supplies `uv`, or does not, needs an external Anthropic or
  MCPB source. Otherwise it is an open question.

### Claude Desktop (`AC-001`, `AC-004`, `AC-005`)

- Documented locations, all macOS-only: config
  `~/Library/Application Support/Claude/claude_desktop_config.json`
  (`docs/getting-started/mcp-clients.md` lines 42-48), logs `~/Library/Logs/Claude`
  (lines 264-272; `docs/operations/troubleshooting.md` lines 221-229), and restart with
  `osascript -e 'quit app "Claude"'` (`mcp-clients.md` lines 119-123). The repository
  has no Windows or Linux equivalents.
- Install, enable and remove steps for custom extensions are absent from the
  repository on every OS.

### Operating systems (`AC-004`, `AC-005`)

- `manifest.json` lines 6-11 declare `darwin`, `linux`, `win32`. The builder does not
  read or validate `compatibility.platforms`: no match in `backend/src`. CI does not
  run Desktop. The list is a declaration only.
- The checkout steps also assume a POSIX shell (`command -v uv`, `pwd`, `$HOME`,
  `find`). On Windows, JSON paths need escaped backslashes and the `uv` executable name
  differs. Any such instruction needs a cited source and an "untested" label under
  `AC-005`.
- The dated evidence in `claude-clients.md` does not record an operating system. The
  Architect session ran on macOS 26.6.2, but that does not show where the 2026-10-07
  smokes ran. Documenter should say "tested on macOS" only with evidence that names it.

### Disk footprint (`AC-006`)

| Component | Role | Evidence |
|---|---|---|
| `data/graph_packages/` (tracked) | Loaded by the server; staged into the bundle; in the Docker image | `KGFEGMCP_GRAPH_PACKAGES_ROOT`; `build_mcpb.py` `_stage_bundle` (about lines 489-560); `docs/operations/deployment.md` lines 35-50 |
| `data/input_artifacts/` (tracked) | Not loaded by the server, not in the bundle or image. Referenced only by the package-preparation tool as a protected tree it must not overwrite. | `normalization.py` line 872 (`_validate_output`); `deployment.md` lines 48-50 |
| Other tracked files, including `dist/kgfegmcp-0.1.0.mcpb` (about 13 MB, `CONTEXT.md`) | Code, config, docs, an old bundle | `git ls-files` |
| `.git` history | Comes with any full clone; a fresh clone's pack may differ from a long-lived local one | `git count-objects -vH` (`size-pack`) |
| `backend/.venv` | Runtime environment from `uv sync --locked --no-dev`. The local one may include the `dev` or `docs` extras. | `backend/pyproject.toml` lines 149-178 |
| uv cache and uv-managed Python 3.13 | Outside the checkout; created by `uv python install` and `uv sync` | `uv cache dir`, `uv python dir` |
| `data/source_artifacts/` | **Git-ignored, local only, about 11 GB here; not in a fresh clone; exclude it** | `.gitignore` line 21; `du -sh` on 2026-10-07 |

- Measure tracked-file sizes from `git ls-files`, not `du` of the working tree, which
  would count `data/source_artifacts/`, `.venv` and other ignored files.
- A runtime-only environment size needs a `--no-dev` environment or must be labelled
  unmeasured or approximate. A fresh-clone size needs an actual clone or must be
  labelled as possibly different.
- `.gitattributes` does not exist, so Git LFS is not used and a clone downloads all
  tracked data.

### Config JSON check (`AC-007`)

- `jq` checks of `claude_desktop_config.json` appear at
  `docs/getting-started/mcp-clients.md` lines 111-113 and 260, and
  `docs/operations/troubleshooting.md` lines 215-219. `jq` is in no prerequisites list.
  `docs/operations/mcpb.md` lines 233 and 239 also use `jq`, to inspect the packed
  manifest. That is not a config check, so it is outside `AC-007`, but `jq` is missing
  from that page's prerequisites too (lines 41-58). Fixing it is Documenter's call
  within the boundary.
- Verified on 2026-10-07 with `backend/.venv/bin/python -m json.tool <file> > /dev/null`
  (Python 3.13.9): a valid file exits 0 with no output; a file with a trailing comma
  exits 1 and prints `Illegal trailing comma before end of object: line 1 column 7
  (char 6)` to stderr.
- The reader-facing form through uv, `uv --directory backend run --locked --no-dev
  python -m json.tool "<config path>" > /dev/null`, was not run here because the
  sandbox blocked uv's cache. `AC-007` requires Documenter to show the form it
  publishes works. The path has spaces, so it must be quoted. `json.tool` echoes the
  JSON to stdout unless redirected.
- `plutil -lint` on macOS rejects valid JSON (`Unexpected character {`, exit 1). Do not
  offer it.

### Old-copy signal (`AC-009`)

- 0.4.0 emits `Routing graph types:` and `Included graph types:`
  (`backend/src/kgfegmcp/mcp/tools/frameworks.py` lines 131-135, `capabilities.py`
  lines 69-70 and 130). They were introduced in `e02dad6` (learning-progression
  support). The single `Graph types:` line from older builds comes from the existing
  guides only.
- Existing remedy text: remove the extension and reinstall the bundle, or, for a
  config-file setup, fully quit and reopen Desktop (`claude-clients.md` lines 70-74;
  `mcpb.md` lines 284-288). The bundle remedy shares `AC-001`'s missing source for
  Desktop's remove and install behavior.

### Docs build (`AC-013`)

- From `backend/` with the `docs` extra: `.venv/bin/mkdocs build --strict
  --config-file ../mkdocs.yml --site-dir <temp dir>`. Strict mode fails on broken
  internal links and anchors. The build passed on 2026-10-07 with only an upstream
  mkdocs-material notice (`CONTEXT.md`).
- `mkdocs.yml` has an explicit `nav` and is outside the boundary, so all content goes
  in the existing pages listed under getting-started and operations.

## Data and Control Flow

`kgfegmcp-stdio-smoke` (`AC-010`):

1. The reader runs `uv --directory backend run --locked --no-dev kgfegmcp-stdio-smoke`.
   This outer `uv run` is not offline. By uv's documented default it creates or updates
   `backend/.venv` from `uv.lock`, downloading if needed, before it runs the CLI.
2. The CLI starts the server as a child process with `uv run --directory <runtime root>
   --locked --no-dev --offline python -m kgfegmcp.mcpb_server`
   (`backend/src/kgfegmcp/cli/stdio_smoke.py` lines 128-143). `--offline` stops this
   child launch from fetching anything.
3. Repository mode: the runtime root is `backend/`, which step 1 just synced, so the
   offline child finds everything. Bundle mode (`--bundle-root <stage>`): the runtime
   root is the stage (`_runtime_paths`, lines 160-181). The child must build the
   stage's environment offline from the local uv cache, which an earlier sync of the
   same lock filled.

What follows: the smoke needs the dependencies already on the machine, either in the
synced environment or in the uv cache. That is why the docs run `uv sync` first. For the
repository smoke, step 1 already syncs, so a separate `uv sync` is not strictly
required. That rests on uv's documented default and was not observed here. A machine
with no network and an empty cache fails at step 1. Any `AC-010` explanation should say
that the child launch is offline and relies on packages already installed. It should
not claim that skipping `uv sync` alone breaks the repository smoke, unless Documenter
shows that it does.

## Technical Acceptance Criteria

- `AC-001`, `AC-003`, `AC-005`: Claims about how Claude Desktop behaves (install,
  enable, remove, `uv` provisioning, non-macOS paths) carry an external citation or an
  unverified, untested or open-question label. None is presented as following from
  repository code.
- `AC-004`: The docs separate the manifest's declared platforms from the operating
  systems the steps were written for and tested on. Any tested-on claim names evidence
  that records the OS.
- `AC-006`: Published figures separate `data/graph_packages` from
  `data/input_artifacts`. They exclude the git-ignored `data/source_artifacts`. They
  are based on tracked-file sizes, and they state whether the environment, history and
  uv cache or Python figures were measured or estimated.
- `AC-007`: Any non-`jq` check is a command shown to exit 0 on valid and non-zero on
  invalid JSON, with the path quoted. `plutil -lint` is excluded.
- `AC-009`: The entry uses the exact strings `Graph types:`, `Routing graph types:` and
  `Included graph types:`.
- `AC-010`: Any added explanation agrees with the control flow above.
- `AC-012`: The command, the args (in checkout order), the nine env keys and the three
  fixed values match the contract above, and path values map to the repository root.
- `AC-013`: The strict build passes with no new warnings from changed pages.

## Risks and Follow-up

- External sources may be unreachable or may not cover `uv` provisioning or Linux.
  Labelled unknowns satisfy the scope, so this does not block.
- Root `README.md` and `packaging/mcpb/README.md` repeat the `jq` and Desktop text and
  will drift from `docs/`. They are a scope non-goal and should be recorded as an
  observation only.
- `AC-007` and `AC-010` depend on uv commands that the Architect sandbox could not run.
  Documenter must run them outside that limit.
