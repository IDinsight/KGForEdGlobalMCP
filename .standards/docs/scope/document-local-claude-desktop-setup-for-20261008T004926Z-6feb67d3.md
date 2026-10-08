<!-- STANDARDS
Artifact: SCOPE
Cycle: document-local-claude-desktop-setup-for-20261008T004926Z-6feb67d3
-->

# Local Claude Desktop setup documentation (0.4.0)

## Goal

Close the seven documentation gaps a Navigator review found on 2026-10-07 (at
`fed4ad4` on `main`) in the guide to running the 0.4.0 STDIO server locally in
Claude Desktop, both from a repository checkout and from the `.mcpb` bundle.

The readers are people setting the server up on their own machine (researchers,
analysts and developers who follow the getting-started pages) and maintainers who
build and install the bundle (`docs/operations/mcpb.md`). Today they hit missing
steps (installing the bundle in Desktop), unstated requirements (`uv`, `jq`, disk
space), an implicit macOS-only assumption, and a few small errors. After this
cycle, each gap is either fixed with cited evidence or named plainly as a known
unknown, and nothing in the docs claims a check that was not run.

Documenter choices saved in the request, to be carried forward unchanged:
collaboration `AUTONOMOUS`; target `VERTICAL_SLICE`, capability "local Claude
Desktop setup for the 0.4.0 STDIO server, from a checkout and from the mcpb
bundle"; user style `tony`.

## Constraints

- Edit only files under `docs/`. Do not change `mkdocs.yml`, code, `packaging/mcpb/manifest.json`, `backend/pyproject.toml`,
  `backend/uv.lock`, data or config. Because every page must be listed in the
  `mkdocs.yml` `nav`, which is outside the boundary, put new content in existing
  pages rather than adding pages.
- Never present something as tested without dated evidence. As of this cycle's
  start, Claude Desktop runs of 0.4.0 and bundle installs in Desktop are untested.
- Statements about Claude Desktop or MCPB behavior that the repository cannot
  establish need a cited external Anthropic (or MCPB project) source, or an
  explicit "unverified" label.
- Disk-space figures must come from a fresh measurement taken during this cycle,
  not from the figures in the request or in `.standards/CONTEXT.md`.
- Follow the existing docs voice: plain second person, short imperative steps,
  dated evidence statements, and server evidence kept apart from client
  observations. Each getting-started page keeps its `**Next:**` link.
- IDinsight writing rules apply: no secrets or real credentials, natural prose.

## Non-goals

- Editing the root `README.md` or `packaging/mcpb/README.md`, even though they
  repeat some of the same Desktop setup text (including the `jq` step). Any
  resulting mismatch is recorded as an observation, not fixed.
- Changing the manifest's declared platforms, the bundle's runtime, or any server
  behavior to match the docs.
- Running Claude Desktop, installing a bundle, or testing on Windows or Linux as a
  condition of this cycle. If the user supplies such observations, they may be
  recorded as dated evidence; their absence does not block completion.
- Building or committing a 0.4.0 `.mcpb`, or removing the tracked
  `dist/kgfegmcp-0.1.0.mcpb`.
- Rewriting unrelated sections of the touched pages.

## Work

### 1. Installing the bundle in Claude Desktop (gap 1)

**Intent:** Maintainers can already build the bundle, but the docs stop before
Desktop. They need the steps to get it running and to replace an older copy.

**Done when:**

- `AC-001`: The "Claude Desktop installation" section of
  `docs/operations/mcpb.md` tells the reader how to install a built `.mcpb` in
  Claude Desktop, how to enable it, and how to remove a previously installed copy
  before reinstalling a bundle with the same version number. Each of these steps
  either cites an external Anthropic or MCPB source or is labelled unverified.
- `AC-002`: After drafting those steps, the user was asked to review them, and the
  documentation record shows the question and the outcome. The published steps
  match that outcome: a step the user confirmed carries a dated observation, and
  any step without a source or confirmation stays labelled unverified.

**Depends on:** None.

### 2. Where a bundle gets `uv` (gap 2)

**Intent:** The manifest launches a bare `uv` command (`server.type` `uv`).
Readers need to know whether they must install `uv` themselves.

**Done when:**

- `AC-003`: The bundle documentation states whether Claude Desktop provides `uv`
  for a `uv`-type bundle or the user must install `uv` and make it findable, citing
  an external source for the answer. If no source settles it, the docs name it as
  an open question without asserting either answer.

**Depends on:** None.

### 3. Operating-system coverage (gap 3)

**Intent:** The checkout instructions use macOS-only paths and tools while the
manifest declares macOS, Linux and Windows. Readers on other systems need to know
where they stand.

**Done when:**

- `AC-004`: The local Desktop setup docs say plainly which operating systems the
  steps are written for and which have been tested, and make clear that the
  manifest's platform list is a declaration rather than evidence of testing.
- `AC-005`: Any Windows or Linux instructions in the touched pages (config file
  location, logs folder, restart, JSON check) cite a source and are labelled
  untested. No such instructions are added without a source.

**Depends on:** None.

### 4. Disk space (gap 4)

**Intent:** The checkout carries large data, and nothing warns readers how much
space they need.

**Done when:**

- `AC-006`: The prerequisites in `docs/getting-started/index.md` and
  `docs/getting-started/local-installation.md` give a disk-space estimate from a
  measurement taken during this cycle. The estimate distinguishes the graph
  packages the server needs from the input artifacts it does not load, and
  accounts for git history and the `uv` environment. Any part that was not
  measured is named as such, and figures that may differ (such as a fresh clone)
  say so. The documentation record holds the date, the commands used and the raw
  results.

**Depends on:** None.

### 5. Checking the config JSON without assuming `jq` (gap 5)

**Intent:** The docs tell readers to run `jq`, but `jq` is not listed anywhere as
something to install.

**Done when:**

- `AC-007`: Every place under `docs/` that tells the reader to check
  `claude_desktop_config.json` with `jq` (including
  `docs/getting-started/mcp-clients.md` and `docs/operations/troubleshooting.md`)
  either has `jq` listed in the relevant prerequisites or offers a check that
  works without `jq`. Any alternative check given is shown to work.

**Depends on:** None.

### 6. Small corrections and the old-copy check (gaps 6 and 7)

**Intent:** Fix a visible typo and put the "am I running an old copy?" check where
readers troubleshoot.

**Done when:**

- `AC-008`: The "intact Launching" run-on in
  `docs/getting-started/mcp-clients.md` is corrected.
- `AC-009`: The Troubleshooting part of `docs/getting-started/mcp-clients.md` has
  a short entry saying that a single `Graph types:` line, instead of separate
  `Routing graph types:` and `Included graph types:` lines, means Desktop is
  running an old copy, with what to do about it. Its wording agrees with the same
  check in `docs/getting-started/claude-clients.md` and `docs/operations/mcpb.md`.

**Depends on:** None.

### 7. Why the smoke test runs after `uv sync` (Documenter's judgment)

**Intent:** The smoke test calls `uv run` with `--offline`, so it fails if the
environment was never synced. The request leaves it to Documenter whether to say
so.

**Done when:**

- `AC-010`: Either the docs explain, where the smoke test is introduced, that it
  must run after `uv sync` because it runs `uv` offline, or the documentation
  record states why that explanation was not added.

**Depends on:** None.

### 8. Accuracy and integrity of the result

**Intent:** The fixes must not break what is already right or overstate what was
checked.

**Done when:**

- `AC-011`: The "What has and has not been checked" table in
  `docs/getting-started/claude-clients.md` is accurate after the cycle. It shows
  no new pass without dated evidence, and still lists Claude Desktop runs of 0.4.0
  and bundle installs in Desktop as not checked unless the documentation record
  holds evidence otherwise. Changes made under the other work items are reflected
  where the table covers them.
- `AC-012`: The macOS checkout configuration in
  `docs/getting-started/mcp-clients.md` still matches the code and manifest: the
  `command` is an absolute `uv` path; the args are `--directory`, the absolute
  `backend` path, `run`, `--locked`, `--no-dev`, `python`, `-m`,
  `kgfegmcp.mcpb_server`; and the `env` block has the same nine keys and fixed
  values as the manifest's `env` block, with each path value pointing at the
  matching absolute location in the checkout.
- `AC-013`: The docs build passes in strict mode
  (`mkdocs build --strict --config-file ../mkdocs.yml` from `backend/`, with the
  `docs` extra).
- `AC-014`: Compared with the cycle's starting commit, the project changes are
  confined to existing files under `docs/`, apart from STANDARDS workflow
  records.

**Depends on:** Work items 1–7.

## Assumptions

- The request's "nine path replacements" is read as the nine `env` entries that
  must match the manifest (`AC-012`). In the current JSON there are eight
  `/absolute/path/...` placeholders (the `uv` path, the `backend` directory and six
  env paths) and three fixed env values; `AC-012` checks the full set either way.
- External sources (Anthropic help pages, the MCPB project) may be reachable during
  documentation. If none can be reached, the affected statements stay labelled
  unverified or are named as known unknowns, which still satisfies `AC-001`,
  `AC-003` and `AC-005`.
- "Cycle's starting commit" in `AC-014` means `57f8036` on `tz6/doc-updates`, whose
  `docs/`, code, manifest and data match `fed4ad4` on `main`.
