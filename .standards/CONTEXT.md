# Project Context

## Project Baseline

- KGForEdGlobalMCP is a read-only, deterministic FastMCP server that serves
  curriculum knowledge-graph "graph packages" (Academic Standards, Learning
  Components, stored Learning Progressions). It makes no server-side LLM calls.
  Released as `1.0.0` (`CHANGELOG.md`, `.release-please-manifest.json`).
- Six terminal `passed` packages are served today, one per framework under
  `data/graph_packages/<framework-id>/<framework-id>@<version>+<hash>/`:
  Ghana NaCCA English B1-3, Ghana NaCCA Math B4-6, India CBSE Science 9-10, India
  Tamil Nadu TNSCERT Math 1-5, Nigeria NERDC Math P1-3, Rwanda REB Math P1-3.
- Public MCP surface: 19 tools, 1 fixed resource, 14 resource templates, 9
  prompts (`README.md`; asserted in
  `backend/tests/kgfegmcp/test_progression_protocol.py`).
- Adding a framework is documented as a data and configuration change, not a
  Python change (`docs/development/framework-package.md`). No runtime, Docker,
  MCPB, build/prepare CLI, or `.gitignore` code keeps a list of frameworks; all
  of them discover packages, profiles, prompts, and input sets by walking
  directories.
- This cycle's request targets the CAPS English Home Language export at an
  external path:
  `/Users/tzz/Projects/private/idi/KGForEdGlobal/results/kg_for_ed/c939a3a9dcce92ed61d970f4599ced6f2ddc425d1220eeeab9828472b878d24d/`
  (source document key `c939a3a9…d24d`). Facts about that export are under
  **External Systems and Data**.

## Stack and Tooling

- Python `>=3.13,<3.14`, managed with `uv` (`backend/pyproject.toml`,
  `backend/uv.lock`). Uses FastMCP, Pydantic v2 strict models, and Typer CLIs.
- Package console scripts (`backend/pyproject.toml`): `kgfegmcp-build-manifest`,
  `kgfegmcp-validate-packages`, `kgfegmcp-prepare-learning-progressions`,
  `kgfegmcp-verify-evidence-archive`, `kgfegmcp-stdio-smoke`,
  `kgfegmcp-build-mcpb`, and others.
- Docs use MkDocs (`mkdocs.yml`, `docs/`), deployed by
  `.github/workflows/docs.yml`.
- Node.js and npm are needed only to build the optional `.mcpb` bundle.

## Structure and Boundaries

- `backend/src/kgfegmcp/packages/` — builder (`builder.py`), loader, validator
  (`validator.py`, `lp_validation.py`), LP normalization/preparation
  (`normalization*.py`), slim provenance sharding (`slim.py`), evidence archive
  records.
- `backend/src/kgfegmcp/profiles/` — typed interpretation-profile models and
  loader.
- `backend/src/kgfegmcp/{catalog,services,search,graph,resources,prompts,mcp}/`
  — generic runtime. Its catalog counts are computed from loaded packages.
- `config/profiles/<profile-id>/2.0/profile.json` — per-framework semantic
  contract: grade mappings, statement types and hierarchy, code-search policy,
  rights, and disclosures.
- `config/prompts/<profile-id>/2.0/prompts.json` — optional prompt overlay
  (max 64 KiB).
- `data/graph_packages/` — committed, sealed, runtime-only packages:
  `package_manifest.json`, `delivery/`, small `detailed/` files, 64 `slim/` LP
  provenance shards plus their index, and `evidence/evidence_archive_record.json`.
- `data/input_artifacts/<set>/` — per-package build inputs. `package_build.json`
  and 9 small `detailed/` files are committed. `delivery/`, `additional/` (64
  original LP provenance shards), and 11 archive-only `detailed/` files are
  git-ignored by wildcard rules that also cover new sets. The archive copies are
  kept by hand in the IDinsight Google Drive.
- `data/source_artifacts/` — git-ignored local preparation area
  (`learning_progressions/<doc-key>/kgs/`, `copy_receipt.json`, `prepared/`,
  `rebuilt_packages/`). **It does not exist in this checkout.**
- `Dockerfile`, `.dockerignore` (allowlist), `packaging/mcpb/` — copy all of
  `config/` and `data/graph_packages/` with no per-package list.

## Commands

All commands run from the repository root. In this sandboxed environment, `uv`
needed `UV_CACHE_DIR` pointed at a writable temp directory.

- `uv --directory backend sync --locked --no-dev` — create the backend
  environment (`README.md`).
- `PYTHONDONTWRITEBYTECODE=1 UV_OFFLINE=1 uv --directory backend run --locked --offline --no-sync pytest -q -p no:cacheprovider -m 'not costs-money' tests`
  — full offline test suite (`docs/development/testing.md`).
- `uv --directory backend run --locked kgfegmcp-prepare-learning-progressions [--framework-id …] [--receipt …] [--output-root …]`
  — normalize verified local source copies into
  `data/source_artifacts/learning_progressions/prepared/<framework-id>/`,
  including the 64 original LP provenance shards.
- `uv --directory backend run --locked kgfegmcp-build-manifest --spec <abs-path> [--dry-run]`
  — build a pending package from a `package_build.json` spec.
- `uv --directory backend run --locked --no-dev kgfegmcp-validate-packages one --framework-id <id> --snapshot-id <id> [--read-only]`
  — validate a package. Running it without `--read-only` persists the
  pending-to-terminal transition. Full validation reads the archived evidence.
- `uv --directory backend run --locked --no-dev kgfegmcp-verify-evidence-archive all|one …`
  — check restored archive files against evidence records.
- `uv --directory backend run --locked --no-dev kgfegmcp-stdio-smoke [--bundle-root …]`
  — real STDIO MCP smoke test.
- `uv --directory backend run --locked --no-dev kgfegmcp-build-mcpb --stage-output ./dist/kgfegmcp-stage`
  — build an MCPB stage.

## Conventions and Constraints

- Sealed packages are immutable. Never edit a passed package in place. Package
  revision is fixed at `1`; changed inputs or profile bytes require a new
  snapshot identity. Builds are deterministic.
- The builder accepts only input paths inside the repository, because the
  evidence archive record stores repository-relative `localPath`s. External
  exports must first be copied into the repository. The source project must not
  be edited.
- The documented preparation flow: copy exactly the 23 listed files into
  `data/source_artifacts/learning_progressions/<doc-key>/kgs/` and write a
  verified `copy_receipt.json` at
  `data/source_artifacts/learning_progressions/copy_receipt.json`. The receipt
  holds `receiptVersion` `1.0`, `status` `verified`, a framework mapping (64-hex
  `documentKey`, `frameworkCaseUuid`, `frameworkId`, destination), and per-file
  hashes and sizes (`packages/normalization_models.py`,
  `packages/normalization_sources.py`). The framework mapping lives only in the
  receipt, and nothing in the repository writes the receipt. After that: run
  prepare, move the output into a new `data/input_artifacts/<set>/`, author
  `package_build.json` (template:
  `data/input_artifacts/ghana_english/package_build.json`), then build, validate
  read-only, accept, and smoke test.
- Flat versus envelope combined exports are detected by record shape, not by
  framework (`packages/normalization.py` `_check_combined_export`).
- Profile/package agreement is enforced exactly. The profile's `localSubject`,
  `rights.attributionStatement`, and `rights.sourceLicense` must equal the root
  `StandardsFramework` node's `academicSubject`, `attributionStatement`, and
  `license` (`packages/builder.py` ~L899-916, `validator.py`). LP edge licenses
  must match the root (`lp_validation.py`).
- Every item `gradeLevel` value must appear exactly in some profile
  `gradeMappings[].normalizedGrades` (`validator.py` `_validate_item_grade_levels`).
  Normalized grades are free strings. Every existing profile uses numeric
  strings, and comparison grade filters match them literally.
- `codeSearchPolicy.availability: none` is an established option (used by the
  Nigeria and Rwanda profiles). It must declare no code types and no prefix
  search (`profiles/models.py`).
- `jurisdictionType` is a free non-empty string. Existing values are `country`
  (5 packages) and `state` (Tamil Nadu).
- Rights gating: `reviewStatus` must be approved or
  `provisional_operator_approved` before resources and prompts are exposed;
  prompts and packages with learning components need
  `allowGeneratedDerivatives: allowed`. Every existing profile uses
  `allowFullText: true` and `allowBulkResource: false`, and a test asserts this
  for all packages.
- Generic code must not branch on framework IDs. Do not weaken validation to
  admit one framework.
- Tests must never call live or paid LLM services.
- Deployment and publication are user-owned. Uploading to the Google Drive
  archive is manual and outside the repository.
- Pre-commit runs detect-secrets, end-of-file-fixer, and trailing-whitespace,
  including on data files.

## External Systems and Data

- **CAPS English export** (`…/c939a3a9…d24d/kgs/`, 1.7 GB directory, owned by
  the external KGForEdGlobal project):
  - All 23 required copy-set files are present, plus extra pipeline files that
    are not needed.
  - Framework: "Curriculum and Assessment Policy Statement (CAPS): English Home
    Language, Foundation Phase, Grades R-3".
    - CASE UUID `7bb16abe-6d0a-5bb9-9a01-aeb7c4baeaa3`.
    - Jurisdiction South Africa; author Department of Basic Education.
    - `academicSubject` "English Home Language"; language `en`.
    - `license` "Unknown" on all 2,057 nodes.
    - Attribution: "Source curriculum: Curriculum and Assessment Policy
      Statement (CAPS), English Home Language, Foundation Phase, Grades R-3. ©
      2011 Department of Basic Education, Republic of South Africa."
    - Source PDF `caps_english_hl_grade_3_fs.pdf`, 100 pages. No publication
      date in metadata.
  - Record format is the **envelope** shape (`identifier`/`labels`/`properties`/`type`
    for nodes; `label`/`source_identifier`/`target_identifier`/`properties` for
    relationships). This is the same shape as the CBSE export. The other five
    exports are flat.
  - Nodes: 1 StandardsFramework, 1,144 StandardsFrameworkItems, 912
    LearningComponents.
    - Statement types: Skill 924 (normalized `Standard`), Sub-strand 152,
      Skill Area 48, Term 16, Grade 4 (the last four normalized
      `Standard Grouping`).
  - **No item has `statementCode`** (0 of 1,144).
  - `gradeLevel` values are `"K"` (385 items, the source's encoding of Grade R),
    `"1"`, `"2"`, and `"3"`.
  - Relationships: 11,935 in total.
    - hasChild 1,144, a strict tree with no multi-parent children.
    - supports 1,204.
    - buildsTowards 2,879 and relatesTo 6,708, so 9,587 LP edges.
  - `as_lc_validation_report.json` and `lp_validation_report.json` both report
    `passed: true` with no errors. The LP report has 0 needs-review claims, 0
    unresolved warning pairs, and 0 cycles.
  - `lp_generation_pending_completions.json` is empty. An empty
    `.lp_generation.lock` file remains from 2026-10-10.
  - `lp_relationship_provenance.json` is about 116 MB, compared with 40.9 MB for
    CBSE and about 101 MB for all six current maps combined.
- **Scale relative to the existing corpus:** the corpus today holds 8,080 LP
  edges (3,039 buildsTowards plus 5,041 relatesTo), so CAPS alone more than
  doubles that.
  - Estimated new package: about 85–90 MB, of which about 70 MB is `slim/`
    with shards around 1.1 MB each. This would roughly double
    `data/graph_packages/` (currently 81 MB on disk). This is an extrapolation
    from CBSE, not a measurement.
  - Per-file limits: `max_resource_bytes` is 8 MiB and
    `max_resource_source_bytes` is 32 MiB (`config.py`); GitHub's per-file
    limit is 100 MB.
  - Build and acceptance load the original provenance map whole, with no byte
    cap (`slim.py`, `normalization.py`).
  - The repository uses no Git LFS.
- **Google Drive evidence archive:** a manual, out-of-repository store for the
  archive-only input files.

## Testing and Verification Baseline

- 149 pytest tests live under `backend/tests/kgfegmcp/`, with fixtures in
  `backend/tests/fixtures/`. CI is `.github/workflows/tests.yml`; it triggers on
  `data/**` and `config/**` and runs without archived evidence.
- Verified on 2026-10-14: **149 passed**, when run against a copy of
  `data/graph_packages/` that excludes the stray `.claude/` directory (see
  **Known Unknowns**). Run in place, the suite fails catalog loading with
  "A graph-packages framework directory has an invalid identifier name." (1
  failed, 27 passed, 121 errors).
- Tests that encode the current six-package corpus will fail when a seventh
  package is added:
  - `test_runtime_only_packages.py:201,334` and
    `test_progression_discovery_text.py:79,92,93,143` assert a count of 6.
  - `test_progression_discovery.py:116` and `test_progression_lookup.py:161`
    assert 8,080 LP edges.
  - `test_progression_algorithms.py:342` asserts 6,522 connected buildsTowards
    pairs with a maximum shortest path of 8. The BFS over every connected pair
    will also run noticeably longer.
  - `test_progression_regressions.py:102` looks up `baseline[framework_id]` in
    `tests/fixtures/progression_baseline.json`, which has one entry per
    framework, so a new framework raises `KeyError`.
  - `test_progression_resources.py:146-148` asserts the rights flags for all
    packages.
- Smoke CLIs pin specific Ghana English, Nigeria, CBSE, and Ghana Math
  diagnostic IDs and expectations (`cli/smoke_checks.py`,
  `cli/smoke_access.py`). These stay valid when a package is added.
- Archived evidence (the git-ignored input files) is not restored in this
  checkout, so full evidence-tier validation of the existing packages cannot run
  locally. Runtime-only validation and tests can.

## Relevant Existing Behavior

- The six existing packages, their snapshot IDs, and their served behavior must
  not change. Adding a package must not alter their bytes.
- LP edges are IDinsight-generated judgments with required disclosures.
  Acceptance is structural/process integrity, not pedagogical certification.
- Documentation is maintained by hand; nothing generates it. Framework lists,
  counts, and totals ("six", 8,080 edges, package sizes, file counts, input-set
  table) appear in:
  - `docs/data/framework-catalog.md`
  - `docs/index.md`
  - `docs/development/framework-package.md`
  - `docs/guides/progression.md`
  - `docs/reference/{resources,progression-tool}.md`
  - `docs/data/*.md`
  - `docs/operations/{deployment,mcpb,cli}.md`
  - `docs/getting-started/*.md`
  - `docs/development/{testing,local-setup}.md`
  - `backend/README.md`
  - `packaging/mcpb/README.md`
  The root `README.md` lists no frameworks.

## Known Unknowns

- `data/graph_packages/.claude/.cc-writes` is an untracked, empty local
  directory, probably a Claude Code harness artifact created on 2026-10-14. It
  breaks strict catalog loading and the test suite in this checkout. It is not
  in Git and was left untouched; whether to remove it locally is the user's
  call.
- Which profile grade label and normalized value represent CAPS "Grade R" (the
  source carries `"K"`), and whether "Foundation Phase" belongs in
  `educationStageMappings`. These are scope and design decisions.
- Rights posture for CAPS (`reviewStatus`, derivative and full-text flags). The
  source license is "Unknown", and operator approval has not been established.
- The new framework ID, version token, input-set name, and source publication
  date are not established by any repository artifact.
- Whether the roughly doubled package footprint is acceptable for the Git
  repository, the Docker image, and the MCPB bundle has not been established.
- Whether the empty `.lp_generation.lock` in the source export signals anything.
  Every completion artifact indicates a finished, validated run.

## Evidence

- `README.md`, `docs/development/framework-package.md`,
  `docs/development/testing.md` — purpose, onboarding workflow, commands, and
  test policy.
- `data/input_artifacts/ghana_english/package_build.json` — build spec shape.
- `config/profiles/*/2.0/profile.json` — code availability, grade, rights, and
  multi-parent settings per framework.
- `backend/src/kgfegmcp/packages/{builder,validator,normalization,normalization_sources,normalization_models,slim}.py`,
  `profiles/models.py`, `config.py` — enforced contracts and limits.
- Offline pytest run on 2026-10-14 against a cleaned package copy — 149 passed.
- Read-only inspection of the CAPS `kgs/` directory: file presence, record
  shapes, counts, metadata, and validation reports.
