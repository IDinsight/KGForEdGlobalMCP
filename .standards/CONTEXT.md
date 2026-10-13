# Project Context

## Project Baseline

- Knowledge Graph for Education Global MCP: a read-only, deterministic FastMCP server
  that validates, indexes and serves curriculum graph packages (Academic Standards,
  Learning Components, Learning Progressions). It makes no server-side LLM calls.
  Server/MCPB version 0.4.0.
- Six accepted mixed AS/LC/LP packages are served, one per framework, all with
  manifest `validation.status: passed`, `packageRevision: 1`, manifest `1.1`,
  delivery `1.2`, source `1.0`, profile version `2.0`:
  `ghana-nacca-primary-english-language-basic-1-3`,
  `ghana-nacca-primary-mathematics-basic-4-6`,
  `india-cbse-science-learning-framework-classes-9-10`,
  `india-tamil-nadu-tnscert-mathematics-classes-1-5`,
  `nigeria-nerdc-mathematics-primary-1-3`,
  `rwanda-reb-mathematics-lower-primary-1-3`.
- Every package file is committed today. On 2026-10-13 the six packages held 86
  declared files each (manifest + 2 delivery + 19 detailed + 64 `additional/`
  shards), about 671 MB on disk. `data/input_artifacts/` (six sets, 522 tracked
  files, also about 671 MB) holds byte-identical copies of the same artifacts plus a
  `package_build.json` spec per set. The local Git pack is 281 MiB because identical
  blobs are deduplicated. No single tracked file exceeds GitHub's 100 MB hard limit;
  the largest is CBSE `detailed/lp_final_claims.json` (46.4 MB).
- Measured totals by artifact kind across the six packages: `lp_final_claims.json`
  125.8 MB; `lp_relationships_builds_towards/relates_to.jsonl` 109.9 MB;
  `lp_relationship_provenance.json` 101.4 MB; the 64 shards 101.4 MB in total
  (largest single shard 0.9 MB); `as_lc_kg_bundle.json` 81.6 MB; `as_kg_bundle.json`
  67.5 MB; `as_entity_provenance.json` 27.8 MB; `as_standards_framework_items.jsonl`
  17.3 MB; delivery relationships 16.9 MB; `as_relationships_has_child.jsonl` 14.3
  MB; delivery nodes 4.5 MB; `lc_entity_provenance.json` 1.9 MB; all remaining
  summary, report, receipt, index and manifest files under 1 MB combined per kind.
- The current `additional/lp_relationship_provenance_shard_NN.json` files are
  full-fidelity partitions, not slimmed: each record is identical to its entry in
  `detailed/lp_relationship_provenance.json`, and the 64-shard union equals the
  original map (checked for Rwanda, 1,831 records; about 12.7 KB per record).

## Stack and Tooling

- Python `>=3.13,<3.14`, managed with `uv` from `backend/` (`pyproject.toml`,
  `uv.lock`). FastMCP server; Pydantic models; pytest with pytest-asyncio,
  pytest-bdd, pytest-xdist, pytest-randomly.
- Lint/format in CI: isort, black, interrogate, plus pylint/ruff/mypy configuration
  in `backend/pyproject.toml`.
- Docs: MkDocs (`mkdocs.yml`, `docs/`).
- Git LFS is not installed locally and the repository has no `.gitattributes`.
- Remote: `github.com/IDinsight/KGForEdGlobalMCP`.

## Structure and Boundaries

- `backend/src/kgfegmcp/packages/` — package loading (`loader.py`), validation
  (`validator.py`), LP evidence acceptance (`lp_validation.py`, `lp_models.py`,
  `lp_graph.py`), manifest models (`models.py`), checksums (`checksums.py`),
  builder (`builder.py`), LP normalization (`normalization*.py`).
- `backend/src/kgfegmcp/catalog/repository.py` — startup catalog; revalidates each
  package read-only and applies the invalid-package policy.
- `backend/src/kgfegmcp/resources/` — runtime artifact reads (`repository.py`), LP
  index/shard resolution (`lp.py`), resource service (`service.py`), rights gates
  (`policy.py`), `read_evidence` paging (`evidence.py`).
- `backend/src/kgfegmcp/services/learning_progressions.py` — progression tools,
  which use in-memory judgment projections only.
- `backend/src/kgfegmcp/cli/` — `build_manifests.py`, `validate_packages.py`,
  `prepare_learning_progressions.py`, `build_mcpb.py`, smoke CLIs.
- `config/profiles/`, `config/prompts/` — interpretation profiles and prompt
  overlays bound to packages by ID, version and SHA-256.
- `data/graph_packages/<framework-id>/<snapshot-id>/` — accepted packages served at
  runtime (`package_manifest.json`, `delivery/`, `detailed/`, `additional/`).
- `data/input_artifacts/<set>/` — committed rebuild inputs and `package_build.json`
  specs; not loaded by the server, image or bundle.
- `data/source_artifacts/` — git-ignored local preparation evidence (raw verified
  copies keyed by source document hash, copy receipts, scratch recovery trees; about
  11 GB locally). Not in a fresh clone.
- `Dockerfile`, `.dockerignore` (allowlist), `packaging/mcpb/`, `dist/` — hosted image
  and MCPB distribution.

## Commands

Run from the repository root unless noted.

- `uv --directory backend sync --locked --extra dev` — install dev environment.
- `uv --directory backend run --locked --no-sync pytest -rsPQ -m "not costs-money" tests`
  (CI runs the equivalent from `backend/` with coverage flags) — test suite.
- `uv --directory backend run --locked --no-dev kgfegmcp-stdio-smoke` — real STDIO
  server smoke; `--bundle-root <stage>` smokes an MCPB stage.
- `uv --directory backend run --locked --no-dev kgfegmcp-http-smoke --url <url>` —
  hosted/loopback HTTP smoke.
- `uv --directory backend run --locked kgfegmcp-validate-packages one --framework-id <id> --snapshot-id <id> --read-only`
  — read-only acceptance; omitting `--read-only` persists pending → terminal status.
- `uv --directory backend run --locked kgfegmcp-build-manifest --spec <abs-path> --dry-run`
  — propose a pending package from a build spec.
- `uv --directory backend run --locked kgfegmcp-prepare-learning-progressions` —
  normalize verified local copies under `data/source_artifacts/` into a preparation
  root.
- `uv --directory backend run --locked --no-dev kgfegmcp-build-mcpb --stage-output ./dist/kgfegmcp-stage`
  — build MCPB with a retained stage.
- `docker build -t kgfegmcp-http:local .` — hosted image.

## Conventions and Constraints

- Accepted packages are immutable. Changed artifact bytes or profile bytes need a new
  snapshot identity; do not patch a sealed package in place
  (`docs/development/framework-package.md`). The snapshot-ID suffix is recomputed from
  all declared checksums, so dropping, adding or editing any declared file changes the
  snapshot ID.
- The loader requires the package tree to match the manifest exactly: a missing
  declared file (`package_declared_file_missing`, `artifact_missing`), an undeclared
  file or directory, or a checksum mismatch is a blocking finding. For a `passed`
  package, any error aborts startup under both `fail` and `quarantine` policies
  (`catalog/repository.py`). Git-ignoring a declared file without changing the
  manifest/package contract therefore breaks a fresh clone, CI, the image and MCPB.
- The LP normalization receipt binds the hashes of every other artifact, and the
  provenance index binds the original map's SHA-256
  (`originalProvenanceSha256`) plus each shard's hash and entry count.
- Shard placement is `SHA256(UTF8(relationship_id))[0] modulo 64`, logical names
  `learningProgressionProvenanceShard00`–`63` (`resources/lp.py`).
- Configuration-driven design: no framework-specific branches in generic code;
  framework semantics live in profiles/manifests.
- Acceptance is structural/process integrity, not pedagogical certification.
  Preserve source truncation, warning pairs, eligibility notices and CBSE's one
  `needs_review` claim.
- Tests must mock live-model/paid boundaries; the `costs-money` marker never
  authorizes calls. Deployment and publication are user-owned.
- STDIO stdout is reserved for protocol traffic; logs go to stderr.
- Organization rules: no raw respondent PII/PHI and no real credentials in outputs or
  code.

## External Systems and Data

- Hosted deployment: Railway builds the root `Dockerfile` from `main`
  (`https://kg-for-ed-global-mcp.up.railway.app/mcp`). The image bakes in `config/`
  and the entire `data/graph_packages/` tree; a rollback restores code and data
  together. The build context is the Git repository, so whatever the server loads
  must be committed (or otherwise supplied to the build).
- MCPB bundle (`cli/build_mcpb.py`) copies the whole `data/graph_packages/` tree,
  excluding only OS/cache/bytecode files, and sets `KGFEGMCP_INVALID_PACKAGE_POLICY=fail`.
- Rights gates (`resources/policy.py`): all six manifests set
  `allowBulkResource: false`, so every `bulk_content` artifact (delivery nodes and
  relationships, both KG bundles, entity provenance maps, framework items, hierarchy
  relationships, LP split JSONL, final claims, the original provenance map and the
  shards) is denied through the generic artifact resource. Per-edge LP provenance and
  standard/LC provenance resources require reviewed rights plus full-text and
  standard-resource permission.
- Resource limits: default 32 MiB source-read and 8 MiB returned bytes
  (`config.py`); CBSE's original provenance map (40.9 MB) exceeds the source-read
  limit, which is why shards exist.
- There is no existing evidence archive outside GitHub. Raw copies under
  `data/source_artifacts/` are local only.

## Testing and Verification Baseline

- Tests live in `backend/tests/` (14 `test_*.py` modules under `tests/kgfegmcp/`,
  fixtures in `tests/fixtures/`). CI (`.github/workflows/tests.yml`) runs them on a
  plain checkout, so they see only committed data.
- `tests/kgfegmcp/conftest.py` `accepted_state` and `test_progression_traversal.py`
  bootstrap the real six packages, which requires every declared file, including the
  original provenance map and all shards.
- Tests that read full evidence directly: `test_progression_resources.py` compares a
  shard-served entry with the full `learningProgressionProvenance` map;
  `test_progression_acceptance.py` reads every artifact and copies whole packages to
  `tmp_path`; `test_progression_regressions.py` reads delivery files and
  `fixtures/progression_baseline.json`. `test_progression_lookup.py` proves exact LP
  queries never reopen source files.
- Smoke CLIs verify the exact tool/resource/template/prompt inventory over STDIO,
  HTTP and MCPB stages.

## Relevant Existing Behavior

- Startup (`app.py` → `bootstrap.py` → `CatalogRepository.load` →
  `GraphPackageLoader.load`) handles each declared artifact in one of two ways:
  - **Fully read and parsed:** `nodes`, `relationships`, `validationReport`, and,
    when LP is included, all nine LP artifacts (`learningProgressionBuildsTowards`,
    `RelatesTo`, `Provenance`, `Validation`, `Unresolved`, `Summary`, `FinalClaims`,
    `ProvenanceIndex`, `Normalization`) plus every shard. LP acceptance
    (`lp_validation.py`) checks that the shard union equals the original map,
    validates each provenance record, and reconciles provenance against final claims,
    the split JSONL, delivery edges, summary, report and unresolved evidence.
  - **Streamed for SHA-256 only:** `as_kg_bundle`, `as_lc_kg_bundle`,
    `as_entity_provenance`, `lc_entity_provenance`, `lc_dedup_groups`,
    `lc_generation_summary`, `as_relationships_has_child`, `as_standards_framework`,
    `as_standards_framework_items`, `as_unresolved_items`.
- After startup, LP data is kept in memory only as small projections
  (`LearningProgressionEvidence`: coverage counts and a per-edge `JudgmentProjection`
  with `confidence`, the first 512 characters of `claim.judgment.rationale`, and up to
  five 512-character warnings). Progression tools use only these projections plus a
  `provenance_uri`.
- Per-request file reads go through `ResourceRepository.read_artifact`, which rechecks
  size and SHA-256:
  - `learningProgressionSummary` and `learningProgressionProvenanceIndex`
    (`resources/lp.py`);
  - one shard for the `relationship/{id}/provenance` resource
    (`resources/service.py` `relationship_provenance`), selected via the validated
    index; the original map is referenced by hash only;
  - `learningComponentProvenance` (`lc_entity_provenance.json`) for
    `learning_component_provenance`;
  - `entityProvenance` (`as_entity_provenance.json`) for `standard_provenance`;
  - `unresolvedItems` and `validationReport`;
  - any rights-permitted artifact through the generic artifact resource.
- The `relationship/{id}/provenance` resource and `read_evidence` currently return the
  whole raw per-edge provenance record unfiltered. `docs/reference/resources.md`
  documents this as the complete original claim, judgment and trace: rationale,
  confidence, warnings, candidate evidence and references, and
  source/config/content/model/producer/checker hashes. A per-edge record's top-level
  fields are `approved_by`, `attribution_statement_template`,
  `candidate_artifact_byte_hashes`, `candidate_pairs_content_hash`,
  `candidate_summary_content_hash`, `claim` (`candidate`, `judgment`, `provenance`,
  `source_sfi_uuid`, `target_sfi_uuid`), `config_content_hash`, `doc_key`,
  `effective_lp_config_content_hash`, `final_claims_content_hash`,
  `model_configuration`, `model_configuration_content_hash`, `model_settings`,
  `model_settings_content_hash`, `relationship_identity_key`, `requests_content_hash`,
  `source_framework`, `upstream_content_hash`.
- Delivery LP relationship records already carry attribution, author, license,
  provider, relationship type and endpoint keys in their `properties`.
- Package lifecycle: `kgfegmcp-build-manifest` writes a `pending` package;
  `kgfegmcp-validate-packages` runs the same loader/validator as startup and persists
  `pending` → `passed`/`failed`/`quarantined`; terminal packages are never rewritten;
  only `passed` packages that pass read-only revalidation are served. The maintained
  rebuild is a manual operator procedure from `data/input_artifacts/<set>/package_build.json`
  (no Makefile target or CI job). `kgfegmcp-prepare-learning-progressions` refuses to
  write into `data/input_artifacts` or `data/graph_packages`.

## Known Unknowns

- The request places "entity provenance" and "hierarchy and framework items" in the
  archive-only set. `as_entity_provenance.json` and `lc_entity_provenance.json` back
  the existing `standard_provenance` and `learning_component_provenance` resources,
  and `validationReport`/`unresolvedItems` are read per request. Whether those
  resources should change, be removed or keep a slim runtime artifact is a scope
  decision not settled by the request.
- Slimming the per-edge provenance changes the documented "complete original"
  contract of the `relationship/{id}/provenance` resource and `read_evidence`. The
  intended public contract after slimming is not yet established.
- No archive location, owner, access model or retention policy outside GitHub exists
  in the repository or docs; the request asks for one to be decided.
- Whether `data/input_artifacts/` should remain committed, be slimmed or move to the
  archive is implied ("large input-set files") but its exact boundary is not stated.
- Existing Git history already contains all evidence blobs (281 MiB pack). Whether
  history rewriting is in or out of scope is not stated.
- Railway's build context and whether it could fetch an external archive at build
  time were not inspected beyond the documented "deployed from `main`" setting.

## Evidence

- `README.md`, `docs/development/framework-package.md`, `docs/data/graph-packages.md`,
  `docs/data/validation.md`, `docs/reference/resources.md`,
  `docs/operations/deployment.md`, `docs/getting-started/local-installation.md` —
  documented package contract, lifecycle, resources, deployment, sizes.
- `data/graph_packages/*/*/package_manifest.json` — artifact declarations, checksums,
  rights, validation status.
- `git ls-files data/`, `git count-objects -vH`, `stat`/`shasum` over package files —
  tracking, sizes, byte identity between `data/input_artifacts` and packages, shard
  vs original provenance equality.
- `backend/src/kgfegmcp/packages/loader.py` (`_CAPTURED_ARTIFACT_NAMES`, LP capture
  around line 1903), `packages/lp_validation.py` (`_projection`, index and provenance
  validation), `packages/lp_models.py`, `resources/lp.py` (`partition_name`),
  `resources/service.py`, `resources/policy.py`, `catalog/repository.py`,
  `config.py` — load, acceptance and serving behavior.
- `Dockerfile`, `.dockerignore`, `backend/src/kgfegmcp/cli/build_mcpb.py` — image and
  bundle contents.
- `.github/workflows/tests.yml`, `backend/pyproject.toml`, `backend/tests/` — CI and
  test dependencies on full evidence.
- `.gitignore` — `data/source_artifacts/` ignored; `data/input_artifacts/` explicitly
  not ignored.
