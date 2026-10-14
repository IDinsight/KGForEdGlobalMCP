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

`Status`: `DONE` `Depends On`: `DEV-002`
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

Result (2026-10-14, working tree at `10b6416` plus `builder.py` changes): from
`backend/`, `.venv/bin/kgfegmcp-build-manifest --spec <scratch spec>` run twice
with the Rwanda `package_build.json` copied unchanged except `outputRoot` set to
two scratch directories. Both exit 0 and produce snapshot
`rwanda-reb-mathematics-lower-primary-1-3@2025+7c2d6f401157`, pending, manifest
`1.2`, 79 declared files (the Interfaces 1 set), byte-identical across the two
builds, 19.4 MB. Scratch `dev003_check.py` confirmed: the file tree equals the
declared set plus the manifest; no archive-only kind is declared; the record
holds all 86 full-evidence entries with the same names, package paths and
SHA-256 as the current `1.1` manifest, each `localPath` under
`data/input_artifacts/rwanda_math/` matching size and hash; 11 entries are
`runtime: true` and carried byte-identical; slim files equal a fresh `slim.py`
derivation from the inputs; capabilities `hasDetailedProvenance`,
`hasLearningProgressionProvenance`, `hasLearningProgressions` are true. No
existing test exercises the builder; the suite still gives 117 passed. isort,
black, ruff, mypy, interrogate (100%) and pylint (10.00/10) clean on
`builder.py`.

**Implementation Notes**

Inputs are still discovered as before, but under their full-evidence names
(`_prepare_evidence_sources`). `_prepare_runtime_artifacts` carries every input
except archive-only kinds and the full forms of slimmed artifacts, derives the
slim files and the record in memory (`_GeneratedArtifact`), and declares the
runtime set. Input fingerprints now cover the whole evidence set. Full-evidence
inputs must sit inside the repository so `localPath` is repository-relative.
`hasLearningProgressionProvenance` now means the slim index is declared.

---

### DEV-004 — Runtime validation tier

`Status`: `DONE` `Depends On`: `DEV-002, DEV-003`
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

Result (2026-10-14, working tree at `7a3e16b` plus `lp_runtime.py` (new),
`loader.py` and `lp_validation.py` changes): all six frameworks built with the
DEV-003 builder into a scratch output root (unchanged specs, `outputRoot`
redirected) and loaded with `GraphPackageLoader`. Scratch `dev004_all.py`: every
`1.2` package loads with no findings, and its `LearningProgressionEvidence`
(judgments and coverage) equals the current `1.1` package's (1051, 599, 3206,
907, 486, 1831 judgments). Scratch snapshot IDs: Ghana English `…@2019+f2a9ab5922a1`,
Ghana Math `…@2019+ed3b9450718a`, CBSE `…@undated+21ece81a7ac5`, Tamil Nadu
`…@2025-proposed-draft+82b183ba9acc`, Nigeria `…@undated+424e546e2284`, Rwanda
`…@2025+7c2d6f401157`. Scratch `dev004.py` on Rwanda copies: missing shard →
`artifact_missing`, `package_declared_file_missing`; extra file →
`package_undeclared_file`; altered record → `artifact_checksum_mismatch`,
`snapshot_checksum_identity_mismatch` (none load). On verified bytes passed
straight to `validate_runtime_evidence`: flipped decision →
`lp_slim_record_mismatch`; removed field reinstated → `lp_slim_record_shape`;
record entry dropped and archive file marked runtime →
`evidence_record_runtime_mismatch`; record hash change →
`lp_normalization_output_hashes`; slim index original-index hash change →
`lp_partition_declarations`; record moved to the wrong shard →
`lp_partition_contents`. `grep` finds no `local_path` use in `lp_runtime.py` or
`loader.py`. Suite: 117 passed. isort, black, ruff, mypy, interrogate (100%) and
pylint (10.00/10) clean on the three files.

**Implementation Notes**

`_projection` now takes the `Judgment` and `_coverage` takes the report and
summary; their outputs are unchanged and `lp_runtime.py` imports them. The
loader picks `validate_runtime_evidence` for `1.2` and the existing validator
for the `1.1` bridge, and captures the record bytes. Runtime findings use new
codes `evidence_record_identity`, `evidence_record_runtime_mismatch`,
`lp_slim_record_shape`, `lp_slim_record_mismatch` and `runtime_evidence_shape`,
and reuse `lp_normalization_output_hashes`, `lp_partition_declarations`,
`lp_partition_identity`, `lp_partition_contents` and `lp_provenance_ids`.

---

### DEV-005 — `FullEvidenceView` evidence tier and `validate-packages`

`Status`: `DONE` `Depends On`: `DEV-004`
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

Result (2026-10-14, working tree at `71c4ac7` plus changes to `evidence.py` (new),
`evidence_models.py`, `lp_validation.py`, `loader.py`, `slim.py`, `builder.py`,
`errors.py`, `cli/validate_packages.py`). CLI runs from `backend/` with
`PATHS_PROJECT_DIR` set to a scratch project holding `config/`, a copy of
`data/input_artifacts/rwanda_math/` and the scratch Rwanda `1.2` pending package
(`…@2025+7c2d6f401157`), `kgfegmcp-validate-packages one …`:
1) evidence present, `--read-only` → exit 0, valid, still pending;
2) `--runtime-only` → exit 0, valid, still pending;
3) `lp_final_claims.json` moved away, persisting run → exit 2,
`evidence_archive_unavailable`, manifest still pending;
4) same, `--runtime-only` → exit 0, valid;
5) one byte of `as_kg_bundle.json` changed, `--read-only` → exit 1,
`evidence_archive_checksum_mismatch`, pending;
6) same, persisting run → exit 1, `failed`, persisted;
7) package and evidence restored, persisting run → exit 0, `passed`;
8) passed package, `--runtime-only` → exit 0, valid, not persisted;
9) altered evidence with `--invalid-package-policy quarantine` → exit 1,
`quarantined`.
All six scratch `1.2` packages (DEV-004 builds) with
`KGFEGMCP_GRAPH_PACKAGES_ROOT` pointed at them and the real input sets:
`pending --read-only` → exit 0, all six valid, no findings. Scratch
`dev005_direct.py` against the verifier internals: changed archived AS item →
`slim_derivation_mismatch` (`entityProvenance`); changed archived LP rationale →
`slim_derivation_mismatch` for the slim index and one shard; non-canonical
record bytes → `slim_derivation_mismatch`; altered runtime projections →
`slim_projection_mismatch`; final claims `total_claims` changed in the view →
`lp_final_counts_mismatch`; one LC node removed → `slim_entity_coverage_mismatch`.
Scratch `dev005_bridge.py`: on the real `1.1` package the view-based checks
return the same projections as startup, and `{}` for
`learningProgressionSummary`/`learningProgressionProvenance` gives
`lp_evidence_shape`/`lp_partition_declarations`. Suite: 115 passed, 2 failed —
both `test_progression_acceptance.py::test_evidence_rejects_missing_required_content`
cases call `validate_learning_progression_evidence(captured_contents=…,
package=…)`, the signature the design replaces with `view=` (Tester rework;
the bridge script shows the scenario still fails with `lp_` codes). isort,
black, ruff, mypy, interrogate (100%) and pylint (10.00/10) clean on all nine
touched files.

**Implementation Notes**

`FullEvidenceView` is a frozen dataclass in `evidence_models.py` so
`lp_validation.py` can take it without importing `evidence.py`. The full LP
checks read the view's artifacts, counts, framework root, item nodes and
relationships where they read the loaded package before; check logic and codes
are unchanged. `EvidenceVerifier` reads only the files the checks parse
(LP files, original shards, delivery, entity provenance) and stream-hashes the
rest. A missing archive file raises `EvidenceArchiveUnavailableError`, so the
validator persists nothing. `slim.derive_slim_artifacts` is now the shared
bytes-level derivation for the builder and acceptance. `full_layout_view` is the
temporary `1.1` bridge; DEV-010 removes it.

---

### DEV-006 — Serve slim LP and entity provenance

`Status`: `DONE` `Depends On`: `DEV-004`
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

Result (2026-10-14, working tree at `7ef0092` plus changes to `resources/service.py`,
`resources/lp.py`, `resources/models.py`, `mcp/resources/register.py`). Copies
of the six scratch `1.2` packages accepted with `KGFEGMCP_GRAPH_PACKAGES_ROOT`
set to them (`kgfegmcp-validate-packages pending`, exit 0, all `passed`). Scratch
`dev006.py` bootstrapped the app on the real `1.1` packages and on the accepted
`1.2` copies and compared, per framework, about 40 LP edges, 21 standards and
21 components (every Nth by ID): the `1.2` edge provenance equals
`slim_lp_record` of the `1.1` record; standard provenance equals the `1.1` item
without `candidate_source_refs` plus `original_item_sha256`; LC provenance equals
the `1.1` entry plus `original_component_sha256`; `archivedProvenanceSha256`
equals the `1.1` manifest hash of the full map, AS or LC document;
`sourceDocument` and `attributionStatement` agree. `source_artifacts`: edge →
manifest, shard, slim index, `relationships`, `evidenceArchiveRecord`;
standard/LC → slim artifact, `evidenceArchiveRecord`. `read_evidence` on a
`1.2` edge URI returns the slim record. Generic artifact resource outcomes for
a shard, `entityProvenance`, `learningComponentProvenance`,
`learningProgressionSummary` and the index are the same exception class as on
`1.1` (`ResourceAccessDeniedError` under the current rights);
`evidenceArchiveRecord` → `ResourceNotFoundError`. The `learning_progressions`
resource lists Normalization, ProvenanceIndex, Summary, Unresolved and
Validation. `resources/policy.py` is unchanged. Suite: 115 passed, the same 2
known DEV-005 failures. isort, black, ruff, mypy, interrogate (100%) and pylint
(10.00/10) clean on the four files.

Limitation: `kgfegmcp-stdio-smoke` could not run here. It launches the server
with `uv` and a fixed environment (no `UV_CACHE_DIR`), and the sandbox denies
`~/.cache/uv`; it also always serves `<repo>/data/graph_packages`. Smoke runs
stay in DEV-009, after the new packages are in place.

**Implementation Notes**

`validated_partition_index`, `_archive_reference`, `_entity_source` and
`_entity_sources` branch on the manifest version; the `1.1` branches are the
temporary bridge (DEV-010 removes them). The bridge fills the new result fields
from the full documents so both layouts return the same shape. The MCP resource
template description for edge provenance no longer says "full original".

---

### DEV-007 — `kgfegmcp-verify-evidence-archive` CLI

`Status`: `DONE` `Depends On`: `DEV-001`
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

Result (2026-10-14, working tree at `3045cf8` plus new
`cli/verify_evidence_archive.py` and the `pyproject.toml` console script;
registered with `uv sync --locked --extra dev --extra docs`, `uv.lock`
unchanged). From `backend/`, `.venv/bin/kgfegmcp-verify-evidence-archive`:
1) `one` on the scratch Rwanda package with `PATHS_PROJECT_DIR` set to the
DEV-005 scratch project → exit 0, 86 `ok`, archive location
`IDinsight Google Drive`;
2) `lp_final_claims.json` moved aside, `all` → exit 1, `incomplete`,
`learningProgressionFinalClaims` `missing`;
3) one byte appended to the scratch copy of original shard 10 → exit 1,
`learningProgressionProvenanceShard10` `mismatch`;
4) `all` with `KGFEGMCP_GRAPH_PACKAGES_ROOT` at the six accepted scratch `1.2`
packages and the real input sets → exit 0, 86 `ok` each;
5) `all` on the repository's current `1.1` packages → exit 1,
`record_unavailable` (expected until cutover);
6) invalid IDs → exit 2.
The module imports no network client. Suite unchanged: 115 passed plus the 2
known DEV-005 failures. isort, black, ruff, mypy, interrogate (100%) and pylint
(10.00/10) clean.

**Implementation Notes**

The command checks every record entry's `localPath`, including carried files,
so one run confirms a whole restored input set. It finds the record at the fixed
`evidence/evidence_archive_record.json` path and never reads the manifest.

---

### DEV-008 — Build and accept the six `1.2` snapshots

`Status`: `DONE` `Depends On`: `DEV-003, DEV-005, DEV-006, DEV-011`
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

Progress (2026-10-14, working tree at `ec30e40` plus DEV-002 to DEV-007 changes):
built the six `1.2` packages into `data/graph_packages/` from temporary spec
copies that only set `outputRoot` to `data/graph_packages` (snapshot IDs
identical to the scratch builds: Ghana English `…@2019+f2a9ab5922a1`, Ghana
Math `…@2019+ed3b9450718a`, CBSE `…@undated+21ece81a7ac5`, Tamil Nadu
`…@2025-proposed-draft+82b183ba9acc`, Nigeria `…@undated+424e546e2284`, Rwanda
`…@2025+7c2d6f401157`), then `kgfegmcp-validate-packages pending` → exit 0, all
six `passed`, persisted. The old `1.1` snapshots are still present (not
deleted); the catalog loads all twelve. Scratch `dev008_compare.py` paired
calls on old and new snapshots: delivery hashes equal; `LearningProgressionEvidence`
equal; `get_framework`, framework statistics, `get_standard`,
`get_standard_context` identical after snapshot/graph-package ID normalization;
`search_standards` identical except `page.nextCursor`, which encodes a hash of
the effective query including the snapshot ID. Every progression service call
on `1.2` (`get_learning_progression` ×8080, `get_standard_progressions` ×196,
`traverse_learning_progressions` ×196, `get_learning_progression_paths` ×65,
`search_learning_progressions` ×6) raised `CapabilityUnavailableError`:
`LearningProgressionsService.evidence_metadata` requires every name in
`services/lp_models.py` `PROGRESSION_DERIVATION_ARTIFACT_NAMES`
(`learningProgressionProvenance`, `learningProgressionProvenanceIndex`, `nodes`,
`relationships`) to be declared, and `1.2` packages no longer declare the full
map. Routed as an `ARCHITECTURE` failure (see Plan Notes, Suspended Assignment 2).

Result after DEV-011 (2026-10-14, `7f02e77`, where the six `1.2` packages are
committed): the comparison rerun is clean except the expected fields (see
DEV-011). The six `1.1` snapshot directories (`…+e00c5329a507`,
`…+0b768f7cfaf9`, `…+576740bed2d1`, `…+aa0dd9310a0f`, `…+bc5e769ed26f`,
`…+2ee0fa308d13`; 522 tracked files) were confirmed `1.1`/`passed` and deleted
from the working tree (unstaged deletions; still in Git history). Then:
`bootstrap_application()` with `KGFEGMCP_INVALID_PACKAGE_POLICY=fail` loads
exactly the six `1.2` packages, all `passed`; `kgfegmcp-validate-packages one
… --read-only` for each (evidence tier against the real input sets) → exit 0,
valid, `passed`, not persisted, no findings; `kgfegmcp-build-manifest --dry-run`
from the unchanged Nigeria spec (only `outputRoot` redirected to scratch) →
`nigeria-nerdc-mathematics-primary-1-3@undated+424e546e2284`, the committed
snapshot ID; `package_build.json` files unchanged. Suite: 113 passed, 4 failed —
the 2 known DEV-005 cases plus the 2 DEV-011 cases recorded in Plan Notes.

---

### DEV-011 — Progression result citations from archived identities

`Status`: `DONE` `Depends On`: `DEV-004, DEV-006`
`Acceptance`: `AC-002`

**Goal**

Make the progression tools work on `1.2` packages with unchanged citations
(Interfaces 10).

**Affected Area**

`packages/models.py` (`LoadedGraphPackage` gains the record's archived
identities, logical name → SHA-256, `runtime: false` entries only);
`packages/lp_runtime.py` and `packages/loader.py` (the runtime tier returns
them and the loader stores them); `services/learning_progressions.py`
(`evidence_metadata` resolves each of the four names generically: declared
artifact first, archived identity second, otherwise
`CapabilityUnavailableError`); `services/lp_models.py` (comment on
`PROGRESSION_DERIVATION_ARTIFACT_NAMES`).

**Expected Outcome**

On `1.2` packages every progression tool answers, and `metadata.artifacts`
keeps the four entries in the same order and shape: `learningProgressionProvenance`
cites the archived map's SHA-256 (unchanged from `1.1`) and its artifact URI;
only the `learningProgressionProvenanceIndex` hash differs. No file is read to
build the metadata.

**Self-Check**

Rerun `dev008_compare.py` with both snapshot sets in `data/graph_packages/`:
every progression call succeeds on `1.2`, and results match `1.1` except
snapshot identity, the index hash and the snapshot-derived search cursor.
Existing suite (no new failures) and lint/type tools on changed files.

Result (2026-10-14, working tree at `f191682` plus changes to `packages/models.py`,
`packages/lp_runtime.py`, `packages/loader.py`, `services/learning_progressions.py`,
`services/lp_models.py`). With both snapshot sets in `data/graph_packages/`,
scratch `dev008_compare.py` (normalizing raw and percent-encoded snapshot and
graph-package IDs) ran 8,887 paired calls; every `1.2` progression call
succeeds. The only differing fields: `metadata.artifacts[1].sha256` (slim index),
`metadata.manifestSha256`, and `page.nextCursor`/`page.nextRequest.cursor`
(they embed the manifest hash or snapshot ID); `search_standards` differs only in
`page.nextCursor`. `metadata.artifacts[0]` (`learningProgressionProvenance`)
keeps the `1.1` SHA-256 and URI. Suite with `KGFEGMCP_GRAPH_PACKAGES_ROOT` at a
copy of only the six `1.1` packages: 115 passed, the 2 known DEV-005 failures.
At the six accepted `1.2` copies: 113 passed, 4 failed — the 2 known plus
`test_progression_lookup.py::test_every_exact_edge_preserves_accepted_evidence`
(expects every derivation name among declared artifacts) and
`test_progression_resources.py::test_original_per_edge_trace_and_hashes`
(expects a declared `learningProgressionProvenance`); both encode the old
contract (Tester rework). On the repository root, which holds both snapshot
sets until DEV-008 deletes the `1.1` ones, 33 fail; the extra 31 come from two
snapshots per framework. isort, black, ruff, mypy, interrogate (100%) and pylint
(10.00/10) clean on the changed files.

**Implementation Notes**

`validate_runtime_evidence` now returns `RuntimeEvidenceResult` (projections,
archived identities, findings); the loader stores the identities on
`LoadedGraphPackage.archived_artifact_sha256`. `evidence_metadata` resolves each
cited name from declared artifacts first, then archived identities, with no
name-specific branch.

---

### DEV-010 — Remove `1.1` support

`Status`: `DONE` `Depends On`: `DEV-008`
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

Progress (2026-10-14, working tree at `7c67871` plus uncommitted DEV-010 edits to
`packages/models.py`, `builder.py`, `loader.py`, `evidence.py`, `slim.py`,
`evidence_models.py`, `resources/lp.py`, `resources/service.py`,
`resources/policy.py`): `1.1` rules, the eight archive-only `PackageArtifacts`
fields, the `full_layout_view` bridge, the loader and resource `1.1` branches,
the undeclarable policy and `LP_ARTIFACT_NAMES` entries, and the "legacy"
wording are removed; ruff, mypy, isort, black, interrogate clean on `src/`,
pylint 10.00/10. Self-check then failed: `bootstrap_application()` loads no
package, and the committed Nigeria `1.2` manifest fails
`GraphPackageManifest.model_validate_json` with eight `extra_forbidden` errors
(`artifacts.academicStandardsBundle`, `learningComponentsBundle`,
`learningProgressionBuildsTowards`, `learningProgressionFinalClaims`,
`learningProgressionProvenance`, `learningProgressionRelatesTo`,
`relationshipsHasChild`, `standardsFrameworkItems`, all `null`). The builder's
`_canonical_manifest_bytes` uses `model_dump(by_alias=True, mode="json")`, which
writes unset fields as `null`; all six accepted `1.2` manifests carry those keys
(the old `1.1` manifests had no null artifact keys). A scratch `1.1` manifest
gave `manifest_version_unsupported` as intended. Routed as an `ARCHITECTURE`
failure (Plan Notes, Suspended Assignment 3). Until the design is corrected the
uncommitted working tree does not start the server; `git stash` or
`git checkout` of the listed files restores the last committed state.

Result after the correction (2026-10-14, `0a47aa8`; the DEV-010 edits are
committed in `f8096e4`): from `backend/`, isort, black, ruff, mypy (123 files),
interrogate (100%) and pylint (10.00/10) clean on all of `src/`. `grep` over
`src/` (excluding LP preparation code) finds no `1.1` path, archive-only field,
bridge or "legacy" wording; the only remaining matches are the
`has_learning_progression_provenance` capability and the builder's
full-evidence input basenames. Earlier on a scratch copy: a `1.1` manifest →
`manifest_version_unsupported`; an archive-only key (`null` or a path) or an
archive-only name as an additional artifact → `manifest_invalid`. Startup,
revalidation, archive verification and the suite are checked in DEV-012, once
the six snapshots are re-sealed.

---

### DEV-012 — Re-seal the six `1.2` snapshots without archive-only keys

`Status`: `DONE` `Depends On`: `DEV-010`
`Acceptance`: `AC-001, AC-004, AC-006, AC-015`

**Goal**

Replace the six unreleased `1.2` snapshots, whose manifests carry the eight
archive-only keys as `null`, with rebuilt and re-accepted ones (Interfaces 2).

**Affected Area**

`data/graph_packages/` (delete the six snapshot directories, rebuild from the
unchanged `package_build.json` specs with only `outputRoot` redirected, accept
with `kgfegmcp-validate-packages pending`).

**Expected Outcome**

Each framework again has one `passed` `1.2` snapshot with the same snapshot ID
and byte-identical declared artifacts; only the manifest differs (no
archive-only keys, new timestamps). The server starts under `fail`.

**Self-Check**

Before deleting, record every declared artifact's SHA-256; after rebuilding,
require identical snapshot IDs and artifact hashes and no archive-only keys in
any manifest. Then: startup under `fail` loads the six; `validate-packages one
--read-only` passes for each; a scratch `1.1` manifest is rejected with
`manifest_version_unsupported` and one with a `null` archive-only key with
`manifest_invalid`; `kgfegmcp-verify-evidence-archive all` passes; suite shows
no new failures beyond those recorded in Plan Notes.

Result (2026-10-14, `0a47aa8`): recorded each manifest's snapshot ID and 79
checksums (all six `1.2`, `passed`, eight `null` archive-only keys each);
deleted the six snapshot directories; rebuilt with
`kgfegmcp-build-manifest --spec <copy>` (unchanged specs, `outputRoot` set to
`data/graph_packages`) → all `created` with the same six snapshot IDs;
`kgfegmcp-validate-packages pending` → exit 0, all six `passed`, persisted, no
findings. Every rebuilt manifest has the same snapshot ID and identical
`checksums` (79/79, also equal to the on-disk SHA-256 of each file) and no
archive-only key; `git status` shows only the six manifests modified. Then:
`bootstrap_application()` with `KGFEGMCP_INVALID_PACKAGE_POLICY=fail` → six
`1.2` packages; `validate-packages one … --read-only` for each → exit 0, valid,
`passed`, not persisted, no findings; `kgfegmcp-verify-evidence-archive all` →
exit 0, 86 `ok` each; on a scratch copy of Nigeria, unchanged → no findings,
`manifestVersion` `1.1` → `manifest_version_unsupported`,
`learningProgressionFinalClaims: null` → `manifest_invalid`. Suite: 112 passed,
5 failed — the 4 recorded in Plan Notes plus
`test_progression_resources.py::test_bulk_is_denied_independently`, which
expects `ResourceAccessDeniedError` for the generic artifact
`learningProgressionProvenance`; since DEV-010 removed its policy entry, the
name is undeclared and gives `ResourceNotFoundError`, the "unavailable instead
of access denied" change the design lists under Risks (Tester rework).

---

### DEV-009 — Ignore and untrack archive-only files

`Status`: `PENDING` `Depends On`: `DEV-012`
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
  to need Tester rework; Developer will record exactly which ones fail. Known so
  far: both cases of
  `test_progression_acceptance.py::test_evidence_rejects_missing_required_content`
  fail with `TypeError` since DEV-005, because they pass `captured_contents` and
  `package` to `validate_learning_progression_evidence`, which now takes `view`.
  On `1.2`-only packages, also
  `test_progression_lookup.py::test_every_exact_edge_preserves_accepted_evidence`
  and `test_progression_resources.py::test_original_per_edge_trace_and_hashes`
  (both expect `learningProgressionProvenance` to be declared).
  Since DEV-010,
  `test_progression_resources.py::test_bulk_is_denied_independently` also
  fails: it expects access denied for the undeclared `learningProgressionProvenance`
  artifact, which now reports unavailable by design.
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

### Suspended Assignment 2

`Recovery Frame`: `1` `Recovery Reason`:
`Progression tool results cite learningProgressionProvenance (PROGRESSION_DERIVATION_ARTIFACT_NAMES), which runtime-only packages no longer declare; the design does not set what they cite, and AC-002 allows no such difference.`
`Purpose`: `DEVELOPMENT` `Target`: `NONE` `Assessed Inputs`:
`architecture spec at 4394d0a; working tree at ec30e40 with DEV-001 to DEV-007 done and the six 1.2 packages built and accepted in data/graph_packages alongside the 1.1 ones`
`Next Action`: `Reconcile the plan with the corrected design (likely a step for the progression result metadata), then resume DEV-008 by rerunning dev008_compare.py and, if clean, deleting the six 1.1 snapshot directories.`

### Recovery Reconciliation 2 (2026-10-14)

Suspended Assignment 2 restored after the Architect's revision (`f191682`,
Interfaces 10). DEV-001 to DEV-007 stay `DONE`; their outcomes are unchanged.
New DEV-011 implements the progression citations, and DEV-008 now depends on it.
DEV-008 keeps its progress: the six `1.2` packages remain built and accepted
alongside the `1.1` ones, and resumes with the comparison rerun. The plan
returned to `PROPOSED` for approval; the locked user style is unchanged.

### Suspended Assignment 3

`Recovery Frame`: `1` `Recovery Reason`:
`The six accepted 1.2 manifests serialize every PackageArtifacts field, so they hold the eight archive-only keys as null; removing those fields (Interfaces 2) makes them invalid, and fixing it needs re-sealing or a model change.`
`Purpose`: `DEVELOPMENT` `Target`: `NONE` `Assessed Inputs`:
`architecture spec at f191682; committed six accepted 1.2 packages at 7f02e77 (manifests with null archive-only artifact keys); uncommitted DEV-010 edits listed under DEV-010`
`Next Action`: `Reconcile DEV-010 with the corrected design (model tolerance or re-sealed packages), finish the removal, then rerun startup, the 1.1 rejection, rebuild ID, full revalidation, archive verification and the suite.`

### Recovery Reconciliation 3 (2026-10-14)

Suspended Assignment 3 restored after the Architect's correction (`0a47aa8`):
archive-only keys must be absent from manifests, and the six unreleased `1.2`
snapshots are rebuilt and re-accepted with the same IDs. The DEV-010 code edits
were committed in `f8096e4`. DEV-010 keeps its code outcome; its startup and
revalidation checks move to new DEV-012, which re-seals the snapshots. DEV-009
now depends on DEV-012. The plan returned to `PROPOSED` for approval; the locked
user style is unchanged.
