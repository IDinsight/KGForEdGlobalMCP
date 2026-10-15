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
- `Request`: Integrate the CAPS English Home Language (Grades R-3) KG export as a seventh framework, using data and configuration. Also make generic Learning Progression path search target-aware and raise its `max_depth` ceiling to 16, and correct the MCPB manifest version (scope replan and design revision, 2026-10-14).

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

`Status`: `PENDING` `Depends On`: `DEV-005, DEV-008, DEV-009`
`Acceptance`: `AC-011, AC-012, AC-013, AC-014, AC-015, AC-017, AC-018, AC-019, AC-022`

**Goal**

Confirm that the generic runtime, MCPB stage, and Docker context pick up CAPS with the corrected path search and MCPB manifest in place, and that the change set stays inside the revised design's **Change boundary**. If any further backend change turns out to be needed, stop and route an `ARCHITECTURE` failure.

**Affected Area**

No new repository files expected. Checks run against the repository server, a fresh MCPB stage and bundle written to the git-ignored `data/source_artifacts/learning_progressions/dev006/` (so the user's `dist/` is untouched), and the Docker build context.

**Expected Outcome**

- Catalog lists 7 frameworks with CAPS statistics equal to its manifest counts.
- A real STDIO session (scratch client, no LLM) can retrieve, search, and get context for CAPS standards and Learning Components, and look up, search, and traverse CAPS LPs with the generic disclosures.
- `kgfegmcp-build-mcpb` succeeds; the fresh stage contains the CAPS package, profile, and overlay; `kgfegmcp-stdio-smoke --bundle-root <stage>` passes.
- Docker context includes the CAPS paths with `Dockerfile` and `.dockerignore` unchanged.
- `git diff f9fdaa2` shows, outside the CAPS additions and `.standards/`, only `services/lp_paths.py`, the `max_depth` bound in `services/lp_models.py`, and the `version` field of `packaging/mcpb/manifest.json` (plus any Tester test updates). Nothing changes under `Dockerfile`, `.dockerignore`, `.gitignore`, release-please files, `CHANGELOG.md`, the project version, or any existing package, profile, overlay, or input set.

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

`Status`: `IN_PROGRESS` `Depends On`: `DEV-005`
`Acceptance`: `AC-018, AC-022, AC-023, AC-024, AC-025, AC-026`

**Goal**

Replace the breadth-first enumeration in `paths_result` with the design's exact-length, target-aware search (**Target-aware path search**), and raise `GetLearningProgressionPathsRequest.max_depth`'s upper bound from 12 to 16. The change is generic, with no framework-specific branch.

**Affected Area**

- `backend/src/kgfegmcp/services/lp_paths.py`: `paths_result` and its private helpers. Kept as they are: the signature, `path_id_bound`, `PathIdBound`, `_admit_path`, `_require_size`, `_stop_on_size`, `_first_path_error`, `_reserved_path`, the result model, and the callers in `services/learning_progressions.py`.
- `backend/src/kgfegmcp/services/lp_models.py`: the single `max_depth` bound of `GetLearningProgressionPathsRequest` (`le=12` becomes `le=16`; default 6). The traversal request's own bound (`le=12`, default 8) is unchanged.

**Expected Outcome**

- **Backward pass.** From the target, using the upstream builds adjacency, compute for each node that can reach the target its exact reachable hop counts ≤ `max_depth` (as a bitmask) and its uncapped longest hop count. Acyclicity is validated, so this is computed without recursion. Every inspected adjacency entry counts toward the fixed 5,000 inspection budget.
- **Forward enumeration.** For each `k` from 1 to `max_depth` that the source can reach in exactly `k` hops, search depth-first in `relationship_id` order. An edge is extended only when its head can still finish in exactly the remaining hops.
  - Output order is unchanged: hop count, then relationship-ID tuple.
  - Every created partial path, including the source state, counts toward the 5,000-state budget.
  - Admission, byte stops, `nextUnreturnedPath`, and the size reservation keep their behavior.
- **Truncation reasons.** `work_limit` and `queue_limit` on the budgets. `path_limit` only when another path within `max_depth` exists. `depth_limit` exactly when the source's uncapped longest connection exceeds `max_depth`. `byte_limit` unchanged. `graph_exhausted` and `scope_complete` keep their formulas. Counters and frontier fields keep their names and report the new search's effort.
- **Request bound.** `max_depth` accepts 1–16, still defaults to 6, and rejects 0 and 17 through the existing validation path. The published tool input schema shows maximum 16.

**Self-Check**

- `black --check`, `isort --check-only`, `ruff check`, `mypy`, `pylint` (McCabe ≤ 10), and `interrogate` on the changed files, using the repository's configuration.
- The existing progression tests that do not encode the six-package corpus or pin counter values still pass.
- A scratch **differential run** (not a committed test) against a reference copy of the baseline enumerator from `git show f9fdaa2:backend/src/kgfegmcp/services/lp_paths.py`, over deterministic request samples on all seven packages (`max_depth` 1–12, `max_paths` 1–20, connected and unconnected pairs). Wherever the baseline returns empty `truncation_reasons`, the new search must return identical `paths`, `relationships`, and `nodes`, with empty reasons.
- A scratch **all-pairs run** over the 43,145 connected CAPS pairs at `max_depth` equal to the shortest length and at 16, with default `max_paths`. The first path must have the oracle's shortest length, no result may report `work_limit`, `queue_limit`, or `byte_limit`, and every result must satisfy the **Result invariants**. Peak inspection and state counts are recorded.
- The published `get_learning_progression_paths` input schema, read over STDIO, shows `max_depth` maximum 16 and default 6.

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

---

### DEV-009 — MCPB manifest version matches the project version

`Status`: `PENDING` `Depends On`: `NONE`
`Acceptance`: `AC-014`

**Goal**

Change only the `version` field of `packaging/mcpb/manifest.json` from `0.4.0` to `1.0.0`, so it equals `backend/pyproject.toml`'s `version`, as the revised design requires. This cuts no release.

**Affected Area**

`packaging/mcpb/manifest.json` (one field). Unchanged: `backend/pyproject.toml`, `backend/uv.lock`, release-please files, `CHANGELOG.md`, and the MCPB README.

**Expected Outcome**

`git diff -- packaging` shows exactly one changed line, and the version check in `cli/build_mcpb.py` no longer fails.

**Self-Check**

`git diff --stat` and `git diff -U0 -- packaging`; a JSON load of the manifest comparing `version` with the pyproject `version`. The full MCPB build and stage smoke run in DEV-006.

---

## Plan Notes

- Test files and fixtures under `backend/tests/` are Tester-owned. The design's **Test-corpus contract** (6→7 corpus counts, 8,080→~17,667 LP edges, the CAPS `progression_baseline.json` entry, and the sampled CAPS buildsTowards pairs) is left to Tester. Developer does not edit tests.
- `AC-020` and `AC-021` are Documenter-owned; this plan makes no documentation edits.
- Cycle baseline for boundary diffs: the design names `f9fdaa2`. `HEAD` has since gained the CAPS data commit `4c88217` and the replan's documentation commits, so boundary diffs use `f9fdaa2` explicitly.
- `data/graph_packages/.claude/` is absent as of plan creation, so local catalog loading and tests can run in place.
- Uploading the new input set to the Google Drive archive remains a user-owned follow-up.
- The `tony` style's Python rules, together with `styles/python.md`, apply to the DEV-008 backend change and to scratch scripts.
- AC-016 was retired by the scope replan and replaced by AC-022; this plan references AC-022 only.

### Suspended Assignment 1

`Recovery Frame`: `1` `Recovery Reason`: `DEV-006 disproved the design: AC-014 MCPB build is blocked by a pre-existing packaging/mcpb manifest 0.4.0 vs backend 1.0.0 version mismatch inside the forbidden packaging/ boundary, and CAPS path search truncates 9+ hop connections that the CAPS path-sample contract assumes complete.` `Purpose`: `DEVELOPMENT` `Target`: `NONE` `Assessed Inputs`: `HEAD d48627f plus uncommitted CAPS profile, overlay, south_africa_english input set, and package south-africa-dbe-caps-english-home-language-grades-r-3@2011+95ab377d1619; DEV-001..DEV-005 DONE; DEV-006 checks recorded under DEV-006 Evidence so far` `Next Action`: `After the corrected design returns, reconcile DEV-006 with it (and revise the plan if the correction changes approved intent), rerun the MCPB stage build and kgfegmcp-stdio-smoke --bundle-root against the stage, recheck the boundary, then continue to DEV-007.`

### Suspended Assignment 2

`Recovery Frame`: `1` `Recovery Reason`: `DEV-008 found the design's change boundary too narrow: raising max_depth to 16 also requires raising ProgressionPath node_ids/relationship_ids caps (13/12) in lp_models.py, which changes the published output schema, and the path tool description's published 'maxima 12/20' text.` `Purpose`: `DEVELOPMENT` `Target`: `NONE` `Assessed Inputs`: `HEAD a18dd76 (CAPS data committed in 4c88217) plus uncommitted .standards plan/state edits; backend/src unchanged; DEV-001..DEV-005 DONE; DEV-008 IN_PROGRESS with no code written; DEV-009, DEV-006, DEV-007 PENDING` `Next Action`: `After the corrected design returns, reconcile DEV-008's Affected Area and Expected Outcome with the widened boundary (revising the plan to PROPOSED if intent changes), then implement DEV-008 and run its self-checks.`

### Reconciliation of Suspended Assignment 1 (2026-10-15)

Architect closed recovery frame 1 with no rerun (`Handoff.Kind: RESUME`). The corrected scope and design materially change the approved implementation: they add a generic backend change and the MCPB manifest correction. So this plan is revised and returned to `PROPOSED`.
- The saved DEVELOPMENT assignment resumes as DEV-008 and DEV-009, then DEV-006 (reopened to `PENDING` and rerun in full), then DEV-007.
- DEV-001..DEV-005 stay `DONE`. The design's CAPS identity, profile, overlay, input-set, and package values are unchanged, so the accepted package `…@2011+95ab377d1619` remains valid.
- `User Style` `tony` stays locked, and `Mode` stays `STEPWISE`.
