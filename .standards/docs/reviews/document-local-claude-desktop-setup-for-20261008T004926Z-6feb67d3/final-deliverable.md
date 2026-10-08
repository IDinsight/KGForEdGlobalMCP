<!-- STANDARDS
Artifact: REVIEW
Cycle: document-local-claude-desktop-setup-for-20261008T004926Z-6feb67d3
ReviewKind: FINAL_DELIVERABLE
-->

# Review Report

`Cycle`: `document-local-claude-desktop-setup-for-20261008T004926Z-6feb67d3` `ReviewKind`: `FINAL_DELIVERABLE`
`Status`: `COMPLETE` `User Style`: `NONE`

## Assessed Inputs and Scope

- Cycle mode `DOCUMENTATION`, `CompletionPolicy: NONE`, `ProjectMode:
  BROWNFIELD`. Recovery and outstanding obligations inactive; `BlockedOn: NONE`.
  Entered on a `FORWARD` handoff from `DOCUMENTING` with the documentation record
  `Status: COMPLETE`.
- Contract (SHA-256): scope
  `.standards/docs/scope/document-local-claude-desktop-setup-for-20261008T004926Z-6feb67d3.md`
  `d9fb4394…18de71`; design
  `.standards/docs/specs/document-local-claude-desktop-setup-for-20261008T004926Z-6feb67d3.md`
  `c6d6b72a…0cebac`; `.standards/CONTEXT.md` `3656a6a0…291621`. Current ACs:
  `AC-001`–`AC-014`; no retired IDs.
- Documentation record
  `.standards/docs/documentation/document-local-claude-desktop-setup-for-20261008T004926Z-6feb67d3.md`
  (committed in `76762b8`).
- Baseline/range: `57f8036..76762b8` on `tz6/doc-updates` (scope assumption for
  `AC-014`). Working tree clean at review start; HEAD `76762b8`. The only
  untracked file is this report.
- Saved docs (SHA-256, all equal to the documentation record's final identities):
  `docs/getting-started/index.md` `3b518726…78c64c`,
  `docs/getting-started/local-installation.md` `dd8add79…6e0a`,
  `docs/getting-started/mcp-clients.md` `9868dd80…5680`,
  `docs/getting-started/claude-clients.md` `e2ee803d…ca03`,
  `docs/operations/mcpb.md` `dce5b66c…04e4`,
  `docs/operations/troubleshooting.md` `ad8b300e…5a73`.
- Supporting source/config (SHA-256 unchanged from the record's entry identities):
  `packaging/mcpb/manifest.json` `3b40f967…f6f46`, `backend/pyproject.toml`
  `373ed791…a7f6a26`, `backend/uv.lock` `fedd1863…a6fd3`,
  `backend/src/kgfegmcp/cli/stdio_smoke.py` `60aa9085…d1227`,
  `backend/src/kgfegmcp/cli/build_mcpb.py` `3676404a…7a97b`,
  `backend/src/kgfegmcp/mcp/tools/frameworks.py` `985c6c97…01d72`,
  `backend/src/kgfegmcp/mcp/tools/capabilities.py` `4793f640…5f35`, `mkdocs.yml`
  `83d47198…aefbcb`. Also read `backend/src/kgfegmcp/app.py` (server name).
- Boundary: existing files under `docs/` only. Development, Testing and
  Implementation Review are intentionally omitted; none of their records are
  required or claimed. Root `README.md` and `packaging/mcpb/README.md` are scope
  non-goals and were not assessed for drift.
- Session: this review ran in a conversation that began with the `/reviewer`
  invocation and contains no authoring history for this cycle's scope, design or
  documentation. Reviewer model Claude Opus 5.5; the authoring model is not
  recorded, so whether it differs is unknown.

## Contract and Evidence Assessment

| Obligation / criterion | Assessed evidence | Current disposition |
| --- | --- | --- |
| AC-001 / design "Bundle runtime", "Claude Desktop"; TAC for AC-001/003/005 | `mcpb.md` "Install and enable the bundle" and "Remove an older copy before reinstalling"; Reviewer fetched the cited Anthropic local MCP guide, allowlist guide (dated 2026-03-16) and Desktop Extensions post | Supported. Install path, Install dialog, double-click route, + > Connectors inspection, restart advice, org upload, Add to team and Upload new version all match the sources. Enable control, local removal and same-version behavior are labelled unverified; the sources contain none of them |
| AC-002 | Documentation record "Resume and Conclusion": question described, user reply quoted, outcome (research, no observations) | Supported. No step claims user confirmation; unsourced steps keep their labels. Reviewer cannot see the original exchange; relies on the record (limitation) |
| AC-003 / design "Bundle runtime" | `mcpb.md` "Where does the bundle get `uv`?"; MCPB MANIFEST.md UV runtime section fetched | Supported. Spec says host installs dependencies with UV and is silent on the `uv` executable; doc names it a known unknown and asserts neither answer |
| AC-004 / design "Operating systems"; TAC AC-004 | `mcp-clients.md` intro, `claude-clients.md` note under the table, `mcpb.md` intro, `troubleshooting.md` | Supported. macOS-only stated; manifest platforms called a declaration; no tested-on-OS claim |
| AC-005 | Grep of changed pages | Supported. No Windows/Linux steps added |
| AC-006 / design "Disk footprint"; TAC AC-006 | `index.md` prerequisites, `local-installation.md` "Disk space"; Reviewer re-measurement | Supported. Re-measured figures match (see Checks); graph and input data separated; ignored `data/source_artifacts/` excluded; unmeasured parts named; fresh-clone caveat present; bundle staging copies only `data/graph_packages` (`build_mcpb.py` lines 520, 558-559) |
| AC-007 / design "Config JSON check"; TAC AC-007 | All `jq` uses under `docs/`; Reviewer ran the published command | Supported. Both config-check `jq` uses replaced; remaining `jq` uses (mcpb.md archive inspection) are listed as optional prerequisites; command exits 0/1/1 on valid/invalid/empty with a quoted path containing spaces; `plutil` not offered |
| AC-008 | `mcp-clients.md` warning admonition | Supported. Full stop added after "intact" |
| AC-009 / TAC AC-009 | `mcp-clients.md` "Desktop is running an old copy"; `claude-clients.md` lines 76-82; `mcpb.md` "Remove an older copy" closing paragraph | Supported. Exact strings match source; remedy (bundle: remove and reinstall, unverified; checkout: verify paths, fully quit, reopen) agrees across all three pages |
| AC-010 / design "Data and Control Flow"; TAC AC-010 | `index.md` smoke introduction; `stdio_smoke.py` lines 128-143, 160-181; uv docs link | Supported. Explanation matches the control flow and does not claim that skipping `uv sync` breaks the repository smoke |
| AC-011 | `claude-clients.md` evidence table | Supported. No new pass; Desktop 0.4.0 still "Prepared; not yet run in Desktop"; new row for bundle install in Desktop marked not checked; bundle-smoke row clarified as not a Desktop install |
| AC-012 / design "Checkout launch contract"; TAC AC-012 | Reviewer script parsing the JSON block against the manifest | Supported. Command, eight args in checkout order, nine env keys, three fixed values and six root-mapped paths all match; JSON unchanged from baseline; added placeholder-count sentence is correct |
| AC-013 / design "Docs build"; TAC AC-013 | Reviewer strict build plus anchor check | Supported. Exit 0; only the upstream Material notice; all 19 anchored internal links in changed pages resolve |
| AC-014 | `git diff --name-status 57f8036 HEAD`, `git status --porcelain` | Supported. Only six existing `docs/` pages plus `.standards/` records changed |

## Checks and Results

All on 2026-10-08, macOS (Darwin), repository root unless noted.

- `node .standards/bin/check.mjs`: exit 0, `STANDARDS check passed.` (entry).
- `shasum -a 256` over the docs, contract, source and config files listed above:
  all match the documentation record's identities.
- AC-012 script (scratchpad, Python 3): parses the `json` block under "2. Add the
  MCP server configuration" and asserts command, args, env keys and values
  against `packaging/mcpb/manifest.json` with `${__dirname}` mapped to the
  repository root. Exit 0, `PASS`.
- From `backend/`: `.venv/bin/mkdocs build --strict --config-file ../mkdocs.yml
  --site-dir <temp>`: exit 0, `Documentation built in 0.87 seconds`; only the
  upstream Material for MkDocs 2.0 notice. `mkdocs.yml` sets no `validation`
  options, so MkDocs 1.6 reports bad anchors only at INFO and strict mode would
  not fail on them; Reviewer therefore parsed every anchored internal link in the
  six changed pages and checked the target `id` in the built HTML
  (`use_directory_urls: false`): 19 checked, 0 missing. Temp site removed.
- Published JSON check, from repository root, with a temp path containing
  `Application Support/Claude/claude_desktop_config.json`:
  `backend/.venv/bin/python -m json.tool "<path>" > /dev/null` (Python 3.13.9).
  Valid JSON exit 0, no output; trailing comma exit 1 with
  `Illegal trailing comma…`; empty file exit 1. No real client config read.
- Tracked size re-measurement (sum of `os.stat` over `git ls-files -z`): 1,464
  files, 1,360,307,291 bytes; `data/graph_packages/` 671,449,871;
  `data/input_artifacts/` 671,370,714. The extra file and ~32 KB versus the
  record are this cycle's later workflow records; rounded figures unchanged.
  `git count-objects -vH`: `size-pack: 281.43 MiB`. `du -sk backend/.venv`:
  328208 KiB (≈321 MiB). Sum ≈1.99 GB, consistent with "about 2 GB".
  `.gitignore` line 21 ignores `/data/source_artifacts/`; no `.gitattributes`.
- `git diff --check 57f8036 HEAD`: exit 0.
- External sources fetched (WebFetch): Anthropic "Getting started with local MCP
  servers on Claude Desktop"; Anthropic "Enabling and using the desktop extension
  allowlist" (dated March 16, 2026); Anthropic "Desktop Extensions" engineering
  post; MCPB `MANIFEST.md`. Each published sourced claim was found; none of them
  covers uv provisioning, a per-extension enable switch, local uninstall or
  same-version reinstall, which the docs correctly leave unverified or unknown.
- Not run: Claude Desktop, bundle build/install, the repository or stage smoke,
  backend tests. None is required by this contract, and no doc claims them.

## Findings

No material findings.

## Questions, Limitations, and Later Dependencies

- AC-002 user exchange: Reviewer cannot see the Documenter conversation and
  relies on the record's description and quoted reply. Not material: the AC asks
  that the record show the question and outcome, which it does, and the published
  steps are consistent with an outcome that confirmed nothing.
- Bundle connector name (`mcpb.md` line 309): the doc suggests looking for
  **Curriculum Knowledge Graph MCP** or **curriculum-knowledge-graph**. The
  manifest's `display_name` is the first; `curriculum-knowledge-graph` is the
  checkout config key and appears in the 2026-10-03 observation and the
  walkthrough; the manifest `name` is `kgfegmcp`. Which label Desktop shows for a
  bundle is unknown, and the sentence is labelled unverified, so no defect is
  established. A reader with both a checkout registration and the bundle could
  confuse the two; that is worth confirming when the bundle is first installed.
- Root `README.md` and `packaging/mcpb/README.md` still carry the older `jq` and
  Desktop text. Scope non-goal; observation only.
- External pages may change after 2026-10-08.
- Later dependencies: NONE.

## Progress and Conclusion

- Inspected the full `docs/` diff from `57f8036`, all six changed pages in the
  affected sections, the contract, record, manifest, smoke and builder code, and
  the cited sources. All 14 ACs and the design's technical criteria have current
  supporting evidence.
- The `FINAL_DELIVERABLE` gate passes: no open finding, no material gap, no
  blocking question, edits within boundary, docs build clean.
- Plain-language summary: the documentation changes can move forward. Each of
  the seven gaps is fixed or plainly marked as unknown, the sourced install steps
  match Anthropic's pages, the disk figures and the new JSON check reproduce, and
  the setup example still matches the bundle manifest. Nothing has been tried in
  Claude Desktop, and the docs say so. Passing this review does not finish the
  cycle; Synchronizer reconciles next, then the user signs off.
- Next: `FORWARD` to `SYNCHRONIZING`.
