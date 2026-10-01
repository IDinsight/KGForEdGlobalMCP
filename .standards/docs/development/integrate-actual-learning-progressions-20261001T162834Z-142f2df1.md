<!-- STANDARDS
Artifact: DEVELOPMENT
Cycle: integrate-actual-learning-progressions-20261001T162834Z-142f2df1
-->

# Development Plan

`Cycle`: `integrate-actual-learning-progressions-20261001T162834Z-142f2df1` `Mode`: `STEPWISE`
`User Style`: `tony` `User Style Locked`: `true`
`Status`: `IN_PROGRESS` `Verification Cadence`: `AFTER_IMPLEMENTATION`
`Current Increment`: `NONE`

## Implementation Contract

- `Scope`: `.standards/docs/scope/integrate-actual-learning-progressions-20261001T162834Z-142f2df1.md`
- `Architecture`: `.standards/docs/specs/integrate-actual-learning-progressions-20261001T162834Z-142f2df1.md`
- `Request`: Integrate all six curricula's stored buildsTowards/relatesTo relationships with exact provenance, bounded queries, resources and educational workflows; remove obsolete hypothesis machinery and preserve useful standards/components behavior. Deployment remains user-owned.

## Build Steps

### DEV-001 — Copy and verify all six source sets

`Status`: `DONE` `Depends On`: `NONE`
`Acceptance`: `AC-001, AC-002, AC-004, AC-018`

**Goal**

Copy the 23 architecture-selected files per curriculum from the external source into the prescribed repository-local preparation directory before changing implementation.

**Affected Area**

data/source_artifacts/learning_progressions/<doc-key>/kgs/ and its copy receipt; the six source mappings in CONTEXT.md; existing package/profile identities.

**Expected Outcome**

All 138 inputs have recorded source/destination paths, sizes and SHA-256 values. Source hashes before/after copying equal destination hashes. Framework mapping and AS/LC delivery agreement are reconciled; LP counts agree with 3,039 buildsTowards and 5,041 relatesTo or drift is explicitly routed. External files remain unchanged.

**Self-Check**

PASS — copy and reconciliation completed using a local inline Python copy script (command: `python3 -u - <<'PY'`), followed by the separate read-only receipt verification command below. Working directory: `/Users/tzz/Projects/private/idi/KGForEdGlobalMCP`. Assessed HEAD: `0dc54cb635a3acd94b514e6affed808188941be9`; dirty-tree additions are the exact 138 destination paths/hashes in the receipt. Copy execution exited 0; separate verification exited 0.

- Receipt: `data/source_artifacts/learning_progressions/copy_receipt.json`, `sha256:e61d67b053a237e8fce6be86842f32ed5b398a145fb223410443d475419ae8ea`; includes every source/destination path, size, source-before/source-after/destination SHA-256, six framework CASE mappings, old package/snapshot/profile/prompt identities and protected baseline hashes.
- 138/138 files verified, 933,392,640 bytes total, all six mappings reconciled; source bytes unchanged after copying and at the final recheck. No selected symlinks or unexpected copied inputs.
- All six AS/LC delivery node and relationship hashes agree exactly with manifest-selected baseline delivery. All 8,080 exported LP IDs are unique and resolve to existing standards CASE UUIDs/node identities: 3,039 buildsTowards and 5,041 relatesTo. Split/combined signatures and accepted final claims agree; provenance covers exactly every edge and equals retained split metadata. relatesTo endpoint order is canonical.
- LP upstream report counts/status agree. CBSE retains one needs_review claim; Ghana Mathematics and Ghana English retain 141 and 10 unresolved-warning pairs respectively; other audited notice counts remain zero. Needs-review/nonrelationship claims were retained as evidence, not copied into accepted edge tables.
- All 296 protected runtime/configuration/package/preparation/CI/packaging files retain their pre-copy hashes. No production source/configuration/accepted package or existing data/input_artifacts files changed.
- Limitation: copy/reconciliation is Developer implementation feedback, not server package acceptance, Tester verification, semantic validation or pedagogical certification. No normalization, replacement package construction, model/paid-service call, or deployment occurred.

Exact read-only receipt verification command:

```sh
python3 -c '
import hashlib
import json
from pathlib import Path

def digest(path):
    with Path(path).open("rb") as stream:
        return "sha256:" + hashlib.file_digest(stream, "sha256").hexdigest()

root = Path.cwd()
receipt_path = root / "data/source_artifacts/learning_progressions/copy_receipt.json"
receipt = json.loads(receipt_path.read_text())
files = receipt["files"]
if len(files) != 138 or len(receipt["frameworks"]) != 6:
    raise RuntimeError("Receipt coverage mismatch")
for entry in files:
    source = Path(entry["sourcePath"])
    destination = root / entry["destinationPath"]
    if digest(source) != entry["sourceSha256Before"] or digest(destination) != entry["destinationSha256"] or entry["sourceSha256After"] != entry["sourceSha256Before"]:
        raise RuntimeError("Source or destination hash drift")
    if source.stat().st_size != entry["sizeBytes"] or destination.stat().st_size != entry["sizeBytes"]:
        raise RuntimeError("Source or destination size drift")
for relative, expected in receipt["protectedBaselineSha256Before"].items():
    if digest(root / relative) != expected:
        raise RuntimeError("Protected baseline changed")
actual_paths = {str(p.relative_to(root)) for p in (root / receipt["destinationRoot"]).glob("*/kgs/*") if p.is_file()}
if actual_paths != {e["destinationPath"] for e in files}:
    raise RuntimeError("Copy inventory mismatch")
if sum(e["sizeBytes"] for e in files) != 933392640 or receipt["totals"] != {"buildsTowards": 3039, "relatesTo": 5041}:
    raise RuntimeError("Copied totals mismatch")
if next(Path(".").glob(".standards/docs/development/*.md")).is_file():
    print(json.dumps({"status": "passed", "files": len(files), "bytes": receipt["totalBytesCopied"], "frameworks": len(receipt["frameworks"]), "totals": receipt["totals"], "protectedFilesUnchanged": len(receipt["protectedBaselineSha256Before"]), "assessedHead": receipt["assessedHead"], "receiptSha256": digest(receipt_path)}, sort_keys=True))
'
```

**Implementation Notes**

The raw inputs remain in the architecture-prescribed `data/source_artifacts/learning_progressions/<doc-key>/kgs/` directories. User explicitly requested local-only retention: the repository-root `.gitignore` rule `/data/source_artifacts/` excludes the raw copies and local copy receipt from commits. Required normalized preparation inputs and accepted runtime package evidence remain version-controlled under their existing unignored roots. This bookkeeping choice does not change approved implementation intent or authorize DEV-002. Ignore-rule self-check passed from the repository root: `git check-ignore --stdin` covered all 139 copied files/receipt; `git ls-files -- data/source_artifacts` returned no tracked files; representative input/profile paths were not ignored. `git status --short` no longer reports the source-artifacts directory. Assessed `.gitignore` hash: `sha256:d1c7e552a4829a5985687439ebd54c730e42137f81e6d19bcd1665d1fc2c39f3`. `node .standards/bin/check.mjs` passed; the DEV-002 continuation blocker remains unchanged. Their receipt intentionally retains external absolute source paths for local preparation traceability; later public normalization receipts must sanitize them. No later step was started.


### DEV-002 — Extend immutable package and delivery contracts for LP

`Status`: `PENDING` `Depends On`: `DEV-001`
`Acceptance`: `AC-002, AC-003, AC-010, AC-018, AC-019`

**Goal**

Represent stored LP edges and their required artifact/count/capability declarations in the existing package and graph models.

**Affected Area**

packages/models.py, wire.py, decoder.py, builder.py; graph/models.py; domain enums/identifiers and regexes.py where required.

**Expected Outcome**

Manifest 1.1/delivery 1.2/source 1.0 contracts recognize buildsTowards and relatesTo with exact standard endpoints, dedicated evidence names, strict LP counts and availability flags. Builder accepts the new safe delivery filenames and declared evidence. Non-LP packages remain representable under the new schemas; AS/LC fields keep their meanings.

**Self-Check**

Changed-module formatter/lint/type checks and local model/decoder/builder sanity checks for valid LP/non-LP inputs and invalid labels/IDs/counts. Full runtime activation waits for accepted replacements. Evidence not yet run. At execution, persist actual commands, repository working directory, assessed HEAD/changed-content hashes, outcomes and limitations here.

### DEV-003 — Prepare normalized LP inputs and verified provenance partitions

`Status`: `PENDING` `Depends On`: `DEV-002`
`Acceptance`: `AC-001, AC-002, AC-004, AC-010, AC-011, AC-012`

**Goal**

Add a reproducible preparation command in the existing CLI family consuming only the verified local copies.

**Affected Area**

cli preparation module and pyproject.toml script entry; packages normalization helpers; local generated delivery/evidence/index/receipt outputs.

**Expected Outcome**

Original node bytes and AS/LC relationship prefix remain exact. Appended LP wire records are sorted, resolve exact CASE endpoints and reconcile with split/combined/provenance inputs. All 64 canonical provenance partitions and index preserve original entries. Runtime normalization receipts expose relative identities/hashes without private source paths; original evidence remains intact.

**Self-Check**

Run command help and deterministic preparation on copied inputs; compare repeated output hashes, AS/LC bytes, complete LP ID/type/endpoint/metadata reconciliation, partition placement/union/deep equality and sanitized receipt content. Never regenerate producer/checker judgments. Evidence not yet run. At execution, persist actual commands, repository working directory, assessed HEAD/changed-content hashes, outcomes and limitations here.

### DEV-004 — Accept LP integrity independently and retain small query projections

`Status`: `PENDING` `Depends On`: `DEV-003`
`Acceptance`: `AC-003, AC-004, AC-010, AC-011, AC-012, AC-018, AC-019`

**Goal**

Extend the package acceptance boundary to verify LP records, evidence and topology independently of preparation.

**Affected Area**

packages/validator.py, loader.py and focused evidence models/helpers; LoadedGraphPackage/catalog runtime projections.

**Expected Outcome**

Malformed/duplicate/pair-conflicting edges, invalid endpoints/attribution/confidence, missing or mismatched provenance, counts, partitions and builds cycles cannot pass acceptance. AS/LC report comparison remains subgraph-specific. hasChild cycle checks remain separate. Runtime keeps immutable small judgment/coverage projections and releases rich maps.

**Self-Check**

Static/type checks plus bounded temporary-package sanity checks exercising successful loading and representative integrity/cycle/provenance failures without damaging terminal baseline packages. Validate the large original evidence without bypassing resource policies. Evidence not yet run. At execution, persist actual commands, repository working directory, assessed HEAD/changed-content hashes, outcomes and limitations here.

### DEV-005 — Build six accepted replacement snapshots in a separate root

`Status`: `PENDING` `Depends On`: `DEV-004`
`Acceptance`: `AC-002, AC-003, AC-004, AC-017, AC-018, AC-019, AC-020`

**Goal**

Publish fresh interpretation/prompt configuration contracts and prepare all six replacement packages without overwriting terminal baseline directories.

**Affected Area**

profiles/models.py and configuration validation; prompts/models.py configuration schema/overlay contracts; new config/profiles and config/prompts version 2.0 trees; separate package preparation root.

**Expected Outcome**

Profile/prompt-config schemas advance to 1.1, preserve useful interpretation/rights/guidance, remove progressionHeuristics and hypothesis overlays, and allow the three designed overlays. Replacement revision-1 snapshots retain source version/current status and required runtime artifacts. All six pass persisted atomic acceptance and read-only revalidation before activation.

**Self-Check**

Load all fresh configurations; build/accept/revalidate each replacement with established CLI commands; compare counts, exact AS/LC IDs/text/relationships, generated LP metadata, complete declared evidence and old identity receipt. Old terminal packages remain byte-identical until retirement in DEV-017. Evidence not yet run. At execution, persist actual commands, repository working directory, assessed HEAD/changed-content hashes, outcomes and limitations here.

### DEV-023 — Replace all six package preparation sets and build specifications

`Status`: `PENDING` `Depends On`: `DEV-005`
`Acceptance`: `AC-002, AC-003, AC-017, AC-018, AC-022, AC-027`

**Goal**

Make data/input_artifacts the maintained, reproducible preparation inputs for the six accepted AS/LC/LP replacements, then remove superseded preparation files and stale build references.

**Affected Area**

data/input_artifacts/{ghana_english,ghana_math,madhi_math,nigeria_math,pratham_science,rwanda_math}/delivery/, detailed/ and package_build.json; existing preparation CLI output selection as needed.

**Expected Outcome**

After all six replacements pass acceptance in the separate preparation root, each input set contains the corresponding normalized as_lc_lp_nodes_<token>.jsonl and as_lc_lp_relationships_<token>.jsonl delivery files, retained required AS/LC and LP detailed evidence, all 64 provenance partitions, index and sanitized normalization receipt. Updated package_build.json files reference profile version 2.0, the new delivery filenames and every required declared artifact, preserve authoritative framework/source/version metadata, and support rebuilding into a separate preparation root with repository-relative input paths. No preparation input depends on the external source folder or an old configuration version.

Verify all replacement inputs and specifications before deleting the corresponding superseded delivery files, outdated build references or obsolete preparation-only artifacts. Preserve unchanged required AS/LC evidence, unrelated files, and the exact source copies/copy receipt under data/source_artifacts/learning_progressions. Old preparation paths/hashes and replacement identities are recorded in implementation evidence; old versions remain recoverable in Git. input_artifacts and source_artifacts remain outside runtime discovery and MCPB staging. This step does not modify sealed accepted packages or user documentation.

**Self-Check**

Inventory each old/new input set and record hashes before cleanup. Validate all six build specifications and rebuild/revalidate their packages in an isolated preparation root using the established build/validation CLI, comparing exact manifest-derived snapshot/profile/artifact identities and counts with the accepted replacements from DEV-005. Check that every referenced path exists, complete evidence/shard declarations are present, no stale profile-version or delivery reference remains in the six specifications, and superseded files are absent while required AS/LC content and source copies are unchanged. Evidence not yet run. At execution, persist actual commands, repository working directory, assessed HEAD/changed-content hashes, outcomes and limitations here.

### DEV-012 — Implement exact LP selection and shared evidence results

`Status`: `PENDING` `Depends On`: `DEV-023`
`Acceptance`: `AC-005, AC-009, AC-010, AC-012, AC-018`

**Goal**

Introduce LearningProgressionsService with shared typed request/result, route, selector, rights, excerpt, evidence-identity and byte-budget helpers, then implement exact lookup.

**Affected Area**

services/learning_progressions.py and focused typed models; errors.py; accepted catalog/GraphStore and existing standards/rights helpers.

**Expected Outcome**

Exact LP lookup pins one package/snapshot and returns original stored edge/endpoints, generated judgment projection and resource links. Missing/non-LP IDs, missing/ambiguous standards, unavailable capability and invalid requests have distinct typed failures. Excerpts, semantic/origin notices and 1 MiB encoded result ceiling follow the architecture.

**Self-Check**

Changed-module static/type checks and local exact-ID sanity calls against prepared packages, including non-LP ID/unavailable/rights/oversized cases. Inspect stable package/profile/manifest/artifact identities and excerpt flags. Evidence not yet run. At execution, persist actual commands, repository working directory, assessed HEAD/changed-content hashes, outcomes and limitations here.

### DEV-013 — Implement direct connections and filtered paged discovery

`Status`: `PENDING` `Depends On`: `DEV-012`
`Acceptance`: `AC-006, AC-007, AC-009, AC-010, AC-012`

**Goal**

Expose directional direct links, symmetric related links and explicit endpoint-conjunction discovery with deterministic stateless continuation.

**Affected Area**

LearningProgressionsService/models, existing profile facet/standard lookup helpers and cursor conventions.

**Expected Outcome**

Direct results distinguish incoming/outgoing builds from related concepts and retain canonical orientation/IDs. Discovery validates all selectors/facets and either/both/source/target semantics. Ordering, bound cursor identity/filter fingerprint, examined-candidate advancement, 25/100 pages, 5,000 work budget and byte stopping report honest completeness and empty results.

**Self-Check**

Static/type checks and local calls covering both relates endpoints, same-endpoint filter conjunction, valid/invalid facets/selectors, successive pages, mismatched/stale cursors, zero-match work-limited pages and byte-limit progress. Use temporary in-memory inputs where actual packages cannot exercise a bound. Evidence not yet run. At execution, persist actual commands, repository working directory, assessed HEAD/changed-content hashes, outcomes and limitations here.

### DEV-014 — Implement bounded upstream and downstream traversal

`Status`: `PENDING` `Depends On`: `DEV-013`
`Acceptance`: `AC-008, AC-009, AC-010, AC-018`

**Goal**

Return a deterministic builds-only reachable subgraph with exact stored edges and explicit frontier/completeness.

**Affected Area**

LearningProgressionsService traversal helpers/models; existing label adjacency indexes.

**Expected Outcome**

Breadth-first traversal preserves branching/merging edges and upstream stored orientation. Depth 8/12, nodes 100/250, edges 100, work 5,000 and byte limits are enforced before excess work/allocation; depth-frontier inspection consumes budget. Distances, scopeComplete, graphExhausted and reasons distinguish bounded evidence from global exhaustion.

**Self-Check**

Static/type checks and local branch/merge/cycle/depth/node/edge/work/byte sanity checks; inspect every hop as a buildsTowards edge and confirm hierarchy/support isolation. No traversal cursor or inferred direct edge. Evidence not yet run. At execution, persist actual commands, repository working directory, assessed HEAD/changed-content hashes, outcomes and limitations here.

### DEV-015 — Implement bounded connecting paths without losing alternatives

`Status`: `PENDING` `Depends On`: `DEV-014`
`Acceptance`: `AC-008, AC-009, AC-010`

**Goal**

Find directed simple builds paths between two exact standards using breadth-first partial paths.

**Affected Area**

LearningProgressionsService path helpers and typed path request/result models.

**Expected Outcome**

Paths retain alternatives through merging branches, ordered by hop count then edge-ID tuple. Default depth 6/paths 3, maxima 12/20, work/queue 5,000 and byte ceilings apply. Per-path visited sets prevent loops; target paths do not expand. Missing/invalid endpoints, same endpoint and incomplete zero-path search are explicit.

**Self-Check**

Static/type checks and temporary DAG/cycle sanity calls for multiple paths, direction, deterministic order and each bound. Validate every reported hop against accepted edges and inspect incomplete versus exhausted absence. Evidence not yet run. At execution, persist actual commands, repository working directory, assessed HEAD/changed-content hashes, outcomes and limitations here.

### DEV-016 — Expose exact LP provenance and sanitized summary resources

`Status`: `PENDING` `Depends On`: `DEV-015`
`Acceptance`: `AC-004, AC-010, AC-011, AC-012`

**Goal**

Extend resource URI, repository/policy and service boundaries for per-edge provenance and LP summary using accepted partitions.

**Affected Area**

resources/uri.py, models.py, policy.py, service.py and mcp/resources/register.py; existing relationship/artifact resources.

**Expected Outcome**

Two new resource templates resolve accepted package-local identities. Exact provenance returns the original entry with canonical content/source hashes; sanitized summary retains counts/notices/evidence links. Artifact exposure classes follow the design, partition access requires validated membership, and existing rights/32 MiB source/8 MiB return limits remain enforced.

**Self-Check**

Static/type checks and local exact resource reads including CBSE partition access, unknown edge/artifact, denied rights, low configured byte limits, content/source hash agreement and summary redaction. Inspect retained unresolved/needs_review evidence without returning it as edges. Evidence not yet run. At execution, persist actual commands, repository working directory, assessed HEAD/changed-content hashes, outcomes and limitations here.

### DEV-017 — Activate accepted replacements and register the five LP tools

`Status`: `PENDING` `Depends On`: `DEV-016`
`Acceptance`: `AC-005, AC-006, AC-007, AC-008, AC-009, AC-017, AC-018, AC-019, AC-020, AC-021`

**Goal**

Wire the shared service and thin read-only MCP tools, truthful package capabilities and separate statistics; atomically replace active sealed data/configuration only after all six replacement checks pass.

**Affected Area**

bootstrap.py, services exports/capabilities/statistics, catalog metadata where needed, mcp/register.py and new LP tool adapters; active data/graph_packages and config roots.

**Expected Outcome**

One GraphStore/runtime per package exposes five new tools with service/protocol bounds and stable masked errors. Active roots contain one current new snapshot per framework and fresh profile/prompt configs; old terminal directories are retired rather than rewritten. Old progression tool/service/models/bootstrap/exports are removed. LP availability/counts match accepted evidence; useful AS/LC routing, DAGs, search and supports remain usable.

**Self-Check**

Bootstrap only repository roots; inspect five schemas/annotations/error mapping and exact tool inventory. Exercise representative LP calls and AS/LC discovery/search/context/support/statistics/comparison across six frameworks. Compare pre-retirement old hashes and accepted replacement identities. Full shared transport smoke runs after prompts are complete. Evidence not yet run. At execution, persist actual commands, repository working directory, assessed HEAD/changed-content hashes, outcomes and limitations here.

### DEV-018 — Add the teaching-sequence prompt workflow

`Status`: `PENDING` `Depends On`: `DEV-017`
`Acceptance`: `AC-010, AC-013, AC-021`

**Goal**

Render the deterministic teaching-sequence workflow and its thin MCP prompt adapter.

**Affected Area**

prompts/definitions.py, models.py, service.py and focused mcp/prompts adapters/registration; public prompt version 1.3.0.

**Expected Outcome**

Topic or exact-standard selection pins the package, retains up to three standards and instructs the designed bounded direct/downstream/path/LC/provenance retrieval before composition. Related concepts remain separate; generated pedagogy, sparse/partial/denied evidence and stored origin are explicit. No LLM runs on the server.

**Self-Check**

Static/type checks and local prompt rendering for topic/exact selection, grade filters, language/context bounds, unavailable capability and rights. Inspect exact tool arguments, retrieval/provenance caps, citations and disclosures. Evidence not yet run. At execution, persist actual commands, repository working directory, assessed HEAD/changed-content hashes, outcomes and limitations here.

### DEV-019 — Add the support-planning prompt workflow

`Status`: `PENDING` `Depends On`: `DEV-018`
`Acceptance`: `AC-010, AC-014, AC-021`

**Goal**

Render a target-standard support workflow grounded in bounded incoming/related/upstream evidence and components.

**Affected Area**

Shared prompt models/definitions/service and MCP prompt adapters/registration.

**Expected Outcome**

Exact target and teacher context drive designed retrieval: incoming/related pages, depth-3 upstream evidence and bounded LC/provenance retention. Caller observations remain distinct from generated review/practice suggestions; no diagnosis or mandatory prerequisites are claimed.

**Self-Check**

Static/type checks and local rendering with valid/malformed target/context, rights and unavailable/empty evidence instructions. Inspect designed depth/node/edge/page/component/provenance caps and accurate observation/suggestion separation. Evidence not yet run. At execution, persist actual commands, repository working directory, assessed HEAD/changed-content hashes, outcomes and limitations here.

### DEV-020 — Add the curriculum-review prompt workflow

`Status`: `PENDING` `Depends On`: `DEV-019`
`Acceptance`: `AC-004, AC-010, AC-015, AC-021`

**Goal**

Render bounded curriculum inspection with explicit endpoint scope, coverage metadata and exact cited judgments.

**Affected Area**

Shared prompt models/definitions/service and MCP prompt adapters/registration.

**Expected Outcome**

Selectors/facets use the query contract; summary/statistics, up to three pages and ten exact provenance reads support a clearly bounded reviewed subset. Warnings/needs_review, unknown denominators and structural-only validation are visible; absence is not curriculum omission or cross-framework alignment.

**Self-Check**

Static/type checks and local rendering for selectors/either/both/source/target/facets and invalid inputs. Inspect exact discovery arguments, page/inspection caps, artifact links and distinction between package totals and reviewed subset. Evidence not yet run. At execution, persist actual commands, repository working directory, assessed HEAD/changed-content hashes, outcomes and limitations here.

### DEV-021 — Integrate stored evidence into existing prompts and remove hypothesis remnants

`Status`: `PENDING` `Depends On`: `DEV-020`
`Acceptance`: `AC-010, AC-016, AC-017, AC-018, AC-021`

**Goal**

Extend four useful teaching/study workflows through shared bounded LP evidence guidance and finish removal of all obsolete prompt/configuration logic.

**Affected Area**

prompts/definitions.py, models.py, service.py; mcp/prompts registration/arguments; existing teacher/student/multigrade/administrator/comparison adapters and configs.

**Expected Outcome**

Teacher guide, study support, handbook and multigrade retrieve optional stored links/provenance/LC evidence after exact selection while preserving existing outputs. Administrator/comparison notices remain truthful. No old hypothesis prompt, guidance type, candidate fallback or obsolete heuristic/overlay/reference expectation remains in active runtime/configuration. Historical source-origin text and useful LC/comparison inference remain.

**Self-Check**

Static/type checks and render every retained/new prompt; inspect bounded shared retrieval and unavailable/partial behavior. Targeted symbol/config searches plus exact nine-prompt inventory establish removal; scope documentation replacements as Documenter-owned work. Evidence not yet run. At execution, persist actual commands, repository working directory, assessed HEAD/changed-content hashes, outcomes and limitations here.

### DEV-022 — Align local transport checks, CI and retained MCPB distribution

`Status`: `PENDING` `Depends On`: `DEV-021`
`Acceptance`: `AC-018, AC-019, AC-021, AC-022, AC-023, AC-024, AC-025`

**Goal**

Update executable smoke/CI/distribution integration and record final implementation-level evidence before independent Tester handoff.

**Affected Area**

cli/smoke_checks.py, stdio_smoke.py/http_smoke.py as needed, build_mcpb.py, packaging configuration and .github/workflows/tests.yml.

**Expected Outcome**

Shared exact inventory is 17 tools, nine prompts, one fixed resource and 14 templates. Smoke identities resolve replacement snapshots and inspect representative LP evidence. CI includes data/config/package changes and rejects pytest no-collection success. Retained MCPB stage contains complete active runtime evidence and no source-preparation/external/retired inputs. Local transports and staged runtime run without model/paid calls or deployment.

**Self-Check**

Run applicable established formatting/lint/type/docstring checks, all six read-only package revalidations, STDIO and local HTTP smoke, MCPB build/retained-stage smoke and stage closure inspection. Run existing tests if present; record absent tests as a Tester-owned gap, never as passing verification. Record actual commands/content identities/results/limitations before workflow check and independent Tester handoff. Evidence not yet run. At execution, persist actual commands, repository working directory, assessed HEAD/changed-content hashes, outcomes and limitations here.

## Plan Notes

- Approval: user approved the revised 17-step plan and persisted tony style, and explicitly directed DEV-001 only. Style is locked for this cycle; STEPWISE pauses remain in effect.
- Entry: STANDARD/BROWNFIELD, DEVELOPING from Architect; no recovery frames, baseline-reconciliation entries or outstanding obligations. Initial workflow check passed. DEV-001 is DONE with verified copy evidence; STEPWISE is paused before DEV-002. No later step has started.
- Sufficiency: scope/design establish LP meanings, attribution, eligibility, package/profile revisions, normalization/partition algorithm, five query schemas, selectors/facets, bounds/cursors/completeness/errors, rights/resources, prompt workflows, removal and operational boundaries. Existing package/catalog/GraphStore/standard selection/resource/prompt/CLI machinery supports the chosen boundaries. Helper/module factoring remains reversible Developer work.
- STEPWISE: explicit approval covers this plan and user style tony. First approval locks that style. Execute exactly one dependency-ready step, record its outcome/self-check, then persist a continuation blocker and wait. Verification remains AFTER_IMPLEMENTATION, independent of these pauses.
- Preflight: all 23 required files are present for each of six source mappings (138 files, 933,392,640 bytes total), with no selected source symlinks. Copy-time exact hashes and edge reconciliation remain DEV-001 work; this preflight is not copy/acceptance evidence. The local backend Python environment exists.
- Plan revision: user requested replacing the legacy data/input_artifacts sets and build specifications. DEV-023 runs after DEV-005 and before DEV-012, preserving the architecture-prescribed raw-copy location and accepted-package boundaries. The revised 17-step plan was explicitly approved before DEV-001 began.
- Preserve source files and old sealed package/profile identities. Raw preparation copies stay outside runtime/distribution roots. Required runtime evidence is retained in accepted packages. During schema migration the incomplete development checkout may not bootstrap until replacement activation; do not deploy partial work or introduce legacy decoders/aliases to hide that boundary.
- Developer owns production implementation and executable integration/CI commands, not formal test suites or user documentation. Use local temporary/ad hoc implementation sanity checks; Tester creates meaningful offline formal cases and owns AC-023 through AC-025 evidence. Architecture requests for synthetic cases are exercised as implementation feedback here and independently formalized by Tester. AC-020 is established by Architect; AC-026/AC-027 remain Documenter-owned, supported by these persisted contracts/receipts/actual evidence.
- Identifier gaps are retained: the ID tool reserved numbers referenced in the draft before those headings were written. Preserve existing step identities; dependency order is the heading order, not an assumption of contiguous numbering.
- No live LLM/paid-service calls, producer/checker regeneration, model sampling, deployed endpoint changes or publication. Existing LC/comparison generated-origin evidence stays intact.
- Resume: first approved step DEV-001 is DONE. Next approved dependency-ready step is DEV-002; user continuation is required before starting it. Re-read its relevant package/delivery contracts and retained receipts.
- Full handoff requires all steps DONE, locked style, satisfactory self-checks, resolved owned blockers/obligations and workflow check. Save current identities and actual evidence for a separate independent Tester chat. Do not fabricate tests or claim formal acceptance based on Developer checks.
