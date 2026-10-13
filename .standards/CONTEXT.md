# Project Context

## Project Baseline

- KGForEdGlobalMCP is a Python MCP server (package `kgfegmcp`, version `0.4.0`)
  that serves curriculum knowledge graphs (Academic Standards, Learning
  Components, Learning Progressions) from immutable, validated graph packages.
  It does not contain the upstream PDF extraction or KG-construction pipeline;
  that lives in the separate `KGForEdGlobal` project and is consumed only as
  exported artifacts.
- Six frameworks are currently served, each as one mixed AS/LC/LP package with
  profile and prompt-config version `2.0`:
  `ghana-nacca-primary-english-language-basic-1-3`,
  `ghana-nacca-primary-mathematics-basic-4-6`,
  `india-cbse-science-learning-framework-classes-9-10`,
  `india-tamil-nadu-tnscert-mathematics-classes-1-5`,
  `nigeria-nerdc-mathematics-primary-1-3`, and
  `rwanda-reb-mathematics-lower-primary-1-3`. No South African framework exists.
- Prior curriculum additions were landed as two paired commits per framework:
  "enable learning progressions for X" (profile/prompts, graph package, docs)
  and "add X learning progression input artifacts" (maintained inputs), e.g.
  `ea143f7`/`01a19d9` for Ghana English.
- The active request's source is a completed `KGForEdGlobal` run (completed
  `2026-10-13T09:07:32Z`) for document key
  `c939a3a9dcce92ed61d970f4599ced6f2ddc425d1220eeeab9828472b878d24d`:
  CAPS English Home Language, Foundation Phase, Grades R-3 (South Africa,
  Department of Basic Education, © 2011; source PDF
  `caps_english_hl_grade_3_fs.pdf`, 100 pages). The request names Funda Wande;
  the artifacts themselves name only DBE as author and IDinsight as provider.

## Stack and Tooling

- Python `>=3.13,<3.14`, `fastmcp==3.4.4`, Pydantic v2 / pydantic-settings;
  packaging and execution through `uv` with a committed `backend/uv.lock`
  (commands use `--locked`).
- Lint/format/type stack: ruff, black, isort, pylint, mypy (pydantic plugin),
  interrogate (docstring coverage), pre-commit with detect-secrets.
- Docs: MkDocs (`mkdocs.yml`, `docs/`), built strictly.
- Distribution: MCPB bundle via `kgfegmcp-build-mcpb` (`packaging/mcpb/`), plus
  Dockerfile / docker-compose.

## Structure and Boundaries

- `backend/src/kgfegmcp/packages/` — package builder, loader, validator,
  checksums, LP models/graph/validation, and LP input normalization
  (`normalization.py`, `normalization_models.py`, `normalization_sources.py`).
- `backend/src/kgfegmcp/cli/` — operator CLIs (prepare, build, validate, smoke,
  MCPB). `smoke_checks.py` and `smoke_access.py` pin specific existing
  framework/snapshot/node IDs as smoke targets.
- `backend/src/kgfegmcp/profiles/` — typed interpretation-profile models and
  loading.
- `config/profiles/<profile-id>/<version>/profile.json` and
  `config/prompts/<profile-id>/<version>/prompts.json` — per-framework semantic
  contract and optional prompt overlays.
- `data/input_artifacts/<set>/` — version-controlled, maintained rebuild inputs
  per framework: `delivery/` (normalized `as_lc_lp_nodes_<framework-id>.jsonl`,
  `as_lc_lp_relationships_<framework-id>.jsonl`), `detailed/` (20 evidence
  files incl. `lp_normalization_receipt.json` and
  `lp_relationship_provenance_index.json`), `additional/` (64
  `lp_relationship_provenance_shard_NN.json`), and `package_build.json`. Set
  names are short informal labels (`ghana_english`, `madhi_math`,
  `pratham_science`, …), some named after partner programmes rather than
  jurisdictions.
- `data/graph_packages/<framework-id>/<snapshot-id>/` — accepted, immutable
  runtime packages; the only data the runtime and MCPB consume (with
  profiles/prompts).
- `data/source_artifacts/` — git-ignored local preparation area: raw verified
  copies under `learning_progressions/<doc-key>/kgs/`, the local
  `copy_receipt.json`, and prepared outputs. Not present in a fresh clone.
- `docs/development/framework-package.md` — the authoritative operator guide
  for adding or updating a framework.

## Commands

- `uv --directory backend run --locked kgfegmcp-prepare-learning-progressions`
  — normalize verified local copies (`--framework-id`, `--receipt`,
  `--output-root` options) into
  `data/source_artifacts/learning_progressions/prepared/<framework-id>/`.
- `uv --directory backend run --locked --no-dev kgfegmcp-build-manifest --spec <abs-path> [--dry-run]`
  — build a pending package from a `package_build.json`-style spec.
- `uv --directory backend run --locked --no-dev kgfegmcp-validate-packages one --framework-id <id> --snapshot-id <id> [--read-only]`
  — validate; omitting `--read-only` persists pending→terminal.
- `uv --directory backend run --locked --no-dev kgfegmcp-stdio-smoke [--bundle-root <stage>]`
  — end-to-end STDIO smoke (repository or MCPB stage).
- `uv --directory backend run --locked --no-dev kgfegmcp-build-mcpb --stage-output ./dist/kgfegmcp-stage`
  — build an MCPB stage.
- `uv --directory backend run --locked pytest` — test suite (`make test` in
  `backend/` runs it with xdist and coverage).
- Lint: `uv --directory backend run --locked {ruff check .|black --check .|isort --check-only .|pylint src/kgfegmcp|mypy src/kgfegmcp|interrogate src/kgfegmcp}`.
- Docs: `uv --directory backend run --locked mkdocs build --strict` (after
  `uv --directory backend sync --locked --extra docs`).

## Conventions and Constraints

- Adding a framework is meant to be a data/configuration change. Generic Python
  changes are justified only for a genuinely new reusable capability, and
  `if framework_id == ...` branches in runtime code are prohibited.
- Do not weaken validation to admit one framework. Accepted packages are
  immutable; changes require a new snapshot/identity, never patching in place.
  Only terminal `passed` packages are served; keep one unambiguous current
  snapshot per framework.
- Preparation flow: copy only the 23 listed files from the external
  `<doc-key>/kgs/` into a repository-local source copy (never edit the
  external source), record a verified copy receipt (`receiptVersion: 1.0`,
  `status: verified`, framework mapping with `frameworkId`, `documentKey`,
  `frameworkCaseUuid`, per-file before/after/destination SHA-256 and size),
  then run preparation, build, read-only validate, persist, smoke. The local
  receipt may keep private source paths; package receipts must expose only
  relative paths and hashes.
- Preparation code is framework-generic: framework identity comes from the copy
  receipt mapping; no prior package for the framework is required.
- Framework/profile IDs follow `<country>-<authority>-<subject>-<grade-band>`
  slugs; snapshot IDs are `<framework-id>@<versionToken>+<hash>`.
- Current contract versions: manifest `1.1`, delivery `1.2`, source `1.0`,
  package revision `1`, profile schema `1.1` / version `2.0`, prompt-config
  schema `1.1` / version `2.0.0`, prompt library `1.4.0`.
- Profiles: `codeSearchPolicy.availability: none` is supported (Nigeria and
  Rwanda use it) and forbids code types, parent rules, and prefix search.
  `normalizedGrades` are free strings (no numeric constraint found);
  `allowMultiParent` is per profile. Existing rights blocks use
  `sourceLicense: Unknown` with `reviewStatus: provisional_operator_approved`.
- Remote is GitHub (`IDinsight/KGForEdGlobalMCP`) with no `.gitattributes`/LFS;
  maintained inputs and packages are committed as plain git blobs, each large
  detailed file appearing twice (input set and package). GitHub rejects
  individual files over 100 MB.
- Commits follow Conventional Commits; release-please manages versions and
  `CHANGELOG.md`.
- Never commit secrets; `.env*` is ignored, detect-secrets runs in pre-commit.

## External Systems and Data

- Source artifact directory (external, read-only):
  `/Users/tzz/Projects/private/idi/KGForEdGlobal/results/kg_for_ed/c939a3a9dcce92ed61d970f4599ced6f2ddc425d1220eeeab9828472b878d24d/kgs/`.
  All 23 required preparation files are present. Export schema
  (`learning_commons_export_schema_version` `2026-07-09`) and LP record key
  sets match the existing maintained inputs.
- CAPS graph shape: framework CASE UUID
  `7bb16abe-6d0a-5bb9-9a01-aeb7c4baeaa3`; 1,144 standards items (Grade 4,
  Term 16, Skill Area 48, Sub-strand 152, Skill 924) forming a strict tree
  Framework → Grade → Term → Skill Area → Sub-strand → Skill (1,144 hasChild
  edges, no multi-parent). Normalized types: Skill → `Standard`, others →
  `Standard Grouping`. Grade labels are `Grade R`, `Grade 1`, `Grade 2`,
  `Grade 3` (`Grade R` is a reception year). No item has a `statement_code`.
  `in_language: en`; `license: Unknown`; attribution cites DBE © 2011.
- LC/LP: 912 learning components, 1,204 supports edges; 2,057 AS/LC nodes and
  2,348 AS/LC relationships; 9,587 LP edges (2,879 `buildsTowards`, 6,708
  `relatesTo`) from 12,892 final claims (3,305 `no_relation`, 0
  `needs_review`). AS/LC and LP validation reports pass with no errors, no
  cycles, and no unresolved items or warning pairs; 8 generation failure
  attempts recorded with 0 unresolved failed pairs. This LP volume exceeds the
  combined 8,080 LP edges of all six current frameworks.
- Large source files: `lp_final_claims.json` ≈127 MB,
  `lp_relationship_provenance.json` ≈119 MB, `lp_relationships_relates_to.jsonl`
  ≈91 MB, `as_lc_kg_bundle.json` ≈40 MB, `as_kg_bundle.json` ≈35 MB. The
  existing maintained sets retain the first three (and both bundles) under
  `detailed/`; the largest current equivalents are CBSE's ≈46 MB and ≈41 MB.
  `as_lc_lp_kg_bundle.json` (≈282 MB) is copied for preparation but is not
  retained in maintained inputs or packages. The default resource source-read
  limit is 32 MiB; the 64 provenance shards exist to keep per-read size within
  limits.

## Testing and Verification Baseline

- Tests live in `backend/tests/` (pytest, pytest-bdd base `tests/features/`,
  xdist). `backend/tests/kgfegmcp/conftest.py` bootstraps the actual local
  packages under `data/graph_packages/` as the positive acceptance baseline.
- Several tests hard-code the current six-package population: exact counts of
  6 in `test_progression_discovery_text.py` (lines 79, 92, 93, 143), total LP
  edge count `8080` in `test_progression_lookup.py:130` and
  `test_progression_discovery.py:116`, and the six-entry
  `backend/tests/fixtures/progression_baseline.json` used by
  `test_progression_regressions.py`. Adding a served package changes these
  observed values.
- `backend/tests/fixtures/comparison/evaluation_queries.json` names specific
  frameworks for comparison evaluations.
- Tests must mock live-model/paid boundaries; the `costs-money` marker does not
  authorize calls. CI workflows: `.github/workflows/tests.yml`, `linting.yml`,
  `docs.yml`, `trufflehog-pr.yml`, `release-please.yml`.
- Package acceptance is structural/process integrity, not pedagogical
  certification.

## Relevant Existing Behavior

- The runtime discovers frameworks from `data/graph_packages` plus
  profiles/prompts; MCP tools include framework discovery, standards search,
  hierarchy context, learning components, comparison, and learning-progression
  search/get/traverse, with resources gated by profile rights policy.
- The MCPB build copies the whole `data/graph_packages` tree into the bundle
  with `KGFEGMCP_INVALID_PACKAGE_POLICY=fail`, so every served package ships in
  and must validate within the bundle.
- Framework-facing documentation lists or names current frameworks in
  `README.md`, `backend/README.md`, `docs/data/framework-catalog.md`,
  `docs/data/manifest.md`, `docs/data/profiles.md`,
  `docs/data/prompt-configs.md`, the "Retained input boundaries" table in
  `docs/development/framework-package.md`, and many guides/reference pages.

## Known Unknowns

- Funda Wande's role (partner, commissioning organisation, or programme label)
  is not recorded in the artifacts; it may matter for naming the input set,
  attribution, or rights wording.
- Source licence is `Unknown`; whether the existing provisional
  operator-approved rights posture applies to DBE CAPS content has not been
  established in this repository.
- Whether the oversized LP evidence files can be committed as-is to the GitHub
  remote, or need a different retention approach, is not settled by any
  existing project convention.
- The external run directory contains an empty `.lp_generation.lock` (dated
  2026-10-10) although `kg_run.json` records completion; it appears to be a
  stale lock, not an in-progress run.
- `data/source_artifacts/learning_progressions/` locally holds raw copies for
  five of the six current document keys (Ghana English's
  `e49a7926…` is absent); this is ignored local state and does not affect
  rebuilds from maintained inputs.

## Evidence

- `docs/development/framework-package.md` — integration workflow, contracts,
  retained inputs, preparation rules.
- `git show --name-status ea143f7 01a19d9` — precedent change set for adding
  an English framework.
- `backend/src/kgfegmcp/packages/normalization.py`,
  `normalization_models.py` — framework-generic preparation and receipt
  contract.
- `config/profiles/*/2.0/profile.json`,
  `backend/src/kgfegmcp/profiles/models.py` — profile conventions and
  code-availability rules.
- `data/input_artifacts/*/package_build.json` and `detailed/` listings —
  maintained input layout and sizes.
- External `kgs/as_standards_framework.json`, `as_standards_framework_items.jsonl`,
  `as_relationships_has_child.jsonl`, `as_lc_validation_report.json`,
  `lp_validation_report.json`, `lp_unresolved_items.json`, `kg_run.json` —
  CAPS graph facts (read only).
- `backend/tests/kgfegmcp/*.py`, `backend/tests/fixtures/progression_baseline.json`
  — six-package test assumptions.
- `backend/src/kgfegmcp/cli/build_mcpb.py`, `smoke_checks.py`,
  `smoke_access.py` — bundle scope and smoke targets.
- `git remote -v`, `.gitignore`, absence of `.gitattributes` — hosting and data
  tracking.
