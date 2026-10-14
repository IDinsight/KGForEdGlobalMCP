<!-- STANDARDS
Artifact: ARCHITECTURE
Cycle: slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15
-->

# Technical Design: Runtime-Only Graph Packages

Design mode: Evolution. The change replaces the accepted package contract (every
evidence file declared, loaded and committed) with a two-tier contract, and
migrates all six frameworks to new snapshots. By user decision (2026-10-14), no
backward compatibility is kept: manifest `1.1` and the full-package layout are
removed, not supported alongside the new contract.

## Context

- Scope:
  `.standards/docs/scope/slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15.md`.
  Project context: `.standards/CONTEXT.md`.
- Today one code path serves both acceptance and startup:
  `GraphPackageLoader.load` checksums every declared file, captures all nine LP
  artifacts plus 64 full-fidelity shards, and `validate_learning_progression_evidence`
  (`packages/lp_validation.py`) runs the full LP checks and emits the only LP data
  kept in memory (`JudgmentProjection` per edge, `CoverageProjection`). Startup
  and `kgfegmcp-validate-packages` both construct the loader (`bootstrap.py`,
  `cli/validate_packages.py`).
- The loader requires the package tree to match the manifest exactly, and the
  snapshot-ID suffix is computed from all declared checksums.
- `lp_normalization_receipt.json` binds the SHA-256 of every other file in the
  current full layout (`outputSha256`, keyed by package path), including the original
  index and all 64 original shards. The original index binds the original map.
  Original shards are canonical (`normalization._canonical_bytes`) partitions of
  the original map.
- Docker (`.dockerignore` allowlist) and MCPB (`cli/build_mcpb.py`) ship only
  `config/` and `data/graph_packages/`. Nothing under `data/input_artifacts/` is
  shipped.
- `data/input_artifacts/<set>/` mirrors each current full package layout byte for byte,
  and `package_build.json` maps logical names to those input paths.
- Measured on 2026-10-13: removing `claim.candidate.evidence`,
  `claim.candidate.admissible_decisions` and `claim.provenance.producer_judgment`
  from every per-edge record cuts LP per-edge provenance from 101.4 MB to about
  54.7 MB (compact canonical JSON) across six packages. Removing
  `candidate_source_refs` from AS entity items leaves about 3.1 MB.

## Decision

1. **Two-tier package contract, gated by manifest version `1.2`.** A `1.2`
   package declares only runtime files plus a declared **evidence archive
   record**. The record binds the full evidence set by logical name,
   full-evidence package path, size and SHA-256. Because the record is a declared file,
   the snapshot-ID suffix commits to the archived evidence without changing the
   identity rule. `1.2` is the only supported manifest version; `1.1` support,
   the full-package layout and every code path that exists only for them are
   removed.
2. **Two validation tiers in one loader.** The runtime tier runs at startup and
   in every validation. It reads only declared runtime files. The evidence tier
   runs only inside `kgfegmcp-validate-packages`. It verifies the archived files,
   builds an in-memory full-evidence view, runs today's LP acceptance checks on it
   with their semantics unchanged, and requires every slim artifact to equal its deterministic
   derivation from the evidence byte for byte.
3. **The input set is the local archive.** Archive-only files stay at their
   current paths under `data/input_artifacts/<set>/` and become git-ignored. The
   record stores each evidence file's repository-relative path there. The Drive
   archive mirrors those input-set folders. This leaves one restore location,
   which is also the rebuild input, and nothing under `data/graph_packages/` is
   ever git-ignored.
4. **Slimming is pure field removal plus a hash link.** Slim records are the
   original records minus named bulky fields, plus the SHA-256 of the original
   record. Derivation is one shared, deterministic, bytes-in/bytes-out module
   used by both the builder and acceptance.
5. **Keep runtime logical names; move slim files to `slim/`.** The names
   `learningProgressionProvenanceIndex`, `learningProgressionProvenanceShardNN`,
   `entityProvenance` and `learningComponentProvenance` keep their roles, rights
   classes and artifact URIs. Their content becomes slim and their paths move to
   `slim/`. Shard resolution (`partition_name`) and the rights classes therefore
   stay as they are. This avoids churn; it is not a compatibility promise.
6. **Archive the original shards and original index too.** Archiving them costs
   about 101 MB in Drive and in the local working tree. In return, today's index
   and receipt-binding checks run on real files, and no code is needed to
   reproduce the original shards.

## Acceptance Coverage

- `AC-001`: Runtime-only layout (Interfaces 1–2). The six new `1.2` snapshots
  declare exactly the runtime set. The manifest model cannot express
  archive-only kinds, and `1.1` manifests are rejected.
- `AC-002`: Delivery files are carried byte-identical. Judgment projections are
  built from slim records whose `confidence`, `rationale` and `warnings` are
  verbatim, and coverage still comes from the carried summary and report. The
  evidence tier cross-checks runtime projections against projections from full
  evidence. Expected differences are limited to snapshot identity, package and
  artifact hashes, and the `learning_progressions` resource artifact-link list,
  which now names only the declared runtime LP artifacts. Progression tool
  results keep their four derivation citations unchanged except for the slim
  index hash (Interfaces 10). See Risks.
- `AC-003`: The runtime set is estimated at about 84 MB including committed
  input-set small files, with large input-set files ignored (Interfaces 7).
- `AC-004`, `AC-005`: Evidence tier (Data and Control Flow; Interfaces 3, 6).
- `AC-006`, `AC-007`, `AC-008`: Runtime tier; the archive location sits outside
  `data/graph_packages/`; tree, checksum and policy behavior are preserved.
- `AC-009`, `AC-010`, `AC-011`: Slim LP record, index and shards (Interfaces 4);
  rights classes are unchanged.
- `AC-012`, `AC-013`: Slim AS and LC entity provenance (Interfaces 5); rights
  classes are unchanged.
- `AC-014`, `AC-015`: Ignore rules and the runtime-only build layout
  (Interfaces 7–8).
- `AC-016`: Docker and MCPB contents are unchanged by construction, because no
  archive file lives under `data/graph_packages/`.
- `AC-017`: Runtime tier needs no archive; a synthetic evidence fixture exercises
  the evidence tier (Technical Acceptance Criteria).
- `AC-018`: Evidence archive record plus the verify CLI (Interfaces 3, 9).
- `AC-019`: No architectural impact. Documenter describes the contracts this
  design fixes (Interfaces 1–9, Data and Control Flow).

## Components

- `packages/models.py`: accepts only manifest version `1.2` and its layout rules
  (Interfaces 2). Remove the `1.1` rules and the dedicated fields for
  archive-only kinds.
- `resources/policy.py`: drop the entries for logical names that can no longer
  be declared. Entries for declared names keep their classes.
- `packages/evidence_models.py` (new): evidence archive record, slim LP index,
  slim record and slim entity-document models.
- `packages/slim.py` (new): pure derivation functions from full-evidence bytes
  to slim artifact bytes and record entries. It is the single source of truth for
  derivation.
- `packages/lp_runtime.py` (new): runtime-tier LP validation from the slim index,
  slim shards, summary, report, unresolved, receipt and record. It produces
  `LearningProgressionEvidence` with the same `_projection` and `_coverage`
  semantics. Share those helpers; do not duplicate them.
- `packages/evidence.py` (new): the evidence-tier verifier. It checks archive
  files, builds a dedicated in-memory `FullEvidenceView`, runs the full LP checks
  on it, and checks derivation, projection and entity coverage equality.
- `packages/lp_validation.py`: becomes evidence-tier only. Its full LP checks
  (index and shard union, receipt binding, final claims, provenance records,
  report, summary and unresolved reconciliation) take a `FullEvidenceView`
  instead of a manifest-shaped `LoadedGraphPackage`. Check semantics and finding
  codes are preserved; only the input type changes.
- `packages/loader.py`: one path for `1.2`. Any other manifest version yields the
  existing `manifest_version_unsupported` blocking finding. It accepts an
  optional evidence verifier: `bootstrap.py` passes none (runtime tier only) and
  `cli/validate_packages.py` passes one rooted at the project directory.
- `packages/builder.py`: builds only the runtime-only layout (Interfaces 8). The
  full-package output path is removed.
- `resources/service.py`, `resources/lp.py`, `resources/models.py`: serve slim
  content and cite the record (Interfaces 4–5).
- `cli/verify_evidence_archive.py` (new) with console script
  `kgfegmcp-verify-evidence-archive` (Interfaces 9).
- `.gitignore`, the six `package_build.json` files, and `data/graph_packages/`
  (new snapshots replace old ones).

## Interfaces and Contracts

### 1. Runtime set (manifest `1.2`, mixed AS/LC/LP)

| Logical name                         | Package path                                     | Source              |
| ------------------------------------ | ------------------------------------------------ | ------------------- |
| `nodes`, `relationships`             | `delivery/…` (unchanged)                         | carried             |
| `validationReport`                   | `detailed/as_lc_validation_report.json`          | carried             |
| `unresolvedItems`                    | `detailed/as_unresolved_items.json`              | carried             |
| `standardsFramework`                 | `detailed/as_standards_framework.json`           | carried             |
| `learningComponentDedupGroups`       | `detailed/lc_dedup_groups.json`                  | carried             |
| `learningComponentSummary`           | `detailed/lc_generation_summary.json`            | carried             |
| `learningProgressionNormalization`   | `detailed/lp_normalization_receipt.json`         | carried             |
| `learningProgressionSummary`         | `detailed/lp_generation_summary.json`            | carried             |
| `learningProgressionUnresolved`      | `detailed/lp_unresolved_items.json`              | carried             |
| `learningProgressionValidation`      | `detailed/lp_validation_report.json`             | carried             |
| `learningProgressionProvenanceIndex` | `slim/lp_relationship_provenance_index.json`     | derived             |
| `learningProgressionProvenanceShard00`–`63` (additional) | `slim/lp_relationship_provenance_shard_NN.json` | derived |
| `entityProvenance`                   | `slim/as_entity_provenance.json`                 | derived             |
| `learningComponentProvenance`        | `slim/lc_entity_provenance.json`                 | derived             |
| `evidenceArchiveRecord` (additional) | `evidence/evidence_archive_record.json`          | generated           |

"Carried" means the file is byte-identical to its full-evidence input and keeps
the same logical name and package path. All derived and generated JSON uses canonical bytes:
sorted keys, compact separators, `ensure_ascii=False`, no NaN, UTF-8 and one
trailing newline, exactly as `normalization._canonical_bytes` writes them. Shard
placement stays `SHA256(UTF8(relationship_id))[0] modulo 64`.

### 2. Manifest `1.2` rules (generic, no framework branches)

- `manifestVersion` must be `1.2`, and the manifest must declare
  `evidenceArchiveRecord`.
- A manifest cannot declare `academicStandardsBundle`,
  `learningComponentsBundle`, `relationshipsHasChild`,
  `standardsFrameworkItems`, `learningProgressionFinalClaims`,
  `learningProgressionProvenance`, `learningProgressionBuildsTowards` or
  `learningProgressionRelatesTo`. The model has no fields for them, and these
  names are reserved, so they cannot be declared as additional artifacts either.
- When LP is included, the required LP set is `Normalization`,
  `ProvenanceIndex`, `Summary`, `Unresolved`, `Validation` and the 64 shard
  names. `hasLearningProgressionProvenance` means that this slim set is present.
  The capability rules are otherwise unchanged (`hasDetailedProvenance` still
  means that `entityProvenance` is declared).
- `evidenceArchiveRecord` and the shards remain additional artifacts, so they
  fail closed in the generic artifact resource, as shards do today. The record
  is never exposed.

### 3. Evidence archive record (`evidence/evidence_archive_record.json`)

```text
formatVersion: "1.0"
frameworkId: <framework id>
archive: { location: "IDinsight Google Drive" }   # fixed constant
evidenceArtifacts: {                       # the complete full-evidence declaration
  <full-evidence logical name>: {
    packagePath: <full-evidence package-relative path>,   # receipt outputSha256 key
    sha256: "sha256:<hex>", sizeBytes: <int>,
    localPath: <repository-relative input-set path>,
    runtime: <bool>                        # true = carried byte-identical
  }, ...
}
```

- `evidenceArtifacts` is exactly the full-evidence declaration for the
  package: every artifact of the full layout except a manifest, including the
  original index and the 64 original shards under their original names. These
  names and paths form the evidence namespace; they are not runtime
  declarations. Every entry has a
  `localPath`, so one record also verifies a restored input set.
- `runtime: true` requires that the runtime manifest declares the same logical
  name and path with the same SHA-256. `runtime: false` marks an archive-only
  file.
- `archive.location` is a fixed constant that names where the archive lives.
  No folder link is recorded, and no tool contacts or checks Drive. No absolute
  paths, credentials or timestamps appear in the record. The record is
  deterministic for a given build spec and evidence set.

### 4. Slim per-edge LP provenance

- **Slim record** (record format `1.0`): the original entry with exactly
  `claim.candidate.evidence`, `claim.candidate.admissible_decisions` and
  `claim.provenance.producer_judgment` removed. Add
  `original_entry_sha256 = sha256(canonical JSON of the original entry, no
  trailing newline)` in the `sha256:<hex>` form. Every other field is kept
  verbatim, including identity, endpoints, judgment (decision, direction,
  confidence, full rationale, full warnings), candidate warnings, checker
  outcome and trace hashes, model configuration and settings, attribution
  fields and all content hashes.
- **Slim shard**: a JSON object that maps `relationship_id` to its slim record.
- **Slim index** (`formatVersion` `"2.0"`): `partitionAlgorithm`,
  `partitionCount: 64`, `recordFormatVersion: "1.0"`, `removedFields` (the three
  paths above), `originalProvenanceSha256`, `originalProvenanceIndexSha256`, and
  `partitions` (`artifactPath`, `entryCount`, `sha256` per shard name).
- **Resource and `read_evidence`**: `RelationshipProvenanceResult.provenance` is
  the slim record. The result adds `archived_provenance_sha256` (from the slim
  index), and its docstring and notices drop the "complete original" wording.
  `source_artifacts` lists the manifest, the slim shard, the slim index,
  `relationships` and `evidenceArchiveRecord`. It no longer cites the undeclared
  original map. Rights checks are unchanged.

### 5. Slim entity provenance

- `slim/as_entity_provenance.json`: `formatVersion` `"1.0"`,
  `originalSha256` (the archived `as_entity_provenance.json`),
  `removedItemFields: ["candidate_source_refs"]`, `sourceDocument` (the original
  `framework` object verbatim), and `items`. Each item is the original item
  without `candidate_source_refs`, plus `original_item_sha256`. The
  `kg_run_manifest` and `relationships_has_child` sections are dropped.
- `slim/lc_entity_provenance.json`: `formatVersion` `"1.0"`, `originalSha256`,
  `sourceDocument` (`doc_key`, `pdf_name`), and `learning_components`. Each
  component record is kept verbatim plus `original_component_sha256`.
- `StandardProvenanceResult` and `LearningComponentProvenanceResult` add
  `source_document`, `attribution_statement` (from the manifest
  `rights.attributionStatement`) and `archived_provenance_sha256`.
  `source_artifacts` cites the slim artifact and `evidenceArchiveRecord`. Lookup
  keys (CASE UUID for standards, outer node ID for components) and rights checks
  are unchanged.

### 6. Validation tiers and CLI behavior

- **Runtime tier** (startup, `--runtime-only`, and the first stage of every
  validation):
  - existing tree, checksum and snapshot-identity checks;
  - `1.2` layout rules;
  - record parse and runtime agreement;
  - receipt `outputSha256` equals `{packagePath: sha256}` over every record
    entry except the receipt itself;
  - slim index binding: shard paths, hashes and counts, plus
    `originalProvenanceSha256` and `originalProvenanceIndexSha256` equal to the
    record entries;
  - every slim shard parses strictly with correct placement and no duplicate
    IDs; the union of IDs equals the LP delivery edge IDs; each record's
    identity, endpoints and decision agree with its delivery edge;
  - projections and coverage are built as described above;
  - slim entity documents are checksummed only, as entity provenance is today.
  - The runtime tier never opens `localPath`.
  - A manifest other than `1.2` fails with `manifest_version_unsupported`.
- **Evidence tier** (default in `kgfegmcp-validate-packages` for `1.2`): runs
  after the runtime tier passes (Data and Control Flow).
- **Status outcomes**:
  - If any archive-only file is absent, the result is
    `evidence_archive_unavailable`. The CLI exits non-zero without persisting a
    transition, and the package stays `pending`.
  - If a file is present but its size or hash differs (finding
    `evidence_archive_checksum_mismatch`), a full-evidence LP check fails, a derivation
    differs (`slim_derivation_mismatch`), or the projections differ
    (`slim_projection_mismatch`), the finding is blocking. A pending package
    transitions to `failed`, or to `quarantined` under that policy, exactly as
    today's blocking findings do.
- `--runtime-only` runs only the runtime tier and never persists a transition.
  Startup policies (`fail`, `quarantine`) and their handling of findings are
  unchanged.

### 7. Repository tracking

- `.gitignore`: under each `data/input_artifacts/*/`, ignore `delivery/`,
  `additional/`, and these `detailed/` files: `as_entity_provenance.json`,
  `as_kg_bundle.json`, `as_lc_kg_bundle.json`,
  `as_relationships_has_child.jsonl`, `as_standards_framework_items.jsonl`,
  `lc_entity_provenance.json`, `lp_final_claims.json`,
  `lp_relationship_provenance.json`, `lp_relationship_provenance_index.json`,
  `lp_relationships_builds_towards.jsonl` and `lp_relationships_relates_to.jsonl`.
  These rules must take effect after the existing `!/data/input_artifacts/`
  negation. Untrack the matched files with `git rm --cached`.
- Committed per input set: `package_build.json` and the small carried files
  (receipt, LP summary, validation and unresolved, AS validation report, AS
  unresolved, `as_standards_framework.json`, `lc_dedup_groups.json`,
  `lc_generation_summary.json`).
- Nothing under `data/graph_packages/` is ignored. Old snapshot directories are
  deleted from the tree; they remain in Git history and Drive.

### 8. Build spec and builder (runtime-only layout)

- The runtime-only layout is the builder's only output; `package_build.json`
  gains no layout field.
- The builder reads the spec's inputs as the full evidence set, with input
  discovery rules unchanged. It writes the carried files, the `slim/`
  artifacts (via `packages/slim.py`) and the record, and writes a pending `1.2`
  manifest. Inputs that the spec lists must exist and match.
- Reproduction means identical declared artifact bytes, and therefore the same
  snapshot ID, from the same spec and restored inputs. `createdAt` may differ.

### 9. Archive verification CLI

`kgfegmcp-verify-evidence-archive` takes `all` or `one --framework-id
--snapshot-id`. It reads only the record and the local files, so it is
read-only. For each entry it reports `ok`, `missing` or `mismatch` (size or
SHA-256), together with the archive location, and exits non-zero on any missing
or mismatched entry. It never downloads or uploads.

### 10. Progression result citations

- `ProgressionMetadata.artifacts` keeps the same four entries, in the same order
  and shape: `learningProgressionProvenance`,
  `learningProgressionProvenanceIndex`, `nodes`, `relationships`.
- Each entry resolves generically, with no name-specific branch: use the
  declared runtime artifact when the name is declared. Otherwise use the
  archived identity from the evidence archive record (an entry with
  `runtime: false`). If neither exists, raise `CapabilityUnavailableError` as
  today.
- For `learningProgressionProvenance`, `sha256` is therefore the archived
  original map's hash. That value is unchanged from today, and the runtime tier
  already checks that it equals the slim index's `originalProvenanceSha256`.
  `uri` stays the same artifact URI string. It is an identifier, not a readable
  link: the generic artifact resource reports the name as unavailable, because
  it is not declared. On today's six packages that URI was already denied by
  `allowBulkResource: false`.
- The runtime tier keeps the record's archived identities (logical name to
  SHA-256) on the loaded package, so building these results never reads files.
- Rationale: progression projections still derive from the original map's
  judgment fields, carried verbatim in the slim records. The map remains
  accepted evidence, bound by hash, and the slim index binds every slim shard.
  Keeping the citation makes tool results identical except for package-hash and
  snapshot-identity fields, as `AC-002` requires.
- Update the comment on `PROGRESSION_DERIVATION_ARTIFACT_NAMES` to say that
  entries may be archived evidence identities.

## Data and Control Flow

1. **Build:** spec and input set → builder → pending `1.2` package under the
   output root. The operator moves it into `data/graph_packages/` as today.
2. **Accept:** `kgfegmcp-validate-packages` → loader runtime tier → evidence
   verifier:
   - check every `localPath` file's size and SHA-256 against the record;
   - assemble the `FullEvidenceView`: the record's full-evidence declaration
     (logical name → package path, SHA-256 and verified bytes), with bytes read
     from the runtime file when `runtime: true` and from `localPath` otherwise.
     Add the decoded delivery, framework root, item nodes and manifest counts
     from the runtime package. This view is in memory only and never persisted.
   - run the full LP checks on that view;
   - re-derive the slim index, slim shards, slim AS and LC documents and the
     record's evidence entries, and require byte equality with the runtime
     files;
   - require the full-evidence projections and coverage to equal the runtime-tier
     projections and coverage;
   - only then may the existing persistence step write `passed`.
3. **Start:** catalog → loader runtime tier only → in-memory projections →
   serving. No archive access.
4. **Request:** per-edge provenance reads the slim index and one slim shard.
   Standard and LC provenance read their slim documents. All reads go through
   `ResourceRepository.read_artifact` with the existing size and checksum
   limits.

## Technical Acceptance Criteria

- `AC-001`: Each new manifest is `1.2` and declares exactly the Interfaces 1 set.
  Validation rejects any archive-only kind and any `1.1` manifest. No `1.1`
  package, build path or test fixture remains on the delivered branch.
- `AC-002`: Delivery file hashes equal the current snapshots'. For every edge,
  the runtime-tier `JudgmentProjection` equals the projection that today's code
  builds from the full record. Progression `artifacts` metadata differs from
  today only in the `learningProgressionProvenanceIndex` hash (Interfaces 10).
- `AC-003`: `git ls-files -z data | xargs -0 du -cb` totals ≤ 100 MB (estimate
  about 84 MB).
- `AC-004`: On the `FullEvidenceView`, the evidence tier runs every check that
  `validate_learning_progression_evidence` runs today, with the same semantics,
  and checks byte equality for every derived file. The record holds
  `packagePath`, `localPath`, `sizeBytes` and `sha256` for every full-evidence
  artifact.
- `AC-005`: Missing archive files never yield `passed`. An altered, inconsistent
  or mismatched archive yields a blocking finding.
- `AC-006`, `AC-008`: With only tracked files present, the runtime tier passes
  for all six packages under `fail`. A missing, extra or altered runtime file
  still produces today's blocking findings.
- `AC-007`: The server never resolves `localPath` or reads
  `data/input_artifacts/`.
- `AC-009`, `AC-010`: Slim records satisfy Interfaces 4. Shard ID union equals
  the LP delivery edge set. Every slim shard is ≤ the 32 MiB source-read limit.
- `AC-011`, `AC-013`: The policy classes and resource kinds for all four
  provenance and artifact surfaces are unchanged.
- `AC-012`: Every delivery standard with a CASE UUID and every LC node resolves
  to exactly one slim entry. The evidence tier checks this coverage explicitly,
  in addition to derivation equality (current packages: full coverage, no
  extras), and runtime lookups use the existing keys.
- `AC-014`: No path matched by Interfaces 7 is tracked, and every such path is
  ignored.
- `AC-015`: Rebuilding from the restored input sets reproduces each snapshot ID.
- `AC-016`: Image and MCPB stage file lists under `data/graph_packages/` equal
  the union of declared runtime files plus manifests.
- `AC-017`: CI needs no archive. The evidence tier is exercised against real
  validator code, not a mock, using a small synthetic full-evidence input set
  (committed under `backend/tests/` or generated at test time) with at least one
  passing case and failing cases for a missing file, an altered file and a
  derivation mismatch.
- `AC-018`: The verify CLI follows Interfaces 9.

## Build Plan

1. Add the evidence and slim models and `packages/slim.py`; unit-cover the
   derivations on the current packages, which are still fully present locally.
2. Add the manifest `1.2` rules, the runtime tier (`lp_runtime.py`), the
   `FullEvidenceView` evidence tier, and the validate-packages CLI changes
   (evidence required by default, `--runtime-only`, non-persisting
   `evidence_archive_unavailable`).
3. Make the builder produce only the runtime-only layout, and add the verify
   CLI.
4. Make the resource-service and result-model changes for slim LP and entity
   provenance.
5. Before deleting the old snapshots, make sure the AC-002 comparison inputs can
   be reproduced from the current snapshots; Git history is sufficient.
6. Build and accept the six `1.2` snapshots with local evidence, then delete the
   old `1.1` snapshot directories.
7. Remove the `1.1` model rules, the full-package build path, policy entries for
   names that can no longer be declared, and every test or fixture that exists
   only for `1.1`. Migrate the remaining tests to `1.2`.
8. Apply the ignore rules and untrack the matched files; measure tracked size.
9. Rework the tests that read full evidence. Add the synthetic evidence fixture
   and run the STDIO, HTTP loopback, MCPB stage and Docker smokes.

Steps 2–6 may temporarily leave `1.1` code in place so the suite keeps running
against the current packages. The delivered branch must not contain it.

## Risks and Follow-up

- **Size margin:** the estimate is about 84 MB against the 100 MB cap. If the
  measured size exceeds the cap, the fallback is to hoist per-package constant
  per-edge fields (`attribution_statement_template`, `model_configuration`,
  `model_settings`, `source_framework`; about 8.5 MB) into the slim index and
  re-inflate them at response time. Adopting it would revise this design.
- **Client-visible changes:** new snapshot IDs, a slimmer per-edge payload, the
  added result fields, the `learning_progressions` resource artifact list
  shrinking to the declared runtime LP artifacts, and archived-artifact URIs
  (such as the progression citation for `learningProgressionProvenance`)
  answering "unavailable" instead of "access denied". All of these follow from the
  scope and must be documented under AC-019.
- **Cutover:** once `1.1` loading is removed, the six current snapshots no
  longer start. Removal therefore has to land after the six `1.2` snapshots are
  accepted (Build Plan 6–7), so the server never lacks a loadable package. Older clients or tools that read `1.1` packages are not supported.
- **Evidence-tier cost:** acceptance memory and time stay at today's levels for
  CBSE. Startup gets cheaper, because the final claims, the original map and
  the split JSONL are no longer parsed.
- **Shared evidence location:** the input sets double as the archive. An
  operator who edits an input set invalidates acceptance for its package, which
  is the intended behavior.

## Alternatives

- **Separate `data/package_evidence/` tree:** rejected. It duplicates the input
  sets and creates two restore locations.
- **Evidence section inside the manifest:** rejected. It would not enter the
  snapshot identity unless the identity rule changed.
- **Re-derive the original shards and index at acceptance instead of archiving
  them:** rejected. It needs new reproduction code and weakens the "today's
  checks unchanged" guarantee, while saving only Drive space.
- **New logical names for slim artifacts:** rejected. They would change the
  policy table and artifact URIs for no runtime benefit.
- **Git LFS, history rewriting, fetching the archive at Railway build time:**
  excluded by scope or constraints.
