<!-- STANDARDS
Artifact: SCOPE
Cycle: slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15
-->

# Runtime-Only Graph Packages

## Goal

The six accepted framework packages are about 671 MB, and `data/input_artifacts/`
holds another 671 MB of byte-identical copies. Almost all of that is evidence the
server never needs to answer a request. This change makes each framework's served
package a runtime-only set, so large evidence files no longer have to be committed,
while keeping the full evidence verifiable.

The server must load only what it serves: delivery nodes and relationships, slimmed
per-edge LP relationship provenance (sharded), the provenance index, slim entity
provenance for standards and learning components, and small summary, report,
unresolved and resource files. Full evidence (final claims, the original provenance
map, the LP split relationship files, the KG bundles, full entity provenance,
hierarchy relationships and framework items, and large input-set files) is checked
at build or acceptance time, bound to the package by hash, kept git-ignored in the
working tree, and archived in IDinsight Google Drive.

## Constraints

- Accepted packages are immutable. Changing the declared file set means a new
  snapshot for each framework, built and accepted through the existing
  pending → `passed` lifecycle; sealed snapshots are not patched in place.
- Railway builds the hosted image from the Git repository, and CI runs on a plain
  checkout. Everything the server loads must be committed.
- The archive is the user's existing IDinsight Google Drive copy of the full files.
  Local copies sit in the repository working tree but are git-ignored. Uploading
  to and managing Drive stay with the user.
- Generic code keeps the configuration-driven design: no framework-specific
  branches.
- Acceptance stays structural and process integrity, not pedagogical certification.
  Source truncation, warning pairs, eligibility notices and CBSE's one
  `needs_review` claim are preserved.
- Existing resource limits (32 MiB source read, 8 MiB returned), the
  invalid-package policies, and the rights gates in `resources/policy.py` stay in
  force.
- Tests mock live-model and paid boundaries. Deployment and publication are
  user-owned.

## Non-goals

- Rewriting Git history. Evidence blobs already in history stay there, so clone
  size from history does not shrink.
- Adopting Git LFS or any other Git-hosted large-file storage.
- Changing graph content, profiles, prompt overlays, or the semantics of any tool.
  Only the content of provenance resources changes, as defined below.
- Adding frameworks, rebuilding evidence from source documents, or rerunning any
  model-backed preparation step.
- Uploading files to Drive, setting Drive permissions, or deploying the result.

## Work

### 1. Runtime-only packages for all six frameworks

**Intent:** Replace each framework's served snapshot with one whose declared files
are only what the server needs at runtime.

**Done when:**

- `AC-001`: For each of the six framework IDs, `data/graph_packages/` holds one
  accepted (`validation.status: passed`) snapshot whose declared files are limited
  to the runtime set named in the Goal. None of the archive-only artifacts (LP final
  claims, original LP provenance map, LP split relationship JSONL, AS and AS-LC KG
  bundles, full AS and LC entity provenance, hierarchy relationships, standards
  framework items) is a declared runtime file.
- `AC-002`: Served graph content is unchanged. For every framework, the delivery
  node and relationship sets, framework and standards tool results, and progression
  tool results (including confidence and the judgment projections) match the
  current snapshots, except for snapshot identity and package-hash fields.
- `AC-003`: Tracked files under `data/` total no more than 100 MB on the delivered
  branch, down from about 1.34 GB.

**Depends on:** None.

### 2. Acceptance with full evidence, runtime without it

**Intent:** Keep today's full-evidence integrity checks at build and acceptance
time, and let the server start from the runtime set alone.

**Done when:**

- `AC-004`: With the full evidence present locally, acceptance runs at least the
  integrity checks it runs today on that evidence (provenance record validation and
  reconciliation against final claims, the split JSONL, delivery edges, summary,
  report and unresolved evidence). It also confirms that every slim runtime artifact
  is a faithful derivation of the full evidence, and records each archived file's
  path, size and SHA-256 in the package.
- `AC-005`: Acceptance does not mark a package `passed` when any archive-only file
  is missing, altered, or inconsistent with the other evidence, or when a slim
  runtime artifact does not match what the full evidence yields.
- `AC-006`: From a fresh clone, with no archive-only files present, the server
  starts under the `fail` invalid-package policy and serves all six packages.
  Runtime revalidation needs only the runtime files.
- `AC-007`: A working tree that also holds the git-ignored full-evidence files in
  their documented locations starts and serves the same as a fresh clone.
- `AC-008`: Runtime revalidation still rejects a package with a missing, extra or
  altered runtime file, and the existing invalid-package policies behave as before.

**Depends on:** 1.

### 3. Slim per-edge LP relationship provenance

**Intent:** Cut per-edge provenance to the judgment and its trace, which is what
callers use, and leave the bulky candidate evidence in the archive.

**Done when:**

- `AC-009`: For every LP edge, the `relationship/{id}/provenance` resource and
  `read_evidence` return a record with the relationship identity and endpoints,
  decision, direction, confidence, full rationale, full warnings, checker outcome,
  model identity, attribution, and the content hashes that link the edge to its
  archived evidence. Candidate evidence text, admissible decisions and the
  duplicate producer judgment are not returned.
- `AC-010`: Every LP edge in each delivery package resolves through the provenance
  index to exactly one slim record. No slim shard exceeds the existing source-read
  limit.
- `AC-011`: Rights gating for per-edge provenance, `read_evidence` and the generic
  artifact resource behaves as it does today.

**Depends on:** 1.

### 4. Slim entity provenance for standards and learning components

**Intent:** Keep `standard_provenance` and `learning_component_provenance` working
after full entity provenance moves to the archive.

**Done when:**

- `AC-012`: For every standard and learning component in each package,
  `standard_provenance` and `learning_component_provenance` return provenance
  served from slim runtime artifacts. Each response carries what is needed to
  attribute the entity and trace it to its source and to the archived full record.
- `AC-013`: Rights gating for both resources behaves as it does today.

**Depends on:** 1.

### 5. Repository, image and bundle hold only runtime data

**Intent:** Stop committing and shipping evidence the server does not use, without
losing the ability to rebuild.

**Done when:**

- `AC-014`: On the delivered branch, no archive-only package file and no large
  input-set file is tracked, and each one's documented local location is
  git-ignored.
- `AC-015`: `data/input_artifacts/` keeps each set's `package_build.json` and small
  files committed. With the git-ignored inputs restored locally, the documented
  rebuild and acceptance procedure reproduces each accepted runtime package.
- `AC-016`: The Docker image and the MCPB bundle contain only declared runtime
  package files, even when archive-only files exist locally, and pass the existing
  STDIO, HTTP loopback and MCPB stage smoke checks.
- `AC-017`: The CI test suite passes on a plain checkout with no archive-only files.
  Tests that don't need the real archive cover the full-evidence acceptance
  behavior in `AC-004` and `AC-005`.

**Depends on:** 1, 2.

### 6. Archive record and documentation

**Intent:** Let an operator find, restore and verify the archived evidence, and
let readers rely on the new contracts.

**Done when:**

- `AC-018`: For each package, a committed record lists every archived file with
  its repository-relative local path, size and SHA-256, plus a reference to the
  IDinsight Google Drive archive. A documented command verifies a restored local
  copy against that record.
- `AC-019`: Project documentation describes the runtime and archive-only file sets,
  the slim per-edge and entity provenance contracts (replacing the "complete
  original" wording), how acceptance works with and without full evidence, how to
  restore the archive locally for rebuilds, and the effect on the image, bundle
  and fresh clones.

**Depends on:** 2, 3, 4, 5.

## Assumptions

- The Drive copies and the local copies of the full evidence are byte-identical to
  today's committed files. The user confirms the Drive side; acceptance confirms the
  local side.
- New snapshot IDs for all six frameworks are acceptable to clients. Framework IDs
  stay the same.
- Small detail files such as validation reports, unresolved items, generation
  summaries, the normalization receipt and `as_standards_framework.json` may stay
  in the runtime set when Architect finds them useful.
- Whether to bump the server/MCPB version is a release decision outside this scope.
