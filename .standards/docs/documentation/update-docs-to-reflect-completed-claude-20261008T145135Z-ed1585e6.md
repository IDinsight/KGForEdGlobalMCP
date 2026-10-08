<!-- STANDARDS
Artifact: DOCUMENTATION
Cycle: update-docs-to-reflect-completed-claude-20261008T145135Z-ed1585e6
-->

# Documentation Record

`Cycle`: `update-docs-to-reflect-completed-claude-20261008T145135Z-ed1585e6` `Status`: `COMPLETE`
`Collaboration`: `AUTONOMOUS` `Target`: `ACTIVE_CHANGE` `Target Detail`:
`active cycle` `User Style`: `tony`

## Assessed Inputs and Boundary

- Cycle mode `DOCUMENTATION`, `CompletionPolicy: NONE`, no recovery or
  outstanding obligations. Branch `tz6/doc-updates`, HEAD `a16ac2e`.
- Contract and context (git blob ids, first 12 hex):
  - Scope `.standards/docs/scope/update-docs-to-reflect-completed-claude-20261008T145135Z-ed1585e6.md`
    `25fb50d62408` (current ACs: `AC-001`–`AC-006`, `AC-008`–`AC-011`,
    `AC-013`–`AC-017`; `AC-007` and `AC-012` retired, history only).
  - Technical design `.standards/docs/specs/update-docs-to-reflect-completed-claude-20261008T145135Z-ed1585e6.md`
    `3af9e632b592` (contracts I-1 to I-9, decisions 1–5).
  - Auditor context `.standards/CONTEXT.md` `04d713ed5467`.
- Behavior sources relied on through the design, not re-derived: I-1 version
  (`backend/pyproject.toml`, `packaging/mcpb/manifest.json`), I-2 transport
  (`backend/src/kgfegmcp/http_server.py`), I-3 smoke CLI, I-4 manifest facts.
  The user's 2026-10-08 observations come from `Active Work.Request` and the
  scope; no new client or endpoint test was run (scope non-goal).
- Baseline: project files were unchanged since `8df7879` (design I-9); later
  commits add only STANDARDS files. Pre-edit blob ids: `claude-clients.md`
  `dfc7497d96e1`, `mcp-clients.md` `c0d6a351b075`, `mcpb.md` `c26065de8642`,
  `troubleshooting.md` `0181ec11e36b`, `resources.md` `16e8c7c9b14d`,
  `deployment.md` `d3a342e0ad4f`, `cli.md` `ab3fad4be885`, `README.md`
  `53b5e22d2df9`, `backend/README.md` `72dc713d6d48`,
  `packaging/mcpb/README.md` `6cb6d328352c`. Working tree was clean at start.
- Editing boundary: Markdown under `docs/` plus the three READMEs. No code,
  tests, manifest, `config/`, `data/`, `mkdocs.yml`, CI or other configuration.
- Styles: `.claude/skills/documenter/styles/universal.md` and user style
  `.standards/user-styles/documenter/tony.md` (plain language, no jargon or
  filler). No technology style applies (Markdown prose only).
- This record and `STATE.md` are coordination files, not deliverable inputs.

## Documentation Work and Evidence

Saved deliverable identities (uncommitted working tree):

| File | Blob id | ACs |
|---|---|---|
| `docs/getting-started/claude-clients.md` | `ec024784453f` | `AC-001`–`AC-005`, `AC-009`, `AC-011`, `AC-017` |
| `docs/getting-started/mcp-clients.md` | `76717c04f889` | `AC-006`, `AC-009`, `AC-011` |
| `docs/operations/mcpb.md` | `adf6a65c7f0e` | `AC-015`, `AC-016`, `AC-011` |
| `docs/operations/troubleshooting.md` | `654815dd77fe` | `AC-008` |
| `docs/guides/resources.md` | `819974755164` | `AC-008`, `AC-004` |
| `docs/operations/deployment.md` | `b252028debaa` | `AC-009` |
| `docs/operations/cli.md` | `0cd14feb10d5` | `AC-009` |
| `README.md` | `a23514b833b8` | `AC-010`, `AC-009` |
| `backend/README.md` | `34b9cd994ebf` | `AC-010` |
| `packaging/mcpb/README.md` | `6d5d83505a05` | `AC-010` |

Audiences: people setting up Claude Desktop or a claude.ai connector; maintainers
and operators reading the evidence tables.

- `AC-001`: Evidence table now has a "Claude Desktop, version 0.4.0, on macOS"
  row (user observation, 2026-10-08, both checkout config and `.mcpb`, steps
  1–13 incl. 9a, composed answers checked, no failures, app version not
  recorded). The MCPB-installation row records install and use on macOS and
  keeps removal/same-version replacement unchecked. 2026-10-07 automated rows
  and the 2026-10-03 earlier-build row are unchanged. OS paragraph says the
  2026-10-08 Desktop observations were on macOS.
- `AC-002`: claude.ai row records the 2026-10-08 observation against the named
  0.4.0 deployment, same results as Desktop, prompts shown, resources
  attachable, plan type and connector name not recorded. Supported-routes
  claude.ai cells for resources and prompts now say observed (2026-10-08).
- `AC-003`: "Run status" records the 2026-10-08 Desktop run of steps 1–13
  incl. 9a; "Record your results" table column renamed "Recorded results" and
  keeps the 2026-10-07 replay plus the 2026-10-08 Desktop result per row, with a
  note that claude.ai gave the same results. The "no end-to-end workflow"
  paragraph now states the user ran and checked the workflows in Desktop and
  claude.ai on 2026-10-08.
- `AC-004`: Known-limits bullet keeps the dated 2026-10-03 earlier-build
  observation, adds that 0.4.0 listed more than Catalog, says finding a
  progression link was not recorded, and keeps the `read_evidence` advice. No
  resource names. `resources.md` "Client support varies" made consistent.
- `AC-005`: Remote checklist intro no longer says the service is not updated or
  that nothing ran; it records the 2026-10-08 0.4.0 confirmation and points to
  the evidence table; says no HTTP smoke result is recorded for that deployment;
  item 10 notes connector name and plan type not recorded (Desktop app version
  noted as not recorded under the results table). Method of confirmation not
  described. Checklist steps kept for re-checks.
- `AC-006`: `mcp-clients.md` Desktop intro, custom-connector note and optional
  MCPB passage replaced untested claims with the 2026-10-08 observations;
  troubleshooting keeps same-version removal/replacement unverified.
- `AC-015`: `mcpb.md` installation intro records the 0.4.0 macOS install and
  use; removal/reinstall stay unchecked; "Unverified UI detail" sentences,
  Team/Enterprise allowlist paragraph and organization **Upload new version**
  paragraph removed; step 4 no longer says untried. Section reads cleanly
  (inspected).
- `AC-016`: "Where does the bundle get `uv`?" subsection and its closing
  reference removed; grep finds no allowlist route, **Add to team**, **Upload
  new version**, `12592343` link, enable-control wording, `uv` provisioning or
  `where-does-the-bundle-get-uv` anchor in `docs/` or the READMEs (the two
  remaining "allowlist" hits are unrelated: resource MIME policy and
  `.dockerignore`). Manifest runtime facts at `mcpb.md:72` and `:164` remain.
  The checkout `command -v uv` / absolute-path instruction in `mcp-clients.md`
  is unchanged.
- `AC-009`: All nine `https://<service-domain>/mcp` occurrences replaced with
  `https://kg-for-ed-global-mcp.up.railway.app/mcp` (plus two new mentions in
  the evidence page). Grep finds no `service-domain` in scope files. Endpoint
  still described as unauthenticated. Deployment admonition reworded to fit a
  named, shared domain.
- `AC-010`: `README.md` (Desktop section, hosted section, MCPB section),
  `backend/README.md` (two "confirmed" statements) and
  `packaging/mcpb/README.md` now say "documented" method and record the
  2026-10-08 macOS bundle/checkout observations; disabled **Install** button
  caveat and other-build/OS hedges kept. Claude Code stays without a test
  claim.
- `AC-011`: Windows/Linux still undocumented and untested on every edited page
  that mentions platforms; manifest platform list still described as a
  declaration, not evidence.
- `AC-017`: No claim of HTTP smoke against the public deployment, named app
  version, plan type, connector name, resource names, or Windows/Linux/Claude
  Code/other-client testing. Remaining untested items keep that wording.
- `AC-013`: see Checks.
- `AC-014`: see Checks.
- `docs/guides/prompts.md` (`83b9c5584856`): inspected; describes Desktop
  prompt behavior with no tested/untested claim. No change needed.

## Checks and Applicability

1. Strict build. From the repo root:
   `uv --directory backend sync --locked --extra docs` (exit 0) then
   `uv --directory backend run --locked mkdocs build --strict --config-file "$PWD/mkdocs.yml" --site-dir <tmp>`
   (exit 0, no WARNING/ERROR lines). Run on final content listed above. Only
   difference from the `AC-013` command is `--site-dir` pointing to a temp
   directory so no `site/` output lands in the repo. The sandbox blocked uv's
   cache (`~/.cache/uv`, "Operation not permitted"), so both commands ran
   outside the sandbox. Side effect: the `--extra docs` sync removed dev-only
   packages from the untracked `backend/.venv`; `uv --directory backend sync --locked`
   restores them. Establishes no missing-page links; does not check anchors
   (design I-7). An mkdocs-material banner about MkDocs 2.0 printed; not an
   error.
2. Anchor check on the built site: every I-6 anchor exists in the built HTML;
   a script checked every `](path#anchor)` link in `docs/**/*.md` against built
   ids: 0 broken. `where-does-the-bundle-get-uv` appears 0 times. The README
   link to `docs/getting-started/claude-clients.md#what-has-and-has-not-been-checked`
   targets that same existing heading (READMEs are not built by MkDocs).
3. Boundary: `git status --short` and
   `git diff --stat 8df7879 -- . ':!.standards' ':!.agents' ':!.claude' ':!.codex' ':!AGENTS.md' ':!CLAUDE.md'`
   show only the ten Markdown files above; the only untracked file is this
   record (`.standards/`). Satisfies `AC-014`.
4. Greps: `service-domain` (0 hits in scope files); dropped-topic patterns
   (only unrelated hits); `untested|unverified|not tested|confirmed local`
   sweep reviewed line by line; remaining hits are intended (Windows/Linux,
   other builds, same-version removal/reinstall, `local-setup.md` panzoom note
   unrelated).
5. Manual inspection of each edited section after saving.

## Discrepancies, Dependencies, and Remaining Work

NONE blocking. Non-blocking notes:

- `.standards/CONTEXT.md` still shows the smoke command with the placeholder and
  omits `docs/operations/cli.md:128` (already noted in design Risks). Auditor-
  owned; does not affect the deliverable.
- Final review and synchronization are the next owners' work; not claimed.

## Resume and Conclusion

- Selected target and full Documenter gate: complete for the inputs above.
- Next: hand off to `REVIEWING_FINAL` (`FINAL_DELIVERABLE`), policy `NONE`.
- Blocking question: NONE.
