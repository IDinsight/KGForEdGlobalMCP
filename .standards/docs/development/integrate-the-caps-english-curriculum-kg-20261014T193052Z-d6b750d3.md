<!-- STANDARDS
Artifact: DEVELOPMENT
Cycle: integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3
-->

# Development Plan

`Cycle`: `integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3` `Mode`: `STEPWISE`
`User Style`: `tony` `User Style Locked`: `true`
`Status`: `IN_PROGRESS` `Verification Cadence`:
`AFTER_IMPLEMENTATION` `Current Increment`: `NONE`

## Implementation Contract

- `Scope`: `.standards/docs/scope/integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3.md`
- `Architecture`: `.standards/docs/specs/integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3.md`
- `Request`: Integrate the CAPS English Home Language (Grades R-3) KG export as a seventh framework, using data and configuration. Also make generic Learning Progression path search target-aware and raise its `max_depth` ceiling to 16, correct the MCPB manifest version, and return path, standard-progression, LP-search, and traversal results in a compact shared-place form, with an IDs-only fallback for paths that still do not fit (scope replans and design revisions, 2026-10-14 and 2026-10-15).

## Build Steps

### DEV-001 — Verified local copy of the CAPS source

`Status`: `DONE` `Depends On`: `NONE`
`Acceptance`: `AC-001`

**Goal**

Copy the documented 23-file copy set from the external CAPS `kgs/` directory into the repository's git-ignored preparation area and write a verified copy receipt, without touching the external export.

**Affected Area**

- `data/source_artifacts/learning_progressions/c939a3a9dcce92ed61d970f4599ced6f2ddc425d1220eeeab9828472b878d24d/kgs/` (23 files, git-ignored)
- `data/source_artifacts/learning_progressions/copy_receipt.json` (git-ignored)
- A one-off operator script in the session scratchpad, not committed (the design keeps receipt authoring out of the codebase).

**Expected Outcome**

- A manifest (relative path, size, SHA-256) of the external `kgs/` directory taken before the copy equals one taken after it.
- The 23 copied files exist locally. For each one, source-before, source-after, and destination SHA-256 are equal and sizes match.
- `copy_receipt.json` has `receiptVersion` `1.0`, `status` `verified`, `selectedFileCount` 23, one `frameworks` entry (document key, CASE UUID `7bb16abe-6d0a-5bb9-9a01-aeb7c4baeaa3`, framework ID `south-africa-dbe-caps-english-home-language-grades-r-3`, destination), and 23 verified `files` entries.

**Self-Check**

- Validate the receipt with `packages/normalization_models.py` `CopyReceipt` through the backend environment.
- Diff the before and after external manifests (expect empty).
- Confirm `git status` shows nothing new under `data/source_artifacts/`.

Evidence (2026-10-14, repository root, tree at `d48627f` plus this cycle's uncommitted `.standards/` edits):

- `python3 -I <scratchpad>/copy_caps_source.py` printed `{"copiedFiles": 23, "externalFiles": 73, "externalUnchanged": true, "receipt": "data/source_artifacts/learning_progressions/copy_receipt.json"}`. The script hashes the whole external `kgs/` tree (73 files), copies each copy-set file with `shutil.copyfile`, re-hashes source and destination, and refuses to overwrite an existing copy or receipt.
- `UV_OFFLINE=1 uv --directory backend run --locked --offline --no-sync python -` loaded the receipt with `CopyReceipt.model_validate`, passed `normalization._validate_selection(framework_id=<framework-id>)`, and passed `normalization_sources.checked_copy_files` (the prepare command's own per-file hash/size/coverage check): `receipt valid; checked files: 23 selected: 23`.
- The before and after manifests are saved at `data/source_artifacts/learning_progressions/external_manifests/<doc-key>-{before,after}.json` (git-ignored, 73 entries each) and compare equal.
- `git status --porcelain --untracked-files=all data/` printed nothing; `data/source_artifacts/` is ignored by `/data/source_artifacts/` in `.gitignore`.

**Implementation Notes**

- The receipt keeps two extra fields the strict models ignore: per-file `sourcePath` (the private external path, as the onboarding doc allows) and per-framework `profileId`/`profileVersion`.
- Rerunning the script stops if the local copy or receipt already exists. Delete both deliberately before recopying.
- `uv run` must use `--offline --no-sync` here. A synced run tries to reach pypi.org, which the sandbox blocks.

---

### DEV-002 — CAPS interpretation profile

`Status`: `DONE` `Depends On`: `NONE`
`Acceptance`: `AC-007, AC-008, AC-009, AC-010`

**Goal**

Author the CAPS profile exactly as the design's **Interpretation profile** contract fixes it, transforming the upstream `kg_run.json` `extra.as` policy field by field (read-only from the external export) and copying shared fields from the existing profiles.

**Affected Area**

`config/profiles/south-africa-dbe-caps-english-home-language-grades-r-3/2.0/profile.json` (new).

**Expected Outcome**

- Profile ID and `frameworkIds` equal the fixed framework ID; schema `1.1`, version `2.0`.
- Grade mappings `Grade R`→`K`, `Grade 1`→`1`, `Grade 2`→`2`, `Grade 3`→`3`, with upstream aliases and no alias-key collisions.
- Five statement types (Grade, Term, Skill Area, Sub-strand, Skill) with upstream wording, controlled values, allowed parents, and identity scopes; strict-tree hierarchy rooted at Grade.
- `codeSearchPolicy` identical to Nigeria's (`availability: none`).
- The two `knownSourceAnomalies` entries with the design's disclosure text.
- Rights `provisional_operator_approved`, derivatives allowed, full text allowed, bulk not allowed, standard resources allowed, `sourceLicense` `Unknown`, attribution identical to the source root string.
- Formatting matches existing profiles: sorted keys, tab indentation, UTF-8, single trailing newline.

**Self-Check**

- Load the profile with the existing profile loader and models (schema validity, alias collisions).
- Compare `localSubject`, `sourceLicense`, and `attributionStatement` against the source root node, code point for code point.
- Diff the shared blocks (`requiredDisclosures`, `comparisonDimensions`, `sourceRoleCapabilities`, `subjectVocabulary`, `codeSearchPolicy`) against an existing profile (expect identical).

Evidence (2026-10-14, repository root, `d48627f` plus uncommitted cycle files; profile is 12,301 bytes):

- `python3 -I <scratchpad>/write_caps_profile.py` printed `Wrote config/profiles/south-africa-dbe-caps-english-home-language-grades-r-3/2.0/profile.json (12301 bytes).` Before writing, the script confirmed that its serializer (`json.dumps(..., ensure_ascii=False, indent="\t", sort_keys=True) + "\n"`) reproduces all six existing profiles byte for byte. It also checked grade alias keys (casefolded, whitespace collapsed) for cross-grade collisions and found none.
- `UV_OFFLINE=1 uv --directory backend run --locked --offline --no-sync python -` loaded the profile with `profiles.loader.load_curriculum_profile(profile_id=<framework-id>, profile_root=config/profiles, profile_version="2.0")` with no error. Results:
  - `localSubject`, `rights.sourceLicense`, and `rights.attributionStatement` equal the delivery root node's `academicSubject`, `license`, and `attributionStatement` (`True`, `True`, `True`; the attribution includes "©").
  - Grade mappings are `Grade R`→`K`, `Grade 1`→`1`, `Grade 2`→`2`, `Grade 3`→`3`.
  - All five source item `statementType` values (Grade 4, Term 16, Skill Area 48, Sub-strand 152, Skill 924) are declared.
  - Code availability is `none`. Rights are `provisional_operator_approved` / `allowed` / full text `True` / bulk `False`.
  - `codeSearchPolicy`, `comparisonDimensions`, `requiredDisclosures`, `sourceRoleCapabilities`, and `subjectVocabulary` are identical to Nigeria's.
  - Tab indentation and a single trailing newline are confirmed.
- After decoding each item's JSON-encoded `gradeLevel` list, as the package decoder does, the grades are `K` 385, `1` 237, `2` 262, `3` 260 (1,144 items), all in the profile's normalized grades. A first check without decoding wrongly printed "all mapped: False". That was the check's bug, not the profile's.
- `git status` lists only the new profile under `config/`, `data/`, and `backend/`.

**Implementation Notes**

- Statement types, controlled values, allowed parents, identity scopes, the hierarchy order, grade aliases, and the language note are copied verbatim from external `kg_run.json` `extra.as`. Grade aliases are the upstream Grade controlled-value aliases. Like upstream, they leave out the canonical label, which is the mapping's `localLabel`.
- Anomaly `requiredDisclosure` strings are the design's exact text. The two `description` strings are Developer wording within the design's stated meaning.

---

### DEV-003 — CAPS prompt overlay

`Status`: `DONE` `Depends On`: `DEV-002`
`Acceptance`: `AC-012`

**Goal**

Add a framework-local prompt overlay adapted from the Ghana English overlay to CAPS terminology, with the same shape and guidance keys.

**Affected Area**

`config/prompts/south-africa-dbe-caps-english-home-language-grades-r-3/2.0/prompts.json` (new).

**Expected Outcome**

- `promptConfigId` `<framework-id>-guidance`, schema `1.1`, version `2.0.0`, `mode: append` guidance for `studentHandbookSection`, `studentStudySupport`, and `teacherGuideDraft`.
- Content uses Grade R and Grades 1-3, Terms 1-4, the four skill areas, and Home Language. It labels any example as generated, makes no source assertions, and states no pedagogical judgments about CAPS content.
- File is at or below 64 KiB and formatted like the existing overlays.

**Self-Check**

- Load the overlay through the existing prompt-config loader and confirm it resolves against the CAPS profile identity and version.
- Check byte size ≤ 65,536.

Evidence (2026-10-14, repository root, `d48627f` plus uncommitted cycle files; overlay is 19,470 bytes):

- `python3 -I <scratchpad>/write_caps_prompts.py` printed `Wrote config/prompts/south-africa-dbe-caps-english-home-language-grades-r-3/2.0/prompts.json (19470 bytes).` Before writing, the script confirmed that its serializer reproduces all six existing overlays byte for byte.
- `UV_OFFLINE=1 uv --directory backend run --locked --offline --no-sync python -` loaded the CAPS profile, then ran the same per-profile path as `PromptConfigRepository.load_registry`: `_verify_optional_components` returned `True`, and `_read_configuration(max_file_bytes=MAX_PROMPT_CONFIG_BYTES, profile=<CAPS profile>, ...)` returned a `LoadedPromptConfig`. Schema validation, the size limit, and the profile/framework identity checks all passed. Config `south-africa-dbe-caps-english-home-language-grades-r-3-guidance` `2.0.0` resolves to profile `south-africa-dbe-caps-english-home-language-grades-r-3` `2.0`.
- The guidance groups and keys match Ghana English's exactly, all in `mode: append`. The overlay has 81 instructions; the longest is 359 characters, under the 1,000-character limit. A scan found no leftover Ghana terms ("Ghana", "BASIC", "NaCCA", "Indicator", "second language").
- `git status` under `config/`, `data/`, and `backend/` lists only the new CAPS profile and overlay.
- Not checked here: rendered prompt size against `MAX_RENDERED_PROMPT_BYTES` (64 KiB). That needs a loaded CAPS package and retrieved evidence, so it runs with the STDIO checks in DEV-006. The overlay is a similar size to Ghana English's (19,629 bytes).

**Implementation Notes**

- The overlay names the five Skill Area labels as the source and profile use them (Listening and Speaking (Oral), Emergent Reading, Emergent Writing, Reading and Phonics, Writing). The design's shorthand "Emergent Reading and Writing" refers to the two separate source labels.
- Guidance that would assert facts about CAPS content, such as Ghana's "five books per term" expectation, assessment taxonomy, and second-language framing, was dropped rather than adapted. Timing, routines, and activity formats are explicitly labelled as generated unless retrieved evidence states them.

---

### DEV-004 — Prepared CAPS input set and build spec

`Status`: `DONE` `Depends On`: `DEV-001`
`Acceptance`: `AC-002, AC-003, AC-005`

**Goal**

Normalize the verified local copy with the existing prepare command, move the prepared output unchanged into a new input set, and author its `package_build.json` from the Nigeria template.

**Affected Area**

- `data/source_artifacts/learning_progressions/prepared/<framework-id>/` (git-ignored, transient)
- `data/input_artifacts/south_africa_english/` (new): `package_build.json` and 9 small `detailed/` files committed; `delivery/`, `additional/` (64 shards), and 11 archive-only `detailed/` files git-ignored.

**Expected Outcome**

- `kgfegmcp-prepare-learning-progressions --framework-id <framework-id>` reports `created`.
- `package_build.json` differs from Nigeria's only in the fields the design lists: input-set paths, `as_lc_lp_{nodes,relationships}_<framework-id>.jsonl` names, `profileId`, `versionToken` `2011`, `jurisdictionType` `country`, `sourcePublicationDate` `null`. All 64 shard entries present, no `sourceDocument`, `outputRoot` unchanged.
- Delivery records decode to 1 / 1,144 / 912 nodes and 1,144 / 1,204 / 2,879 / 6,708 relationships.

**Self-Check**

- Prepare command output and hashes.
- `git check-ignore` on every archive-only path; `git status` lists only `package_build.json` and the 9 small `detailed/` files as new.
- Count delivery node labels and relationship types with a short read-only script.
- Diff the spec against Nigeria's (only the listed fields change).

Evidence (2026-10-14, repository root, `d48627f` plus uncommitted cycle files):

- `UV_OFFLINE=1 uv --directory backend run --locked --offline --no-sync kgfegmcp-prepare-learning-progressions --framework-id south-africa-dbe-caps-english-home-language-grades-r-3` exited 0 in about 11 s. It reported `outcome: created`, `buildsTowardsRelationships: 2879`, `relatesToRelationships: 6708`, and 86 file hashes. The full JSON output is saved at `data/source_artifacts/learning_progressions/prepare_output_south-africa-dbe-caps-english-home-language-grades-r-3.json` (git-ignored).
- `delivery/`, `detailed/` (20 files), and `additional/` (64 shards) were moved with `mv` from `prepared/<framework-id>/` into the new `data/input_artifacts/south_africa_english/`; the emptied prepared directory was removed. All 86 files re-hashed after the move match the prepare output (0 mismatches).
- `package_build.json` (9,765 bytes) was generated from the Nigeria spec. The generator first confirmed that `json.dumps(..., indent=2, sort_keys=True) + "\n"` reproduces the template byte for byte.
  - Fields that differ from Nigeria: `additionalArtifacts`, `detailedArtifactsDirectory`, `nodes`, `profileId`, `relationships`, `versionToken`. `jurisdictionType` (`country`) and `sourcePublicationDate` (`null`) already had the design's values.
  - All 64 shard entries are identical to Nigeria's apart from the set name. `outputRoot` is unchanged, there is no `sourceDocument`, and every referenced input file exists.
- `git status --porcelain --untracked-files=all -- data config backend` lists only the CAPS profile, the CAPS overlay, `package_build.json`, and the 9 small `detailed/` files (372 KiB together).
- `git check-ignore --no-index --verbose --non-matching --stdin` matched all 77 archive-only paths (2 delivery, 64 shards, 11 `detailed/`); none were reported as not ignored.
- A read-only count of the delivery files found 1 `StandardsFramework`, 1,144 `StandardsFrameworkItem`, and 912 `LearningComponent` nodes, and `hasChild` 1,144, `supports` 1,204, `buildsTowards` 2,879, `relatesTo` 6,708 relationships (11,935 total). These equal the AC-003 figures.
- The largest input-set files are archive-only and git-ignored: `lp_final_claims.json` 127.2 MB, `lp_relationship_provenance.json` 119.2 MB, `lp_relationships_relates_to.jsonl` 90.6 MB.

---

### DEV-005 — Built, accepted, and installed CAPS package

`Status`: `DONE` `Depends On`: `DEV-002, DEV-003, DEV-004`
`Acceptance`: `AC-002, AC-003, AC-005, AC-006`

**Goal**

Run the documented build → read-only validate → persist → install lifecycle into a fresh git-ignored output root, and move only the terminal `passed` package into `data/graph_packages/`.

**Affected Area**

- A fresh local spec copy and output root under `data/source_artifacts/learning_progressions/` (git-ignored).
- `data/graph_packages/south-africa-dbe-caps-english-home-language-grades-r-3/<snapshot-id>/` (new, committed).

**Expected Outcome**

- Snapshot ID matches `<framework-id>@2011+<12-hex>`; manifest `validation` status `passed`, profile reference `<framework-id>` version `2.0`.
- Manifest counts equal the scope's figures (AC-003).
- Every committed CAPS file ≤ 100 MB; every artifact or evidence read permitted under CAPS rights within `config.py` defaults.
- Every archive-only input is listed in `evidence/evidence_archive_record.json`.

**Self-Check**

- `kgfegmcp-build-manifest --spec <abs local spec> --dry-run`, then the real build.
- `KGFEGMCP_GRAPH_PACKAGES_ROOT=<fresh root> kgfegmcp-validate-packages one … --read-only` (no findings), then without `--read-only` to persist.
- `kgfegmcp-verify-evidence-archive one --framework-id … --snapshot-id …` (all `ok`).
- File-size scan of the package and input set; compare permitted artifact sizes with `max_resource_bytes` and `max_resource_source_bytes`.

Evidence (2026-10-14, repository root, `d48627f` plus uncommitted cycle files; all commands use `UV_OFFLINE=1 uv --directory backend run --locked --offline --no-sync`; raw outputs are saved under the git-ignored `data/source_artifacts/learning_progressions/operator-build-caps/`):

- **Local spec.** `caps-build.json` is `data/input_artifacts/south_africa_english/package_build.json` with only `outputRoot` set to the fresh, previously absent `operator-build-caps/packages`. It was written by the documented "Rebuild and accept separately" snippet, which refuses existing paths.
- **Dry run.** `kgfegmcp-build-manifest --spec <abs>/caps-build.json --dry-run` exited 0 with `outcome: dry_run` (`dry-run.out`).
- **Build.** The same command without `--dry-run` exited 0 with `outcome: created` (`build.out`).
  - Package: 80 files, 86,880,508 bytes. That is the same file count as the Nigeria package.
  - Snapshot ID: `south-africa-dbe-caps-english-home-language-grades-r-3@2011+95ab377d1619`.
  - Graph package ID: `…@2011+95ab377d1619--academic-standards--p1`.
  - Profile reference: `<framework-id>` version `2.0`, sha256 `8ced6a29…331a`.
- **Read-only validation.** `KGFEGMCP_GRAPH_PACKAGES_ROOT=<abs>/operator-build-caps/packages kgfegmcp-validate-packages one --framework-id <id> --snapshot-id <snapshot> --read-only` exited 0 in about 15 s: `isValid: true`, `findings: []`, `observedStatus: pending`, `targetStatus: passed`, `persisted: false` (`validate-readonly.out`). This is full validation: `--runtime-only` was not passed, so the archive evidence tier ran.
- **Acceptance.** The same command without `--read-only` exited 0: `effectiveStatus: passed`, `persisted: true`, `findings: []`, `validatedAt: 2026-10-14T20:37:04Z` (`validate-accept.out`).
- **Install.** The accepted snapshot directory was moved with `mv` to `data/graph_packages/south-africa-dbe-caps-english-home-language-grades-r-3/south-africa-dbe-caps-english-home-language-grades-r-3@2011+95ab377d1619/`, and the emptied build root was removed. This is the only CAPS snapshot.
- **Archive check (installed root).** `kgfegmcp-verify-evidence-archive one --framework-id <id> --snapshot-id <snapshot>` exited 0: `status: ok`, `ok: 86`, `missing: 0`, `mismatch: 0` (`verify-archive.out`).
- **Full revalidation (installed root).** `kgfegmcp-validate-packages one … --read-only` exited 0: `observedStatus: passed`, `effectiveStatus: passed`, `terminalRevalidation: true`, `findings: []` (`validate-installed.out`).
- **Manifest.** `validation.status: passed`. Counts: framework 1, items 1,144, Learning Components 912, relationships 11,935, supports 1,204, buildsTowards 2,879, relatesTo 6,708; `codedItems: 0`, `unresolvedRelationships: 0`, `multiParentTargets: 0`. The relationship count is the total of all four types, including the 1,144 hasChild edges that DEV-004 counted in the delivery file. These equal AC-003 with no normalization difference. The served framework metadata shows `jurisdiction` South Africa, `jurisdictionType` country, `issuingAuthority` Department of Basic Education, `localSubject` English Home Language, and `localGradesOrStages` `["Grade R","Grade 1","Grade 2","Grade 3"]`. Rights equal the profile. Capabilities include `codeSearch: none` and `multiParent: false`.
- **Sizes.**
  - No package file exceeds 100 MB. The largest is the delivery relationships file at 15.7 MB (14.94 MiB), then delivery nodes at 1.8 MB.
  - Every non-delivery file is ≤ 8 MiB; the largest is `slim/as_entity_provenance.json` at 1.64 MiB. The 64 slim shards range from 0.86 to 1.23 MB.
  - So every metadata, full-text, or slim-evidence artifact is within both the `max_resource_bytes` (8 MiB) and `max_resource_source_bytes` (32 MiB) defaults in `config.py`, whatever its exposure class.
  - The two delivery files are ≤ 32 MiB source bytes. The relationships file is larger than 8 MiB, but delivery files are bulk content that CAPS rights deny (`allowBulkResource: false`), the same as for the six existing packages.
  - The largest committed input-set file is a small `detailed/` file; the committed set totals 372 KiB.
  - `data/graph_packages/` is now 164 MB on disk, up from about 81 MB.
- **Archive record.** `evidence/evidence_archive_record.json` has 86 `evidenceArtifacts` entries. All 77 git-ignored archive-only input paths from DEV-004 are present, with none missing.
- **Git.** `git status` shows all 80 package files as untracked (to commit). `git ls-files --others --ignored --exclude-standard -- data/graph_packages` lists none, so nothing in the package is ignored.

**Implementation Notes**

- The evidence-archive verifier and validator read the installed root; both were run against `data/graph_packages/` after the move as well.
- That the server denies the delivery files at runtime is rights behaviour for Tester to verify. The size check above does not depend on it for any non-delivery artifact.

---

### DEV-006 — CAPS served through the repository server and distributions

`Status`: `PENDING` `Depends On`: `DEV-005, DEV-008, DEV-009, DEV-011, DEV-012`
`Acceptance`: `AC-011, AC-012, AC-013, AC-014, AC-015, AC-017, AC-018, AC-019, AC-036`

**Goal**

Confirm that the generic runtime, MCPB stage, and Docker context pick up CAPS with the corrected path search and MCPB manifest in place, and that the change set stays inside the revised design's **Change boundary**. If any further backend change turns out to be needed, stop and route an `ARCHITECTURE` failure.

**Affected Area**

No new repository files expected. Checks run against the repository server, a fresh MCPB stage and bundle written to the git-ignored `data/source_artifacts/learning_progressions/dev006/` (so the user's `dist/` is untouched), and the Docker build context.

**Expected Outcome**

- Catalog lists 7 frameworks with CAPS statistics equal to its manifest counts.
- A real STDIO session (scratch client, no LLM) can retrieve, search, and get context for CAPS standards and Learning Components, and look up, search, and traverse CAPS LPs with the generic disclosures.
- `kgfegmcp-build-mcpb` succeeds; the fresh stage contains the CAPS package, profile, and overlay; `kgfegmcp-stdio-smoke --bundle-root <stage>` passes.
- Docker context includes the CAPS paths with `Dockerfile` and `.dockerignore` unchanged.
- `git diff f9fdaa2` shows, outside the CAPS additions and `.standards/`, only the design's **Change boundary** exceptions: `services/lp_paths.py`, `services/lp_discovery.py`, `services/lp_traversal.py`, the new compact helper, the permitted `services/lp_models.py` changes, the path tool description, and the `version` field of `packaging/mcpb/manifest.json` (plus any Tester test updates). Tools other than the four compacted ones serve byte-identical results. Nothing changes under `Dockerfile`, `.dockerignore`, `.gitignore`, release-please files, `CHANGELOG.md`, the project version, or any existing package, profile, overlay, or input set.

**Self-Check**

- `kgfegmcp-stdio-smoke`, the scratch STDIO session (including the previously truncated 11-hop CAPS pair), `kgfegmcp-build-mcpb --mcpb-command $(which mcpb) --output <dev006>/… --stage-output <dev006>/mcpb-stage`, and `kgfegmcp-stdio-smoke --bundle-root <dev006>/mcpb-stage`.
- Docker context inspection against the `.dockerignore` allowlist (no image build required).
- Full offline suite. The corpus-dependent assertions listed in CONTEXT.md, and any test pinning baseline path counters or frontier counts, are expected to fail until Tester applies the design's **Test-corpus contract**; any other failure is a defect.
- Boundary `git diff --stat` and a grep for the CAPS framework ID under `backend/src/`.

Evidence from the first, suspended run (pre-replan; kept as history, superseded by the rerun after DEV-008 and DEV-009) (2026-10-14, repository root, `d48627f` plus uncommitted cycle files; raw outputs are in the git-ignored `data/source_artifacts/learning_progressions/dev006/`). The step is **not done**: it is suspended by the ARCHITECTURE failure recorded in Plan Notes (Suspended Assignment 1).

- **Repository STDIO smoke: passed.** Command: `UV_OFFLINE=1 uv --directory backend run --locked --offline --no-sync --no-dev kgfegmcp-stdio-smoke`, exit 0 (`stdio-smoke.out`). Results:
  - `status: passed`, `accepted_package_count=7`, 19 tools, 1 fixed resource, 14 resource templates, 9 prompts, 15 resource reads, 7 LP snapshots discovered.
  - The WARNING lines in `stdio-smoke.err` are the smoke's own deliberate error-path checks (`learning_progression_not_found`, `invalid_evidence_uri`, `resource_access_denied`, and a duplicate `relationshipTypes` argument).
  - Limitation: inside the sandbox it failed with `failed to open file ~/.cache/uv/sdists-v9/.git: Operation not permitted`. The smoke's subprocess environment passes only the `KGFEGMCP_*` settings, so the child `uv` falls back to `~/.cache/uv`. It passed when rerun outside the sandbox.
- **Scratch CAPS STDIO session: passed.** Command: `backend/.venv/bin/python -I <scratchpad>/caps_stdio_session.py <repo>` (`caps-session.json`). It uses a real STDIO subprocess (`python -m kgfegmcp.mcpb_server`, same environment as the smoke) and no LLM. Results:
  - `list_frameworks` lists 7 frameworks including CAPS.
  - `get_framework` `sourceMetadata` shows the root name, South Africa / `country`, Department of Basic Education, English Home Language, and `["Grade R","Grade 1","Grade 2","Grade 3"]`. Package `counts` equal the manifest. Rights equal the profile.
  - `get_capabilities` reports CAPS standards search modes as text only. `code_exact` and `code_prefix` searches scoped to CAPS return `capability_unavailable` ("Available package search modes: text"), so there are no CAPS code hits.
  - Grade filters: text search for "letters sounds" filtered by `localGradeLabels: ["Grade R"]` and by `normalizedGrades: ["K"]` each returned the same 44 hits (`hasMore: false`), all with facets `normalizedGrades ["K"]` and `resolvedLocalGradeLabels ["Grade R"]`.
  - `get_standard` facets show `nodeGradeLevels ["K"]`, `resolvedLocalGradeLabels ["Grade R"]`, and `statementType Skill`.
  - These calls all returned results: `get_standard_context`, `get_learning_components_for_standard` (1), `get_learning_component`, `get_learning_component_context`, and `search_learning_components` (5 hits).
  - LPs: `get_learning_progression` (edge `aba99f19…`) reports stored counts 2,879 / 6,708. `search_learning_progressions` returned 5 per page. `get_standard_progressions` returned 2. `traverse_learning_progressions` (depth 2) returned 9 relationships and 9 nodes. `get_learning_progression_paths` returned the two-hop path `0016a784… → 2ea5b6a8… → 3b22cd47…`.
  - The generic LP disclosures (`continuationNotice`, `artifactInventoryNotice`, `generatedOriginNotice`, `semanticNotice`, and `epistemicStatus`) are identical to a Ghana English edge's.
  - Resource reads of `framework`, `manifest` (27,220 bytes), `interpretation-profile` (16,404 bytes), `standard`, and `learning-progressions` all succeeded. `artifact/nodes` (delivery, bulk) was denied with `resource_access_denied`, as CAPS rights require.
  - Rendered prompts are 32,974 bytes for `student_handbook_section` (Grade R), 34,535 for `teacher_guide_draft` (Grade 2), and 27,786 for `learning_progression_teaching_sequence`. All are under the 64 KiB `MAX_RENDERED_PROMPT_BYTES`, and all contain the CAPS overlay terms. `get_workflow_instructions student_study_support` (Grade 1) succeeded.
- **Docker context: passed.** `Dockerfile` and `.dockerignore` are unchanged from `HEAD`. Simulating the `.dockerignore` allowlist rules over the paths includes all 82 CAPS runtime files (80 package files, the profile, and the overlay) and excludes the input set. No image was built, as the plan specifies.
- **Change boundary: passed.**
  - `git diff --stat f9fdaa2 -- . ':!.standards'` is empty for tracked files.
  - `git status` shows nothing under `backend/src`, `Dockerfile`, `.dockerignore`, `.gitignore`, `packaging`, or any existing package, profile, overlay, or input set.
  - The only new paths are the CAPS profile, the overlay, 80 package files, and 10 committed input-set files.
  - The CAPS framework ID and input-set name appear nowhere under `backend/src/`. The only `caps` match is the English word "caps" in a docstring in unchanged `prompts/learning_progressions.py`.
  - Each framework directory holds exactly one snapshot.
- **MCPB stage: blocked; this is the reason for the failure route.**
  - Command: `kgfegmcp-build-mcpb --mcpb-command $(which mcpb) --output <dev006>/kgfegmcp-caps-check.mcpb --stage-output <dev006>/mcpb-stage`. Output was written to `dev006/` so the user's existing `dist/kgfegmcp-0.1.0.mcpb` is untouched.
  - It exited 1 with `MCPB build failed: MCPB manifest version must match backend project version exactly.` (`build-mcpb.err`).
  - Cause: `backend/pyproject.toml` has `version = "1.0.0"` from release commit `868eeb1`, which changed `.release-please-manifest.json`, `CHANGELOG.md`, `backend/pyproject.toml`, and `backend/uv.lock`. `packaging/mcpb/manifest.json` still has `"version": "0.4.0"`. `build_mcpb.py` (~L655) requires them to be equal.
  - The mismatch predates this cycle: `git diff HEAD -- packaging backend/pyproject.toml` is empty. The bundle smoke (`--bundle-root`) therefore could not run.
- **Full offline suite: 138 passed, 11 failed.** Command: `UV_OFFLINE=1 uv --directory backend run --locked --offline --no-sync pytest -q -p no:cacheprovider -m 'not costs-money' tests`, about 4.5 min, output in `pytest.out`.
  - Ten failures are the expected six-package assertions CONTEXT.md lists:
    - `test_progression_discovery_text.py:79` (×3, framework-ID lists), `:92`, and `:143`: `7 == 6`.
    - `test_runtime_only_packages.py:201` and `:334`: `7 == 6`.
    - `test_progression_discovery.py:116` and `test_progression_lookup.py:161`: `17667 == 8080`. The 17,667 equals 8,080 plus 9,587 CAPS LP edges, as the design predicts.
    - `test_progression_regressions.py:102`: `KeyError` for the CAPS framework ID.
  - The eleventh failure is **not** a stale count. `test_progression_algorithms.py:332` (`assert len(result.paths) == 1`, giving `0 == 1`): `get_learning_progression_paths` returned no path for the connected CAPS pair `0016a784… → 2ccbf220…` (11 hops) with `truncation_reasons=('queue_limit',)`. The six existing packages passed this check before it reached CAPS.
- **CAPS path-completeness measurement** (`<scratchpad>/caps_paths_scan.py` over STDIO, `caps-paths-scan.txt`):
  - CAPS has 43,145 connected buildsTowards pairs. Compare 6,522 across all six existing packages.
  - Shortest-path lengths by hops: 1: 2,879; 2: 4,966; 3: 6,449; 4: 7,604; 5: 7,609; 6: 5,955; 7: 3,953; 8: 2,234; 9: 1,004; 10: 362; 11: 97; 12: 28; 13: 5. The longest is 13, against 8 for the existing packages.
  - For every connected pair from the first 5 sorted CAPS sources (336 pairs), every pair of 8 hops or fewer returned its complete shortest path. Of the pairs at 9–11 hops, 7 returned no path: 3 with `queue_limit` and 4 with `depth_limit` plus `work_limit`.
  - The server reports this truncation honestly; it does not crash. But the design's assumption that a CAPS sample meets the same complete-shortest-path invariants as the exhaustive check does not hold for long CAPS connections. Up to 1,496 pairs have 9 or more hops.
  - Changing that behaviour would mean changing generic code or the `config.py` limits, both outside the design's change boundary.

---

### DEV-007 — Rebuild determinism evidence

`Status`: `PENDING` `Depends On`: `DEV-005`
`Acceptance`: `AC-004`

**Goal**

Rebuild CAPS from the committed spec and the local input set into a second fresh output root and compare it with the installed package.

**Affected Area**

A second fresh output root under `data/source_artifacts/learning_progressions/` (git-ignored; left in place after the comparison).

**Expected Outcome**

Same snapshot ID, byte-identical package files, and `package_manifest.json` differing only in `createdAt` and validation state.

**Self-Check**

Recursive hash comparison of both package trees, plus a JSON diff of the two manifests.

---

### DEV-008 — Target-aware exact-length path search with `max_depth` ceiling 16

`Status`: `DONE` `Depends On`: `DEV-005`
`Acceptance`: `AC-018, AC-023, AC-024, AC-026, AC-028, AC-036`

**Goal**

Replace the breadth-first enumeration in `paths_result` with the design's exact-length, target-aware search (**Target-aware path search**), including its **Cycle guard**, and raise `GetLearningProgressionPathsRequest.max_depth`'s upper bound from 12 to 16. The change is generic, with no framework-specific branch. Result form (compact tables and the IDs-only fallback) belongs to DEV-012.

**Affected Area**

- `backend/src/kgfegmcp/services/lp_paths.py`: `paths_result` and its private helpers. Kept as they are: the signature, `path_id_bound`, `PathIdBound`, `_admit_path`, `_require_size`, `_stop_on_size`, `_first_path_error`, `_reserved_path`, the result model, and the callers in `services/learning_progressions.py`.
- `backend/src/kgfegmcp/services/lp_models.py`: a module-level path-depth constant `MAX_PATH_DEPTH = 16`. It drives the `GetLearningProgressionPathsRequest.max_depth` upper bound (default stays 6) and the `ProgressionPath` caps: `relationship_ids` at most 16 and `node_ids` at most 17, up from 12 and 13. The traversal request's own bound (`le=12`, default 8) and its distance model are unchanged.
- `backend/src/kgfegmcp/mcp/tools/learning_progressions.py`: the `get_learning_progression_paths` description's maxima text becomes "maxima 16/20", derived from the constant. The traversal tool description is unchanged.

**Expected Outcome**

- **Backward pass.** From the target, using the upstream builds adjacency, compute for each node that can reach the target its exact reachable hop counts ≤ `max_depth` (as a bitmask) and its uncapped longest hop count. Acyclicity is validated, so this is computed without recursion. Every inspected adjacency entry counts toward the fixed 5,000 inspection budget.
- **Forward enumeration.** For each `k` from 1 to `max_depth` that the source can reach in exactly `k` hops, search depth-first in `relationship_id` order. An edge is extended only when its head can still finish in exactly the remaining hops.
  - Output order is unchanged: hop count, then relationship-ID tuple.
  - Every created partial path, including the source state, counts toward the 5,000-state budget.
  - Admission, byte stops, `nextUnreturnedPath`, and the size reservation keep their behavior.
- **Truncation reasons.** `work_limit` and `queue_limit` on the budgets. `path_limit` only when another path within `max_depth` exists. `depth_limit` exactly when the source's uncapped longest connection exceeds `max_depth`. `byte_limit` unchanged. `graph_exhausted` and `scope_complete` keep their formulas. Counters and frontier fields keep their names and report the new search's effort.
- **Cycle guard.** If Kahn settlement leaves any collected node unsettled, the search fails explicitly through an existing service error path and never returns a result.
- **Request bound and path caps.** `max_depth` accepts 1–16, still defaults to 6, and rejects 0 and 17 through the existing validation path. Requests with `max_depth` 13–16 raise no model error from the size reservation. The published schema shows input `max_depth` maximum 16, output `nodeIds` maxItems 17 and `relationshipIds` maxItems 16, and the description reads "maxima 16/20".

**Self-Check**

- `black --check`, `isort --check-only`, `ruff check`, `mypy`, `pylint` (McCabe ≤ 10), and `interrogate` on the changed files, using the repository's configuration.
- The existing progression tests that do not encode the six-package corpus or pin counter values still pass.
- A scratch **differential run** (not a committed test) against a reference copy of the baseline enumerator from `git show f9fdaa2:backend/src/kgfegmcp/services/lp_paths.py`, over deterministic request samples on all seven packages (`max_depth` 1–12, `max_paths` 1–20, connected and unconnected pairs). Wherever the baseline returns empty `truncation_reasons`, the new search must return identical `paths`, `relationships`, and `nodes`, with empty reasons.
- A scratch **all-pairs run** over the 43,145 connected CAPS pairs at `max_depth` equal to the shortest length and at 16, with default `max_paths`. This checks the search, not the envelope: no request may report `work_limit` or `queue_limit`, every returned result must put the oracle's shortest path first and satisfy the **Result invariants**, and peak inspection and state counts are recorded. Envelope outcomes are DEV-012's.
- The **Cycle guard** on a synthetic cyclic adjacency (scratch, not a committed test) raises the chosen service error instead of returning a result.
- The published `get_learning_progression_paths` schema and description, read over STDIO, show input `max_depth` maximum 16 and default 6, output `nodeIds` maxItems 17 and `relationshipIds` maxItems 16, and "maxima 16/20". The traversal tool's schema and description are unchanged.

**Implementation Notes**

Formal tests for AC-023..AC-026 (the differential oracle, CAPS samples, bound checks) are Tester-owned under the **Test-corpus contract**. These scratch runs are Developer feedback only.

Pre-implementation finding (2026-10-15). No code was changed; DEV-008 is suspended (Plan Notes, Suspended Assignment 2). Reading the affected models before coding showed that the design's **Change boundary** omits two required changes:

- `services/lp_models.py` `ProgressionPath` caps `node_ids` at `max_length=13` and `relationship_ids` at `max_length=12`.
  - With `max_depth` 13–16, `_reserved_path` builds a worst-case path of `max_depth` hops for the size reservation. That raises a validation error on every such request before any search runs.
  - Any real 13-hop CAPS path (5 pairs) cannot be represented at all. Results for AC-023 and AC-025 are therefore unreachable.
  - Raising the caps to 17 and 16 changes the published output schema of `get_learning_progression_paths`, because `ProgressionPath` is used for both `paths` and `nextUnreturnedPath`.
- `mcp/tools/learning_progressions.py` (~L228–230): the `get_learning_progression_paths` tool description publishes "Defaults: depth 6, paths 3; maxima 12/20 …". This becomes false at 16.
- Checked and not affected:
  - The traversal bounds (`TraverseLearningProgressionsRequest.max_depth` ≤ 12 and `ProgressionTraversalDistance.depth` ≤ 12) are traversal-only and stay as the design says.
  - `cli/smoke_progressions.py` compares each tool's nested request schema with the live model rather than with pinned values, and only reports `toolSchemaIdentities` hashes. So the smoke follows a bound change without edits.


Implementation and self-check evidence (2026-10-15, repository root, `HEAD d635c6a` plus uncommitted DEV-008 code). Raw outputs and the scratch harnesses are in the git-ignored `data/source_artifacts/learning_progressions/dev008/`. The step is **not done**: AC-025's criterion is unmet for reasons outside the change boundary (Plan Notes, Suspended Assignment 3).

- **Code** (`git diff --stat -- backend`: 3 files, +334/−69). It stays within the widened **Change boundary**:
  - `services/lp_models.py`: `MAX_PATH_DEPTH: Final[int] = 16` drives `GetLearningProgressionPathsRequest.max_depth` (`le=MAX_PATH_DEPTH`, default 6) and the `ProgressionPath` caps (`node_ids` ≤ 17, `relationship_ids` ≤ 16).
  - `mcp/tools/learning_progressions.py`: the path tool description reads `f"…maxima {MAX_PATH_DEPTH}/20…"`.
  - `services/lp_paths.py`: `paths_result` now runs `_target_reach` (an upstream BFS from the target, then Kahn settlement of exact-length bitmasks and uncapped longest and shortest hop counts, with every upstream edge charged to the inspection budget). It then runs `_enumerate`, `_search_length`, and `_extend`: depth-first search per exact length in `relationship_id` order.
  - The new `_has_more` computes exactly whether a further path exists, both for `path_limit` and for the byte stop's `byte_limit`. `_admit_path` and `_stop_on_size` now take `more` instead of testing "queue non-empty". This was found by the differential run (see below).
  - `_expand_state` was removed. `_SEARCH_BUDGET = 5000` replaces the literal 5000s. `PathIdBound`, `path_id_bound`, `_first_path_error`, `_require_size`, `_reserved_path`, `_result` (apart from the constant), and the callers are unchanged.
  - Local choice: the source state counts once toward `enqueued_state_count`, not once per exact length.
- **Static checks** on the three files: `black --check` and `isort --check-only` leave the files unchanged; `ruff check` passed; `mypy` found no issues; `pylint --rcfile=.pylintrc` rated 10.00/10 (the only warning was the sandbox blocking its stats cache in `~/Library/Caches`); `interrogate` passed at 100%. The tracked `interrogate_badge.svg` was regenerated byte-identical.
- **Published schema over STDIO** (`schema_bounds.py`, `schema-bounds.txt`):
  - Path input `maxDepth` has minimum 1, maximum 16, default 6. Output `nodeIds` maxItems is 17 and `relationshipIds` maxItems is 16. The description says "maxima 16/20".
  - The traversal tool is unchanged: `maxDepth` 1–12, default 8, "maxima 12/250/100".
  - Requests with `maxDepth` 17 and 0 are rejected by input validation ("17 is greater than the maximum of 16", "0 is less than the minimum of 1"). A CAPS request at 16 raises no model error from the size reservation.
- **Differential run against the baseline** (`paths_differential.py`, `differential.json`). It loads `git show f9fdaa2:…/lp_paths.py` as a reference module and swaps it into the real service call. It ran 5,127 deterministic requests over all seven packages: up to 600 connected and 200 unconnected pairs each, with `maxDepth` cycling 1–12 and `maxPaths` 1–20.
  - The baseline was untruncated on 3,448 requests (2,197 of them with paths). On all of them the new search returned identical `paths`, `relationships`, and `nodes` with empty reasons: **0 mismatches** after the fix.
  - Before the fix there was 1 mismatch (Nigeria, `maxDepth` 7, `maxPaths` 15). The new search reported `byte_limit` because the depth-first stack is never empty. Fixed with `_has_more`.
- **All-pairs CAPS run** (`caps_all_pairs.py`, `caps-all-pairs.json`, 444 s in-process): each of the 43,145 connected pairs at `max_depth` equal to its shortest length and at 16, with default `max_paths` (3). That is 86,290 requests.
  - No `work_limit` or `queue_limit` at all. Peak use was 1,239 inspections and 26 states, against 5,000 each.
  - 59,244 requests returned with no budget or size stop, the oracle's shortest path first, and every **Result invariant** holding.
  - 26,062 requests returned the shortest path first but report `byte_limit`. The size reservation stopped before the second or third path while one exists.
  - 984 requests, covering **every pair of 10–13 hops (492 pairs)** at both depths, raise `progression_result_too_large`: the first path itself does not fit.
  - Measured on the 11-hop pair `0016a784… → 2ccbf220…`: the one-path result is 115,310 bytes and **115,286 characters**, against `MAX_TOOL_RESULT_CHARACTERS` of 100,000 (the byte limit is 1 MiB).
  - So AC-025's criteria (complete shortest path for every pair; no `byte_limit`) fail on the fixed result envelope and existing size policy, not on the search. Changing either is outside the **Change boundary** and scope's non-goals.
- **Full offline suite on the final code** (`pytest-final.out`): 132 passed, 17 failed. Classification:
  - Expected six-package corpus failures (10, unchanged from DEV-006): `test_progression_discovery_text.py` ×5, `test_runtime_only_packages.py` ×2, `test_progression_lookup.py:161`, `test_progression_discovery.py:116`, `test_progression_regressions.py:102` (`KeyError`).
  - Tests pinning baseline path behaviour that the design changes (5, Tester-owned under the **Test-corpus contract**):
    - `test_progression_acceptance.py:135`: asserts path `max_depth` 13 is rejected; now valid (AC-023).
    - `test_paths_work_boundary` and `test_paths_cumulative_queue_boundary`: their synthetic sources cannot reach target `t`. The new search answers immediately with no work and no truncation, so the budget assertions (5000) no longer apply.
    - `test_paths_depth_boundary` (DIAMOND, `max_depth` 1): `depth_limit` is reported correctly, but `depth_limited_extension_count` is 0 rather than 2, because no length-1 path exists and no edge is inspected. The counter's meaning changed by design.
    - `test_paths_combination_only_bytes`: paths, `byte_limit`, rollback, and `nextUnreturnedPath` assertions passed up to the counter check. `examined_relationship_count` is 8 rather than 4 because the backward pass is now charged.
  - `test_paths_cycle_is_per_path`: a **synthetic cyclic** graph (`a→b→c→a`). The new search returns `[("z",)]` without the `("a","b","d")` path and without truncation. The design's exact-length search is valid only for acyclic graphs, which validation guarantees for accepted packages (**Risks: Reliance on acyclicity**). Flagged for Architect and Tester: this test's premise is outside the new contract.
  - `test_paths_every_real_shortest_connection_fits:322`: the six packages pass. The first long CAPS pair raises `progression_result_too_large`, which is the same envelope limit as above.


Completion evidence (2026-10-15, repository root, `HEAD 2ea9553`, where the DEV-008 search code is committed in `504a8e5`, plus the uncommitted cycle guard in `services/lp_paths.py`). Raw outputs are in `data/source_artifacts/learning_progressions/dev008/`.

- **Cycle guard.** `_target_reach` counts the nodes the Kahn pass settles. If that is fewer than the nodes it collected, it raises `PackageValidationError` (public code `package_validation_error`, the existing error for graph invariant violations) with details `target_node_id` and `unsettled_node_count`, and the message "Stored buildsTowards relationships reaching this target form a directed cycle; path search requires an acyclic graph." It never returns a result in that case.
- **Static checks on `lp_paths.py`.** black: file unchanged. isort: clean. ruff: passed. mypy: no issues. pylint: 10.00/10. interrogate: passed. The tracked `interrogate_badge.svg` is unchanged.
- **Fast path tests** (`pytest … test_progression_algorithms.py -k "paths and not every_real"`, `pytest-paths-cycleguard.out`): 6 passed and 5 failed.
  - Passed: preserved alternative merges, empty-is-success, identical endpoints rejected, the count boundary, the oversized entry rejected, and the later oversized alternative.
  - `test_paths_cycle_is_per_path` now fails with the guard's `PackageValidationError` rather than an incomplete result, which the design intends. Its expectation changes under the **Test-corpus contract**.
  - The other four are the work, queue, depth, and combination-bytes tests already classified above as pinning baseline behaviour.
- **Differential against the baseline** (`differential-cycleguard.json`): 5,127 requests on seven packages; 3,448 compared where the baseline was untruncated (2,197 with paths); **0 mismatches** in `paths`, `relationships`, `nodes`, or empty reasons.
- **All-pairs search check** (`caps_all_pairs_search.py`, `caps-all-pairs-search.json`, 516 s). These are DEV-008's search-only criteria: 43,145 pairs × {shortest depth, 16}, default `max_paths`.
  - No `work_limit` or `queue_limit`. Peak use was 1,239 inspections and 26 states.
  - Every returned result put the oracle's shortest path first and satisfied the **Result invariants**: 0 failures.
  - The envelope outcomes are unchanged and belong to DEV-012: `byte_limit` on 26,062 requests, and `progression_result_too_large` on all 984 requests for the 492 pairs of 10–13 hops.
- **Published schema** (`schema-bounds.txt`, from before the guard; the guard changes no schema): `maxDepth` 1–16 with default 6; `nodeIds` ≤ 17 and `relationshipIds` ≤ 16; "maxima 16/20"; traversal unchanged.
- **Suspended Assignment 3** is resolved by the reconciliation recorded in Plan Notes.

---

### DEV-010 — Compact relationship-evidence models and shared lifting helper

`Status`: `DONE` `Depends On`: `NONE`
`Acceptance`: `AC-032, AC-034`

**Goal**

Add the design's compact form (**Compact Learning Progression results**) as one generic implementation: the compact entry and shared-evidence models, a compact result base, and a single helper that lifts identical liftable fields out of a tuple of full `ProgressionRelationshipEvidence`.

**Affected Area**

- `backend/src/kgfegmcp/services/lp_models.py`: new models.
  - `SharedRelationshipEvidence`: every liftable field optional, `None` omitted on output.
  - The compact relationship entry: the full entry's structure with every liftable field optional and omitted when `None`.
  - The design's **Result type hierarchy**:
    - a common base (`continuation_notice`, `metadata`, `nodes`, no `relationships`);
    - `ProgressionEvidenceResult` extends it with the existing full `relationships` (`GetLearningProgressionResult` stays its only subclass, schema byte-identical);
    - a compact base extends it with compact `relationships` and `shared_relationship_evidence` (always present, `{}` when empty).
    - The three compacted result classes switch to the compact base in DEV-011 and DEV-012, when their builders do.
- Type annotations only: `services/learning_progressions.py` (`progression_result_text`, `require_progression_result_size`, and similar helpers) and `mcp/tools/learning_progressions.py` (`_build_progression_result`) are typed against the common base. Behavior is unchanged.
  - Unchanged: `ProgressionEvidenceResult`, `GetLearningProgressionResult`, `ProgressionRelationshipEvidence`, `GraphRelationship`, and `JudgmentProjection`.
  - Field descriptions state the rehydration rule, so the published schemas carry it. No response notice text is added.
- `backend/src/kgfegmcp/services/lp_compact.py` (new): the lifting helper and the rehydration function, both production code. Lifting applies to a field only when there is at least one relationship and every relationship has the same non-`null` value. The smoke CLI uses rehydration from DEV-011 onward.

**Expected Outcome**

- Liftable fields are exactly the design's: `epistemicStatus`; `judgment.confidenceNotice`; and `relationship.attributionStatement`, `author`, `description`, `label`, `license`, `provider`, `relationshipType`, `sourceEntity`, `sourceEntityKey`, `sourceLabels`, `targetEntity`, `targetEntityKey`, `targetLabels`.
- Every other field stays per entry.
- `canonical_result_text` and `GetLearningProgressionResult` are unchanged.

**Self-Check**

- Static checks (black, isort, ruff, mypy, pylint, interrogate) on the changed files, and `mypy` over the whole package.
- `get_learning_progression`'s published input and output schemas are byte-identical to `HEAD`'s, and the existing suite shows no new failures.
- A scratch round-trip over real evidence from all seven packages: lift, then rehydrate, must equal the full `relationship_evidence` exactly. Cases include a mixed `buildsTowards`/`relatesTo` set (`description`, `label`, and `relationshipType` stay per entry), an empty set (`{}`), and a synthetic set where one liftable value differs or is `null`.

**Implementation Notes**

Pre-implementation finding (2026-10-15). No code was changed; DEV-010 is suspended (Plan Notes, Suspended Assignment 4). Reading the consumers of the progression result models before coding showed two conflicts with the design's **Change boundary**. Neither file is a permitted exception.

- **STDIO smoke would fail (AC-012, AC-014).** `cli/smoke_progressions.py` `_require_edge` (about lines 153–176, called at about line 301 for `get_standard_progressions`, `search_learning_progressions`, `traverse_learning_progressions`, and `get_learning_progression_paths`) requires `expected.relationships[0] not in result.relationships` to be false. Here `expected` is the full `GetLearningProgressionResult` from `get_learning_progression`.
  - Once those four tools emit compact entries, a full `ProgressionRelationshipEvidence` can never equal a compact entry. `kgfegmcp-stdio-smoke` (repository and `--bundle-root`) would then raise "Progression query lost the exact edge or evidence identity."
  - Fixing it means rehydrating, or comparing on identity fields, inside that CLI.
- **Typing of the shared result base.** Both modules are typed against `ProgressionEvidenceResult`, whose `relationships` is `tuple[ProgressionRelationshipEvidence, ...]`, and mypy runs with the `pydantic.mypy` plugin (`pyproject.toml`).
  - `mcp/tools/learning_progressions.py` `_build_progression_result(result: ProgressionEvidenceResult)` handles all five tools.
  - `cli/smoke_progressions.py` has `_RESULT_MODELS: Mapping[str, type[ProgressionEvidenceResult]]` and `_require_edge(result: ProgressionEvidenceResult)`.
  - If the three compacted results stop subclassing `ProgressionEvidenceResult`, both modules fail type checking.
  - If they keep subclassing it with a compact `relationships` type, that is an incompatible override, and the base type misstates their entries. Widening the base field to a union would change `get_learning_progression`'s published output schema, which AC-036 forbids.
  - A clean base needs those annotations updated, for example to a shared base without `relationships`, or to a union of result types, outside the boundary.
- `services/learning_progressions.py` `progression_result_text(result: ProgressionEvidenceResult)` has the same annotation. It is not a permitted exception either.


Completion evidence (2026-10-15, repository root, `HEAD 566226d` plus uncommitted DEV-010 code). Raw outputs and scripts are in the git-ignored `data/source_artifacts/learning_progressions/dev010/`.

- **Code.**
  - `services/lp_models.py`:
    - `_is_none`, and the compact models `CompactGraphRelationship`, `CompactJudgmentProjection`, and `CompactProgressionRelationshipEvidence`. They mirror the full models field for field; liftable fields are `X | None` with `Field(exclude_if=_is_none)`.
    - The shared models `SharedGraphRelationshipEvidence`, `SharedJudgmentEvidence`, and `SharedRelationshipEvidence`. Shared evidence is nested like an entry (`epistemicStatus`, `judgment.confidenceNotice`, `relationship.*`), and every field is omitted when absent.
    - The **Result type hierarchy**: `ProgressionResultBase` (`continuation_notice`, `metadata`, `nodes`); `ProgressionEvidenceResult(ProgressionResultBase)` with full `relationships`; and `CompactProgressionEvidenceResult(ProgressionResultBase)` with compact `relationships` and `shared_relationship_evidence`, whose `Field(description=…)` states the rehydration rule.
    - The alias `ProgressionResult = ProgressionEvidenceResult | CompactProgressionEvidenceResult`.
  - `services/lp_compact.py` (new, about 230 lines after black): `LIFTABLE_*_FIELDS`, `compact_relationships(relationships=…)`, and `rehydrate_relationships(relationships=…, shared=…)`, plus private `_shared_values`, `_strip`, and `_fill`.
  - Annotations only: `progression_result_text` and `require_progression_result_size` in `services/learning_progressions.py`, and `_build_progression_result` in `mcp/tools/learning_progressions.py`, now take `ProgressionResult`.
    - Local choice: these helpers read `result.relationships[0].provenance_uri`, so they use the union of the two branches rather than the bare common base (design: "code that reads relationships is typed against the specific branch").
  - No result class has switched base yet; DEV-011 and DEV-012 do that.
- **Static checks.** black and isort were applied, reformatting only `lp_compact.py`. ruff: all checks passed. **mypy over the whole package** (`src/kgfegmcp`, 123 files): no issues. pylint: 10.00/10. interrogate: passed. The tracked `interrogate_badge.svg` is unchanged.
- **Published schemas** (`dump_lp_schemas.py`; `schemas-before.json` and `schemas-after.json`): all nine progression request and result schemas are byte-identical before and after, including `GetLearningProgressionRequest` and `GetLearningProgressionResult` (`cmp` reports no difference).
- **Round trip on real evidence** (`compact_round_trip.py`, `compact-round-trip.json`): **0 problems** over 733 sets and 17,842 entries across all seven packages. The sets cover every LP edge in 25-entry single-type chunks, plus a 10+10 mixed page, an empty set, and a synthetic set per package.
  - In mixed pages, `description`, `label`, and `relationshipType` stay per entry; the other relationship liftables lift.
  - In synthetic sets, the differing `license` and the null `author` stay per entry and round-trip.
  - Empty sets produce `{}`.
  - Compact relationship JSON is 67.7% of the full form (42,119,151 of 62,225,551 characters, one copy).
  - The compact-base schema carries the rehydration rule in both field descriptions, and `CompactGraphRelationship` requires only `relationshipId`, `sourceNodeId`, `sourceExportOrder`, and `targetNodeId`.
- **Full offline suite** (`pytest.out`): 132 passed, 17 failed. These are the same 17 tests as after DEV-008 (10 six-package corpus, 6 baseline-path-behaviour or cycle tests, and the all-pairs envelope test). No new failures.

---

### DEV-011 — Standard progressions, LP search, and traversal results in compact form

`Status`: `DONE` `Depends On`: `DEV-010`
`Acceptance`: `AC-034, AC-035, AC-036`

**Goal**

Build `get_standard_progressions`, `search_learning_progressions`, and `traverse_learning_progressions` results in the compact form, with every size check and reservation measuring the emitted compact form, while selection, order, cursors, counts, and every non-relationship field stay computed exactly as before (**Preservation rule**).

**Affected Area**

- `backend/src/kgfegmcp/services/lp_discovery.py` and `services/lp_traversal.py`, at the points where results and trial results are assembled. Internal rows keep full evidence; the helper compacts them at result construction. `ProgressionCollectionResult` and `TraverseLearningProgressionsResult` move to the compact base.
- `backend/src/kgfegmcp/cli/smoke_progressions.py`: its result-model mapping and helper annotations use the common base. `_require_edge` (and the path-edge check after it) compares a compacted tool's entry with the full `get_learning_progression` edge after rehydrating it with the shared helper. It stays an exact equality on the whole evidence entry. Pinned diagnostics are unchanged.

**Expected Outcome**

- All three tools return compact entries plus `sharedRelationshipEvidence`. Their published output schemas describe both.
- `get_learning_progression` and every non-progression tool return byte-identical results.
- After rehydration, results equal the baseline where the baseline did not stop for size. Where it did, the baseline's items are a prefix of the new result, in order.

**Self-Check**

- Static checks on the changed files.
- A scratch **collection and traversal differential**. Record baseline outputs from a separate `git worktree` at `f9fdaa2`, run with the same virtualenv against that worktree's six packages, over deterministic request samples for the three tools. Rehydrate the new outputs and compare `relationships`, `nodes`, `connections` and distances, order, cursors, and stopping reasons. Size-stopped baseline cases use the prefix rule.
- A rehydration round-trip on every new result produced by the differential.
- Published output schemas over STDIO show the compact entry and the shared object. `get_learning_progression`'s output for a fixed request is byte-identical to the baseline's.
- `kgfegmcp-stdio-smoke` against the repository passes with the rehydrating edge check.


Completion evidence (2026-10-15, repository root, `HEAD 218de79` plus uncommitted DEV-011 code). Raw outputs and scripts are in the git-ignored `data/source_artifacts/learning_progressions/dev011/`. The baseline worktree is a detached `git worktree` at `f9fdaa2` in the session scratchpad.

- **Code** (`git diff --stat -- backend`: 4 files, +35/−10).
  - `services/lp_models.py`: `ProgressionCollectionResult` and `TraverseLearningProgressionsResult` now subclass `CompactProgressionEvidenceResult`.
  - `services/lp_discovery.py` `_build_result` and `services/lp_traversal.py` `_result`, the single constructors behind every trial, reservation, and final result, call `compact_relationships` and emit `relationships=entries, shared_relationship_evidence=shared`. Internal rows keep full evidence. Every existing size check (per-entry trials, `_require_entry_size` and `_require_edge_size`, the traversal reservation after each admitted edge, and the final checks) therefore measures the emitted compact form, including any un-lifted field.
  - `cli/smoke_progressions.py`:
    - `_RESULT_MODELS` is typed `type[ProgressionEvidenceResult] | type[CompactProgressionEvidenceResult]`, and `_read_query` and `_require_edge` take `ProgressionResult`.
    - `_require_edge` rehydrates a compact result's entries with `rehydrate_relationships` and then applies the unchanged exact whole-entry check `expected.relationships[0] not in relationships`. Full-form results (paths, until DEV-012) compare directly.
    - Pinned diagnostics are untouched.
- **Static checks.** black and isort were applied. ruff: passed. **mypy over the whole package** (123 files): no issues. pylint: 10.00/10. interrogate: passed. `interrogate_badge.svg` is unchanged.
- **Collection and traversal differential** (`record_lp_outputs.py`, `compare_lp_outputs.py`, `baseline-outputs.json`, `new-outputs.json`, `compare.json`).
  - The baseline was recorded by running `record_lp_outputs.py` with the `f9fdaa2` worktree first on `sys.path` and its own config and data roots. The module path was confirmed in the output.
  - Sample: 582 request sequences over the six baseline packages, following up to 3 pages: 240 `get_standard_progressions`, 102 `search_learning_progressions`, and 240 `traverse_learning_progressions`. The sample covers four connection kinds, three limits, both directions, depths 1–8, varied node and edge caps, type filters, and endpoint scopes.
  - **0 mismatches.**
    - 464 sequences never stopped for size in the baseline. They match exactly, page by page, after rehydration: `relationships`, `nodes`, `connections`, `distances`, cursors, `page`, counters, and stopping reasons.
    - 118 sequences had a baseline size stop (most `search` pages stop on `byte_limit`). Pages before the stop match exactly. From the stop on, the baseline's relationships, connections, and distances (and traversal nodes) are an in-order prefix of the new ones.
  - For example, an unfiltered Ghana English search with limit 10 now returns 8 entries per page where the baseline returned 7 and 6. That is why new pages total 776 against the baseline's 789.
- **Unchanged tool and schemas** (`record_exact_lookups.py`, `lookups-baseline.json`, `lookups-new.json`).
  - 150 `get_learning_progression` outputs (25 per baseline package) are byte-identical to the baseline, and `GetLearningProgressionResult`'s published schema is byte-identical.
  - `ProgressionCollectionResult` and `TraverseLearningProgressionsResult` publish compact entries and `sharedRelationshipEvidence`, with the rehydration description. `GetLearningProgressionPathsResult` is unchanged until DEV-012.
- **Repository STDIO smoke** (`kgfegmcp-stdio-smoke`, `stdio-smoke.out`). Run outside the sandbox: its child `uv` needs `~/.cache/uv`. Result: `status: passed`, 19 tools, 1 fixed resource, 14 templates, 9 prompts, 15 resource reads, and 7 LP snapshots. All five progression queries ran, and the rehydrating edge check held for both compacted tools.
- **Full offline suite** (`pytest.out`): 123 passed, 26 failed. 17 are unchanged from DEV-010. 9 are new, all pinning the full form (Tester-owned under the **Test-corpus contract**, AC-034 and AC-035):
  - `test_progression_text_only.py::test_ordinary_text_carries_the_complete_result[direct|search|traverse]`: `KeyError` reading `relationship.label` or `epistemicStatus` from entries; those are now in `sharedRelationshipEvidence`.
  - `test_progression_discovery.py::test_direct_adjacency_matches_original_records[outgoing_builds|incoming_builds|related]` (:164) and `test_progression_algorithms.py::test_traversal_keeps_merging_edges` (:69). Membership, order, and distances pass; only the check that each entry's `relationship` equals or is the stored `GraphRelationship` object fails, because entries are now `CompactGraphRelationship`.
  - `test_traversal_combination_only_bytes` (:125, `byte_limit` no longer reported) and `test_discovery_combination_bytes_preserve_continuation` (:397, a page now holds 3 entries instead of 1). Their fixture (`builds(pairs, text)`) places the oversized text in `attributionStatement`, which is identical across entries and is now lifted once. The "oversized only in combination" setup therefore fits, which is the AC-035 size-stopped exception. Tester needs a fixture whose oversized text sits in a per-entry field.

---

### DEV-012 — Path results in compact form with the IDs-only fallback

`Status`: `DONE` `Depends On`: `DEV-008, DEV-010`
`Acceptance`: `AC-024, AC-026, AC-028, AC-030, AC-032`

**Goal**

Emit every `get_learning_progression_paths` result in the compact form, and, when the first shortest path does not fit even compacted, return the design's IDs-only fallback instead of `progression_result_too_large`.

**Affected Area**

`backend/src/kgfegmcp/services/lp_paths.py`: `_result`, `_admit_path`, `_stop_on_size`, `_first_path_error`, and the reservation, so they measure the compact form after each admission. The design's **Size-accounting edge**: a new entry can un-lift a field.

**Expected Outcome**

- Every path result carries compact entries and `sharedRelationshipEvidence` on all seven packages, whether or not the full form would fit.
- If the first path does not fit compacted, the tool returns a normal result:
  - `paths`, `relationships`, and `sharedRelationshipEvidence` are empty;
  - `nodes` keeps the source and target summaries;
  - `nextUnreturnedPath` holds the complete shortest path's IDs;
  - `truncation_reasons` includes `byte_limit` plus any exact `depth_limit` or `path_limit`.
- The first-path error remains only if even that result cannot fit.

**Self-Check**

- Static checks on `lp_paths.py`.
- The DEV-008 differential rerun with rehydration: identical `paths`, `nodes`, and rehydrated `relationships` with empty reasons wherever the baseline was untruncated.
- A scratch **all-pairs run** over the 43,145 CAPS pairs at the shortest depth and at 16:
  - no errors;
  - the shortest path is `paths[0]`, or `nextUnreturnedPath` when `paths` is empty, with the oracle's hop count;
  - no `work_limit` or `queue_limit`;
  - **Result invariants** hold, including on `nextUnreturnedPath`;
  - rehydration round-trips.
  - It records the counts of full, `byte_limit`, and IDs-only outcomes by hop count, and the measured sizes of the 11-, 12-, and 13-hop results against the Architect's projection.
- A compact-versus-full size comparison on a sample of short path results.


Completion evidence (2026-10-15, repository root, `HEAD 8e1361c` plus uncommitted DEV-012 code). Raw outputs and scripts are in the git-ignored `data/source_artifacts/learning_progressions/dev012/`.

- **Code** (`git diff --stat -- backend`: 2 files, +25/−9).
  - `services/lp_models.py`: `GetLearningProgressionPathsResult` now subclasses `CompactProgressionEvidenceResult`.
  - `services/lp_paths.py` `_result`, the single constructor behind the reservation, the actual-size checks, and the final result, compacts `rows.relationships` and emits `relationships=entries, shared_relationship_evidence=shared`. Every admission therefore measures the emitted compact form, including any un-lifted field.
  - `_stop_on_size` applies the existing rollback (pop the path, restore the node and relationship tables to their state before the path, set `next_unreturned`, re-queue the state, add `byte_limit`) to the **first** path too. That rollback produces the IDs-only result:
    - empty `paths`, `relationships`, and `sharedRelationshipEvidence` (`{}`);
    - source and target summaries in `nodes`;
    - the path in `nextUnreturnedPath`;
    - `byte_limit` plus any exact `depth_limit`.
  - Only if that IDs-only result also fails `_require_size` does it raise `_first_path_error` (the degenerate case).
- **Static checks.** black and isort were applied. ruff: passed. **mypy over the whole package** (123 files): no issues. pylint: 10.00/10. interrogate: passed. `interrogate_badge.svg` is unchanged.
- **Path differential with rehydration** (`record_path_outputs.py`, `compare_path_outputs.py`, `paths-baseline.json`, `paths-new.json`, `paths-compare.json`).
  - The baseline came from the `f9fdaa2` worktree code (module path confirmed) run against the current seven packages; the new code ran normally. Both used the same deterministic sample as DEV-008: 5,127 requests, `maxDepth` cycling 1–12, `maxPaths` 1–20, connected and unconnected pairs.
  - The baseline was untruncated on 3,448 requests (2,197 with paths). On all of them the new code returns identical `paths`, `nodes`, rehydrated `relationships`, reasons, `graphExhausted`, `scopeComplete`, `nextUnreturnedPath`, request, metadata, and notices: **0 mismatches**. Only counters and frontier counts were excluded, as the design permits.
- **All-pairs CAPS run** (`caps_all_pairs_ac028.py`, `caps-all-pairs-ac028.json`, 469 s): 43,145 pairs × {shortest depth, 16}, default `max_paths`, 86,290 requests. **0 failures and 0 errors.**
  - Every request returned a result. The shortest path is `paths[0]` (hops 1–12), or `nextUnreturnedPath` with `byte_limit` (hops 13), with the oracle's hop count.
  - There were no `work_limit` or `queue_limit` stops. Peak use was 1,243 inspections and 32 states.
  - The **Result invariants** hold, including on `nextUnreturnedPath`.
  - Every rehydrated entry equals `relationship_evidence` for its edge.
  - Outcomes by hop count, at the shortest depth: hops 1–4 are all full. Hops 5–12 are full or keep the shortest path with `byte_limit` on later alternatives (for example, 11 hops: 29 full and 68 `byte_limit`; 12 hops: 8 full and 20 `byte_limit`). Hops 13 are IDs-only for all 5 pairs, at both depths.
  - Totals: `byte_limit` on 9,078 requests (it was 26,062 with the full form) and IDs-only on 10 requests. **No 10–12 hop shortest path falls back to IDs**; with the full form, all 984 of those requests errored.
  - Measured envelope characters at the shortest depth, compared with the Architect's projection:
    - 9 hops: 76,872–99,308.
    - 10 hops: 83,667–99,634.
    - 11 hops: 90,292–93,915 (projected about 92,000).
    - 12 hops: 96,855–99,872 (projected as borderline, about 98,000).
    - 13 hops, IDs-only: 19,931–20,065 (projected IDs-only).
  - Relationship tables of 1–3 hop results are 77.8% of their full-form size.
- **Unchanged tool and schemas** (`lookups-new.json` against `dev011/lookups-baseline.json`): 150 `get_learning_progression` outputs are byte-identical, and `GetLearningProgressionResult`'s schema is byte-identical. `GetLearningProgressionPathsResult` now publishes compact entries and `sharedRelationshipEvidence` with the rehydration description; `ProgressionPath` caps are 17 and 16.
- **Repository STDIO smoke** (run outside the sandbox for its child `uv` cache): `status: passed`, 19/1/14/9, all five progression queries. The rehydrating exact edge check holds for all four compacted tools, paths included.
- **Full offline suite** (`pytest.out`): 120 passed, 29 failed. 26 are unchanged from DEV-011; 3 are new, all intended by the design (Tester-owned under the **Test-corpus contract**):
  - `test_progression_text_only.py::test_ordinary_text_carries_the_complete_result[paths]`: `KeyError` on lifted fields (AC-032).
  - `test_paths_oversized_entry_rejected` (:227) and `test_paths_later_oversized_alternative_is_partial` (:276): both expect `ProgressionResultTooLargeError` for an unreturnable first path, which now gets the IDs-only fallback (AC-030).
  - `test_paths_every_real_shortest_connection_fits` now fails at :332 on `…5532996f103a → 2ccbf220…`, one of the five 13-hop CAPS pairs, which correctly returns IDs-only with `depth_limit` and `byte_limit`. Every earlier pair in that sweep, including CAPS pairs of 10–12 hops, passed. The design limits the exhaustive check to the six original packages.

---

### DEV-009 — MCPB manifest version matches the project version

`Status`: `DONE` `Depends On`: `NONE`
`Acceptance`: `AC-014`

**Goal**

Change only the `version` field of `packaging/mcpb/manifest.json` from `0.4.0` to `1.0.0`, so it equals `backend/pyproject.toml`'s `version`, as the revised design requires. This cuts no release.

**Affected Area**

`packaging/mcpb/manifest.json` (one field). Unchanged: `backend/pyproject.toml`, `backend/uv.lock`, release-please files, `CHANGELOG.md`, and the MCPB README.

**Expected Outcome**

`git diff -- packaging` shows exactly one changed line, and the version check in `cli/build_mcpb.py` no longer fails.

**Self-Check**

`git diff --stat` and `git diff -U0 -- packaging`; a JSON load of the manifest comparing `version` with the pyproject `version`. The full MCPB build and stage smoke run in DEV-006.

Completion evidence (2026-10-15, repository root, `HEAD 0b056dd` plus this change):

- `git diff -U0 -- packaging` shows exactly one changed line in `packaging/mcpb/manifest.json`: line 53, `"version": "0.4.0"` → `"version": "1.0.0"`. Tab indentation and the trailing newline are preserved.
- A JSON and TOML load reports manifest `1.0.0` equal to `backend/pyproject.toml` `1.0.0`. `manifest_version` is `0.4` and the name matches the project.
- The builder's own `kgfegmcp.cli.build_mcpb._validate_manifest_contract(manifest=…, project_metadata=…)`, run through `UV_OFFLINE=1 uv --directory backend run --locked --offline --no-sync python -`, passes. The version mismatch that stopped DEV-006's first build is gone.
- `git diff --quiet HEAD -- backend/pyproject.toml backend/uv.lock release-please-config.json .release-please-manifest.json CHANGELOG.md packaging/mcpb/README.md` reports them unchanged, so no release was cut. The README's `dist/kgfegmcp-0.4.0.mcpb` references are Documenter-owned (design **Risks**).
- The full MCPB build and the `--bundle-root` stage smoke run in DEV-006.

---

## Plan Notes

- Test files and fixtures under `backend/tests/` are Tester-owned. The design's **Test-corpus contract** (6→7 corpus counts, 8,080→~17,667 LP edges, the CAPS `progression_baseline.json` entry, and the sampled CAPS buildsTowards pairs) is left to Tester. Developer does not edit tests.
- `AC-020` and `AC-021` are Documenter-owned; this plan makes no documentation edits.
- Cycle baseline for boundary diffs: the design names `f9fdaa2`. `HEAD` has since gained the CAPS data commit `4c88217` and the replan's documentation commits, so boundary diffs use `f9fdaa2` explicitly.
- `data/graph_packages/.claude/` is absent as of plan creation, so local catalog loading and tests can run in place.
- Uploading the new input set to the Google Drive archive remains a user-owned follow-up.
- The `tony` style's Python rules, together with `styles/python.md`, apply to the DEV-008 backend change and to scratch scripts.
- Retired acceptance identifiers: AC-016 (replaced by AC-022), AC-022 and AC-033 (replaced by AC-036), AC-025 (replaced by AC-028 and AC-030), and AC-029 (replaced by AC-032). Current steps reference only current identifiers; retired ones appear only in historical evidence text.
- Step order once approved: DEV-008 (finish the cycle guard and recheck), then DEV-010, DEV-011, DEV-012, DEV-009, DEV-006, and DEV-007. The DEV-008 code is already committed in `504a8e5`.
- The compact form is a breaking output change for four tools. Per the design's risks, the eventual commit for DEV-011 and DEV-012 should be marked breaking (`!` or a `BREAKING CHANGE:` footer).
- AC-031 and AC-037 are Documenter-owned.

### Suspended Assignment 1

`Recovery Frame`: `1` `Recovery Reason`: `DEV-006 disproved the design: AC-014 MCPB build is blocked by a pre-existing packaging/mcpb manifest 0.4.0 vs backend 1.0.0 version mismatch inside the forbidden packaging/ boundary, and CAPS path search truncates 9+ hop connections that the CAPS path-sample contract assumes complete.` `Purpose`: `DEVELOPMENT` `Target`: `NONE` `Assessed Inputs`: `HEAD d48627f plus uncommitted CAPS profile, overlay, south_africa_english input set, and package south-africa-dbe-caps-english-home-language-grades-r-3@2011+95ab377d1619; DEV-001..DEV-005 DONE; DEV-006 checks recorded under DEV-006 Evidence so far` `Next Action`: `After the corrected design returns, reconcile DEV-006 with it (and revise the plan if the correction changes approved intent), rerun the MCPB stage build and kgfegmcp-stdio-smoke --bundle-root against the stage, recheck the boundary, then continue to DEV-007.`

### Suspended Assignment 2

`Recovery Frame`: `1` `Recovery Reason`: `DEV-008 found the design's change boundary too narrow: raising max_depth to 16 also requires raising ProgressionPath node_ids/relationship_ids caps (13/12) in lp_models.py, which changes the published output schema, and the path tool description's published 'maxima 12/20' text.` `Purpose`: `DEVELOPMENT` `Target`: `NONE` `Assessed Inputs`: `HEAD a18dd76 (CAPS data committed in 4c88217) plus uncommitted .standards plan/state edits; backend/src unchanged; DEV-001..DEV-005 DONE; DEV-008 IN_PROGRESS with no code written; DEV-009, DEV-006, DEV-007 PENDING` `Next Action`: `After the corrected design returns, reconcile DEV-008's Affected Area and Expected Outcome with the widened boundary (revising the plan to PROPOSED if intent changes), then implement DEV-008 and run its self-checks.`

### Suspended Assignment 3

`Recovery Frame`: `1` `Recovery Reason`: `DEV-008 disproved AC-025 as designed: target-aware search finds every CAPS pair within budgets, but the fixed 100,000-character result envelope rejects all 492 CAPS pairs of 10-13 hops (progression_result_too_large) and reports byte_limit on 26,062 of 86,290 all-pairs requests.` `Purpose`: `DEVELOPMENT` `Target`: `NONE` `Assessed Inputs`: `HEAD d635c6a plus uncommitted DEV-008 code in services/lp_paths.py, services/lp_models.py, mcp/tools/learning_progressions.py; DEV-001..DEV-005 DONE; DEV-008 IN_PROGRESS (implemented; AC-025 self-check unmet); DEV-009, DEV-006, DEV-007 PENDING` `Next Action`: `After the corrected design or scope returns, reconcile DEV-008 with it (revising the plan to PROPOSED if intent changes), apply any newly permitted change, rerun the all-pairs, differential, schema, and static checks, then continue with DEV-009.`

### Suspended Assignment 4

`Recovery Frame`: `1` `Recovery Reason`: `DEV-010 found the compact-form change boundary too narrow: cli/smoke_progressions.py asserts the full get_learning_progression edge is in each compacted tool's relationships (stdio smoke for AC-012/AC-014 would fail), and mcp/tools/learning_progressions.py plus that smoke CLI are typed against ProgressionEvidenceResult, so a compact result base needs changes outside the boundary.` `Purpose`: `DEVELOPMENT` `Target`: `NONE` `Assessed Inputs`: `HEAD e200189 (DEV-008 complete with cycle guard); backend/src unchanged since; DEV-001..DEV-005 and DEV-008 DONE; DEV-010 IN_PROGRESS with no code written; DEV-011, DEV-012, DEV-009, DEV-006, DEV-007 PENDING` `Next Action`: `After the corrected design returns, reconcile DEV-010..DEV-012 with the widened boundary (revising the plan to PROPOSED if intent changes), then implement DEV-010.`

### Reconciliation of Suspended Assignment 1 (2026-10-15)

Architect closed recovery frame 1 with no rerun (`Handoff.Kind: RESUME`). The corrected scope and design materially change the approved implementation: they add a generic backend change and the MCPB manifest correction. So this plan is revised and returned to `PROPOSED`.
- The saved DEVELOPMENT assignment resumes as DEV-008 and DEV-009, then DEV-006 (reopened to `PENDING` and rerun in full), then DEV-007.
- DEV-001..DEV-005 stay `DONE`. The design's CAPS identity, profile, overlay, input-set, and package values are unchanged, so the accepted package `…@2011+95ab377d1619` remains valid.
- `User Style` `tony` stays locked, and `Mode` stays `STEPWISE`.

### Reconciliation of Suspended Assignment 2 (2026-10-15)

Architect closed recovery frame 1 with no rerun (`d635c6a`), widening the **Change boundary** to the path-depth constant, the `ProgressionPath` caps, and the path tool description's maxima. DEV-008 resumes `IN_PROGRESS` with its Affected Area, Expected Outcome, and Self-Check updated to match. The approved intent is unchanged: target-aware exact-length search with a `max_depth` ceiling of 16. The added edits are the design-required means of returning paths of up to 16 hops, so this is treated as bookkeeping reconciliation without re-approval. No other step changes.

### Reconciliation of Suspended Assignment 3 (2026-10-15)

Architect closed recovery frame 1 with no rerun (`2ea9553`), after two scope replans (`504a8e5` and `dfb199a`). AC-025 was retired in favour of AC-028 and AC-030 (a non-error result that identifies the shortest path, with `byte_limit` allowed) and AC-032. The compact shared-place form now applies to four tools (AC-034, AC-035, AC-036), and the design adds a **Cycle guard**.

These materially change the implementation plan:
- DEV-008 is narrowed to the search, the ceiling, and the cycle guard.
- DEV-010, DEV-011, and DEV-012 are added.
- DEV-006's dependencies and acceptance are updated.

The plan returns to `PROPOSED` for approval. `Mode` stays `STEPWISE` and `User Style` `tony` stays locked. The DEV-008 code committed in `504a8e5` stays as the basis for the next steps.

### Reconciliation of Suspended Assignment 4 (2026-10-15)

Architect closed recovery frame 1 with no rerun (`566226d`). The **Change boundary** now includes:
- the result type hierarchy split;
- annotation-only updates in `services/learning_progressions.py` and `mcp/tools/learning_progressions.py`;
- `cli/smoke_progressions.py`'s annotations and its rehydrating, still-exact edge check.

The approved intent is unchanged: the compact form for four tools, without weakening the smoke check. These are the design-required means to deliver it. The plan is therefore reconciled as bookkeeping without re-approval:
- DEV-010 takes the type split, the annotations, and production rehydration.
- DEV-011 takes the smoke edge check.

DEV-010 resumes `IN_PROGRESS`.
