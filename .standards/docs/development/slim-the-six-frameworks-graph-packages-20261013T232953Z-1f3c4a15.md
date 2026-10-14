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
  git-ignored under `data/input_artifacts/`, and record it by hash.

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

### DEV-002 — Manifest `1.2` layout rules

`Status`: `PENDING` `Depends On`: `DEV-001`
`Acceptance`: `AC-001, AC-008`

**Goal**

Teach the manifest model the two-tier contract without changing `1.1`.

**Affected Area**

`backend/src/kgfegmcp/packages/models.py` (`MANIFEST_VERSION`, version
validator, `PackageArtifacts`, `learning_progression_artifacts`, capability
rules); `resources/policy.py` only if `evidenceArchiveRecord` needs an explicit
fail-closed entry.

**Expected Outcome**

`1.2` manifests must declare `evidenceArchiveRecord`, must not declare any
archive-only kind, and require the slim LP set when LP is included. `1.1`
manifests must not declare the record and validate exactly as before. The record
and shards stay additional artifacts and fail closed in the generic artifact
resource.

**Self-Check**

Existing suite `uv --directory backend run --locked --no-sync pytest -rsPQ -m
"not costs-money" tests` stays green (all six packages are still `1.1`); scratch
script validates accepted and rejected `1.2` manifest variants; lint/type tools.

---

### DEV-003 — Builder `runtime_only` layout

`Status`: `PENDING` `Depends On`: `DEV-002`
`Acceptance`: `AC-001, AC-004, AC-015, AC-018`

**Goal**

Let `kgfegmcp-build-manifest` produce a pending runtime-only `1.2` package from
an unchanged legacy input set.

**Affected Area**

`packages/models.py` (`PackageBuildSpec.package_layout`),
`packages/builder.py` (plan, copy, manifest creation, staged verification).

**Expected Outcome**

With `packageLayout: "runtime_only"`, the builder reads the inputs as the legacy
evidence set, writes the carried files, the `slim/` artifacts via `slim.py`, and
`evidence/evidence_archive_record.json` (with `localPath` = the spec's input
paths), and writes a pending `1.2` manifest. Without the field, legacy behavior
is unchanged. The same spec and inputs give the same snapshot ID.

**Self-Check**

Build one framework (Rwanda) into a scratch output root twice with a temporary
copy of its spec plus `packageLayout`; confirm the declared file set matches
Interfaces 1, carried files are byte-identical, and both builds share a snapshot
ID. Existing suite stays green.

---

### DEV-004 — Runtime validation tier and loader selection

`Status`: `PENDING` `Depends On`: `DEV-002, DEV-003`
`Acceptance`: `AC-002, AC-006, AC-007, AC-008, AC-010`

**Goal**

Load and validate a `1.2` package from runtime files alone.

**Affected Area**

New `packages/lp_runtime.py`; `packages/loader.py` (tier choice by manifest
version, captured names for `1.2`); `packages/lp_validation.py` only to expose
`_projection`/`_coverage` for sharing, without changing their behavior.

**Expected Outcome**

For `1.2`, the loader runs Interfaces 6 runtime checks (record parse and runtime
agreement, receipt binding over the record, slim index binding, strict shard
parsing and placement, ID union and endpoint/decision agreement with delivery)
and builds `LearningProgressionEvidence` with the existing projection and
coverage semantics. It never opens `localPath`. `1.1` packages go through the
unchanged path.

**Self-Check**

Load the scratch-built Rwanda `1.2` package with `GraphPackageLoader` and
compare its projections and coverage with the current `1.1` package's (must be
equal); tamper copies (missing, extra, altered runtime file) still produce
today's blocking findings. Existing suite stays green.

---

### DEV-005 — Evidence tier and `validate-packages` wiring

`Status`: `PENDING` `Depends On`: `DEV-004`
`Acceptance`: `AC-004, AC-005, AC-012`

**Goal**

Run full-evidence acceptance at validation time only.

**Affected Area**

New `packages/evidence.py`; `packages/loader.py` (optional verifier hook);
`cli/validate_packages.py` (`--runtime-only`, non-persisting
`evidence_archive_unavailable`); `packages/validator.py` if persistence needs
the new outcome; `bootstrap.py` stays runtime-only.

**Expected Outcome**

For `1.2`, `kgfegmcp-validate-packages` checks every `localPath` size and hash,
assembles the in-memory legacy view, runs the unchanged
`validate_learning_progression_evidence`, requires byte-equal re-derivation of
every slim file and record entry, explicit standard/LC slim coverage, and equal
projections. Missing archive files exit non-zero without a transition; mismatch
findings are blocking and transition pending → `failed`/`quarantined` as today.
`--runtime-only` never persists.

**Self-Check**

On scratch copies of the Rwanda `1.2` package: `--read-only` passes with
evidence present; removing, altering, or mismatching an evidence file or a slim
file gives the expected outcome; `--runtime-only` passes without evidence.
Existing suite stays green.

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

For `1.2` packages, per-edge results return the slim record plus
`archived_provenance_sha256`; standard and LC results add `source_document`,
`attribution_statement` and `archived_provenance_sha256`; `source_artifacts`
cite the slim artifact and `evidenceArchiveRecord`; "complete original" wording
is gone. Lookup keys and rights checks are unchanged. `1.1` packages keep
working.

**Self-Check**

Serve the scratch Rwanda `1.2` package through the resource service for a sample
of edges, standards and components and check the payload shape; confirm rights
denials match the `1.1` package. Existing suite stays green.

---

### DEV-007 — `kgfegmcp-verify-evidence-archive` CLI

`Status`: `PENDING` `Depends On`: `DEV-001`
`Acceptance`: `AC-018`

**Goal**

Add the read-only archive verification command.

**Affected Area**

New `cli/verify_evidence_archive.py`; `backend/pyproject.toml` console script.

**Expected Outcome**

`all` or `one --framework-id --snapshot-id` reads only the record and local
files, prints `ok`/`missing`/`mismatch` per entry with the archive location, and
exits non-zero on any missing or mismatched entry. No network access.

**Self-Check**

Run it against the scratch Rwanda package with evidence present, with one file
moved aside, and with one file altered (on a scratch copy). `uv sync` registers
the script.

---

### DEV-008 — Migrate the six frameworks to runtime-only snapshots

`Status`: `PENDING` `Depends On`: `DEV-003, DEV-005, DEV-006`
`Acceptance`: `AC-001, AC-002, AC-004, AC-006, AC-015`

**Goal**

Replace each served `1.1` snapshot with an accepted `1.2` snapshot.

**Affected Area**

`data/input_artifacts/*/package_build.json` (add `packageLayout`),
`data/graph_packages/` (new snapshot directories; old ones deleted from the
tree, still in Git history and the input sets).

**Expected Outcome**

Each framework has exactly one `1.2` snapshot with `validation.status: passed`,
produced by the builder and accepted by `kgfegmcp-validate-packages` with local
evidence. Before deleting the old snapshots, a comparison captures delivery
hashes and tool results so AC-002 differences are limited to the expected
identity, hash and artifact-link fields.

**Self-Check**

Scratch comparison script: delivery file hashes equal; per-edge projections and
framework, standards and progression tool outputs equal between old and new
packages except the expected fields. Server bootstrap under `fail` loads all
six. Rebuilding one framework from its spec reproduces its snapshot ID.

---

### DEV-009 — Ignore and untrack archive-only files

`Status`: `PENDING` `Depends On`: `DEV-008`
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
  (AC-017) or rework tests that read full evidence. After DEV-008/DEV-009, tests
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
  any package; scratch scripts skip dot directories.

### Suspended Assignment 1

`Recovery Frame`: `1` `Recovery Reason`:
`User rework: drop manifest 1.1 support and all legacy behavior; no backward compatibility needs to be maintained.`
`Purpose`: `DEVELOPMENT` `Target`: `NONE` `Assessed Inputs`:
`architecture spec at 5f43d67; scope at 9db106a; DEV-001 modules evidence_models.py and slim.py (uncommitted)`
`Next Action`: `Reconcile the plan with the revised design (expect DEV-002 to DEV-006 to drop 1.1 paths, possibly a removal step), return it to PROPOSED for approval, then resume at DEV-002.`
