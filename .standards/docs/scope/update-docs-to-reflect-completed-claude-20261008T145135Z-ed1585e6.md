<!-- STANDARDS
Artifact: SCOPE
Cycle: update-docs-to-reflect-completed-claude-20261008T145135Z-ed1585e6
-->

# Record 2026-10-08 Claude client testing in the docs

## Goal

The user finished testing Claude Desktop and claude.ai against server version
0.4.0 on 2026-10-08. The docs still say that this testing has not happened.
Update the project docs and READMEs so that:

- readers can see what was tested, when, through which route and by whom
  (user observation, not automated evidence);
- readers can connect to the public deployment;
- anything the testing did not cover still says "untested" or "unverified",
  except four topics the user asked to drop (see **Topics to drop**).

Audiences are people setting up Claude Desktop or a claude.ai connector, and
maintainers and operators who rely on the evidence tables to decide what still
needs checking.

### User observations to record (all 2026-10-08)

From `Active Work.Request`, plus the user's answers to Scoper's questions on
2026-10-08:

1. **Claude Desktop, macOS, server 0.4.0**, through both the checkout
   configuration (`claude_desktop_config.json`) and the `.mcpb` bundle. The
   connector started, frameworks were listed, and prompts and resources appeared.
   Walkthrough steps 1–13 were run, including the composed, cited answers and
   reviews in steps 11–13, and the user checked them. No failures were observed.
2. **Desktop resource menu on 0.4.0** listed more resources than Catalog alone.
   The user did not say which resources appeared or whether a progression link
   could be found by URI.
3. **Public deployment** at `https://kg-for-ed-global-mcp.up.railway.app/mcp`
   was verified as running server 0.4.0. The user did not say how it was
   verified.
4. **claude.ai custom connector** against that deployment gave the same results
   as the Desktop testing, including the full walkthrough. The server prompts
   showed in claude.ai, and server resources could be attached.
5. **Not tested:** Windows and Linux setups.

### Topics to drop

On 2026-10-08 the user said the docs do not need to cover these topics.
Existing mentions should be removed rather than kept as "unverified":

1. How the user confirmed the public deployment.
2. The exact name of the bundle's extension label and enable control in Claude
   Desktop.
3. The organization-managed extension allowlist route (Team or Enterprise
   upload, **Add to team**, and versioned updates through that route).
4. How the bundle gets or is supplied with `uv`.

## Constraints

- Editing boundary: Markdown documentation under `docs/` plus `README.md`,
  `backend/README.md` and `packaging/mcpb/README.md`. Do not change code, tests,
  `packaging/mcpb/manifest.json`, `config/`, `data/`, `mkdocs.yml`, CI or other
  configuration.
- Mark nothing as tested beyond the observations above. Items they do not cover
  keep "untested" or "unverified" wording, except the topics to drop, which are
  removed instead.
- Keep evidence classes separate, as the docs already do: automated server and
  smoke checks, user client observations, and untested items. Each claim keeps
  its own ISO date, for example `2026-10-07`, `2026-10-03` and `2026-10-08`.
- The user chose to name the public endpoint everywhere. Docs and READMEs use
  `https://kg-for-ed-global-mcp.up.railway.app/mcp` in place of the
  `https://<service-domain>/mcp` placeholder.
- Follow IDinsight tone rules: plain, professional prose with no credentials or
  secrets. The endpoint is unauthenticated and needs no credentials.

## Non-goals

- Code, manifest, configuration, data, CI or deployment changes, and new
  automated tests.
- Running the Desktop or claude.ai tests again, or contacting the public
  endpoint, to create new evidence beyond what the user reported. Documenter
  may use the existing checks to confirm doc correctness, such as the MkDocs
  build.
- Documenting Windows or Linux Desktop setup.
- Claude Code and other MCP clients. Their testing status stays as it is.

## Work

### 1. Client evidence page

**Intent:** `docs/getting-started/claude-clients.md` is the main page showing
what has been checked. It should record the 2026-10-08 results and stay
accurate about what is still unchecked.

**Done when:**

- `AC-001`: The "What has and has not been checked" table records that on
  2026-10-08, Claude Desktop on macOS ran server 0.4.0 through both the checkout
  configuration and the `.mcpb` bundle. The connector started, frameworks were
  listed, prompts and resources appeared, walkthrough steps 1–13 were run with
  their composed answers checked, and no failures were observed. The rows label
  this as a user observation and date it. The earlier automated rows
  (2026-10-07) and the 2026-10-03 earlier-build row stay distinct and are not
  relabelled as 0.4.0 client evidence. The line on OS coverage says the
  2026-10-08 Desktop observations were on macOS.
- `AC-002`: The claude.ai custom connector row records the 2026-10-08 user
  observation against the public 0.4.0 deployment, with the same results as
  Desktop. In the "Supported routes" table, the claude.ai cells for prompt
  visibility and resource attachment say both were observed working on
  2026-10-08 and no longer say "untested".
- `AC-003`: The walkthrough's "Run status" note and its "Record your results"
  table show that steps 1–13 (including 9a) were run in Claude Desktop on 0.4.0
  on 2026-10-08 with no failures observed, and that the earlier local replay
  stays recorded. The paragraph saying no end-to-end teaching workflow has been
  run in any client now says the walkthrough workflows, including their
  composed answers, were run and checked by the user in Desktop and claude.ai on
  2026-10-08.
- `AC-004`: The Desktop resource-menu limit keeps the 2026-10-03 observation,
  dated and tied to the earlier build. It adds that on 0.4.0 on 2026-10-08 the
  menu listed more than Catalog. It does not name specific resources or claim
  that a progression link can be found from the menu. The `read_evidence`
  advice for links returned by tools remains.
- `AC-005`: The claude.ai remote acceptance checklist no longer says the hosted
  service has not been updated to 0.4.0 or that no item has been run. It records
  that the public deployment was confirmed to run 0.4.0 on 2026-10-08 and that
  the user's claude.ai results are recorded on the page. It does not claim the
  HTTP smoke command was run against that deployment, and it does not describe
  how the deployment was confirmed. Where the checklist asks
  for the Claude Desktop app version, claude.ai plan type or connector name, the
  record says these were not recorded. The checklist stays usable for later
  re-checks.

**Depends on:** None.

### 2. Setup, operations and guide pages

**Intent:** Remove claims elsewhere in the docs that contradict the new
evidence, and keep the remaining unverified details clearly flagged.

**Done when:**

- `AC-006`: `docs/getting-started/mcp-clients.md` no longer says the 0.4.0
  checkout connection, bundle installation or claude.ai connector path is
  untested. This covers the Desktop on macOS intro, the custom-connector
  section, the optional MCPB passage and troubleshooting. It points to or
  states the 2026-10-08 macOS and claude.ai observations instead. Same-version
  bundle removal and reinstall stay unverified.
- `AC-015`: The "Claude Desktop installation" section of
  `docs/operations/mcpb.md` records that a 0.4.0 bundle was installed and used
  in Claude Desktop on macOS on 2026-10-08. Same-version removal and reinstall
  keep their unverified wording. The section no longer covers the topics to
  drop: the "Unverified UI detail" about the exact label and enable control,
  the organization-managed allowlist installation route, and its versioned
  update instructions are removed, and the section stays readable without them.
- `AC-008`: The 0.4.0 testing-status claims in
  `docs/operations/troubleshooting.md` (Desktop connector and `.mcpb`
  installation sections) and in `docs/guides/resources.md` ("Client support
  varies") are consistent with the 2026-10-08 observations. This includes
  claude.ai resource attachment observed working. Neither file claims more than
  was observed.

**Depends on:** Work item 1 (the evidence page these pages refer to).

### 3a. Topics to drop

**Intent:** Remove material the user does not need, so the docs don't keep
flagging details nobody plans to check.

**Done when:**

- `AC-016`: No file under `docs/` and none of the three READMEs mentions any
  of the four topics to drop. The "Where does the bundle get `uv`?" subsection
  of `docs/operations/mcpb.md` is removed, along with every link or reference
  to it. Removing these passages does not remove other content or leave broken
  links, dangling sentences or empty sections. The checkout route's
  instruction to install `uv` and use its absolute path stays.

**Depends on:** None.

### 3. Public endpoint

**Intent:** Readers can connect to the project's public deployment without
having to find the domain themselves.

**Done when:**

- `AC-009`: Every `https://<service-domain>/mcp` occurrence in `docs/` and the
  three READMEs is replaced with `https://kg-for-ed-global-mcp.up.railway.app/mcp`.
  This covers client connection steps, `claude mcp add`, smoke-check examples,
  the remote checklist and the deployment page. No `<service-domain>`
  placeholder is left in those files. The text keeps the endpoint
  unauthenticated and needs no credentials. The deployment page's guidance on
  treating the public domain as permanent still makes sense with the named
  domain.

**Depends on:** None.

### 4. READMEs

**Intent:** The top-level and package READMEs should not contradict the
updated evidence.

**Done when:**

- `AC-010`: In `README.md`, `backend/README.md` and `packaging/mcpb/README.md`,
  each statement about Claude Desktop connection methods, MCPB installation, or
  hosted or claude.ai use matches the 2026-10-08 observations. For example, a
  README must not describe checkout registration as the only confirmed local
  method when the bundle also worked on macOS. Caveats about other Desktop
  builds or operating systems keep their hedged wording.

**Depends on:** Work items 1 and 3.

### 5. Limits on the claims

**Intent:** Keep the docs from overstating the evidence, and keep them
buildable.

**Done when:**

- `AC-011`: Wherever the edited docs and READMEs mention platform support,
  Windows and Linux Desktop setup is still described as undocumented and
  untested. The manifest's `darwin`/`linux`/`win32` declaration is still
  described as not being installation or testing evidence.
- `AC-017`: The edited docs and READMEs make no claim beyond the recorded
  observations: no HTTP smoke run against the public deployment, no named
  Desktop app version, claude.ai plan type or connector name, no specific
  resource names from the Desktop menu, and no Windows, Linux, Claude Code or
  other-client testing. Items the observations do not cover keep "untested" or
  "unverified" wording, except the topics to drop, which are removed under
  `AC-016`.
- `AC-013`: The strict documentation build passes. Run
  `uv --directory backend run --locked mkdocs build --strict --config-file "$PWD/mkdocs.yml"`
  from the repository root after `uv --directory backend sync --locked --extra docs`.
- `AC-014`: The cycle's project changes touch only Markdown files under `docs/`
  and the three READMEs. No code, test, manifest, configuration, data or CI file
  changes.

**Depends on:** Work items 1–4 and 3a.

## Retired Acceptance Identifiers

- `AC-007`: Retired on 2026-10-08 at the user's request. It required the exact
  label and enable control, the organization allowlist route and `uv`
  provisioning to keep unverified wording. Replaced by `AC-015` and `AC-016`.
- `AC-012`: Retired on 2026-10-08 at the user's request. It required every
  item the observations do not cover to keep untested or unverified wording,
  with no exception for the topics to drop. Replaced by `AC-017`.

## Assumptions

- "Same results as the Claude Desktop testing" for claude.ai covers the full
  walkthrough, including composed answers. The user's answers on 2026-10-08
  confirm prompt visibility and resource attachment in claude.ai.
- The Desktop app version, claude.ai plan type and connector name were not
  recorded. Docs say "not recorded" where the checklist asks for them, and do
  not make them up. How the deployment was confirmed is a topic to drop, so
  the docs leave it out instead of saying it was not recorded.
- The remote checklist's HTTP smoke step is an instruction for future checks,
  not a statement of how the user confirmed the deployment. It stays.
- Claude.ai connector guidance that a Team or Enterprise organization owner
  adds the connector first is not the Desktop extension allowlist route. It
  stays.
- Line numbers in `Active Work.Request` and `.standards/CONTEXT.md` point to
  likely places to edit. The required outcomes above take precedence over the
  exact line numbers.
