<!-- STANDARDS
Artifact: REVIEW
Cycle: integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3
ReviewKind: FINAL_DELIVERABLE
-->

# Review Report

`Cycle`: `integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3` `ReviewKind`: `FINAL_DELIVERABLE`
`Status`: `COMPLETE` `User Style`: `NONE`

## Assessed Inputs and Scope

- **Workflow.** Cycle mode `STANDARD`, completion policy `FULL_DELIVERABLE`. Entered by a `FORWARD` handoff from `DOCUMENTING`. No recovery frame, no outstanding obligations, `BlockedOn: NONE`. No Reviewer user style was selected (and `.standards/user-styles/reviewer/` does not exist).
- **Contract** (sha256 prefixes, unchanged during this review):
  - Scope `.standards/docs/scope/integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3.md` `50a623e035475fe1`.
  - Design `.standards/docs/specs/integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3.md` `0566cde98b2cff1d`.
  - Current acceptance set: `AC-001`..`AC-015`, `AC-017`..`AC-021`, `AC-023`, `AC-024`, `AC-026`..`AC-028`, `AC-030`..`AC-032`, `AC-034`..`AC-037` (32 IDs). Retired and historical only: `AC-016`, `AC-022`, `AC-025`, `AC-029`, `AC-033`.
- **Upstream records:**
  - development plan `45c6a599e931a261` (`COMPLETE`, DEV-001..DEV-012 `DONE`, `Current Increment: NONE`);
  - verification report `f753f9c21634b29f` (`COMPLETE`, `Assessment Purpose: FULL`);
  - implementation review `d7ce5dbcded84c02` (`COMPLETE`, no material findings);
  - documentation record `.standards/docs/documentation/integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3.md` `333c939a101bcb9c` (`COMPLETE`);
  - context `.standards/CONTEXT.md` `397206b4133bd43c` (last changed `eb21608`).

  These match the identities the Documenter and the implementation review recorded.
- **Repository.** `HEAD 3119147` on `tz6/fw`; the tree was clean apart from this report.
  - Cycle range `f9fdaa2..HEAD`. `f9fdaa2` is the design's cycle baseline; its code equals the `main` merge base `868eeb1`.
  - Since the implementation review's handoff (`b31da38`), only `.standards/` and 27 hand-maintained Markdown files changed (+393/−107 across 29 files): 24 under `docs/`, plus `README.md`, `backend/README.md` and `packaging/mcpb/README.md`.
  - `backend/src`, `backend/tests`, `config/`, `data/`, `packaging/mcpb/manifest.json`, `Dockerfile`, `.dockerignore`, `.gitignore` and `mkdocs.yml` are byte-unchanged since `989954b`, the commit the implementation review assessed. `backend/src`, `config/`, `data/` and the manifest are also unchanged since `c2b698d`, where the Tester's smoke and MCPB runs took place.
  - Cycle-wide, the changes outside `.standards/`, CAPS data/config, tests and documentation are exactly the 8 design-boundary files under `backend/src` and the one-line `packaging/mcpb/manifest.json` version (FR11).
- **Environment.** macOS sandbox, `backend/.venv` (Python 3.13, the locked environment), offline. The repository STDIO smoke ran outside the sandbox (FR10). Scratch scripts are in this session's scratchpad; outputs are under `$TMPDIR/frv/` (`/tmp/claude-501/frv/`). Both are session-local.
- **Included.**
  - Every changed documentation file, read as a diff together with its surrounding sections.
  - The documentation record's evidence, rechecked against the saved documents and actual behavior.
  - The behavior those documents describe: the path-search, compact-helper and model code the reference pages explain; the CAPS manifest, profile, overlay and delivery nodes; and the tests that `docs/development/testing.md` describes.
  - Prior implementation-review conclusions, rechecked against current content identities and the rerun suite.
- **Excluded.** A second line-by-line implementation review: the code is byte-identical to what the implementation review assessed (above), and FR1 and FR10 re-establish it at `HEAD`. Also excluded: an MCPB rebuild, a Docker image build, and Claude Desktop or claude.ai sessions (Limitations).
- **Session.** This conversation contains none of the authoring work for these artifacts. This review ran on Claude Opus 5.5. The authoring sessions' models are not recorded here, so a different-model comparison cannot be stated. Session freshness is not machine-certified.

## Contract and Evidence Assessment

Evidence types are kept separate. Tester evidence is E1–E11 and the committed tests (verification report). Developer self-checks are DEV-NNN. Implementation-review diagnostics are R1–R9. Documentation evidence is Documenter checks C1–C8. FR1–FR11 are this review's diagnostics (**Checks and Results**).

| Obligation / criterion | Assessed evidence | Current disposition |
| --- | --- | --- |
| `AC-001` | Tester E1; implementation review R6 | Supported by reused evidence. The receipt and local copies are unchanged inputs, and the external export is read-only. |
| `AC-002`, `AC-003` | `test_caps_identity_rights_and_counts` (FR1); FR4 manifest read | Supported. `passed`, snapshot `…@2011+95ab377d1619`, profile `2.0`. Counts are 1 / 1,144 / 912 / 1,144 hasChild / 1,204 / 2,879 / 6,708 (11,935 relationships). |
| `AC-004` | Tester E4; DEV-007 | Supported by reused evidence. The builder, spec, profile and inputs are unchanged since both rebuilds. |
| `AC-005` | Tester E3; R5; FR4 | Supported. The CAPS package is 86,880,508 B in 80 files, and the input sets total 1,343,745 B tracked. Each archive record has 86 entries: 9 committed and 77 archive-only. |
| `AC-006` | Tester E3; R5 | Supported by reused evidence; the package and archive inputs are unchanged. |
| `AC-007`, `AC-008`, `AC-009`, `AC-010` | CAPS tests (FR1); FR4; FR5 | Supported. Rights and verbatim attribution match the root node. Grades are K 385, 1 237, 2 262, 3 260. CAPS-only code search returns `capability_unavailable`, and cross-framework code searches return 0 CAPS hits. Identity matches the manifest. |
| `AC-011`, `AC-012`, `AC-013` | FR1; FR5; FR10; Tester E7 | Supported. Seven frameworks are listed, including with the LP filter. The repository STDIO smoke passes at `HEAD`. The E7 CAPS session is reused, since code and data are unchanged. |
| `AC-014`, `AC-015` | Tester E9, E10; R5 | Supported by reused evidence. The bundle is unaffected except that its `README.md` (copied from `backend/README.md`) now holds the updated text; the builder requires this file to exist but does not validate its content. `AC-015` rests on inspection. |
| `AC-017` | FR5 (19/9/1/14); FR10 | Supported. |
| `AC-018` | FR11; R4 | Supported. The boundary is unchanged since the implementation review, and the docs commit touched no code. |
| `AC-019` | FR1 | Supported. 159 passed at `HEAD`. |
| `AC-023` | FR5 schema and description; FR5 depth 17 | Supported. `maxDepth` runs from 1 to 16 with default 6, the description says "maxima 16/20", and 17 is rejected through input validation. |
| `AC-024`, `AC-035` | Tester E5, E11; R3, R8; `test_paths_match_baseline_enumerator` (FR1) | Supported by reused evidence; code and packages are unchanged. |
| `AC-026`, `AC-028`, `AC-030` | Tester E6; R7, R9; FR5; FR7 | Supported. FR7 also covers depths that earlier evidence did not: there were 0 problems over 14,838 more requests. |
| `AC-032`, `AC-034` | FR1; FR5 (rehydration helper on 13 results); R7 | Supported. |
| `AC-036` | Tester E10, E11; R4; FR11 | Supported. The six packages, profiles and overlays are unchanged. On the criterion's wording about documentation edits, see Questions. |
| `AC-020` | Documentation record (C5–C8); FR2–FR6, FR9 | Supported. Every changed figure checks out against current data: totals, sizes, file counts, input sets, the seven-package wording, archive and provenance sizes, corrected-edge counts, disk measurements and the bundle name. No stale six-framework or old-corpus statement remains. |
| `AC-021` | `docs/data/framework-catalog.md` CAPS section and rows; FR4, FR5 | Supported. It covers identity, the snapshot, hierarchy, terms and skill areas (Grade R: Emergent Reading and Emergent Writing; Grades 1–3: Reading and Phonics and Writing), Grade R labelling with the exact disclosure and per-grade counts, no codes with the exact disclosure and actual failure mode, rights with `Unknown`, the verbatim attribution, LP disclosures, and the 13-hop note. |
| `AC-027` | `docs/reference/progression-tool.md` **Paths**, bounds table and operations table; guide; protocol page; FR5, FR7 | Supported. It documents 1–16 with default 6, target-aware search in plain words, results unchanged where the earlier search completed, and exact `depth_limit`/`path_limit`. Its coverage statements hold at every depth tested. |
| `AC-031` | Reference **Shared evidence…** and **Paths**; FR5 | Supported. The IDs-only shape matches a live 13-hop result. The documented hop-evidence route (`get_learning_progression` → `provenanceUri` → `read_evidence`) read all 13 hops. |
| `AC-037` | Reference **Shared evidence…**; guide and protocol pointers; FR5 | Supported. The liftable fields and lifting rule match `lp_compact.py`. The CAPS example values match the live result. The documented Python helper rehydrated 97 entries from all four tools with 0 differences from `get_learning_progression`. |

Earlier later-role dependencies (`AC-020`, `AC-021`, `AC-027`, `AC-031`, `AC-037`, Documenter) are resolved by the documentation record and the documents above. None remains.

## Checks and Results

All checks ran on 2026-10-15 against `HEAD 3119147`, from the repository root unless noted.

- **FR1 Full offline suite.** From `backend/`: `UV_CACHE_DIR=$TMPDIR/uv-cache PYTHONDONTWRITEBYTECODE=1 UV_OFFLINE=1 uv run --locked --offline --no-sync pytest -q -p no:cacheprovider -m 'not costs-money' tests`. Result: **159 passed in 128.37 s, exit 0**.
- **FR2 Docs build and links.**
  - From `backend/`: `.venv/bin/mkdocs build --strict --config-file ../mkdocs.yml --site-dir $TMPDIR/frv/site`. Exit 0. The only non-INFO output is Material for MkDocs' upstream notice about MkDocs 2.0, and no anchor or link messages appeared at any level.
  - In the built site, all 8 new or affected link targets exist: `#paths`, `#shared-evidence-in-multi-edge-results`, `#shared-package-properties`, `#read_evidence`, `#claude-desktop-installation`, `#record-your-results`, `#restore-and-verify-archived-evidence` and `#learning-progression-inputs-and-updates`.
  - `git diff --check b31da38 HEAD` is clean.
- **FR3 Stale-statement scans.** `grep` over `docs/`, `README.md`, `backend/README.md` and `packaging/mcpb/README.md` for:
  - "six" counts;
  - the old totals and sizes (8,080, 3,039, 5,041, 13,902, 2,729, 84 MB, 101 MB, 480 files, 103 MB, 293 MiB, 670 MB, 32.3 MB);
  - `0.4.0.mcpb`;
  - path-depth 12, `maxima`, queue admissions, per-path cycle wording and the old first-path error wording;
  - direct reads of liftable fields;
  - framework lists that omit CAPS.

  No stale hit remains. The remaining "six" mentions are "the other six packages" (relative to CAPS), "six `related`", "six scan pages" and "six environment paths". The `0.4.0` mentions are dated observations.
- **FR4 On-disk facts.** `python3 -I <scratchpad>/frv_disk_facts.py <repo>`, plus an archive-record sum and `git count-objects -vH` / `du`. Every figure equals the documentation:
  - package sizes 5,203,387 B (Nigeria) to 86,880,508 B (CAPS), total 170,738,966 B, 560 files;
  - manifest totals 3,873 / 4,108 / 3,568 / 4,062 / 5,918 / 11,749 / 25,837; coded 1,439, unresolved 15, multi-parent 235;
  - checker outcome `corrected` 1,324 of 17,667 LP edges (CAPS 890);
  - LP provenance maps CAPS 119,245,153 B and seven-package total 220,595,948 B; CBSE 40,860,837 B;
  - archive-only total 1,289,938,414 B;
  - tracked 190,047,015 B; Git objects 292.59 + 19.48 MiB; `.venv` 318.9 MiB;
  - CAPS statement types, grades, Terms 1–4 per grade and skill areas per grade;
  - profile anomalies, code policy and rights; overlay ID `…-guidance` `2.0.0`, three prompt overlays, five shared-guidance sections, 19,470 B.
- **FR5 Live behavior probe.** `backend/.venv/bin/python -I <scratchpad>/frv_probe.py <repo>` runs the real server through `fastmcp.Client(create_mcp())`, with no network and no LLM. It covers:
  - Surface 19/9/1/14, seven frameworks, and seven with the `learning_progressions` filter.
  - The path tool's `maxDepth` schema (1–16, default 6) and "maxima 16/20".
  - All four compacted tools publish `sharedRelationshipEvidence` with the rehydration rule.
  - Walkthrough step 3 (0/2/6, `all` 8, complete).
  - Step 4: first page 9 with `byte_limit`, cursor and `nextRequest` present; pages `[9, 8, …, 9, 9, 1]`, 24 pages, 189 distinct.
  - Step 5 (5/5, complete, no reasons).
  - Step 6: the two documented 2-hop paths, `scopeComplete` and `graphExhausted` true, no reasons. At `maxDepth` 16 and `maxPaths` 20 there are still only 2 paths, so these are all the paths.
  - Step 13 scans, using the workflow's own requests: `buildsTowards` 9/8/8 = 25 and `relatesTo` 9/9/8 = 26, all `byte_limit`, with a cursor after page 3.
  - The CAPS reference example: first entry `00090dab…`, `ee045978…` → `309b1c92…`, confidence 0.68, 11 warnings, and the shared object's values.
  - The reference page's Python helper, extracted from the page and run on 13 results of all four tools (CAPS, Nigeria, Ghana Mathematics; one mixed-type result): 97 entries, 0 differences from `get_learning_progression`.
  - CAPS BFS: 43,145 connected pairs, five of 13 hops. The 13-hop IDs-only result has 0 paths, 0 relationships, `{}`, the two endpoint nodes, a 13-hop `nextUnreturnedPath` and `["byte_limit"]`. The same pair at `maxDepth` 12 returns `["depth_limit"]`, and at 17 it fails input validation. Reading the 13 hops the documented way succeeded for 13 of 13. 12-hop pairs return the path with its edges at 12 and 16.
  - Code search: CAPS-only returns `capability_unavailable`, and cross-framework queries return 0 CAPS hits.
- **FR6 Walkthrough steps 2 and 7–12.** `<scratchpad>/frv_probe_steps7_12.py`. Every value the walkthrough states still holds:
  - step 2: `buildsTowards`, 0.72, 9 warnings, 5 excerpts, flags, and no shared object on the exact lookup;
  - step 7: 7,107 B in one `full` window, and two windows at 4,096;
  - step 9: 3,335 / 1,806 / 214 B;
  - step 9a: 42,831 B in 3 windows;
  - step 10: `resource_not_found` and `resource_access_denied`;
  - step 8: the component and support IDs;
  - steps 11 and 12: prompt 1.4.0, both sections, and workflow text identical to the native prompt.

  This supports the walkthrough's statement that steps 7–12 did not change.
- **FR7 Path coverage at untested depths.** `<scratchpad>/frv_paths_claims.py` used the service directly with an independent BFS, 103 s, **0 problems**.
  - All 6,522 connected pairs of the six original packages at `maxDepth` 16 with default `maxPaths`.
  - All 1,496 CAPS pairs of 9–13 hops at every depth strictly between their shortest length and 16 (8,316 requests).

  The shortest path always came first: in `paths` with its edges, and IDs-only only for the 13-hop pairs. There was no `work_limit` or `queue_limit`; peak use was 1,213 inspections and 34 states. A first path's fit cannot get worse at smaller depths, because the size reservation grows with `maxDepth` (`_reserved_path`). This supports the reference page's general statement "when `maxDepth` is at least its length".
- **FR8 Size stops that name no next path.** `$TMPDIR/frv/kept_case.py`:
  - CAPS 9–13-hop pairs at shortest depth and 16 (2,992 requests): `byte_limit` with `nextUnreturnedPath` 1,939, without it 136.
  - Six original packages, every pair at shortest depth and 16 (13,044 requests): Rwanda 16 with and 5 without; none elsewhere.

  See the Questions section.
- **FR9 Documentation record identities.** The record's C8 lists sha256 prefixes for 27 files. 26 match the committed files. `docs/getting-started/claude-clients.md` is recorded as `ff450e9f7c67e309`, but the committed file is `afeb49f628955101` (24,715 B). No unreachable Git blob has the recorded hash, so the recorded version was never staged. See the Questions section.
- **FR10 Repository STDIO smoke.** `UV_OFFLINE=1 backend/.venv/bin/kgfegmcp-stdio-smoke`.
  - Inside the sandbox it exits 1: the child `uv` cannot open `~/.cache/uv/sdists-v9/.git` (Operation not permitted), the same limit the Tester recorded.
  - Outside the sandbox it exits 0 with `status: passed`, 19 tools, 9 prompts, 1 fixed resource, 14 templates and 15 resource reads; the server loaded 7 packages.
- **FR11 Boundary.** `git diff --name-only f9fdaa2 HEAD`, excluding `.standards/`, `data/`, `config/`, `docs/`, `backend/tests/` and the three READMEs, lists only the 8 design-boundary `backend/src` files and `packaging/mcpb/manifest.json`. `git diff --stat f9fdaa2 HEAD` over the Docker, release-please, changelog, `pyproject.toml` and `uv.lock` files is empty. `packaging/` changed only in `manifest.json` (version) and `README.md` (documentation).
- **Reused evidence, not rerun:**
  - E1 and R6 (receipt);
  - E3 and R5 (archive check and full validation);
  - E4 and DEV-007 (rebuild);
  - E5, E11, R3 and R8 (baseline differentials);
  - E6 and R7 (exhaustive CAPS pairs);
  - E7 (CAPS STDIO session);
  - E9 (MCPB build and bundle smoke);
  - E10 (Docker context inspection);
  - R9 (randomized exactness).

  They still apply because their inputs (code, packages, profiles, overlays, archive inputs, the MCPB manifest and the Docker files) are byte-unchanged since they ran. The one bundle-content change is the copied `README.md`, which affects no assessed property.

## Findings

**No material findings.**

## Questions, Limitations, and Later Dependencies

- **Later dependencies.** `NONE`. The implementation stage's Documenter dependencies are resolved (see the table).
- **Non-material: stale content identity in the documentation record (FR9).**
  - The record states that its checks ran on "the final content", but its identity for `docs/getting-started/claude-clients.md` does not match the committed file. The record therefore cannot by itself show which content its walkthrough replay (C5) covered.
  - This does not prevent assessing this gate. The record's 26 other identities match. This review assessed the committed content (`afeb49f628955101`) directly: every changed claim in it, and every numeric walkthrough expectation in steps 1–13, was replayed against the live server (FR5, FR6). The strict build, anchor and stale-statement checks also pass on it (FR2, FR3). No content error was found.
  - Synchronizer should reconcile the record's stale identity with the committed file, using this report's identity and evidence, and decide whether the record needs a Documenter correction.
- **Non-material, pre-existing: a size-stopped path result does not always name the next path (FR8).**
  - When a path fits but leaves no guaranteed room for another, the result keeps it and reports `byte_limit` with `nextUnreturnedPath: null`. This affects 136 of 2,992 long CAPS requests and 5 Rwanda requests.
  - The guide sentence "If a path result stops at the size limit, `nextUnreturnedPath` names the next path…" (`docs/guides/progression.md`) does not cover this case. The reference page's bullet "`byte_limit`: the next path did not fit" is loose for it.
  - Both the behavior and that guide sentence predate this cycle; the baseline `_stop_on_size` has the same keep-then-stop branch. The case lies outside the five documentation ACs, which concern the IDs-only shortest path, compact form, depth and corpus facts. The result still reports itself as incomplete.
  - This is a candidate for later documentation polish, not a gate blocker.
- **Non-material: "earlier server (0.4.0 or 1.0.0)".** `docs/getting-started/claude-clients.md` uses this phrase to explain differences. This repository still reports version `1.0.0` until the next user-owned release bumps it, so a reader cannot yet tell the released 1.0.0 from this branch by version number. The walkthrough's expected results are correct for this repository, and the routing-line check identifies stale servers. The design's **Risks** already record the MCPB version-drift follow-up.
- **Non-material: `AC-036` criterion wording.** The design's technical criterion says tracked changes outside the CAPS additions are limited to the change-boundary code, the manifest version and tests. It predates the documentation phase. The documentation edits, including `packaging/mcpb/README.md`, are required by `AC-020` (CONTEXT lists that README among the corpus-fact surfaces) and anticipated by the design's **Risks**. No code, config, data or packaging content outside the boundary changed (FR11).
- **Limitations.**
  - No MCPB rebuild or bundle smoke was run (E9 reused, as justified above).
  - No Docker image was built (`AC-015` stays inspection-based).
  - No Claude Desktop or claude.ai session was run; the walkthrough's client observations stay dated 2026-10-08, as the page says.
  - The repository smoke needed the sandbox lifted for its child `uv` cache.

## Progress and Conclusion

- **Checked.**
  - Every current AC and its technical criteria, against current evidence.
  - Every changed documentation file, against data and live behavior.
  - The documentation record's checks and identities.
  - The prior implementation-review conclusions, rechecked against unchanged identities and the rerun suite and smoke.
  - Cross-artifact consistency of scope, design, plan, verification, both reviews, the documentation record and the deliverable.

  Nothing remains unassessed for this gate.
- **Gate.** This gate passes. There is no unresolved material finding, no material assessment gap, no unresolved dependency and no blocking question, and every current AC has sufficient current evidence. Under `FULL_DELIVERABLE` the next phase is `SYNCHRONIZING`. Passing this review is not cycle completion or user sign-off.
- **Plain-language summary.** The work can move forward to the final consistency check.
  - The new South African curriculum is installed and works through the same tools as the other six.
  - The faster path search and the shorter result format behave as the documents say.
  - The updated documentation states the right numbers: frameworks, totals, sizes, grades and page counts, which were checked against the real data and a running server.
  - No problems were found that need fixing.
  - One bookkeeping slip should be tidied by the next role: the documentation record lists an out-of-date fingerprint for one page. That page itself was rechecked line by line and is accurate.
  - Two small wording points in the docs could be improved later, but they do not affect this release.
  - Not checked here: a live Claude Desktop session, a Docker image build and a fresh bundle build. Earlier bundle and server checks still apply, because the code and data have not changed since.
- **Next.** Synchronizer reconciles the current deliverable, this report and the earlier records, including the FR9 identity note. Evidence is in this report; scratch outputs are session-local.
