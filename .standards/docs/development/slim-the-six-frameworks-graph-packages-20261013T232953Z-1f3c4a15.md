<!-- STANDARDS
Artifact: DEVELOPMENT
Cycle: slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15
-->

# Development Plan

`Cycle`: `slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15` `Mode`: `STEPWISE`
`User Style`: `tony` `User Style Locked`: `true`
`Status`: `IN_PROGRESS` `Verification Cadence`:
`AFTER_IMPLEMENTATION` `Current Increment`: `NONE`

## Implementation Contract

- `Scope`: `.standards/docs/scope/slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15.md`
- `Architecture`: `.standards/docs/specs/slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15.md`
- `Request`: Slim the six frameworks' served packages to a runtime-only manifest
  `1.2` set, verify full evidence only at acceptance, keep archive-only evidence
  git-ignored under `data/input_artifacts/`, and record it by hash. Drop `1.1`
  support; no backward compatibility is kept.

## Build Steps

### DEV-001 — Shared slim derivation and evidence models

`Status`: `DONE` `Depends On`: `NONE`
`Acceptance`: `AC-004, AC-009, AC-010, AC-012, AC-018`

**Goal**

Add the pure, deterministic bytes-in/bytes-out derivation that turns legacy
evidence into the slim runtime artifacts and the evidence archive record, plus
the Pydantic models that parse them.

**Affected Area**

New `backend/src/kgfegmcp/packages/evidence_models.py` (record, slim LP index,
slim record, slim AS/LC documents) and `backend/src/kgfegmcp/packages/slim.py`.
Reuses `normalization._canonical_bytes` and `resources/lp.py` shard placement.

**Expected Outcome**

From a legacy package's bytes, `slim.py` yields the slim LP index (`2.0`), 64
slim shards, slim AS and LC entity documents, and record entries exactly as
Interfaces 3–5 define: three named fields removed, `original_*_sha256` added,
everything else verbatim, canonical bytes. Output is identical across runs.

**Self-Check**

Scratch script (outside the repo) runs the derivation on all six current
packages and asserts: removed fields absent, other fields equal to the original,
shard ID union equals LP delivery edge IDs, each shard ≤ 32 MiB, two runs
byte-equal; reports slim sizes. Then `black`, `isort`, `mypy`, `pylint` on the
new modules.

Result (2026-10-14, uncommitted working tree on `tz6/data-file-cleanup` at
`5f43d67` plus the two new modules): scratch script `dev001.py` (session
scratchpad), run as `backend/.venv/bin/python dev001.py <repo>` from the repo
root, passed every assertion for all six `1.1` packages. Slim totals: LP 55.9 MB
(largest shard 0.49 MB, CBSE), AS 3.5 MB, LC 1.8 MB. Shard ID unions equal LP
delivery edge IDs (1051, 599, 3206, 907, 486, 1831). Two runs byte-equal. From
`backend/`: `isort --check`, `black --check`, `ruff check`, `interrogate`
(100%), `mypy --explicit-package-bases --ignore-missing-imports` and `pylint`
(10.00/10) clean on both files. Dev extras were installed with `uv sync
--locked --extra dev --extra docs` (`UV_CACHE_DIR` in `$TMPDIR` for the sandbox).

---

### DEV-002 — Manifest `1.2` contract

`Status`: `DONE` `Depends On`: `DEV-001`
`Acceptance`: `AC-001, AC-008`

**Goal**

Teach the manifest model the `1.2` runtime-only contract (Interfaces 2).

**Affected Area**

`backend/src/kgfegmcp/packages/models.py` (`MANIFEST_VERSION`, version
validator, `PackageArtifacts`, `learning_progression_artifacts`, capability
rules, reserved names).

**Expected Outcome**

`1.2` manifests must declare `evidenceArchiveRecord`, cannot declare any
archive-only kind (as a field or an additional artifact), and require the slim
LP set when LP is included. The record and shards stay additional artifacts and
fail closed in the generic artifact resource. `1.1` acceptance stays only as a
temporary bridge until DEV-010 removes it after cutover.

**Self-Check**

Scratch script validates accepted and rejected `1.2` manifest variants. Existing
suite still passes against the current `1.1` packages; lint and type tools clean
on changed files.

Result (2026-10-14, working tree at `4394d0a` plus changes to `models.py`,
`builder.py`, `slim.py`): scratch `dev002.py`, run as
`backend/.venv/bin/python dev002.py <repo>`, accepted the current Rwanda `1.1`
manifest and a runtime-only `1.2` variant of it (79 declared artifacts, the
Interfaces 1 set), and rejected: `1.2` without the record; `1.2` declaring
`academicStandardsBundle`; `1.2` declaring `learningProgressionFinalClaims`;
`standardsFrameworkItems` as an additional artifact (reserved name); `1.2`
missing one slim shard; `1.1` declaring the record; version `1.3`. `dev001.py`
re-run after the `slim.py` refactor: same totals (LP 55.9 MB, AS 3.5 MB, LC
1.8 MB). From `backend/`: `.venv/bin/pytest -rsPQ -m "not costs-money" -n auto
-p no:randomly tests` → 117 passed; isort, black, ruff, mypy, interrogate
(100%) and pylint (10.00/10) clean on the three changed files.

**Implementation Notes**

`FULL_LAYOUT_MANIFEST_VERSION` (`1.1`) and `SUPPORTED_MANIFEST_VERSIONS` are the
temporary bridge; DEV-010 deletes them. The builder pins the bridge version
explicitly until DEV-003 switches it to the runtime-only layout. The new
`MANIFEST_VERSION` is `1.2`. `EVIDENCE_ARCHIVE_RECORD_NAME` and
`LP_PROVENANCE_SHARD_NAMES` now live in `models.py`; `slim.py` reuses them.

---

### DEV-003 — Builder produces the runtime-only layout

`Status`: `PENDING` `Depends On`: `DEV-002`
`Acceptance`: `AC-001, AC-004, AC-015, AC-018`

**Goal**

Make `kgfegmcp-build-manifest` build only runtime-only `1.2` packages from the
unchanged full-evidence input sets (Interfaces 8).

**Affected Area**

`packages/builder.py` (plan, copy, manifest creation, staged verification);
`cli/build_manifests.py` only if its output reporting depends on the layout.

**Expected Outcome**

From an unchanged `package_build.json`, the builder reads the inputs as the full
evidence set, writes the carried files, the `slim/` artifacts via `slim.py` and
`evidence/evidence_archive_record.json` (with `localPath` = the spec's input
paths), and writes a pending `1.2` manifest. The full-package output path is
gone. The same spec and inputs give the same snapshot ID.

**Self-Check**

Build Rwanda into a scratch output root twice; confirm the declared file set
matches Interfaces 1, carried files are byte-identical to the inputs, and both
builds share a snapshot ID. Record which existing builder tests now fail
because they expect the full layout (Tester rework).

---

### DEV-004 — Runtime validation tier

`Status`: `PENDING` `Depends On`: `DEV-002, DEV-003`
`Acceptance`: `AC-002, AC-006, AC-007, AC-008, AC-010`

**Goal**

Load and validate a `1.2` package from runtime files alone.

**Affected Area**

New `packages/lp_runtime.py`; `packages/loader.py` (`1.2` load path and
captured names); `packages/lp_validation.py` only to share `_projection` and
`_coverage` without changing their behavior.

**Expected Outcome**

For `1.2`, the loader runs the Interfaces 6 runtime checks (record parse and
runtime agreement, receipt binding over the record, slim index binding, strict
shard parsing and placement, ID union and endpoint/decision agreement with
delivery) and builds `LearningProgressionEvidence` with the existing projection
and coverage semantics. It never opens `localPath`.

**Self-Check**

Load the scratch-built Rwanda `1.2` package with `GraphPackageLoader` and
compare projections and coverage with the current `1.1` package's (must be
equal); tamper copies (missing, extra, altered runtime file) still give today's
blocking findings. Existing suite still passes on the `1.1` packages.

---

### DEV-005 — `FullEvidenceView` evidence tier and `validate-packages`

`Status`: `PENDING` `Depends On`: `DEV-004`
`Acceptance`: `AC-004, AC-005, AC-012`

**Goal**

Run the full LP checks at acceptance only, on a dedicated in-memory view of the
archived evidence.

**Affected Area**

New `packages/evidence.py` (`FullEvidenceView`, verifier);
`packages/lp_validation.py` (full checks take a `FullEvidenceView` instead of a
`LoadedGraphPackage`; check semantics and finding codes preserved);
`packages/loader.py` (optional verifier hook); `cli/validate_packages.py`
(`--runtime-only`, non-persisting `evidence_archive_unavailable`);
`packages/validator.py` if persistence needs the new outcome. `bootstrap.py`
stays runtime-only.

**Expected Outcome**

For `1.2`, `kgfegmcp-validate-packages` checks every `localPath` size and hash,
builds the `FullEvidenceView`, runs every check `validate_learning_progression_evidence`
runs today, requires byte-equal re-derivation of every slim file and record
entry, explicit standard/LC slim coverage, and equal projections. Missing
archive files exit non-zero without a transition; mismatch findings are
blocking and move pending → `failed`/`quarantined` as today. `--runtime-only`
never persists. Until DEV-010, the `1.1` path feeds its own captured bytes
through the same view.

**Self-Check**

On scratch copies of the Rwanda `1.2` package: `--read-only` passes with
evidence present; removing, altering or mismatching an evidence or slim file
gives the expected outcome; `--runtime-only` passes without evidence. The six
`1.1` packages still load with identical projections.

---

### DEV-006 — Serve slim LP and entity provenance

`Status`: `PENDING` `Depends On`: `DEV-004`
`Acceptance`: `AC-009, AC-011, AC-012, AC-013`

**Goal**

Make the provenance resources and `read_evidence` serve slim content and cite
the record.

**Affected Area**

`resources/service.py` (`relationship_provenance`, `standard_provenance`,
`learning_component_provenance`, `learning_progressions` artifact links),
`resources/models.py` (new result fields, docstrings), `resources/lp.py` (slim
index parsing), `resources/evidence.py` if it reads the raw record shape.

**Expected Outcome**

Per-edge results return the slim record plus `archived_provenance_sha256`;
standard and LC results add `source_document`, `attribution_statement` and
`archived_provenance_sha256`; `source_artifacts` cite the slim artifact and
`evidenceArchiveRecord`; "complete original" wording is gone. Lookup keys and
rights checks are unchanged.

**Self-Check**

Serve the scratch Rwanda `1.2` package through the resource service for a sample
of edges, standards and components and check the payload shape; confirm rights
denials match today's.

---

### DEV-007 — `kgfegmcp-verify-evidence-archive` CLI

`Status`: `PENDING` `Depends On`: `DEV-001`
`Acceptance`: `AC-018`

**Goal**

Add the read-only archive verification command (Interfaces 9).

**Affected Area**

New `cli/verify_evidence_archive.py`; `backend/pyproject.toml` console script.

**Expected Outcome**

`all` or `one --framework-id --snapshot-id` reads only the record and local
files, prints `ok`/`missing`/`mismatch` per entry with the archive location, and
exits non-zero on any missing or mismatched entry. No network access.

**Self-Check**

Run it against the scratch Rwanda package with evidence present, with one file
moved aside, and with one file altered (on a scratch copy).

---

### DEV-008 — Build and accept the six `1.2` snapshots

`Status`: `PENDING` `Depends On`: `DEV-003, DEV-005, DEV-006`
`Acceptance`: `AC-001, AC-002, AC-004, AC-006, AC-015`

**Goal**

Replace each served `1.1` snapshot with an accepted `1.2` snapshot.

**Affected Area**

`data/graph_packages/` (new snapshot directories; old ones deleted from the
tree, still in Git history and the input sets). `package_build.json` files are
unchanged.

**Expected Outcome**

Each framework has exactly one `1.2` snapshot with `validation.status: passed`,
built from its unchanged spec and accepted by `kgfegmcp-validate-packages` with
local evidence. Before the old snapshots are deleted, a comparison captures
delivery hashes and tool results so AC-002 differences are limited to the
expected identity, hash and artifact-link fields.

**Self-Check**

Scratch comparison: delivery file hashes equal; per-edge projections and
framework, standards and progression tool outputs equal between old and new
packages except the expected fields. Server bootstrap under `fail` loads all
six. Rebuilding one framework from its spec reproduces its snapshot ID.

---

### DEV-010 — Remove `1.1` support

`Status`: `PENDING` `Depends On`: `DEV-008`
`Acceptance`: `AC-001, AC-008`

**Goal**

Delete every code path that exists only for `1.1` or the full-package layout.

**Affected Area**

`packages/models.py` (`1.1` rules, fields for archive-only kinds),
`packages/loader.py` (`1.1` load and full-capture path), `resources/policy.py`
(entries for names that can no longer be declared), `resources/lp.py`
(`LP_ARTIFACT_NAMES` entries for undeclarable names), the bridge in
`packages/evidence.py`/`lp_validation.py`, and `legacy` wording in `slim.py`
and `evidence_models.py`.

**Expected Outcome**

Only `1.2` manifests load; any other version yields
`manifest_version_unsupported`. Archive-only kinds cannot be declared as fields
or additional artifacts. No `1.1` code path remains in `src/`.

**Self-Check**

`grep` for `1.1` paths and archive-only field names in `src/`; bootstrap under
`fail` loads all six `1.2` packages; a scratch `1.1` manifest is rejected with
`manifest_version_unsupported`; full lint and type tools on `src/`. Record which
tests or fixtures still reference `1.1` (Tester removes or migrates them).

---

### DEV-009 — Ignore and untrack archive-only files

`Status`: `PENDING` `Depends On`: `DEV-010`
`Acceptance`: `AC-003, AC-006, AC-014, AC-016`

**Goal**

Stop tracking archive-only evidence while keeping local copies.

**Affected Area**

`.gitignore` (Interfaces 7 rules after the `!/data/input_artifacts/` negation);
`git rm --cached` of the matched input-set files (local files kept).

**Expected Outcome**

No archive-only or large input-set file is tracked; each one is ignored; small
carried files and `package_build.json` stay committed; tracked `data/` totals
≤ 100 MB. Image and bundle contents under `data/graph_packages/` equal the
declared runtime files plus manifests.

**Self-Check**

`git ls-files -z data | xargs -0 du -cb`; `git check-ignore` on every matched
path; `kgfegmcp-verify-evidence-archive all` passes; a fresh-clone-equivalent
check (archive files moved aside) starts the server under `fail`; STDIO smoke,
HTTP loopback smoke and MCPB stage smoke; Docker build if the sandbox allows it,
otherwise recorded as a limitation.

---

## Plan Notes

- Tests are Tester-owned. Developer does not add the synthetic evidence fixture
  (AC-017), remove or migrate `1.1` fixtures, or rework tests that read full
  evidence. After DEV-008/DEV-009, tests
  that read archive-only files or compare against the full provenance map
  (`conftest.py` `accepted_state` is fine; `test_progression_resources.py`,
  `test_progression_acceptance.py` and others noted in `CONTEXT.md`) are expected
  to need Tester rework; Developer will record exactly which ones fail.
- All self-check scripts live in the session scratchpad, not the repository.
- The size fallback in the design's Risks (hoisting constant per-edge fields)
  is a design revision; if DEV-009 measures over 100 MB, Developer routes an
  `ARCHITECTURE` failure rather than adopting it.
- No commits are created unless the user asks.
- An empty, untracked `data/graph_packages/.claude/.cc-writes/` directory exists
  locally (created 2026-10-08 by tooling, not by this cycle). It is not part of
  any package; scratch scripts skip dot directories. Baseline on 2026-10-14 at
  `4394d0a`: `.venv/bin/pytest -rsPQ -m "not costs-money" -n auto -p no:randomly
  tests` from `backend/` gave 11 passed, 106 errors, all from catalog discovery
  rejecting `.claude` as a framework ID. The existing suite cannot serve as a
  self-check until that directory is removed (user decision). The user removed
  it on 2026-10-14. A second empty `.claude/.cc-writes/` inside the Rwanda
  snapshot (dated 2026-10-13, flagged `package_undeclared_directory`) was then
  removed with `rmdir`; the suite went to 117 passed. These folders appear in
  directories used as a shell working directory, so Developer never sets one
  under `data/graph_packages/`.

### Suspended Assignment 1

`Recovery Frame`: `1` `Recovery Reason`:
`User rework: drop manifest 1.1 support and all legacy behavior; no backward compatibility needs to be maintained.`
`Purpose`: `DEVELOPMENT` `Target`: `NONE` `Assessed Inputs`:
`architecture spec at 5f43d67; scope at 9db106a; DEV-001 modules evidence_models.py and slim.py (uncommitted)`
`Next Action`: `Reconcile the plan with the revised design (expect DEV-002 to DEV-006 to drop 1.1 paths, possibly a removal step), return it to PROPOSED for approval, then resume at DEV-002.`

### Recovery Reconciliation (2026-10-14)

Suspended Assignment 1 restored after the Architect's revision (`4394d0a`,
`1.2` only). DEV-001 stays `DONE`: its derivation and models are unchanged by
the revision; only the "legacy" wording differs, which DEV-010 aligns. DEV-002
to DEV-009 keep their IDs and outcomes but drop every "`1.1` unchanged" promise.
DEV-003 now replaces the full-package build path (no `packageLayout` field).
DEV-005 now refactors `lp_validation.py` onto a `FullEvidenceView`. New DEV-010
removes `1.1` support after the DEV-008 cutover, and DEV-009 now follows it. The
plan returned to `PROPOSED` for approval; the locked user style is unchanged.
