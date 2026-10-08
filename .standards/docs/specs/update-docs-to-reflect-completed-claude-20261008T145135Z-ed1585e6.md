<!-- STANDARDS
Artifact: ARCHITECTURE
Cycle: update-docs-to-reflect-completed-claude-20261008T145135Z-ed1585e6
-->

# Technical Design: Record 2026-10-08 Claude client testing in the docs

## Context

This is a Brownfield `DOCUMENTATION` cycle. The completed scope
(`.standards/docs/scope/update-docs-to-reflect-completed-claude-20261008T145135Z-ed1585e6.md`)
asks Documenter to replace "untested" claims about Claude Desktop and claude.ai
with the user's 2026-10-08 observations, name the public endpoint, and remove
four topics the user dropped. Project context is `.standards/CONTEXT.md`.

No implementation is permitted, so this design has no Build Plan. It records
the existing technical facts the edits must stay consistent with, the exact
edit locations those facts imply, and the limits of the build check.

Evidence classes this design relies on:

- **Repository facts** (source, manifest, lock files, config), cited by path
  below. These hold for the current checkout.
- **User observations** dated 2026-10-08, as listed in the scope's "User
  observations to record". They are not automated or Tester evidence, and this
  design does not upgrade them.
- **Existing documented evidence** dated 2026-10-07 (automated server, smoke and
  in-process walkthrough replay) and 2026-10-03 (user observation of an earlier
  Desktop build), held in `docs/getting-started/claude-clients.md`.

## Decision

Documenter edits prose only, within the scope's editing boundary, against the
facts and location map in **Interfaces and Contracts**. The material choices
this design fixes are:

1. **The public endpoint string is exactly
   `https://kg-for-ed-global-mcp.up.railway.app/mcp`.** The `/mcp` path matches
   the server's transport (see I-2). Every `https://<service-domain>/mcp`
   occurrence is replaced verbatim; there are nine, including one in
   `docs/operations/cli.md` that `.standards/CONTEXT.md` does not list.
2. **Manifest runtime facts stay; only the "how Desktop supplies `uv`" topic
   goes.** `docs/operations/mcpb.md` line 72 ("a UV server runtime") and line
   179 ("server type `uv`") describe what the manifest declares (I-4), not how
   the bundle obtains `uv`. They are not topic 4 and must remain. Topic 4 is the
   "Where does the bundle get `uv`?" subsection (lines 89–102) and the closing
   sentence and link at lines 356–357.
3. **The organization allowlist route covers three passages** in
   `docs/operations/mcpb.md`: the Team/Enterprise allowlist paragraph (lines
   321–325), the organization-managed **Upload new version** paragraph that
   opens "Remove an older copy before reinstalling" (lines 328–334), and the
   clause "and your organization's extension settings" (line 352). The
   claude.ai connector note in `docs/getting-started/mcp-clients.md` line 209
   is a different route and stays, as the scope's assumptions say.
4. **The extension label and enable control topic** is the "Unverified UI
   detail" sentence and the two sentences after it in step 3 of "Install and
   enable the bundle" (`docs/operations/mcpb.md` lines 308–311). The
   Anthropic-sourced inspection route (**+ > Connectors**) in the same step is
   not a dropped topic and may stay. The name **Curriculum Knowledge Graph MCP**
   in the same-version removal procedure is the manifest `display_name` (I-4);
   it can stay there as part of that still-unverified procedure.
5. **Preserve all heading anchors that other pages link to** (I-6). Renaming
   them would break links that the strict build does not catch (I-7).

## Acceptance Coverage

- `AC-001`, `AC-003`: Technical coverage: I-1 (version 0.4.0), I-5 (evidence
  classes and dates) and I-6 (anchors on the evidence page). Satisfaction is
  Documenter-owned prose in `docs/getting-started/claude-clients.md`.
- `AC-002`: Technical coverage: I-1, I-2 (claude.ai reaches the server over
  stateless Streamable HTTP at `/mcp`) and I-5. Documenter-owned prose.
- `AC-004`: No architectural impact. It depends on the 2026-10-03 and
  2026-10-08 user observations (I-5) and on the existing `read_evidence`
  guidance, which stays.
- `AC-005`: Technical coverage: I-3 (the smoke command and its `--url`
  option stay as an instruction for later checks) and I-2. The checklist's
  record fields and the "not recorded" values are Documenter-owned prose.
- `AC-006`, `AC-008`: Technical coverage: I-5 and the location map in I-8.
  Documenter-owned prose.
- `AC-015`: Technical coverage: Decisions 3 and 4, I-4 and I-8. The
  same-version removal and reinstall procedure stays unverified.
- `AC-016`: Technical coverage: Decisions 2–4, I-6 and I-7. The only inbound
  link to the removed `uv` subsection is `docs/operations/mcpb.md:357`.
- `AC-009`: Technical coverage: Decision 1, I-2 and I-8 (all nine
  occurrences). The deployment page's "Treat the public domain as permanent"
  wording is Documenter-owned prose.
- `AC-010`: Technical coverage: I-8 (README locations). Caveats about other
  Desktop builds, including the disabled **Install** button, are not dropped
  topics and keep their hedged wording.
- `AC-011`: Technical coverage: I-4 (`compatibility.platforms` declares
  `darwin`, `linux`, `win32`; no Windows or Linux setup exists in the docs).
- `AC-017`: No architectural impact. It is a limit on Documenter's claims; the
  evidence-class rules in I-5 define what each class may support.
- `AC-013`: Technical coverage: I-7 (build commands and their limits).
- `AC-014`: Technical coverage: I-9 (diff base and excluded framework paths).

## Interfaces and Contracts

### I-1. Server version

`0.4.0` in `backend/pyproject.toml`, `packaging/mcpb/manifest.json`
(`"version"`) and `.release-please-manifest.json`. The bundle file name for this
version is `dist/kgfegmcp-0.4.0.mcpb` (`docs/operations/mcpb.md`).

### I-2. Hosted transport and endpoint

`backend/src/kgfegmcp/http_server.py` runs FastMCP with `transport="http"` and
`stateless_http=True` on the platform `PORT`, and adds a `GET /health` route.
FastMCP serves Streamable HTTP at `/mcp`, matching every documented endpoint.
No authentication is configured; `docs/operations/deployment.md` ("Access and
rights posture") states the endpoint is unauthenticated, and rights gates apply
as locally. The hosted domain is a user-supplied fact (CONTEXT "External Systems
and Data"); no tracked file named it before this cycle. Nobody in this cycle
contacts the endpoint.

### I-3. HTTP smoke command

`kgfegmcp-http-smoke` (`backend/pyproject.toml` script →
`kgfegmcp.cli.http_smoke:cli`) takes `--url` and connects to an already-running
endpoint. The documented form is
`uv --directory backend run --locked --no-dev kgfegmcp-http-smoke --url <endpoint>`.
With the named endpoint it remains an instruction for later checks. No record
shows it was run against the public deployment, so docs must not say it was.

### I-4. Bundle manifest facts

From `packaging/mcpb/manifest.json`: `display_name` is
`Curriculum Knowledge Graph MCP`; `server.mcp_config.command` is `uv`;
`compatibility.platforms` is `darwin`, `linux`, `win32`; there are no
`user_config` fields. The platform list is a declaration, not installation or
testing evidence. The manifest is out of bounds for edits.

### I-5. Evidence classes and what each supports

| Class | Date | Supports |
|---|---|---|
| Automated offline tests, STDIO/HTTP smoke, unpacked-bundle STDIO smoke, in-process walkthrough replay | 2026-10-07 | Server behavior on 0.4.0; not a client result |
| User observation, earlier Desktop build | 2026-10-03 | Six frameworks, nine prompts, Catalog attached, menu offered only Catalog and no progression link |
| User observation, Desktop on macOS, 0.4.0, checkout config and `.mcpb` | 2026-10-08 | Connector started, frameworks listed, prompts and resources appeared, walkthrough 1–13 (including 9a and composed answers in 11–13) run and checked, no failures; menu listed more than Catalog (no names) |
| User observation, public deployment | 2026-10-08 | Runs 0.4.0 at the named endpoint (method not documented) |
| User observation, claude.ai custom connector | 2026-10-08 | Same results as Desktop, full walkthrough; prompts shown; resources attachable |
| Not tested | — | Windows, Linux, Claude Code, other clients, same-version bundle removal/reinstall, HTTP smoke against the public deployment |

Not recorded: Desktop app version, claude.ai plan type, connector name.

### I-6. Heading anchors with inbound links

These anchors are linked from other pages and must keep resolving:

- `getting-started/claude-clients.md#what-has-and-has-not-been-checked`,
  `#claude-desktop-walkthrough`, `#record-your-results`,
  `#claudeai-remote-acceptance-checklist`
- `operations/mcpb.md#claude-desktop-installation`,
  `#smoke-test-the-retained-stage`
- `getting-started/mcp-clients.md#desktop-is-running-an-old-copy`,
  `#connect-to-a-hosted-server`, `#3-validate-the-json`

`operations/mcpb.md#where-does-the-bundle-get-uv` is removed with its
subsection; its only inbound link is `docs/operations/mcpb.md:357`.

### I-7. Documentation build

MkDocs 1.6.1 (`backend/uv.lock`), configured by `mkdocs.yml` with no
`validation:` block. Acceptance commands, from the repository root:

```text
uv --directory backend sync --locked --extra docs
uv --directory backend run --locked mkdocs build --strict --config-file "$PWD/mkdocs.yml"
```

With MkDocs 1.6 defaults, `--strict` fails on links to missing pages but
reports a missing heading anchor only at `info` level, so the build passes with
a broken anchor. Anchor integrity (I-6) needs a separate check, for example a
search for each changed or removed anchor. The README files are outside
`docs/` and are not built by MkDocs.

### I-8. Edit location map

Starting points from the request and `.standards/CONTEXT.md`, confirmed against
the current files. Outcomes in the scope take precedence over line numbers.

- `docs/getting-started/claude-clients.md`: evidence table and OS line (10–28),
  supported-routes claude.ai cells (36, 38), resource-menu limit (46–47),
  walkthrough "Run status" and old-copy note (71–81), "Record your results"
  (275–285), remote checklist (287–321, endpoint at 297, record fields at 320–321).
- `docs/getting-started/mcp-clients.md`: Desktop on macOS intro (45–52),
  hosted endpoint (199), custom-connector note (219–221), Claude Code (226),
  smoke (239), optional MCPB path (261–266), old-copy troubleshooting (283–292).
- `docs/operations/mcpb.md`: `uv` subsection (89–102), installation intro
  (287–292), step 3 UI detail (308–311), step 4 (312–315), allowlist paragraph
  (321–325), versioned-update paragraph (328–334), same-version procedure
  (335–342), blocked-install paragraph and `uv` link (350–357).
- `docs/operations/troubleshooting.md`: 215 and 372–376.
- `docs/guides/resources.md`: "Client support varies" (263–271).
- `docs/operations/deployment.md`: endpoint (109), permanent-domain admonition
  (112–115), smoke (121).
- `docs/operations/cli.md`: smoke example (128).
- `README.md`: Desktop "confirmed local integration" (187), hosted endpoint and
  Claude Code (265, 272), "confirmed local connection method" (336–338).
- `backend/README.md`: 350–351. `packaging/mcpb/README.md`: 254–262.

### I-9. Editing boundary check

Project files are unchanged since `8df7879`; later commits on this branch add
only STANDARDS framework and cycle files. To check `AC-014`, list changes since
`8df7879` excluding `.standards/`, `.agents/`, `.claude/`, `.codex/`,
`AGENTS.md` and `CLAUDE.md`, plus untracked files. Only Markdown files under
`docs/` and the three READMEs may appear.

## Technical Acceptance Criteria

- `AC-009`: Every replaced URL is byte-for-byte
  `https://kg-for-ed-global-mcp.up.railway.app/mcp`, and no `<service-domain>`
  remains in `docs/`, `README.md`, `backend/README.md` or
  `packaging/mcpb/README.md`.
- `AC-005`, `AC-017`: Smoke command text keeps the `--url` form from I-3 and is
  framed as a check to run, not as a recorded result against the public
  deployment.
- `AC-015`, `AC-016`: Lines 72 and 179 of `docs/operations/mcpb.md` (manifest
  runtime facts) remain; no anchor `#where-does-the-bundle-get-uv` and no
  `support.claude.com/en/articles/12592343` link remains anywhere in the edited
  files.
- `AC-013`, `AC-016`: The strict build passes, and every anchor in I-6 still
  resolves to an existing heading.
- `AC-011`: Any statement about platforms is consistent with I-4: the
  manifest's three platforms are a declaration, and Windows and Linux Desktop
  setup is undocumented and untested.

## Risks and Follow-up

- The strict build does not catch broken heading anchors (I-7). Documenter
  needs to check them separately.
- Naming the public endpoint makes a live URL part of the docs. If the domain
  changes later, these nine places and the deployment page need updating. This
  follows the user's choice in the scope.
- `.standards/CONTEXT.md` still lists the smoke command with the placeholder and
  omits `docs/operations/cli.md:128`. This does not block Documenter, because
  the scope requires every occurrence under `docs/`. Auditor can refresh it in a
  later cycle.
