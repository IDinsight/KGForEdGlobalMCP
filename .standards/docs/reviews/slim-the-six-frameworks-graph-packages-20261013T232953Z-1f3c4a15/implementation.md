<!-- STANDARDS
Artifact: REVIEW
Cycle: slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15
ReviewKind: IMPLEMENTATION
-->

# Review Report

`Cycle`: `slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15` `ReviewKind`: `IMPLEMENTATION`
`Status`: `COMPLETE` `User Style`: `NONE`

## Assessed Inputs and Scope

- Cycle mode `STANDARD`, completion policy `FULL_DELIVERABLE`, project mode
  `BROWNFIELD`. Recovery inactive, no outstanding obligations, no blockers.
- Contract:
  - Scope `.standards/docs/scope/slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15.md`
    (last changed `9db106a`, sha256 `c60c8d3d94ef…`). Current set `AC-001`–`AC-019`;
    no retired IDs.
  - Architecture `.standards/docs/specs/slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15.md`
    (`0a47aa8`, sha256 `2c6131ea35ec…`): Decisions 1–6, Interfaces 1–10, Technical
    Acceptance Criteria.
  - Context `.standards/CONTEXT.md` (`af2a814`, sha256 `d0e61000cf18…`).
- Development plan `.standards/docs/development/slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15.md`
  (`845f469`, sha256 `a321112f3d9c…`): `COMPLETE`, `AFTER_IMPLEMENTATION`,
  `Current Increment: NONE`, DEV-001–DEV-012 `DONE`.
- Verification report `.standards/docs/verification/slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15.md`
  (`e5cfbee`, sha256 `c5ff6c5b298f…`): `COMPLETE`, `FULL`, `REVERIFY` after the
  user-reported mypy fix.
- Repository: branch `tz6/data-file-cleanup`, HEAD `e5cfbee`, clean tree (the only
  untracked path is this report). Active change: `2763e19..e5cfbee`. `2763e19` only
  installs STANDARDS on top of `main` (`7798c43`); the first cycle change is `af2a814`.
  The change covers 21 files under `backend/src/kgfegmcp`, `backend/pyproject.toml`,
  `.gitignore`, test modules and fixtures, the six new snapshot directories, the
  deleted `1.1` snapshots and the untracked input-set evidence. `845f469..e5cfbee`
  touches only tests, `STATE.md` and the verification report, so source, data and
  configuration equal what the Tester assessed.
- Local archive: the git-ignored evidence under `data/input_artifacts/<set>/` is
  present and matches every record (Checks).
- Environment: macOS Darwin 25.6.0, `backend/.venv` Python with dev extras, Claude
  Code sandbox.
- Inspected in full: `packages/evidence.py`, `evidence_models.py`, `slim.py`,
  `lp_runtime.py`, `cli/verify_evidence_archive.py`; diffs of `models.py`,
  `loader.py`, `validator.py`, `lp_validation.py`, `builder.py`,
  `cli/validate_packages.py`, `errors.py`, `resources/{lp,models,policy,service}.py`,
  `services/{learning_progressions,lp_models}.py`, `mcp/resources/register.py`,
  `.gitignore`; callers `bootstrap.py` and `catalog/repository.py`; the new and
  reworked tests' structure and main assertions; CI workflows and `.dockerignore`.
- Not inspected line by line: the 1,085-line synthetic fixture builder (judged by
  what the tests built on it assert and by its use of the production builder),
  smoke-check pin files beyond the snapshot IDs, and `docs/` (Documenter, AC-019).
- Session: fresh Reviewer chat with no authoring history from scoping, design,
  context, implementation or tests. The models that wrote the artifacts are not
  recorded, so whether this review used a different model cannot be confirmed.
  That limits the record but does not block the review.

## Contract and Evidence Assessment

| Obligation / criterion | Assessed evidence | Current disposition |
| ---------------------- | ----------------- | ------------------- |
| AC-001 / Interfaces 1–2, TAC (only `1.2`, exact runtime set, archive-only and `1.1` rejected, no `1.1` leftovers) | `models.py` diff (eight fields removed, names reserved, record and 64 shards required); Tester TROP rows; my manifest scan; `git grep` | Supported. Six manifests are `1.2`/`passed` with 79 checksums each and no archive-only key. The only `1.1` in tests is the rejection case. |
| AC-002 / TAC (delivery hashes, projections, progression citations differ only in the index hash) | Tester's 13,863 paired tool calls against `2763e19`; evidence-tier projection equality in each real acceptance (rerun by me); `services/learning_progressions.py` diff | Supported. `compare_framework_evidence` was not sampled, but `services/comparison.py` reads no package artifacts, so it runs on unchanged delivery data (non-material). |
| AC-003 / TAC ≤ 100 MB | My `git ls-files -z data` sum | Supported: 540 files, 84,851,042 bytes. |
| AC-004 / TAC (today's LP checks on the view, byte-equal derivations, record fields) | `lp_validation.py` diff: only the input type changes, codes and logic are kept; `evidence.py` re-derives every slim file and the record; my six real `--read-only` acceptances; Tester TEA rows and `real_oracle.py` | Supported. Hierarchy, framework-item and bundle files were only checksummed before; they are still checksummed against the record. |
| AC-005 (missing, altered, inconsistent or mismatched evidence never passes) | `evidence.py` control flow: absent or unreadable → `EvidenceArchiveUnavailableError`, no transition; checksum, LP, derivation, coverage and projection checks → blocking findings; Tester TEA rows | Supported. |
| AC-006 (fresh clone, `fail`, six served; runtime revalidation needs only runtime files) | My `git archive HEAD` export with no archive: bootstrap under `fail` → 6 `passed` runtimes, 0 excluded; `--runtime-only` exit 0; default evidence tier → `evidence_archive_unavailable`; suite 149 passed | Supported. |
| AC-007 / TAC (server never reads `localPath`) | `bootstrap.py` builds the loader with no verifier; `lp_runtime.py` never touches `local_path`; Tester's file-access guard | Supported. |
| AC-008 (runtime rejects missing, extra or altered files; policies unchanged) | Loader tree and checksum path unchanged; `catalog/repository.py` read-only, policy handling unchanged; Tester TROP and `policy_checks.py` | Supported. |
| AC-009 (slim per-edge record contents) | `slim.slim_lp_record` removes exactly three fields and adds `original_entry_sha256`; `RelationshipProvenanceResult` adds `archived_provenance_sha256`; Tester TPR and oracle | Supported. |
| AC-010 (each LP edge resolves to one slim record; shard ≤ limit) | `lp_runtime._slim_shard`/`_validate_slim_shards` (placement, counts, union = LP edges); Tester sizes (largest 0.49 MB) | Supported. |
| AC-011 / AC-013 (rights gating unchanged) | `policy.py` drops only undeclarable names; service rights calls precede reads; Tester TPR and TROP denial rows | Supported. Archived names now report unavailable instead of denied, as the design's Risks section lists for AC-019. |
| AC-012 / TAC (slim entity provenance attributable and traceable; exact coverage) | `service.py` adds `source_document`, `attribution_statement`, `archived_provenance_sha256`; `evidence._coverage_findings`; Tester TROP rows | Supported. |
| AC-014 / TAC (untracked and ignored) | `.gitignore` rules follow the `!/data/input_artifacts/` negation; my export holds only `package_build.json` and 9 small files per set | Supported. |
| AC-015 / TAC (rebuild reproduces IDs) | Committed specs build to the ignored `data/source_artifacts/...` root; Tester `rebuild_all.sh` and `TEA::test_rebuild_reproduces_snapshot`; source and data unchanged since | Supported for reproduction. The written procedure belongs to AC-019 (Documenter). |
| AC-016 / TAC (image and bundle contents, smokes) | `.dockerignore` allowlist unchanged (`data/graph_packages` only); Tester's MCPB stage, Docker image and smokes at `845f469` | Supported. Reused evidence; no source, data or packaging change since. |
| AC-017 / TAC (CI without archive; synthetic coverage on real validator code) | CI `tests.yml` runs only pytest; my committed-tree export suite → 149 passed; TEA uses the production builder, verifier and CLIs (only a faulty builder is simulated) | Supported. |
| AC-018 / Interfaces 3, 9 | `EvidenceArchiveRecord` model, builder `_evidence_archive_record`, verify CLI; my `verify-evidence-archive all` → 86 `ok` × 6 | Supported. |
| AC-019 (documentation) | `docs/` still names the old `1.1` snapshot IDs in four files; architecture records no architectural impact | Permitted later dependency: Documenter. |

## Checks and Results

All on 2026-10-14 at HEAD `e5cfbee`, working tree clean.

- `backend/`: `.venv/bin/pytest -q -m "not costs-money" -n auto -p no:randomly tests`
  → exit 0, 149 passed.
- `backend/`: `isort --check-only src/ tests/` → 0; `black --check -q src/ tests/` → 0;
  `ruff check -q src/ tests/` → 0; `mypy src/` and `mypy tests/` (Makefile flags) →
  no issues in 123 and 24 files. I ran non-mutating equivalents because `make lint`
  rewrites files with isort and black. Pylint and interrogate were not rerun; the
  Tester's `make lint` exit 0 was on the same source and tests.
- `backend/`: `.venv/bin/kgfegmcp-verify-evidence-archive all` → exit 0; archive
  location `IDinsight Google Drive`; each of the six packages `ok`, 86 `ok`,
  0 missing, 0 mismatch.
- `backend/`: `.venv/bin/kgfegmcp-validate-packages one --framework-id <fw>
  --snapshot-id <id> --read-only` for all six → exit 0, valid, `passed`, not
  persisted, 0 findings. This runs the full evidence tier against the local archive.
- Fresh-clone equivalent: `git archive HEAD | tar -x` into the session scratchpad
  `clone/` (82 MB `data/`, no archive files). With `PYTHONPATH=clone/backend/src
  PATHS_PROJECT_DIR=clone` (imports confirmed from the export):
  `bootstrap_application()` under `KGFEGMCP_INVALID_PACKAGE_POLICY=fail` → 6 package
  runtimes, 0 excluded, all `passed`; `python -m pytest -q -m "not costs-money" -n
  auto tests` (random order on) → 149 passed; Nigeria `validate_packages one
  --runtime-only` → exit 0; `--read-only` → `evidence_archive_unavailable`.
- Manifest scan (Python over `data/graph_packages/*/*/package_manifest.json`): all
  six `1.2`, `passed`, 79 checksums, no archive-only key.
- `git grep` for `1.1` manifest code or fixtures in `backend/`: only the rejection
  test row and unrelated profile, prompt and lock-file versions remain.
- `git grep` for the six old snapshot hashes outside `.standards/`: only
  `docs/data/framework-catalog.md`, `docs/getting-started/claude-clients.md`,
  `docs/guides/framework-discovery.md` and `docs/reference/access-tools.md`
  (AC-019).
- Reused Tester evidence: STDIO, HTTP loopback, MCPB stage and Docker smokes; the
  rebuild of all six; the AC-002 comparison; synthetic and tamper controls. I relied
  on these because `git diff --stat 845f469 e5cfbee` shows only test files, the
  verification report and `STATE.md` changed since they ran. I did not rerun them:
  they need the sandbox disabled (`~/.cache/uv`, port binding, Docker), and none of
  their inputs changed.

## Findings

**No material findings.**

## Questions, Limitations, and Later Dependencies

- AC-019 (permitted later dependency): Documenter must document the runtime and
  archive-only sets, the slim per-edge and entity provenance contracts (replacing
  "complete original"), acceptance with and without the archive, archive restore and
  verification, rebuild steps (including that committed specs build to the ignored
  `data/source_artifacts/...` root), the effect on the image, bundle and fresh
  clones, and the client-visible changes in the design's Risks section. The old
  snapshot IDs in the four `docs/` files must be replaced. Final Reviewer and
  Synchronizer then assess that evidence.
- Non-material: `compare_framework_evidence` was not part of the AC-002 comparison.
  Its service reads no package artifacts, and the delivery data it reads has
  identical hashes.
- Non-material observation (pre-existing, not introduced here): locally built
  package directories are `0700` because the builder stages with
  `tempfile.mkdtemp`. A Docker build from a working tree, rather than a checkout,
  could then produce an unreadable image. Railway builds from Git, so delivery is
  unaffected.
- Session limitation: model identities are unknown (see Assessed Inputs).

## Progress and Conclusion

- Assessment complete for all current ACs and technical criteria. No changed inputs
  need reconciling: this is the first review report for the cycle.
- The implementation review gate passes. The implementation matches the scope and
  design: one runtime tier at startup, the evidence tier only in acceptance, one
  shared derivation module, and `1.1` removed. Every AC except AC-019 has current
  evidence, and AC-019 is a permitted Documenter dependency. Developer claims held
  up under re-execution, and the Tester's coverage exercises real validator code.
- Plain-language summary: the work can move on to documentation. I found nothing
  that needs fixing. I reran the tests, type and format checks, the archive check,
  and full acceptance of all six packages against the local archive. I also started
  the server from a copy of the repository with no archive files, and it served all
  six frameworks. Not rerun by me, but unaffected by anything since the Tester ran
  them: the Docker, bundle and live-server smoke checks and the package rebuild. The
  project documentation still describes the old packages; updating it is the next
  step and is not part of this review.
- Next: `DOCUMENTING` (Documenter), then final review and synchronization.
