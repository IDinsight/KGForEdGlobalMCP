<!-- STANDARDS
Artifact: VERIFICATION
Cycle: slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15
-->

# Verification Report

`Cycle`: `slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15` `Mode`: `REVERIFY` `Status`:
`COMPLETE` `User Style`: `tony`
`Assessment Purpose`: `FULL` `Assessment Target`: `NONE`

## Assessed Inputs

- Scope `.standards/docs/scope/slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15.md`
  (`9db106a`, sha256 `c60c8d3d94ef…`): current set `AC-001`–`AC-019`, no retired IDs.
- Architecture `.standards/docs/specs/slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15.md`
  (`0a47aa8`, sha256 `2c6131ea35ec…`), including Interfaces 1–10 and its Technical
  Acceptance Criteria.
- Context `.standards/CONTEXT.md` (`af2a814`, sha256 `d0e61000cf18…`).
- Development plan `.standards/docs/development/slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15.md`
  (`845f469`, sha256 `a321112f3d9c…`): `COMPLETE`, cadence `AFTER_IMPLEMENTATION`,
  `Current Increment: NONE`, DEV-001–DEV-012 `DONE`.
- Implementation: HEAD `845f469` on `tz6/data-file-cleanup`, clean source tree. The
  plan's handoff names `bd0110c` plus uncommitted changes to `validator.py`,
  `loader.py`, `evidence.py`, `evidence_models.py` and `verify_evidence_archive.py`;
  those are committed as `845f469` (`git diff bd0110c HEAD --stat` touches only those
  files, STATE and the plan). Active change: `2763e19..845f469` (21 source files under
  `backend/src/kgfegmcp`, `.gitignore`, the six input-set specs unchanged, six new
  snapshots). Tester dirty-tree content: the test files listed under Scenario Budget
  and this report; no source change.
- Data: six `1.2` snapshots (Ghana English `…@2019+f2a9ab5922a1`, Ghana Math
  `…@2019+ed3b9450718a`, CBSE `…@undated+21ece81a7ac5`, Tamil Nadu
  `…@2025-proposed-draft+82b183ba9acc`, Nigeria `…@undated+424e546e2284`, Rwanda
  `…@2025+7c2d6f401157`). The git-ignored archive-only files are present locally under
  `data/input_artifacts/<set>/` and verified against each record (Execution Evidence).
- Baseline for AC-002: commit `2763e19` (code and six `1.1` snapshots before the first
  cycle code change `59eac96`), extracted with `git archive` into the scratchpad.
- Environment: macOS Darwin 25.6.0, Python 3.13.9 (`backend/.venv`, dev extras),
  Docker 29.6.2. Commands ran in the Claude Code sandbox except where noted.
- Reason: initial full verification after Developer's `RESUME` handoff (Recovery
  Frame 1 closed; no Tester work had started, so no earlier report existed).
- Session: fresh Tester chat started with `/tester`; it holds no Developer authoring
  history. Client metadata cannot certify freshness.

## Acceptance Evidence

Test names are under `backend/tests/kgfegmcp/`; `TEA` = `test_evidence_acceptance.py`,
`TROP` = `test_runtime_only_packages.py`, `TPR` = `test_progression_resources.py`,
`TPL` = `test_progression_lookup.py`. "Scratch" scripts live in the session scratchpad
(`scripts/`, logs in `logs/`); Execution Evidence gives their commands and results.

| AC / technical criterion | Tests or checks | Disposition and evidence |
| ------------------------ | --------------- | ------------------------ |
| AC-001 runtime-only layout; TAC: `1.2` declares exactly Interfaces 1, archive-only kinds and `1.1` rejected, no `1.1` package/path/fixture remains | `TROP::test_accepted_manifests_declare_only_runtime_files`, `TROP::test_manifest_rejects_retired_contracts` (4 rows); scratch `inspect_packages.py`; `grep` of `backend/` | VERIFIED. Six manifests `1.2`/`passed`, exactly 79 declared runtime artifacts at the Interfaces 1 paths, no archive-only key at any depth, record lists all eight archive-only kinds as `runtime: false`. `1.1` → `manifest_version_unsupported`; archive-only `null` field, archive-only additional name, undeclared record → `manifest_invalid`. No `1.1` fixture or snapshot remains (old tests reworked; `data/graph_packages` holds only the six `1.2` snapshots). |
| AC-002 served content unchanged; TAC: delivery hashes equal, projections equal, progression `artifacts` differ only in the index hash | Scratch `dump_tools.py` + `compare_tools.py` (baseline `2763e19` vs `845f469`); `TPL::test_every_exact_edge_preserves_accepted_evidence` (reworked); evidence tier `slim_projection_mismatch` check in all six acceptances; existing `test_progression_regressions.py` | VERIFIED. 13,863 paired MCP tool calls (in-process `fastmcp.Client`) on the baseline (`1.1`, `2763e19`) and current (`1.2`) servers, after replacing old snapshot/graph-package IDs (raw and percent-encoded) and manifest hashes: delivery nodes/relationships hashes equal for all six; `get_framework`, `get_framework_statistics`, every `get_standard`, sampled `get_standard_context`, `get_learning_components_for_standard`, `get_learning_component` identical; every `get_learning_progression` (8,080) and sampled standard-progression, traversal, paths and search results identical except `metadata.artifacts[1].sha256` (`learningProgressionProvenanceIndex`, all 10,035 citing results; entries 0, 2, 3 incl. the archived `learningProgressionProvenance` hash unchanged) and pagination cursors, whose decoded differences are only `manifestSha256`, `packageIdentity` and `payloadSha256`; `list_frameworks` items identical, only `catalogSha256` (a digest of the catalog, which carries snapshot identities) differs. Projections: evidence tier finds runtime and full-evidence projections equal on all six. Not sampled here: `search_standards` (Developer's DEV-008 comparison: differs only in its cursor), `compare_framework_evidence`, resource payloads (provenance resources change by design under AC-009/AC-012). |
| AC-003 tracked `data/` ≤ 100 MB | Scratch `inspect_packages.py` (`git ls-files -z data` sizes) | VERIFIED: 540 files, 84,851,042 bytes (84.9 MB). |
| AC-004 full-evidence checks at acceptance; TAC: every check `validate_learning_progression_evidence` runs today on the view, byte equality for every derived file, record holds path/size/hash | Real archive: `kgfegmcp-validate-packages one … --read-only` ×6; scratch `real_oracle.py`. Synthetic: `TEA::test_evidence_tier_accepts_synthetic_full_evidence`, `TEA::test_evidence_view_runs_full_lp_checks` (2 rows), `TEA::test_slim_artifacts_follow_the_contract` (3 rows), `TEA::test_record_binds_every_input_file` | VERIFIED. Six real packages pass the evidence tier with 0 findings. The full LP checks run on the evidence view (control passes; `{}` summary or original map → `lp_` findings). Independent oracle: real and synthetic slim LP/AS/LC artifacts equal originals minus the named fields plus `sha256` of canonical JSON. Record entries carry `packagePath`, `localPath`, `sizeBytes`, `sha256` and correct `runtime` flags for every input. Check semantics in `lp_validation.py` inspected: only the input type changed (view instead of package). |
| AC-005 acceptance never passes on missing/altered/inconsistent archive or mismatched slim artifact | `TEA::test_missing_archive_file_blocks_acceptance`, `TEA::test_altered_archive_file_fails_acceptance`, `TEA::test_faulty_slim_artifact_fails_acceptance` (lp-shard, lc-document), `TEA::test_evidence_view_runs_full_lp_checks`; scratch `policy_checks.py` | VERIFIED. Missing → exit 2 `evidence_archive_unavailable`, stays `pending`; unreadable (mode 000) → same; altered → `evidence_archive_checksum_mismatch`, `failed` (or `quarantined` under that policy); faulty LP shard → `slim_derivation_mismatch` (index and shard) plus `slim_projection_mismatch`, `failed`; non-JSON LC document → `slim_derivation_mismatch` plus `slim_entity_coverage_mismatch`, `failed`, no exception. |
| AC-006 fresh clone starts under `fail`, serves six; runtime revalidation needs only runtime files | Plain-checkout export (scratch `export/`); `TROP::test_runtime_tier_never_reads_archived_evidence`; `TEA::test_runtime_only_validation_needs_no_archive` | VERIFIED. Export without ignored files: bootstrap under `fail` → six `passed` packages; `--runtime-only` exit 0 ×6; default evidence tier exit 2 `evidence_archive_unavailable` ×6; verify command exit 1 (77 missing / 9 ok each). Full suite passes on the export. |
| AC-007 working tree with archive starts and serves the same; TAC: server never resolves `localPath` or reads `data/input_artifacts/` | `TROP::test_runtime_tier_never_reads_archived_evidence`; controlled failure (scratch `controls.py`); STDIO/HTTP smokes in the working tree | VERIFIED. Startup with a guard on every open/stat/read of `data/input_artifacts` loads six packages without a trip; the same guard trips immediately when the evidence tier runs. Smokes pass in the working tree that holds the archive. |
| AC-008 runtime revalidation rejects missing/extra/altered runtime file; policies unchanged | `TROP::test_runtime_tier_rejects_missing_and_extra_files` (2 rows), existing `test_progression_acceptance.py::test_copied_package_checksum_rejected`; scratch `policy_checks.py` | VERIFIED. Missing slim shard → `artifact_missing`, `package_declared_file_missing`; extra file → `package_undeclared_file`; altered → checksum finding. An accepted package altered after acceptance aborts startup under both `fail` and `quarantine` (`CatalogError`), as before; pending invalid → `failed`/`quarantined` per policy. |
| AC-009 slim per-edge record contents via resource and `read_evidence` | `TPR::test_slim_per_edge_trace_and_hashes` (reworked); existing `test_progression_evidence.py` (read_evidence reassembles native resource bytes); scratch `real_oracle.py` | VERIFIED. Six packages × both LP types: record equals the slim shard entry; identity, endpoints, decision, direction, confidence, full rationale (never shorter than the projection), full warnings, checker outcome, model configuration/settings, attribution and hashes present; the three removed fields absent; `archivedProvenanceSha256` equals the record's archived map hash; sources = manifest, shard, slim index, `relationships`, `evidenceArchiveRecord`. Real records equal originals minus the three fields. |
| AC-010 every LP edge resolves to one slim record; shards ≤ source limit | `TROP::test_slim_shards_cover_every_lp_edge`; runtime tier `lp_provenance_ids`; scratch `inspect_packages.py` | VERIFIED. Index binds 64 shards (path, hash, count); each edge in exactly one correctly placed shard; union equals LP edges (1051, 599, 3206, 907, 486, 1831); largest shard 0.49 MB ≤ 32 MiB. |
| AC-011 rights gating for per-edge provenance, `read_evidence`, generic artifact unchanged | `TPR::test_bulk_is_denied_independently` (reworked), `TPR::test_archived_and_record_artifacts_are_unavailable`; existing `test_full_text_denial_precedes_reads`, `test_source_bytes_refused`, `test_progression_evidence.py` denial parity; `policy.py` diff inspection | VERIFIED. Declared bulk artifacts (slim shard, `entityProvenance`, `learningComponentProvenance`, `nodes`) still `ResourceAccessDeniedError` on all six; per-edge denial precedes reads. Archived names and the record → `ResourceNotFoundError` (the design's documented "unavailable instead of denied" change). Policy diff removes only undeclarable names. |
| AC-012 standard and LC provenance from slim artifacts, attributable and traceable | `TROP::test_slim_entity_provenance_serves_attributed_entries` (2 rows); evidence-tier coverage check; scratch `real_oracle.py` | VERIFIED. Slim keys equal delivered standards with CASE UUID and LC node IDs on all six; sampled responses return the slim entry (no `candidate_source_refs`), `sourceDocument`, manifest `attributionStatement`, `archivedProvenanceSha256` = record hash = `originalSha256`; sources = slim artifact + record. |
| AC-013 rights gating for both resources unchanged | `TROP::test_slim_entity_provenance_denies_before_reads` (2 rows) | VERIFIED. Denied full-text (standard) and standard-resource (component) rights raise `ResourceAccessDeniedError` before any artifact read. |
| AC-014 no archive-only or large input file tracked; each ignored | Scratch `inspect_packages.py` | VERIFIED. 450 archive-only `localPath`s plus 12 input-set delivery copies untracked and matched by `git check-ignore --no-index`; `git ls-files -ci --exclude-standard` empty. |
| AC-015 small input files committed; rebuild reproduces each runtime package | Scratch `rebuild_all.sh`; `TEA::test_rebuild_reproduces_snapshot` | VERIFIED. Each set tracks `package_build.json` + 9 small files. All six unchanged specs rebuild the committed snapshot IDs with byte-identical artifacts; rebuilt pending packages pass the evidence tier. |
| AC-016 image and bundle hold only declared runtime files; smokes pass | `kgfegmcp-build-mcpb` stage, `kgfegmcp-stdio-smoke` (repo and stage), `kgfegmcp-http-smoke` (loopback and container), `docker build` | VERIFIED. Stage and image `data/` = 480 files = declared runtime files + manifests, no `input_artifacts`, built with the archive present locally; all smokes `passed` (19 tools, 14 templates, 9 prompts); container started with six accepted packages. |
| AC-017 CI suite passes without archive; synthetic coverage of AC-004/005; TAC: real validator code, passing + missing + altered + derivation-mismatch cases | Full suite on repo and on the plain-checkout export; `TEA` module | VERIFIED. 149 passed in the repo (parallel and serial random order) and on the export. The synthetic fixture runs the production builder, validator, verifier and CLIs (no mock of the verifier; only a faulty producer is simulated). |
| AC-018 committed record per package and a verify command | Scratch `inspect_packages.py`; `kgfegmcp-verify-evidence-archive all`; `TEA::test_archive_verification_reports_each_entry` | VERIFIED. Records list every archived file with path, size, SHA-256 and the fixed Drive location; the command reports 86 `ok` per real package (exit 0) and `missing`/`absent` plus `mismatch` with exit 1 when damaged. |
| AC-019 project documentation | — | PENDING LATER ROLE: Documenter (`DOCUMENTING`) must document the runtime/archive-only sets, slim provenance contracts, acceptance with and without evidence, archive restore, and image/bundle/clone effects; Reviewer and Synchronizer then assess it. Plan notes `docs/` still names old `1.1` snapshot IDs. Architecture records no architectural impact. |

## Scenario Budget

Allocations are new or materially reworked scenarios (parameter rows counted
separately). Reused unchanged coverage includes `test_progression_evidence.py`,
`test_progression_regressions.py`, `test_progression_acceptance.py::test_copied_package_checksum_rejected`,
and the remaining existing modules. No user additions.

| Source file | Reused coverage | Active-change allocations | User additions |
| ----------- | --------------- | ------------------------- | -------------- |
| `packages/evidence.py` | — | 5: TEA accepts, altered, missing, faulty lp-shard, faulty lc-document | NONE |
| `packages/loader.py` | existing checksum test | 5: TEA accepts (verifier hook), TEA batch-skips-terminal (`read_manifest`), TROP never-reads-archive, TROP missing, TROP extra | NONE |
| `packages/lp_runtime.py` | — | 5: TROP never-reads-archive, TROP inconsistent ×4 (reinstated field, decision, record runtime, record key) | NONE |
| `packages/evidence_models.py` | — | 1: TROP inconsistent record-key row | NONE |
| `packages/lp_validation.py` | — | 2: TEA evidence view ×2 (replace removed `test_evidence_rejects_missing_required_content` ×2) | NONE |
| `packages/slim.py` | — | 3: TEA slim contract ×3 | NONE |
| `packages/builder.py` | — | 3: TEA accepts, rebuild reproduces, record binds inputs | NONE |
| `packages/validator.py` | — | 2: TEA batch skips terminal, batch no partial transitions | NONE |
| `packages/models.py` | — | 4: TROP retired contracts ×4 | NONE |
| `cli/validate_packages.py` | — | 4: TEA accepts, altered, missing, runtime-only | NONE |
| `cli/verify_evidence_archive.py` | — | 1: TEA archive verification | NONE |
| `resources/service.py` | existing denial/source-limit tests | 5: TPR slim per-edge (replaces original-entry test), TROP entity serves ×2, TROP denies ×2 | NONE |
| `resources/models.py` | — | 3: TPR slim per-edge, TROP entity serves ×2 | NONE |
| `resources/policy.py` | `test_unknown_artifact_cannot_use_prefix_policy` | 2: TPR bulk denied (reworked), TPR archived/record unavailable | NONE |
| `services/learning_progressions.py` | other `TPL` tests | 1: TPL exact-edge citations (reworked) | NONE |
| six `data/graph_packages/*/*` snapshots | six-package bootstraps | 2 each: TROP runtime-files-only, TROP shards cover LP edges | NONE |

Test-only assets: `backend/tests/fixtures/evidence_fixtures.py` (synthetic input set
derived from the committed Nigeria runtime package, built with the production builder)
and conftest fixtures `synthetic_template` (session) and `synthetic_project`. Removed:
`test_progression_acceptance.py::test_evidence_rejects_missing_required_content`
(called the replaced `captured_contents`/`package` signature; replaced by the TEA
evidence-view rows). One assertion in `test_progression_acceptance.py` changed from
`== ()` to `not …` for pylint only.

## Execution Evidence

All from `backend/` unless noted, at `845f469` plus the Tester test changes.

- Baseline suite before Tester changes: `.venv/bin/pytest -rsPQ -m "not costs-money" -n auto
  -p no:randomly tests` → 112 passed, 5 failed (the plan's recorded Tester-rework
  list). Superseded by the runs below.
- Final suite: same command → 149 passed; `.venv/bin/pytest -q -m "not costs-money" tests`
  (serial, pytest-randomly on, as CI) → 149 passed.
- Plain checkout: `git ls-files -co --exclude-standard` exported to scratch `export/`
  (82 MB `data/`, 60 input-set files, no archive); from `export/backend` with
  `PYTHONPATH=export/backend/src PATHS_PROJECT_DIR=export`, `python -m pytest -q -m "not
  costs-money" -n 4 tests` → 149 passed (148 before the record-key row; rerun below).
  Same env: `python -m kgfegmcp.cli.validate_packages one … --runtime-only` exit 0 ×6;
  `one … --read-only` exit 2, `evidence_archive_unavailable` ×6;
  `python -m kgfegmcp.cli.verify_evidence_archive all` exit 1, `incomplete`;
  `bootstrap_application()` with `KGFEGMCP_INVALID_PACKAGE_POLICY=fail` → 6 `passed`.
- Lint/type: from `backend/`, `make lint` (isort, black, ruff, interrogate, mypy on
  `src/` and `tests/`, pylint, cloc) → exit 0; mypy "no issues" in 123 source and 24
  test files; pylint 10.00/10. Superseded: an earlier mypy run from the repository root
  with `backend/tests/...` paths reported clean, but there `tests.fixtures` imports did
  not resolve and became `Any`, hiding a type error (see Reverification below).
- Real archive acceptance: `.venv/bin/kgfegmcp-validate-packages one --framework-id <fw>
  --snapshot-id <id> --read-only` ×6 → exit 0, valid, `passed`, 0 findings, not
  persisted; `--runtime-only` ×6 → exit 0; `pending --read-only` → exit 0, `[]`.
- `.venv/bin/kgfegmcp-verify-evidence-archive all` → exit 0, 86 `ok` per package.
- Scratch `inspect_packages.py` (`backend/.venv/bin/python -I`, repo root): layout,
  record, shard, size and tracking results as in Acceptance Evidence; its one flagged
  item (12 untracked runtime `localPath`s) was my script's wrong assumption: those are
  input-set delivery copies that Interfaces 7 ignores.
- Scratch `rebuild_all.sh`: six `kgfegmcp-build-manifest --spec <copy, outputRoot →
  scratch>` exit 0; same IDs, `diff -rq` empty, manifests equal except `createdAt` and
  `validation`; rebuilt `pending --read-only` (`KGFEGMCP_GRAPH_PACKAGES_ROOT=<scratch>`)
  exit 0, six valid.
- Scratch `real_oracle.py`: the TEA slim-contract oracle against the six real packages
  and real input sets → all three kinds pass for all six.
- Scratch `controls.py` (controlled failures, no application change): the AC-007 guard
  trips on `input_artifacts/nigeria_math/detailed/as_kg_bundle.json` once the evidence
  tier runs; the slim oracle fails on packages built by a faulty LP or AS derivation and
  passes on correct ones. During development the faulty LP row first failed because an
  appended suffix left the 512-character projection unchanged; the mutation now
  prefixes the rationale (test fix, not a product defect).
- Scratch `policy_checks.py` (synthetic projects, real CLI): altered archive with
  `--invalid-package-policy quarantine` → exit 1, `quarantined`; archive shard at mode
  000 → exit 2 `evidence_archive_unavailable`, `pending`; accepted package with a
  runtime file altered afterwards → startup `CatalogError` under `fail` and under
  `quarantine`.
- Smokes (sandbox disabled: the STDIO smoke launches `uv`, whose `~/.cache/uv` the
  sandbox denies — sandboxed attempt failed with "Operation not permitted"; the HTTP
  server binds a port): `kgfegmcp-stdio-smoke` → `passed` (19 tools, 14 templates,
  9 prompts, 15 resource reads); `kgfegmcp-build-mcpb --output <scratch> --stage-output
  <scratch>` exit 0, stage `data/graph_packages` = 480 = declared + manifests, no
  `input_artifacts`; `kgfegmcp-stdio-smoke --bundle-root <stage>` exit 0; local
  `python -m kgfegmcp.http_server` (`PORT=8765`, policy `fail`) + `kgfegmcp-http-smoke`
  → `passed`, server stopped.
- Docker: context = plain export plus the restored archive copied into
  `data/input_artifacts`. First `docker build -q` exited 1 with no captured cause; an
  identical `docker build --progress=plain` succeeded. Image `/app/data` = only
  `graph_packages`, 480 files, 0 `input_artifacts` paths; container (policy `fail`)
  logged `accepted_package_count=6`, `kgfegmcp-http-smoke` → `passed`; container and
  image removed.
- AC-002: baseline extracted with `git archive 2763e19 backend/src config data/graph_packages`
  into scratch `baseline/`; `PYTHONPATH=<baseline>/backend/src PATHS_PROJECT_DIR=<baseline>
  .venv/bin/python scripts/dump_tools.py logs/tools_old.json` (imports confirmed from the
  baseline tree) and `PATHS_PROJECT_DIR=<repo> .venv/bin/python scripts/dump_tools.py
  logs/tools_new.json` → 13,863 calls each, 0 errors; `scripts/compare_tools.py` results
  as in the AC-002 row (same call keys, delivery hashes equal).

## Reverification

User-reported verification defect after the first `COMPLETE` handoff (recovery Frame 1,
`USER_REWORK`, `VERIFICATION`, from `REVIEWING_IMPLEMENTATION`): `make lint-mypy` →
`test_evidence_acceptance.py:548: Invalid index type "str" for
"dict[_SnapshotId, SyntheticProject]"`. Cause: the pending-batch test converted
discovered snapshot IDs to `str` before indexing a `SnapshotId`-keyed dict. Correction:
index with the discovered `SnapshotId` values unchanged (test-only; same scenario and
allocation, no assertion weakened). Inputs otherwise unchanged (source still `845f469`,
same contract and data), so the other evidence stays valid. Reruns: `make lint` exit 0;
`.venv/bin/pytest -q -m "not costs-money" -n auto -p no:randomly tests` → 149 passed.
No Reviewer work had started (no review report exists).

## Open Findings and Dependencies

- AC-019: later-role dependency on Documenter (evidence still required: documentation
  record covering the items in the AC row), then final Reviewer and Synchronizer.

## Resume or Handoff

Full verification is complete for the current implementation (`845f469`) plus the
Tester test changes listed under Scenario Budget. Every current AC has passing
evidence except AC-019, a permitted later-role dependency on Documenter. No
implementation, upstream or verification defect is open; no recovery is active.

For the independent Reviewer (review kind `IMPLEMENTATION`): inputs are the scope,
architecture, context and plan identities in Assessed Inputs; the test changes (one
new fixture module, two new test modules, three reworked modules, conftest fixtures);
and this report's execution evidence. Commands needing the local archive, `uv` cache
or port binding are marked; the synthetic fixture is the archive-free evidence-tier
path CI runs. Observations for downstream roles, not defects: the six input-set
delivery copies are git-ignored as Interfaces 7 requires; the Developer's note that
locally built package directories are `0700` (pre-existing builder behavior) did not
affect the Docker check, which built from an export.
