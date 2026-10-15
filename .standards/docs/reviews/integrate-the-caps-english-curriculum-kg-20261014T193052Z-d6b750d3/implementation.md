<!-- STANDARDS
Artifact: REVIEW
Cycle: integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3
ReviewKind: IMPLEMENTATION
-->

# Review Report

`Cycle`: `integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3` `ReviewKind`: `IMPLEMENTATION`
`Status`: `COMPLETE` `User Style`: `NONE`

## Assessed Inputs and Scope

- **Workflow.** Cycle mode `STANDARD`, completion policy `FULL_DELIVERABLE`. Entered by a `FORWARD` handoff from `TESTING`. No recovery frame and no outstanding obligations. No user style was selected for Reviewer.
- **Contract.**
  - Scope `.standards/docs/scope/integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3.md` (sha256 `50a623e035475fe1…`).
  - Design `.standards/docs/specs/integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3.md` (`0566cde98b2cff1d…`).
  - Current acceptance set: `AC-001`..`AC-015`, `AC-017`..`AC-021`, `AC-023`, `AC-024`, `AC-026`..`AC-028`, `AC-030`..`AC-032`, `AC-034`..`AC-037`. Retired and historical only: `AC-016`, `AC-022`, `AC-025`, `AC-029`, `AC-033`.
- **Upstream records.**
  - Development plan (`45c6a599e931a261…`): `COMPLETE`, `AFTER_IMPLEMENTATION`, `Current Increment: NONE`, DEV-001..DEV-012 `DONE`.
  - Verification report (`f753f9c21634b29f…`): `COMPLETE`, `Assessment Purpose: FULL`.
  - Context `.standards/CONTEXT.md` (`397206b4133bd43c…`).
  - These identities match the ones the Tester recorded.
- **Repository.**
  - `HEAD 989954b` on `tz6/fw`, with a clean tree before this report.
  - Comparison range `f9fdaa2..HEAD`. `f9fdaa2` is the design's cycle baseline. Its code is identical to `main` (`868eeb1`, the merge base); it adds only the STANDARDS install.
  - Outside `.standards/`, the range changes:
    - 8 files under `backend/src` (+799/−97);
    - 14 test files;
    - the one-line `packaging/mcpb/manifest.json`;
    - 92 new CAPS data and config files (80 package files under `…@2011+95ab377d1619`, 10 input-set files, the profile, and the overlay).
  - `git diff c2b698d HEAD -- backend/src config data packaging Dockerfile .dockerignore` is empty. Since the Tester's smoke and MCPB runs at `c2b698d`, only tests and `.standards/` records have changed.
- **Environment.**
  - macOS sandbox, `backend/.venv` (Python 3.13, the locked environment), offline.
  - Baseline comparisons ran against a temporary detached worktree of `f9fdaa2` in this session's scratchpad. It has since been removed.
  - Git-ignored local inputs used: the CAPS archive-only input set and `copy_receipt.json`.
- **Included.** Every changed backend file, read in full or as a diff with its surrounding code: `lp_paths.py`, `lp_compact.py`, `lp_models.py`, `lp_discovery.py`, `lp_traversal.py`, the annotation-only files, and `cli/smoke_progressions.py`. Also the CAPS profile against the design, the package manifest, the new and changed tests and fixtures, and the protected-path boundary.
- **Excluded.** Hand-maintained project documentation, which belongs to Documenter's phase (later dependency below). The six existing packages' content, which is unchanged by diff.
- **Session.** This conversation contains none of the authoring work for these artifacts. Session freshness and the authoring models' identities are not machine-certified.

## Contract and Evidence Assessment

The verification report cites each test and evidence item (E1..E11) in the "Assessed evidence" column. R-numbers refer to this review's checks under **Checks and Results**.

| Obligation / criterion | Assessed evidence | Current disposition |
| --- | --- | --- |
| `AC-001` | Tester E1; R6 receipt recheck | Supported. All 23 receipt entries still agree with the local copies and the read-only external sources. |
| `AC-002`, `AC-003` | `test_caps_identity_rights_and_counts`; R5 manifest | Supported. The package is `passed` with profile `<id>` `2.0`. Counts are 1 / 1,144 / 912 / 1,204 / 2,879 / 6,708, plus 1,144 hasChild (11,935 relationships). |
| `AC-004` | Tester E4 and Developer DEV-007, two independent rebuilds | Supported by reused evidence. The builder (`packages/`), the CAPS profile, and the spec are unchanged since both rebuilds, so the evidence still applies. |
| `AC-005` | Tester E3; R5 | Supported. 92 tracked CAPS files; the largest is 15,670,671 B. The largest non-delivery package file is 1,716,796 B, under 8 MiB. The input set has 10 tracked files and its archive-only inputs are ignored. |
| `AC-006` | Tester E3; R5 | Supported. Archive check ok 86 / missing 0 / mismatch 0. Full read-only validation reports `isValid` with no findings. |
| `AC-007`, `AC-008`, `AC-009`, `AC-010` | `test_caps_*` (3 tests); R5 profile check | Supported. Rights, grade mappings (R→K, 1, 2, 3), the exact anomaly disclosures, code search `none`, the hierarchy, and the statement types all match the design. |
| `AC-011`, `AC-012`, `AC-013` | Discovery and protocol tests; Tester E7 and E8 | Supported. Reused STDIO evidence still applies, because code, config, and data are unchanged since `c2b698d`. |
| `AC-014`, `AC-015` | Tester E9 and E10; R5 `.dockerignore` | Supported. Manifest `1.0.0` equals the project version, and the stage smoke passed. The allowlist admits `config` and `data/graph_packages` wholesale. `AC-015` rests on inspection; no image was built. |
| `AC-017` | Published-surface tests in R1 | Supported. 19 tools, 1 fixed resource, 14 resource templates, 9 prompts. |
| `AC-018` | R4 boundary diff and grep | Supported. The `backend/src` diff is exactly the design's change-boundary set. No CAPS ID, snapshot hash, or input-set name appears there. `packages/`, `profiles/`, and `catalog/` are unchanged. |
| `AC-019` | R1 full offline suite | Supported. 159 passed, exit 0. |
| `AC-023` | `test_published_progression_schemas`, `test_strict_integer_properties`, `test_approved_request_defaults` | Supported. `max_depth` accepts 1–16 with default 6. Path caps are 17 nodes / 16 relationships. The description says "maxima 16/20". Traversal is unchanged. |
| `AC-024` | `test_paths_match_baseline_enumerator`; Developer and Tester differentials; R3 | Supported. R3 used new requests and the real `f9fdaa2` code: 2,525 requests where the baseline was complete, 2,137 of them with paths. Paths, nodes, rehydrated evidence, reasons, flags, and `nextUnreturnedPath` were identical in every case. |
| `AC-026` | `assert_path_invariants` in every path test; R3; R7; R9 | Supported. Paths are always real stored hops returned as an ordered prefix. Incomplete results always report a reason. `path_limit`, `depth_limit`, and `byte_limit` are exact. |
| `AC-028` | CAPS sample tests; Tester E6 and Developer DEV-012 exhaustive runs; R7 | Supported. In R7, all 1,496 pairs of 9–13 hops plus 1,000 random pairs, each at the shortest depth and at 16 (4,992 requests), returned the oracle-length shortest path first. There was no budget stop; peak use was 1,231 inspections and 32 states. |
| `AC-030` | `test_paths_oversized_first_path_returns_ids`, the 13-hop test; R7 | Supported. All 10 thirteen-hop requests return the IDs-only result with `byte_limit` and no error. |
| `AC-032` | `assert_compact_form` in every path test; `test_paths_unlifted_field_rolls_back_later_path`; R7 | Supported. Rehydrated evidence equals `relationship_evidence` on every returned R7 result. A later path that would un-lift a shared field is rolled back. |
| `AC-034` | `test_compact_collection_and_traversal_results`, `test_compact_lifting_keeps_differing_and_null_fields`, schema test | Supported. Lifting is lossless on all seven packages, including mixed, empty, differing, and null cases. The schemas carry the rehydration rule. |
| `AC-035` | Tester E11 and Developer DEV-011 baseline differentials; R8 | Supported. Results are exact where the baseline was not size-stopped, and an in-order prefix where it was. In R8 every multi-relationship page held at least as many entries as the baseline, within the same envelope. |
| `AC-036` | Tester E10 and E11; R4 | Supported. The six packages, profiles, overlays, and input sets are unchanged. Tracked changes stay inside the boundary. `get_learning_progression` and the non-progression tools are byte-identical (Tester E11), and their code is untouched. |
| `AC-020`, `AC-021`, `AC-027`, `AC-031`, `AC-037` | — | Permitted later dependency (Documenter); see below. |

Evidence types are kept separate. The committed tests and E1..E11 are formal Tester evidence. DEV-NNN runs are Developer self-checks. R1..R8 are Reviewer diagnostics: they test the claims independently but do not replace Tester acceptance evidence.

## Checks and Results

All checks ran on 2026-10-15 against `HEAD 989954b`. Scratch scripts are in this session's scratchpad, and git-ignored local outputs are under `$TMPDIR/rev/`.

- **R1 Full offline suite.** From `backend/`: `UV_CACHE_DIR=$TMPDIR/uv-cache PYTHONDONTWRITEBYTECODE=1 UV_OFFLINE=1 uv run --locked --offline --no-sync pytest -q -p no:cacheprovider -m 'not costs-money' tests`. Result: **159 passed in 156.81 s, exit 0**.
- **R2 Static checks.** Ran `.venv/bin` `black --check`, `isort --check-only`, `ruff check`, `pylint --rcfile=.pylintrc`, and `interrogate` on the 8 changed `backend/src` files, plus `mypy src/kgfegmcp`. Result: all clean. black left 8 files unchanged, ruff passed, mypy found no issues in 123 files, pylint scored 10.00/10, interrogate exited 0.
- **R3 Independent path differential.** `rev_paths_diff.py` ran once with the `f9fdaa2` worktree code and once with `HEAD` code. Both used the HEAD seven packages and the same profile and prompt roots; the module paths are printed in the outputs.
  - Requests: 3,149, generated deterministically with seed 7331 (different from the Developer and Tester samples). They mix connected and unconnected pairs, with `max_depth` 1–12 and `max_paths` 1–20.
  - Where the baseline was complete (2,525 requests): 0 differences in `paths`, `nodes`, rehydrated evidence hash, reasons, `graphExhausted`, `scopeComplete`, or `nextUnreturnedPath`.
  - Where the baseline was truncated (624 requests): `HEAD` always extended the baseline's paths in order, returned more paths in 96, and never returned fewer. `HEAD` raised no errors.
- **R4 Boundary.** `git diff --stat f9fdaa2 HEAD`, excluding `.standards/` and the CAPS additions, lists only the design-boundary backend files, tests, and the manifest version line. `git diff --quiet f9fdaa2 HEAD` reports no change to:
  - `Dockerfile`, `.dockerignore`, `.gitignore`;
  - the release-please files, `CHANGELOG.md`, `backend/pyproject.toml`, `backend/uv.lock`;
  - `cli/smoke_checks.py`, `cli/smoke_access.py`;
  - `packages/`, `profiles/`, `catalog/`.

  All 92 changed `data/` and `config/` paths are CAPS additions. A grep for CAPS identifiers under `backend/src` found no matches.
- **R5 CAPS package and profile.**
  - `kgfegmcp-verify-evidence-archive one`: exit 0, ok 86, missing 0, mismatch 0.
  - Full `kgfegmcp-validate-packages one --read-only`: exit 0, `isValid: true`, `findings: []`, `passed`/`passed`, terminal revalidation.
  - Manifest counts and file sizes are as summarized under `AC-002`/`AC-005`. Profile fields were compared with the design's **Interpretation profile** contract and match.
  - The `.dockerignore` allowlist admits `config` and `data/graph_packages`.
- **R6 Receipt.** All 23 `copy_receipt.json` entries were re-hashed: source, destination, and receipt SHA-256 agree, and sizes match. Result: 0 mismatches.
- **R7 CAPS long connections.** `rev_caps_long.py` uses an independent BFS oracle. It covered every CAPS pair of 9–13 hops (1,496) plus 1,000 random shorter pairs, each at the shortest depth and at 16 with default `max_paths`: 4,992 requests.
  - Problems: 0. Every request identified the shortest path first with the oracle's hop count, over stored builds edges.
  - There were no `work_limit` or `queue_limit` stops. Peak use was 1,231 inspections and 32 states.
  - Rehydrated evidence matched `relationship_evidence` on every result that returned paths.
  - Outcomes by hops: 13 hops were IDs-only (10 requests). 12 hops were 9 full and 47 kept with `byte_limit`. 11 hops were 32 full and 162 kept with `byte_limit`.
- **R8 Latency and size.** `rev_timing.py` ran 48 requests on the six original packages for each tree: maximum traversals from the three highest out-degree sources, standard progressions and search at limit 100, and a direct 1-hop path.
  - Totals: baseline 0.34 s, `HEAD` 0.47 s. The slowest single call was 18 ms. There is no material latency regression.
  - Multi-relationship results held 0–5 more relationships within the envelope.
  - The 1-relationship path result grew by 96–124 characters on about 24,000.
- **R9 Randomized exactness probe.** `rev_fuzz_paths.py` built 400 random DAGs through the committed `Topology` double, with random relationship IDs and parallel edges. It ran `max_depth` 1–16 × `max_paths` {1, 2, 3, 5, 20}: 32,000 requests compared with brute-force enumeration.
  - Problems: 0.
  - Returned paths were always the ordered prefix.
  - `path_limit` and `depth_limit` appeared exactly when further or longer paths existed.
  - `byte_limit` appeared only when a further path existed, and `nextUnreturnedPath` was always the next path in order.
  - There were no budget stops.
- **Reused evidence, not rerun.** These Tester and Developer results were not rerun:
  - the repository and `--bundle-root` STDIO smokes (Tester E8 and E9);
  - the MCPB build (E9);
  - the real STDIO CAPS session (E7);
  - the rebuild determinism checks (E4, DEV-007);
  - the exhaustive 86,290-request all-pairs runs (E6, DEV-012).

  They still apply because `backend/src`, `config/`, `data/`, `packaging/`, and the Docker files are byte-unchanged since the commit they ran on (`c2b698d`). The smokes also need the sandbox lifted for their child `uv` cache.

## Findings

**No material findings.**

## Questions, Limitations, and Later Dependencies

- **Later dependency: Documenter.** The documentation ACs depend on Documenter's phase:
  - `AC-020`: corpus facts.
  - `AC-021`: CAPS catalog entry.
  - `AC-027`: path depth 1–16 and target-aware search.
  - `AC-031`: compact path form, rehydration, and the IDs-only fallback.
  - `AC-037`: compact form for the other three tools.

  The required evidence is Documenter's record with the edited documents and their checks, against the facts fixed in the design's **Technical Acceptance Criteria**. The MCPB README's `dist/kgfegmcp-0.4.0.mcpb` references are also Documenter-owned (design **Risks**).
- **Non-material observation: compact form for one relationship.** A result with exactly one relationship is about 100–125 characters larger in compact form than in full form, because of the wrapper objects (R8). The design's **Compatibility contract** says the compact result "is smaller". That holds for two or more relationships but not for one. This does not affect `AC-024` or `AC-035` on the seven packages, because single-relationship results are about 24,000 characters against the 100,000 limit. Documentation should not claim the compact form is always smaller.
- **Non-material observation: uncounted lookahead.** The `_has_more` lookahead in `lp_paths.py` reads adjacency without charging `examined_relationship_count`. It runs at most once per admitted path (≤ 20), so per-request work stays bounded by fixed caps. No AC pins counter values.
- **Non-material observation: commit type.** The target-aware search and depth ceiling were committed inside `504a8e5`, typed `docs(scope)`. Recent history shows the repository squash-merges PRs (for example `#33`, `#34`), so the PR title, not this commit type, will drive release-please. Both compact-form commits carry `BREAKING CHANGE:` footers.
- **Limitations.**
  - No Docker image was built; `AC-015` rests on inspection.
  - The STDIO smokes were not rerun here (reuse justified above).
  - Two stale worktree entries from earlier sessions remain in `git worktree list`. They are harmless; the user can run `git worktree prune`.

## Progress and Conclusion

- **Checked.** Every current AC and its technical criteria; all backend changes; tests and fixtures; data and boundary checks; R1–R9. Nothing remains unassessed for this gate.
- **Gate.** This gate passes. There is no unresolved finding or material gap. The only open items are Documenter's documentation ACs, which are permitted later dependencies. The next step under `FULL_DELIVERABLE` is `DOCUMENTING`.
- **Plain-language summary.** The work can move forward. The new framework is installed correctly and passes validation. The faster path search finds the same paths as before wherever the old one finished, and now also finds every long CAPS connection. The shorter result format loses no information. Independent re-checks of all of this found no problems. What remains is updating the user-facing documentation, which is Documenter's job.
