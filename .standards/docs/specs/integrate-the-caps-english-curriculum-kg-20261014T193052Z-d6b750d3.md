<!-- STANDARDS
Artifact: ARCHITECTURE
Cycle: integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3
-->

# Technical Design: Integrate CAPS English Home Language (Grades R-3)

Design mode: `EVOLUTION` (revised 2026-10-14 after the scope replan). Most of
the cycle is still a bounded data and configuration onboarding. The replan,
however, replaces the existing path-search algorithm, which every framework
uses. Keeping the results that search already returns unchanged (`AC-022`,
`AC-024`) is now the primary design risk.

## Context

- Scope: `.standards/docs/scope/integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3.md`
  (current: `AC-001`..`AC-015`, `AC-017`..`AC-027`; `AC-016` retired and
  replaced by `AC-022`). Its rights, footprint, Grade R, and path-search
  decisions are fixed inputs here.
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
- Existing path search (`services/lp_paths.py`, at the cycle baseline):
  - It is a breadth-first enumeration of partial paths. Each partial path
    keeps its own visited set, and nothing is shared between paths.
  - Edges are visited in `relationship_id` order, from the sorted
    `TraversalAdjacency`. Results therefore come out by hop count, then by
    relationship-ID tuple.
  - It stops at 5,000 inspected relationships (`work_limit`), 5,000 created
    states (`queue_limit`), `max_paths` (`path_limit`), extensions beyond
    `max_depth` (`depth_limit`), or the envelope size (`byte_limit`).
  - `GetLearningProgressionPathsRequest.max_depth` allows 1 to 12 (default
    6) in `services/lp_models.py`. The MCP tool takes that model directly,
    so the tool schema follows it.
  - The search never looks toward the target, so on CAPS it fills its
    budgets before reaching 9–11 hop targets (`DEV-006`).
- Accepted packages have acyclic buildsTowards graphs. Both validation tiers
  reject a directed buildsTowards cycle (`packages/lp_graph.py`
  `lp_builds_towards_cycle`), and the LP report models require
  `graph_status: acyclic`. In a DAG every path is simple, so an exact
  length-based search is valid.
- `data/graph_packages/.claude/` was absent when this design was written, on
  2026-10-14. The catalog-loading hazard noted in CONTEXT.md does not apply
  unless that directory reappears.

## Decision

Add CAPS as a seventh framework using only new data and configuration files.
Separately, replace the generic path-search algorithm with an exact-length,
target-aware search and raise the path `max_depth` ceiling to 16. That is the
only change to `backend/src/`, and it contains no framework-specific branch.
Every CAPS identity value is fixed here, so the build is reproducible and
reviewable.

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
- **Exact-length target-aware path search (scope replan).** Pruning the
  existing breadth-first search is not enough. Breadth-first search finishes
  every partial path of length *k−1* before it completes any path of length
  *k*. With `max_depth` headroom above the shortest length, those detour
  prefixes still multiply and fill the 5,000 budgets.
  - The design instead computes, from the target backwards, which exact hop
    counts can still reach the target from each node.
  - It then emits paths length by length, depth-first in relationship-ID
    order, along edges that can still finish at exactly that length.
  - Every partial path it creates therefore becomes a returned path. The
    work grows with the paths returned, not with the size of the graph.
  - The output order is the existing one: hop count, then relationship-ID
    tuple.
  - Architect measurement, 2026-10-14, scratch script over the committed
    delivery files: all 6,522 connected pairs in the six packages and all
    43,145 CAPS pairs. Each pair was requested with (`max_depth` = shortest
    length, `max_paths` 1), (16, 3), and (16, 20).
  - The first path was the oracle's shortest every time. The worst request
    used 1,810 inspections (backward plus forward) and 218 states, against
    budgets of 5,000 each. The CAPS backward pass alone peaked at 1,126
    inspections.
  - This measurement is design evidence, not Tester verification.

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
  template, and prompt applicable. LP disclosures are generic. CAPS path
  lookups use **Target-aware path search**.
- `AC-014`, `AC-015`: The existing MCPB stage builder and the Docker
  allowlist copy `config/` and `data/graph_packages/` wholesale. No
  per-framework list is added or needed. For `AC-014`, the MCPB manifest
  version correction is also required.
- `AC-022`: The six existing packages, profiles, and overlays are not
  edited (**Change boundary**). Path-search results keep the
  **Compatibility contract** under **Target-aware path search**. Requests
  the baseline truncated may now come back complete or with different
  truncation reasons.
- `AC-017`: No tool, resource, template, or prompt is added or removed. Only
  the existing `max_depth` bound of `get_learning_progression_paths` changes
  (`AC-023`).
- `AC-018`: The change to `backend/src/` is the generic path-search
  replacement and request bound. It contains no framework ID and relaxes no
  validation rule.
- `AC-023`: The request-model bound under **Target-aware path search**.
- `AC-024`: Same order and the **Compatibility contract**. The argument rests
  on validated acyclicity.
- `AC-025`: The exact-length search with its measured budgets, under the
  fixed 5,000 limits.
- `AC-026`: **Result invariants** under **Target-aware path search**.
- `AC-019`: Corpus-dependent test expectations under **Test-corpus
  contract**.
- `AC-020`, `AC-021`, `AC-027`: No architectural impact. They depend on
  Documenter's phase. The values those documents must state are fixed here
  (identity, grades, codes, rights, the path `max_depth` ceiling of 16, and
  how target-aware search behaves) or come from the accepted CAPS manifest
  (counts, sizes, snapshot ID).

## Components

The CAPS artifacts are additive, and the existing generic components consume
them unchanged. The one generic component that changes is path search.

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
- **Path search** (`services/lp_paths.py`): `paths_result` and its private
  helpers are replaced by the target-aware algorithm. Its signature, its
  callers in `services/learning_progressions.py`, `path_id_bound`, the
  size-reservation and byte-stop logic, and the result model are kept.
- **Path request model** (`services/lp_models.py`
  `GetLearningProgressionPathsRequest`): the `max_depth` upper bound becomes
  16.

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
  - `backend/src/`, except `services/lp_paths.py` (the algorithm
    replacement) and the single `max_depth` bound of
    `GetLearningProgressionPathsRequest` in `services/lp_models.py`. The
    traversal request (`max_depth` ≤ 12, default 8), its distance model, the
    path default (6), `max_paths` (≤ 20), and the 5,000 budgets stay as they
    are. So do `path_notice` and every other notice text, because their
    statements remain true.
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
- If implementation finds that any further backend change is unavoidable,
  stop and route an `ARCHITECTURE` failure. Do not add a framework-specific
  branch or relax a rule.

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
- In the default offline suite, CAPS gets a small, deterministic sample of
  connected buildsTowards pairs, pinned from the accepted package. The goal
  is evidence that CAPS path search works, not full enumeration (user
  guidance, 2026-10-14).
  - The sample includes a direct pair, a pair of 8 hops or fewer, at least
    one 9–12 hop pair (for example, the 11-hop pair `DEV-006` measured), and
    at least one 13-hop pair.
  - Each pair is requested at `max_depth` equal to its shortest length and
    at 16. Each must satisfy the `AC-025` criterion below.
- `AC-025` also needs evidence over all 43,145 CAPS pairs. Tester chooses how
  to get it. Options include a separately marked exhaustive test or a
  recorded one-off run. The default suite must stay practical either way.
- `AC-024` needs a differential check:
  - The oracle is a test-only reference copy of the cycle-baseline
    breadth-first enumerator (`services/lp_paths.py` at `f9fdaa2`).
  - Run it against deterministic request samples on all seven packages:
    `max_depth` 1–12, `max_paths` 1–20, connected and unconnected pairs.
  - Wherever the oracle returns empty `truncation_reasons`, the new search
    must return the same `paths`, `relationships`, and `nodes`, in the same
    order, and empty `truncation_reasons`.
- `AC-023` needs bound checks: `max_depth` 16 is accepted, 17 and 0 are
  rejected the same way as other out-of-range values, and the default is 6.
  The tool's published input schema shows maximum 16.
- `AC-026`: every path result produced by any of these checks satisfies the
  **Result invariants**.
- The rights-flag assertions over all packages then cover CAPS without
  further change.
- No test calls a live or paid LLM service.

### Target-aware path search

This section replaces the per-request search in `paths_result`. Inputs,
endpoint resolution, the same-endpoint error, and the result model stay as
they are. `max_depth` may now be up to 16.

**Backward pass**

- Starting from the target, walk the package's upstream buildsTowards
  adjacency to collect every node that can reach the target.
- For each such node *n*, compute:
  - `lengths[n]`: the set of exact hop counts *h* ≤ `max_depth` for which a
    path of exactly *h* hops from *n* to the target exists. A bitmask is
    sufficient.
  - `longest[n]`: the longest hop count from *n* to the target, with no
    `max_depth` cap.
- Validated acyclicity makes both computations well defined. Compute them
  without unbounded recursion, for example in topological order.
- Every adjacency entry inspected in this pass counts toward the existing
  5,000 inspection budget (`examined_relationship_count`, `work_limit`).

**Forward enumeration**

- For each *k* from 1 to `max_depth` in ascending order, skipping any *k*
  not in `lengths[source]`, search depth-first from the source.
- Visit each node's downstream edges in the existing sorted
  (`relationship_id`) order.
- Extend a partial path of length *ℓ* along an edge to node *m* only when
  *k − ℓ − 1* is in `lengths[m]`.
- Admit each completed path of length *k* in the order it is found. This is
  the existing order: hop count, then relationship-ID tuple.
- Every created partial path, including the initial source state, counts
  toward the existing 5,000-state budget (`enqueued_state_count`,
  `queue_limit`). Every inspected edge counts toward the inspection budget.
- Admission, byte stops, `nextUnreturnedPath`, and the size reservation keep
  their existing behavior, through `_admit_path`, `_stop_on_size`, and
  `_require_size`.

**Truncation reasons** (`graph_exhausted` and `scope_complete` keep their
existing formulas)

- `work_limit` and `queue_limit`: one of the fixed 5,000 budgets above was
  reached.
- `path_limit`: `max_paths` paths were admitted and at least one further
  path within `max_depth` exists. This is now exact; the baseline reported
  it whenever its queue was non-empty.
- `depth_limit`: `longest[source]` > `max_depth`, meaning a connection longer
  than the requested depth exists. A source that cannot reach the target
  reports no `depth_limit`.
- `byte_limit`: unchanged.

**Counters and frontier.** These keep their field names and bounds. They
report the new search's effort, so they may differ from the baseline on any
request.

- `examined_relationship_count`: inspections in both passes.
- `enqueued_state_count`: partial paths created, source state included.
- `peak_queue_state_count`: the most partial paths alive at once, at least 1.
- `frontier.queued_state_count`: partial paths still alive when the search
  stopped; 0 when it finished.
- `frontier.pending_adjacency_count`: edges not yet inspected at the node
  being expanded when the search stopped; 0 when it finished.
- `depth_frontier_examined_relationship_count` and
  `frontier.depth_limited_extension_count`: inspected edges rejected because
  their head reaches the target only in more hops than remain.

**Compatibility contract** (`AC-022`, `AC-024`)

Suppose the baseline returns empty `truncation_reasons` for a request.
- Then no simple path from the source exceeds `max_depth`. If it did, the
  baseline would have reported `depth_limit`.
- The baseline also returned every path to the target within `max_depth`,
  in the shared order.
- So the new search finds exactly the same paths, in the same order, with
  the same `nodes` and `relationships` tables, and with empty
  `truncation_reasons`.

Only the counters and frontier counts may differ. Their exact values were
never part of the "same results" promise: they describe search effort, and
the user accepted on 2026-10-14 that they shrink. Requests the baseline
truncated may now return more or complete paths, no paths with
`graph_exhausted: true`, or different reasons. `AC-022` allows that.

**Result invariants** (`AC-026`)

- Every returned path runs from the source to the target over stored
  buildsTowards edges.
- Its hop count is at most `max_depth`. Its `node_ids` length is its
  `relationship_ids` length plus 1.
- The `relationships` table equals the union of the returned paths' edges.
- Paths are distinct and in the stated order.
- Any result that misses a path within `max_depth`, whether by budget, by
  `max_paths`, or by size, reports a non-empty `truncation_reasons`.

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
  disclosure text as the other frameworks.
- `AC-014`:
  - `packaging/mcpb/manifest.json` `version` equals `backend/pyproject.toml`
    `version` (`1.0.0`).
  - `kgfegmcp-build-mcpb` produces a fresh stage that contains the CAPS
    package, profile, and overlay.
  - `kgfegmcp-stdio-smoke --bundle-root <stage>` passes.
- `AC-015`: `Dockerfile` and `.dockerignore` are unchanged, and the build
  context includes the CAPS package, profile, and overlay paths.
- `AC-022`:
  - `git diff f9fdaa2 --` over the six packages, profiles, overlays, and
    input sets is empty, and their snapshot IDs are unchanged.
  - Outside the CAPS additions and `.standards/`, the tracked changes are
    limited to the **Change boundary** exceptions: the path-search files, the
    one-field `packaging/mcpb/manifest.json` correction, and test updates.
  - Non-path tools serve the same results as the baseline. Path results
    satisfy the **Compatibility contract**.
- `AC-017`: The public surface counts are unchanged: 19 tools, 1 fixed
  resource, 14 resource templates, and 9 prompts.
- `AC-018`: Under `backend/src/`, the cycle's diff touches only
  `services/lp_paths.py` and the `max_depth` bound in
  `services/lp_models.py`. No CAPS framework ID, snapshot ID, or input-set
  name appears in any generic source file. No validation rule changes.
- `AC-019`: The full offline suite passes under the **Test-corpus contract**
  above.
- `AC-023`: `max_depth` is accepted from 1 to 16, out-of-range values are
  rejected through the existing validation error path, the default is 6, and
  the published tool input schema reflects this.
- `AC-024`: The differential check in **Test-corpus contract** finds no
  difference on any baseline request with empty `truncation_reasons`.
- `AC-025`: For each of the 43,145 connected CAPS pairs, requested with the
  default `max_paths`:
  - at `max_depth` equal to its shortest length, and at 16, the first
    returned path has exactly the oracle's shortest hop count and satisfies
    the **Result invariants**;
  - `truncation_reasons` contains none of `work_limit`, `queue_limit`, or
    `byte_limit`.

  `path_limit` and `depth_limit` may appear, because they describe further
  or longer paths beyond the request, not the returned shortest path.
- `AC-026`: Every path result in the checks above satisfies the **Result
  invariants**.
- `AC-027`: No architectural impact (Documenter). The facts to document are
  the 1–16 range, the default of 6, and target-aware behavior: long
  connections are found within the fixed budgets, and `depth_limit` and
  `path_limit` keep their exact meanings.

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
5. Replace the path-search algorithm and raise the request bound. Then
   update corpus-dependent test expectations, add the CAPS baseline entry,
   and add the path-search checks. Run the full offline suite.
   (`AC-017`..`AC-019`, `AC-022`..`AC-026`)
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
- **`AC-025` "without truncation".** An empty `truncation_reasons` cannot
  be required for every pair. `path_limit` or `depth_limit` legitimately
  appears whenever more paths exist than requested, or a longer connection
  exists. The technical criterion therefore forbids only budget and size
  stops. If Scoper meant an empty reason list, that is unattainable for any
  algorithm, and the question goes back to Scoper.
- **Counter values change.** Clients or tests that pin path counters or
  frontier counts will see smaller numbers. The tests that pin them are
  updated under the **Test-corpus contract**.
- **Reliance on acyclicity.** The exact-length search is correct only
  because validation rejects buildsTowards cycles. If that rule is ever
  relaxed, path search must be redesigned.
- **Larger graphs.** The backward pass costs up to one inspection per
  ancestor edge. A future package whose ancestor sets approach 5,000 edges
  would hit `work_limit` and report it honestly. CAPS peaks at 1,126.

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
- **Target-distance pruning of the existing breadth-first search.**
  Rejected. With depth headroom, breadth-first search still holds every
  detour prefix of length *k−1* before completing any path of length *k*,
  so the fixed budgets fill on long CAPS pairs.
- **Raising the 5,000 budgets.** Rejected by scope. It would also only delay
  the blow-up, and it would raise the worst-case cost per request for every
  framework.
- **Not charging the backward pass to the budget.** Rejected. Charging it
  keeps the budget an honest bound on all per-request work, and measured
  worst-case use stays well under 5,000.
