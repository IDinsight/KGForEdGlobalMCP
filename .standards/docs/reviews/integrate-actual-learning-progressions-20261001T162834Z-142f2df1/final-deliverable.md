<!-- STANDARDS
Artifact: REVIEW
Cycle: integrate-actual-learning-progressions-20261001T162834Z-142f2df1
ReviewKind: FINAL_DELIVERABLE
-->

# Review Report

`Cycle`: `integrate-actual-learning-progressions-20261001T162834Z-142f2df1` `ReviewKind`: `FINAL_DELIVERABLE`
`Status`: `COMPLETE` `User Style`: `NONE`

## Assessed Inputs and Scope

**Current assessment: Frame 1 Desktop rework, 2026-10-07.** Entered REVIEWING_FINAL by FORWARD from DOCUMENTING, then, before review began, the user's style rework pushed Documenter-owned Frame 2; the Documenter popped it and RESUMED this review. ARCHITECTING-owned Frame 1 remains (From/ResumeAt AWAITING_USER_SIGNOFF, RerunThrough SYNCHRONIZING). This review is a downstream rerun, not the frame owner. STANDARD/BROWNFIELD. Current inventory AC-001..AC-037; no retired IDs; scope unchanged. No blocker, pending cadence, baseline reconciliation or outstanding obligation, so no protocol chapter applies.

The 2026-10-06 COMPLETE conclusion was reopened: since then the runtime (four F1–F3 areas), the retained candidate and 16 documentation pages changed. Its exact bytes (SHA256 `b503f53a…`) are kept in [prior-final-review-20261006.json](final-frame1/prior-final-review-20261006.json). F-001..F-003 keep their IDs below because other records cite them.

- **Identities** (SHA256, all in [evidence-index.json](final-frame1/evidence-index.json)): HEAD `87c3595f209ff0097eec6799b62a2dbbda4ec5a3`, tracked tree clean at entry; scope `2eabb26b…`; architecture `f95eae97…`; CONTEXT `64d9b6d5…`; plan `8c3ee4e1…`; verification `a8fc1323…`; implementation review `037c9998…`; documentation record `e22a6968…`; synchronization record `0f13ea0c…` (predates the rework); STATE `3238181a…`. Every identity in the Documenter's [final-inputs.json](../../documentation/style-rework-20261007/final-inputs.json) (6 contracts, 51 documentation files, candidate, 6 evidence files) matched current bytes; no tracked documentation file is missing from it.
- **Boundary:** `a87ae15` (the synchronization point that reached sign-off before this rework) to HEAD. Product changes `a87ae15..1c31450` (35 non-workflow files) were assessed by the implementation review at the same identities. Since its assessed HEAD `73455ff`, only workflow records and documentation changed: `git diff --stat 8143ef4 HEAD -- . ':!.standards' ':!docs'` and `git diff --stat 108914e HEAD -- . ':!.standards' ':!docs'` are empty. Documentation changes are the 16 pages of `87c3595` (Frame 1 documentation plus the user's style rework). Affected unchanged boundaries (README files, unchanged LP tools, resources, native prompts) were checked through the replay and owner checker below.
- **Distribution:** `data/source_artifacts/learning_progressions/frame1-rework-dev022/kgfegmcp-0.4.0-frame1-rework.mcpb`, SHA256 `2f0b981ca94a595f1e2a78c70084609dfcbc0aba1d5f434d56341228f4f1c2d3`, 657 members, and sibling `bundle/`. Earlier 0.4.0 candidates (incl. `01df98e1…`) are history.
- **Session:** fresh Reviewer conversation started by this /reviewer invocation. It holds no scope, design, implementation, test or documentation authoring history. Client freshness and author-model metadata are unavailable; no attestation or model ranking is inferred.
- **Excluded:** deployment, publication, Claude Desktop or claude.ai execution, composed teaching output, external links, visual checks, unrelated refactoring.

## Contract and Evidence Assessment

**Full Verification Boundary** independently rechecked: plan COMPLETE, 23 steps all `DONE`, AFTER_IMPLEMENTATION, Current Increment NONE; verification COMPLETE, REVERIFY, FULL/NONE at HEAD `108914e` for candidate `2f0b981c…`. Nothing outside workflow records and docs changed after `108914e`, and the Reviewer reruns below (suite, closure) agree, so the full Developer and Tester gates hold for the current implementation and distribution. The Tester's open items were AC-026/027/036/037 and the shipped-README part of AC-035, all Documenter dependencies; they are resolved below.

"Supported" means current evidence suffices for this gate. Developer self-checks, Tester formal evidence and Reviewer diagnostics are kept apart in Checks.

| Obligation / criterion | Assessed evidence | Current disposition |
| --- | --- | --- |
| AC-019 (Frame 1 included graph types, filter, discovery text) | Implementation review behavior probe and Tester discovery-text tests at unchanged runtime. Reviewer replay: six Routing/Included line pairs, no single `Graph types:` line, every package line ends with LP availability and stored counts equal to the package edges, LP filter returns all six snapshots, capabilities lists 19/9/1/14 and six LP blocks, `get_framework` LP flags and counts. Docs (discovery guide, framework-tools, concepts, first queries, walkthrough step 1) match. | Supported. |
| AC-016, AC-029 (Frame 1 component citation text) | Implementation review exhaustive probe; Tester citation tests. Reviewer replay of walkthrough step 8: all seven citation fields in text, support relationship `5f89e75a…`, three text-derived reads complete in one window (1,049 / 541 / 3,077 bytes), `supports` record from component to standard. LC reference text matches source (`_NOT_READABLE` marking). | Supported. |
| AC-013, AC-014, AC-015, AC-016 (per-type scans, per-kind calls, page wording) | Implementation review and Tester workflow evidence. Reviewer replay: support plan has two calls (incoming_builds, related; no cursor following); teaching sequence and the four existing workflows call outgoing_builds, incoming_builds, related, with no `all` call or "page of 25"; Ghana BASIC 5 review renders two scans, each executed returns 7/7/7 links of its own type with `byte_limit` and a cursor left; `relationship_types` `["relatesTo"]` gives one scan with native/tool parity; `[]` means both. Prompt reference/guide and progression guide wording read against `prompts/learning_progressions.py`. | Supported (rendering and retrieval; composed output not run, as the docs say). |
| AC-026 | 16 changed pages read against code; owner checker copy (109 calls, 45 pages, 5,111 links) reproduces the Documenter's results byte for byte; strict build exit 0; 46 Reviewer claim replays pass. The docs' claim that an `all` page can stop before any related link appears is confirmed by real data (Rwanda node `8a274bb8…`: 11 stored builds, 1 related; the `all` page returns 8 builds, 0 related, `byte_limit`). | Supported. |
| AC-027 | Architecture page describes the current design in plain language ("How clients get results and evidence", reuse of existing services); testing and CLI pages list the new test modules and smoke checks, matching the tests and `cli/smoke_access.py`; local preparation and user-owned deployment stay separate. Development history removed as the user asked. | Supported. |
| AC-036 | Walkthrough steps 1, 3, 8, 9, 9a, 11–13 replayed (window counts tied to window size: Ghana hierarchy report 3 windows at 16,384 and 11 at 4,096; LP versus hierarchy unresolved records kept apart; Nigeria LP unresolved 214 bytes with empty claims; classroom note fits "write correctly number 6-9"); run status recorded per step; nothing claims a Desktop pass. | Supported. |
| AC-037 | Status table separates server STDIO/HTTP and bundle results (2026-10-07, matching Tester E6), user observations of an earlier build (2026-10-03), the prepared Desktop walkthrough and untested claude.ai; remote checklist covers included types and step 13. Shipped README equals `backend/README.md`; strict build passes. | Supported. |
| AC-035 | Reviewer closure at HEAD `87c3595`: all 657 archive members equal committed blobs, none missing, manifest 0.4.0; archive and stage `README.md` equal `backend/README.md` (`9ce0fc15…`). That README lists tools/prompts and links to the guides; it states no discovery text format, page size or workflow call pattern changed by this rework, so it is accurate without a rebuild. Tester E6 staged smoke covers the runtime. | Supported (shipped-instruction dependency resolved). |
| AC-021, AC-022, AC-025, AC-034 | Tester E6 repository STDIO, staged STDIO and loopback HTTP (exit 0, equal results), closure and 117-test suite; implementation review comparison of the three receipts. Runtime unchanged since; Reviewer suite rerun 117 passed and closure rerun pass. | Supported (local; not public-client acceptance). |
| AC-030, AC-031 | Native/tool parity (implementation review, Tester, Reviewer replay of steps 12–13); rendered-size headroom probe from the implementation review on unchanged runtime. | Supported. |
| AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-017, AC-018, AC-020, AC-023, AC-024, AC-028, AC-032, AC-033 | Packages, configuration and LP services unchanged since `a87ae15` (annotation-only edit aside); implementation review dispositions at the same runtime; Reviewer suite rerun 117 passed; owner checker re-executes the unchanged walkthrough steps 2, 4–7 and 10; obsolete-term scan in the owner checker passes. AC-020/AC-032 decisions unchanged and consistent with the plain-language architecture page. | Supported. |

## Checks and Results

All new runs on 2026-10-07 from `/Users/tzz/Projects/private/idi/KGForEdGlobalMCP` at HEAD `87c3595`, through [run_check.py](final-frame1/run_check.py) receipts (argv, cwd, environment, exit, duration, log hashes). Environment: `PYTHONDONTWRITEBYTECODE=1`, `PATHS_PROJECT_DIR` set, `UV_OFFLINE=1`, uv cache in session temp; locked backend environment used directly (`backend/.venv/bin/...`). In-process diagnostics block socket connections; no model or paid call. Reviewer diagnostics only, not Tester acceptance evidence.

1. `node .standards/bin/check.mjs`: passed at entry. On the rewritten report it first flagged AC-002..AC-012 as unaccounted because one table row used a range; the row now names each ID, and the check passes.
2. Identity reconciliation (inline script, results in [evidence-index.json](final-frame1/evidence-index.json), `11d76556…`): Documenter final identities all equal; candidate `2f0b981c…`.
3. [check-final-frame1-claims.py](final-frame1/check-final-frame1-claims.py) (`93204456…`): exit 0, **46 claims, 0 failed** ([results](final-frame1/final-frame1-claims-results.json), `5072ac14…`; [receipt](final-frame1/final-frame1-claims.command.json)). Covers the claims listed in the table for steps 1, 3, 8, 9, 9a, 11–13, the access-tools window counts, the prompt reference and guide call patterns and the informative `all`-page data case.
4. `mkdocs build --strict --config-file <root>/mkdocs.yml --site-dir $TMPDIR/frv/site`: exit 0 ([receipt](final-frame1/strict-build.command.json)).
5. Owner checker copy [check-docs-copy.py](final-frame1/check-docs-copy.py) ([binding](final-frame1/check-docs-copy-binding.json): only ROOT depth and output file changed; reverse substitution reproduces the owner script): exit 0, 109 tool calls, 45 pages, 5,111 local links. Output equals the Documenter's `results.json` byte for byte (`14571087…`).
6. `python -m pytest -q -p no:cacheprovider -m 'not costs-money' tests` (cwd backend): exit 0, **117 passed** in 73 s ([receipt](final-frame1/pytest-suite.command.json)).
7. Implementation review's [check-archive-closure.py](frame1-rework/check-archive-closure.py) (unchanged) on the candidate at HEAD `87c3595`: exit 0, 657/657 equal, nothing unmatched or missing, manifest 0.4.0 ([output](final-frame1/archive-closure-head.stdout), `62a58228…`). `unzip -p … README.md`, `bundle/README.md` and `backend/README.md` all hash `9ce0fc15…`.
8. `git diff --check 8143ef4 HEAD -- docs README.md backend/README.md packaging`: exit 0. (Over the whole range it flags only trailing spaces in captured Documenter stderr logs, which are receipts, not deliverables.)
9. Inspection: the 16 changed pages read against `prompts/learning_progressions.py` (scan rendering, per-kind calls, selection of up to 5 per type), `mcp/tools/learning_components.py` (citation lines, rights marking), `cli/smoke_access.py` and the two new test modules; READMEs scanned for statements touched by the rework (none); public docs scanned for development-history and jargon terms (only a pre-cycle `compare_framework_evidence` migration note in `backend/README.md` and a "Budget" table header in the progression reference remain, both useful to readers).

Harness iterations, not product results: two trial runs of the claims script before its recorded run. The first used a wrong key name for the CBSE count (`needs_review_claims`) and wrong arguments for the four existing prompts (they need `grade_or_stage` / `grades_in_room`); both were fixed in the script.

Reused prior evidence: implementation-review diagnostics (behavior, headroom, client-access probe) and Tester E5/E6 receipts on byte-identical runtime, tests and configuration. Superseded: the 2026-10-06 `client-access-final/` receipts describe candidate `01df98e1…` and the pre-rework runtime.

## Findings

**No material findings in this Frame 1 rerun.** No new P0/P1/P2 defect was established. F-001..F-003 come from earlier assessments, stay RESOLVED and keep their stable IDs.

### F-003 — Tester evidence does not cover the final retained 0.4.0 candidate

`Severity`: `P2` `Status`: `RESOLVED` `Owner`: `TESTER` `FailureType`: `VERIFICATION`

Historical 2026-10-06 finding about candidate `01df98e1…`, kept with its stable ID; full text in [prior-final-review-20261006.json](final-frame1/prior-final-review-20261006.json).

- **Reference / failure case:** the verification report named the earlier candidate `15c80166…` and left re-verification of the README-only rebuild `01df98e1…` pending; no Tester receipt identified or ran that bundle's own stage. AC-022, AC-025, AC-035.
- **Smallest correction:** Tester closure and staged STDIO smoke for the bundle offered for sign-off.
- **Reassessment:** RESOLVED 2026-10-06 (Tester E4 closure and staged smoke, rechecked by Reviewer). For the current candidate `2f0b981c…` the same requirement is met by Tester E6 (closure, staged STDIO of `frame1-rework-dev022/bundle`) and Reviewer Check 7.

### F-001 — Refresh the retained bundle after updating its README

`Severity`: `P2` `Status`: `RESOLVED` `Owner`: `DEVELOPER` `FailureType`: `IMPLEMENTATION`

Historical 2026-10-03 finding for the 0.3.1 deliverable, kept with its stable ID; not a claim about the current candidate. The shipped README told users to call the removed `collect_progression_evidence` tool. RESOLVED 2026-10-03 by a rebuilt archive whose README matched source, with fresh Tester stage evidence.

### F-002 — Reconcile the saved documentation and its completion evidence

`Severity`: `P2` `Status`: `RESOLVED` `Owner`: `DOCUMENTER` `FailureType`: `DOCUMENTATION`

Historical 2026-10-03 finding, kept with its stable ID. `docs/data/prompt-configs.md` said seven instead of nine prompts, and the Documenter's catalog parser depended on table padding. RESOLVED 2026-10-03: count corrected, parser made padding-independent, results reproduced by Reviewer.

## Questions, Limitations, and Later Dependencies

- Blocking user question: NONE; `Active Work.BlockedOn` stays NONE. Reviewer-owned obligation: NONE.
- Earlier dependencies resolved with current evidence: AC-026, AC-027, AC-036, AC-037 (Documenter content, Checks 3–5, 8, 9) and the shipped-README part of AC-035 (Check 7). Unresolved dependencies: NONE.
- Non-material: at the user's request, the Claude page no longer lists the user's 2026-10-07 observations of the first 0.4.0 build (they described defects fixed in the current build). The page still separates user observations (2026-10-03 row) from server evidence and untested clients, and claims no Desktop pass, so AC-037 holds. "Not yet run in Desktop" is accurate for the current bundle and walkthrough.
- Non-material: the remove-and-reinstall advice for a same-version bundle is an untested precaution, worded as "may keep the old copy", with a visible check in walkthrough step 1.
- Non-material (from the implementation review): a curriculum review with extreme selector input reaches the 64 KiB prompt cap sooner and then fails with an explicit error; realistic inputs keep at least 7 KiB of headroom.
- The synchronization record predates this rework; reconciling it is Synchronizer's work.
- Not validated locally: Desktop or claude.ai execution, composed teaching output, external links, deployment. The docs label these as prepared or untested; they are user-owned follow-up outside this gate.

## Progress and Conclusion

**COMPLETE — the FINAL_DELIVERABLE gate passes.** Every current AC (AC-001..AC-037) and relevant design criterion, including the Frame 1 discovery, citation and per-type/per-kind workflow criteria, has sufficient current evidence. There is no open P0/P1/P2 finding, material assessment gap, unresolved dependency, blocking question or Reviewer-owned obligation. Immediately before completion, the assessed inputs matched current content (HEAD `87c3595`, identities in the evidence index) and `node .standards/bin/check.mjs` passed.

Routing: Frame 1 is ARCHITECTING-owned and this review is a downstream rerun (RerunThrough SYNCHRONIZING), so take the normal FORWARD REVIEWING_FINAL → SYNCHRONIZING, FailureType NONE, preserving Frame 1. Synchronizer reloads current records and candidate `2f0b981c…`, reconciles every completed assessment with the offered deliverable and passes its own gate; only then does it pop Frame 1 and RESUME AWAITING_USER_SIGNOFF. This gate is not cycle completion, synchronization or sign-off.

Plain-language summary: the work can move forward to the Synchronizer. I found no problems. I re-ran the walkthrough steps that changed and checked them against the server: framework listings show learning progressions and their link counts, the components tool prints the links needed to cite evidence, the curriculum review reads "builds towards" and "relates to" links separately, and the reported wording problems (window counts, the wrong unresolved record, the classroom note) are fixed. The docs now read plainly and no longer carry development history, while still saying what was tested and what was not. Tests (117) pass, the docs build cleanly, and the bundle still matches the committed code. Still untested, as the docs say: real runs in Claude Desktop and claude.ai, and a full teaching workflow ending in a cited answer. Passing this review does not finish the cycle; synchronization and your sign-off come next.
