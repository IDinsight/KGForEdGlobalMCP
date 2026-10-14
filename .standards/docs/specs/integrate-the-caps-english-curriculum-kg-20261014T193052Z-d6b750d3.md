<!-- STANDARDS
Artifact: ARCHITECTURE
Cycle: integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3
-->

# Technical Design: Integrate CAPS English Home Language (Grades R-3)

Design mode: `FEATURE`. Adding CAPS is a bounded capability that runs through
the established onboarding route. It changes no foundational structure, needs
no transition or compatibility mechanism, and defines no new shared rule.

## Context

- Scope: `.standards/docs/scope/integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3.md`
  (`AC-001`..`AC-021`). Its rights, footprint, and Grade R decisions are fixed
  inputs here.
- Project context: `.standards/CONTEXT.md`. The decisive facts:
  - Onboarding is data and configuration only.
  - The builder takes the framework ID from the profile's single
    `frameworkIds` entry. It also takes `name`, `jurisdiction`, `author`,
    `academicSubject`, `license`, and `attributionStatement` from the root
    `StandardsFramework` node, and it enforces exact agreement between the
    profile and that root.
  - The validator requires every item `gradeLevel` to appear verbatim in some
    `gradeMappings[].normalizedGrades`.
  - The search service treats node `gradeLevel` values as the normalized
    grade facet. It resolves the local grade label from the mapping whose
    `normalizedGrades` contains that value (`search/service.py`
    `evidence()`).
  - Learning Progression disclosures are generic code, not profile data
    (`mcp/tools/learning_progressions.py`, `prompts/`).
  - Docker (`.dockerignore` allowlist) and MCPB copy all of `config/` and
    `data/graph_packages/`. `.gitignore` wildcard rules already cover any new
    input set.
- Source export facts are listed in CONTEXT.md under **External Systems and
  Data**. The upstream run configuration in `kgs/kg_run.json`, under
  `extra.as`, holds the statement-type, parent, identity-scope, and grade
  policy the export was extracted with. Its `extra.metadata` holds the
  framework identity. That file is not in the 23-file copy set, so it is read
  from the external export, read-only, only to author the profile.
- `data/graph_packages/.claude/` was absent when this design was written, on
  2026-10-14. The catalog-loading hazard noted in CONTEXT.md does not apply
  unless that directory reappears.

## Decision

Add CAPS as a seventh framework using only new data and configuration files.
Code under `backend/src/` does not change. Every identity value is fixed here,
so the build is reproducible and reviewable.

| Item | Fixed value |
| --- | --- |
| Framework ID = profile ID | `south-africa-dbe-caps-english-home-language-grades-r-3` |
| Profile path | `config/profiles/<framework-id>/2.0/profile.json` (`profileSchemaVersion` `1.1`, `profileVersion` `2.0`) |
| Prompt overlay | `config/prompts/<framework-id>/2.0/prompts.json`, `promptConfigId` `<framework-id>-guidance`, schema `1.1`, version `2.0.0` |
| Input set | `data/input_artifacts/south_africa_english/` |
| `versionToken` | `2011` |
| `sourcePublicationDate` | `null` |
| `jurisdictionType` | `country` |
| `packageRevision` / `snapshotRelations` | `1` / `[]` |
| Snapshot ID | `<framework-id>@2011+<12-hex>`, derived by the builder |
| Source document key | `c939a3a9dcce92ed61d970f4599ced6f2ddc425d1220eeeab9828472b878d24d` |
| Framework CASE UUID | `7bb16abe-6d0a-5bb9-9a01-aeb7c4baeaa3` |
| Normalized grades | `K`, `1`, `2`, `3`; `K` is labelled "Grade R" |

Rationale for the material choices:

- **Framework ID.** It follows the existing pattern
  `<jurisdiction>-<authority>-<subject>-<grade span>`, using DBE as the
  authority token (compare `nacca`, `nerdc`, `reb`). `caps` is kept because
  it names the curriculum. The ID is well under the 200-character
  `FrameworkId` limit.
- **Version token `2011`.** The source's own attribution prints "© 2011". That
  identifies the CAPS edition the same way Ghana's `2019` does. The token is a
  source-version label, not a publication date. Because no exact date is
  established, `sourcePublicationDate` stays `null`.
- **Grade R as normalized `K`.** The delivery nodes must stay identical to the
  source, so their `gradeLevel` stays `"K"`. The validator requires that
  value verbatim in `normalizedGrades`, and the search service uses node
  values as the normalized facet. `K` is therefore the only normalized value
  that needs no source rewrite and no generic code change. The Grade R
  presentation comes from the mapping's `localLabel` "Grade R". A profile
  anomaly disclosure states that `K` is the source encoding and does not
  establish equivalence with any other system.
- **No education-stage mapping.** `educationStageMappings` stays `[]`, as in
  all six profiles. "Foundation Phase" remains visible in the framework name.
  Adding a stage would put a seventh value into `localGradesOrStages`, and no
  existing package exercises that generic path.
- **Prompt overlay.** All six frameworks ship one. Adding it keeps prompt
  behavior consistent without changing the prompt surface.
- **Receipt authoring stays out of the codebase.** Nothing in the repository
  writes `copy_receipt.json`, by established practice. The copy and its
  receipt are a one-off local operator step validated by the strict
  `CopyReceipt` models. Adding a writer CLI would be new generic code that
  no AC requires.
- **MCPB manifest version correction (revised after `DEV-006`).** The MCPB
  build refuses to run unless `packaging/mcpb/manifest.json` `version` equals
  `backend/pyproject.toml` `version` (`cli/build_mcpb.py`, about line 657).
  Release `1.0.0` (`868eeb1`) bumped the project to `1.0.0`, but
  release-please's `extra-files` do not include the MCPB manifest, so it was
  left at `0.4.0`. No repository MCPB build can pass until the two match, so
  `AC-014` cannot be met without fixing this. The only value the existing
  check accepts is the shipped project version, `1.0.0`. This cycle therefore
  changes that one field and nothing else. It does not cut a release: no
  version is bumped, no tag or changelog entry is made, and nothing is
  published. Making release-please keep the two versions in step is a
  separate release-tooling follow-up.

## Acceptance Coverage

- `AC-001`: Covered by **Source copy and receipt** under Interfaces and
  Contracts, and by build-plan step 1.
- `AC-002`: Input-set layout and `package_build.json` contract. The package
  goes through the build → read-only validate → persist → install lifecycle
  (Data and Control Flow) and must reach a terminal `passed` state.
- `AC-003`: The package's counts come from decoded delivery facts. No
  normalization rule is expected to change any count: LP normalization
  appends edges and preserves node and AS/LC bytes. Any difference must cite
  the rule responsible.
- `AC-004`: The builder's established determinism contract. The committed
  `package_build.json`, the committed small inputs, and the archive-only
  inputs fully determine the package.
- `AC-005`: File-size and served-artifact limits under **Size and exposure**.
  The archive-only inputs are git-ignored by existing wildcard rules, and
  the builder writes their entries into `evidence/evidence_archive_record.json`.
- `AC-006`: Existing `kgfegmcp-verify-evidence-archive one` and full
  `kgfegmcp-validate-packages one` against the restored local input set. No
  new mechanism.
- `AC-007`, `AC-008`, `AC-009`, `AC-010`: The CAPS profile contract under
  **Interpretation profile**, with framework metadata derived by the builder
  from the source root and the profile.
- `AC-011`, `AC-012`, `AC-013`: Generic catalog, search, graph, resource,
  prompt, and LP services pick CAPS up by directory discovery. With rights
  as fixed, the CAPS profile and overlay make every existing tool, resource
  template, and prompt applicable. LP disclosures are generic. Path search
  keeps its existing generic bounds: `max_depth` is at most 12, plus queue
  and work limits. That is enough for traversal and path lookup in CAPS's
  short and typical connections. Long CAPS connections may come back
  truncated, with the reasons stated, as described under **Bounded path
  search**.
- `AC-014`, `AC-015`: The existing MCPB stage builder and the Docker
  allowlist copy `config/` and `data/graph_packages/` wholesale. No
  per-framework list is added or needed. For `AC-014`, the MCPB manifest
  version correction is also required.
- `AC-016`, `AC-017`, `AC-018`: Additive-only change set under **Change
  boundary**. No edits to existing packages, profiles, overlays, or
  `backend/src/`.
- `AC-019`: Corpus-dependent test expectations under **Test-corpus
  contract**.
- `AC-020`, `AC-021`: No architectural impact. They depend on Documenter's
  phase. The values those documents must state are fixed here (identity,
  grades, codes, rights, and the bounded path-search behavior for long CAPS
  connections) or come from the accepted CAPS manifest (counts, sizes,
  snapshot ID).

## Components

All new artifacts are additive. The existing generic components consume them
unchanged.

- **Local source copy** (git-ignored):
  `data/source_artifacts/learning_progressions/<doc-key>/kgs/`, holding the
  23-file copy set, plus `data/source_artifacts/learning_progressions/copy_receipt.json`.
- **Prepared output** (git-ignored):
  `data/source_artifacts/learning_progressions/prepared/<framework-id>/`,
  written by `kgfegmcp-prepare-learning-progressions`.
- **Input set** `data/input_artifacts/south_africa_english/`:
  - `package_build.json` and the 9 small `detailed/` files, committed.
  - `delivery/`, `additional/` (64 original shards), and the 11 archive-only
    `detailed/` files, git-ignored and held in the archive.
- **Interpretation profile** and **prompt overlay** under `config/`.
- **Graph package** `data/graph_packages/<framework-id>/<snapshot-id>/`: the
  runtime-only layout, matching the existing six.
- **Test fixture entry**: a CAPS entry in
  `backend/tests/fixtures/progression_baseline.json`.

## Interfaces and Contracts

### Source copy and receipt

- Copy exactly the 23 files listed in `docs/development/framework-package.md`
  from the external `kgs/` directory into the local copy directory. Use
  read-only access to the source and modify nothing there.
- Write `copy_receipt.json` so that it validates against
  `packages/normalization_models.py` `CopyReceipt`:
  - `receiptVersion` `1.0` and `status` `verified`.
  - `selectedFileCount` 23.
  - One `frameworks` entry: the document key, the CASE UUID, the framework
    ID, and the destination directory.
  - One `files` entry per file: `sourceSha256Before` (hashed before
    copying), `sourceSha256After` (re-hashed after copying),
    `destinationSha256`, `sizeBytes`, and `verified: true`. All three hashes
    must be equal and every size must match.
- Prove the external export is unchanged: record a manifest of the external
  `kgs/` directory (relative path, size, and SHA-256 of every file) before
  the copy and compare it after the copy. This proof is operator evidence for
  `AC-001`. It is not a repository artifact.

### Input set and build spec

- Move the prepared `delivery/`, `detailed/`, and `additional/` output into
  the input set unchanged.
- Author `package_build.json` from the Nigeria template, changing only these
  fields:
  - Every path points to `data/input_artifacts/south_africa_english/`.
  - The delivery file names are
    `as_lc_lp_{nodes,relationships}_<framework-id>.jsonl`, as preparation
    names them.
  - `profileId`, `versionToken` `2011`, `jurisdictionType` `country`, and
    `sourcePublicationDate` `null`.
  - `outputRoot` stays `data/source_artifacts/learning_progressions/rebuilt_packages`,
    consistent with the six committed specs.
- All 64 `learningProgressionProvenanceShardNN` entries are present.
- Do not set `sourceDocument`. The source PDF is not in the copy set, and the
  scope does not require it.

### Interpretation profile

Author the profile by transforming `kg_run.json` `extra.as` field by field,
plus the rights decision. Use the existing profiles for the shape and for the
fields upstream does not carry.

- `frameworkIds`: `[<framework-id>]`.
- `localSubject`: `English Home Language`. `normalizedSubjects`:
  `["English Language Arts"]`. `subjectMappingStatus`: `mapped`. The
  `subjectMappingNote` follows Ghana English's wording.
  `subjectAliases`: `[]`. `subjectVocabulary` is identical to the existing
  profiles.
- `gradeMappings`, in this order:
  - `Grade R` → `["K"]`
  - `Grade 1` → `["1"]`
  - `Grade 2` → `["2"]`
  - `Grade 3` → `["3"]`

  Each mapping's aliases are the upstream Grade controlled-value aliases for
  that grade. Normalized alias keys must not collide across mappings.
- `gradeLevelStatementTypes`: `["Grade"]`. `educationStageMappings`: `[]`.
- `statementTypes`: one entry per upstream `statement_type_policy` entry
  (Grade, Term, Skill Area, Sub-strand, Skill), mapped as follows:
  - `statement_type` → `sourceStatementType`.
  - `aliases`, `description`, and `normalized_statement_type` →
    `normalizedStatementType`. Skill becomes `Standard`; the other four become
    `Standard Grouping`.
  - `controlled_values` → `controlledValues`, with fields `aliases` and
    `canonicalValue`.
  - `allowedParents` comes from `sfi_has_child_parent_policy`, with fields
    `minCount`, `maxCount`, and `parentStatementType`.
  - `identityScope` comes from `identity_scope_statement_types` (Grade:
    `[]`).
  - `isGraphNode`: `true`.

  Wording is copied verbatim. Nothing is invented.
- `hierarchy`:
  - `relationshipType`: `hasChild`.
  - `allowMultiParent`: `false`. The source is a strict tree.
  - `rootStatementTypes`: `["Grade"]`.
  - `statementTypeOrder`: `["Grade","Term","Skill Area","Sub-strand","Skill"]`.
- `codeSearchPolicy`: identical to the Nigeria profile. Availability is
  `none`, there are no code types or code-parent rules, and prefix search is
  off.
- `knownSourceAnomalies`, two entries:
  - `uncoded_repeated_skill_statements`: CAPS prints no statement codes. The
    same Skill wording repeats across sub-strands, terms, and grades, and each
    occurrence is scoped by Grade, Term, Skill Area, and Sub-strand. Required
    disclosure: "Code search is unavailable; text and hierarchy context are
    used for retrieval."
  - `grade_r_encoded_as_k`: the source encodes Grade R items as `gradeLevel`
    `"K"`. The profile labels them "Grade R" and keeps `K` as the retrieval
    facet. Required disclosure: "Grade R items carry the normalized grade
    facet K, which is the source's encoding and does not establish
    equivalence with kindergarten or any other system's grade."
- `requiredDisclosures`, `comparisonDimensions`, and `sourceRoleCapabilities`:
  identical to the existing profiles.
- `languagePolicy`:
  - `languages`: `["en"]`.
  - `allowBilingualPairing`: `false`.
  - `preserveSourceTerminology`: `true`.
  - `notes`: `[<upstream bilingual_pair_policy text>]`.
- `rights`:
  - `reviewStatus`: `provisional_operator_approved`.
  - `allowGeneratedDerivatives`: `allowed`.
  - `allowFullText`: `true`.
  - `allowBulkResource`: `false`.
  - `allowStandardResources`: `true`.
  - `sourceLicense`: `Unknown`.
  - `attributionStatement`: equal to the root's string, code point for code
    point, including "©".
- File formatting matches the existing profiles: sorted keys, tab
  indentation, UTF-8, and a single trailing newline.

### Prompt overlay

- Same shape as the existing overlays: guidance for `studentHandbookSection`,
  `studentStudySupport`, and `teacherGuideDraft`, with the same guidance keys
  and `mode: append`.
- The content adapts the Ghana English overlay to CAPS terminology: Grade R
  and Grades 1-3, Terms 1-4, the skill areas (Listening and Speaking (Oral),
  Emergent Reading and Writing, Reading and Phonics, Writing), and Home
  Language.
- The overlay is soft, framework-local guidance:
  - Any added example must be labelled as generated.
  - The overlay makes no source assertions and states no pedagogical
    judgments about CAPS content.
  - It stays at or below 64 KiB.
- It must resolve against the CAPS profile identity and version.

### Size and exposure

- Every committed CAPS file is ≤ 100 MB. Expected sizes:
  - Largest committed file: delivery relationships, about 16 MB.
  - `slim/as_entity_provenance.json`: below the 14.6 MB source map.
  - Slim shards: about 1.1 MB each.
- Under CAPS rights, only `PUBLIC_METADATA` and `FULL_TEXT` artifacts and
  single-edge evidence reads are served. Each must keep its source bytes
  ≤ `max_resource_source_bytes` (32 MiB) and its served payload ≤
  `max_resource_bytes` (8 MiB). The `BULK_CONTENT` artifacts, including the
  delivery files, are denied by rights.
- Default limits in `config.py` are not raised.

### Change boundary

- No change to:
  - `backend/src/`
  - any existing `data/graph_packages/*`, `config/profiles/*`,
    `config/prompts/*`, or `data/input_artifacts/*` path
  - `Dockerfile`, `.dockerignore`, or `.gitignore`
  - `packaging/`, except the single `version` field of
    `packaging/mcpb/manifest.json`, which changes from `0.4.0` to `1.0.0`
  - `release-please-config.json`, `.release-please-manifest.json`,
    `CHANGELOG.md`, and the project version in `backend/pyproject.toml` and
    `backend/uv.lock`
  - the smoke CLIs' pinned diagnostics (`cli/smoke_checks.py`,
    `cli/smoke_access.py`)
- If implementation finds that a backend code change is unavoidable, stop
  and route an `ARCHITECTURE` failure. Do not add a framework-specific branch
  or relax a rule.

### Test-corpus contract

- Corpus-size assertions move from 6 to 7 frameworks.
- LP edge totals move from 8,080 to 8,080 plus the CAPS package's LP edges
  (expected 17,667).
- `progression_baseline.json` gains one CAPS entry. The six existing entries
  stay byte-identical.
  - Its `nodeCount`, `nodesDigest`, `hasChildCount`, `hasChildDigest`,
    `supportsCount`, and `supportsDigest` are computed with the existing
    `semantic_baseline` helper from the source's AS/LC-only export
    (`as_lc_nodes.jsonl`, `as_lc_relationships.jsonl`) in the verified local
    copy. This makes the baseline an oracle independent of the build.
  - Its `originalSnapshotId` is the accepted CAPS snapshot ID, because no
    pre-LP CAPS package exists.
- The exhaustive buildsTowards pair check stays limited to the six existing
  frameworks, with their result still pinned at 6,522 pairs and a longest
  shortest path of 8. CAPS is excluded from that check because an exhaustive
  pairwise search over its 2,879 buildsTowards edges is too slow (user
  decision, 2026-10-14).
- CAPS gets a small, deterministic sample of connected buildsTowards pairs
  instead, pinned from the accepted package. The goal is evidence that CAPS
  traversal works, not full enumeration. The sample has two parts:
  - **Short pairs.** At least one direct pair and one multi-hop pair, each
    with a shortest path of 8 hops or fewer. For each, the check asserts the
    invariants the exhaustive check applies:
    - exactly one path, of the oracle's hop count, from the source to the
      target;
    - the returned relationships equal the path's relationships;
    - the response stays within its envelope bounds.
  - **Long pair.** At least one pair with a shortest path of 9 or more hops,
    for example the 11-hop pair `DEV-006` measured. Its check asserts the
    honest-bound contract described under **Bounded path search**, and
    neither requires nor forbids a found path.
- The rights-flag assertions over all packages then cover CAPS without
  further change.
- No test calls a live or paid LLM service.

### Bounded path search

`get_learning_progression_paths` and traversal keep their existing generic
limits: request `max_depth` of at most 12, plus internal queue and work
limits. Neither the limits nor `config.py` change for CAPS.

- `DEV-006` measured CAPS on 2026-10-14: 43,145 connected buildsTowards
  pairs. Their shortest paths are up to 13 hops, compared with 8 for the
  existing six.
- Every sampled pair of 8 hops or fewer returned its complete shortest path.
  Some pairs of 9 or more hops returned no path, reporting `queue_limit`,
  `depth_limit`, or `work_limit` in `truncation_reasons`. A 13-hop
  connection is beyond the request's `max_depth` ceiling.

This is the established contract: a bounded search that reports incomplete
results instead of failing or inventing a path. The contract every result must
satisfy is:

- either the complete shortest path of the requested length, with matching
  endpoints and relationships;
- or no path, with non-empty `truncation_reasons`.

A path that is wrong, partial, or the wrong length is a defect. A truncated
result for a long CAPS connection is not.

## Data and Control Flow

```text
external kgs/ (read-only)
  └─ copy 23 files + receipt ─▶ data/source_artifacts/learning_progressions/<doc-key>/kgs/
       └─ kgfegmcp-prepare-learning-progressions --framework-id <id>
            ─▶ data/source_artifacts/learning_progressions/prepared/<id>/
                 └─ move ─▶ data/input_artifacts/south_africa_english/ (+ package_build.json)
                      └─ kgfegmcp-build-manifest --spec <abs, local copy with fresh outputRoot> [--dry-run]
                           ─▶ <fresh root>/<id>/<snapshot-id>/  (pending)
                                └─ validate one --read-only (KGFEGMCP_GRAPH_PACKAGES_ROOT=<fresh root>)
                                     └─ validate one (persist pending → passed)
                                          └─ move ─▶ data/graph_packages/<id>/<snapshot-id>/
```

- The profile must exist before the build, because the builder binds the
  profile's bytes into the snapshot.
- Profile and overlay edits after acceptance require a new snapshot. Never
  edit the accepted package.
- Build into a fresh, unused, git-ignored output root using a local copy of
  the spec, as documented. Only a terminal `passed` package is moved into
  `data/graph_packages/`.
- At server start, catalog discovery loads seven packages. Search, graph, and
  resource indexes are built per package with no cross-package coupling, so
  the six existing runtimes are unaffected.

## Technical Acceptance Criteria

- `AC-001`: Every local copy matches its receipt entry: equal source-before,
  source-after, and destination hashes, plus size. `CopyReceipt` validation
  passes. The before and after manifests of the external `kgs/` directory
  are identical.
- `AC-002`: The installed package's manifest has `validation` status
  `passed`. Its `profile` reference is `<framework-id>` version `2.0`. Its
  snapshot ID matches `<framework-id>@2011+<12-hex>`.
- `AC-003`: The manifest counts and the decoded delivery counts equal the
  scope's figures (1 / 1,144 / 912 / 1,144 / 1,204 / 2,879 / 6,708).
- `AC-004`: A rebuild from the committed spec, with the input set restored
  from the archive set, yields the same snapshot ID and byte-identical
  package files. The only exception is `package_manifest.json`, whose
  differences are limited to `createdAt` and validation state, per the
  builder's documented determinism contract. The user confirmed on
  2026-10-14 that this is what "identical package" means.
- `AC-005`:
  - No committed CAPS file exceeds 100 MB.
  - No CAPS artifact or evidence read permitted under CAPS rights exceeds the
    default `config.py` limits.
  - `git check-ignore` matches every archive-only input.
  - Every archive-only input appears in the evidence archive record.
- `AC-006`: `verify-evidence-archive one` reports `ok` for every CAPS entry.
  Full `validate-packages one --read-only` reports no findings.
- `AC-007`, `AC-010`: The served framework metadata reports:
  - the root `name`
  - `jurisdiction` South Africa
  - `jurisdictionType` `country`
  - `issuingAuthority` Department of Basic Education
  - `localSubject` English Home Language
  - `localGradesOrStages` `["Grade R","Grade 1","Grade 2","Grade 3"]`

  Its rights equal the profile values above.
- `AC-008`: Every item `gradeLevel` is in `{K,1,2,3}`. A `"K"` item's facets
  show the resolved local label `Grade R`. Filtering by the local label
  `Grade R` or the normalized grade `K` returns exactly the 385 `"K"` items
  among CAPS hits. The same holds for Grades 1-3.
- `AC-009`: Capabilities report code search as unavailable for CAPS, and
  code-mode searches scoped to CAPS return no CAPS hits.
- `AC-011`: The catalog lists 7 frameworks. Catalog and framework statistics
  for CAPS equal its manifest counts.
- `AC-012`, `AC-013`: A client on a real STDIO transport, launching the
  repository server and calling no LLM, retrieves, searches, and gets
  context for CAPS standards and Learning Components. It also looks up,
  searches, and traverses CAPS LPs. LP responses carry the same generic
  disclosure text as the other frameworks. CAPS path results satisfy
  **Bounded path search**.
- `AC-014`:
  - `packaging/mcpb/manifest.json` `version` equals `backend/pyproject.toml`
    `version` (`1.0.0`).
  - `kgfegmcp-build-mcpb` produces a fresh stage that contains the CAPS
    package, profile, and overlay.
  - `kgfegmcp-stdio-smoke --bundle-root <stage>` passes.
- `AC-015`: `Dockerfile` and `.dockerignore` are unchanged, and the build
  context includes the CAPS package, profile, and overlay paths.
- `AC-016`: `git diff <cycle-baseline> --` over the six packages, profiles,
  overlays, and input sets is empty. The cycle baseline is the commit the
  cycle's implementation starts from, currently `f9fdaa2`. Outside the CAPS
  additions, the only tracked change outside `.standards/` is the
  one-field `packaging/mcpb/manifest.json` version correction.
- `AC-017`: The listed public surface counts are unchanged: 19, 1, 14, 9.
- `AC-018`: The cycle's diff contains no changes under `backend/src/`, and
  the CAPS framework ID appears in no generic runtime, build, or validation
  source file.
- `AC-019`: The full offline suite passes under the **Test-corpus contract**
  above.

## Build Plan

1. Record the external manifest. Copy the 23 files, write and validate the
   receipt, then re-check the external manifest. (`AC-001`)
2. Author the CAPS profile and prompt overlay. Load both through the existing
   loaders to confirm schema validity. (`AC-007`..`AC-010`)
3. Run the prepare command for CAPS. Move its output into the new input set
   and author `package_build.json`.
4. Dry-run the build. Build into a fresh root, validate read-only, persist
   acceptance, and install the passed package under `data/graph_packages/`.
   (`AC-002`..`AC-006`)
5. Update corpus-dependent test expectations and add the CAPS baseline entry.
   Run the full offline suite. (`AC-016`..`AC-019`)
6. Run the repository STDIO smoke test and a STDIO session that exercises
   CAPS. Correct the MCPB manifest version, then build the MCPB stage and
   run the stage smoke test. Confirm the Docker build context.
   (`AC-011`..`AC-015`)
7. Prove determinism with a second build from the committed spec into
   another fresh root. (`AC-004`)

## Risks and Follow-up

- **Version token `2011` is a judgment.** It rests on the source's printed ©
  year. Changing it later requires a new snapshot ID, though not a new
  framework ID.
- **Footprint.** The repository, image, and bundle roughly double in size.
  The user accepted this.
- **Memory.** Build and acceptance load the about-119 MB provenance and
  about-127 MB final-claims files whole. This is acceptable on a developer
  machine.
- **Stray directory.** If `data/graph_packages/.claude/` reappears, local
  catalog loading and tests fail. Run verification without it.
- **Leftover lock file.** The empty `.lp_generation.lock` in the source is
  treated as leftover, per scope. It is not in the copy set.
- **Archive upload.** Uploading the new input set to the Google Drive archive
  is a user-owned follow-up.
- **MCPB version drift will recur.** release-please does not update
  `packaging/mcpb/manifest.json`. The next release that bumps the project
  version will break the MCPB build again. Adding that file to release-please
  `extra-files` belongs in a separate release-tooling change. Docs that name
  the default bundle file `dist/kgfegmcp-0.4.0.mcpb` will no longer match the
  build output, which is now named for `1.0.0`. Dated statements about 0.4.0
  installs remain historically true.
- **Long CAPS connections are truncated.** Some CAPS connections of 9 or more
  hops come back from path search as truncated, with the reasons stated,
  instead of as a path. Raising the generic limits would change behavior for
  every framework, so it is out of scope. The user documentation should
  state this for CAPS (Documenter).

## Alternatives

- **Normalized grade `R` or `0` for Grade R.** Rejected. It would require
  rewriting source `gradeLevel` values or adding generic remapping code,
  which conflicts with source fidelity and `AC-018`.
- **A "Foundation Phase" education-stage mapping.** Rejected. It adds an
  unexercised generic path, and no AC needs it.
- **Extending the smoke CLIs with CAPS diagnostics.** Rejected. It would add
  framework-pinned code that `AC-012`/`AC-013` do not need, and a generic
  STDIO session covers them.
- **A framework ID without the authority token**
  (`south-africa-caps-english-home-language-grades-r-3`). Rejected for
  consistency with the existing IDs.
- **`versionToken` `undated`.** Viable, but rejected because the source
  itself identifies its edition year.
- **Leaving `packaging/` untouched and building the MCPB stage from a
  temporary corrected manifest.** Rejected. The stage would not be built from
  the repository as `AC-014` requires, and the repository's MCPB build would
  stay broken.
- **Raising path-search limits or making them depend on package size.**
  Rejected. It changes generic behavior and limits for all frameworks, which
  conflicts with `AC-016` and `AC-018`.
