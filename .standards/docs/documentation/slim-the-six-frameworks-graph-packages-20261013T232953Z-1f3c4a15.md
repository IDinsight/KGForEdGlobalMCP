<!-- STANDARDS
Artifact: DOCUMENTATION
Cycle: slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15
-->

# Documentation Record

`Cycle`: `slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15` `Status`: `COMPLETE`
`Collaboration`: `AUTONOMOUS` `Target`: `ACTIVE_CHANGE` `Target Detail`:
`slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15` `User Style`:
`tony`

## Assessed Inputs and Boundary

- Workflow: `STANDARD`, `FULL_DELIVERABLE`, `BROWNFIELD`; entered `DOCUMENTING` by a
  normal forward handoff from `REVIEWING_IMPLEMENTATION`. Recovery and outstanding
  obligations inactive; no blockers.
- Contract and owner evidence (sha256 prefix of the content assessed on 2026-10-14):
  - Scope `.standards/docs/scope/slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15.md`
    (`c60c8d3d94ef`): current ACs `AC-001`–`AC-019`, no retired IDs. Re-read after
    Scoper's correction `44cd750` (`db83fa0715fe`): AC-009 wording and item 3's intent
    changed; meaning of the served contract and the AC set unchanged.
  - Architecture `.standards/docs/specs/slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15.md`
    (`2c6131ea35ec`): Decisions 1–6, Interfaces 1–10, Technical Acceptance Criteria,
    Risks ("Client-visible changes" assigned to `AC-019`).
  - Context `.standards/CONTEXT.md` (`d0e61000cf18`).
  - Development plan (`a321112f3d9c`), verification report (`c5ff6c5b298f`, `COMPLETE`,
    AC-019 pending Documenter) and implementation review (`076ca392a25d`, `COMPLETE`,
    no material findings, AC-019 a permitted later dependency).
- Repository: branch `tz6/data-file-cleanup`, HEAD `d830837`, clean tree at entry.
  Active change `2763e19..d830837` (STANDARDS install at `2763e19`; first cycle change
  `af2a814`). No source, test, data or configuration file was changed by this role.
- Behavior sources inspected: `packages/models.py` (1.2 rules, reserved names, record
  requirement, LP required set), `packages/builder.py` (record, `localPath`
  repository constraint), `packages/validator.py` (pending batch skips terminal
  packages before loading), `packages/lp_runtime.py` (runtime-tier checks),
  `packages/evidence_models.py`, `resources/{models,policy,lp}.py`,
  `mcp/resources/register.py`, `errors.py`, `cli/validate_packages.py`,
  `cli/verify_evidence_archive.py`, `.gitignore`, `pyproject.toml` scripts, one real
  manifest, record, slim index, shard and slim entity documents (Nigeria), and
  `data/input_artifacts/nigeria_math/package_build.json`.
- Editing boundary: Documenter-owned prose in `docs/`, `README.md`,
  `backend/README.md` and `packaging/mcpb/README.md`. `AGENTS.md`/`CLAUDE.md` hold only
  the managed STANDARDS block, so no project guidance change. `.standards/CONTEXT.md` is
  Auditor-owned and was not edited (it still describes the pre-change baseline, which
  Auditor reconciles in a later cycle). No generated documentation exists; `site/` is
  built, not committed.
- Styles: `.claude/skills/documenter/styles/universal.md` (`21dce31e9669`), user style
  `tony` (`.standards/user-styles/documenter/tony.md`, `dd6b47df4a55`; plain language,
  no jargon or stock phrases). No technology style applies: no Python, TypeScript, HTML
  or CSS documentation was changed.
- User instruction (2026-10-14, this invocation): legacy and backward-compatibility
  documentation need not be kept and may be removed where applicable. Applied as listed
  under Documentation Work.

## Documentation Work and Evidence

Saved content identities (sha256 prefixes) are listed under Checks. Audiences:
operators and maintainers (data, operations, development pages), MCP client users
(reference, guides, getting started).

| Surface | Change | ACs / criteria |
|---|---|---|
| `docs/data/graph-packages.md` | New runtime layout (`detailed/`, `slim/`, `evidence/`), per-package sizes, "Runtime files and archived evidence" (runtime vs archive-only sets, Drive copy, record fields), "Slim provenance" (removed fields, hash links, index, shard placement, canonical bytes) | AC-001, AC-004, AC-010, AC-012, AC-018, AC-019; Interfaces 1, 3, 4, 5 |
| `docs/data/manifest.md` | Manifest `1.2` only (other versions → `manifest_version_unsupported`); current declarations and paths; required LP set and 64 slim shards; required `evidenceArchiveRecord`; eight reserved archive-only names; capability flags | AC-001, AC-019; Interfaces 1–2 |
| `docs/data/validation.md` | New "Two validation tiers" (what each reads and checks, evidence-tier steps, outcome/finding table, `--runtime-only`); LP validation split by tier | AC-004, AC-005, AC-006, AC-007, AC-008, AC-019; Interface 6 |
| `docs/data/rights-and-provenance.md` | Artifact policy table without undeclarable names; archived names → `resource_not_found`; slim standard/LC provenance; LP evidence classes | AC-011, AC-012, AC-013, AC-019 |
| `docs/reference/resources.md` | Artifact and LP policy tables; record never served; archived names `resource_not_found`; standard and LC provenance result fields; slim per-edge record contract (replaces "complete original" wording); source artifacts; LP summary artifact links; progression citation of the archived map | AC-009, AC-010, AC-011, AC-012, AC-013, AC-019; Interfaces 4, 5, 10 |
| `docs/reference/progression-tool.md` | Result metadata: the manifest lists package files; the cited `learningProgressionProvenance` is the archived map, hashed from the evidence archive record, and its URI returns `resource_not_found`; provenance contents without "candidate references" (Rework 1) | AC-009, AC-019; Interface 10 |
| `docs/guides/resources.md`, `docs/guides/progression.md` | Per-edge provenance wording; standard provenance contents; artifact table; obsolete `…+5ea90021b08d` snapshot in two example URIs replaced | AC-009, AC-012, AC-019 |
| `docs/reference/access-tools.md`, `docs/guides/framework-discovery.md`, `docs/data/framework-catalog.md` | Six new snapshot IDs; measured `read_evidence` sizes | AC-002, AC-019 |
| `docs/getting-started/claude-clients.md` | New snapshot IDs; steps 7–10 values replayed; step 10 now shows `resource_not_found` (archived map) and `resource_access_denied` (`nodes`); evidence table row for the runtime-only server; note that 2026-10-08 client runs used the earlier packages | AC-002, AC-009, AC-011, AC-012, AC-019 |
| `docs/development/framework-package.md` | Input sets (committed vs git-ignored files), Drive archive, "Restore and verify archived evidence" (steps, output, exit codes, counts), rebuild and accept with the archive (builder skips absent `detailed/` files; a reproduced snapshot ID keeps the sealed committed package, Rework 1), `localPath` repository constraint, current contracts, slim shards, LP declarations, tier split; new-framework steps (input-set layout, evidence tier needs inputs, commit and archive split) | AC-014, AC-015, AC-018, AC-019; Interfaces 7–9 |
| `docs/operations/cli.md` | Command table and help list add `kgfegmcp-verify-evidence-archive`; `--runtime-only`; evidence tier and `evidence_archive_unavailable`; pending batch behavior; verify command section | AC-004, AC-005, AC-006, AC-018, AC-019; Interfaces 6, 9 |
| `docs/operations/troubleshooting.md` | Startup-equivalent check uses `--runtime-only`; new `evidence_archive_unavailable` entry | AC-006, AC-019 |
| `docs/development/testing.md` | Archive needed only without `--runtime-only`; CI on a plain checkout; synthetic evidence fixture; slim per-edge test wording | AC-017, AC-019 |
| `docs/operations/deployment.md`, `docs/operations/mcpb.md` | Image and bundle hold only declared runtime files (480 files); no archive needed to deploy; validation advice before building | AC-016, AC-019 |
| `docs/getting-started/index.md`, `docs/getting-started/local-installation.md` | Sizes remeasured 2026-10-14 (103 MB tracked, 84 MB packages, 1 MB input sets, 293 MiB packs, 319 MiB venv); archive restore adds about 670 MB | AC-003, AC-019 |
| `docs/architecture.md`, `docs/data/index.md` | Archived evidence paragraph; package tree shows `slim/` and `evidence/` | AC-019 |
| `README.md`, `backend/README.md`, `packaging/mcpb/README.md` | Verify command in CLI lists; archive note; validator bullet; MCPB README LP sentence | AC-018, AC-019 |

No documentation impact beyond the above:

- AC-002 (served content unchanged): no tool behavior changed, so tool references stay
  as they are. Only snapshot IDs, measured byte sizes and the documented contract
  changes in Risks were updated.
- AC-008 (runtime revalidation rejects missing, extra or altered files): the existing
  "Closed package tree", "Filesystem discovery and tree integrity" and "Catalog
  acceptance" sections remain accurate; unchanged.
- AC-011, AC-013 (rights gating unchanged): rights classes for served resources are
  unchanged; only tables naming undeclarable artifacts were corrected.

User-directed legacy removal (in pages touched for this change): manifest `1.1`
wording; historical migration notes in `framework-package.md` ("initial copy retained
138 files …", "Adding evidence changed artifact-set snapshot hashes", retiring old
active directories); "retired packages" in the MCPB README; observations from an
"earlier build" (2026-10-03) in `claude-clients.md` and `guides/resources.md`; the
"no longer accepts a public nested `match`" compatibility note in `backend/README.md`.
A pre-existing broken link to a nonexistent `instructions.md` in
`packaging/mcpb/README.md` now points to `docs/architecture.md`.

## Checks and Applicability

All on 2026-10-14, macOS Darwin 25.6.0, `backend/.venv` (Python 3.13.9, dev and docs
extras present), Claude Code sandbox, HEAD `d830837` plus the documentation edits.

- Saved content (sha256 prefix):
  `README.md` `2c5c79511858`;
  `backend/README.md` `900df172bb1f`;
  `docs/architecture.md` `b118e3d13c3f` (after Rework 2; was `ea101b8626e4`);
  `docs/data/framework-catalog.md` `46138a23608a` (after Rework 2; was `e5aa0f753f54`);
  `docs/data/graph-packages.md` `fbad43d60ef0`;
  `docs/data/index.md` `c0a150d356e1`;
  `docs/data/manifest.md` `a703472bb4da`;
  `docs/data/rights-and-provenance.md` `baf6c5a54413`;
  `docs/data/validation.md` `1c21509f7f21`;
  `docs/development/framework-package.md` `45aebd9fc0f3` (after Rework 1; was `f292ec185e82`);
  `docs/development/testing.md` `957dec2104ff`;
  `docs/getting-started/claude-clients.md` `a0f62b0629f3` (after Rework 2; was `e5135ae5c332`);
  `docs/getting-started/index.md` `d9569076617b`;
  `docs/getting-started/local-installation.md` `ec87440abf99`;
  `docs/guides/framework-discovery.md` `9f8eb78c056b`;
  `docs/guides/progression.md` `5ca2691bee04`;
  `docs/guides/resources.md` `7d0190afeb40`;
  `docs/operations/cli.md` `6b1d177ef718`;
  `docs/operations/deployment.md` `e22eb7867525` (after Rework 2; was `343b67e03109`);
  `docs/operations/mcpb.md` `2350974a0142`;
  `docs/operations/troubleshooting.md` `de3b50b67e65`;
  `docs/reference/access-tools.md` `bc35d9449232`;
  `docs/reference/progression-tool.md` `099a7c85da68` (Rework 1);
  `docs/reference/resources.md` `5a8aca2f0424` (after Rework 2; was `cb50937d62ee`);
  `packaging/mcpb/README.md` `18e01beda4c9`.
- `backend/`: `.venv/bin/mkdocs build --strict --config-file ../mkdocs.yml --site-dir
  <scratchpad>/doc/site` → exit 0, no `WARNING` lines (only the Material for MkDocs 2.0
  banner). Rerun after the last edit with the same result.
- Link and anchor check: scratchpad `doc/anchors.py <site> . <changed .md files>` (24, then 25 after Rework 1)
  resolves every relative link and `#anchor` against the built HTML ids, ignoring fenced
  code → `problems 0`. (The first run found the pre-existing `instructions.md` link,
  fixed above.)
- `git diff --check` → exit 0; every changed file ends with a newline.
- In-process MCP replay (scratchpad `doc/measure.py`, `doc/replay.py`, run with
  `backend/.venv/bin/python` and `fastmcp.Client(create_mcp())`, six packages accepted):
  - Nigeria edge `0129f5d5…` provenance 7,107 bytes, one window (two at 4,096), nine
    warnings; result keys include `archivedProvenanceSha256`; source artifacts are the
    manifest, the slim shard, the slim index, `relationships`, `evidenceArchiveRecord`.
  - Step 2: `buildsTowards`, confidence 0.72, nine warnings, five excerpts, omitted and
    excerpted flags true; `metadata.artifacts` = archived map, index, nodes,
    relationships.
  - Step 4: first page 7 edges, `byte_limit`; full paging 27 pages, 189 distinct edges.
  - Step 8: support relationship 1,049 bytes; component provenance 1,067; standard
    provenance 2,059; both provenance results carry `sourceDocument`,
    `attributionStatement`, `archivedProvenanceSha256`; source artifacts are the slim
    artifact and `evidenceArchiveRecord`.
  - Step 9: Nigeria LP summary 3,335 bytes; LP validation 1,806; LP unresolved 214; CBSE
    summary contains `needs_review`; LP summary artifact links are the five declared LP
    artifacts.
  - Step 9a: Ghana Mathematics `/unresolved` 42,831 bytes, three windows (11 at 4,096).
  - Step 10: `learningProgressionProvenance` → `resource_not_found`; `nodes` →
    `resource_access_denied`.
  - Nigeria manifest 20,186 bytes, two windows.
- `backend/.venv/bin/kgfegmcp-verify-evidence-archive all` → exit 0, location
  `IDinsight Google Drive`, six packages `ok`, 86 `ok` each; entry fields observed.
  `--help` lists `all` and `one`. The documented `uv … run` form was attempted and
  stopped by the sandbox (`~/.cache/uv … Operation not permitted`, exit 2); the venv
  entry point is the same console script. Fresh-clone counts (9 `ok`, 77 `missing`) are
  from the verification report's plain-checkout run, not rerun here.
- Measurements: per-package sizes (5.2–32.3 MB), largest slim shard 493,545 bytes,
  tracked files 963 / 102.6 MB, `data/` 84.9 MB, `data/graph_packages/` 83.9 MB,
  tracked `data/input_artifacts/` 1.0 MB, input sets on disk 671.4 MB, Git packs
  292.59 MiB, venv 319 MiB.
- Relied on without rerun (inputs unchanged since): image and stage contents (480
  files), smokes, rebuild reproduction, fresh-clone behavior and AC-002 equality, from
  the verification report and implementation review.
- Not run: test suite, lint and MCPB/Docker smokes. No source, test or packaging code
  changed. `backend/README.md` is copied into the MCPB stage as its README; the change
  is prose only and does not affect the stage smoke's inventory checks.

### Rework 1 (2026-10-14)

Recovery Frame 1 (`USER_REWORK`, `DOCUMENTATION`, `REVIEWING_FINAL` → `DOCUMENTING`):
the user asked for a recheck of every updated page for major correctness issues before
final review. No final review had started (no
`.standards/docs/reviews/<cycle>/final-deliverable.md`). Every changed page was reread
and its claims checked against `lp_graph.py`, `evidence.py`, `builder.py`,
`validator.py`, the build specs and earlier measurements; other pages were swept for
statements this change made false. Findings and corrections:

- `docs/reference/progression-tool.md` (missed in the first pass) said the manifest
  lists every checksum a progression result cites and that provenance holds
  "candidate references". The cited `learningProgressionProvenance` is now archived:
  its hash comes from the evidence archive record and its URI returns
  `resource_not_found`; candidate evidence is not served. Corrected.
- `docs/development/framework-package.md` said the builder stops if any listed input
  is missing. `_discover_detailed_artifacts` skips absent files in the `detailed/`
  directory (`continue`); only directly named files (delivery, shards) raise. It also
  told operators to move every accepted rebuild into `data/graph_packages/`, which
  would replace a sealed package's manifest when a rebuild reproduces its snapshot ID.
  Corrected: the verify step catches a partial restore, and a reproduced snapshot keeps
  the committed package.

Checks after the corrections: strict MkDocs build exit 0, no warnings; link and anchor
check over 25 changed pages → `problems 0`; `git diff --check` exit 0. No other page
needed a change. Downstream work to rerun: none, because no final-review or
synchronization work existed. The frame closes and the workflow resumes at
`REVIEWING_FINAL`.

### Rework 2 (2026-10-14)

Recovery Frame 1 (`USER_REWORK`, `DOCUMENTATION`, `REVIEWING_FINAL` → `DOCUMENTING`),
pushed again after Rework 1's frame closed: the user asked for a second recheck for
major issues. No final review had started. Two independent read-only reviewers (one
for the changed text, one sweeping every Markdown page) checked claims against code,
data and in-process server output; their findings were confirmed here before any
change. Every tool call and prompt rendering in the Claude Desktop walkthrough (steps
1–13, scratchpad `doc/replay_all.py`) was also replayed with the runtime-only packages:
every documented expectation held (six snapshots and graph-type lines, Nigeria 189/297,
19 tools, 9 prompts, 14 templates, 1 fixed resource; step 3: 0/2/6/8 connections, no
cursor; step 5: 5 standards, 5 edges, complete; step 6: two paths via `c4885674` and
`12b603df`, `depth_limit`; step 11: version 1.4.0, pinned snapshot, EVIDENCE ACCESS and
LINKS; step 12: identical to the native prompt; step 13: two scans, 7 per page with
`byte_limit`, cursors after three pages). Findings and corrections:

- `docs/data/framework-catalog.md` "Shared package properties" still said manifest
  schema `1.1`. Corrected to `1.2`.
- `docs/architecture.md` said each progression result names "the four package files"
  it was built from, all listed in the manifest. `learningProgressionProvenance` is
  archived and cited by hash only. Corrected.
- `docs/reference/resources.md` said the removed producer judgment "repeats the final
  judgment". In the archived provenance maps it equals `claim.judgment` for all 7,646
  `accepted` edges and differs for all 434 `corrected` edges (e.g. Nigeria
  `5966cb12…`: producer `buildsTowards` 0.78, final `relatesTo` 0.60). Corrected to
  describe actual behavior; the underlying scope premise is `DOC-001`.
- `docs/operations/deployment.md` gave `kgfegmcp-validate-packages one --runtime-only`
  without the required `--framework-id`/`--snapshot-id`. Corrected.
- `docs/getting-started/claude-clients.md` claimed results other than steps 2, 4 and
  7–10 had been "compared with the earlier packages"; that did not cover the prompt and
  workflow steps. Replaced with the full 2026-10-14 replay above.

Checks after the corrections: strict MkDocs build exit 0, no warnings; link and anchor
check over the 25 changed pages → `problems 0`; `git diff --check` exit 0.

## Discrepancies, Dependencies, and Remaining Work

### DOC-001 — AC-009 calls the removed producer judgment a duplicate

`Status`: `RESOLVED` `Owner`: `SCOPER`

- Failure type: `SCOPING`. Affected: `AC-009` (and its documentation under `AC-019`),
  scope `.standards/docs/scope/slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15.md`
  line 119 ("the duplicate producer judgment are not returned").
- Evidence: comparing `claim.provenance.producer_judgment` with `claim.judgment` in the
  six archived `data/input_artifacts/*/detailed/lp_relationship_provenance.json` files
  gives 7,646 equal (`checker_outcome: accepted`) and 434 different (`corrected`:
  Ghana English 96, Ghana Mathematics 31, CBSE 186, Tamil Nadu 37, Nigeria 5, Rwanda 79).
  The differing producer judgments total about 1.24 MB of JSON.
- Impact: the field-selection decision the request delegated ("which provenance
  fields to keep") rests on a false premise. For the 434 corrected edges the served
  record no longer shows the model's pre-correction decision, direction, confidence
  or rationale, although the scope's goal for this item is to keep "the judgment and
  its trace" and leave bulky candidate evidence in the archive. Keeping it only for
  corrected edges would add about 1.24 MB.
- Required correction: Scoper settles with the user whether the served per-edge
  record keeps the producer judgment for corrected edges, corrects AC-009's wording,
  and plans any reruns. Documentation then follows the decision: `resources.md` and
  the docstrings that call it a duplicate (`resources/models.py`
  `RelationshipProvenanceResult`, `packages/evidence_models.py` `SlimTrace`), by the
  Documenter if behavior is unchanged or with the Developer's change otherwise.
- Resolution (2026-10-14): Scoper (`44cd750`) kept the producer judgment
  archive-only with the user and corrected AC-009 to say it matches the final judgment
  for accepted edges and is the pre-correction judgment for corrected edges. Behavior
  is unchanged, so no code, package or test rerun. `docs/reference/resources.md`
  (`5a8aca2f0424`, from Rework 2) already matches the new wording. Docstrings
  corrected by the Documenter (prose only): `packages/evidence_models.py` `SlimTrace`
  (`5ce8c3ef0840`), `resources/models.py` `RelationshipProvenanceResult`
  (`95fa404f1e3b`) and a third found on recheck, `packages/slim.py` `slim_lp_record`
  Returns (`6a708abd10af`). No "duplicate producer" wording remains in `docs/`,
  `backend/`, `README.md` or `packaging/`.

Non-blocking observations for Reviewer and Synchronizer (not documentation defects;
no AC depends on them):

- Runtime text, Developer-owned: the progression result's `artifactInventoryNotice`
  says the manifest "records every accepted artifact checksum"; the cited archived
  map's checksum is in the evidence archive record, which the manifest binds. Reading
  an archived name returns the correct `resource_not_found` code with the message "The
  declared artifact does not have an approved resource exposure contract", although
  the name is not declared. The docs describe the codes, not these messages.
- Pre-existing: `dist/kgfegmcp-0.1.0.mcpb` is tracked and contains old snapshot IDs.
  It is a build artifact, not documentation.
- Pre-existing and left unchanged: `docs/operations/cli.md` and steps 4–5 of
  `framework-package.md` pass `--spec ./package-build-spec.json`, although the LP
  section notes that `uv --directory backend` changes the working directory.
- Client runs in Claude Desktop and claude.ai (2026-10-08) predate the runtime-only
  packages; the walkthrough says so. Whether the hosted deployment serves the new
  packages depends on a user-owned deployment.
- `.standards/CONTEXT.md` describes the pre-change baseline (manifest `1.1`, committed
  evidence); Auditor reconciles it in a later audit.
- Pre-existing procedure gap: smoke checks pin current snapshot IDs
  (`cli/smoke_access.py`, `cli/smoke_checks.py`), so a rebuild that creates a new
  snapshot for a pinned framework also needs those pins updated before step 8 of
  `framework-package.md` passes. Not introduced by this change.

### Return after Scoper (2026-10-14)

Frame 2 closed with `RESUME` from `SCOPING`; Frame 1 remains. Checks on the current
tree (docs committed in `837b8d3`, scope in `44cd750`, the three docstring edits
uncommitted): strict MkDocs build exit 0, no warnings; link and anchor check over the
25 documentation pages changed in this cycle → `problems 0`; `git diff --check` exit 0.
For the three edited source files: `black --check`, `isort --check-only`,
`ruff check` and `pylint` exit 0, and both modules import. Running
`pytest --doctest-modules` on `slim.py` fails two examples with `NameError`
(`index_bytes`, `original_entry`): those examples use illustrative names, predate this
edit, and the project does not run doctests (no doctest setting in `pyproject.toml`,
Makefile or CI). The edits are docstring prose only, so verification and implementation
review evidence still applies; the final Reviewer sees them in the diff.

## Resume and Conclusion

- Full Documenter gate passes for the current inputs: every current AC has a
  documentation disposition, `DOC-001` is resolved, checks pass, and no Documenter
  obligation or blocking question remains.
- Frame 1 (owned here): no downstream work to rerun, because no final-review report
  (`final-deliverable.md`) or synchronization record exists. Pop it and `RESUME` at
  `REVIEWING_FINAL` (kind `FINAL_DELIVERABLE`) in a fresh session.
