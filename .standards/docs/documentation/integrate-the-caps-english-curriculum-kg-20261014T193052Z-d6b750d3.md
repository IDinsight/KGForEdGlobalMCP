<!-- STANDARDS
Artifact: DOCUMENTATION
Cycle: integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3
-->

# Documentation Record

`Cycle`: `integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3` `Status`: `COMPLETE`
`Collaboration`: `AUTONOMOUS` `Target`:
`ACTIVE_CHANGE` `Target Detail`:
`integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3` `User Style`:
`tony`

## Assessed Inputs and Boundary

- **Workflow.** `STANDARD`, `FULL_DELIVERABLE`, entered by `FORWARD` from `REVIEWING_IMPLEMENTATION`. No recovery, no outstanding obligations, no blocker.
- **Contract and owner records** (sha256 prefixes, unchanged during this work):
  - scope `.standards/docs/scope/…d6b750d3.md` `50a623e035475fe1`;
  - design `.standards/docs/specs/…d6b750d3.md` `0566cde98b2cff1d` (facts to document under **Technical Acceptance Criteria**, `AC-027`, `AC-031`, `AC-037`, and **Compact Learning Progression results**, **Target-aware path search**, **Risks and Follow-up**);
  - plan `.standards/docs/development/…d6b750d3.md` `45c6a599e931a261` (`COMPLETE`);
  - verification `.standards/docs/verification/…d6b750d3.md` `f753f9c21634b29f` (`COMPLETE`, `FULL`; documentation ACs pending Documenter);
  - implementation review `.standards/docs/reviews/…d6b750d3/implementation.md` `d7ce5dbcded84c02` (`COMPLETE`, no material findings; observation that compact form is not smaller for a single relationship);
  - context `.standards/CONTEXT.md` `397206b4133bd43c` (**Relevant Existing Behavior** lists the hand-maintained surfaces with corpus facts).
- **Current ACs.** `AC-001`..`AC-015`, `AC-017`..`AC-021`, `AC-023`, `AC-024`, `AC-026`..`AC-028`, `AC-030`..`AC-032`, `AC-034`..`AC-037`. Retired, history only: `AC-016`, `AC-022`, `AC-025`, `AC-029`, `AC-033`.
- **Repository.** `HEAD b31da38` on `tz6/fw`, tree clean at entry. Comparison base `f9fdaa2` (the design's cycle baseline). `git diff f9fdaa2 b31da38` over `docs/`, `README.md`, `backend/README.md` and `packaging/mcpb/README.md` was empty at entry, so all documentation work for the cycle was outstanding. Implementation (`backend/src`, `config/`, `data/`, `packaging/`) was not edited.
- **Behavior sources inspected.** CAPS `package_manifest.json` (snapshot `…@2011+95ab377d1619`), profile `config/profiles/south-africa-dbe-caps-english-home-language-grades-r-3/2.0/profile.json`, prompt overlay, evidence archive records of all seven packages, CAPS delivery nodes and slim shards, `backend/src/kgfegmcp/services/lp_compact.py`, `lp_models.py` (compact models and `_REHYDRATION_RULE`), `lp_paths.py` (`_reserved_path`), `mcp/tools/learning_progressions.py` (descriptions), `packages/normalization.py` (flat vs envelope export), `cli/build_mcpb.py` (default output name), `cli/smoke_access.py` (graphTypes check), tests `test_progression_algorithms.py` and `test_progression_compact.py`. Plus in-process runs of the real server (Checks C2–C6).
- **Collaboration and target.** No explicit choice in request, scope or invocation, so the defaults `AUTONOMOUS` and `ACTIVE_CHANGE` apply.
- **Styles.** `.claude/skills/documenter/styles/universal.md` (`21dce31e96694331`); user style `tony` selected explicitly in the invocation, `.standards/user-styles/documenter/tony.md` (`dd6b47df4a5597cb`); `styles/python.md` for the one Python example added to the progression reference.
- **Editing boundary.** Hand-maintained Markdown under `docs/`, `README.md`, `backend/README.md`, `packaging/mcpb/README.md`. Nothing generates these documents (CONTEXT.md). `CHANGELOG.md` is release-please output and excluded by scope. `AGENTS.md` and `CLAUDE.md` hold only the managed STANDARDS block and `@AGENTS.md`, so no project agent guidance needed changes.

## Documentation Work and Evidence

Final content identities (sha256 prefixes) are under **Checks**, C8.

| Surface (audience) | ACs / design facts | Saved outcome |
| --- | --- | --- |
| `docs/data/framework-catalog.md` (users, operators) | `AC-020`, `AC-021`; design **Interpretation profile** | Seven-package intro; CAPS row and new totals (items 3,873, hasChild 4,108, LCs 3,568, supports 4,062, buildsTowards 5,918, relatesTo 11,749, all 25,837; coded 1,439, unresolved 15, multi-parent 235 unchanged); new CAPS section: identity, snapshot, hierarchy, terms and skill areas, Grade R labelling with the `K` disclosure and per-grade counts, no codes and the code-search disclosure and actual failure mode, rights posture with `Unknown` license and verbatim attribution, LP disclosures and 13-hop note; "All seven" shared properties. |
| `docs/index.md` (all) | `AC-020` | Seven packages; CAPS row. |
| `docs/reference/progression-tool.md` (client developers) | `AC-027`, `AC-031`, `AC-037`; design `AC-031`/`AC-037`/`AC-027` facts | New **Shared evidence in multi-edge results** section: the four tools, `get_learning_progression` unchanged, liftable fields, lifting rule, `{}` case, mixed-page example, abridged CAPS example, rehydration rule and a checked Python helper. New **Paths** section: order, `maxDepth` 1–16 default 6, `maxPaths` 1–20, target-aware search in plain words, same results where the earlier search completed, exact `depth_limit`/`path_limit`, counters, later-path `byte_limit`, IDs-only fallback shape, how to read each hop's full evidence (`get_learning_progression` → `provenanceUri` → `read_evidence`), evidence-scoped coverage statement. Bounds table depth 16; queue row renamed; Nigeria page example updated; `progression_result_too_large` row narrowed. Does not claim the compact form is always smaller (review observation). |
| `docs/guides/progression.md` (educators, client users) | `AC-020`, `AC-027`, `AC-031`, `AC-037` | Seven-curriculum totals; note on `sharedRelationshipEvidence` with link; depth 16 and target-aware search; IDs-only fallback pointer; Ghana Basic 5 page size. |
| `docs/reference/protocol-behavior.md` | `AC-027`, `AC-031`, `AC-037` | Error row, path caps 16/20, budget wording, first-path behavior, compact-form pointer. |
| `docs/getting-started/claude-clients.md` (Desktop users) | `AC-020`; `AC-036` behavior change | Walkthrough now describes the current repository: step 1 seven snapshots; step 4 nine then eight relationships, 24 pages; step 6 no `depth_limit`, `graphExhausted` true; step 13 eight or nine per page, 25/26 links. Each notes the earlier-server result. Run status and results table record the 2026-10-15 replay. |
| Data docs: `profiles.md`, `prompt-configs.md`, `rights-and-provenance.md`, `manifest.md`, `index.md`, `graph-packages.md` | `AC-020`, `AC-021` | CAPS rows and anomaly bullet; seven counts; CAPS among `Unknown` licenses; package size range 5.2–86.9 MB, about 171 MB. |
| Getting started: `index.md`, `local-installation.md`, `first-queries.md`; guide `framework-discovery.md` | `AC-020` | Disk figures re-measured 2026-10-15 (tracked 190 MB, packages 171 MB, Git objects 312 MiB, venv 319 MiB, archive restore about 1.29 GB); `Grade R` local-label example; seven snapshots. |
| Operations: `deployment.md`, `mcpb.md`, `cli.md`, `troubleshooting.md` | `AC-020`; design **Risks** (MCPB name) | 171 MB / 560 files for seven packages; smoke wording; bundle file name `kgfegmcp-1.0.0.mcpb` in commands and the default-output note. Dated 0.4.0 observations kept as history. |
| Development: `framework-package.md`, `testing.md`, `local-setup.md` | `AC-020` | Seven packages; CBSE and CAPS use envelope exports (checked in `normalization.py` and the CAPS combined export); CAPS input-set row; provenance maps (CAPS 119.2 MB, all seven about 221 MB); server/MCPB `1.0.0`; LP test guidance for the cycle guard, IDs-only first path, baseline-enumerator equality, CAPS sample and compact rehydration. |
| `README.md`, `backend/README.md`, `packaging/mcpb/README.md` (developers, operators) | `AC-020`; design **Risks** | Seven profiles/configs/packages; 64 shards per package; `kgfegmcp-1.0.0.mcpb`. Root README lists no frameworks (CONTEXT.md); only the bundle name changed there. |

AC dispositions (references only; wording stays with Scoper):

- `AC-020`: documented, all surfaces in the table. Final scan (C7) finds no stale six-framework count, total, size, file count or input-set statement; the remaining "six" mentions are unrelated (environment paths, related links, scan pages, "the other six packages").
- `AC-021`: documented in `docs/data/framework-catalog.md` CAPS section, plus `profiles.md` and `prompt-configs.md` rows.
- `AC-027`: documented in `docs/reference/progression-tool.md` (Operations table, Bounds table, **Paths**), with supporting text in the guide and protocol page.
- `AC-031`: documented in `docs/reference/progression-tool.md` **Shared evidence…** and **Paths** (when compact, when IDs-only, `nextUnreturnedPath`, reading each hop's evidence).
- `AC-037`: documented in **Shared evidence…** for the three collection/traversal tools, with the guide and protocol pointers.
- No separate documentation impact beyond the facts already documented above; their satisfaction evidence belongs to Tester's report and the implementation review, and this record does not restate or certify it:
  - `AC-001` (source copy), `AC-004` (rebuild determinism), `AC-005` (file sizes; the documented package sizes come from C6), `AC-006` (archive verification; the "86 ok" statement now says seven packages): build and acceptance facts, no user-facing change.
  - `AC-002`, `AC-003`: snapshot ID and counts are stated in the catalog (C6 manifest values).
  - `AC-007`, `AC-008`, `AC-009`, `AC-010`: their client-visible results are what `AC-021` documents (rights, Grade R, codes, identity).
  - `AC-011`: seven-framework catalog statements under `AC-020`, and walkthrough step 1 (C5).
  - `AC-012`, `AC-013`: no new tool, resource or prompt usage to document; CAPS works through the existing guides, and LP disclosures are noted in the catalog.
  - `AC-014`, `AC-015`: bundle and image contents updated under `AC-020` (seven packages, 560 files, 171 MB, `kgfegmcp-1.0.0.mcpb`).
  - `AC-017`: surface counts unchanged (19/1/14/9); existing docs already state them, confirmed in C5.
  - `AC-018`, `AC-019`: code-boundary and test-suite outcomes; `docs/development/testing.md` now describes the new LP test expectations.
  - `AC-023`, `AC-024`, `AC-026`, `AC-028`, `AC-030`: their client-visible behavior is what `AC-027` and `AC-031` document (bounds, same results where the earlier search completed, truncation reasons, long CAPS paths, IDs-only fallback).
  - `AC-032`, `AC-034`, `AC-035`: documented as the compact form under `AC-031` and `AC-037`; `AC-035`'s page-size effect is reflected in the updated page examples (C5).
  - `AC-036`: the visible changes it allows are documented (compact form; walkthrough steps 4, 6 and 13 now show the current results).

## Checks and Applicability

All from the repository root unless noted, 2026-10-15, macOS sandbox, `backend/.venv` (Python 3.13), offline. Scratch scripts are in `$TMPDIR/doc/` (session-local).

- **C1 Docs build.** `cd backend && .venv/bin/mkdocs build --strict --config-file ../mkdocs.yml --site-dir $TMPDIR/doc/site` (the CI workflow's tool, built into a scratch directory, not `gh-deploy`). Exit 0, no warnings, on the final content. The only extra output is Material for MkDocs' upstream notice about MkDocs 2.0.
- **C2 Internal links and anchors.** Scratch script parses every Markdown link in the changed `docs/` files and checks the target page and `id="…"` anchor in the built HTML: 164 links, 0 problems (final content). Covers the new `#paths`, `#shared-evidence-in-multi-edge-results` and `#shared-package-properties` targets.
- **C3 Compact-form example.** `check_example.py` extracts the Python block from `docs/reference/progression-tool.md`, runs it on real results through an in-process MCP client (`fastmcp.Client(create_mcp())`): search, standard progressions and traversal on Nigeria, CBSE and CAPS, plus a CAPS 2-hop path. Every result's text parses to its `structuredContent`; all 83 rehydrated entries equal `get_learning_progression`'s entry for the same ID; 2 results mix both relationship types. Rerun on the final file: same result. The abridged JSON example's values come from probe C4 output.
- **C4 Live behavior probe.** `probe.py` on CAPS: compact `get_standard_progressions` keys and shared object; a 2-hop path; the 13-hop pair at `maxDepth` 16 returns a normal result with empty paths/relationships, `{}`, 2 nodes, `nextUnreturnedPath` and `["byte_limit"]`; `maxDepth` 17 fails input validation ("17 is greater than the maximum of 16"); `maxDepth` 12 on that pair gives no paths with `["depth_limit"]`.
- **C5 Walkthrough replay.** `step1.py`, `walk.py`, `step35.py`: step 1 (7 snapshots, all with routing and included lines; filter keeps 7; Nigeria and CAPS counts present; surface 19/9/1/14), step 2 (type, confidence 0.72, 9 warnings, 5 excerpts, flags; no shared object on exact lookup), step 3 (0/2/6/8, IDs and sources), step 4 (first page 9 `byte_limit`; pages `[9, 8, …, 1]`, 24 pages, 189 distinct), step 5 (5 nodes/5 edges, complete, deepest supports), step 6 (two 2-hop paths, `scopeComplete` and `graphExhausted` true, no reasons), step 13 scans (pages 9/8/8 and 9/9/8; 13 and 15 pages). Steps 7–12 were not replayed: they use `read_evidence`, Learning Component and prompt tools whose results Tester E11 found byte-identical to the baseline.
- **C6 Fact sources.** Manifest counts and file sizes of all seven packages; per-package `checker_outcome` counts in slim shards (six: 434 corrected, CAPS 890, total 1,324 of 17,667); `learningProgressionProvenance` sizes from evidence archive records (CAPS 119,245,153 B, seven 220,595,948 B); archive-only input totals (seven 1,289,938,414 B); CAPS item grades (K 385, 1 237, 2 262, 3 260), statement types, terms and skill areas from delivery nodes; code search on CAPS raises `capability_unavailable` and a cross-framework code search has 0 CAPS hits; CAPS combined export rows carry `properties` (envelope branch of `_check_combined_export`); `git ls-files` sizes (190,012,309 B tracked; 170,738,966 B packages; 1,343,745 B input sets); `git count-objects -vH` (292.59 MiB packs + 19.23 MiB loose); `du` of `backend/.venv` (319 MiB); 560 package files.
- **C7 Stale-statement scans.** `grep` over the four documentation roots for six/seven counts, old totals (8,080, 3,039, 5,041, 13,902, 2,729…), 84 MB/101 MB, `0.4.0.mcpb`, path depth 12, `maxima`, per-path cycle wording and direct reads of liftable fields: no stale hit remains.
- **C8 Whitespace and identities.** `git diff --check` clean; no added line has trailing whitespace (pre-existing trailing spaces in untouched README lines left alone). Final sha256 prefixes: `README.md` `f2421d8b95d0832e`, `backend/README.md` `c8dd7de3de410012`, `packaging/mcpb/README.md` `775a40140fff9115`, `docs/data/framework-catalog.md` `9f322dbf38f5687e`, `graph-packages.md` `6a414054f4f7128b`, `data/index.md` `26420f08fd21b072`, `manifest.md` `e699af5e3704ee63`, `profiles.md` `964ee90a9302a1e3`, `prompt-configs.md` `22d86f2ddd75c012`, `rights-and-provenance.md` `2506e30d06a55cec`, `development/framework-package.md` `f91a11a09b4fcf59`, `local-setup.md` `e401de5919dc3b8b`, `testing.md` `8522133986fc135a`, `getting-started/claude-clients.md` `ff450e9f7c67e309`, `first-queries.md` `7bcb3785cb187a60`, `getting-started/index.md` `d9cbbfb588025f46`, `local-installation.md` `89c2cf25e59ffa8b`, `guides/framework-discovery.md` `9fd51994b11c77e5`, `guides/progression.md` `3849c142c30d7817`, `docs/index.md` `107e4934be853060`, `operations/cli.md` `5fa1821c99749d30`, `deployment.md` `6e1d7e145118a2a0`, `mcpb.md` `3fe04388f13bdb00`, `troubleshooting.md` `880ce9ca1fc679f2`, `reference/progression-tool.md` `b3cd7ae01354d454`, `protocol-behavior.md` `2a11fa147276cc7d`, `resources.md` `0027b0e88dff0b0d`.
- **Not run.** No Claude Desktop or claude.ai session (the walkthrough's client observations stay dated 2026-10-08); no Docker image build or image size measurement; no MCPB build (bundle name taken from `cli/build_mcpb.py` and the manifest version). These are documentation checks, not Tester acceptance evidence.

## Discrepancies, Dependencies, and Remaining Work

`NONE` blocking. No `DOC-NNN` entry was needed: every inspected behavior matched the design and Tester evidence.

Non-blocking notes, outside documentation ownership or scope:

- MCPB version drift will recur because release-please does not update `packaging/mcpb/manifest.json` (design **Risks**). The docs state the current name `kgfegmcp-1.0.0.mcpb` and that the archive name follows the manifest version; keeping them in step is release-tooling work.
- Uploading the CAPS input set to the Google Drive evidence archive is user-owned (scope).
- Disk and size figures are a dated 2026-10-15 measurement of this checkout; a fresh clone's Git size may differ, as the page says.

## Resume and Conclusion

- Target and full Documenter gate: complete. Every required surface was assessed and updated, the five documentation ACs have checked evidence, checks C1–C5 and C7–C8 passed on the final content, and no pending edit, question or Documenter-owned obligation remains.
- Blocking question: `NONE`.
- Next: `REVIEWING_FINAL`, Reviewer kind `FINAL_DELIVERABLE`, in a fresh session. Reviewer should rerun C1 and may rerun the scratch checks from the descriptions above. This record is documentation evidence, not cycle completion or sign-off.
