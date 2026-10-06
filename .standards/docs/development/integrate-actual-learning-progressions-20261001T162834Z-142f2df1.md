<!-- STANDARDS
Artifact: DEVELOPMENT
Cycle: integrate-actual-learning-progressions-20261001T162834Z-142f2df1
-->

# Development Plan

`Cycle`: `integrate-actual-learning-progressions-20261001T162834Z-142f2df1` `Mode`: `STEPWISE`
`User Style`: `tony` `User Style Locked`: `true`
`Status`: `IN_PROGRESS` `Verification Cadence`: `AFTER_IMPLEMENTATION`
`Current Increment`: `NONE`

## Frame 2 Size-Correction Revision — approved 2026-10-06

Architect returned Frame 2 (RESUME from ARCHITECTING) with the user-selected result-size correction in the architecture's "Result-size correction" section. Restore Suspended Assignment 3 (DEVELOPMENT/NONE). This changes approved behavior of DEV-012 (all five tools' metadata) and DEV-015 (later-path handling), so the plan returns to PROPOSED for explicit approval. STEPWISE, locked style tony, AFTER_IMPLEMENTATION and Current Increment NONE are unchanged. Frame 1 is unchanged.

| Order | Step | Revised observable outcome |
|---|---|---|
| 1 | DEV-012 (reopened) | LP query metadata.artifacts lists exactly nodes, relationships, learningProgressionProvenance and learningProgressionProvenanceIndex (logical name, sha256, artifact URI), sorted by logical name, plus a fixed artifactInventoryNotice pointing to manifestUri; manifest hash/URI, package/profile identity and all other fields unchanged. Re-measure real envelopes of all five tools and rerun the DEV-013/014 feedback against the smaller metadata. DEV-013/014 algorithms and cursors do not change and stay DONE unless that rerun shows their outcome unmet. |
| 2 | DEV-015 (revised) | After at least one selected path, the next path that does not fit (alone or combined) stops selection: return selected paths, add byte_limit, scopeComplete/graphExhausted false, and set nextUnreturnedPath (ProgressionPath shape, IDs only, otherwise null); its edges stay out of the tables. Only an unfittable first path raises progression_result_too_large, now with that path's ordered relationship IDs in bounded details. The path notice explains later paths may exist beyond the stop and the recovery routes. |
| 3–5 | DEV-024, DEV-025, DEV-022 | Unchanged. |

Local implementation choices (Developer-owned, within the design):
- Reservation for nextUnreturnedPath uses the pinned package's longest JSON-encoded builds relationship ID and endpoint node ID, precomputed once per package at service construction beside the existing immutable adjacency, times max_depth / max_depth+1. Reserving the 1,024-character type maxima would consume about 51k characters and undo the correction.
- The stopped path stays counted in frontier.queuedStateCount (existing DEV-015 frontier behavior); nextUnreturnedPath additionally identifies it.
- The later-path standalone oversize check is removed (it is no longer an error case), superseding the earlier DEV-015 wording edit for that check.

Self-check for both steps: offline Developer feedback at production ceilings, including the Architect's verification target: for every connected ordered pair in all six packages, a max_paths 1 request with depth equal to the shortest stored path length (up to the real 8 hops) returns that complete path under both ceilings; and the known Tamil Nadu default request returns its 2-hop path with byte_limit and nextUnreturnedPath. Plus existing regression tests, changed-module static checks, and real FastMCP text-only calls.

Formal tests: some Tester-owned cases encode the superseded contract and are expected to fail (for example the full artifact list in test_progression_lookup and later-path rejection in test_paths_oversized_entry_rejected). Developer does not edit them. Proposed handling: record each such failure as superseded-contract evidence in the step's self-check, finish DEV-012 and DEV-015, then route one scoped VERIFICATION correction to Tester for both before DEV-024, instead of two separate round trips. Any other formal failure is treated as an implementation defect.

## Current Recovery Plan — approved 2026-10-06

This section supersedes historical completion, next-action, surface and recovery-route claims below. Recovery Frame 1 is SCOPING-owned, from/resuming at AWAITING_USER_SIGNOFF, with RerunThrough SYNCHRONIZING. Developer is a downstream rerun and does not change that frame. The revised scope has 37 current acceptance IDs; architecture establishes the new text, evidence and workflow contracts.

User explicitly approved this material revision and directed DEV-012 on 2026-10-06. Preserve STEPWISE, locked User Style tony, AFTER_IMPLEMENTATION and Current Increment NONE. Fourteen original steps are DONE after DEV-013 recovery. DEV-013/014/015/022 were reopened for recovery; DEV-024 and DEV-025 are added. Their old self-checks remain historical evidence. Tester corrected the scoped discovery cases, popped only nested Frame 2 and RESUMED Developer. Developer reconciled that return and reran the affected checks; DEV-013 is DONE. User authorized DEV-014; Tester corrected the scoped traversal/shared-path fixtures, popped only nested Frame 2 and RESUMED Developer. Developer restored Suspended Assignment 2, reconciled that return and reran the affected checks; DEV-014 is DONE. User authorized DEV-015; real data disproved the path size design, so ARCHITECTURE Frame 2 was routed and returned with the user-selected size correction (see Frame 2 Size-Correction Revision). DEV-012 (reopened) and DEV-015 are DONE under it. A scoped VERIFICATION Frame 2 now routes the superseded formal cases to TESTING; Suspended Assignment 4 preserves the remaining DEVELOPMENT/NONE work. DEV-024/025/022 remain PENDING. Current feedback and resume directions are recorded in Plan Notes.

| Order | Step | Observable recovery outcome |
|---|---|---|
| 1 | DEV-012 | Canonical JSON text equals structured output; one shared encoder counts the entire tool envelope against 1 MiB and 100,000 characters; exact results disclose limits and usable evidence recovery. |
| 2 | DEV-013 | Direct/search pages admit whole entries under both ceilings and return real replayable cursors without lost edges or zero-progress loops. |
| 3 | DEV-014 | Traversal preserves coherent branches, stored direction and honest frontier/completeness under both ceilings; no continuation is offered. |
| 4 | DEV-015 | Paths preserve complete ordered alternatives and honest partialness under both ceilings; no continuation is offered. |
| 5 | DEV-024 | read_evidence dispatches only Catalog/the fourteen native URI families to ResourceService, then returns faithful UTF-8 windows with exact hashes, identity and bound continuation. |
| 6 | DEV-025 | get_workflow_instructions supports exactly seven typed variants through the native renderers; generic instructions explain bounded evidence reads; versions become server/MCPB 0.4.0 and prompt library 1.4.0. |
| 7 | DEV-022 | Discovery and shared STDIO/local HTTP smoke agree on 19 tools/9 prompts/1 fixed resource/14 templates; a distinct retained 0.4.0 archive/stage matches current inputs and exercises all access routes. |

Do not repeat copying, preparation, partition generation, package acceptance mutation or cutover. Preserve all six accepted snapshots, config/profile/prompt-configuration bytes, original judgments/rights, prior receipts and archives/stages. Developer owns runtime/executable smoke integration and ad hoc implementation feedback; Tester owns formal cases/full acceptance, Documenter owns prose/strict builds/Desktop walkthrough/remote checklist. No model/paid API call, publication, deployment or sign-off is authorized.

## Implementation Contract

- `Scope`: `.standards/docs/scope/integrate-actual-learning-progressions-20261001T162834Z-142f2df1.md`
- `Architecture`: `.standards/docs/specs/integrate-actual-learning-progressions-20261001T162834Z-142f2df1.md`
- `Request`: Preserve the implemented six-curriculum stored LP integration and revise client access with complete bounded canonical query text, paged native ResourceService evidence, seven typed shared workflow instruction variants, both envelope ceilings and a retained 0.4.0 distribution. Preserve native prompts/resources, immutable accepted identities, stored semantics and rights. Formal verification/documentation remain with their owners; deployment and sign-off remain user-owned.

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

`Status`: `DONE` `Depends On`: `DEV-001`
`Acceptance`: `AC-002, AC-003, AC-010, AC-018, AC-019`

**Goal**

Represent stored LP edges and their required artifact/count/capability declarations in the existing package and graph models.

**Affected Area**

packages/models.py, wire.py, decoder.py, builder.py; graph/models.py; domain enums/identifiers and regexes.py where required.

**Expected Outcome**

Manifest 1.1/delivery 1.2/source 1.0 contracts recognize buildsTowards and relatesTo with exact standard endpoints, dedicated evidence names, strict LP counts and availability flags. Builder accepts the new safe delivery filenames and declared evidence. Non-LP packages remain representable under the new schemas; AS/LC fields keep their meanings.

**Self-Check**

PASS — completed the immutable LP package/delivery construction contract. Working directory: `/Users/tzz/Projects/private/idi/KGForEdGlobalMCP`; assessed HEAD: `a3b40387048ff075d13eabe8266fc482a3e90e89` plus the six changed-module identities below. All final commands exited 0. Backend checks used the existing Python 3.13.9 environment through locked/offline/no-sync uv; no dependency installation or network/model calls.

Actual final commands (from the repository root):

```sh
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync python /tmp/kgfegmcp-dev002-self-check.py /Users/tzz/Projects/private/idi/KGForEdGlobalMCP
```

The temporary ad hoc script assessed real copied LP edges in memory and temporary package proposals only; it is not a Tester-owned test suite. Script identity: `sha256:6c0c8ddd7165dee4c4f84870439708c1876803fa1f145fde62180f3da6d6de76`; result identity: `sha256:47fdc2c969f04d9e94f82df7367f5447774b39a990abddfac2f7211818903cf5`; protected baseline inventory identity: `sha256:7e70c9bdc5ec7807a58f769bfdc651cb87bcfd8b60efa3721560653e157f07a0`. These scratch files may be discarded after this step; the assessed outcomes are persisted here.

For each command below the full prefix was `/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync`; its effective working directory was `backend`. The exact module arguments were `src/kgfegmcp/packages/builder.py src/kgfegmcp/packages/loader.py src/kgfegmcp/packages/models.py src/kgfegmcp/packages/repository.py src/kgfegmcp/packages/wire.py src/kgfegmcp/regexes.py`.

- `ruff check <module arguments>`: all checks passed.
- `black --check <module arguments>`: all six unchanged by formatting.
- `isort --check-only <module arguments>`: passed.
- `mypy --cache-dir /tmp/kgfegmcp-dev002-mypy <module arguments>`: no issues in six source files.
- `pylint <module arguments>`: 10.00/10.
- `interrogate <module arguments>`: 100% docstring coverage; its configured badge generation caused no tracked badge change.
- `git diff --check`: passed. `node .standards/bin/check.mjs`: passed before recording completion and at the final STEPWISE pause.

Self-check outcomes:

- 69 named sanity checks passed; all 8,080 stored LP edges (3,039 buildsTowards, 5,041 relatesTo) decoded across six curricula with preserved identifiers, types, exact CASE selectors, authors, attribution and licensing. All six existing AS/LC node/relationship counts and supports counts remain unchanged.
- New-schema non-LP manifests, loader graph-type checks, persistence contract checks and temporary builder proposals remain representable. No acceptance was persisted.
- Strict LP counts reject negative, boolean, fractional and string values. Malformed LP label/type agreement, outer/property identifiers, endpoint labels/entities/keys and blank/whitespace/coerced selectors are rejected. Conflicting availability, missing dedicated evidence, counts exceeding total, logical-name shadowing, unsafe paths/delivery names, mismatched/out-of-range provenance partitions and unsupported relationship labels are rejected.
- Temporary LP proposals declare all nine evidence artifacts and their checksum closure; buildsTowards/relatesTo counts are separate from existing supports and hierarchy-related counts. Repeated proposals retain snapshot/checksum identities; materialized temporary packages remain PENDING and round-trip. A declared LP package with zero LP edges remains available.
- All 180 protected files across `config/profiles`, `config/prompts`, `data/graph_packages` and `data/input_artifacts` retain their start-of-step hashes. No raw sources, preparation inputs, accepted packages or active configuration were changed.
- Limits: evidence contents were placeholders in temporary builder checks; full provenance/graph integrity and package acceptance belong to DEV-004. Existing legacy manifests remain schema 1.0 and will be replaced/activated in later steps; this intermediate checkout is not a runtime activation milestone. Developer sanity checks do not establish formal Tester verification, semantic validation or pedagogical certification. No live LLM/paid-service calls or deployment occurred.

Assessed changed-content identities:

- `backend/src/kgfegmcp/packages/builder.py`: `sha256:d917e9590ee9ab81fd264ed60500ed8d63a2610110f174182b35eea224308188`.
- `backend/src/kgfegmcp/packages/loader.py`: `sha256:08408a9ae718976a2fccf702482a41cbaf0a5a625b55cc3844385cdb07a88817`.
- `backend/src/kgfegmcp/packages/models.py`: `sha256:dcd73e308d658c962b793a1b9e6f72eebaf445ce3876269186efb0604a1c0591`.
- `backend/src/kgfegmcp/packages/repository.py`: `sha256:4e0f0621d1ee2c1fa5e557fd7e91230922310ee9bc610965acaf810619632cfa`.
- `backend/src/kgfegmcp/packages/wire.py`: `sha256:6384effad1fd2c4d6fbfd185a358a058ae12cfc77e6f06b493adf0ff2a229147`.
- `backend/src/kgfegmcp/regexes.py`: `sha256:ec989cbd55da39100806fe284139751f253066d02083b56f63ad2867090a3182`.

**Implementation Notes**

Existing decoder, graph models and domain enums already preserve generic LP relationship fields, so they were reused. Loader and validation-persistence graph-type constraints were adjusted alongside the package contracts to admit supported combinations with or without LP; this is contract consistency within the approved outcome, not an integrity-acceptance implementation. Availability is derived from complete evidence declarations rather than nonzero counts. Original LP provenance maps remain dedicated evidence; the builder only permits the 64 canonical additional provenance filenames with their matching logical slots. DEV-003 will construct the complete partitions; DEV-004 will verify their contents. No later step was started.

### DEV-003 — Prepare normalized LP inputs and verified provenance partitions

`Status`: `DONE` `Depends On`: `DEV-002`
`Acceptance`: `AC-001, AC-002, AC-004, AC-010, AC-011, AC-012`

**Goal**

Add a reproducible preparation command in the existing CLI family consuming only the verified local copies.

**Affected Area**

cli preparation module and pyproject.toml script entry; packages normalization helpers; local generated delivery/evidence/index/receipt outputs.

**Expected Outcome**

Original node bytes and AS/LC relationship prefix remain exact. Appended LP wire records are sorted, resolve exact CASE endpoints and reconcile with split/combined/provenance inputs. All 64 canonical provenance partitions and index preserve original entries. Runtime normalization receipts expose relative identities/hashes without private source paths; original evidence remains intact.

**Self-Check**

PASS — reproducible local preparation completed for all six copied frameworks. Working directory: `/Users/tzz/Projects/private/idi/KGForEdGlobalMCP`; assessed HEAD: `d601908b040d21eb5b3f0fe8b08c6273521e08d5` plus the five changed-content identities below. Final commands exited 0. No network/model/paid-service calls, producer/checker regeneration or package acceptance occurred.

Actual command-help and execution commands from the repository root:

```sh
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync python -m kgfegmcp.cli.prepare_learning_progressions --help
/Users/tzz/.local/bin/uv --directory backend run --locked --offline kgfegmcp-prepare-learning-progressions --help
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync python -m kgfegmcp.cli.prepare_learning_progressions > /tmp/kgfegmcp-dev003-first-run.json
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync kgfegmcp-prepare-learning-progressions > /tmp/kgfegmcp-dev003-repeat-run.json
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync python -m kgfegmcp.cli.prepare_learning_progressions --framework-id nigeria-nerdc-mathematics-primary-1-3 > /tmp/kgfegmcp-dev003-selected-run.json
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync python /tmp/kgfegmcp-dev003-self-check.py /Users/tzz/Projects/private/idi/KGForEdGlobalMCP
```

The command-help run without `--no-sync` rebuilt only the local editable project offline to register its new console entry point. Python remains 3.13.9; no dependency or lockfile change. First execution created six complete trees. Repeat execution returned `existing_identical` for all six, with identical counts and all artifact hashes; exact selection returned one unchanged tree. A separate fresh temporary root reproduced every artifact hash for all six frameworks.

The ad hoc Developer feedback script assessed the produced bytes independently and exercised temporary negative fixtures only; it is not a Tester-owned suite. Final scratch identities: script `sha256:6195020ccbd3a54b1d16f14e915ea49f0f85062a4b9d966ba3b7114df4e65dcd`, result `sha256:8ca842ff7cbacfaf9563cca09ffb403a46bd04f82e67a41e3bc03a7fe5e1961b`, protected baseline inventory `sha256:a89f7624ab4a0729889b1803e192e08909d8fabb7f1b190819730c391120617b`. Scratch files may be discarded; material outcomes and persistent preparation identities are recorded here.

Static checks used the prefix `/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync`, effective working directory `backend`, and these exact module arguments: `src/kgfegmcp/packages/normalization.py src/kgfegmcp/packages/normalization_models.py src/kgfegmcp/packages/normalization_sources.py src/kgfegmcp/cli/prepare_learning_progressions.py`.

- `ruff check <module arguments>`: all checks passed.
- `black --check <module arguments>` and `isort --check-only <module arguments>`: passed for all four modules. The final isort pass removed one blank import-separator line in normalization_models.py; Black reconfirmed that file. Earlier successful semantic checks are unchanged by this whitespace-only fix.
- `mypy --cache-dir /tmp/kgfegmcp-dev003-mypy <module arguments>`: no issues in four files.
- `pylint <module arguments>`: 10.00/10, including configured complexity checks.
- `interrogate <module arguments>`: 100% docstrings; configured badge generation caused no tracked badge change.
- `git diff --check` and `node .standards/bin/check.mjs`: passed; workflow check rerun at the final STEPWISE pause.

Self-check outcomes:

- 519 named implementation sanity checks passed. Every original node byte and AS/LC relationship prefix is unchanged; all 8,080 stored LP IDs/types/endpoint values/author/provider/license/attribution/descriptions match original split records. CASE selectors resolve to existing outer IDs, including a synthetic case where those IDs differ. Appended LP records are sorted by type/ID; optional non-null date strings are preserved and null dates omitted. A temporary no-final-LF prefix receives only the recorded separator.
- Split records agree with both combined JSONL formats, the rich combined bundle, exact original provenance metadata and accepted final claims. Original report/unresolved/summary/final-claims bytes remain intact, including CBSE needs_review and Ghana warning evidence. Candidates/no_relation/needs_review never supply exported edges.
- All 384 partition maps (64 per framework) use canonical UTF-8 JSON, sorted keys and one final LF. Placement independently matches the SHA-256-first-byte modulo-64 rule. Their unique exhaustive union is deeply equal to every original provenance entry and covers exactly all exported LP IDs. Index version 1.0 records exact original-map hash, fixed algorithm and all manifest logical slots with relative paths/counts/hashes. The largest actual partition is 900,480 bytes, below the unchanged 32 MiB source-read limit; future resource limits remain independently enforced.
- Normalization receipts record exact input/output byte hashes, copy-receipt identity, framework/document CASE mapping, per-type counts and prefix/separator facts. Generated receipts/indexes contain no private filesystem/source paths or copied model/rationale content. Original evidence is retained rather than sanitized or regenerated.
- Negative feedback covers unknown/missing/coerced split fields, invalid CASE namespaces/IDs, unresolved endpoints, duplicate/wrong-slot split IDs, missing/mismatched combined edges/rich metadata/provenance/final claims, duplicate JSON keys/nonfinite numeric values including overflow, copied-byte drift, symlink components, unknown framework selection, protected output roots and conflicting existing output without overwrite. Empty LP provenance generates all 64 empty maps. CLI failures remain concise and omit private paths.
- All 319 start-of-step files across raw copies/copy receipt, config/profiles, config/prompts, data/graph_packages and data/input_artifacts retain their hashes. The 516 generated files (86 per framework) live only under ignored `data/source_artifacts/learning_progressions/prepared/<framework-id>/`; no active configuration, old accepted package or existing preparation input was changed. Temporary fixtures/fresh-root trees were removed after feedback.
- Limits: this is deterministic preparation feedback, not independent package integrity acceptance, formal Tester verification, semantic/pedagogical certification or runtime activation. DEV-004 independently validates LP graph/provenance/report integrity; DEV-005 constructs accepted replacements. Current legacy active packages remain unchanged and the intermediate schema-migration checkout is not a deployment milestone. DEV-023 later replaces tracked data/input_artifacts with normalized rebuild inputs; required runtime evidence will be retained in accepted packages, separate from ignored raw copies. No later step started.

Persistent preparation evidence (paths relative to each framework's prepared tree):

| Framework | buildsTowards | relatesTo | detailed/lp_relationship_provenance_index.json | detailed/lp_normalization_receipt.json |
|---|---:|---:|---|---|
| `nigeria-nerdc-mathematics-primary-1-3` | 189 | 297 | `sha256:0c103b882464e2f078e6c7e1bb4d6c07347ef94efd62762b0854ed789e718385` | `sha256:0b2faaa042f116cbf20690021a3ebaa738ac2b37c641a39acfb815e936839038` |
| `india-tamil-nadu-tnscert-mathematics-classes-1-5` | 472 | 435 | `sha256:15f1599034ab63ab5266ecd84e0d3b2d5bfd5ffb70af65a55761363ab6f858fc` | `sha256:961770d68d9c5d27815738c35fe1a37ede13f09760b1a8ad252f869a6c3b4783` |
| `india-cbse-science-learning-framework-classes-9-10` | 891 | 2315 | `sha256:fbd393547c06471e51ff9b2f6c98cd91ca765315868f39a53bd6136f8708766d` | `sha256:1ac49085408a87f5b0ee47868a4a6e61c69150bc3b63e109000dc28f92b93056` |
| `rwanda-reb-mathematics-lower-primary-1-3` | 938 | 893 | `sha256:7d7c981b93e521d7f73b6784a23984a271989e289604aeddc0a022b4922d1582` | `sha256:a74ada4497caf42dcfa8ad02dad93e533167cf4ca93a4bb99d95943a1b11d4ef` |
| `ghana-nacca-primary-mathematics-basic-4-6` | 299 | 300 | `sha256:d53ac196c33c101fc75ae4f5259ce8c65a3a039ebb35c40c66895df3cf72c075` | `sha256:f44484d55b0ec667a93cd761f98b4c991f90e45e6a47a8b7fa0156723fa216ca` |
| `ghana-nacca-primary-english-language-basic-1-3` | 250 | 801 | `sha256:87ccab088d8a24324336af72eecb97d1da791b52f082eba9f2cf2510739971b0` | `sha256:57e7047c33a09350d7ea9b99e0cf7e5850d6965bd6c7dd5035d6b8878f22b262` |

Each normalization receipt's `outputSha256` covers the other 85 generated files; its own exact-byte hash above closes the complete preparation-tree identity.

Assessed changed-content identities:

- `backend/pyproject.toml`: `sha256:83fc2343c199c7aaa9140a1b093408a1df9c992dfb9c7af8d1b53b06c84181e0`.
- `backend/src/kgfegmcp/cli/prepare_learning_progressions.py`: `sha256:dcc19231323c3a4194198e8b9d32f03ebd8546bf98f0fbb39d41a5e1996cf53b`.
- `backend/src/kgfegmcp/packages/normalization.py`: `sha256:aef47a5a472fc9ecc8787ce5b8e09303ffe8c0a98df2c0593cebae723cabac33`.
- `backend/src/kgfegmcp/packages/normalization_models.py`: `sha256:a4fc413d1432e056807ece8ba14295f6f63334dc7cbde80328576aa7163ed060`.
- `backend/src/kgfegmcp/packages/normalization_sources.py`: `sha256:0f269e0b154f6b87b5660d17897c1fc91128fa54f79be82885bb5c4ffe6927fd`.

**Implementation Notes**

New `kgfegmcp-prepare-learning-progressions` console command and matching Python module consume only the repository-local copy receipt and its exact 23-file mappings; external receipt paths are ignored and never read. By default all frameworks are prepared in sorted order under the ignored local prepared root; optional `--framework-id` selects an exact mapping. Every framework publishes from an isolated stage only after reconciliation and repeat copy-hash checks. Existing identical output is reusable; conflicting output is preserved and rejected. Source/copy/config/runtime path overlap and symlinks are rejected. No package manifest or old profile build specification is written here; later steps supply the new profile identities and acceptance. Strict source models and generated receipt/index models make these boundaries available to DEV-004 without adopting producer/checker judgments as validation.

### DEV-004 — Accept LP integrity independently and retain small query projections

`Status`: `DONE` `Depends On`: `DEV-003`
`Acceptance`: `AC-003, AC-004, AC-010, AC-011, AC-012, AC-018, AC-019`

**Goal**

Extend the package acceptance boundary to verify LP records, evidence and topology independently of preparation.

**Affected Area**

packages/validator.py, loader.py and focused evidence models/helpers; LoadedGraphPackage/catalog runtime projections.

**Expected Outcome**

Malformed/duplicate/pair-conflicting edges, invalid endpoints/attribution/confidence, missing or mismatched provenance, counts, partitions and builds cycles cannot pass acceptance. AS/LC report comparison remains subgraph-specific. hasChild cycle checks remain separate. Runtime keeps immutable small judgment/coverage projections and releases rich maps.

**Self-Check**

Completed: all six prepared frameworks passed independent full-evidence loading, graph validation, temporary atomic acceptance and read-only terminal revalidation. All 53 bounded implementation-feedback checks passed, as did a complete synthetic zero-edge LP package and a new-schema AS/LC-only package. Static/type/style/format/complexity checks passed. The 835 protected baseline files remain byte-identical; no replacement was published or activated.

**Actual Evidence**

- Assessed repository HEAD: `255772c9f0e44046f7f3aae34204d237e42f4d45`; initial tracked working tree was clean. No commit was created by Developer.
- Command working directory: `/Users/tzz/Projects/private/idi/KGForEdGlobalMCP`; `uv --directory backend` runs Python tools in the backend directory. Every Python command used `/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync`.
- Executed `python /tmp/kgfegmcp-dev004-feedback.py`: all six temporary packages loaded without findings, passed graph validation and persisted atomic `pending` → `passed` acceptance. Each terminal package then passed read-only revalidation with unchanged manifest bytes and no persistence. All 8,080 stored LP edges were represented by validated bounded judgments: 3,039 buildsTowards and 5,041 relatesTo. All 384 canonical partitions were independently checked. Temporary packages used existing profiles only as implementation feedback and were removed on context exit.
- Executed `python /tmp/kgfegmcp-dev004-negative.py`: 53 feedback checks passed. Covered complete evidence, frozen/bounded projections and exact omission flags; temporary atomic acceptance/read-only terminal revalidation; original-byte tampering, missing shard, stale integrity snapshot, failed/error-bearing/false-semantic-certification reports, LP count/fingerprint disagreements, duplicate JSON keys and missing evidence; nonfinite/out-of-range/boolean confidence, direction/endpoint and relationship identity mismatch, source-author inheritance and config/request mismatch; wrong partition algorithm, missing slots, count/path/reference errors, changed original entries and incorrect buckets, explicit integer/count/format requirements; AS/LC prefix and complete appended LP suffix mismatch; duplicate and reversed/type-conflicting pairs, self edges, framework/nonstandard/wrong-CASE endpoints, relatesTo canonical order, separate builds cycle findings with exact offending relationship IDs and exclusion of relatesTo from cycle detection; complete request-set and accepted-claim count correspondence; AS/LC-only acceptance without LP availability.
- Executed `python /tmp/kgfegmcp-dev004-zero.py`: a complete synthetic zero-publication LP package passed read-only validation with both LP availability flags true, zero LP counts and an immutable empty judgment tuple. No absent evidence was fabricated at runtime.
- Executed `ruff check`, `mypy`, `pylint`, `black --check` and `isort --check-only` against `src/kgfegmcp/packages/learning_progressions_graph.py`, `learning_progressions_models.py`, `learning_progressions_validation.py`, `loader.py`, `models.py` and `validator.py`: all passed; mypy checked six files and pylint rated 10.00/10. Also executed `ruff check --select C901` against the same six modules: no complexity findings (maximum configured 10). An AST sanity check confirmed NumPy Examples on all 24 new functions/methods and alphabetical multi-keyword calls in the three new modules. `git diff --check` passed.
- Baseline manifest `/tmp/kgfegmcp-dev004-baseline.json`, exact bytes `sha256:3be244d56410d11640a364c34720a1e5eb4a4dfce959b68a443dd5fb7873abb0`, inventoried 835 files under config, data/graph_packages, data/input_artifacts and data/source_artifacts/learning_progressions. Post-feedback SHA-256 comparison found no changed, missing or added protected files. All scratch package roots were removed. Existing resource size/rights policies were unchanged.
- STANDARDS check passed before implementation and after saving this completed step/continuation blocker.
- Limits: these are Developer implementation checks, not independent Tester verification, semantic/pedagogical certification or runtime activation. Producer content hashes are retained, format-checked and cross-referenced where available; acceptance does not invent producer hashing algorithms or regenerate unavailable upstream inputs. Complete original evidence is checked regardless of resource response limits; those limits remain enforced by existing resource boundaries. Current legacy active manifests/configuration remain untouched during this intermediate migration. No live LLM/paid-service calls, sampling, external source reads, deployment or later-step implementation occurred.

Temporary feedback source identities (scripts are session-local, not committed formal tests):

- `/tmp/kgfegmcp-dev004-feedback.py`: `sha256:23904fc4e6388e5ca92e68d034f9160bf522688a74b6619079a1f0062bf06347`.
- `/tmp/kgfegmcp-dev004-negative.py`: `sha256:2887adc2c057873b2cf9adb8846f4ed4f9021b8c17e072ab55a75a08ca2c4656`.
- `/tmp/kgfegmcp-dev004-zero.py`: `sha256:dd7a1b3bd1e556f7fbb276be45c3857b287f6d743809816f4778e169efefa3e3`.

Temporary acceptance/revalidation results:

| Framework | buildsTowards | relatesTo | Original provenance bytes | Runtime projection JSON bytes | needs_review | Unresolved warning pairs |
|---|---:|---:|---:|---:|---:|---:|
| ghana-nacca-primary-english-language-basic-1-3 | 250 | 801 | 13,080,019 | 1,541,671 | 0 | 10 |
| ghana-nacca-primary-mathematics-basic-4-6 | 299 | 300 | 7,290,536 | 875,801 | 0 | 141 |
| india-cbse-science-learning-framework-classes-9-10 | 891 | 2315 | 40,860,837 | 4,713,076 | 1 | 0 |
| india-tamil-nadu-tnscert-mathematics-classes-1-5 | 472 | 435 | 11,199,490 | 1,432,774 | 0 | 0 |
| nigeria-nerdc-mathematics-primary-1-3 | 189 | 297 | 5,682,836 | 704,913 | 0 | 0 |
| rwanda-reb-mathematics-lower-primary-1-3 | 938 | 893 | 23,237,077 | 2,692,240 | 0 | 0 |

CBSE’s 40,860,837-byte original provenance artifact exceeds the 32 MiB single-resource policy but was validated in full. Projection sizes above describe aggregate serialized scalar/tuple metadata, not resource-limit exceptions; each stored rationale is at most 512 characters, with at most five warning excerpts of 512 characters each and explicit omission/excerpt flags. Full rationale, candidate and checker trace remain unmodified in declared evidence.

Assessed changed-content identities:

- `backend/src/kgfegmcp/packages/learning_progressions_graph.py`: `sha256:a53dfb90d1a9535cb65a57a8aaf4dac11bfdfdb1e8044624a085c47e4fdc33a0`.
- `backend/src/kgfegmcp/packages/learning_progressions_models.py`: `sha256:557065f60b0969dd398dea2cc772ecbabed092f86f0bb704142616c48cff9fb6`.
- `backend/src/kgfegmcp/packages/learning_progressions_validation.py`: `sha256:660021a4837cf547e4de80fdc6a966419df54e2ccb2c117ecc2897ed8e6de71d`.
- `backend/src/kgfegmcp/packages/loader.py`: `sha256:05c19ead7c5ff5d76fce98a63ea5ab9a8fe984ab334ba63a692180950c36d2bd`.
- `backend/src/kgfegmcp/packages/models.py`: `sha256:24288e1cf3fe5d3e705d4106125d82c6ee2135ed3bed4283545abfa25b600593`.
- `backend/src/kgfegmcp/packages/validator.py`: `sha256:10a667fbb29e974cc9425817b81aa631932c3041a81625f85a3d1b286b141b75`.

**Implementation Notes**

The loader captures dedicated LP artifacts and all partition bytes through the existing safe checksum boundary, then parses and validates evidence without filesystem/resource rereads. Strict source models require final candidate/judgment/trace identities, source-framework and available input/config fingerprints, report/count/status fields, unresolved decisions and final request coverage. Original split metadata, final claims, provenance and every indexed shard must agree exactly. The public normalization receipt independently binds unchanged node bytes, original AS/LC relationship prefix, normalized sorted LP suffix, complete output hashes and retained input hashes; it cannot supply private producer paths or implicit format defaults.

Separate LP graph checks require exact standards-only CASE endpoints, matching outer/property identity/type fields, no self edges, unique IDs/pairs across types and directions, canonical relatesTo order and distinct buildsTowards cycle findings with offending IDs. Generic relationship identity checks remain in place. LP generated credit is checked against retained evidence and source framework/license separately from hierarchy and supports inheritance. Manifest LP counts/availability are evidence-derived; retained AS/LC report and unresolved counts are scoped to the AS/LC subgraph. Non-LP packages remain supported.

LoadedGraphPackage carries only frozen LearningProgressionEvidence made of bounded JudgmentProjection tuples and scalar/tuple CoverageProjection metadata, including structural-only notice, excluded/nonpublishing counts, warning excerpts/counts and optional unknown eligibility denominators. All rich maps and captured bytes are acceptance-local and released afterward; catalog runtimes inherit the small aggregate through their existing loaded-package reference. Full evidence stays in the declared artifacts for later resources. DEV-005 remains pending; no accepted replacement/configuration was retained or activated.

**User-requested naming follow-up**

User explicitly requested shorter module names after completing DEV-004. Renamed `learning_progressions_graph.py` → `lp_graph.py`, `learning_progressions_models.py` → `lp_models.py` and `learning_progressions_validation.py` → `lp_validation.py`, updating all production imports in those modules and loader.py, models.py and validator.py. This changes naming only within the approved DEV-004 intent; all six module bodies are AST-identical after excluding imports. Prior evidence and original path/hash bindings above remain historical; the current identities below supersede their implementation locations.

- Assessed HEAD: `255772c9f0e44046f7f3aae34204d237e42f4d45`. Working directory: `/Users/tzz/Projects/private/idi/KGForEdGlobalMCP`. Used `/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync` for all Python checks.
- Executed `ruff check`, `mypy`, `pylint`, `black --check` and `isort --check-only` on `src/kgfegmcp/packages/lp_graph.py`, `lp_models.py`, `lp_validation.py`, `loader.py`, `models.py` and `validator.py`: all passed; mypy checked six files and pylint rated 10.00/10.
- Reused the prior temporary negative/acceptance feedback, changing only its module imports in `/tmp/kgfegmcp-dev004-rename-feedback.py`; executed `python /tmp/kgfegmcp-dev004-rename-feedback.py`: all 53 checks passed, including temporary acceptance and read-only revalidation. Original temporary scripts were preserved. This is Developer feedback, not formal Tester verification.
- Repository search found no remaining old module-name references under backend. Git index SHA-256 and `.standards/STATE.md` SHA-256 match the pre-rename snapshot `/tmp/kgfegmcp-dev004-rename-baseline.json`; preexisting staged changes remain intact. Rename/import updates and this follow-up record are unstaged. DEV-004 remains DONE; DEV-005 remains PENDING and its STEPWISE continuation blocker is unchanged. No configuration/data changes or later-step work occurred.
- `git diff --check` and `node .standards/bin/check.mjs` passed after saving this follow-up.

Current renamed-source identities:

- `backend/src/kgfegmcp/packages/lp_graph.py`: `sha256:a53dfb90d1a9535cb65a57a8aaf4dac11bfdfdb1e8044624a085c47e4fdc33a0`.
- `backend/src/kgfegmcp/packages/lp_models.py`: `sha256:557065f60b0969dd398dea2cc772ecbabed092f86f0bb704142616c48cff9fb6`.
- `backend/src/kgfegmcp/packages/lp_validation.py`: `sha256:07db6512c5caf3237e171ebb51e6f5ece442fd922014cda1d881dcb5e2ffcc22`.
- `backend/src/kgfegmcp/packages/loader.py`: `sha256:b831511b1859b12879dc8cb1c09356b03b1624daa9ae1de597cd19971f81fcda`.
- `backend/src/kgfegmcp/packages/models.py`: `sha256:4bb800230ebe88dbd10437d9a36bb0214a87febccc932e2e0074bed18c4a9342`.
- `backend/src/kgfegmcp/packages/validator.py`: `sha256:304d7ff1e7f56145e0c52bb54b4827bff3f3a9848ff0cbc753b408da41aef1e4`.

Adapted feedback source: `/tmp/kgfegmcp-dev004-rename-feedback.py`, `sha256:aa854fe0af79f554e2948275bce8823991ad085792700f31a4d660d743dc0650`.

### DEV-005 — Build six accepted replacement snapshots in a separate root

`Status`: `DONE` `Depends On`: `DEV-004`
`Acceptance`: `AC-002, AC-003, AC-004, AC-017, AC-018, AC-019, AC-020`

**Goal**

Publish fresh interpretation/prompt configuration contracts and prepare all six replacement packages without overwriting terminal baseline directories.

**Affected Area**

profiles/models.py and configuration validation; prompts/models.py configuration schema/overlay contracts; new config/profiles and config/prompts version 2.0 trees; separate package preparation root.

**Expected Outcome**

Profile/prompt-config schemas advance to 1.1, preserve useful interpretation/rights/guidance, remove progressionHeuristics and hypothesis overlays, and allow the three designed overlays. Replacement revision-1 snapshots retain source version/current status and required runtime artifacts. All six pass persisted atomic acceptance and read-only revalidation before activation.

**Self-Check**

Completed: both configuration schemas are 1.1; all six profile version 2.0 and matching prompt configuration version 2.0.0 files load through the existing repositories. All six revision-1 replacements passed persisted atomic acceptance and read-only terminal revalidation. The package total is 3,039 buildsTowards and 5,041 relatesTo. All 835 start-of-step protected files remain unchanged. Replacements are retained separately and have not been activated.

**Actual Evidence**

- Assessed HEAD: `19bcb440b0164dfacbc398693ccc92cf2d6955a8`; entry tracked working tree was clean. Working directory: `/Users/tzz/Projects/private/idi/KGForEdGlobalMCP`. No commit was created. Workflow check passed before implementation; this continuation was explicitly authorized by the user and cleared only DEV-005's matching blocker.
- Python command prefix: `/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync`. Python tools execute in `backend`; no dependency installation or network call was needed.
- Executed `python /tmp/kgfegmcp-dev005-build.py` with that prefix. This scratch orchestrator ran the established CLI, once per exact generated specification: `kgfegmcp-build-manifest --spec /Users/tzz/Projects/private/idi/KGForEdGlobalMCP/data/source_artifacts/learning_progressions/dev005/build_specs/<framework-id>.json` for six frameworks; then `kgfegmcp-validate-packages pending`; then `kgfegmcp-validate-packages one --framework-id <framework-id> --snapshot-id <replacement-snapshot-id> --read-only` for each terminal replacement. Every command exited 0. Acceptance returned six valid pending-to-passed persisted transitions with no findings. Each subsequent revalidation reported observed/effective passed, terminalRevalidation true, readOnly true and persisted false, with byte-identical terminal manifest before/after.
- CLI environment overrides were `PATHS_PROJECT_DIR=/Users/tzz/Projects/private/idi/KGForEdGlobalMCP`, `KGFEGMCP_PROFILE_ROOT=<project>/config/profiles`, `KGFEGMCP_PROMPT_ROOT=<project>/config/prompts`, and `KGFEGMCP_GRAPH_PACKAGES_ROOT=<project>/data/source_artifacts/learning_progressions/dev005/replacement_packages`. The generated specifications use repository-relative prepared delivery/detailed/shard paths, profileVersion 2.0, unchanged jurisdiction/source version/publication/snapshot-relation settings, and packageRevision 1. Existing maintained `data/input_artifacts/*/package_build.json` files were not changed; their replacement is DEV-023.
- Executed `python /tmp/kgfegmcp-dev005-feedback.py` with the prefix: 1,543 named assertions passed, including individual protected-file and artifact comparisons. Read-only catalog reconstruction yielded six accepted runtimes; PromptConfigRepository loaded all six exact version 2.0 configurations, bound by actual byte hashes. Entire new profile JSON equals the original after only version/schema changes and heuristic removal; entire new prompt JSON equals the original after only version/schema changes and hypothesis-overlay removal. Shared and all unrelated guidance, grade/code/hierarchy interpretation, source anomalies and rights remain intact.
- Every replacement's 86 declared artifacts is byte-identical to its prepared input, including all nine dedicated LP artifacts and all 64 canonical provenance shards (384 total). Closed-tree acceptance verifies their exact checksum closure and complete retained evidence. Original node delivery bytes and complete AS/LC relationship prefix remain byte-identical to the baseline, preserving all AS/LC IDs, source text, hasChild/supports edges, unresolved status and multi-parent targets. AS/LC counts are unchanged; total relationships add exactly the two LP counts. All 8,080 exported LP identifiers and type/author/provider/license/attribution/description/endpoint values agree with split evidence. All 8,080 validated judgment projections remain present. Source framework metadata, sourceVersion, isCurrent, rights and snapshotRelations equal the baseline.
- Config feedback accepts/round-trips every declared field of all three new overlays and their 60-instruction boundary; rejects old schema versions, progressionHeuristics, inferredProgressionHypothesis, unknown guidance fields, empty configs, excess shared/per-prompt/block instructions, duplicate/blank/oversized instruction text and invalid modes. New overlays are optional bounded soft-guidance contracts only; future workflows are not registered or rendered by this step.
- Initial scratch feedback stopped on an overstrict expectation that old and newly copied detailed evidence would all be byte-identical. Read-only recursive comparison reconciled 2,721 scalar differences across 23 detailed artifacts: producer run paths, the Ghana Mathematics AS run timestamp, run/bundle/LC input fingerprints and LC generated-from-bundle metadata. All other detailed values agree with the baseline, and every new detailed artifact exactly matches the previously normalized copied input. Sealed originals are unchanged. Two subsequent scratch-script errors used an incorrect attribution key and Python tuple-versus-JSON-list equality; corrected to attribution_statement/attributionStatement and JSON-mode serialization. Final feedback passed without package/source changes or weakening the delivery/evidence contract. The receipt records all differing JSON paths and old/new artifact hashes without copying private producer paths into the plan.
- Final source checks against `src/kgfegmcp/profiles/models.py src/kgfegmcp/prompts/models.py src/kgfegmcp/prompts/__init__.py src/kgfegmcp/prompts/service.py`: `ruff check`, `mypy --cache-dir /tmp/kgfegmcp-dev005-mypy`, `pylint`, `interrogate`, `black --check`, and `isort --check-only` all passed. Mypy found no issues in four files; pylint rated 10.00/10; docstring coverage was 100%. Interrogate's configured badge write produced no tracked badge diff. `git diff --check` passed. Searches returned no old heuristic/guidance-class references under backend/src and no heuristic/hypothesis-overlay keys in version 2.0 JSON; version 1.0 sealed configs are deliberately preserved until DEV-017 retirement.
- Limits: these are Developer implementation checks, not independent Tester verification or semantic/pedagogical certification. CBSE's single needs_review claim and Ghana English/Mathematics 10/141 unresolved-warning pairs remain retained and excluded from published LP edges. CBSE's original provenance is still over 32 MiB; all evidence was checked without increasing resource limits, and the 64 validated partitions remain the later per-edge access mechanism. Active old packages/configurations were not activated, modified or retired; this intermediate migration checkout is not a deployment milestone. No full bootstrap/transport/distribution acceptance was claimed; those depend on future service/prompt/activation steps. No external source reads/writes, upstream regeneration, live LLM/paid-service calls, sampling, deployment, DEV-023 or later implementation occurred.

Retained preparation root: `data/source_artifacts/learning_progressions/dev005/replacement_packages/`. It is outside active discovery and distribution and remains ignored local preparation until the approved activation step; do not delete it before DEV-023 comparison/DEV-017 activation. Each package has one manifest plus 86 exact declared artifacts; all six contain 522 files. New version 2.0 configuration files are ordinary unignored repository changes. Build specs, command/result receipts and identity inventory are retained beside the replacement root for continuation.

Replacement identities and actual counts (graph package ID is the snapshot ID plus `--academic-standards--p1`):

| Framework | Replacement snapshot ID | buildsTowards | relatesTo | Accepted manifest SHA-256 |
|---|---|---:|---:|---|
| `ghana-nacca-primary-english-language-basic-1-3` | `ghana-nacca-primary-english-language-basic-1-3@2019+e00c5329a507` | 250 | 801 | `sha256:ab2bd1ce95caddfb8f9f67f66a46b7117f45e61f7ccc76e5c62fe444cd70861e` |
| `ghana-nacca-primary-mathematics-basic-4-6` | `ghana-nacca-primary-mathematics-basic-4-6@2019+0b768f7cfaf9` | 299 | 300 | `sha256:4a602730f1144bb961b1b9118c02ef4dc7ea9906f893e104eea16313209c2f3d` |
| `india-cbse-science-learning-framework-classes-9-10` | `india-cbse-science-learning-framework-classes-9-10@undated+576740bed2d1` | 891 | 2315 | `sha256:7068e5a5b39ff45bd373b15fa33a6311e899e896e5d3cb5f0851c7883cb836b3` |
| `india-tamil-nadu-tnscert-mathematics-classes-1-5` | `india-tamil-nadu-tnscert-mathematics-classes-1-5@2025-proposed-draft+aa0dd9310a0f` | 472 | 435 | `sha256:3e9fdacf040a5a6ca957b2ae9adca4a8bf2b871d779361103d6c19712696def8` |
| `nigeria-nerdc-mathematics-primary-1-3` | `nigeria-nerdc-mathematics-primary-1-3@undated+bc5e769ed26f` | 189 | 297 | `sha256:994dd1270d5badffaf07c8c9325a3b5985a5541296415ba10ce0f68879a5c981` |
| `rwanda-reb-mathematics-lower-primary-1-3` | `rwanda-reb-mathematics-lower-primary-1-3@2025+2ee0fa308d13` | 938 | 893 | `sha256:d2cd631accaf1ec382d185b7a21d1be479f51a54cf4e817b84de92c9ec2488d6` |

Fresh configuration byte identities (paths `config/profiles/<framework>/2.0/profile.json` and `config/prompts/<framework>/2.0/prompts.json`):

| Framework | Profile SHA-256 | Prompt configuration SHA-256 |
|---|---|---|
| `ghana-nacca-primary-english-language-basic-1-3` | `sha256:fe2b269f7e76d0abf89d00799857602e17c8e76b6d1b4055797c662629ce7212` | `sha256:2b941a1e93e3b1c133f0d5b40ee2abf24b36333a6d87d523378f25c6a72e357e` |
| `ghana-nacca-primary-mathematics-basic-4-6` | `sha256:4981190e0b1f79a924b92088ed7e78820961935a022ea1abcb13500e8136e848` | `sha256:1702079f466317e0e953449938cd7b45a9dce77b92aabcc0b99497e23589c877` |
| `india-cbse-science-learning-framework-classes-9-10` | `sha256:5e5e9ed3ec1f52f296b0ff5538aff56e6f2b8f58cc87ba0a29ac6e892bf5f852` | `sha256:788fd22501ea2a84a8db5f36a48a894bd7c715aaf6b5d0f64a4ff1873e71fb50` |
| `india-tamil-nadu-tnscert-mathematics-classes-1-5` | `sha256:8b9e1ffde3595ff24fa20bc2fa468fd952ec78aad6daaa4b19c1d5ebefc46595` | `sha256:4711bb6d09b8e07fac6e9cac9d7d6a3d8cad8a754d1c76803e127f30150a96cd` |
| `nigeria-nerdc-mathematics-primary-1-3` | `sha256:b04a2bcefa88d2e235cd9a1f988ae6af7dd9e50da565ec7aa9a5ac76015cd3e8` | `sha256:a9d6e333574a9a12c9b77514caace37b494120293831efbfb371991b18e90ec6` |
| `rwanda-reb-mathematics-lower-primary-1-3` | `sha256:d3fc130a70ce0502fc07f93a8211124adbe69a3b36b6302cf463f728fb41e0b6` | `sha256:3113ae183123271e5a3d0e075c72b807bfc59df5a3bf7bd0e0d1babf1e3aeb69` |

Preserved sealed baseline identities:

| Framework | Original snapshot ID | Original manifest SHA-256 |
|---|---|---|
| `ghana-nacca-primary-english-language-basic-1-3` | `ghana-nacca-primary-english-language-basic-1-3@2019+c33ab5a379fb` | `sha256:d5f1e8c40903ad0e2034018e9b08cda6a74bdd0e97e588c870ee15e0a8f630a7` |
| `ghana-nacca-primary-mathematics-basic-4-6` | `ghana-nacca-primary-mathematics-basic-4-6@2019+7afbd99e7f80` | `sha256:ae3ed336fb4303ab4908a1f998c2cf53683894c022b5aaed3d595ed4ec476afb` |
| `india-cbse-science-learning-framework-classes-9-10` | `india-cbse-science-learning-framework-classes-9-10@undated+e8361376ae1e` | `sha256:2e80061fd906c5972096686690f244ebc6722411e128b32e340667456772cb2a` |
| `india-tamil-nadu-tnscert-mathematics-classes-1-5` | `india-tamil-nadu-tnscert-mathematics-classes-1-5@2025-proposed-draft+3b9f8f89171e` | `sha256:9c96732b5ff8cb8b1a655d20ced0ed00131687edd8bd896e7133a900d08fce5a` |
| `nigeria-nerdc-mathematics-primary-1-3` | `nigeria-nerdc-mathematics-primary-1-3@undated+3f35e11c6624` | `sha256:bbab42346d3cf0258e4783c6c44889ed57f326aa77b06be00f4b10c7a94ae611` |
| `rwanda-reb-mathematics-lower-primary-1-3` | `rwanda-reb-mathematics-lower-primary-1-3@2025+98426787aa9f` | `sha256:cf2bb982bce3b505c5936e418b5a09620cf1daab1056fcf982fecf158329c1c1` |

Assessed source byte identities:

- `backend/src/kgfegmcp/profiles/models.py`: `sha256:6f067fa55ded0c528d6597ecf54ca2b3276ce4a85c8a10e41c93c774621b98af`.
- `backend/src/kgfegmcp/prompts/models.py`: `sha256:01094ab256b267d1acb1a5cdee9ca222ddcb7475f72943cf4c1fb29917bd71b7`.
- `backend/src/kgfegmcp/prompts/__init__.py`: `sha256:14e340575f28c2da083fef04a7bff158a4a2c9c4b7a11726f3d6d6f2abba4d5e`.
- `backend/src/kgfegmcp/prompts/service.py`: `sha256:acbaf7207b79968a11d6d8441e043ae6a522d92e16bb8ddfba44728392f1c9ad`.

Exact evidence identities (local preparation receipts contain full commands, artifact checksum maps and comparison outcomes):

- `/tmp/kgfegmcp-dev005-baseline.json`: `sha256:1a9d8f37fe668eda0c1d0280b7914dff249aefa9365179fd584928e36f9bce64`.
- `/tmp/kgfegmcp-dev005-build.py`: `sha256:37554b3f469afa09359411670d012c61493cf225eef70c57b70f3fc443583089`.
- `/tmp/kgfegmcp-dev005-feedback.py`: `sha256:10edf4c0e060df97de6d355c86b41707e31fa3dc07e7cde8e1d3abaa88034a0a`.
- `data/source_artifacts/learning_progressions/dev005/commands.json`: `sha256:6e66db4cc79483b24afdf37763b44cffc075a7b139d2341e583f47d87fec6e5a`.
- `data/source_artifacts/learning_progressions/dev005/checks/atomic-acceptance.json`: `sha256:bbd833d7d444494c4f9f18146a049365c25b89989a97a12f0ec29b63c4989db0`.
- `data/source_artifacts/learning_progressions/dev005/checks/content-feedback.json`: `sha256:0c7a96a030de08b9f1368922c5317b9230cbc21b140984460c2143d9a962c0eb`.
- `data/source_artifacts/learning_progressions/dev005/checks/assessed-identities.json`: `sha256:af0f06880a445b4530ac8995c6b560525a423589918aaab3733e0f7d43d4a35b`.

Per-framework build, read-only validation and specification receipt identities:

- `data/source_artifacts/learning_progressions/dev005/build_specs/ghana-nacca-primary-english-language-basic-1-3.json`: `sha256:27ad9c29a54d012571f5e42929b32b5cfdca4b39663b99d3d0a28defe8134516`.
- `data/source_artifacts/learning_progressions/dev005/checks/ghana-nacca-primary-english-language-basic-1-3-build.json`: `sha256:ad53d70e6e30e7fa8f1b3bf48ef6327aebafd6a382a26fab685f32f04944ded4`.
- `data/source_artifacts/learning_progressions/dev005/checks/ghana-nacca-primary-english-language-basic-1-3-revalidation.json`: `sha256:d04d63316975ec14610900e75f0e2e7ddfd07fe03d08cb43b73805412b5b7682`.
- `data/source_artifacts/learning_progressions/dev005/build_specs/ghana-nacca-primary-mathematics-basic-4-6.json`: `sha256:8e13b7dfbbdf6b482569ffaf0eb765f1379437b04c0b78a812a33eeef8156689`.
- `data/source_artifacts/learning_progressions/dev005/checks/ghana-nacca-primary-mathematics-basic-4-6-build.json`: `sha256:2aa04013a137a3fbf3993644ea2600759376bf1389e8b887c2632b6c2267d919`.
- `data/source_artifacts/learning_progressions/dev005/checks/ghana-nacca-primary-mathematics-basic-4-6-revalidation.json`: `sha256:f75efb7f972458aa4c8375eb9e95bc020197de1bc0e79ea3618a81ff9d6330d0`.
- `data/source_artifacts/learning_progressions/dev005/build_specs/india-cbse-science-learning-framework-classes-9-10.json`: `sha256:c568767512e4849ffc984c13cb746c3c243719b3656d613f83bd1e659abbd685`.
- `data/source_artifacts/learning_progressions/dev005/checks/india-cbse-science-learning-framework-classes-9-10-build.json`: `sha256:a0c96f59daa15aef6fb456ad1f2d5856ac1fb5cc94f98398b259b9356c98329f`.
- `data/source_artifacts/learning_progressions/dev005/checks/india-cbse-science-learning-framework-classes-9-10-revalidation.json`: `sha256:9a6da17e21f64679e73a758ded60cbe5892c51aa134d976dc1c85c34641ad781`.
- `data/source_artifacts/learning_progressions/dev005/build_specs/india-tamil-nadu-tnscert-mathematics-classes-1-5.json`: `sha256:daaaa4e718a7e21519fa5ae38abed1e5c76300c73bd552f12398da51f9e865de`.
- `data/source_artifacts/learning_progressions/dev005/checks/india-tamil-nadu-tnscert-mathematics-classes-1-5-build.json`: `sha256:cd4c9be0640f64519d600165ee5a583aaf987b97f70df8ac62d95f78d084fcbd`.
- `data/source_artifacts/learning_progressions/dev005/checks/india-tamil-nadu-tnscert-mathematics-classes-1-5-revalidation.json`: `sha256:261767a71fb55497afe9c7fcf1a2e1d78b862a40afeac97bdfc4a0ba288ca478`.
- `data/source_artifacts/learning_progressions/dev005/build_specs/nigeria-nerdc-mathematics-primary-1-3.json`: `sha256:2e639a83e293184069c2b586cd267945954890e84eb8210578ed248fa8d8c401`.
- `data/source_artifacts/learning_progressions/dev005/checks/nigeria-nerdc-mathematics-primary-1-3-build.json`: `sha256:304b9d5064814c8c46406a2ae55eb9a542ba3f136d3d19f47790ef692a58e176`.
- `data/source_artifacts/learning_progressions/dev005/checks/nigeria-nerdc-mathematics-primary-1-3-revalidation.json`: `sha256:f7c2fb693487cbee70764296be8d26dec9977e7befb8ead21c0f9bfeb5505e05`.
- `data/source_artifacts/learning_progressions/dev005/build_specs/rwanda-reb-mathematics-lower-primary-1-3.json`: `sha256:724874bfc0e5ffe6c9bc61d1dd9802abaacd73fa2722d237aa71bfc6c5352ec6`.
- `data/source_artifacts/learning_progressions/dev005/checks/rwanda-reb-mathematics-lower-primary-1-3-build.json`: `sha256:cd20f06d08cdf59d4ff8ce6798c99484a05a85078ce560aa60d11ee8bbc2db8d`.
- `data/source_artifacts/learning_progressions/dev005/checks/rwanda-reb-mathematics-lower-primary-1-3-revalidation.json`: `sha256:9b5d1dcc24ed636da80fc3c032ee5142b61dd08b0ffc67aa89bb138cb055864d`.

**Implementation Notes**

Removed progressionHeuristics from the profile model/collection validator and removed the hypothesis guidance class/export/overlay. Added typed optional curriculum-review, support-plan and teaching-sequence guidance models; configuration instruction accounting covers all nine retained/new overlay slots, including multigrade. The remaining old prompt renderer's references to the deleted configuration field/class were removed so imports and type checks remain valid during migration; its complete obsolete runtime removal remains DEV-017/DEV-021. Public prompt version remains 1.2.0 until the planned DEV-018 workflow implementation advances it to 1.3.0. Version 2.0.0 is the new prompt-configuration version, distinct from profile version 2.0 and schema version 1.1.

`node .standards/bin/check.mjs` and `git diff --check` passed after persisting completion and the DEV-023 blocker.

DEV-005 is DONE. The next dependency-ready approved step is DEV-023, but it has not started; wait for explicit user continuation. Verification cadence remains AFTER_IMPLEMENTATION, Current Increment NONE, plan IN_PROGRESS, and workflow DEVELOPING with no recovery/obligations. No full Developer handoff gate passes while later approved work is unfinished.

### DEV-023 — Replace all six package preparation sets and build specifications

`Status`: `DONE` `Depends On`: `DEV-005`
`Acceptance`: `AC-002, AC-003, AC-017, AC-018, AC-022, AC-027`

**Goal**

Make data/input_artifacts the maintained, reproducible preparation inputs for the six accepted AS/LC/LP replacements, then remove superseded preparation files and stale build references.

**Affected Area**

data/input_artifacts/{ghana_english,ghana_math,madhi_math,nigeria_math,pratham_science,rwanda_math}/delivery/, detailed/ and package_build.json; existing preparation CLI output selection as needed.

**Expected Outcome**

After all six replacements pass acceptance in the separate preparation root, each input set contains the corresponding normalized as_lc_lp_nodes_<token>.jsonl and as_lc_lp_relationships_<token>.jsonl delivery files, retained required AS/LC and LP detailed evidence, all 64 provenance partitions, index and sanitized normalization receipt. Updated package_build.json files reference profile version 2.0, the new delivery filenames and every required declared artifact, preserve authoritative framework/source/version metadata, and support rebuilding into a separate preparation root with repository-relative input paths. No preparation input depends on the external source folder or an old configuration version.

Verify all replacement inputs and specifications before deleting the corresponding superseded delivery files, outdated build references or obsolete preparation-only artifacts. Preserve unchanged required AS/LC evidence, unrelated files, and the exact source copies/copy receipt under data/source_artifacts/learning_progressions. Old preparation paths/hashes and replacement identities are recorded in implementation evidence; old versions remain recoverable in Git. input_artifacts and source_artifacts remain outside runtime discovery and MCPB staging. This step does not modify sealed accepted packages or user documentation.

**Self-Check**

Completed: all six maintained input sets contain the exact 86-artifact normalized AS/LC/LP payload plus updated package_build.json. Specifications bind profile version 2.0, declare all 64 provenance shards and build into a separate local root. All six dry-run proposals, actual builds, persisted atomic acceptance and read-only revalidation passed and reproduce the DEV-005 snapshot/package/profile/count/artifact identities. Only after that comparison passed were the twelve superseded delivery files removed. Sealed packages, configs, original copies and prepared/DEV-005 evidence remain unchanged.

**Actual Evidence**

- Assessed HEAD: `20f47ab2f50474aef5ac26f54341385338469652`; entry tracked working tree was clean. Working directory: `/Users/tzz/Projects/private/idi/KGForEdGlobalMCP`. User explicitly authorized DEV-023; its matching continuation blocker was cleared and this step alone changed to IN_PROGRESS. No recovery, outstanding obligation, mode/cadence change or material plan revision was needed. No Git commit or staging was performed.
- Executed `python3 /tmp/kgfegmcp-dev023-prepare.py`: inventoried 84 old input files and 1,526 protected files; verified the six DEV-005 accepted manifest/profile and full artifact byte identities, all 138 local copied source hashes, and prepared bytes before mutation. Backed up the complete old input tree under ignored `data/source_artifacts/learning_progressions/dev023/old_inputs/`. Copied 473 new/updated artifacts through checked temporary files and atomic per-file replacement: 450 new delivery/LP/shard files plus 23 previously reconciled producer metadata artifacts. The other 43 required AS/LC detailed files remain byte-identical. Six specifications were replaced after verifying their authoritative metadata, preserving jurisdiction, source publication/version, package revision, profile ID and snapshot relations. Old delivery files remained until rebuild verification succeeded.
- Executed `/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync python /tmp/kgfegmcp-dev023-build.py`. Its 19 established CLI invocations all exited 0: for each maintained specification, `kgfegmcp-build-manifest --spec <project>/data/input_artifacts/<set>/package_build.json --dry-run` and the same command without `--dry-run`; then `kgfegmcp-validate-packages pending`; then for each exact replacement `kgfegmcp-validate-packages one --framework-id <framework-id> --snapshot-id <snapshot-id> --read-only`. The orchestrator uses the same locked/offline/no-sync uv prefix with absolute backend directory; Python tooling executes in backend and subprocess working directory is the repository root. Command arguments, environment overrides, exit codes and output hashes are retained in commands.json.
- CLI environment explicitly bound `PATHS_PROJECT_DIR=<project>`, `KGFEGMCP_PROFILE_ROOT=<project>/config/profiles`, `KGFEGMCP_PROMPT_ROOT=<project>/config/prompts`, and `KGFEGMCP_GRAPH_PACKAGES_ROOT=<project>/data/source_artifacts/learning_progressions/rebuilt_packages`. This ignored isolated rebuild root is also the maintained specifications' repository-relative outputRoot. All actual input references are within the corresponding maintained input set; no build reads prepared/raw-copy or external-project inputs. The profile reference is 2.0, with no stale delivery/configuration paths. Existing builder/normalization/validation implementation sufficed; no production Python changes or new CLI contract were needed.
- All six pending packages atomically persisted to passed with no findings. Terminal read-only revalidation reported valid, terminalRevalidation true, readOnly true and persisted false, no findings, with identical terminal manifest bytes before/after. Entire rebuilt manifest content equals DEV-005 except createdAt and validation.validatedAt, which record this new build/acceptance event. Snapshot ID, graph package ID, profile ID/version/hash, every declared artifact path/checksum, all counts, framework/source/current metadata, rights, included graph types, capabilities and snapshot relations match. Every one of the 516 rebuilt artifacts is byte-identical to the DEV-005 accepted counterpart. Total stored edges remain 3,039 buildsTowards and 5,041 relatesTo. Full-evidence validation retains the same CBSE needs_review and Ghana warning evidence and does not promote those items into published edges.
- Executed `python3 /tmp/kgfegmcp-dev023-cleanup.py` only after all six rebuild/acceptance/revalidation/content comparisons passed. Rechecked every new input against prepared bytes and each obsolete file against its pre-migration hash, then deleted only the twelve old as_lc_nodes/as_lc_relationships delivery files. Final maintained inventory is exactly 522 files: 87 per set, including the specification, with 384 shards. Of the 84 previous input paths, 43 detailed files are unchanged, 23 detailed evidence files and six specs are updated, and twelve delivery files are removed. The 450 new paths consist of twelve normalized delivery files, 54 dedicated LP artifacts and 384 provenance shards. No unrelated/required file disappeared; final payload for each set exactly equals the prepared/accepted 86-artifact payload.
- Preservation check passed for all 1,526 entry protected files: backend source, every config version (including 1.0), old sealed active graph packages, source copies/copy receipt, normalized preparation, DEV-005 accepted replacements and previous local evidence. All hashes and sizes match. The old input backup also remains available locally; Git HEAD retains the old committed versions. Inputs are repository data, while provenance's historical producer paths/hashes remain original evidence rather than live dependencies. The 23 detailed metadata updates are exactly those reconciled in DEV-005; no curriculum/source text or graph edge was changed.
- `git check-ignore --stdin` confirmed all 522 maintained files are unignored, while new local receipts and rebuilt packages are ignored. Inspected existing Dockerfile and build_mcpb.py: they select config and data/graph_packages, excluding input_artifacts/source_artifacts from runtime distribution. These files were not changed; no distribution was built or deployed in this step. `git diff --check` passed after cleanup. Workflow validation passed at entry.
- Limits: these are Developer implementation checks, not independent Tester verification, semantic/pedagogical certification or runtime activation. No formal test suite was added/changed and no Python static checks were needed for this data/spec-only change. No external source access/modification, model/paid-service call, producer/checker regeneration, sampling, publication or deployed service update occurred. Full application bootstrap, new query surface, transports and staged distribution remain future approved work. Active sealed packages and version 1.0 configuration folders remain intact until DEV-017. DEV-012 and later steps have not started.

Maintained build specifications (reusable command prefix `/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync kgfegmcp-build-manifest --spec`, followed by the absolute specification path):

| Input set | Specification SHA-256 | Canonical 87-file input inventory SHA-256 |
|---|---|---|
| `data/input_artifacts/ghana_english/package_build.json` | `sha256:e24c249dceff96646d0630da12e56a20b49d6f6b881d0271fe8ce069dad951ad` | `sha256:ba3d99844a107516b263c4bde98fa10c6676be8e81d7bcd4761ab69ee626063d` |
| `data/input_artifacts/ghana_math/package_build.json` | `sha256:8eca68df6015f2fc99197a120073c88a78c8d0e17791bf040577347c47def260` | `sha256:e56c47326282231bcd1d8d7a7e15bdb115cf650e92fb8ae6724ab196a9a3cda5` |
| `data/input_artifacts/madhi_math/package_build.json` | `sha256:50397815509dbe255be2269a34852ec5d77d9d866fe87815a58bb9407389d945` | `sha256:914f1d5d40a025fda9dfa3e2afcbbdab066d7321fbfd979f28b9ccf91ee7c0c9` |
| `data/input_artifacts/nigeria_math/package_build.json` | `sha256:3989fb1ef27f20437ddde1883ffa9f50f8c1bdf9f920e57fba9d33b9c56f0dd7` | `sha256:2c19f0d71b7a05656a7cd970e2c9b379fdd7461c95c5b6d50bf2d3e01883502b` |
| `data/input_artifacts/pratham_science/package_build.json` | `sha256:77c5ac915b0c8d5bfc79dec51f3c572317c20586ab8b4c9479b5c7a0a87368ac` | `sha256:c7d46165150367ce4dd1ea36c59c3962540cbfa1d0866153ce91e81f7fbffc2f` |
| `data/input_artifacts/rwanda_math/package_build.json` | `sha256:d44e564ac1c9e1f750f7aa61de97aa0764d43d374a69ff2e5c4cde929e5d1477` | `sha256:75e5f84e497a8876d3cad9149bb1bd0a160361104e960cbe80b3c237531a4b1b` |

Rebuilt snapshot identities (graph package ID is the snapshot ID plus `--academic-standards--p1`; profile identities/artifact checksums match the DEV-005 tables and retained comparison receipt):

| Set | Snapshot ID | buildsTowards | relatesTo | Rebuilt accepted manifest SHA-256 |
|---|---|---:|---:|---|
| `ghana_english` | `ghana-nacca-primary-english-language-basic-1-3@2019+e00c5329a507` | 250 | 801 | `sha256:5cf5dbb35785b0ded64f062c19589b1601cd1f76e08cdddf991f9a1a14439f7b` |
| `ghana_math` | `ghana-nacca-primary-mathematics-basic-4-6@2019+0b768f7cfaf9` | 299 | 300 | `sha256:16ef563d4fea0a5f6d259580ef834b1231d4376c9d34b521e416b39960b70533` |
| `madhi_math` | `india-tamil-nadu-tnscert-mathematics-classes-1-5@2025-proposed-draft+aa0dd9310a0f` | 472 | 435 | `sha256:32e860054447d9dde6d6d7b15bddb118e33727111953f2c4671b0b3359ca359b` |
| `nigeria_math` | `nigeria-nerdc-mathematics-primary-1-3@undated+bc5e769ed26f` | 189 | 297 | `sha256:3b0616d3ad9c2d6017c7c9bd4f9624927875daf9d1a6cd46b0a2316916544479` |
| `pratham_science` | `india-cbse-science-learning-framework-classes-9-10@undated+576740bed2d1` | 891 | 2315 | `sha256:d7431e9e49ff4d4c99b985d3a42dd10bae506c406dca0e96c26d9d8159515a96` |
| `rwanda_math` | `rwanda-reb-mathematics-lower-primary-1-3@2025+2ee0fa308d13` | 938 | 893 | `sha256:7a00e1afee01ff60ba4862eb833e26a4f85c727f08447573d229c5a3e89b3e2b` |

Superseded delivery paths and their exact original byte identities (removed only after successful comparison):

| Previous path | Original SHA-256 |
|---|---|
| `data/input_artifacts/ghana_english/delivery/as_lc_nodes_ghana_english.jsonl` | `sha256:cdd93c3e5d42bc1f13d1deca34863a46e292d94668e3e11f524b0d01f53e4902` |
| `data/input_artifacts/ghana_english/delivery/as_lc_relationships_ghana_english.jsonl` | `sha256:36fef88e4622f8c63d0f1937873945c7cece861b5f235446a76ecc650ddac9e7` |
| `data/input_artifacts/ghana_math/delivery/as_lc_nodes_ghana_math.jsonl` | `sha256:24e662c76cca3d2a209615e4e8961f5b008a6857c2d2c1829bd59f1394a396ac` |
| `data/input_artifacts/ghana_math/delivery/as_lc_relationships_ghana_math.jsonl` | `sha256:28a904a0c1a496ad9d4065a5719aa7324d9c3e8b0b8e70c4c97ff8891ac5af1b` |
| `data/input_artifacts/madhi_math/delivery/as_lc_nodes_madhi_math.jsonl` | `sha256:df6b2ef0d01ad439fd1d10e214069c2006ec3527ce6b7bd4b00bc196289a4263` |
| `data/input_artifacts/madhi_math/delivery/as_lc_relationships_madhi_math.jsonl` | `sha256:d89b1aaabe5ea6db121f69233b3e5e466673660acc66b9bbd6382cf675e79575` |
| `data/input_artifacts/nigeria_math/delivery/as_lc_nodes_nigeria_math.jsonl` | `sha256:cebe0db559f29c93da432216ad468d1d2449cdc2019e66745809812c262b7252` |
| `data/input_artifacts/nigeria_math/delivery/as_lc_relationships_nigeria_math.jsonl` | `sha256:497d2896475adf959814845085beb73b153d23a372cce172c44d474a718870c2` |
| `data/input_artifacts/pratham_science/delivery/as_lc_nodes_pratham_science.jsonl` | `sha256:aa523e7642a63b29b301f9396e98c365849796ef1d68a87b8afdb19a5c8b1132` |
| `data/input_artifacts/pratham_science/delivery/as_lc_relationships_pratham_science.jsonl` | `sha256:490671e915dc261929d903b4bb211a0d5dc1fed3b3666398c25abf957eb09e72` |
| `data/input_artifacts/rwanda_math/delivery/as_lc_nodes_rwanda_math.jsonl` | `sha256:5baa25285b2ff926a168d6d2736c209713b2041c46b0be348aec98bb0761f00f` |
| `data/input_artifacts/rwanda_math/delivery/as_lc_relationships_rwanda_math.jsonl` | `sha256:6414f565f8ad02fd9dabf8e50f68998d7f644bde4525255f501b6858a0fdf23c` |

Exact implementation evidence identities:

- `/tmp/kgfegmcp-dev023-prepare.py`: `sha256:d66fe6fce9a76d936450e892da16ab8b396492ce484fe4986055ca8c0996df9a`.
- `/tmp/kgfegmcp-dev023-build.py`: `sha256:04a1fc0314413cf31163ce84777112d856ed6067c04ade20251999a63e3b8de8`.
- `/tmp/kgfegmcp-dev023-cleanup.py`: `sha256:466f9d50a3c245fc77eae1501aa1c4493291f829467a3de8a648a3c5dcf36841`.
- `data/source_artifacts/learning_progressions/dev023/baseline.json`: `sha256:d157b315de640f8b4887fd936746dc40e238372655b7c96bbab9b0263a8ee1df`.
- `data/source_artifacts/learning_progressions/dev023/migration-plan.json`: `sha256:a86804ebf5d84ea20b37a182028f6e04f3d0d9525425bf53b9ca80c8b05e675c`.
- `data/source_artifacts/learning_progressions/dev023/copied-files.json`: `sha256:c3ce60f13ac6b65660d2a8ea9926699787a170aedb66ea84dac0e74cb63a0ffb`.
- `data/source_artifacts/learning_progressions/dev023/new-inputs-before-cleanup.json`: `sha256:7c44d37e13f275dc66b92a726f3172599456dd58cbf80cecab9c24e9bb621225`.
- `data/source_artifacts/learning_progressions/dev023/commands.json`: `sha256:5f2e53b543d4897d4973340b156de1542521a285e5a8511682b8cf943f2db5fb`.
- `data/source_artifacts/learning_progressions/dev023/checks/atomic-acceptance.json`: `sha256:b775a6f651a9b5684ac2d10c682a75116a234a1f70724b473a6755f930a06cd4`.
- `data/source_artifacts/learning_progressions/dev023/checks/rebuild-comparison.json`: `sha256:f3b884d148434589522d3e4c1023f7b9183f4fa318ff89df8addf36150c9dc0c`.
- `data/source_artifacts/learning_progressions/dev023/checks/final-inventory.json`: `sha256:0c15ab6550c3ddc0a7df248886c44243f5f8f247c1232bdc3875eb899eada5fa`.
- `data/source_artifacts/learning_progressions/dev023/checks/input-set-identities.json`: `sha256:ce9850f0babe2cfc96a488a34a6f7acf00573e35c9b84b123a1d81cc5a925b5b`.

The baseline receipt records every old input/protected path, size and hash; final-inventory.json records every new path/hash and all removed/retained/updated paths. Canonical inventory hashes above bind the complete per-set content, using the encoding specified in input-set-identities.json. commands.json binds every per-set dry-run/build/revalidation output. The comparison receipt binds rebuilt versus original manifest byte hashes, profile/artifact identities, actual counts and both timestamp pairs. These local receipts are ignored preparation evidence; current maintained inputs and the workflow plan are version-controlled deliverables.

**Implementation Notes**

Normalized delivery filenames retain the framework-ID tokens produced by DEV-003, rather than introducing new short tokens: the sanitized normalization receipt and provenance index stay byte-identical, so exact artifact-set snapshot identities reproduce DEV-005. Shards remain under each set's additional/ directory with explicit logical-name mappings; the existing detailedArtifactsDirectory discovery includes all eleven AS/LC and nine LP detailed artifacts. The output root is safe local preparation, distinct from active graph_packages; activation remains DEV-017. The existing normalization command still stages verified output separately, and the maintained builder can rebuild directly from these repository input sets without raw copies or an external project.

`node .standards/bin/check.mjs` and `git diff --check` passed after saving completion and the DEV-012 continuation blocker.

DEV-023 is DONE. Plan remains IN_PROGRESS, STEPWISE, locked tony, AFTER_IMPLEMENTATION and Current Increment NONE; workflow remains DEVELOPING with no recovery or obligations. Next dependency-ready step is DEV-012; explicit user continuation is required. Suggested commit: `feat(data): replace preparation inputs with accepted learning progressions`.

### DEV-012 — Implement exact LP selection and shared evidence results

`Status`: `DONE` `Depends On`: `DEV-023`
`Acceptance`: `AC-005, AC-009, AC-010, AC-012, AC-018, AC-028, AC-031, AC-033`

**Frame 2 reopening — approved 2026-10-06**

Reopened for the compact derivation-artifact metadata and artifactInventoryNotice described in the Frame 2 Size-Correction Revision. Earlier DEV-012 evidence remains history for the superseded full artifact list.

Frame 2 self-check: PASS — see "Frame 2 compact metadata for DEV-012 — completed" in Plan Notes. Two Tester-owned formal cases encode the superseded contract and fail as expected; they go to Tester in the approved combined correction after DEV-015.

**Current Recovery Assignment — approved 2026-10-06**

Implement the shared ordinary encoder below MCP, canonical alias-keyed JSON (sorted keys, compact separators, ensure_ascii=False, original array order), conservative complete CallToolResult byte/character accounting including isError/metadata and escaping, and the thin five-LP adapter text path. Add compatible effective character-ceiling/continuation metadata while retaining useful public result fields. Exact lookup and shared candidate/indivisible-entry checks must enforce both <=1,048,576 UTF-8 bytes and <=100,000 Unicode code points; failure is progression_result_too_large with a usable read_evidence URI hint. Preserve rights, exact identities, excerpts/disclosures and safe error masking. No unrelated retained-tool text rewrite.

Affected area additionally includes mcp/tools/learning_progressions.py and a focused ordinary encoder helper reused by later access tools. Direct/search/traversal/path size hooks start using the shared encoder here; their detailed outcome reconciliation belongs to the next three steps.

Current self-check: PASS. See Plan Notes, Client-access recovery for DEV-012 — completed 2026-10-06, for actual final commands, 64 ad hoc checks, 13 existing tests, configured static checks, assessed content/receipt hashes and limitations.

The prior definition and execution evidence below remain history where superseded by this recovery assignment.

**Goal**

Introduce LearningProgressionsService with shared typed request/result, route, selector, rights, excerpt, evidence-identity and byte-budget helpers, then implement exact lookup.

**Affected Area**

services/learning_progressions.py and focused typed models; errors.py; accepted catalog/GraphStore and existing standards/rights helpers.

**Expected Outcome**

Exact LP lookup pins one package/snapshot and returns original stored edge/endpoints, generated judgment projection and resource links. Missing/non-LP IDs, missing/ambiguous standards, unavailable capability and invalid requests have distinct typed failures. Excerpts, semantic/origin notices and 1 MiB encoded result ceiling follow the architecture.

**Self-Check**

PASS — exact stored LP lookup and shared service contracts implemented. Working directory: `/Users/tzz/Projects/private/idi/KGForEdGlobalMCP`. Assessed HEAD: `9357949fb79d734514e493f51fe5d81a2434b0e8`; the entry tree was clean. All final commands below exited 0 against the changed-content identities recorded here.

- `services/learning_progressions.py` adds a frozen LearningProgressionsService using the existing accepted primary mixed-graph runtime. Route resolution pins the exact framework/snapshot once; no file read, graph reload, second GraphStore or generated relationship is needed for queries. Exact lookup accepts only stored buildsTowards/relatesTo IDs and retains the original GraphRelationship record instance, endpoint node/CASE IDs, code/type/grade facets, author/provider/license/attribution and bounded accepted judgment.
- `services/lp_models.py` adds immutable exact request/result and shared evidence-table/metadata/selector contracts. Existing node/CASE selectors and profile-governed exact-code search are reused; missing/nonstandard/ambiguous selectors preserve typed failures, unavailable code/LP capability stays distinct, semantic invalid codes use invalid_progression_request, and malformed request types/extra fields use normal Pydantic transport validation.
- Shared rights helper applies the existing reviewed/full-text/single-standard relationship policy. Metadata carries PackageReference (including exact profile version/hash), manifest byte hash, every declared source-artifact byte hash, retained coverage projection, request/limits, generated-origin/semantic/confidence notices and pinned evidence links. Standard statements are bounded to 2,048 characters with an explicit excerpt flag/full URI; accepted rationale/warning bounds and omitted/excerpt flags are preserved. Confidence is explicitly not a calibrated probability of learner success.
- Shared tool text is a concise summary, and shared size enforcement counts the UTF-8 JSON envelope of all text blocks plus aliased structured content, including escaping and conservative whitespace. The hard ceiling is 1,048,576 bytes. Oversized exact evidence fails progression_result_too_large with resource recovery guidance, without silently discarding original fields. New summary/provenance URI constructors reuse existing percent-encoding; no handler/template/tool/prompt inventory was registered or activated in this step.
- Offline feedback loaded all six maintained DEV-023 replacements through CatalogRepository/GraphPackageValidator and checked every one of 8,080 accepted LP IDs. All original edges, endpoints/facets, judgment values/flags, manifest/profile/artifact identities and generated semantics were checked. File reads were blocked during query execution. Final feedback reports 132 named checks plus exhaustive per-edge assertions. Synthetic cases supplement actual sources for Unicode statement clipping, CASE/scoped-code ambiguity, rights denials (review/full-text/single-standard), missing projections, and oversized retained attribution. Exact 1 MiB output passes; one byte over fails; multiple text blocks include Unicode, escaping and block overhead.
- All 2,462 pre-existing protected files under config, maintained input artifacts, sealed baselines, raw/prepared/accepted/rebuilt source artifacts and prior receipts retained exact hashes and inventories at feedback completion. Only this step's local ignored `dev012/checks` receipts were added afterward. Baseline packages/source artifacts/version 1.0 configurations remain preserved. No replacement activation, later development step, live LLM/paid-service call, producer/checker regeneration, deployment or publication occurred.

Actual final commands (run from the working directory above):

```sh
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync python /tmp/kgfegmcp-dev012-feedback.py
python3 /tmp/kgfegmcp-dev012-static.py
```

The persisted static script runs the existing offline uv runtime against these four changed modules: `src/kgfegmcp/services/lp_models.py`, `src/kgfegmcp/services/learning_progressions.py`, `src/kgfegmcp/errors.py`, `src/kgfegmcp/resources/uri.py`. Exact argv/cwd/exit/output for every command is retained in static-feedback.json: `black --check`, `isort --check-only`, `ruff check --select E,F,C90`, `mypy --cache-dir /tmp/kgfegmcp-dev012-mypy`, `pylint`, `interrogate --generate-badge /tmp/kgfegmcp-dev012-badge`, `node .standards/bin/check.mjs`, and `git diff --check`. Final outcomes: formatting unchanged; Ruff syntax/complexity passes; mypy no issues in four files; pylint 10.00/10 with the repository configuration/McCabe extension; interrogate 100%; workflow/whitespace checks pass.

During implementation, Ruff initially rejected long documentation/message lines; these were shortened. The first scratch feedback run rejected its oversized fixture because CatalogPackageRuntime correctly requires the GraphStore to retain the exact loaded record instances; the fixture was corrected to inject oversized projected evidence at the service boundary without altering accepted source records. An intermediate workflow check rejected the temporary Current Increment DEV-012 bookkeeping; it was restored to NONE as AFTER_IMPLEMENTATION requires. Final feedback and all static/workflow checks were rerun successfully after these corrections. No source acceptance or production query failure was hidden by those corrections.

Assessed production content identities:

- `backend/src/kgfegmcp/services/lp_models.py`: `sha256:16754291deabaaee2020bda51fc45b09ee33bb81f5850ed42ba611b2a2efba88`
- `backend/src/kgfegmcp/services/learning_progressions.py`: `sha256:6f6b8837406a5e2c12b476df2559cabe2a112f6450b4aa19821f3505541c6ece`
- `backend/src/kgfegmcp/errors.py`: `sha256:53464ff3819e8d70151c4c07b2808dcea1b5ab75407434fe1206221145ffe6c4`
- `backend/src/kgfegmcp/resources/uri.py`: `sha256:2ca7075533804d58946edf68d766dd8719fb6a98e6fa88adbc398bd0cc5977de`

Exact package and evidence identities (the artifact-map digest covers canonical compact JSON with sorted logical-name keys; the complete 86-entry maps and snapshot/package IDs remain in content-feedback.json and accepted manifests):

| Framework | Exact edges checked | Maximum encoded result bytes | Manifest byte SHA-256 | Profile byte SHA-256 | Artifact-map SHA-256 |
|---|---:|---:|---|---|---|
| ghana-nacca-primary-english-language-basic-1-3 | 1051 | 39108 | sha256:5cf5dbb35785b0ded64f062c19589b1601cd1f76e08cdddf991f9a1a14439f7b | sha256:fe2b269f7e76d0abf89d00799857602e17c8e76b6d1b4055797c662629ce7212 | sha256:95b8c46423fe81ba544a97357b8877e569d3b80b7def1a4b8c0f5604b6d72005 |
| ghana-nacca-primary-mathematics-basic-4-6 | 599 | 38147 | sha256:16ef563d4fea0a5f6d259580ef834b1231d4376c9d34b521e416b39960b70533 | sha256:4981190e0b1f79a924b92088ed7e78820961935a022ea1abcb13500e8136e848 | sha256:2c6ddb75470b8bad7a9021dd2b8fe7416eabe1ee9af3661e0e841eb737d9f00b |
| india-cbse-science-learning-framework-classes-9-10 | 3206 | 40267 | sha256:d7431e9e49ff4d4c99b985d3a42dd10bae506c406dca0e96c26d9d8159515a96 | sha256:5e5e9ed3ec1f52f296b0ff5538aff56e6f2b8f58cc87ba0a29ac6e892bf5f852 | sha256:e6c2d4a855c8b360c341afe3f6bb7fae879c8889dd24d4709c167bc22e15a706 |
| india-tamil-nadu-tnscert-mathematics-classes-1-5 | 907 | 40684 | sha256:32e860054447d9dde6d6d7b15bddb118e33727111953f2c4671b0b3359ca359b | sha256:8b9e1ffde3595ff24fa20bc2fa468fd952ec78aad6daaa4b19c1d5ebefc46595 | sha256:5ea590b21575ef269a107be21f5047b60cc54679ee856f0f8f0272fe8a0939a9 |
| nigeria-nerdc-mathematics-primary-1-3 | 486 | 37088 | sha256:3b0616d3ad9c2d6017c7c9bd4f9624927875daf9d1a6cd46b0a2316916544479 | sha256:b04a2bcefa88d2e235cd9a1f988ae6af7dd9e50da565ec7aa9a5ac76015cd3e8 | sha256:0148160d46f2e397240872cccb3356037249c74f6f1cf18e8ee5cc57651a5a54 |
| rwanda-reb-mathematics-lower-primary-1-3 | 1831 | 37493 | sha256:7a00e1afee01ff60ba4862eb833e26a4f85c727f08447573d229c5a3e89b3e2b | sha256:d3fc130a70ce0502fc07f93a8211124adbe69a3b36b6302cf463f728fb41e0b6 | sha256:9ad500a92d2483089f75e6aaa64704ab1dc919ee3f01ce26d599bbf5a0a3281e |

Local ignored feedback receipts and reproducible scripts:

- `data/source_artifacts/learning_progressions/dev012/checks/content-feedback.json`: `sha256:f9e3ec1c9c3c22b1f28585d796d4ee00f47419e339d691930974590f980e73dd`
- `data/source_artifacts/learning_progressions/dev012/checks/content-feedback.py`: `sha256:bf7db1bd9652cbfed759ba0c88fe388ca5db847f77e5596b23fc745ecceeefee`
- `data/source_artifacts/learning_progressions/dev012/checks/protected-inputs.json`: `sha256:fcfa03a6eadb4ee95161f2eca8c9b5e91ee363b65756ffdf08c87d3507d5aa12`
- `data/source_artifacts/learning_progressions/dev012/checks/static-feedback.json`: `sha256:74e4167b9a38e82fc07c212fdf77d88add0e75614c03bb8527c1d9af99778957`
- `data/source_artifacts/learning_progressions/dev012/checks/static-feedback.py`: `sha256:1033125e29267edc82925f1fd33209e0a5d39c04a8fd3a0fddb196368dd42f83`

Limitations: this is offline Developer implementation feedback, not independent Tester verification, semantic validation or pedagogical certification. Real packages do not naturally exercise every error/ceiling; named synthetic cases are explicitly recorded. The closed acceptance/catalog load is rechecked here, but source artifact read-only CLI revalidation was already established in DEV-023 and not repeated as a separate command in DEV-012. LP resources/MCP adapters/public bootstrap/transport checks remain their later planned increments; the migration checkout still selects sealed old packages until DEV-017 activation and may not bootstrap against the advanced profile schema. Formal test suites remain Tester-owned. Resource policy limits remain unchanged; full evidence links are governed by their eventual handlers and existing resource-size limits.

**Implementation Notes**

User explicitly authorized DEV-012 after DEV-023. Only DEV-012 implementation and its workflow records were changed. Conventional Commit suggestion: `feat(progressions): add exact stored relationship lookup`. STEPWISE pauses before DEV-013; verification cadence remains AFTER_IMPLEMENTATION, Current Increment NONE and WorkflowState DEVELOPING. DEV-013 and all later steps remain PENDING.

### DEV-013 — Implement direct connections and filtered paged discovery

`Status`: `DONE` `Depends On`: `DEV-012`
`Acceptance`: `AC-006, AC-007, AC-009, AC-010, AC-012, AC-028, AC-031, AC-033`

**Current Recovery Assignment — approved 2026-10-06**

Reconcile direct/discovery selection against the shared encoder's byte and character ceilings. Roll back the next whole edge and dependent node/match rows before either ceiling; resume at its real candidate position. Preserve deterministic type/ID order, bound cursor fingerprint (route, identity, selection and semantic limits), examined nonmatch advancement, work/page limits, counts and truthful output-size stopping reason. Reject an individually unreturnable entry before a zero-progress cursor; no silent edge loss. Text includes actual cursor and complete replay request/how to use it, and distinguishes complete empty pages from incomplete work-limited pages.

Current self-check: PASS — Tester-owned correction reconciled on RESUME; Developer reran the affected 26 discovery/exact/AS-LC cases successfully. Runtime text-only/boundary/static evidence remains applicable to unchanged source hashes. See Plan Notes, Developer resumption after DEV-013 Tester correction, for current commands/results, evidence reuse, preservation and next STEPWISE continuation.

The prior definition and execution evidence below remain history where superseded by this recovery assignment.

**Goal**

Expose directional direct links, symmetric related links and explicit endpoint-conjunction discovery with deterministic stateless continuation.

**Affected Area**

LearningProgressionsService/models, existing profile facet/standard lookup helpers and cursor conventions.

**Expected Outcome**

Direct results distinguish incoming/outgoing builds from related concepts and retain canonical orientation/IDs. Discovery validates all selectors/facets and either/both/source/target semantics. Ordering, bound cursor identity/filter fingerprint, examined-candidate advancement, 25/100 pages, 5,000 work budget and byte stopping report honest completeness and empty results.

**Self-Check**

PASS — direct connections and filtered paged discovery implemented. Repository working directory: `/Users/tzz/Projects/private/idi/KGForEdGlobalMCP`; uv commands select the existing backend runtime. Assessed HEAD: `c77c04125184f1192513ff85a67bb893f470322a`; entry tree was clean. Final static/style/workflow commands and both final runtime feedback scripts exited 0.

- `services/learning_progressions.py` adds get_standard_progressions and search_learning_progressions. Direct queries reuse the existing label-specific incoming/outgoing GraphStore indexes and distinguish incoming_builds, outgoing_builds and related meanings relative to the exact selected standard. Related queries combine both adjacency directions, deduplicate by original ID and preserve canonical stored orientation. Discovery uses one immutable sorted tuple index of original LP references per accepted runtime, constructed once at service initialization; it does not construct another GraphStore or scan/sort the whole source graph on each page. Existing shared route, rights, standard selector, endpoint/judgment projection and byte helpers are retained. Exact DEV-012 lookup remains intact.
- `services/lp_models.py` adds strict bounded direct/discovery request and shared collection/page/match contracts: default 25 / maximum 100 edges; positive StrictInt limits reject booleans/fractions/coercion; filter arrays at most 32 values, standard selectors at most 20, cursor at most 4,096 characters. Every result includes the original request, canonical effective filters, resolved standard node set, explicit endpoint_scope, per-endpoint matched criterion values/membership, connection meanings, deduplicated standard/relationship tables and exact evidence identities. Package per-type stored totals are separate metadata, independent of page counts or filtered matching counts.
- `services/lp_discovery.py` owns profile-governed normalized canonical facet matching, private checksum-bound cursor contracts and bounded page assembly. Existing normalize_facet_value rules and SearchService.get_node_facet_evidence provide normalization and standard grade/type evidence. Local grade and source statement aliases resolve through the selected profile; unsupported, blank, unsafe or normalized duplicate criteria, duplicate types/selectors, and unresolved standards fail explicitly. Criteria are OR within a field and AND across fields plus selector membership on one endpoint; either/both/source/target combines those complete endpoint conjunctions. No grade/type criterion is borrowed from the opposite endpoint. Grades remain retrieval facets; no LP edge supplies inferred grade or lexical evidence.
- Ordering is `(stored relationship label, original relationship ID)` independent of file order. Opaque base64url cursors carry strict format/version/position, exact package/profile identity and manifest byte hash, normalized operation/selection fingerprint and canonical SHA-256 checksum. Fingerprints bind connection meaning, type set, resolved node set, endpoint scope, canonical filters, page limit, fixed work/byte ceilings and facet normalizer version. Shape, canonical encoding, checksum, identity, fingerprint and candidate range are checked before scanning. Equivalent exact identifier namespaces/profile aliases preserve effective selection; changed meaning/route/filter/limit or stale identity rejects continuation as invalid_cursor. No session-local cursor state is required.
- At most 5,000 candidate relationships are examined per page. Nonmatches consume budget and advance the candidate position. Page/byte stops retain the first unconsumed entry; zero-match work-limited pages return continuation. Complete empty selections succeed. Counts expose examined/returned candidates, stopping reason, hasMore and isComplete; totalMatchingCount is exact only when the complete candidate stream was examined in the current page, otherwise null. Tool text explicitly identifies a page and separates stored coverage from absence of a pedagogical connection. Package rights are checked before either query returns content, including empty selections.
- The existing 1 MiB text-plus-structured-result limit includes all final cursor/count/request/match metadata. Whole entries are rewound if later nonmatches/final envelope overhead would exceed the ceiling; original IDs and next candidate position prevent loss or zero-progress byte loops. An entry that cannot fit alone fails progression_result_too_large with resource recovery guidance. No evidence field is silently dropped to fit.

Actual final execution commands (from the repository working directory above):

```sh
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync python /tmp/kgfegmcp-dev013-feedback.py
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync python /tmp/kgfegmcp-dev013-boundary.py
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync python /tmp/kgfegmcp-dev013-selectors.py
python3 /tmp/kgfegmcp-dev013-static.py
```

The main feedback script reloaded all six DEV-023 replacements through CatalogRepository/GraphPackageValidator and queried with file reads blocked. It reports 905 named checks and 382 actual direct/discovery pages. Exhaustive discovery returned all 8,080 original LP IDs exactly once in deterministic type/ID order. Direct queries were checked against original stored adjacency for all four connection meanings, including both relates endpoints; independent endpoint/filter oracles checked selectors/scopes/type/local-normalized facets. Checks cover deterministic repeated pages/cursors, missing standards, rights-boundary propagation, invalid filters/types/selectors/transport bounds, page sizes/deduplication, CASE/node namespace/alias-equivalent selection, stale manifest identity, direct/discovery or connection-kind mismatch, corrupted/malformed/recomputed-invalid cursors (including strict boolean/version/position rejection) and correctly checksummed out-of-range continuation. Synthetic endpoint evidence establishes no cross-endpoint mixing, OR-within/AND-across criteria, true complete empty results and both/source/target/either behavior. A 5,002-candidate synthetic stream establishes a 5,000-examination zero-match page followed by correct completion; artificial large retained attribution establishes byte continuation and oversized-single-entry failure.

Supplementary selector-feedback reports 16 named integration checks across all six frameworks: direct statement-code and CASE URI selectors agree with exact node selection; discovery code selectors agree with exact node membership; snapshots without profile-enabled code selection reject both methods as capability_unavailable. Queries use accepted in-memory runtimes with file reads blocked. Shared code ambiguity/policy behavior also retains DEV-012 evidence. Total named runtime feedback across these three scripts is 923 checks.

The separate boundary feedback adds two named checks for final-envelope rewind: a temporary 47,533-byte ceiling admits two initial entries, but 5,000 actual examinations and final cursor/count overhead require rewinding one complete entry to candidate position 1. Returned page sizes were 41,875, 43,040 and 36,243 bytes; examination counts 5,000, 5,000 and 2; stopping reasons byte_limit, work_limit and exhaustion. Both original matching IDs were returned once, with no skips. Artificial candidate/byte fixtures never modify the accepted package, GraphStore or production 1 MiB ceiling outside the scratch process.

Final static-feedback.json retains exact argv/cwd/exit/stdout/stderr for all commands against the three changed modules: `black --check`, `isort --check-only`, `ruff check --select E,F,C90`, `mypy --cache-dir /tmp/kgfegmcp-dev013-mypy`, `pylint`, `interrogate --generate-badge /tmp/kgfegmcp-dev013-badge`, `node .standards/bin/check.mjs` and `git diff --check`. Results: formatting unchanged; Ruff syntax/McCabe passes; mypy no issues in three files; pylint 10.00/10 under the repository configuration; interrogate 100%; workflow and whitespace checks pass. At final persistence, workflow/whitespace checks were run again and passed.

Initial static feedback found an unused import, long strings/examples and insertion positions that moved existing staticmethod decorators onto the new instance methods; these were corrected while preserving the existing helper semantics. The initial scratch feedback command exited 1 due to a script syntax error before runtime work; it was corrected. Subsequent complete runtime passes succeeded. Final review tightened integer-only cursor versions and added explicit package totals, then reran the main runtime script successfully. A remaining long string was split into adjacent literals afterward: Python AST equality was explicitly checked and the before/after hashes plus unchanged AST identity are retained in content-feedback.json. Main runtime results are reused across that formatting-only change; the separate final-envelope boundary feedback and final static checks assessed the final content. No failed runtime behavior or unresolved finding is deferred.

Final production content identities:

- `backend/src/kgfegmcp/services/lp_discovery.py`: `sha256:5e0354d79a3c0d73295f45ba47c3c82a040537e457f76db3bcfb9c731667de9a`
- `backend/src/kgfegmcp/services/lp_models.py`: `sha256:1e21bcbc6e4eb5859aac4df127d9f672d2891d846fa0b970f73d14efe410e5db`
- `backend/src/kgfegmcp/services/learning_progressions.py`: `sha256:d11f3fc1e273cfe8141e8493f5a5351c50181ae48eb65422951ed2611d290e0a`

Exact package/evidence identities (artifact-map SHA-256 covers sorted compact canonical JSON of the complete 86-entry logical-name/hash map; exact snapshot/package IDs and every artifact hash are retained in content-feedback.json and accepted manifests):

| Framework | Original edges retrieved | First 100-edge page bytes | Cursor characters | Manifest byte SHA-256 | Profile byte SHA-256 | Artifact-map SHA-256 |
|---|---:|---:|---:|---|---|---|
| ghana-nacca-primary-english-language-basic-1-3 | 1051 | 547893 | 1119 | sha256:5cf5dbb35785b0ded64f062c19589b1601cd1f76e08cdddf991f9a1a14439f7b | sha256:fe2b269f7e76d0abf89d00799857602e17c8e76b6d1b4055797c662629ce7212 | sha256:95b8c46423fe81ba544a97357b8877e569d3b80b7def1a4b8c0f5604b6d72005 |
| ghana-nacca-primary-mathematics-basic-4-6 | 599 | 534087 | 1092 | sha256:16ef563d4fea0a5f6d259580ef834b1231d4376c9d34b521e416b39960b70533 | sha256:4981190e0b1f79a924b92088ed7e78820961935a022ea1abcb13500e8136e848 | sha256:2c6ddb75470b8bad7a9021dd2b8fe7416eabe1ee9af3661e0e841eb737d9f00b |
| india-cbse-science-learning-framework-classes-9-10 | 3206 | 583840 | 1148 | sha256:d7431e9e49ff4d4c99b985d3a42dd10bae506c406dca0e96c26d9d8159515a96 | sha256:5e5e9ed3ec1f52f296b0ff5538aff56e6f2b8f58cc87ba0a29ac6e892bf5f852 | sha256:e6c2d4a855c8b360c341afe3f6bb7fae879c8889dd24d4709c167bc22e15a706 |
| india-tamil-nadu-tnscert-mathematics-classes-1-5 | 907 | 559118 | 1170 | sha256:32e860054447d9dde6d6d7b15bddb118e33727111953f2c4671b0b3359ca359b | sha256:8b9e1ffde3595ff24fa20bc2fa468fd952ec78aad6daaa4b19c1d5ebefc46595 | sha256:5ea590b21575ef269a107be21f5047b60cc54679ee856f0f8f0272fe8a0939a9 |
| nigeria-nerdc-mathematics-primary-1-3 | 486 | 515981 | 1079 | sha256:3b0616d3ad9c2d6017c7c9bd4f9624927875daf9d1a6cd46b0a2316916544479 | sha256:b04a2bcefa88d2e235cd9a1f988ae6af7dd9e50da565ec7aa9a5ac76015cd3e8 | sha256:0148160d46f2e397240872cccb3356037249c74f6f1cf18e8ee5cc57651a5a54 |
| rwanda-reb-mathematics-lower-primary-1-3 | 1831 | 559140 | 1087 | sha256:7a00e1afee01ff60ba4862eb833e26a4f85c727f08447573d229c5a3e89b3e2b | sha256:d3fc130a70ce0502fc07f93a8211124adbe69a3b36b6302cf463f728fb41e0b6 | sha256:9ad500a92d2483089f75e6aaa64704ab1dc919ee3f01ce26d599bbf5a0a3281e |

Local ignored reproducible feedback/identity receipts:

- `data/source_artifacts/learning_progressions/dev013/checks/boundary-feedback.json`: `sha256:83702a4855c88719a1bbfaa9eb0bc68935273421b9ed8374b23724102c24c88e`
- `data/source_artifacts/learning_progressions/dev013/checks/boundary-feedback.py`: `sha256:f3746140423b45d1433195a43d617b0e3cf8789bc7733b2c46eb81ff6e5b3fa0`
- `data/source_artifacts/learning_progressions/dev013/checks/content-feedback.json`: `sha256:a2c31924072286c13123c72de49c3e74fd3d94416672753a999d42f4af3cf41d`
- `data/source_artifacts/learning_progressions/dev013/checks/content-feedback.py`: `sha256:0d7adf790484dd98d32eaa9ba0826b2445a16171f380b1c8492e6a14c28d335c`
- `data/source_artifacts/learning_progressions/dev013/checks/protected-inputs.json`: `sha256:58684c1e94ef3d0b9a0e1ff0cf21d6405dfb65b848911997e40aaf42942f26fa`
- `data/source_artifacts/learning_progressions/dev013/checks/static-feedback.json`: `sha256:1ad7b330beffc290477008fed3f3bdc0146f9f3814f9d3f3abe9f53c9725f51c`
- `data/source_artifacts/learning_progressions/dev013/checks/static-feedback.py`: `sha256:5249c4b77c4a55ff311d0d9f036d1767806e27b9c475bceb806a9294bbe82a21`

- `data/source_artifacts/learning_progressions/dev013/checks/selector-feedback.py`: `sha256:7fffb601324f7546e53407f1a41e14a8954babc9a75b7141bebfa77e6beeabfa`
- `data/source_artifacts/learning_progressions/dev013/checks/selector-feedback.json`: `sha256:b38dfb58065f4ecd7fa07f12bb5a51272cc9bc4080a9ca0090ec4c7cdbce82ea`

All 2,467 pre-existing protected config, maintained input, sealed baseline, raw/prepared/accepted/rebuilt artifact and prior receipt files retain their exact hashes and inventories; this was rechecked before saving these new ignored dev013/checks receipts. No configuration/source/package artifact changed and no replacement was activated. No MCP tool/resource/prompt registration, traversal/path implementation, later DEV step, live LLM/paid-service call, producer/checker regeneration, transport/deployment change or publication occurred.

Limitations: this is offline Developer implementation feedback, not independent Tester verification, pedagogical/semantic validation or full acceptance certification. Actual source packages cannot exercise every budget/ambiguity boundary; temporary projections and artificial candidate streams/byte ceilings supplement them explicitly. Collection methods reuse DEV-012 exact/code selectors and existing typed domain/resource errors; transport registration/bootstrap/resource handlers remain planned later work. Formal test suites and transport-wide acceptance remain Tester/later increments' responsibilities. The advanced-schema checkout may not bootstrap against sealed legacy active packages until DEV-017; no legacy compatibility path or activation was introduced to hide that boundary.

**Implementation Notes**

User explicitly authorized DEV-013 after committed DEV-012. This step changes only LP service/models, the focused discovery helper and its workflow records. Conventional Commit suggestion: `feat(progressions): add direct links and filtered discovery`. STEPWISE pauses before DEV-014; Verification Cadence AFTER_IMPLEMENTATION, Current Increment NONE and WorkflowState DEVELOPING remain unchanged. DEV-014 and all later steps remain PENDING.

### DEV-014 — Implement bounded upstream and downstream traversal

`Status`: `DONE` `Depends On`: `DEV-013`
`Acceptance`: `AC-008, AC-009, AC-010, AC-018, AC-028, AC-031, AC-033`

**Current Recovery Assignment — approved 2026-10-06**

Reconcile traversal whole-edge admission and final output against both shared envelope ceilings. Preserve the corrected individually oversized-edge failure, breadth-first branch/merge retention, distances, stored upstream orientation, work/depth/node/edge limits and pending frontier bookkeeping. Include compatible character limits and an explicit noncontinuation notice: clients may narrow bounded inputs and rerun. A size-limited result remains coherent and accurately reports scopeComplete, graphExhausted and truncation reasons; never clip a JSON string or drop an edge after service selection.

Current self-check: PASS after Tester's scoped fixture correction — all 16 formal algorithm cases, eight traversal/protocol/AS/LC regressions and 3510 rerun feedback assertions pass on unchanged runtime identities; see "Developer resumption after DEV-014 Tester correction" in Plan Notes. Earlier assessment, retained as history: PARTIAL. Offline feedback passed 3510 assertions, 406 accepted-package queries and 20 synthetic outcomes, including nonempty upstream/downstream canonical text and actual serialized envelopes. Eight traversal/protocol/AS/LC regressions and all six changed-module static checks pass. The additional formal traversal algorithm selection has two fixture failures and four passes; route a scoped VERIFICATION correction to Tester before finalizing this step. See the current DEV-014 implementation assessment and Suspended Assignment 2 in Plan Notes. Preserve historical checks and all prior correction evidence.

The prior definition and execution evidence below remain history where superseded by this recovery assignment.

**Goal**

Return a deterministic builds-only reachable subgraph with exact stored edges and explicit frontier/completeness.

**Affected Area**

LearningProgressionsService traversal helpers/models; existing label adjacency indexes.

**Expected Outcome**

Breadth-first traversal preserves branching/merging edges and upstream stored orientation. Depth 8/12, nodes 100/250, edges 100, work 5,000 and byte limits are enforced before excess work/allocation; depth-frontier inspection consumes budget. Distances, scopeComplete, graphExhausted and reasons distinguish bounded evidence from global exhaustion.

**Self-Check**

PASS — bounded builds-only upstream/downstream traversal implemented and checked offline. Working directory: `/Users/tzz/Projects/private/idi/KGForEdGlobalMCP`. Assessed HEAD: `24dee0f150eb360ab298eadb04ec0ec70c272994`; entry tracked working tree was clean. The user explicitly authorized this one dependency-ready step; only its matching continuation blocker was cleared. The plan stays IN_PROGRESS with STEPWISE, locked style tony, AFTER_IMPLEMENTATION and Current Increment NONE.

**Implemented outcome**

- Added frozen typed traversal request/result, distance/frontier/counter contracts and a focused `services/lp_traversal.py` helper. Requests strictly reject coercion, booleans, invalid directions and nonpositive/excess bounds: depth default 8/max 12; nodes default 100/max 250 including origin; edges default/max 100. Fixed adjacency work 5,000 and text-plus-structured UTF-8 result ceiling 1,048,576 bytes remain service constants.
- Reuses the accepted runtime, exact standard/code/CASE selectors, rights policy, metadata, endpoint summaries and original relationship/judgment projections. At service construction, existing builds-only incoming/outgoing GraphStore adjacency is sorted into immutable original-reference tuples by relationship ID; query work never sorts or copies an unbounded adjacency list. No second graph store, file reads during query, altered accepted records or pedagogical inference.
- BFS deduplicates nodes/edges while retaining branching, merging and cycle-closing edges. Minimum directional hop distances are separate from original source/target orientation; upstream never reverses stored records. Internal edges between returned nodes also survive depth-frontier inspection. hasChild, supports and relatesTo never participate.
- Applies node/edge caps before evidence/queue admission and work before each adjacency inspection. Depth-frontier edges consume actual work. `scopeComplete` reports complete requested-depth evidence; depth-only truncation leaves it true while `graphExhausted` is false. Node/edge/work/byte interruptions leave both false. Frontier gives returned node/depth, examined depth-excluded edge count and pending adjacency count; pending includes an inspected entry whose admission was blocked. Counters distinguish actual examinations, depth examinations, fully inspected nodes and returned rows. Exact exhausted ceilings and isolated valid standards do not falsely truncate.
- Reserves bounded worst-case final counter/reason/frontier overhead before accepting each entry, then checks the actual final shared tool envelope. Reservation can conservatively stop a later entry early. A first entry that fits its exact final envelope survives reservation and returns with explicit byte frontier (or full exhaustion when no frontier remains); an actually oversized single entry fails progression_result_too_large with resource recovery. Excess entries and their speculative endpoints are omitted together. No traversal cursor or synthetic direct relationship; notices explain derived evidence, rerun with changed bounded inputs and absent-edge limits.

**Actual commands and results**

Runtime feedback and repository Python tools used `/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync` from the repository directory above; no install/sync/network/model/API/paid-service execution.

- `python /tmp/kgfegmcp-dev014-feedback.py` — final exit 0: 3,495 named checks, 406 actual accepted-package queries and 17 synthetic outcome records. All six DEV-023 replacements loaded through CatalogRepository/GraphPackageValidator read-only. Query calls ran with Path.open, Path.read_bytes and builtins.open blocked. Independent whole-graph reachable-set/minimum-depth and induced-edge oracles compared complete depth-1/depth-8 results for high-degree and isolated samples in both directions; every returned edge was the original accepted builds record with original endpoint/rights/provenance/judgment identity, and all 3,039 builds edges were checked in both immutable sorted indexes. Repeated envelopes, exact node/CASE/code selections, unavailable code, missing framework/standard, root rejection and rights failures passed.
- Synthetic feedback passed branch/merge diamond order, upstream orientation, cycles including a closing edge at requested depth, complete empty subgraph, depth-only versus exhausted distinction, node/edge stops, strict request schemas, depth 12 versus thirteenth hop, exact 100-edge exhaustion, depth-frontier work stop at 5,000 actual examinations and exact 5,000 completion. UTF-8 attribution expansion established whole-entry byte stop, oversized-single-entry failure and both complete/incomplete fitting first-entry envelopes at exactly 1,048,575 bytes.
- `python /tmp/kgfegmcp-dev014-regression.py` — final exit 0: 905 prior direct/discovery implementation checks, 382 actual pages and all 8,080 original LP IDs retrieved once. Existing selectors/filters/cursors/counts/work/byte/endpoint behavior remains usable with the new shared service constructor. Its protected-input comparison passed against this step's entry inventory.
- `python3 /tmp/kgfegmcp-dev014-static.py` ran Black --check, isort --check-only, Ruff `check --select E,F,C90`, mypy `--cache-dir /tmp/kgfegmcp-dev014-mypy`, pylint and interrogate `--generate-badge /tmp/kgfegmcp-dev014-badge` on learning_progressions.py/lp_models.py/lp_traversal.py. All exit 0: mypy no issues in three files, pylint 10.00/10 and McCabe <=10, docstrings 100%. Workflow `node .standards/bin/check.mjs` and `git diff --check` also passed; final persisted-state `node .standards/bin/check.mjs` and `git diff --check` each exited 0 after saving DONE and the DEV-015 blocker. The final post-record comparison also confirmed all 2,476 original files plus exactly nine local receipt additions, and verified persisted source/receipt hashes.
- Initial static feedback found an overlong module docstring and McCabe 11 in edge admission; shortened the docstring and separated admission/rollback from depth/node/edge decisions. Initial scratch traversal feedback referenced `framework_node` instead of the existing `framework_root`; corrected the feedback script. Initial regression feedback completed query cases then stopped on its historical DEV-013 inventory (which preceded nine later DEV-013 receipts); reran with the current DEV-014 entry inventory. These iterations are not counted as passes. No package data or contract workaround was applied.
- Independent final preservation comparison confirmed every byte and path in all 2,476 entry files under config, sealed active packages, maintained input artifacts and source/prepared/replacement/evidence roots unchanged. Only new ignored DEV-014 receipts were subsequently added. One unrelated whitespace-only line removal in lp_discovery.py appeared in the working diff during execution and was left intact; DEV-014 does not depend on it.

**Assessed implementation identities**

| File | SHA-256 |
|---|---|
| `backend/src/kgfegmcp/services/learning_progressions.py` | `sha256:fd56fd282f26e235022094c26713de0cfd63a537912f4e942ecc74712db8b218` |
| `backend/src/kgfegmcp/services/lp_models.py` | `sha256:2b0bd8e28f8c9e56f41698b510332ef4d79740ec3c5b3cfba1dbf5545b1366fa` |
| `backend/src/kgfegmcp/services/lp_traversal.py` | `sha256:35c7a0a33f66f217f6403c6c6b34f46e1e8555a702e2b09c831740bf444e05e8` |

**Accepted query input identities**

All six are mixed academic_standards revision 1 packages, graphPackageId = exact snapshot below plus `--academic-standards--p1`; profile ID = framework, profile version 2.0. Each result retains all 86 declared artifact identities. Artifact-table digest hashes the sorted compact JSON logical-name→SHA-256 map; full maps and exact package references are in content-feedback.json.

| Exact snapshot | Manifest bytes | Profile bytes | 86-artifact hash-table digest | Queries / stored builds |
|---|---|---|---|---|
| `ghana-nacca-primary-english-language-basic-1-3@2019+e00c5329a507` | `sha256:5cf5dbb35785b0ded64f062c19589b1601cd1f76e08cdddf991f9a1a14439f7b` | `sha256:fe2b269f7e76d0abf89d00799857602e17c8e76b6d1b4055797c662629ce7212` | `sha256:95b8c46423fe81ba544a97357b8877e569d3b80b7def1a4b8c0f5604b6d72005` | 68 / 250 |
| `ghana-nacca-primary-mathematics-basic-4-6@2019+0b768f7cfaf9` | `sha256:16ef563d4fea0a5f6d259580ef834b1231d4376c9d34b521e416b39960b70533` | `sha256:4981190e0b1f79a924b92088ed7e78820961935a022ea1abcb13500e8136e848` | `sha256:2c6ddb75470b8bad7a9021dd2b8fe7416eabe1ee9af3661e0e841eb737d9f00b` | 68 / 299 |
| `india-cbse-science-learning-framework-classes-9-10@undated+576740bed2d1` | `sha256:d7431e9e49ff4d4c99b985d3a42dd10bae506c406dca0e96c26d9d8159515a96` | `sha256:5e5e9ed3ec1f52f296b0ff5538aff56e6f2b8f58cc87ba0a29ac6e892bf5f852` | `sha256:e6c2d4a855c8b360c341afe3f6bb7fae879c8889dd24d4709c167bc22e15a706` | 68 / 891 |
| `india-tamil-nadu-tnscert-mathematics-classes-1-5@2025-proposed-draft+aa0dd9310a0f` | `sha256:32e860054447d9dde6d6d7b15bddb118e33727111953f2c4671b0b3359ca359b` | `sha256:8b9e1ffde3595ff24fa20bc2fa468fd952ec78aad6daaa4b19c1d5ebefc46595` | `sha256:5ea590b21575ef269a107be21f5047b60cc54679ee856f0f8f0272fe8a0939a9` | 68 / 472 |
| `nigeria-nerdc-mathematics-primary-1-3@undated+bc5e769ed26f` | `sha256:3b0616d3ad9c2d6017c7c9bd4f9624927875daf9d1a6cd46b0a2316916544479` | `sha256:b04a2bcefa88d2e235cd9a1f988ae6af7dd9e50da565ec7aa9a5ac76015cd3e8` | `sha256:0148160d46f2e397240872cccb3356037249c74f6f1cf18e8ee5cc57651a5a54` | 67 / 189 |
| `rwanda-reb-mathematics-lower-primary-1-3@2025+2ee0fa308d13` | `sha256:7a00e1afee01ff60ba4862eb833e26a4f85c727f08447573d229c5a3e89b3e2b` | `sha256:d3fc130a70ce0502fc07f93a8211124adbe69a3b36b6302cf463f728fb41e0b6` | `sha256:9ad500a92d2483089f75e6aaa64704ab1dc919ee3f01ce26d599bbf5a0a3281e` | 67 / 938 |

**Local receipts and limits**

Retained under ignored `data/source_artifacts/learning_progressions/dev014/checks`. Scratch commands above are the actual runs; saved script copies use persisted local receipt inputs for resumption and allow only this step's receipt additions when comparing inventory. They are Developer ad hoc feedback, not formal Tester-owned test artifacts. Actual commands/stdout/stderr/exit codes, changed hashes, full package/artifact maps and protected inventory are persisted:

| Receipt | SHA-256 |
|---|---|
| `content-feedback.json` | `sha256:ee67595e341fb343997a6588ce7788c8390c09de31cabf7b2a53878cb920e839` |
| `content-feedback.py` | `sha256:d9ff39905ce55da4733fd1e08b41cede0bc3983bac3fb2f41b97b09ed51c8e31` |
| `evidence-index.json` | `sha256:74ebe2660f86a6c55f650a3f40dc66db27751cc5f087f4f9729dd59f50853ae8` |
| `preservation.json` | `sha256:07814b17c551dab08346700a1ae62ad7e0924a8766be08aa5b1845067344dd63` |
| `protected-inputs.json` | `sha256:b9060c308d795b3623d57341c03a1e6a6de10e989992ff4038fb0c96af88780f` |
| `regression-feedback.json` | `sha256:c8dc44fdcc6e48bd1d3ec0e5ba89494c0c121ea2a6b7a5b416588903eb06562d` |
| `regression-feedback.py` | `sha256:836d153920dd538187549c408f9ed2707c123feda43e5303f560fd098cc08e44` |
| `static-feedback.json` | `sha256:34f2caac26f2945e881f929420b521ec0176c68ab954cb9d236470d3a6556ba8` |
| `static-feedback.py` | `sha256:e07f0c8effdf2e806019fdb8efbbd3b6a27af7ed421c02925671974d486935f2` |

No formal AC acceptance or pedagogical correctness is claimed. Accepted-package query samples plus all-edge index checks are supplemented by synthetic cycle/high-frontier/large-entry cases; the accepted six curricula have no such generated artificial records. Public MCP registration, connecting paths, resource handlers, bootstrap/replacement activation and transport/distribution verification remain their later approved steps. The incomplete schema-migration checkout retains the previously recorded legacy-bootstrap limitation until DEV-017; no activation, compatibility alias, original/source change, producer regeneration or deployment occurred.

**Continuation**

DEV-014 is DONE. Suggested Conventional Commit: `feat(progressions): add bounded upstream and downstream traversal`. STEPWISE pauses before DEV-015 (bounded connecting paths without losing alternatives), which remains PENDING. Effective cadence AFTER_IMPLEMENTATION, Current Increment NONE, workflow DEVELOPING, historical Architect handoff and inactive recovery/obligations are preserved; the full Developer handoff gate does not pass while later steps remain unfinished.

### DEV-015 — Implement bounded connecting paths without losing alternatives

`Status`: `DONE` `Depends On`: `DEV-014, DEV-012`
`Acceptance`: `AC-008, AC-009, AC-010, AC-028, AC-031, AC-033`

**Frame 2 revision — approved 2026-10-06**

Replace whole-request failure on a later oversized path with the path size stop and nextUnreturnedPath; only an unfittable first path fails, with its relationship IDs in details. Depends on the compact metadata from reopened DEV-012 so real envelopes can be measured. See the Frame 2 Size-Correction Revision.

Frame 2 self-check: PASS — see "Frame 2 path size stop for DEV-015 — completed" in Plan Notes. Superseded formal cases go to Tester in the combined correction now routed.

**Current Recovery Assignment — proposed 2026-10-06**

Reconcile connecting-path admission and final output with both shared envelope ceilings, keeping whole paths/edge and node tables, alternative-path order, per-path cycle protection, fixed work/queue/depth/path limits and truthful incomplete absence/frontier counters. Expose effective character ceiling and explicit lack of continuation. Reject unreturnable indivisible evidence rather than silently dropping it or returning a misleading exhausted result.

Current self-check: PARTIAL — wording/standalone-size reconciliation is implemented and its offline feedback, 39 regression cases and six static checks pass, but measured real-package envelopes show the approved path maxima and oversized-later-path failure cannot serve longer real connections; ARCHITECTURE failure routed. See "Client-access recovery for DEV-015 — implementation assessed" and Suspended Assignment 3 in Plan Notes. Originally planned self-check: offline ad hoc nonempty directed multi-hop/path text-only consumption at pinned identities, synthetic branching/merging/Unicode/whole-path-size boundaries and existing path/algorithm checks as implementation feedback; measure actual emission and run changed-module static checks. No new formal test suite or pedagogical acceptance claim.

The prior definition and execution evidence below remain history where superseded by this recovery assignment.

**Goal**

Find directed simple builds paths between two exact standards using breadth-first partial paths.

**Affected Area**

LearningProgressionsService path helpers and typed path request/result models.

**Expected Outcome**

Paths retain alternatives through merging branches, ordered by hop count then edge-ID tuple. Default depth 6/paths 3, maxima 12/20, work/queue 5,000 and byte ceilings apply. Per-path visited sets prevent loops; target paths do not expand. Missing/invalid endpoints, same endpoint and incomplete zero-path search are explicit.

**Self-Check**

PASS — bounded directed simple connecting paths implemented and checked offline. Working directory: `/Users/tzz/Projects/private/idi/KGForEdGlobalMCP`; assessed HEAD: `0be6494de414fb8367485c28309733ddb00423a7`, with the three source identities below. Entry working tree was clean. The user explicitly authorized DEV-015 only; its matching continuation blocker was cleared before implementation. Plan remains IN_PROGRESS, STEPWISE, locked tony, AFTER_IMPLEMENTATION, Current Increment NONE; workflow remains DEVELOPING with historical Architect handoff and inactive recovery/obligations.

**Implemented outcome**

- Added `services/lp_paths.py`, strict frozen path request/result/counter/frontier contracts, the shared service method `get_learning_progression_paths` and concise tool text/size support. Reuses DEV-014's immutable builds-only sorted adjacency and the exact accepted runtime, route, node/CASE/code selectors, rights policy, endpoint summaries, original relationship/judgment projections and metadata/byte encoder. No new graph store, source reads during queries, relationship inference or public MCP registration.
- Breadth-first partial paths retain their own bounded visited-node tuples. Both prefixes through a merging node survive and are expanded independently; no global visited pruning. Neighbors are original builds edges sorted by ID, so completed paths are ordered by hop count then relationship-ID tuple independently of export order. Completed target paths never expand; cycles cannot repeat nodes. hasChild, supports and relatesTo cannot become hops. Every complete path references ordered original relationship IDs and node IDs in deduplicated evidence tables; tables include both exact endpoints even for a zero-path result.
- StrictInt depth defaults to 6/max 12, returned paths to 3/max 20. Fixed work and cumulative queue admission ceilings are 5,000; the source partial state counts toward admission. Bounds apply before excess adjacency inspection or partial-state allocation. Reports actual examined edges, charged depth-frontier inspections, enqueued states, peak queue and returned paths; frontier reports queued states, pending adjacency and depth-excluded extensions. At requested depth, unseen extensions consume work and set depth_limit; visited cycle closures do not imply an unexplored simple path. No traversal cursor or retry bypass.
- `scopeComplete` means complete enumeration within the requested depth; depth-only exclusion preserves it while `graphExhausted` is false. Path/work/queue/byte stops make both false. Exhaustion is explicitly scoped to source-to-target simple-path search with targets terminal, rather than every edge reachable beyond the target. Zero paths under a hard budget is incomplete; even exhausted absence means no stored connection, not no pedagogical connection. Same standard selected through any namespaces fails invalid_progression_request; missing/ambiguous standards, invalid routes and unavailable capabilities retain shared typed failures.
- Shared 1,048,576-byte UTF-8 text-plus-structured envelope ceiling includes request, original generated evidence, exact identities, final counters/frontier/reasons and JSON escaping. Before admitting each path, reserves worst-case bounded final metadata; reservation may conservatively stop early. A fitting first path survives reservation using its actual final frontier and stops further work when needed. A combination that exceeds the ceiling rolls back the whole last path and its exclusive evidence, retaining it in the queued frontier. An individually oversized first or later path raises progression_result_too_large with resource recovery; no entry is silently clipped. Paths have deterministic_derived status; original hops retain llm_inferred origin/attribution and accepted judgment disclosures.

**Actual commands and results**

All runtime Python commands used `/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync` from the repository directory above; effective Python working directory is backend. Existing Python 3.13 environment was used without installation/sync/network/model/paid-service execution.

```sh
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync python /tmp/kgfegmcp-dev015-feedback.py
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync python /tmp/kgfegmcp-dev015-regression.py
python3 /tmp/kgfegmcp-dev015-static.py
```

- Final path feedback exit 0: 659 named checks, 214 actual accepted-package path queries and 23 recorded synthetic outcomes, plus 60 deterministic randomized DAG/cyclic-graph queries checked against independent depth-first enumeration followed by contractual sorting. All six DEV-023 replacements load read-only through CatalogRepository/GraphPackageValidator. All query calls execute with Path.open, Path.read_bytes and builtins.open blocked. Real direct/multi-hop/reverse-pair samples match the independent whole-edge DFS oracle; returned evidence agrees with exact lookup, original accepted instances, exact IDs/facets/manifest/profile/artifact hashes and generated origin. Repeated envelopes and node/CASE UUID/CASE URI/profile-enabled code selectors agree. Same endpoint across namespaces, missing/root endpoints/frameworks, unavailable LP/code and rights failure propagation are explicit.
- Synthetic checks pass merging diamond alternatives, reversed input order, reverse-direction absence, target-terminal behavior, per-path cycle safety, complete isolated absence, depth 6/12 with charged frontier, exact twelfth-hop target, path caps 1/3/20 and an exactly exhausted one-path cap. Work stops before edge 5,001 and exact 5,000 examination exhaustion does not falsely truncate. Queue insertion stops before state 5,001 with 4,999 queued alternatives; exactly 5,000 cumulative admitted states can exhaust normally. Zero-path work/queue searches are incomplete. UTF-8 combination overflow rolls back whole-path evidence; oversized first and later individual paths fail. Both fully exhausted and pending-frontier first-path envelopes fit exactly 1,048,576 bytes; one byte over is rejected. Strict malformed/coerced/boolean/nonpositive/excess bounds and unsupported cursor are rejected; schema maxima are 12/20.
- Traversal regression exit 0: 3,495 prior DEV-014 checks, 406 actual accepted-package traversal queries and 17 synthetic outcomes. Both directions, reachable/induced-edge/minimum-depth oracles, original adjacency references, selectors/rights, branching/merging/cycle behavior, depth/node/edge/work/byte ceilings and empty/exhausted distinctions remain intact. No direct/discovery helper or adjacency-construction implementation changed; their persisted DEV-013/014 evidence remains supporting history rather than a claim of a new full-suite run.
- Final static feedback retains exact argv/cwd/exit/stdout/stderr: Black --check, isort --check-only, Ruff `check --select E,F,C90`, mypy `--cache-dir /tmp/kgfegmcp-dev015-mypy`, pylint and interrogate `--generate-badge /tmp/kgfegmcp-dev015-badge` on learning_progressions.py/lp_models.py/lp_paths.py all exit 0. Mypy reports no issues in three files; pylint 10.00/10 under the repository McCabe <=10 configuration; docstrings 100%. Workflow `node .standards/bin/check.mjs` and `git diff --check` pass, and are rerun after this DONE/blocker record.
- First static pass found a Black formatting change after final-metadata reservation adjustment; formatted it. A later temporary byte-boundary calibration used 1,040,000 attribution characters without allowing the full shared metadata overhead, correctly raising the size error; corrected the scratch calibration to measure a fitting baseline. These preliminary runs are not counted as final passes. Final runtime/static results above assessed the final source bytes. No accepted-data alteration or bound weakening was used.
- Independent pre/post comparison preserves every byte and path of all 2,485 entry protected files under config (including original version 1.0 and new 2.0), sealed active packages, maintained inputs, raw/prepared/rebuilt/replacement artifacts and earlier receipts. Only the nine new ignored DEV-015 receipts below were added afterward. Preservation is rechecked after recording. No replacement activation, source modification, producer/checker regeneration, live LLM/paid calls, deployment, publication, formal tests or later DEV step.

**Assessed implementation identities**

| File | SHA-256 |
|---|---|
| `backend/src/kgfegmcp/services/learning_progressions.py` | `sha256:8104380a714a38b2f75b22a4f3b5882166fb56b0cb6ccd15c32898a0a11480f1` |
| `backend/src/kgfegmcp/services/lp_models.py` | `sha256:8caf0c41961c08c64fa3084cffd0ec071ff278771a0f1ff350098a5926335b09` |
| `backend/src/kgfegmcp/services/lp_paths.py` | `sha256:49023dc640ab91ee182b6260aadc0ca6a2d67fe39fe8030bead49df640d08497` |

**Accepted query input identities**

All six queried runtimes are the DEV-023 rebuilt mixed academic_standards revision-1 packages under `data/source_artifacts/learning_progressions/rebuilt_packages`. Exact snapshot/package/profile-version-2.0/hash and all 86 artifact identities agree with DEV-014's Accepted query input identities table, preserved unchanged. Full exact package references and artifact maps are in content-feedback.json; evidence-index.json also binds the sorted compact logical-name/hash artifact-map digest. Actual manifest byte identities and path-query counts:

| Framework | Actual path queries | Manifest SHA-256 |
|---|---:|---|
| `ghana-nacca-primary-english-language-basic-1-3` | 31 | `sha256:5cf5dbb35785b0ded64f062c19589b1601cd1f76e08cdddf991f9a1a14439f7b` |
| `ghana-nacca-primary-mathematics-basic-4-6` | 40 | `sha256:16ef563d4fea0a5f6d259580ef834b1231d4376c9d34b521e416b39960b70533` |
| `india-cbse-science-learning-framework-classes-9-10` | 35 | `sha256:d7431e9e49ff4d4c99b985d3a42dd10bae506c406dca0e96c26d9d8159515a96` |
| `india-tamil-nadu-tnscert-mathematics-classes-1-5` | 35 | `sha256:32e860054447d9dde6d6d7b15bddb118e33727111953f2c4671b0b3359ca359b` |
| `nigeria-nerdc-mathematics-primary-1-3` | 35 | `sha256:3b0616d3ad9c2d6017c7c9bd4f9624927875daf9d1a6cd46b0a2316916544479` |
| `rwanda-reb-mathematics-lower-primary-1-3` | 38 | `sha256:7a00e1afee01ff60ba4862eb833e26a4f85c727f08447573d229c5a3e89b3e2b` |

**Local receipts and limitations**

Retained under ignored `data/source_artifacts/learning_progressions/dev015/checks`; commands above are the actual scratch runs. Persisted feedback script only adjusts its protected-inventory input to this receipt directory and permits its own nine additions for resumption; production logic and fixtures are unchanged. They remain ad hoc Developer feedback, not Tester-owned formal tests. Actual scratch source hashes:

- `/tmp/kgfegmcp-dev015-feedback.py`: `sha256:f406b65504c5f4cfe5ed316566a6326c2cdfcdbe9600ab551b75d23f4b1038bb`.
- `/tmp/kgfegmcp-dev015-regression.py`: `sha256:0a17daf70aa2e502184dbe504ec04c322fb080cc9e7a5c1f1391172f09a75637`.
- `/tmp/kgfegmcp-dev015-static.py`: `sha256:e305dff234273b4d73b19df820522fa214c7b8e91439a9f081e5742e2b9323c5`.

| Receipt | SHA-256 |
|---|---|
| `content-feedback.json` | `sha256:347ccfa61ef0d852f856fb91e18c7e75dca079d5cb4193a43a3ea5905a1d5084` |
| `content-feedback.py` | `sha256:dfa75f42336376848f24c8f65e19fcd3188171315550cf083599bf08b40f33ba` |
| `preservation.json` | `sha256:8573eb6131a9598947d289cad7617c5595f554ef943f8c4d3d4403b83161ad3f` |
| `protected-inputs.json` | `sha256:9f83b2461732c34d73007cea673fb77a9bd397cb0e2fab54610d320d76729aca` |
| `regression-feedback.json` | `sha256:ee67595e341fb343997a6588ce7788c8390c09de31cabf7b2a53878cb920e839` |
| `regression-feedback.py` | `sha256:0a17daf70aa2e502184dbe504ec04c322fb080cc9e7a5c1f1391172f09a75637` |
| `static-feedback.json` | `sha256:c7f300a297097ae2607aee5a7939a6d9779b39d5ba6ff293c0b523a6e8f82f93` |
| `static-feedback.py` | `sha256:e305dff234273b4d73b19df820522fa214c7b8e91439a9f081e5742e2b9323c5` |
| `evidence-index.json` | `sha256:b7e17cb191ad5695a1bbfc0cd5ce38c1f04740dd2d07d97408d2e5509b8a176c` |

Limitations: sampled actual query pairs plus independent synthetic/random graph and byte-ceiling cases establish implementation feedback, not exhaustive all-pair enumeration, formal Tester acceptance, semantic/pedagogical verification or a new public transport milestone. Rights/route helpers are reused; denial cases check propagation using temporary boundary faults, while DEV-012 records actual policy-denial checks. Resource handlers/public MCP adapters/bootstrap/activation/transports/distribution remain later approved steps. Legacy-schema bootstrap limitation remains until DEV-017; no workaround or replacement activation was introduced.

**Continuation**

DEV-015 is DONE. Suggested Conventional Commit: `feat(progressions): add bounded connecting paths with alternatives`. Next STEPWISE continuation is DEV-016 (exact LP provenance and sanitized summary resources), which remains PENDING. All later steps remain unstarted. The full Developer handoff gate does not pass while approved later work remains unfinished; wait for explicit user continuation.

### DEV-016 — Expose exact LP provenance and sanitized summary resources

`Status`: `DONE` `Depends On`: `DEV-015`
`Acceptance`: `AC-004, AC-010, AC-011, AC-012`

**Goal**

Extend resource URI, repository/policy and service boundaries for per-edge provenance and LP summary using accepted partitions.

**Affected Area**

resources/uri.py, models.py, policy.py, service.py and mcp/resources/register.py; existing relationship/artifact resources.

**Expected Outcome**

Two new resource templates resolve accepted package-local identities. Exact provenance returns the original entry with canonical content/source hashes; sanitized summary retains counts/notices/evidence links. Artifact exposure classes follow the design, partition access requires validated membership, and existing rights/32 MiB source/8 MiB return limits remain enforced.

**Self-Check**

PASS — exact per-edge LP provenance and sanitized public summary resources implemented and checked offline. Working directory: `/Users/tzz/Projects/private/idi/KGForEdGlobalMCP`; assessed HEAD: `9f0f9fcb1adc786b6b42c8eb85e07f54ee53f320`, with the six final source identities below. Entry working tree was clean. The user explicitly authorized DEV-016 next; its matching continuation blocker was cleared before implementation. Plan remains IN_PROGRESS, STEPWISE, locked tony, AFTER_IMPLEMENTATION, Current Increment NONE; workflow remains DEVELOPING with historical Architect handoff and inactive recovery/obligations.

**Implemented outcome**

- Added the exact `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/relationship/{relationship_id}/provenance` and `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/learning-progressions` templates, strict result/notices contracts, two shared ResourceService handlers and thin MCP resources. Reuses accepted package selection, primary academic-standards routing, existing rights policy, safe checksum/size repository reads, deterministic JSON encoding, canonical URIs and resource error boundary. Existing exact relationship URI remains unchanged.
- Added `resources/lp.py` for the fixed SHA-256 UTF-8 relationship-ID first-byte modulo-64 resolver, exact partition-index/manifest validation and summary allowlist. Each full entry reads only the checksum-verified index and selected declared shard. The original full provenance map is referenced by hash without being read by the handler. Exact 64-slot membership, algorithm/version, original-map hash, all declared shard hashes/paths and canonical relative filenames must agree; no caller-selected paths or permissive shard-prefix exposure. Selected shard entry and count must exist. Malformed/missing/inconsistent evidence maps to resource_not_found rather than inferred fallback.
- Full provenance returns the original retained object, including nested candidate, judgment, rationale, every warning and producer/checker trace, plus llm_inferred/generated-origin/semantics/confidence/coverage notices. Metadata carries exact package/snapshot/profile identity and source hashes/sizes for manifest, original map, selected shard, index and relationships. Canonical returned bytes receive their own content hash.
- Sanitized summary contains availability, manifest per-type stored counts, allowlisted original numeric counts, accepted eligibility denominators, needs-review/no-relation/unresolved/validation warning counts, separate edge-warning totals, structural-only validation status and nine exact artifact URI/hash links. Unknown counts/eligibility remain null. Projection excludes rationale, candidate text, producer paths, model configuration/prompts and arbitrary unknown count names. No-LP returns explicit unavailable metadata; an available zero-edge projection remains distinguishable. Original generation summary bytes remain unchanged.
- Explicit generic policies classify LP validation/index/normalization as PUBLIC_METADATA, unresolved as FULL_TEXT, and split edges/original summary/final claims/original provenance/validated shards as BULK_CONTENT. Per-edge provenance requires reviewed/full-text/single-standard rights independently of bulk; derived summary is public metadata. Capability lookup respects rights, validates the index once when bulk is allowed, and fails closed for unavailable shard membership. Unknown additional artifacts remain unavailable.
- Existing 33,554,432-byte source and 8,388,608-byte returned-content ceilings remain unchanged. Actual index/shard/original-summary reads honor lower operator ceilings; complete deterministic responses honor the return ceiling. No oversized map read or clipped full entry is introduced. No new graph store, activation, five-tool registration or later increment.

**Actual commands and results**

Runtime Python commands used the existing Python 3.13 environment through `/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync` from the repository above; effective Python working directory is backend. No install/sync/network/model/paid-service execution.

```sh
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync python /tmp/kgfegmcp-dev016-feedback.py > /tmp/kgfegmcp-dev016-feedback.log 2>&1
python3 /tmp/kgfegmcp-dev016-static.py > /tmp/kgfegmcp-dev016-static.log 2>&1
```

- Final resource feedback exit 0: 2,197 named checks and 850 verified resource documents across all six accepted DEV-023 rebuilt runtimes, loaded read-only through CatalogRepository/GraphPackageValidator. All 384 shard resources are byte-exact under temporary bulk-permitted rights fixtures; their union equals all 8,080 original accepted LP entries and their judgment IDs, with correct hash buckets and original nested values. One accepted entry per nonempty shard plus each package's longest-rationale/warnings sample preserves complete original evidence. Tracking proves each per-edge read uses exactly index plus selected shard, never the original map. Independent offline oracle reads inspect original source maps directly; they are not resource-handler reads.
- CBSE original map remains 40,860,837 bytes, above the unchanged 32 MiB source ceiling. Its individual provenance reads succeed through partitions; generic original-map access with bulk-permitted fixture rights is still denied by the source ceiling. Oversized original artifacts in other packages remain denied by source/return bounds. The largest measured one-per-partition sample is 15,266 returned bytes; this is a sample measurement, not a global maximum claim.
- Actual accepted rights in all six packages are provisional_operator_approved, full text/single standard allowed, bulk false. Individual provenance and derived summaries succeed under those unchanged rights; raw summary/map/final-claims/shard requests deny before any artifact read. Positive bulk checks use in-memory rights projections only. Separate negative projections deny unreviewed/full-text/single-standard access before content IO while allowing sanitized summary metadata. Public validation/index/normalization and full-text unresolved retain their independent classes. Capability checks both omit shards under actual bulk denial and expose exactly declared shards under permitted fixtures, reading the index once.
- Six summaries agree with stored type counts, accepted needs-review/unresolved counts and separate per-edge warning totals; exact source/content/profile hashes and deterministic repeated responses agree. Public redaction checks and hostile unknown-field/count-name injection pass; unknown eligibility remains null. Retained unresolved totals are inspected without promoting needs_review/no_relation into graph edges. All nine generic LP artifact policies preserve exact source bytes when permitted and within limits; unknown edge, non-LP edge, unknown artifact and shard suffix/bucket expansion reject.
- Lower index/partition/original-summary source limits and full-provenance/derived-summary return limits reject. Temporary checksum-bound fixtures cover missing slot, wrong original/shard hash, wrong path/algorithm, malformed JSON, missing entry, wrong entry count, nonobject partition, changed length/same-length hash and missing file. Malformed/nonobject/duplicate-key summary errors are stable resource_not_found. No-LP and zero-edge fixtures check public availability distinctions and missing provenance; these are boundary projections rather than newly accepted complete packages.
- Existing generic relationship samples remain exact original stored records. Eighteen actual standard/component/standard-component resource samples across six frameworks retain successful reads and content/source identities. In-process FastMCP with real ResourceService and a mocked state lookup exposes exactly one fixed resource and 14 templates, matching the URI constants. New summary/provenance and existing relationship reads succeed through encoded exact snapshot/relationship URIs; missing provenance returns masked resource_not_found without local paths. Full bootstrap/STDIO/HTTP are not exercised here.
- Final static commands retain exact argv/cwd/exit/stdout/stderr in static-feedback.json/log. Black --check, isort --check-only, Ruff `check --select E,F,C90`, mypy `--cache-dir /tmp/kgfegmcp-dev016-mypy`, pylint and interrogate `--generate-badge /tmp/kgfegmcp-dev016-badge` on the six source files all exit 0. Mypy finds no issues in six files; pylint 10.00/10 under repository McCabe <=10; docstrings 100%. `node .standards/bin/check.mjs` and `git diff --check` pass and are rerun after this DONE/blocker record.
- Preliminary static feedback found long description/policy lines; shortened them. Temporary feedback fixtures initially assumed bulk permission and model_copy support on the runtime dataclass; corrected the fixtures to retain runtime invariants and test actual denials separately. Fault injection exposed the strict package JSON parser's ManifestBuildError escaping the resource boundary; explicitly mapped it alongside validation errors in both new helpers and reran the final checks. Preliminary failed runs are not counted as passes; final receipts assess the exact final source hashes below.
- Independent pre/post comparison preserves every byte and path of all 2,494 entry protected files under config (original 1.0 and new 2.0), sealed active packages, maintained inputs, raw/prepared/rebuilt/replacement artifacts and earlier receipts. Only nine new ignored DEV-016 receipts were added afterward. Preservation is rechecked after recording. No activation/retirement, source/config alteration, regeneration, live LLM/paid calls, deployment/publication, formal tests or later DEV step.

**Assessed implementation identities**

| File | SHA-256 |
|---|---|
| `backend/src/kgfegmcp/resources/lp.py` | `sha256:92490dd00f37af1d0a7d52c4c0826ef5356171f8c5b763bcb4e7e50c587fb711` |
| `backend/src/kgfegmcp/resources/models.py` | `sha256:2348900c4e433e9a1b4b1c4b76cfe1ed5d3c54fc72500b81542fea37be04bcbb` |
| `backend/src/kgfegmcp/resources/policy.py` | `sha256:2b7fa57ebad16ad0fee8243fc9081b0349de584d50c768dc4aba6050cba85c0d` |
| `backend/src/kgfegmcp/resources/service.py` | `sha256:dcf6be5421c49500a563cf201d1a84db1931b281e078e9a01eeba76e07bc33cd` |
| `backend/src/kgfegmcp/resources/uri.py` | `sha256:ca68afc115fe1a12833b9a6da7b183d3696ddee42a8307ef4f6e1b214a20c7d4` |
| `backend/src/kgfegmcp/mcp/resources/register.py` | `sha256:ff64b6958e9eb82ddadbe05c3d082327842686f1f2ae7079ceac48477aa9919b` |

**Accepted resource input identities**

All six queried runtimes are DEV-023 revision-1 mixed academic_standards replacements under `data/source_artifacts/learning_progressions/rebuilt_packages`, with profile version 2.0. Exact snapshot/package/profile and all 86 artifact identities agree with DEV-014/015 inputs, preserved unchanged. Full identities, actual rights and complete logical-name/hash maps are retained in content-feedback.json; evidence-index.json binds the sorted compact artifact-map digest. Actual documents/counts and manifest/derived-summary hashes:

| Framework | Accepted LP entries | Verified documents | Manifest SHA-256 | Summary content SHA-256 |
|---|---:|---:|---|---|
| `ghana-nacca-primary-english-language-basic-1-3` | 1,051 | 141 | `sha256:5cf5dbb35785b0ded64f062c19589b1601cd1f76e08cdddf991f9a1a14439f7b` | `sha256:97cc0d338d72b60a483cfba1b8dd58f62a4cd173e990ec3ee1491bffc142e621` |
| `ghana-nacca-primary-mathematics-basic-4-6` | 599 | 143 | `sha256:16ef563d4fea0a5f6d259580ef834b1231d4376c9d34b521e416b39960b70533` | `sha256:ccf05e00b3332f2ecde0a32856785be93e5997356a6471a2bcf3dcabf12df046` |
| `india-cbse-science-learning-framework-classes-9-10` | 3,206 | 140 | `sha256:d7431e9e49ff4d4c99b985d3a42dd10bae506c406dca0e96c26d9d8159515a96` | `sha256:f301fd30d7190a680a394bf49bf0eab31c40ac2351c42d472d2380e83d210533` |
| `india-tamil-nadu-tnscert-mathematics-classes-1-5` | 907 | 142 | `sha256:32e860054447d9dde6d6d7b15bddb118e33727111953f2c4671b0b3359ca359b` | `sha256:a4f0a315ed1b85640027f63ebcd71836fa4432dd04175358d6b0baccfa015cf3` |
| `nigeria-nerdc-mathematics-primary-1-3` | 486 | 144 | `sha256:3b0616d3ad9c2d6017c7c9bd4f9624927875daf9d1a6cd46b0a2316916544479` | `sha256:85838e56fe5174bdf9a56649991b26382fc2984d3d6516ad97811494b091111f` |
| `rwanda-reb-mathematics-lower-primary-1-3` | 1,831 | 140 | `sha256:7a00e1afee01ff60ba4862eb833e26a4f85c727f08447573d229c5a3e89b3e2b` | `sha256:d3376971b3eadcca405d89b3682086b7060b5213776ff3512fdd34ad57b17c37` |

**Local receipts and limitations**

Retained under ignored `data/source_artifacts/learning_progressions/dev016/checks`; commands above are actual scratch runs. The persisted feedback script only adjusts its protected-inventory path and excludes its own nine receipt additions from preservation comparison for resumption. It depends on the retained DEV-013 loader setup and remains ad hoc Developer feedback, not a formal test suite. Actual scratch source identities:

- `/tmp/kgfegmcp-dev016-feedback.py`: `sha256:04e31f4f8abb2231c403a94b2de1b294d7b427d71592e5799c40ad2f0dcc7dd9`.
- `/tmp/kgfegmcp-dev016-static.py`: `sha256:f9dccf6767930e2e82b650d00d418bbc84969cafd1db0bf13c71c07a97202435`.

| Receipt | SHA-256 |
|---|---|
| `content-feedback.json` | `sha256:6fb476c8e66c5dced25bffaf5dc2cb7beb9b2672d8455b483520d087e102a5b3` |
| `content-feedback.log` | `sha256:f988d6951042f5347e25f8df82b991335e6a820548cbf55d940add26a1ffdab9` |
| `content-feedback.py` | `sha256:01622ac22bfeec0ee1bedb1ad89b26fb31b4fc99f9b386573150ad4cc6ccd737` |
| `evidence-index.json` | `sha256:6544956c1870dd92af5a98dcbd0c730d30cd62e275c720db9a56389972604a04` |
| `preservation.json` | `sha256:364537159ca41d9c08b1ce0b0ac73a4d76ea445662ff83bf7cbfa43a88090329` |
| `protected-inputs.json` | `sha256:c543662c86f00a45cb28db1feefab15fa9c391eaafe655e4d1fb3151e65b983d` |
| `static-feedback.json` | `sha256:e0bcfdf5cce15d46a897059dd42b49d2c425dcf71768c232b08357e8c1423e05` |
| `static-feedback.log` | `sha256:722234f1eca02508fb42e4110ec6bf1a8857f1d9c7beb1d1f69d6f425c22e59a` |
| `static-feedback.py` | `sha256:f9dccf6767930e2e82b650d00d418bbc84969cafd1db0bf13c71c07a97202435` |

Limitations: Developer implementation feedback is not independent Tester acceptance, exhaustive per-edge resource querying, semantic validation or pedagogical certification. All entries are compared through raw shard union; individual handlers are sampled per shard and by long-evidence cases. Synthetic faults/rights/no-LP/zero-edge projections supplement actual packages without altering accepted data. Local MCP registration uses a mocked state lookup with the real service; full application bootstrap, five public tools, transports and distribution remain later increments. The legacy-schema bootstrap limitation remains until DEV-017 activation. Formal test suites and the complete Developer handoff remain unfinished approved work.

**Continuation**

DEV-016 is DONE. Suggested Conventional Commit: `feat(resources): expose progression provenance and summary`. Next STEPWISE continuation is DEV-017 (activate accepted replacements and register the five LP tools), which remains PENDING. All later steps remain unstarted. The full Developer handoff gate does not pass while approved later work remains unfinished; wait for explicit user continuation.

### DEV-017 — Activate accepted replacements and register the five LP tools

`Status`: `DONE` `Depends On`: `DEV-016`
`Acceptance`: `AC-005, AC-006, AC-007, AC-008, AC-009, AC-017, AC-018, AC-019, AC-020, AC-021`

**Goal**

Wire the shared service and thin read-only MCP tools, truthful package capabilities and separate statistics; atomically replace active sealed data/configuration only after all six replacement checks pass.

**Affected Area**

bootstrap.py, services exports/capabilities/statistics, catalog metadata where needed, mcp/register.py and new LP tool adapters; active data/graph_packages and config roots.

**Expected Outcome**

One GraphStore/runtime per package exposes five new tools with service/protocol bounds and stable masked errors. Active roots contain one current new snapshot per framework and fresh profile/prompt configs; old terminal directories are retired rather than rewritten. Old progression tool/service/models/bootstrap/exports are removed. LP availability/counts match accepted evidence; useful AS/LC routing, DAGs, search and supports remain usable.

**Self-Check**

PASS — all six accepted replacements are active, the five bounded LP tools are registered, and exact shared bootstrap/capability/statistics integration is checked offline. Working directory: `/Users/tzz/Projects/private/idi/KGForEdGlobalMCP`; assessed entry HEAD: `a1207f480c1222b0bc5f080f8ce0cea210c5acc0`, with final source, deletion and data identities below. Entry working tree was clean. User explicitly authorized DEV-017 next; its matching blocker was cleared before work. Plan remains IN_PROGRESS, STEPWISE, locked tony, AFTER_IMPLEMENTATION, Current Increment NONE; workflow remains DEVELOPING with historical Architect handoff and inactive recovery/obligations.

**Implemented outcome**

- AppState/bootstrap now retain one LearningProgressionsService sharing the exact CatalogService, SearchService, FrameworkService catalog and ResourcePolicy with resources. State invariants reject independent runtime/policy objects. All five methods reuse DEV-012 through DEV-015's accepted edge/projection/selectors, immutable builds adjacency, rights and bounds; no second graph store, query-time source reads or fallback inference.
- Added `mcp/tools/learning_progressions.py` and explicit registration for get_learning_progression, get_standard_progressions, search_learning_progressions, traverse_learning_progressions and get_learning_progression_paths. Each uses the established nested `request` object with camel-case schema aliases, typed service models, required framework, closed fields, shared tool error boundary, read-only/idempotent/non-destructive/closed-world annotations and exact output schema. The adapters use the same concise text plus full structured evidence and recheck the fixed 1 MiB encoder; no extra table copy or unbudgeted resource-link blocks. Direct/discovery cursors remain unchanged in structured results. Schema defaults/maxima match service page 25/100, traversal depth 8/12/nodes 100/250/edges 100/100 and paths depth 6/12/paths 3/20; fixed work/queue counters remain 5,000.
- Removed services/progression.py, services/progression_models.py and mcp/tools/progression.py, their service exports/bootstrap field/invariant and registration. No collect_progression_evidence tool/alias or candidate service/model remains in those runtime boundaries. New service/request/result/statistics contracts are exported under their current names. Prompt-side hypothesis implementation/registration and stale smoke/reference expectations are deliberately still DEV-021/DEV-022/Documenter work; no new prompt step was started.
- Capabilities advertise exactly 17 current tools and implementation features for stored LP paths/traversal, and no longer list learning_progressions as unavailable. Package capability evidence adds includedGraphTypes from accepted metadata and retains exact LP flags/counts/resource policy availability. Global availableGraphTypes keeps its established meaning as primary routing types (academic_standards here); each mixed package separately includes academic_standards, learning_components and learning_progressions. Current prompt/resource inventory remains truthful: seven prompts (including the pending obsolete prompt), one fixed resource, 14 templates. Final nine-prompt inventory is later work.
- FrameworkStatistics adds a separate learningProgressions block with accepted availability/provenance flags and actual buildsTowards/relatesTo counts. Existing totalRelationships, canonical/source relationship types and unresolved statistics count hierarchy only; learningComponents retains supports counts. Root-connected AS/LC counts follow only hasChild/supports, preventing LP edges from changing existing connectivity meaning. Package totals reconcile all four labels; statistics text reports the new counts with generated-origin/semantic limits. No hasChild ancestor/parent/path or supports behavior is changed.
- Revalidated the six accepted DEV-023 rebuilt packages and exact DEV-016 package/manifest/profile/all-artifact identities, then staged byte-exact copies (522 files) and only fresh version-2.0 profile/prompt configs (12 files). Staged package validation and prompt registry load pass before retirement; the real staged application factory/bootstrap/lifespan and all five tools pass before cutover.
- Guarded offline cutover moved the entire prior config and graph_packages trees to `data/source_artifacts/learning_progressions/dev017/retired/{config,graph_packages}` and renamed staged trees into active roots. Each same-filesystem directory rename is atomic; the multi-root operation has reverse-order rollback on failure and a persisted phase journal. No simultaneous filesystem transaction across both roots or deployed atomicity is claimed. All four renames completed and post-move inventories match. Active roots contain one current replacement per framework and only version-2.0 configs; old terminal bytes were moved intact, never rewritten. Source/prepared/rebuilt accepted copies remain unchanged. Deployment/publication remains user-owned.

**Actual commands and results**

All runtime Python checks used the existing Python 3.13 environment through `/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync`, from the repository above (effective Python cwd backend). No installation/sync/model/paid-service call, regeneration, sampling, endpoint update or publication.

```sh
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync python /tmp/kgfegmcp-dev017-stage.py > /tmp/kgfegmcp-dev017-stage.log 2>&1
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync python /tmp/kgfegmcp-dev017-feedback.py --staged > /tmp/kgfegmcp-dev017-staged-feedback.log 2>&1
python3 /tmp/kgfegmcp-dev017-activate.py
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync python /tmp/kgfegmcp-dev017-feedback.py > /tmp/kgfegmcp-dev017-active-feedback.log 2>&1
python3 /tmp/kgfegmcp-dev017-static.py > /tmp/kgfegmcp-dev017-static.log 2>&1
python3 /tmp/kgfegmcp-dev017-preserve.py
```

- Staging exit 0: CatalogRepository/GraphPackageValidator read-only loads six complete accepted runtimes, zero excluded packages, exact agreement with DEV-016 identities and 86 artifacts each. Source/staged inventories are equal (522 files); staged configs are exactly 12 version-2.0 files and their prompt registry loads. Stored totals remain 3,039 buildsTowards and 5,041 relatesTo. No acceptance flag was fabricated or persisted over terminal evidence.
- Staged feedback exit 0: 509 named checks, 142 actual MCP tool calls including successful and negative calls, six frameworks. A real create_mcp factory/lifespan delegates to real bootstrap, with settings pinned to repository-local staged roots; no state-lookup mock. Exact 17-tool inventory and current seven prompts/one fixed resource/14 templates agree with advertised names. Five input/output schemas, closed required-framework requests, annotations and caller bounds are inspected. Query calls execute with Path.open/read_bytes and builtins.open blocked. Both stored types, direct/discovery, upstream/downstream and connecting paths agree exactly with ordinary service payloads, pinned manifest/snapshot/type totals and <=1 MiB actual text-plus-structured envelopes. Real ordered cursor replay preserves IDs; changed-bound cursor fails invalid_cursor.
- Active feedback exit 0: the same 509 checks and 142 MCP calls pass against only active roots and the final source bytes. Existing exact standards/components/context/support resources and lexical search remain usable; original node bytes and complete AS/LC relationship prefixes match retired sealed data for all six. hasChild and supports counts and exact instances remain unchanged. Separate LP statistics are checked through the real public adapter; hierarchy canonical labels remain hasChild only. Retained comparison is usable. Actual LP provenance/summary resources read through real lifespan state and retain exact IDs/counts. Each package shares one original GraphStore for the mixed runtime.
- Negative local protocol cases reject unknown extra fields, missing framework, boolean/string/nonpositive/excess integer bounds, invalid direction/type/connection/scope and >20 selectors. Profile-invalid facets map to invalid_progression_request. Missing/non-LP edge, same endpoint, unknown framework and stale/mismatched cursor retain stable domain failures. Temporary service-method faults confirm resource_access_denied, progression_result_too_large and masked internal_error mapping for all five tools without private paths. Old collect_progression_evidence calls fail as an unknown tool. These faults check adapter propagation; actual policy/entry-size/cycle/branch ceilings have their persisted DEV-012 through DEV-016 evidence and are not newly claimed as exhaustive service verification here.
- Unpatched default `bootstrap_application()` exit 0: BackendSettings resolves exactly this repository's data/graph_packages, config/profiles and config/prompts, and loads six accepted runtimes. Exact actual Python -c argv, cwd, exit and output are retained in default-bootstrap-command.json/log; no settings or state lookup was mocked in this separate check. The prior migration-checkout bootstrap limitation is now resolved. No external source directory is a runtime dependency.
- Final static feedback on the eight listed source files: Black --check, isort --check-only, Ruff `check --select E,F,C90`, mypy `--cache-dir /tmp/kgfegmcp-dev017-mypy`, pylint and interrogate `--generate-badge /tmp/kgfegmcp-dev017-badge` all exit 0. Mypy finds no issues in eight files; pylint 10.00/10 under McCabe <=10; docstrings 100%. Exact argv/cwd/exit/stdout/stderr are in static-feedback.json/log. `node .standards/bin/check.mjs` and `git diff --check` pass and are rerun after this DONE/blocker record.
- Preliminary static feedback found three pre-existing long strings in touched modules; split/shortened them. Temporary feedback fixtures initially assumed an aggregate context view, mapping-valued artifact references, plural wire labels and a generic LC lexical mode; corrected them to the established contracts. Preliminary runs are not passing evidence. Final staged/static records cover the gate before cutover; final active/static records cover the final source. After cutover, capability availableGraphTypes was narrowed back to its established primary-routing meaning while includedGraphTypes remains explicit per package; final active/static checks were rerun. Preactivation source hashes are retained separately and in the activation journal rather than falsely equated with final metadata bytes.
- Activation and preservation exit 0: all 2,503 entry file identities survive; 2,395 remain at their original paths and 108 are retained byte-exact at recorded retirement paths (84 package files, 24 prior configs). All active 522 package files equal the accepted DEV-023 inventory; all 12 active configs equal staged version-2.0 bytes. Original source artifacts, prepared/rebuilt packages, maintained inputs and earlier receipts are unchanged. The root journal records four completed renames and exact preactivation source identities. No old terminal manifest/profile/config was edited.

**Final source identities**

| File | SHA-256 |
|---|---|
| `backend/src/kgfegmcp/bootstrap.py` | `sha256:af6932319ca22fef2280deea26833f6663239b9eb1ab4169f302323b76138b2b` |
| `backend/src/kgfegmcp/services/__init__.py` | `sha256:45cc24abdbb0749c2e0ee4c09a5e929d0f2cf0e92745fb6a361a5ca23a3b7805` |
| `backend/src/kgfegmcp/services/capabilities.py` | `sha256:cf91dc01518c0b8b7550ed470a324093d8a3d86d5b7595fcd5eb118a8bde7425` |
| `backend/src/kgfegmcp/services/models.py` | `sha256:b242e860f27adcb74710dc35746448d98c791e2dc01c97814a68354af6e9c5cd` |
| `backend/src/kgfegmcp/services/statistics.py` | `sha256:da3cdc8fc5a2c823205e3bf51c8f6d897d550314de2e29576c68eb8409f82266` |
| `backend/src/kgfegmcp/mcp/register.py` | `sha256:5cabd9c8a0d43685fc6bd7e3e582349871d7c5cdbbb2d1f9c161acf500cc5ed6` |
| `backend/src/kgfegmcp/mcp/tools/learning_progressions.py` | `sha256:b744eae3100f9fcd3fc32c073a4496e752afff92bcd15cebd29e1c2a49111236` |
| `backend/src/kgfegmcp/mcp/tools/statistics.py` | `sha256:279f3573eb5ddd094e95ed25cbde3a86621e1af108f494912574af9eedcee493` |

Removed module entry content remains in Git history; no alias or dormant copy is kept in active production source:

| Removed file | Entry SHA-256 |
|---|---|
| `backend/src/kgfegmcp/mcp/tools/progression.py` | `sha256:90b68f8bb78c0ca20331bf8a615b1fb1c3afa71b25f69770e76cbeba38d4a0bf` |
| `backend/src/kgfegmcp/services/progression.py` | `sha256:effdff2ce1393de43ee9187bb98fb20a0bea63407cdc9b29752a922c445a4ef6` |
| `backend/src/kgfegmcp/services/progression_models.py` | `sha256:03b213d6fc0f1063188143568003ae6582ae5f0e5e69c9be7ca32cd31b45ecb7` |

**Active input and retirement identities**

Exact new snapshot/package/profile-version-2.0 and all 86 artifact identities remain the accepted DEV-023/DEV-016 identities. Full references and complete active tree/config maps are in stage.json and evidence-index.json; source artifact maps in preceding steps remain unchanged. Every original file's retirement mapping is in preservation.json. Active manifest identities and queryable LP counts:

| Framework | buildsTowards | relatesTo | Manifest SHA-256 |
|---|---:|---:|---|
| `ghana-nacca-primary-english-language-basic-1-3` | 250 | 801 | `sha256:5cf5dbb35785b0ded64f062c19589b1601cd1f76e08cdddf991f9a1a14439f7b` |
| `ghana-nacca-primary-mathematics-basic-4-6` | 299 | 300 | `sha256:16ef563d4fea0a5f6d259580ef834b1231d4376c9d34b521e416b39960b70533` |
| `india-cbse-science-learning-framework-classes-9-10` | 891 | 2315 | `sha256:d7431e9e49ff4d4c99b985d3a42dd10bae506c406dca0e96c26d9d8159515a96` |
| `india-tamil-nadu-tnscert-mathematics-classes-1-5` | 472 | 435 | `sha256:32e860054447d9dde6d6d7b15bddb118e33727111953f2c4671b0b3359ca359b` |
| `nigeria-nerdc-mathematics-primary-1-3` | 189 | 297 | `sha256:3b0616d3ad9c2d6017c7c9bd4f9624927875daf9d1a6cd46b0a2316916544479` |
| `rwanda-reb-mathematics-lower-primary-1-3` | 938 | 893 | `sha256:7a00e1afee01ff60ba4862eb833e26a4f85c727f08447573d229c5a3e89b3e2b` |

Active config byte identities (profiles retain profile version 2.0; prompt configs retain configuration version 2.0.0, distinct from public prompt version 1.2.0 until DEV-018):

| File | SHA-256 |
|---|---|
| `config/profiles/rwanda-reb-mathematics-lower-primary-1-3/2.0/profile.json` | `sha256:d3fc130a70ce0502fc07f93a8211124adbe69a3b36b6302cf463f728fb41e0b6` |
| `config/profiles/ghana-nacca-primary-english-language-basic-1-3/2.0/profile.json` | `sha256:fe2b269f7e76d0abf89d00799857602e17c8e76b6d1b4055797c662629ce7212` |
| `config/profiles/india-tamil-nadu-tnscert-mathematics-classes-1-5/2.0/profile.json` | `sha256:8b9e1ffde3595ff24fa20bc2fa468fd952ec78aad6daaa4b19c1d5ebefc46595` |
| `config/profiles/nigeria-nerdc-mathematics-primary-1-3/2.0/profile.json` | `sha256:b04a2bcefa88d2e235cd9a1f988ae6af7dd9e50da565ec7aa9a5ac76015cd3e8` |
| `config/profiles/ghana-nacca-primary-mathematics-basic-4-6/2.0/profile.json` | `sha256:4981190e0b1f79a924b92088ed7e78820961935a022ea1abcb13500e8136e848` |
| `config/profiles/india-cbse-science-learning-framework-classes-9-10/2.0/profile.json` | `sha256:5e5e9ed3ec1f52f296b0ff5538aff56e6f2b8f58cc87ba0a29ac6e892bf5f852` |
| `config/prompts/rwanda-reb-mathematics-lower-primary-1-3/2.0/prompts.json` | `sha256:3113ae183123271e5a3d0e075c72b807bfc59df5a3bf7bd0e0d1babf1e3aeb69` |
| `config/prompts/ghana-nacca-primary-english-language-basic-1-3/2.0/prompts.json` | `sha256:2b941a1e93e3b1c133f0d5b40ee2abf24b36333a6d87d523378f25c6a72e357e` |
| `config/prompts/india-tamil-nadu-tnscert-mathematics-classes-1-5/2.0/prompts.json` | `sha256:4711bb6d09b8e07fac6e9cac9d7d6a3d8cad8a754d1c76803e127f30150a96cd` |
| `config/prompts/nigeria-nerdc-mathematics-primary-1-3/2.0/prompts.json` | `sha256:a9d6e333574a9a12c9b77514caace37b494120293831efbfb371991b18e90ec6` |
| `config/prompts/ghana-nacca-primary-mathematics-basic-4-6/2.0/prompts.json` | `sha256:1702079f466317e0e953449938cd7b45a9dce77b92aabcc0b99497e23589c877` |
| `config/prompts/india-cbse-science-learning-framework-classes-9-10/2.0/prompts.json` | `sha256:788fd22501ea2a84a8db5f36a48a894bd7c715aaf6b5d0f64a4ff1873e71fb50` |

**Local evidence and limitations**

Retained under ignored `data/source_artifacts/learning_progressions/dev017/checks`. Stage and activation scripts are one-time preparation/cutover evidence; do not rerun them in place or overwrite retirement trees. The saved content feedback defaults to active mode; its staged roots were moved at activation. Preservation script only adjusts checkpoint-input paths to retained receipts for resumption. Actual scratch scripts and source identities are bound in evidence-index.json. The root activation journal is `sha256:e434250149e957730369235ddfecdfd1cd48eb9d5665d0fbece4f1a1d698cff8`.

| Receipt | SHA-256 |
|---|---|
| `activation.json` | `sha256:d5003f1b115adcd0bfe8b684862e7f2c88979cad0b181d3c401827b6989b3543` |
| `activation.py` | `sha256:84f4f3645c1e2a2c390771fbdea9e0ba46871d6ca6c264bef037db3a21528d28` |
| `active-feedback.json` | `sha256:311b11dd41e09be7e3747f9e726dd471a8912233484299e9dcb7134177eb17fb` |
| `active-feedback.log` | `sha256:1a985ca67f131d3284877e67dfa6885a8f622adbbde6c75b934f315326e6f459` |
| `content-feedback.py` | `sha256:2537040afab4d9d814748bdf829520bb729dbffcb0dd48140b6dfbfa64635f87` |
| `default-bootstrap-command.json` | `sha256:1e2c09026885771b779c9c3906c996f194802693237f68349cb50418a3450ee5` |
| `default-bootstrap.json` | `sha256:eefd2e2599ab4c411e4446663f68cc02c9ea38b089ae1d95252afaec504cceaf` |
| `default-bootstrap.log` | `sha256:9209a2d83bc704ab4c01b49975c872f791e15c277c797de97aa38c9ac5dc073b` |
| `entry.json` | `sha256:e1a427c21f83fe243fbc489560a2ca3e54cfb8403eb5129fd92aeb8e48265b38` |
| `evidence-index.json` | `sha256:2ed8bbb96f26e3fd58355bb7055e17eff4c2ea2517c878f2ec2573b14383fb96` |
| `preactivation-static.json` | `sha256:7a4f05c73ebf4393ddd35d1b484695a4dcee4840896a10e575be540696a6d3ea` |
| `preactivation-static.log` | `sha256:8dd15b00925b6f5ec9fc5f5c1793e7c4cfeeea5cbd1bc588582e6071245f2899` |
| `preservation.json` | `sha256:118be8f45114915c0fdd2d81c152ba40c505aece133905526d71343ef204feeb` |
| `preservation.py` | `sha256:30bd8fce10acb18f1d481dcdff12d04db4f6d154bd03f647fe20f934a57be959` |
| `protected-inputs.json` | `sha256:0395a86b0dcb2edd1e29c67df02791469fb302fda6e927ee5365dc4466305d1f` |
| `stage.json` | `sha256:64bd06716e7d3ec417c1f4a607bdb42c46f340b9946aa7f54dbaef52b98ea1d1` |
| `stage.log` | `sha256:5ff70a0a99fda5432489fb107a94c541907d8284682b3c30786bbd4888dd8eba` |
| `stage.py` | `sha256:fe2124c2b2924a890061a0bcead93428c9c747fb550640a7f8a919044ddecea8` |
| `staged-feedback.json` | `sha256:5dc88b5ca9b04a7dc1a49d5d568a8695b95cbf45da6ebd7c6a901e308ef6babe` |
| `staged-feedback.log` | `sha256:7b2008cb7d13489a827e6aa8bda669ccb99606f43c9bc309462b865affa9dc53` |
| `static-feedback.json` | `sha256:f3f2f56142f451ba22a9864c01fe53ad5315a33881fd8cb787d9cc0e8de74563` |
| `static-feedback.log` | `sha256:8dd15b00925b6f5ec9fc5f5c1793e7c4cfeeea5cbd1bc588582e6071245f2899` |
| `static-feedback.py` | `sha256:8bd1876e6eb06ba578da46e323ab32a0db9fa0b7aae00c2872c36cda742f4fdd` |

Limitations: this is ad hoc offline Developer implementation feedback, not independent Tester acceptance, exhaustive all-edge/all-pair query coverage, semantic/pedagogical certification or deployment. Actual factory/lifespan/bootstrap and in-process local protocol calls are established; shared STDIO/local HTTP/MCPB smoke/CI updates remain DEV-022 after prompts. Existing smoke inventory is intentionally stale until then. The old hypothesis prompt adapter/renderer/registration still references the removed tool and is pending DEV-021 removal; it is not a usable retained workflow or an inferred-edge fallback for the new tools. Six useful prompt registrations and fresh config registry remain, but prompt rendering/integration and the three new workflows are later increments. Formal tests and complete scope acceptance remain Tester-owned, and the full Developer gate remains unmet while future approved steps are unfinished.

**Continuation**

DEV-017 is DONE. Suggested Conventional Commit: `feat(mcp)!: activate stored learning progression tools`. Next STEPWISE continuation is DEV-018 (teaching-sequence prompt workflow), which remains PENDING. All later steps remain unstarted. Reuse the now-active shared state and exact nested-request tool schemas; keep both retired roots and all source/accepted copies intact. Wait for explicit user continuation.

### DEV-018 — Add the teaching-sequence prompt workflow

`Status`: `DONE` `Depends On`: `DEV-017`
`Acceptance`: `AC-010, AC-013, AC-021`

**Goal**

Render the deterministic teaching-sequence workflow and its thin MCP prompt adapter.

**Affected Area**

prompts/definitions.py, models.py, service.py and focused mcp/prompts adapters/registration; public prompt version 1.3.0.

**Expected Outcome**

Topic or exact-standard selection pins the package, retains up to three standards and instructs the designed bounded direct/downstream/path/LC/provenance retrieval before composition. Related concepts remain separate; generated pedagogy, sparse/partial/denied evidence and stored origin are explicit. No LLM runs on the server.

**Self-Check**

PASS — offline Developer implementation feedback completed from `/Users/tzz/Projects/private/idi/KGForEdGlobalMCP`, assessed HEAD `8d56cb73e2b99df1707b0a5938f31b1734a7ad99` and the six dirty-tree Python content identities below. Final commands exited 0:

```sh
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync python /tmp/kgfegmcp-dev018-feedback.py
python3 /tmp/kgfegmcp-dev018-static.py
python3 /tmp/kgfegmcp-dev018-preserve.py
```

- Real `create_mcp()` factory/lifespan and default unpatched settings/bootstrap accepted all six active replacements. A bootstrap observer delegates to the real constructor once and captures the shared state; no state-lookup or settings mock. 1,358 named checks passed, including 47 actual local MCP prompt calls, 30 tool calls executing rendered templates, one capabilities tool call and 12 actual summary/per-edge provenance reads. Saved script/results/log identify every scenario and rendered-message byte hash.
- 28 focus render cases cover topic, node ID, CASE UUID, CASE URI for all six and statement-code focus for the four coded profiles. Ordinary and protocol render results agree, repeated renders are deterministic, exact snapshot/package/config identities agree, and every nested-request template validates against its actual request model and pins the same framework/snapshot. Topic/code discovery uses one first page of 10, direct links one page of 25, downstream depth/nodes/edges 8/30/40 and conditional paths depth/paths 6/3. One of each template executes per curriculum using real accepted builds endpoints; this validates call contracts rather than claiming a complete client planning session. Exact focus results are reused; statement-code focus uses existing code search then namespaced lookup because `get_standard` does not accept a code selector.
- Invalid/oversized/blank required focus, unknown focus mode, language, 4,001-character context, 513-character focus, duplicate/33-item/unsupported grade arrays, semantic alias duplicates and unsafe exact selectors are rejected. All available profile grades and canonical aliases are supported. Uncoded statement-code focus, unknown route and framework/snapshot mismatch fail; adapter blank optional values use established defaults. Boundary 512-character focus/4,000-character context fits; lower prompt byte policy raises `prompt_rendering_error` rather than clipping. Ordinary request validation maps to `invalid_progression_request`; existing route/capability errors remain typed.
- Actual derivative policy denies prohibited/review-required derivatives and unreviewed rights through temporary projected catalog metadata. No-LP capability projection skips LP calls/resources, retains standards/components and explicitly avoids inferred-edge fallback. A local teaching-sequence soft-guidance replacement merges only its declared slot; mandatory retrieval caps and output disclosures remain. Unexpected adapter faults are masked as `internal_error` without private paths in the client error. These projections do not mutate accepted packages or claim acceptance of synthetic replacement data.
- Rendered instructions require up to three identified selected standards, up to five retained supporting components per selected standard and at most ten distinct full used-edge provenance reads, deduplicated across direct/traversal/path results. They distinguish component retention from LC tool output limits, require every used path hop to have its original direction/ID and inspect full provenance before recommendation, and reduce/defer recommendations beyond the provenance cap. Related concepts remain separate. Scope, excerpt/omission, warning/needs_review, selected coverage/unknown denominators, limits/counters/cursors/completeness, unavailable/empty/incomplete/denied evidence, origin/rights/license/attribution and exact evidence citations remain explicit. Activity/order choices are generated pedagogy; no new edge, prerequisite, learner diagnosis or certification is asserted.
- Current implemented inventory is 17 tools and eight prompts, with the new teaching-sequence prompt and exact names agreeing with capabilities. Prompt listing requires only framework_id/topic_or_standard; prompt metadata/rendered identity uses public version 1.3.0. The two other new workflows remain unregistered. Six useful old prompt registrations remain; representative teacher-guide rendering still works with its established retrieval/output. AST comparison against entry HEAD confirms 45 existing functions/methods unchanged (excluding the intentionally extended overlay selector), and existing guidance constants unchanged outside expanded registration/default maps. No existing teaching/study LP integration was performed.
- Six-module Black, isort, Ruff `E,F,C90`, mypy, pylint and interrogate passed (pylint 10.00/10, docstrings 100%); workflow and `git diff --check` passed. Exact locked offline argv, cwd, exit codes/stdout/stderr and hashes are in `static.json`. Initial Ruff findings required line splitting of existing strings in the three touched prompt modules plus two new strings; existing literals/functions have identical AST values. Initial feedback fixtures were corrected to the established opaque identifier contract and actual rights enum names; these were checker corrections, not product contract changes.
- All 3,062 entry data/config files retain exact hashes and the same inventory: source artifacts, copied/prepared/rebuilt inputs, sealed retired packages/configs, current 522 accepted-package files, 12 current configuration files and prior receipts are untouched. Preservation receipt and original-input map record every protected path/hash. No package activation, configuration update, source regeneration, model/paid-service call, formal test edit, deployment or publication occurred.

**Content Identities**

- `backend/src/kgfegmcp/prompts/models.py`: `sha256:1720218d16e1a20f025ca09b9349e27cac382f7196ef48768bacf0debaa67390`.
- `backend/src/kgfegmcp/prompts/definitions.py`: `sha256:942efb39d0945ce647459484078642dd9f709d436895aaf6ae5ee08098b518c8`.
- `backend/src/kgfegmcp/prompts/service.py`: `sha256:5a963757265153c29ccf466de53f945f5ba215cd158f550531c5ce5ae6418129`.
- `backend/src/kgfegmcp/prompts/learning_progressions.py`: `sha256:cbac23d011c70852d97085e81fc6a72ed7a0b757d3a4a04a9b87830c9c90d103`.
- `backend/src/kgfegmcp/mcp/prompts/register.py`: `sha256:b1b9b313cfa819499f03a6a8ef454695797996c59d469d1a53223728cb28ffbf`.
- `backend/src/kgfegmcp/mcp/prompts/learning_progressions.py`: `sha256:69ded8d8cd0cdb22381f9084e6668b0a1e46064245439252952f7e8047d0bc48`.

Retained local Developer receipts (ignored by `/data/source_artifacts/`) live at `data/source_artifacts/learning_progressions/dev018/checks/`. The evidence index links every exact receipt and assessed source identity; archived scripts preserve actual check code, and `commands.json` preserves commands, results, initial findings and replay limits. Receipt identities:

- `commands.json`: `sha256:6430c0d09c633c2f8d4e72146d34d0f23d0285417729658d9e79bc66c458deb0`.
- `entry.json`: `sha256:4fd8cc8ad4313f11810141f137d6cf4dfbdca144da3e2e27628a8ec33af5a3aa`.
- `evidence-index.json`: `sha256:0a2449c8a9802d184ab65c76aa434f610da7fbba3b2cb42badf79fdeb30656ce`.
- `feedback.json`: `sha256:112bfdfd467c63834e505509b6f9d3169e0f955446f58be4fc8707db8b26cae3`.
- `feedback.log`: `sha256:6f9fe301de205e16dbe6f5756c420dc80842b5a451003ce25c70af86014c7562`.
- `feedback.py`: `sha256:b6b488061b003e64e5d194ad53315c662d8e8e4921881f3b607dfbd0b5687275`.
- `initial-static.json`: `sha256:faf9b92f8d7ba2348586e2c24887fc2e206068c874382670a3fd6ebdff9b6b32`.
- `initial-static.log`: `sha256:52276fd8b606aa89e8372c55212e01a83f5c59690f4fd76701e9b706e74e0771`.
- `preservation.json`: `sha256:dd8f2a600127473523f8f025cbcc0eab3e15ba394ccac9a5b7bd934031304182`.
- `preservation.log`: `sha256:c4b47dc2d3847dde002b6de4da7c585c058c0acb04b1b5c537d4e91834a3521f`.
- `preservation.py`: `sha256:115b2115c817d668bcb8c695585e8e9716bfb3d0abed82244415cb581618fc5a`.
- `protected-inputs.json`: `sha256:960152f4f26093a75d61b593d28da98a82f53bde3249b210b45b05806c7c6fbb`.
- `static.json`: `sha256:bcf0f58bc95403d3dc9c48c19158312781c2e23a730eeb85d358a6140548fde9`.
- `static.log`: `sha256:0751d0df19e80aa99c61b30f0a58cccd390ee43afd840919602204237ff7ec98`.
- `static.py`: `sha256:6e508773238aaf22c84a5fd3c7b73ccd7533f383455d29818b7097b750210a61`.

**Implementation Notes and Limitations**

The focused `prompts/learning_progressions.py` renders client retrieval templates and reuses existing profile-governed LP facet normalization and exact selector models. `PromptService` retains route selection, derivative-rights checks, configuration merging, shared disclosures and prompt-size policy; the new MCP adapter only delegates and converts the result. No orchestration engine, new graph/index, model invocation or server-side evidence search was introduced. Version-2.0 prompt configuration bytes stay immutable; the previously introduced teaching-sequence guidance slots now have generic defaults and renderer dispatch, without writing new overlays.

These checks are ad hoc Developer feedback, not independent Tester acceptance or certification of educational output. The server returns instructions; client composition, compliance with evidence-retention caps, and every eventual recommended-edge provenance inspection were not executed by a model. MCP calls are in-process local protocol checks, not STDIO/HTTP/MCPB smoke. No formal pytest cases were created/run. The obsolete hypothesis prompt adapter/renderer/registration remains explicitly pending DEV-021 and is not a usable workflow or fallback for this prompt; six useful existing prompts receive shared LP integration in that later step. Support planning and curriculum review remain DEV-019/DEV-020; final smoke/CI/distribution inventory remains DEV-022. The full Developer gate remains unmet while future approved steps are unfinished.

**Continuation**

DEV-018 is DONE. Suggested Conventional Commit: `feat(prompts): add stored progression teaching sequence`. Next STEPWISE continuation is DEV-019 (support-planning prompt workflow), which remains PENDING. Reuse the shared route/rights/guidance/render helpers and exact nested-request tool shapes; preserve active/retired/source/package/config bytes. No later step was started. Wait for explicit user continuation.

### DEV-019 — Add the support-planning prompt workflow

`Status`: `DONE` `Depends On`: `DEV-018`
`Acceptance`: `AC-010, AC-014, AC-021`

**Goal**

Render a target-standard support workflow grounded in bounded incoming/related/upstream evidence and components.

**Affected Area**

Shared prompt models/definitions/service and MCP prompt adapters/registration.

**Expected Outcome**

Exact target and teacher context drive designed retrieval: incoming/related pages, depth-3 upstream evidence and bounded LC/provenance retention. Caller observations remain distinct from generated review/practice suggestions; no diagnosis or mandatory prerequisites are claimed.

**Self-Check**

PASS — the exact-target support-planning prompt is implemented and checked offline. Working directory: `/Users/tzz/Projects/private/idi/KGForEdGlobalMCP`; assessed entry HEAD: `4f46c06638df9c980b49d7b727085ad3c72a2eeb`, with seven changed-module identities below. Entry working tree was clean. The user explicitly authorized DEV-019; its continuation blocker was cleared before implementation. Plan remains IN_PROGRESS, STEPWISE, locked tony, AFTER_IMPLEMENTATION, Current Increment NONE; workflow remains DEVELOPING with historical Architect handoff and inactive recovery/obligations. All final commands exited 0 using the existing Python 3.13 environment through locked/offline/no-sync uv; no dependency sync or network/model calls.

Actual final commands (repository root):

```sh
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync python /tmp/kgfegmcp-dev019-feedback.py
python3 /tmp/kgfegmcp-dev019-static.py
python3 /tmp/kgfegmcp-dev019-preserve.py
```

- Real `create_mcp()` factory/lifespan and unpatched default bootstrap accepted all six active rebuilt runtimes. An observer delegates to the real bootstrap and captures shared state; no settings or state-lookup mock. 945 named checks passed, including 37 actual in-process MCP prompt calls, 42 calls executing rendered tool templates, one capabilities call, one negative target lookup and 12 actual LP summary/per-edge provenance reads. Scripts/results retain scenarios, exact rendered-message hashes and executed request/result receipts.
- 18 render cases cover exact node ID, CASE UUID and CASE URI for all six curricula; protocol messages equal ordinary deterministic renders, identities pin the exact framework/snapshot/package/profile/manifest/configuration hashes, and every nested request validates against its existing tool model. Seven templates execute per curriculum using accepted builds endpoints: target lookup, incoming page, related page, upstream traversal, supporting-standard lookup and components for target/support. Incoming builds preserve source-to-target direction; related links remain conceptual and upstream uses buildsTowards only. These representative calls validate contracts rather than claiming an entire client planning session.
- Required inputs are framework_id and an exact identifier JSON object, with optional teacher context, language and snapshot. Reuse the existing discriminated node/CASE selector models and opaque identifier namespace; bound selector text to 512 characters and context to 4,000. Ordinary and protocol checks reject malformed JSON/selector type/fields, unknown or oversized selectors, unsafe whitespace/control characters, extra fields, oversized context, invalid language, unknown routing and explicit snapshot mismatch. Blank optional protocol values follow established defaults. Boundary 512-character selector/4,000-character context fits the 64 KiB prompt policy; a lower policy raises `prompt_rendering_error` without clipping. Unknown target existence is deliberately checked by the instructed `get_standard` call, which returned typed `standard_not_found`, rather than by server-side prompt search.
- Designed incoming and related retrieval each uses one page of 25 with no cursor follow; upstream is depth 3, 20 nodes and 30 edges. Keep up to three supporting standards from actual incoming/upstream builds, retaining chains/alternatives and every used hop's original ID/direction. Related endpoints cannot become supporting standards. Target plus up to three supporting standards retain at most five returned Learning Components each; this is client evidence retention, not an LC tool limit. At most ten distinct full used-edge provenance resources are inspected across all results, deduplicated by ID; recommendations exceeding this cap or denied/oversized evidence are reduced/deferred. Preserve rationale, model-judgment confidence, warnings, candidates, producer/checker trace, hashes, exact citations, rights/license/attribution, selected coverage, unknown denominators, counts/cursors/frontier/completeness and excerpt omissions. Limits cannot be bypassed by retries or bulk reads.
- Teacher observations remain unverified caller reports, separate from source statements, stored generated-edge evidence and generated practice/review choices. Missing context permits general optional choices without invented observations. No diagnosis, measured mastery/readiness, mandatory prerequisite, direct edge from a multi-hop chain, sequence from relatesTo, or pedagogical certification is asserted. Stored confidence remains model judgment rather than learner probability or LC confidence.
- Rendering performs no evidence-file reads or lexical search after bootstrap, verified with file/search guards. Actual derivative policy denies prohibited/review-required or unreviewed rights via temporary projected metadata. No-LP capability projection skips LP calls/resources and supporting-standard selection while retaining target/components and explicitly forbidding inferred-edge fallback. The new soft support guidance merges only declared slots; mandatory caps/disclosures remain. Unexpected adapter faults become `internal_error` without exposing private paths. These projections leave accepted package/configuration bytes unchanged and do not claim synthetic data acceptance.
- Current inventory is 17 tools and nine implemented prompts, with the support prompt and exact capabilities names agreeing at public version 1.3.0. This intermediate nine includes the obsolete hypothesis prompt: DEV-020 adds curriculum review, DEV-021 removes the obsolete registration to reach the final nine. Six retained DEV-018 teaching-sequence renders have exactly the previous recorded message hashes. AST comparison confirms 52 existing functions/methods unchanged, excluding the intentionally extended overlay dispatch; existing guidance constants retain their AST values outside expanded maps. No existing teaching/study integration or obsolete-remnant removal was started.
- Seven-module Black, isort, Ruff `E,F,C90`, mypy, pylint and interrogate passed (pylint 10.00/10, docstrings 100%); workflow and `git diff --check` passed. Exact argv/cwd/exit/stdout/stderr and changed hashes are in `static.json`. The first static run found one pre-existing overlong argument-description string and overlay complexity 11; an AST-preserving literal split and combined existing guard resolved them. Initial failure receipts are retained. Behavioral checks passed again after these final fixes.
- All 3,077 entry data/config files retain exact hashes and the same inventory: original/raw/prepared/rebuilt/source inputs, retired sealed packages/configs, current accepted packages and configurations, and prior receipts are untouched. Only ignored DEV-019 feedback receipts were added under source_artifacts. No activation, configuration write, source regeneration, live LLM/paid service, formal test edit, deployment or publication occurred.

**Content Identities**

- `backend/src/kgfegmcp/prompts/models.py`: `sha256:cbbe89f1be7dae54b784ab44bb3cdeed2df9423c22ff96fcd4ebf93ba031b102`.
- `backend/src/kgfegmcp/prompts/definitions.py`: `sha256:b8e71a143e9089e31ea3a7ca3a64d4fdbe11b7af399ea43edcb15600a009044e`.
- `backend/src/kgfegmcp/prompts/service.py`: `sha256:ab5430ae105bedfa88c1bcd7c022b2c58ca639b033b7110211c30ecc1c5a27c1`.
- `backend/src/kgfegmcp/prompts/learning_progressions.py`: `sha256:ec84783aabb3c6e6343fa505a755a968dc06558c24ca7e7bacc970d7aaa4920c`.
- `backend/src/kgfegmcp/mcp/prompts/arguments.py`: `sha256:b90f7d5c4876b8bb9f84c7d2262884cd574a31cc574a4c58128aa25ce34ba61c`.
- `backend/src/kgfegmcp/mcp/prompts/register.py`: `sha256:fdb28c7c92854a2d98bda01f2545a9f92b89ba93d30e8e1508bfe5b9f84cdd15`.
- `backend/src/kgfegmcp/mcp/prompts/learning_progressions.py`: `sha256:6845f44fb11de52b08dd0be5e588d811bcf0aaff0aded1076d9ed433afcb9136`.

Retained local Developer receipts (ignored by `/data/source_artifacts/`) live at `data/source_artifacts/learning_progressions/dev019/checks/`. The evidence index records every receipt and assessed source identity; `commands.json` records actual commands, exits, initial findings and replay limits. Receipt identities:

- `commands.json`: `sha256:4e5db1df008b943899dc58dead1e39f4441e348b0d5653063d8788ea35f6bd83`.
- `entry.json`: `sha256:de1c38acd3a0e42732e9d30cad219401a33761b66dd709e792c12a511d19df31`.
- `evidence-index.json`: `sha256:751261d1ad2dd35006e7b78a245ac0bda3d434a0bd292ca9c885515faab5cb8c`.
- `feedback.json`: `sha256:f6572c6e5d0251f40dfbfacfc3e6d7d253d13f8f299c84196e98f105987c28ed`.
- `feedback.log`: `sha256:15fc9f5dd7874d24879a0f916d7ff8e5e4c23435b45d722ce794ee65f56e669a`.
- `feedback.py`: `sha256:a6520f2477f67672b939f6211d4dec7da1f59242c88998419ab575a7df71ca10`.
- `initial-static.json`: `sha256:6252700ab3b25c9cee46916bcf857085237bbd8060a076eb5f321e365b54de66`.
- `initial-static.log`: `sha256:d2171643a1afcf50e824fa1ee48c248ae5922a423de7a6567939484af517c472`.
- `preservation.json`: `sha256:e9da1eaedba6432c1087d3d634cbe5e6cb674b2ff10da2459f347d7e08ea8277`.
- `preservation.log`: `sha256:c7f3e0e33ac1f2dfe72cafe9c4f3b67fdf6a59a784e4618edfca05f849d37f61`.
- `preservation.py`: `sha256:da15f51cc3874a2f19941d62d995f01b0444e255a683a7973faef350350408d2`.
- `protected-inputs.json`: `sha256:62b71d572066dc5b1a05a1b29ba29cb1a48167aeb2f8cc7a9cee2c3f82719acc`.
- `static.json`: `sha256:b552f1dc2d3b3afb1e3ccc66c3023b3e570bdbc4f7a76ee22c69d97ce2e0c087`.
- `static.log`: `sha256:5ba074aa031b5c910f9ab615a0228cc173d47fe83ca8dbc7403a46f14337d083`.
- `static.py`: `sha256:a1f6a3eaeb2e25bc13f619d1cc228aca367225c28f6f369b49de6105134d4ad1`.

**Implementation Notes and Limitations**

Reuse the DEV-018 focused renderer, deterministic nested-request helper, shared PromptService routing/derivative/guidance/metadata/byte policy and existing exact selector union. The support request is located in the focused `prompts/learning_progressions.py` module to reuse service selectors without introducing a base prompt-model/services bootstrap import cycle. The MCP adapter delegates and converts results; no new graph/index, search/orchestration engine or model call is introduced. Version-2.0 configuration bytes remain immutable; existing support guidance slots now have generic defaults and renderer dispatch.

These are ad hoc Developer checks, not independent Tester acceptance or certification of educational output. The server returns bounded instructions; no model executed client composition, evidence-retention compliance or every eventual recommendation's provenance inspection. MCP checks are in-process, not STDIO/HTTP/MCPB smoke. No formal pytest cases were created/run. The obsolete hypothesis prompt remains explicitly pending DEV-021 and is not a usable fallback. Curriculum review remains DEV-020, existing prompt integration/removal DEV-021 and final smoke/CI/distribution DEV-022. The full Developer gate remains unmet while future approved steps are unfinished.

**Continuation**

DEV-019 is DONE. Suggested Conventional Commit: `feat(prompts): add stored progression support planning`. Next STEPWISE continuation is DEV-020 (curriculum-review prompt workflow), which remains PENDING. Reuse shared helpers and exact nested request schemas; preserve active/retired/source/package/config bytes. No later step has started. Wait for explicit user continuation.

### DEV-020 — Add the curriculum-review prompt workflow

`Status`: `DONE` `Depends On`: `DEV-019`
`Acceptance`: `AC-004, AC-010, AC-015, AC-021`

**Goal**

Render bounded curriculum inspection with explicit endpoint scope, coverage metadata and exact cited judgments.

**Affected Area**

Shared prompt models/definitions/service and MCP prompt adapters/registration.

**Expected Outcome**

Selectors/facets use the query contract; summary/statistics, up to three pages and ten exact provenance reads support a clearly bounded reviewed subset. Warnings/needs_review, unknown denominators and structural-only validation are visible; absence is not curriculum omission or cross-framework alignment.

**Self-Check**

PASS — the bounded curriculum-review prompt is implemented and checked offline. Working directory: `/Users/tzz/Projects/private/idi/KGForEdGlobalMCP`; assessed entry HEAD: `9427d3f9622a970a392140c3c45b6034d1d075eb`, plus the seven final module identities below. Entry working tree was clean. User explicitly authorized DEV-020 only; its continuation blocker was cleared before implementation. Plan stays IN_PROGRESS, STEPWISE, locked tony, AFTER_IMPLEMENTATION and Current Increment NONE; workflow stays DEVELOPING with historical Architect handoff and inactive recovery/obligations. No commit or staging was performed.

Actual final commands (repository root; uv selects the existing backend Python 3.13 runtime without dependency sync or network access):

```sh
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync python /tmp/kgfegmcp-dev020-feedback.py > /tmp/kgfegmcp-dev020-feedback.log 2>&1
python3 /tmp/kgfegmcp-dev020-static.py > /tmp/kgfegmcp-dev020-static.log 2>&1
python3 /tmp/kgfegmcp-dev020-preserve.py > /tmp/kgfegmcp-dev020-preservation.log 2>&1
python3 /tmp/kgfegmcp-dev020-evidence-check.py
```

- All final commands exited 0. Real `create_mcp()` factory/lifespan and default unpatched bootstrap accepted all six already-active DEV-023 rebuilt packages with zero exclusions; the observer delegated once to the real bootstrap, without state/settings mocks. Feedback passed 1,203 named assertions, with 81 actual in-process prompt calls, 77 tool calls/attempts (including capabilities and typed selector failures) and 36 resource attempts (30 successful exact relationship/provenance/summary/validation/unresolved reads and six expected bulk-summary denials). These counts include negative calls; they are not all successful educational workflows.
- Twenty-four render cases cover either/both/source/target with all applicable local/normalized grade and statement-type facets for each framework. Repeated ordinary renders equal protocol messages; public version remains 1.3.0 and exact framework/snapshot/package/profile/manifest/configuration hashes are retained. Every rendered nested request validates against its existing statistics/discovery/exact-edge model. Actual discovery calls preserve exact selectors, resolved node sets and endpoint scope. Node ID, CASE UUID, CASE URI and profile-enabled code examples retain namespaces; a real ambiguous code fails explicitly rather than guessing. Rendering performs no file reads or lexical search after bootstrap, checked with guards.
- The chosen designed discovery route uses up to 20 unique exact selectors (each text at most 512 characters) and up to 32 values per existing facet dimension. Profile normalization rejects unsupported, blank, unsafe and duplicate facets; strict request/adapter checks reject invalid scope, malformed/coerced selectors, duplicate/21-item selector sets, 33-item facets, invalid language, overlong selector/context, unknown routing and snapshot mismatch. Model boundary checks accept 20 selectors/32 facet values; 20 maximum-length selectors plus 4,000-character context fit the default prompt budget. Blank optional MCP strings follow established defaults. Missing/ambiguous standard existence is resolved by the instructed discovery tool; it is not silently skipped or searched during rendering.
- All six unfiltered rendered requests executed exactly three pages of 25, preserving identical request fields and adding only the returned cursor: 75 distinct original relationship IDs each, with a remaining cursor and null filtered totalMatchingCount. This demonstrates a bounded reviewed candidate subset, not exhaustive coverage. Statistics remain package-wide per-type totals. One returned exact relationship and its full provenance were inspected per framework; full ten-edge inspection and final model composition are client instructions, not claimed executed behavior.
- Sanitized summaries and actual statistics agree on package stored counts; summaries preserve CBSE needs_review=1, Ghana English/Mathematics unresolved-warning pairs=10/141, separate edge-warning counts, and structural/process-only validation with semanticValidationPerformed=false and pedagogicalCorrectnessEstablished=false. Current summaries actually supply package eligibility counts; these remain distinct from unknown filtered matching/review denominators. The instructions preserve unknown values when absent and forbid invented percentages. Raw generation summary remains bulk-denied under actual rights, while public summary/validation and permitted unresolved/per-edge evidence remain readable.
- Mandatory instructions preserve OR-within/AND-across whole-endpoint conjunctions and either/both/source/target meanings, canonical relatesTo orientation, three total pages of 25 (including zero-match work-limited pages), ten distinct exact-edge/full-provenance inspections, warnings/excerpt/omission flags, original citations/hashes/attribution, and policy failures. Package totals, filtered counts, returned IDs and fully inspected subset are separate. Recommendations requiring uninspected/denied/over-cap provenance are reduced or deferred. Caller observations, source standards, stored generated judgments and generated review questions stay distinct. Absence never establishes curriculum omission, pedagogical disconnection, certification or cross-framework/snapshot alignment.
- Actual derivative policy denies prohibited/review-required generation and unreviewed rights through temporary catalog metadata projections. A no-LP projection retains statistics instructions but skips LP retrieval and dependent review, explicitly distinguishing unavailable from zero. Curriculum soft guidance applies only to its declared slots and cannot replace mandatory caps/disclosures. Lower prompt byte limits fail without clipping. Unexpected adapter faults are masked as internal_error. These are boundary projections, not mutated or newly accepted data.
- Inventory now correctly advertises 17 tools and ten prompts, including curriculum review and the obsolete hypothesis registration intentionally retained for DEV-021. Six teaching-sequence and six support-plan messages retain their exact prior recorded hashes. AST comparison preserves all 57 existing functions/methods outside intentionally extended overlay dispatch, plus existing guidance constants outside expanded maps. The overlay dispatch now uses an explicit mapping to extend it without exceeding complexity 10. Three clean-process import orders across base prompt models, services, focused renderer, adapters and bootstrap pass without import cycles.
- Seven-module Black --check, isort --check-only, Ruff `check --select E,F,C90`, mypy `--cache-dir /tmp/kgfegmcp-dev020-mypy`, pylint and interrogate `--generate-badge /tmp/kgfegmcp-dev020-badge` all passed (mypy no issues; pylint 10.00/10; docstrings 100%). Exact argv/cwd/exit/stdout/stderr and final content hashes are in static.json. Workflow and `git diff --check` passed and are rerun after this DONE/blocker record.
- Initial static findings were import/format/line-length issues; corrected using established tools. Integration exposed the omitted explicit advertised name, now fixed. Scratch checker corrections concerned capabilities' no-argument schema, binary JSON resources, real code ambiguity and the presence of actual package eligibility counts; earlier failed runs are not passing evidence. Iteration notes and retained logs are in commands.json and named preliminary feedback logs.
- Preservation verifies all 3,092 entry data/config files have unchanged paths and exact hashes, including accepted active and retired sealed packages/configs, original/raw/prepared/rebuilt inputs, maintained build sets and prior receipts. Only new ignored DEV-020 receipts were added afterward. No activation rerun, source/configuration regeneration, external source access, live LLM/paid-service call, formal test edit, deployment or publication occurred.

**Content Identities**

- `backend/src/kgfegmcp/prompts/models.py`: `sha256:0af4fc42ba1f81310a4de21ff3f46dc21fdaa7ec875de46375c4ee48d440a43e`.
- `backend/src/kgfegmcp/prompts/definitions.py`: `sha256:0fbc854ff129e72439ef597a52a0c76b6e39ba247eec5509da3e5100a4a4b46d`.
- `backend/src/kgfegmcp/prompts/service.py`: `sha256:ef098c8c3b65b6ae18b2c9d63cf62c0849435a0a8dc7e9ab2fa6512c8ed77449`.
- `backend/src/kgfegmcp/prompts/learning_progressions.py`: `sha256:5eb8d54621203481520abf0500979d5b4b13a06ed5662b7fdff97d74aa90c529`.
- `backend/src/kgfegmcp/mcp/prompts/arguments.py`: `sha256:52e6c7e63e8081ce1ff1deabac6c2c328493ee88a39980615bc12239463d7741`.
- `backend/src/kgfegmcp/mcp/prompts/register.py`: `sha256:edf13c73f2d5311b3347e4a71ddb8d7a0eca083dbe4dec3a0f65b76478dd3c5b`.
- `backend/src/kgfegmcp/mcp/prompts/learning_progressions.py`: `sha256:9baf3c5a709b8627b0f4138e1197c60dbc75dd80d466f307f49ec5391d9960ef`.

**Local Evidence and Limitations**

Retained ad hoc Developer receipts live under ignored `data/source_artifacts/learning_progressions/dev020/checks/`. The evidence index binds actual scripts/results/logs and assessed source/runtime identities; protected-inputs.json binds every unchanged data/config file. All six active package manifest/profile hashes equal the DEV-017/DEV-023 recorded identities; no acceptance or activation was repeated. Selected receipt identities:

- `commands.json`: `sha256:a871d91b42b22a1567a0ea206355c9a57d847a7e90cce0d1fe32c47ca55695e6`.
- `entry.json`: `sha256:da09ce9bf77967a15d4c180350d652d94226a0667d9854cc813c5f75cbc0c34d`.
- `evidence-index.json`: `sha256:cebfd1a57c8577ef2921ee2455ee700768b7c3163856e6fbe2d0836b8eb5351c`.
- `feedback.py`: `sha256:ae0ede13fb6b3eb9edb1be46742e9df9fc32bbd273983c6fb07556432f5e5630`.
- `feedback.json`: `sha256:c6f8e91a34ed6c65def12e95f30ef8c579567f6a8154fa4346c435a2cb3184b4`.
- `static.py`: `sha256:05442dba729b8b56c8759bdf2622a244e69006b847197bacfdb0f9e4be03310e`.
- `static.json`: `sha256:c6dbbe45b11de85f7c7fc1f2e3f4990f46151b3823e6b6aa1424d8bc7d7f6572`.
- `preservation.py`: `sha256:85dc93e761b68db5aa6b7780c03e025d6e83b0eca5cbd6d63378a2c3ab309cdd`.
- `preservation.json`: `sha256:5dfc39533cdbca356fe88540c86286b5bdc9e25fe0c1016d6c086195c40cd118`.
- `protected-inputs.json`: `sha256:e7889618b3635b9e6e4984e392f7dc3d2f2abc04f754a62268c8d820aea4f59c`.
- `evidence-check.py`: `sha256:513edec72ef78840f7794cd7bca58b02cb43dd0b42e8aec03e7aeb54fb00c5de`.
- `evidence-check.json`: `sha256:5b4da647c1e0a0befd886d45accabc01550bcf9caf10efef492468f802fe8312`.

These are Developer implementation checks, not independent Tester acceptance, formal AC verification, semantic/pedagogical validation or curriculum certification. No model executed the final review, enforced client inspection caps or generated educational output. Protocol checks are in-process rather than STDIO/HTTP/MCPB. No formal pytest suite was created or run. Current candidate ordering can leave one relationship type outside the three-page subset; the workflow must disclose that limited subset instead of implying both types were exhaustively reviewed. Full future independent coverage remains Tester-owned.

**Implementation Notes and Continuation**

The focused request inherits existing ProgressionFilters and reuses ProgressionStandardIdentifier, EndpointScope and facet bounds without importing services into base prompts/models.py. PromptService retains routing, selection, derivative rights, configuration guidance, metadata and prompt-byte policy; the focused renderer emits deterministic nested client requests and does not query the graph. No orchestration engine, alternate graph/index or immutable configuration change was introduced.

DEV-020 is DONE. Suggested Conventional Commit: `feat(prompts): add bounded curriculum progression review`. Persist the next STEPWISE continuation for DEV-021 (existing prompt integration and obsolete hypothesis removal), then wait. DEV-021 and DEV-022 remain PENDING; no full Developer/Tester handoff gate passes while those approved steps are unfinished. Public version remains 1.3.0; DEV-021 removes the obsolete registration from the intermediate ten to reach the final nine prompts. Preserve all source/retired/current package/configuration evidence and do not rerun activation.

### DEV-021 — Integrate stored evidence into existing prompts and remove hypothesis remnants

`Status`: `DONE` `Depends On`: `DEV-020`
`Acceptance`: `AC-010, AC-016, AC-017, AC-018, AC-021`

**Goal**

Extend four useful teaching/study workflows through shared bounded LP evidence guidance and finish removal of all obsolete prompt/configuration logic.

**Affected Area**

prompts/definitions.py, models.py, service.py; mcp/prompts registration/arguments; existing teacher/student/multigrade/administrator/comparison adapters and configs.

**Expected Outcome**

Teacher guide, study support, handbook and multigrade retrieve optional stored links/provenance/LC evidence after exact selection while preserving existing outputs. Administrator/comparison notices remain truthful. No old hypothesis prompt, guidance type, candidate fallback or obsolete heuristic/overlay/reference expectation remains in active runtime/configuration. Historical source-origin text and useful LC/comparison inference remain.

**Implementation**

Added one focused `render_optional_progression_workflow` helper, reached through the already-selected accepted runtime by PromptService. Teacher guide, study support, handbook and multigrade each append this step once after exact selection and existing component retrieval. The step retains at most three already-resolved standards across the whole workflow/all room grades, one direct page of 25 per standard with no cursor follow-up/traversal/path expansion, and at most ten distinct full used-edge provenance inspections. It preserves incoming/outgoing/related distinctions, original endpoint/relationship identities, rationale, confidence as model judgment, warnings, producer/checker traces, source/config/content hashes and exact citations. It reuses existing LC support links and earlier results; shared LC, hierarchy/DAG and grade behavior never become LP edges.

Sanitized summary evidence distinguishes package-wide totals from the returned/reviewed subset, exclusions, unknown denominators and structural-only validation. Unavailable/empty/sparse/incomplete/denied optional evidence preserves the original useful output with explicit limits and no inferred-edge fallback. Absence cannot establish curriculum omission or cross-framework alignment. Shared rules now distinguish LC provenance from stored LP judgment provenance and caller observations from source/generated evidence. Administrator/comparison disclosures acknowledge stored generated LP without creating cross-framework links or official equivalence.

Deleted the hypothesis adapter module, PromptService method, old candidate call and scope validator, direction/candidate aliases, name/registration/exports/default guidance/disclosure. Retained ProgressionGradeFilters used by the teaching-sequence workflow. Public prompt version stays 1.3.0. No base prompt-model/service imports were added; selectors, facets, endpoint_scope semantics, three new prompt workflows and shared routing/rights/guidance/metadata/byte enforcement remain intact. Active versioned configurations already removed old heuristics/overlays and remain byte-exact.

**Self-Check — Actual Developer Feedback**

PASS — working directory `/Users/tzz/Projects/private/idi/KGForEdGlobalMCP`; assessed HEAD `da31e934f98fc59435c66c1ae0038d10ed0f221a`, clean entry. Changed working-tree identities below bind implementation checks; no commit was created. Actual final commands:

```sh
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync python /tmp/kgfegmcp-dev021/feedback.py > /tmp/kgfegmcp-dev021/feedback.log 2>&1
python3 /tmp/kgfegmcp-dev021/static.py > /tmp/kgfegmcp-dev021/static.log 2>&1
python3 /tmp/kgfegmcp-dev021/preservation.py
node .standards/bin/check.mjs
git diff --check
```

- Final commands exited 0. Real factory/lifespan/default bootstrap accepted all six already-activated DEV-023 rebuilt runtimes with zero exclusions. Feedback passed 1,116 named assertions: 150 actual in-process prompt calls/attempts, 40 tool calls and 48 successful resource reads. Counts include intended negative prompt calls, not only successful workflows. Fifty-four render cases cover all nine prompts against six frameworks/pairs; repeated protocol renders are deterministic with file-read and lexical-search guards. Maximum sampled message size is 28,555 bytes. Version and exact runtime/config metadata remain present.
- Final exact discovery/capability/PromptName inventory agrees on 17 tools and nine prompts. The old prompt lookup fails as unknown and the obsolete service method/tool is absent. Targeted source/config search finds only the two intentionally stale CLI smoke inventory strings in `backend/src/kgfegmcp/cli/smoke_checks.py` (old prompt and old tool). Those checks are DEV-022-owned and are not active registrations; transport smoke is not claimed passing. Historical STANDARDS evidence, original provenance and Documenter-owned user documentation remain unchanged.
- Shared nested request templates validate against existing direct-query/exact-edge schemas and pin framework/snapshot/node-ID namespaces. Actual calls execute three direct pages per framework (18 total), six existing LC support queries and 15 exact edge queries. Fifteen full per-edge provenance resources and their exact relationship resources were read: ten distinct edges in one framework workflow and one in each other framework. Six sanitized summary/validation/unresolved sets were read. Original generated edge identities and explicit citations remain exact. All 18 sampled direct pages were complete and returned 3–11 relationships each; this sample does not establish all possible cursor/empty conditions. Incomplete/empty/denied handling is explicit rendered guidance, not executed model behavior.
- Missing-LP projections for all four roles across six runtimes skip LP calls while keeping standards/component output. No-LC projections preserve standards-only output for the three applicable roles and retain multigrade's existing capability rejection. Prohibited/review-required derivatives and unreviewed rights reject all four extended prompts. Lower prompt-byte policy fails without clipping; replacement soft lesson guidance cannot remove mandatory evidence limits. Unexpected adapter errors stay masked. These checks use temporary boundary projections only; no accepted package is altered.
- AST comparison preserves 64 existing functions/methods across prompt service/models/renderers/adapters; for the four extended service methods the only ignored addition is the single shared helper call. This preserves their original output contracts, grade/shared-LC behavior, exact selection, three prior LP renderer workflows and support/teaching/curriculum facet contracts. Existing guidance constants remain identical outside the declared shared disclosure/maps and obsolete removals. Three clean-process import orders pass without cycles.
- Seven changed-module Black, isort, Ruff E/F/C90, mypy, pylint and interrogate checks all pass: no type errors, pylint 10.00/10 and 100% docstring coverage. Exact argv/cwd/exit/stdout/stderr and final source hashes are retained in static.json; workflow and whitespace checks pass. Initial static syntax issues from deleting multiline aliases were corrected. The initial no-LP check fixture correctly hit the accepted-runtime manifest invariant and was replaced with an isolated metadata projection. Failed-attempt logs/results are preserved alongside final passing results.
- All 3,112 entry data/config files retain exactly the same inventory and SHA-256 values, including active and retired sealed packages, original/raw/prepared/rebuilt inputs, maintained build sets, versioned configurations and all prior receipts. Only new ignored DEV-021 receipts are added. No activation, source regeneration, external source modification, live LLM/paid call, deployment, publication or formal test edit occurred.

**Content Identities**

- `backend/src/kgfegmcp/prompts/models.py`: `sha256:05e825ec92e45a905501d30da7c9025c41c353850659dce7d2674a706c39c22c`.
- `backend/src/kgfegmcp/prompts/definitions.py`: `sha256:1ff1fb9a93cc87b079c8e988435f10e5b39d7bb1efb9c4bb44c337025a0ed827`.
- `backend/src/kgfegmcp/prompts/service.py`: `sha256:18ffb9109f9c0e53c5b0c6e22fee7e08fa89049ea985795e9fa8fcac51e744e8`.
- `backend/src/kgfegmcp/prompts/learning_progressions.py`: `sha256:b1e523a9607547cd68157bebb52dcd007422ce5af5beb1336755a6dd3a60f187`.
- `backend/src/kgfegmcp/mcp/prompts/arguments.py`: `sha256:c9750355416e7b84b00645774e839021c186a95d5cb599733a9b5b70c88cd1e8`.
- `backend/src/kgfegmcp/mcp/prompts/register.py`: `sha256:bd20dcbba02c522e64af4cfdaf5516f72c728cbe519d67b0cf6a4a3033c54795`.
- `backend/src/kgfegmcp/prompts/__init__.py`: `sha256:df384a97f842ded51435e27ffd039e46086436fe303d00d037545a270c322d87`.
- Deleted `backend/src/kgfegmcp/mcp/prompts/progression.py`; assessed-HEAD content was `sha256:37f4506aa0cf06df57f824646223df323a24dca0c2beb08d91eb1c8f6cccb3ca`.

**Local Evidence and Limitations**

Local Developer scripts, exact command results, rendered-message/runtime identities, protected inventory and hashes are retained under ignored `data/source_artifacts/learning_progressions/dev021/checks/`. Selected receipt identities:

- `commands.json`: `sha256:8b467f17797db106b9f198f5ce6db39c3e94b71f76b20833332893e956c7b947`.
- `entry.json`: `sha256:4f92e51303664d0d88e0450e1c3dc79ea6cbb372d5e3169c5ce052d16b002e65`.
- `evidence-index.json`: `sha256:9472fbbccacc3da83015974d1c501891eca1b717d8c2aa4846b1b37da5d09334`.
- `feedback.py`: `sha256:d95b6b64a5bc426ab173b1e46d3decb0c2179f23a06c1ea2b1048e1780a03338`.
- `feedback.json`: `sha256:b6e8149d23a82c20af7b5d017ed602cb2f708df8814be835122eb5ae8c2b806d`.
- `static.py`: `sha256:565b38773bf4ed669f08c89d46881844f13847df4e618393707e587f3544775f`.
- `static.json`: `sha256:3c90637ee56474dfc702413fa065f21d392ef65631b1b9a36eac61ed3f395501`.
- `preservation.py`: `sha256:32b71463f2c8ffe661f111e667c3b48eae6daeba391af7be934f2b6ee39e74f3`.
- `preservation.json`: `sha256:86faf880f97c590cae46cb8ea10fbe14ca77e38920fadcf2f8eb3ceaf3967c7b`.
- `protected-inputs.json`: `sha256:e207d158512ccae144fbad6756c0f5c1e58edb1af5babe875ec504c685badf9d`.

These are ad hoc Developer checks, not independent Tester acceptance or formal AC verification. No client model composed educational output or enforced evidence-selection/citation instructions. Rendered bounded behavior and representative real evidence retrieval do not establish semantic/pedagogical correctness, exhaustive all-edge/all-selector coverage or curriculum certification. No formal pytest suite was created or run. STDIO, local HTTP, CI and MCPB distribution verification remain DEV-022; Documenter owns user-facing obsolete-reference cleanup.

**Continuation**

DEV-021 is DONE. Suggested Conventional Commit: `feat(prompts)!: replace progression hypotheses with stored evidence`. STEPWISE now waits for explicit DEV-022 continuation. Keep DEVELOPING, locked tony, AFTER_IMPLEMENTATION and Current Increment NONE; no full Developer/Tester handoff gate passes while DEV-022 is unfinished. Preserve all source/package/configuration evidence and do not rerun activation.

### DEV-024 — Retrieve complete permitted evidence through bounded content windows

`Status`: `PENDING` `Depends On`: `DEV-015`
`Acceptance`: `AC-004, AC-010, AC-011, AC-012, AC-018, AC-021, AC-029, AC-031, AC-034`

**Goal**

Expose the native resource content through one deterministic read-only model-callable route, preserving its policy and exact byte identity.

**Affected Area**

resources/uri.py constructors, service.py, models.py and repository/policy contracts; focused ordinary URI dispatcher/paging models/helper; errors.py, bootstrap.py/AppState and mcp/register.py plus a thin read_evidence adapter.

**Expected Outcome**

The nested request has uri (1..4096), maxContentBytes (default 16384, positive maximum 32768) and optional bounded cursor, with extra fields rejected. Dispatch accepts exactly Catalog and the fourteen existing URI templates: validate scheme/authority/path/encoding/typed segments, reject query/fragment/userinfo/port/traversal/encoded separators/double decoding, decode once and return constructor-canonical URI. Snapshot routes stay exact. Call ResourceService directly; no internal MCP client or new policy clone.

Authorize and produce the complete native ResourceDocument before UTF-8 paging: preserve rights, safe manifest reads, 32 MiB source/8 MiB whole-return ceilings and lower operator limits. Return unchanged ResourceMetadata, faithful content window and full/partial contentStatus; original-byte offsets, chunk/whole hashes, total bytes, actual nextCursor/unchanged nextRequest and effective envelope limits distinguish last-window completion from a full original record. Windows end on Unicode boundaries and fit the shared encoder ceilings. Stateless checksum-bound cursors bind canonical URI, complete content/metadata identity, maxContentBytes and next boundary; reapply policy each call. Reject stale/mismatched/nonboundary/no-progress cursors. Missing, denied/native-oversized, unsupported UTF-8 and evidence_result_too_large have safe distinct errors; paging never bypasses native limits or bulk denial.

**Self-Check**

NOT RUN. Offline ad hoc dispatch coverage for all fifteen URI shapes; diagnostic exact edge/full original provenance/endpoint standards and representative LC content/full provenance; concatenate ordered Unicode windows and verify exact original bytes/hash and metadata. Exercise invalid URI/encoding/extra inputs, altered/stale/range cursors, rights/source/whole-return denial, empty document/format/indivisible output failure and both serialized envelope ceilings. Compare with native ResourceService and actual in-process MCP output; run configured changed-module Python checks and relevant existing resource/protocol tests without editing Tester-owned cases. Persist exact commands, cwd, input/output identities and limitations.

**Implementation Notes**

Reuse the same immutable AppState services and resource constructors. Keep accepted artifacts/configuration bytes and existing native registrations unchanged. Full evidence is permitted native content, including clearly identified derived representations; no missing trace is synthesized.

### DEV-025 — Share native workflows through seven typed instruction variants

`Status`: `PENDING` `Depends On`: `DEV-024`
`Acceptance`: `AC-010, AC-013, AC-014, AC-015, AC-016, AC-017, AC-018, AC-021, AC-030, AC-031, AC-034, AC-035`

**Goal**

Expose exactly the seven affected deterministic workflows through get_workflow_instructions and make their native/shared instructions explain the practical evidence route.

**Affected Area**

prompts/models.py, service.py, learning_progressions.py, definitions.py and focused ordinary dispatch/typed models; mcp/prompts argument adaptation and new thin tool adapter/registration; bootstrap.py as needed; generic prompt-library version, backend project/lock metadata and packaging/mcpb/manifest.json.

**Expected Outcome**

A nested request discriminated by workflowName permits only the three LP workflows plus teacher_guide_draft, student_study_support, student_handbook_section and multigrade_lesson_plan. Each variant reuses current renderer inputs/defaults/constraints with camel-case aliases, typed arrays/selectors and extra-field rejection; reject arbitrary names/maps/serialized request strings. Ordinary dispatch reaches the same renderer as native prompts. Return complete rendered PromptRenderResult, validated effectiveRequest and matching pinned PackageReference/profileSha256/manifestSha256; canonical JSON text equals structuredContent. Preserve request-data separation, derivative rights, configuration identity, <=64 KiB/lower PromptPolicy and shared tool ceilings; workflow_instructions_too_large is explicit, with no clipped instructions/cursor/execution.

Generic shared instructions show native reads when accessible or read_evidence with exact returned/constructor URIs; finish used original provenance within at most ten distinct used-edge records and 32 continuation windows (16384-byte requests) per workflow invocation, disclosing/deferring incomplete/denied/oversized claims. Retain every existing retrieval/inspection cap and all nine native prompts; administrator/comparison receive only appropriate shared evidence wording. Native and tool variants render identical messages for identical validated requests/exact context. Server/MCPB advances to 0.4.0 and generic prompt library to 1.4.0; sealed package/source/delivery/manifest/profile/prompt-configuration bytes and versions remain unchanged.

**Self-Check**

NOT RUN. Offline ad hoc native/alternate message equality for all seven variants at pinned accepted identities, effective defaults and schema discrimination/extra-field/type/rights/size failures; inspect practical LP and AS/LC evidence steps, finite continuation/record caps and retained administrator/comparison messages. Measure complete actual MCP text/structured envelopes and prompt policy limits; reconcile version metadata/locked environment locally with no dependency upgrade. Run relevant existing prompt/protocol tests as implementation feedback and changed-module static checks; record commands, cwd, content identities and limits. No LLM call or client composition/end-to-end workflow acceptance.

**Implementation Notes**

Share validation/adaptation below MCP rather than invoke decorated native handlers. Framework-specific prompt configuration is an immutable input. Runtime generic workflow messages are Developer implementation; user-facing guides, Desktop walkthrough and remote checklist remain Documenter-owned.

### DEV-022 — Align local transport checks, CI and retained MCPB distribution

`Status`: `PENDING` `Depends On`: `DEV-021, DEV-025`
`Acceptance`: `AC-018, AC-019, AC-021, AC-022, AC-023, AC-024, AC-025, AC-028, AC-029, AC-030, AC-031, AC-033, AC-034, AC-035, AC-037`

**Current Recovery Assignment — proposed 2026-10-06**

Reconcile capabilities, explicit registration, descriptions and exact input/output schemas with the completed five LP text contracts and two access tools: 19 tools, nine native prompts, one fixed resource, fourteen templates. Extend the existing shared smoke implementation for repository STDIO, local loopback HTTP and stage STDIO to parse ordinary JSON text independently, replay actual LP/evidence cursors, exercise the pinned Nigeria diagnostic edge/target and representative AS/LC full content/provenance, LP summary/validation/unresolved (including CBSE needs_review and Ghana warnings), workflow/native-message equivalence, retained native resources and safe typed failures. Existing CI remains meaningful/offline; reconcile changed triggers only if needed, without owning formal cases.

Use the existing builder for a distinct candidate under data/source_artifacts/learning_progressions/client-recovery-dev022/: kgfegmcp-0.4.0-client-recovery.mcpb and bundle/. If that destination already exists with different content, retain it and choose another distinct preparation path rather than overwrite history. Bind current source/archive/stage member bytes, versions, complete active evidence closure and stage-root imports; preserve all historical candidates/receipts. Refresh the final candidate again through this same step if later Documenter-owned shipped input changes require it. Developer does not edit user documentation; shipped instruction consistency remains an explicit Documenter/Reviewer reconciliation dependency, never a passing claim for stale 17-tool prose.

Current self-check: NOT RUN. Established offline repository STDIO and loopback HTTP smoke, official MCPB build/validate/pack/closure checks and retained-stage smoke under its own roots; measure actual text/structured envelope sizes and retain exact schema/resource/result/receipt identities. Run relevant existing offline tests and static checks as implementation feedback. No public connector/Desktop workflow pass, deployment, publication or semantic certification is claimed. Full Developer handoff waits for all current steps and the applicable gate; Tester independently establishes every current AC.

The prior definition and execution evidence below remain history where superseded by this recovery assignment.

**Goal**

Update executable smoke/CI/distribution integration and record final implementation-level evidence before independent Tester handoff.

**Affected Area**

cli/smoke_checks.py, stdio_smoke.py/http_smoke.py as needed, build_mcpb.py, packaging configuration and .github/workflows/tests.yml.

**Expected Outcome**

Shared exact inventory is 19 tools, nine prompts, one fixed resource and 14 templates. Smoke identities resolve replacement snapshots and inspect representative LP evidence. CI includes data/config/package changes and rejects pytest no-collection success. Retained MCPB stage contains complete active runtime evidence and no source-preparation/external/retired inputs. Local transports and staged runtime run without model/paid calls or deployment.

**Implementation**

Updated shared smoke inventory to the final 17 tools/nine prompts and the replacement Ghana English snapshot, retaining the original standard/component/unresolved representative identities. Added sanitized LP summary and exact per-edge provenance reads so one fixed resource plus all 14 templates are exercised. Capabilities must agree with the listed inventory. The focused smoke_progressions helper compares each of the five nested request schemas with its existing service model after FastMCP's own schema compression, fingerprints all 17 input/output schemas, executes the five bounded stored-edge operations and an expected missing-edge error, and retains exact query/result content identities. The same shared checker runs in repository STDIO, loopback HTTP and retained-stage STDIO; no parallel server/service implementation was introduced.

STDIO smoke now passes `--offline` to its locked uv child and suppresses Python bytecode writes. MCPB retains its established copy/validate/pack/byte-verify mechanism and required paths. Its manifest version now matches the existing backend 0.3.1 (previous stale value 0.1.0); public prompt version remains 1.3.0. Source copying now excludes generated .egg-info alongside existing caches, because editable installation otherwise rewrites development metadata that the old copy recipe included. Runtime source and all declared original/provenance-partition data remain included. No active package/profile/prompt version or source evidence changed.

CI trigger and job filters now include backend, data, configuration, packaging, Dockerfile and the workflow itself; manual dispatch is eligible even without detected changes. Dependency installation is locked. Pytest failures—including exit 5—propagate directly instead of being converted to success; the configured command excludes costs-money cases. This selection is not a substitute for Tester mocking any model/paid boundary.

**Self-Check — Actual Developer Feedback**

PASS for DEV-022 implementation checks; formal test coverage remains pending with Tester. Working directory `/Users/tzz/Projects/private/idi/KGForEdGlobalMCP`; assessed HEAD `3a11ded38a3ad666487207e79c14f31012ec6fa7`, clean entry. No commit was created. Full argv, cwd, results and logs are retained in checks/commands.json, operational.json, http-command.json and static.json. Actual commands include:

```sh
python3 /tmp/kgfegmcp-dev022/operational.py
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync kgfegmcp-stdio-smoke
python3 /tmp/kgfegmcp-dev022/http.py
UV_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 /Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync kgfegmcp-build-mcpb --output /Users/tzz/Projects/private/idi/KGForEdGlobalMCP/data/source_artifacts/learning_progressions/dev022/kgfegmcp-0.3.1-dev022.mcpb --stage-output /Users/tzz/Projects/private/idi/KGForEdGlobalMCP/data/source_artifacts/learning_progressions/dev022/bundle
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync kgfegmcp-stdio-smoke --bundle-root /Users/tzz/Projects/private/idi/KGForEdGlobalMCP/data/source_artifacts/learning_progressions/dev022/bundle
python3 /tmp/kgfegmcp-dev022/static.py
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync python /tmp/kgfegmcp-dev022/final_checks.py
node .standards/bin/check.mjs
git diff --check
```

- All six exact `kgfegmcp-validate-packages one --framework-id … --snapshot-id … --read-only` commands exited 0 with isValid=true, terminalRevalidation=true, readOnly=true and persisted=false. They select the DEV-017 activated/DEV-023 rebuilt identities recorded in operational.json. No activation or validation-state persistence was repeated.
- Repository STDIO, local Streamable HTTP and final retained-stage STDIO exited 0. Each actual factory/bootstrap accepted all six packages with zero exclusions. Each run reports 17 tools, nine prompts, one fixed resource, 14 templates, and 15 representative JSON resource reads. All three inventories, 17 input/output-schema fingerprints, five query payload/result identities, expected learning_progression_not_found error and resource summaries agree exactly. Each performs five successful LP queries, one expected failed lookup and one capabilities query (21 tool calls/attempts and 45 resource reads across the three final runs). This is representative transport evidence, not exhaustive domain acceptance.
- HTTP used only `http://127.0.0.1:51290/mcp` in this run. The bounded harness starts the existing create_mcp factory with stateless HTTP, runs the actual HTTP smoke CLI and terminates its own server process group; the log confirms application shutdown and server completion. No deployed endpoint was contacted or changed. STDIO logs remain on stderr and child shutdown completed.
- Official installed MCPB validate/pack plus existing builder archive verification passed. Final archive contains exactly 650 files, 82,154,022 bytes, with SHA-256 `9fd1bc9c4c03d8c9460388c70f2bdb5b231eda1de693910b76f8dfc5a43866a1`. Every archived file equals the current intended copy input and retained-stage content. All six accepted package trees, full original LP provenance maps, indices and all 64 shards per framework are present. No preparation, raw-copy, retired, external-source, .egg-info or cache tree is archived. Stage startup installs 74 cached dependencies offline into its own .venv and creates local .egg-info; these post-build environment outputs are not archived, and every originally staged distribution file remains byte-exact.
- Final ad hoc final_checks.py passed 3,953 checks, mostly exact file-identity/preservation assertions. It establishes 3,129 protected entry files unchanged (data/config and the existing dist archive), exact archive/stage closure and transport agreement, matching CI YAML trigger/job filters, a shell stub proving exit 5 propagates, and focused copy-boundary exclusion/symlink-rejection behavior. Active source/config searches find no old hypothesis/tool/heuristic/overlay symbols. Historical evidence and Documenter-owned obsolete user references are deliberately retained for the appropriate phase.
- Four changed Python modules pass Black, isort, Ruff E/F/C90, mypy, pylint 10.00/10 and interrogate 100%. Final exact argv/outputs/content hashes are recorded in static.json. Workflow and diff whitespace checks pass and are rerun at handoff.
- Actual offline pytest was run with `pytest -rsPQ -m "not costs-money" --cov-report term-missing --cov-config=./pyproject.toml --cov=kgfegmcp tests -o cache_dir=/tmp/kgfegmcp-dev022/pytest-cache`. It collected zero cases and exited 5. This is NOT passing verification or meaningful coverage; the emitted coverage table is not accepted evidence. There are no test modules to run yet. Tester owns creating the missing meaningful offline cases and AC-023–AC-025 formal evidence; CI now honestly fails until such cases exist. Developer did not create or change formal test artifacts.
- Early smoke assertions incorrectly assumed a referenced instead of inlined FastMCP schema and wrong summary/provenance field names; corrected to the actual typed/public contracts, with failed logs retained. Initial archive passed the old recipe but post-start stage comparison exposed generated .egg-info/SOURCES.txt drift; metadata exclusion corrected the recipe and the rebuilt final stage passes. The initial archive/stage remain retained separately for evidence. Initial relative build paths resolved beneath backend due to uv --directory; only those newly created outputs were moved into the intended ignored DEV-022 evidence directory, and the final build used absolute paths. No existing distribution was overwritten.

**Content Identities**

- `.github/workflows/tests.yml`: `sha256:c42265cbf123f9f840a78daf9e382e0a463fc95175652940103ee405d048a9b8`.
- `backend/src/kgfegmcp/cli/build_mcpb.py`: `sha256:3676404a4a96f5c19c7642f96470128033c634d2c16d9b9417a130c5bc27a97b`.
- `backend/src/kgfegmcp/cli/smoke_checks.py`: `sha256:400aef1c340c8ff931e279a7bcb2fd74bdba6372b12f5a3686901668213ab217`.
- `backend/src/kgfegmcp/cli/smoke_progressions.py`: `sha256:a690a3a0bfb7c298fbb1e60ae887ee45449c06d866269d86aa0de25fc1f7dcc4`.
- `backend/src/kgfegmcp/cli/stdio_smoke.py`: `sha256:60aa908529d9ca7263b81ff9e47561f70275099d8a4e2b75634746435add1227`.
- `packaging/mcpb/manifest.json`: `sha256:76d543a754a1c66f78f7c49dbdfeba2e1480bdca2cc168f2e76deb1de5cad825`.

**Retained Evidence and Limits**

Local scripts/results and identities are in ignored `data/source_artifacts/learning_progressions/dev022/checks/`. Final retained stage: `data/source_artifacts/learning_progressions/dev022/bundle`; final archive: `data/source_artifacts/learning_progressions/dev022/kgfegmcp-0.3.1-dev022.mcpb`. The source/input tree remains sealed. Receipt identities:

- `commands.json`: `sha256:3536272e89d2e2a42bef90750c9bb485034ab3c4b76cb7a2aa66663c38e04283`.
- `entry.json`: `sha256:89cede30f7a52127af42dd30d8d24fab06055bd4dfb3214d930b08906cd2f461`.
- `evidence-index.json`: `sha256:984b371a09565aef9c93765102a1e06bd5931d03202ec28be7cd9bf7f5164857`.
- `operational.py`: `sha256:d2d255443d59d12ce39a29f3e5997b26e450076ee72a0d24b8f0e8734b33b6f4`.
- `operational.json`: `sha256:a13a9211836dad67b8cf15821ecfabe1e032f65e32f33b74ec7f289d0a3fa5cf`.
- `stdio.json`: `sha256:03478cfb7e90e1c7932a0763ff23179af3e413636f207347981dcb2f7ac33929`.
- `http-command.json`: `sha256:02f94936185a3c8581cb17c3a3abc14799ca64b0a67799e2798f327cb53e7289`.
- `http.json`: `sha256:c84831060feb924cd6e1b620dd7b7eab54297cb1bcbdfdae1eb12cf9e27de731`.
- `stage-stdio.json`: `sha256:e79cfd83ad3f5fd4ed93ba3ad11d36d272f5d5ba0b584aaffb4ab3ed93497e2e`.
- `static.py`: `sha256:fc4e77f3d481c0425affb198fe8697374d6b34d80b3edae03532013f0e46a0e4`.
- `static.json`: `sha256:23dcfefb8f1c60557d972a02d4096b1bfd418a04d03bfbdeba04ea1aaed1b431`.
- `final_checks.py`: `sha256:d812d6cdebb1b56efe4f35af0491ecfb22ba0d77254a29c89669fcd7ad313d4f`.
- `final-checks.json`: `sha256:2ed6557e9e04361974530eb1494cb65e4c23f994506526665fb8e4155830482c`.
- `protected-inputs.json`: `sha256:83c35c3880cd9230997180b057b62198c34271de4e4ae63230c5e66d815981a7`.

These are Developer implementation-level checks, not independent Tester acceptance, semantic/pedagogical certification, remote GitHub Actions execution, or deployment. No LLM/paid API, source/checker regeneration, activation, publication or deployment occurred. Formal offline tests are absent; independent Tester must establish meaningful collected behavioral/package/protocol/regression evidence against final content. Documentation replacement and strict documentation build remain Documenter dependencies (AC-026/AC-027). Prior step receipts support reconstruction but cannot substitute for current independent assessment. Prompt client composition/cap compliance remains instruction-level behavior, not executed model output.

**Full Developer Completion and Handoff**

All 17 approved DEV steps are DONE with current-cycle provenance, unchanged locked tony style, AFTER_IMPLEMENTATION and Current Increment NONE. Relevant Developer self-checks passed; no implementation deviation, owned obligation, recovery frame or user blocker remains. Missing formal tests are the explicitly assigned Tester outcome, not a claimed passing suite. The plan is COMPLETE and the workflow proceeds to TESTING for full independent assessment. Suggested Conventional Commit: `build: align progression smoke, CI and MCPB distribution`.

Tester must use the same checkout, reload STATE/context/scope/architecture/development and all relevant retained receipts, and assess HEAD plus the six implementation-content hashes above. Test meaningful positive/negative/bounded contracts across the cycle, rerun applicable static/package/STDIO/HTTP/stage checks, and preserve all input evidence. Keep mock-only model/paid boundaries and do not activate, regenerate, deploy or publish. Use an independent Tester chat separate from this implementation conversation; Developer stops after this handoff.

## Plan Notes

- Approval: user approved the revised 17-step plan and persisted tony style, explicitly directed DEV-001, and subsequently authorized DEV-002, DEV-003, DEV-004, DEV-005, DEV-023, DEV-012, DEV-013, DEV-014, DEV-015, DEV-016, DEV-017, DEV-018, DEV-019, DEV-020, DEV-021 and DEV-022. Style is locked for this cycle; STEPWISE pauses remain in effect.
- Entry: STANDARD/BROWNFIELD, DEVELOPING from Architect; no recovery frames, baseline-reconciliation entries or outstanding obligations. Initial workflow check passed. DEV-001 through DEV-005, DEV-023, DEV-012, DEV-013, DEV-014, DEV-015, DEV-016, DEV-017, DEV-018, DEV-019, DEV-020, DEV-021 and DEV-022 are DONE with persisted implementation feedback; full Developer completion is established for independent Tester handoff.
- Sufficiency: scope/design establish LP meanings, attribution, eligibility, package/profile revisions, normalization/partition algorithm, five query schemas, selectors/facets, bounds/cursors/completeness/errors, rights/resources, prompt workflows, removal and operational boundaries. Existing package/catalog/GraphStore/standard selection/resource/prompt/CLI machinery supports the chosen boundaries. Helper/module factoring remains reversible Developer work.
- STEPWISE: explicit approval covers this plan and user style tony. First approval locks that style. Execute exactly one dependency-ready step, record its outcome/self-check, then persist a continuation blocker and wait. Verification remains AFTER_IMPLEMENTATION, independent of these pauses.
- Preflight: all 23 required files are present for each of six source mappings (138 files, 933,392,640 bytes total), with no selected source symlinks. Copy-time exact hashes and edge reconciliation remain DEV-001 work; this preflight is not copy/acceptance evidence. The local backend Python environment exists.
- Plan revision: user requested replacing the legacy data/input_artifacts sets and build specifications. DEV-023 runs after DEV-005 and before DEV-012, preserving the architecture-prescribed raw-copy location and accepted-package boundaries. The revised 17-step plan was explicitly approved before DEV-001 began.
- Preserve source files and old sealed package/profile identities. Raw preparation copies stay outside runtime/distribution roots. Required runtime evidence is retained in accepted packages. DEV-017 activation has resolved the intermediate schema-migration bootstrap limitation; retired old packages/configs remain byte-exact outside active discovery. Do not deploy partial work or introduce legacy decoders/aliases.
- Developer owns production implementation and executable integration/CI commands, not formal test suites or user documentation. Use local temporary/ad hoc implementation sanity checks; Tester creates meaningful offline formal cases and owns AC-023 through AC-025 evidence. Architecture requests for synthetic cases are exercised as implementation feedback here and independently formalized by Tester. AC-020 is established by Architect; AC-026/AC-027 remain Documenter-owned, supported by these persisted contracts/receipts/actual evidence.
- Identifier gaps are retained: the ID tool reserved numbers referenced in the draft before those headings were written. Preserve existing step identities; dependency order is the heading order, not an assumption of contiguous numbering.
- No live LLM/paid-service calls, producer/checker regeneration, model sampling, deployed endpoint changes or publication. Existing LC/comparison generated-origin evidence stays intact.
- Resume / full assessment: All approved steps (DEV-001–DEV-005, DEV-023 and DEV-012–DEV-022) are DONE. Plan COMPLETE, locked tony, STEPWISE, AFTER_IMPLEMENTATION, Current Increment NONE. Workflow advances to TESTING, with no Developer continuation blocker, recovery or obligations. Final public surface is 17 tools/nine prompts/one fixed resource/14 templates; prompt version 1.3.0, package/MCPB version 0.3.1. Assessed HEAD `3a11ded38a3ad666487207e79c14f31012ec6fa7` plus six DEV-022 changed-content identities and local receipts establish the handoff input. All six accepted rebuilt runtimes remain active; all 3,129 entry protected files are byte-exact. The final retained bundle/archive are under dev022; initial build evidence is separate. Actual pytest exit 5 reflects absent formal cases and is not acceptance; Tester owns those cases and full verification. Documenter owns remaining user-reference cleanup and strict docs checks. Do not rerun activation, regenerate original evidence, call live LLM/paid APIs, deploy or publish. Use an independent Tester session on this checkout; Developer must not continue implementation concurrently.
- Full handoff requires all steps DONE, locked style, satisfactory self-checks, resolved owned blockers/obligations and workflow check. Save current identities and actual evidence for a separate independent Tester chat. Do not fabricate tests or claim formal acceptance based on Developer checks.

### Recovery correction — DEV-014, 2026-10-02

Entry HEAD `9ff00c5c381bf349645655ae7f04057fa649a44c`; clean tree. Active frame 1 is IMPLEMENTATION from TESTING, owner DEVELOPING, ResumeAt TESTING, RerunThrough NONE. Exact reason: `Traversal silently omits a later individually oversized edge instead of raising progression_result_too_large (AC-009).` Read Tester report and Suspended Assignment 1; preserve its FULL/NONE assignment and scenario allocations.

Reopened DEV-014 IN_PROGRESS for the unchanged approved standalone-entry error contract. Reopened DEV-022 PENDING because its retained archive/stage contains the defective traversal source; refresh to a new distinct retained path and rerun relevant distribution/transport checks after the STEPWISE continuation. Preserve both old distributions and receipts. No material intent or dependency change, no duplicate approval required. Unaffected steps remain DONE. Current cadence AFTER_IMPLEMENTATION, Current Increment NONE, locked tony unchanged. This is Developer correction work, not independent Tester acceptance.

**DEV-014 corrective outcome and actual Developer checks**

Added `_require_edge_size` at the later-entry overflow boundary before whole-entry rollback. It uses the existing shared traversal encoder with exact origin, both endpoint summaries, original projected relationship, route metadata and finite counters/frontier. It excludes earlier unrelated rows and uses the actual minimal envelope rather than conservative reservation. An individually unreturnable edge raises the existing `progression_result_too_large` with resource recovery; a fitting edge that overflows only the accumulated result still rolls back with its speculative endpoint and returns explicit byte truncation. First-entry handling, public models/schema, original orientations, rights, metadata and all search/work/queue ceilings remain unchanged. No base-model/service import dependency was added.

Commands ran 2026-10-02 from repository root; Python commands used `/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync` (effective Python cwd backend). Environment explicitly set `UV_OFFLINE=1`, `PYTHONDONTWRITEBYTECODE=1` and `PATHS_PROJECT_DIR=/Users/tzz/Projects/private/idi/KGForEdGlobalMCP`. Exact argv, environments, stdout/stderr and exits are in commands.json and commands-before.json; scripts and logs are retained under `data/source_artifacts/learning_progressions/recovery-dev014/checks/`.

- Before correction: `pytest -q -p no:cacheprovider tests/kgfegmcp/test_progression_traversal.py`, exit 1, one PASS/one FAIL in 12.14s, reproduced later omission with returned=1/examined=2/byte_limit/scopeComplete=false. This deliberate diagnostic failure is superseded only by the changed-content run below.
- After correction: same exact pytest command, exit 0, **2 passed in 5.94s**. Existing Tester-owned file was run unchanged as Developer feedback. Pytest emits the pre-existing pytest-asyncio default-loop-scope deprecation warning; no config/test weakening.
- `python /Users/tzz/Projects/private/idi/KGForEdGlobalMCP/data/source_artifacts/learning_progressions/recovery-dev014/checks/feedback.py`, exit 0. Real accepted local bootstrap, all six DEV-023 rebuilt/DEV-017 active runtimes, no reactivation. Socket connect/connect_ex forbidden. Twelve package/direction combinations each exercised normal deterministic repeat, individually oversized first and later projected edges (24 expected typed errors with resource hints), and two individually fitting 600,000-byte UTF-8 attribution projections exceeding the combined ceiling (12 expected byte-truncated responses). Verified returned/examined counts 1/2, pending frontier, incomplete flags, exact retained first edge, whole-edge/endpoint rollback, final encoded size <=1 MiB and deterministic repeats. Restoring the temporary projection patch reproduces the original normal result. Projections are synthetic feedback only and do not mutate or establish acceptance of giant package records.
- Target module `src/kgfegmcp/services/lp_traversal.py`: `black --check`, `isort --check-only`, `ruff check --no-cache --select E,F,C90`, `mypy --cache-dir /tmp/kgfegmcp-recovery-dev014-mypy`, `pylint` and `interrogate --generate-badge /tmp/kgfegmcp-recovery-dev014-badge`, all exit 0. Mypy no issues; pylint 10.00/10; interrogate 100%. `node .standards/bin/check.mjs` and `git diff --check` exit 0.
- Final read-only exact hash comparison: **4,506 protected files unchanged** under data/config/dist and Tester report/test plus scope/design/context. This includes active/retired sealed packages, original/raw/prepared/rebuilt inputs, versioned configurations, prior receipts and both prior DEV-022 stages/archives. Inventory omits environment/bytecode cache directories `.venv` and `__pycache__`; those are not source evidence. The only new data files are this separate recovery receipt directory. No external-source read, source evidence regeneration, activation, dependency sync, model/paid-service call, publication or deployment occurred.

Assessed changed source: `backend/src/kgfegmcp/services/lp_traversal.py`: `sha256:b6a7982dae8a76b420bd33c2af0e7499d28b88f82039ff80c9a43970070ac577`. Entry source identity was `sha256:5d6a100fb58efc900fdf948ef675c3cb9874ebc096baec15af5b683bedcfbf72`; assessed HEAD remains `9ff00c5c381bf349645655ae7f04057fa649a44c` plus this dirty source content and Developer coordination records. No commit created.

Receipt identities (all relative to the separate recovery checks directory):

- `protected-inputs.json`: `sha256:d949e05047df9e94e8af224568c4b34f91283456542a52b3f9aed9993b602980`.
- `preservation.json`: `sha256:b3888f204d8299ed1d7ae211e4cde7b87349a88a26d5d140bf4d5f6ed61f3304`.
- `commands-before.json`: `sha256:f34ad8fb472ae48e08396ced0e332d27eb8e4b26c80a18a3676b2a5e4ddcaacc`.
- `commands.json`: `sha256:e6bc78affbccda981e8be7598319a3cc1cc1e894545faef77cb2dfd15b04287f`.
- `feedback.py`: `sha256:81908b49affa2aec58fa40984c88528cbe5f575dc4a80301dafad648a769556d`.
- `feedback.log`: `sha256:257a163da42e6afc8b261968a492281b4310dc53bf8d48fd8b150580a75004a6`.
- `run_checks.py`: `sha256:6dd4a25d4369f20fc8a0be46592cccdad4c95b420341705539521433c43b60f5`.
- `pytest-before.log`: `sha256:bb11f75d9785be3bc5a856807c9d62d9093f2824651b2c00ce0511870a7a7694`.
- `pytest-after.log`: `sha256:ab317c10fc7bc4350938075bd6a1b9cdb84e8b63e418f5faa6a2a81ce799246d`.
- `evidence-index.json`: `sha256:84f9e0cb293e3a78ab4a0302018f2248742a3821231bdcb44e8f9032ffcc068f`.

**Limits, current assignment and STEPWISE continuation**

DEV-014 correction is DONE; these are ad hoc Developer checks, not independent Tester acceptance and not closure of the Tester-owned finding/report. No pedagogical/semantic certification or executed model composition is claimed. Historical DEV-014/DEV-022 completion evidence and previous full handoff above remain historical; this recovery section supersedes their current readiness claims. The full Developer gate does not pass yet: reopened DEV-022 is PENDING, because old retained distribution source still has the defect. Repository traversal checks pass, while refreshed transport/archive/stage evidence is not yet run. Prior static/domain evidence outside this small correction supports reconstruction only.

STEPWISE stops here with plan IN_PROGRESS, locked tony, AFTER_IMPLEMENTATION, Current Increment NONE, workflow DEVELOPING. Active recovery frame 1 and FAILURE handoff are preserved; no pop/RESUME or formal Tester handoff yet. Next authorized step after user continuation is DEV-022: build a new distinctly named recovery archive and stage preserving both dev022 archives/stages, rerun applicable offline repository/staged transport checks, verify distribution source/data closure and unchanged protected bytes, then record identities and apply the full Developer gate. No production build recipe change is currently required. Return to TESTING with RESUME and pop the frame only after that gate passes; restore Tester's Suspended Assignment 1 (FULL/NONE), reconcile changed implementation/distribution inputs and rerun affected byte boundaries plus remaining full verification. Independent Tester must allocate missing formal coverage and assess all outstanding obligations itself. Do not edit its tests/report or certify its acceptance. Documenter dependencies AC-026/AC-027 persist.

Suggested Conventional Commit: `fix(progressions): reject individually oversized later traversal edges`.

### Recovery distribution refresh — DEV-022, 2026-10-02

User authorized the next STEPWISE step. Entry HEAD `168a2a8970b976664dad8cfa32bb3751c01c52d4`, clean tree; committed DEV-014 traversal hash `sha256:d5b079569f638eb1be011d987b00101c23b775654bc7f9c8d393eed36135aeb9` reconciles the preceding correction evidence after comment-only wrapping before commit (earlier tested hash `sha256:b6a7982dae8a76b420bd33c2af0e7499d28b88f82039ff80c9a43970070ac577`). DEV-022 IN_PROGRESS; unchanged approved scope/style/cadence. Active frame 1 and Tester FULL/NONE suspended assignment remain authoritative. Clear only its DEV-022 continuation blocker. Build new `data/source_artifacts/learning_progressions/recovery-dev022/kgfegmcp-0.3.1-recovery.mcpb` and `recovery-dev022/bundle`, preserving all old distributions and evidence. Relevant recipe/CI/schema/domain sources are unchanged since their accepted Developer checks; no production source change anticipated. New archive/stage and transport feedback must bind the corrected source before return to Tester.

**DEV-022 refreshed outcome — actual Developer feedback**

PASS. Existing production recipe was reused unchanged, with a fresh recovery output root; no source/configuration/CI changes made by Developer during this step. Retained stage is `data/source_artifacts/learning_progressions/recovery-dev022/bundle`; current recovery archive is `data/source_artifacts/learning_progressions/recovery-dev022/kgfegmcp-0.3.1-recovery.mcpb`. These supersede earlier retained builds for current assessment, while both earlier stages/archives and receipts remain exact historical evidence. Package/MCPB version stays 0.3.1, public prompt version 1.3.0, profile and prompt configuration versions unchanged.

Actual command execution on 2026-10-02 used repository root `/Users/tzz/Projects/private/idi/KGForEdGlobalMCP`. Python tools used `/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync` (Python cwd backend), explicitly setting UV_OFFLINE=1, PYTHONDONTWRITEBYTECODE=1 and PATHS_PROJECT_DIR to the repository. `checks/run_command.py` captures exact argv/cwd/environments/exits/stdout/stderr for each command; full child-server paths, port and termination are in http-command.json. Actual commands, all final exit 0:

```sh
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync kgfegmcp-build-mcpb --output /Users/tzz/Projects/private/idi/KGForEdGlobalMCP/data/source_artifacts/learning_progressions/recovery-dev022/kgfegmcp-0.3.1-recovery.mcpb --stage-output /Users/tzz/Projects/private/idi/KGForEdGlobalMCP/data/source_artifacts/learning_progressions/recovery-dev022/bundle
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync kgfegmcp-stdio-smoke
python3 data/source_artifacts/learning_progressions/recovery-dev022/checks/http.py
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync kgfegmcp-stdio-smoke --bundle-root /Users/tzz/Projects/private/idi/KGForEdGlobalMCP/data/source_artifacts/learning_progressions/recovery-dev022/bundle
/Users/tzz/Projects/private/idi/KGForEdGlobalMCP/data/source_artifacts/learning_progressions/recovery-dev022/bundle/.venv/bin/python /Users/tzz/Projects/private/idi/KGForEdGlobalMCP/data/source_artifacts/learning_progressions/recovery-dev022/checks/stage_feedback.py
python3 data/source_artifacts/learning_progressions/recovery-dev022/checks/final_checks.py
python3 data/source_artifacts/learning_progressions/recovery-dev022/checks/static.py
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync pytest -q -p no:cacheprovider tests/kgfegmcp/test_progression_traversal.py
node .standards/bin/check.mjs
git diff --check
```

- Official installed MCPB validate/pack plus the existing builder verification passed. Archive **650 files, 82,154,373 bytes**, SHA-256 `bf065f7247646c187988a92014cfad423c6842ac53e8615aae8a2932bbe10517`. Independent final_checks.py verifies exact recipe closure and every archive member byte against both current source and retained stage, including after startup/byte feedback. All six active immutable packages, original LP provenance maps and all 64 declared partitions per framework are included. Raw/prepared/retired/input_artifacts/cache/.egg-info trees are excluded from the archive. Stage startup installed 74 already-cached locked runtime dependencies offline into the new stage's own .venv; environment outputs are outside archive closure.
- Repository STDIO, loopback HTTP and fresh-stage STDIO each passed and accepted all six current packages with zero exclusions. Each reports 17 tools, nine prompts, one fixed resource, 14 templates and 15 representative resource reads. Inventories, all 17 input/output schema fingerprints, five successful LP query identities, expected missing-edge error and resource evidence agree exactly across all three. Transport checks use the existing shared smoke implementation and ordinary factory/bootstrap, without any live LLM/client composition.
- HTTP ran only at `http://127.0.0.1:50274/mcp`; actual client exited 0. Harness sent SIGTERM to its own process group, wrapper exit 143 as expected for that signal. Server log confirms application shutdown complete and finished server process; no SIGKILL fallback, remote endpoint or running deployed service. STDIO clients closed normally.
- Stage feedback explicitly verifies the imported traversal module is under the **new staged** src tree, exact module bytes match current repository source, and all application/config/package roots select the stage. Reuses the unchanged Developer feedback.py from recovery-dev014 with socket connections forbidden: six packages/twelve package-direction combinations, 24 required individually oversized first/later errors, twelve combination-only truncation outcomes with 600,000-byte UTF-8 fields, deterministic repeats, exact edge/endpoint rollback, counters/frontier/completeness and final <=1 MiB checks. No sealed evidence mutated by these synthetic projection patches.
- Unchanged Tester regressions rerun as Developer feedback against the actual committed source: **2 passed in 7.82s**, exit 0. Prior warning about pytest-asyncio loop scope remains; no formal coverage or report edits by Developer.
- Current lp_traversal.py and smoke_progressions.py pass Black --check, isort --check-only, Ruff E/F/C90, mypy (no issues in two files), pylint 10.00/10 and interrogate 100%. Exact arguments/outputs in static.json; cache/badge paths outside project sources. Workflow and diff checks pass. Other recipe/CI/domain source, configuration, data and schema bytes remain unchanged; prior applicable Developer checks remain reconstruction evidence, without adopting them as formal Tester acceptance. Separate six-package CLI revalidation and broader formal scenarios remain Tester's full assignment.
- Final preservation comparison: **4,647 protected files byte-identical**, covering data/config/dist, backend/src, packaging, maintained build inputs, all original/raw/prepared/rebuilt/retired evidence, prior receipts/archives/stages, Tester test/report, context/scope/design, pyproject/lock and CI. Protected inventory excludes .venv and __pycache__ environment caches. Only new local data is the fresh recovery-dev022 output root.

**Input reconciliation and diagnostic limits**

Two early final-check attempts failed due to overly narrow ad hoc expectations; neither was a runtime/test failure. Preserved initial/second scripts, commands and stdout/stderr record them. Archive comparison found current smoke_progressions.py differs from the prior archive by one already committed blank line; AST equality verifies no semantic difference. Prior tested traversal hash b6a7982d… differs from committed d5b07956… only in rewrapping three comment lines. Reconstructing those comment bytes yields the exact prior full hash and identical AST; source-reconciliation.json records the proof. Current staged byte tests, current repository regression and static checks bind the actual committed source. The HTTP SIGTERM wrapper exit is 143, matching historical harness behavior, with graceful server shutdown confirmed by logs. Final checks explicitly accept these established facts and retain every prior diagnostic attempt; no runtime contract was weakened.

**Assessed content and persistent receipts**

Assessed implementation HEAD `168a2a8970b976664dad8cfa32bb3751c01c52d4`, clean implementation at entry. No production source change or Git commit made this step; only Developer plan/state changes are tracked. Current exact source identities:

- `backend/src/kgfegmcp/services/lp_traversal.py`: `sha256:d5b079569f638eb1be011d987b00101c23b775654bc7f9c8d393eed36135aeb9`.
- `backend/src/kgfegmcp/cli/smoke_progressions.py`: `sha256:7bafeac9828b9f6f9ff2acd08b9f76d5af7f19589404e22b4f614c4dc0b4ebbc`.
- `backend/src/kgfegmcp/cli/build_mcpb.py`: `sha256:3676404a4a96f5c19c7642f96470128033c634d2c16d9b9417a130c5bc27a97b`.
- `backend/src/kgfegmcp/cli/stdio_smoke.py`: `sha256:60aa908529d9ca7263b81ff9e47561f70275099d8a4e2b75634746435add1227`.
- `.github/workflows/tests.yml`: `sha256:c42265cbf123f9f840a78daf9e382e0a463fc95175652940103ee405d048a9b8`.
- `packaging/mcpb/manifest.json`: `sha256:76d543a754a1c66f78f7c49dbdfeba2e1480bdca2cc168f2e76deb1de5cad825`.

Receipts below are relative to `data/source_artifacts/learning_progressions/recovery-dev022/checks/`; evidence-index.json binds all local scripts/logs/attempts, and final-checks.json contains the full 650-member source/archive/stage hash map.

- `protected-inputs.json`: `sha256:81833db0d269e113c06d730f81779f6f129b37cf5161415ed183ddfd047f5fd7`.
- `source-reconciliation.json`: `sha256:f402046150492601e3bf3e4e115d17c832eab223d8d559632dddfea57c5ba3d6`.
- `build-command.json`: `sha256:11d81385ef4b77f4b76f23734061191ce43a958c0b1ada4c08859ba7c8a5c80e`.
- `stdio-command.json`: `sha256:04fa5d6c32f1523d8fa5c6203d726a235eef1ec8efa636a75dc855c688b510fe`.
- `http-command.json`: `sha256:9ce4f1eb70a280185078c99cc10ff960f36c219a3bd23a290857cd14119af5ec`.
- `stage-stdio-command.json`: `sha256:ff7f28adfbb94f3a7bf2e455e3d9b392375f514f1875c680b24583912a406fcc`.
- `stage-source-identity.json`: `sha256:7964bcf8b67a9ceaf3729e3f6439ae15ea3d85c0c31f95ff30b81b0efc62fd1f`.
- `stage-feedback-command.json`: `sha256:9dd7834647e4f6a6f139e0042697946baa91f569fb3e9e7196363b0f49a090f6`.
- `final-checks.json`: `sha256:10925f28e4a27d532ba3fb22c9e00662bad493e46641d11e9f7c00ef6c96ac3a`.
- `static.json`: `sha256:b4d9e83bc0c44179704c209169340bbeb243f9b13ce2cf249823e27bdb2d85ae`.
- `pytest-command.json`: `sha256:ff43b73c0fdf6b3efad85ac30cc301b6e88ff0c986412b5df9be93301c47bc07`.
- `evidence-index.json`: `sha256:37907aaf331d5cc526999744a463d183033a80e9a29c0dfb8a08b011930e77dd`.

**Completion gate and recovery resumption**

DEV-014 correction and DEV-022 refreshed distribution are DONE; all 17 approved steps are DONE, plan COMPLETE, locked tony unchanged, STEPWISE/AFTER_IMPLEMENTATION/Current Increment NONE. No material deviation, blocking user question or Developer-owned obligation remains. Current relevant implementation feedback passes, and full Developer gate is restored. There is no affected intermediate downstream role before ResumeAt TESTING; pop frame 1 and persist DEVELOPING -> TESTING with RESUME, FailureType NONE, recovery inactive, BlockedOn NONE. Do not take FORWARD/CHECKPOINT or add another Developer continuation blocker.

Restore Tester's Suspended Assignment 1 (FULL/NONE) associated with reason `Traversal silently omits a later individually oversized edge instead of raising progression_result_too_large (AC-009).` Tester must independently reconcile the committed comment-only/source differences, corrected traversal and new current archive/stage identities; select REVERIFY under its own rules and rerun its preserved regression and related byte boundaries, then finish all remaining required formal package/service/rights/prompt/regression/static/STDIO/HTTP/stage evidence. Current target distribution is recovery-dev022/bundle and kgfegmcp-0.3.1-recovery.mcpb, not either old retained build. Tester owns any finding disposition and its report/tests; their prior failure record was preserved unchanged. No prior pass or Developer feedback supplies independent acceptance. Existing separate Tester chat may resume only if it contains no Developer authoring history; otherwise use a fresh independent chat on this same checkout. No simultaneous implementation/assessment work.

Limits persist: no exhaustive acceptance or semantic/pedagogical certification, remote Actions execution, Claude Desktop installation/use, live model/client composition, deployment or publication was performed. No activation or producer/checker/source regeneration occurred. AC-026/AC-027 and obsolete user-facing documentation remain Documenter-owned phase dependencies. Prior no-test exit-5 evidence is historical; two retained regression cases now exist and pass as Developer feedback, while comprehensive independent verification remains unfinished. Suggested Conventional Commit: `docs(development): record MCPB recovery verification`.

### Final-review recovery — DEV-022, 2026-10-03

Entry HEAD `cbc3baf316347428140b61c6fb7e39b4a51e1139`, clean tree. Active frame 1 from REVIEWING_FINAL, Owner DEVELOPING, FailureType IMPLEMENTATION, ResumeAt REVIEWING_FINAL, RerunThrough NONE. Exact reason: `Current retained MCPB ships removed progression-tool instructions; refresh final distribution (AC-022/AC-026).` Reviewer final-deliverable .standards/docs/reviews/integrate-actual-learning-progressions-20261001T162834Z-142f2df1/final-deliverable.md#F-001 owns the current failure; .standards/docs/reviews/integrate-actual-learning-progressions-20261001T162834Z-142f2df1/final-deliverable.md#F-002 remains Documenter-owned, OPEN and unmodified. Read current Reviewer/Tester/Documenter records and current inputs; Tester COMPLETE FULL/NONE with 78 cases and unchanged runtime evidence is prior independent evidence, not a new Developer assessment.

Reopened DEV-022 only, IN_PROGRESS, to rebuild a separately named local archive/stage from the already corrected backend README. Unchanged approved intent, dependencies, style tony locked, STEPWISE, AFTER_IMPLEMENTATION, Current Increment NONE; no duplicate plan approval needed. No production code or user documentation edit requested or required. New paths: `data/source_artifacts/learning_progressions/recovery-final-dev022/bundle` and sibling `kgfegmcp-0.3.1-final-recovery.mcpb`; preserve every old bundle/stage/input/receipt.

Corrective self-checks: existing MCPB builder validate/pack/verify, new staged STDIO, full source/stage/archive byte closure including corrected README, exact inventory/schema/query/resource agreement with unchanged formal transport evidence, active data and source preservation. Application code/data/config/tests/dependencies are unchanged; broader suite/static/package/HTTP reruns are not required as Developer feedback for a README-only packaged change. Independent Tester must reconcile current distribution evidence under its own gate.

Planned resumption after the Developer gate: earliest affected downstream role TESTING; RerunThrough DOCUMENTING. Tester re-establishes applicable independent distribution/stage evidence and reconciles retained FULL/NONE verification, followed by IMPLEMENTATION review on the standard route, then Documenter reconciles the new candidate and corrects Reviewer .standards/docs/reviews/integrate-actual-learning-progressions-20261001T162834Z-142f2df1/final-deliverable.md#F-002 within its ownership. At DOCUMENTING boundary pop this frame and RESUME REVIEWING_FINAL. Preserve both Reviewer findings for its own reassessment; do not resolve them, bypass independent gates or invent Outstanding Obligations. Current final deliverable is not ready for sign-off while .standards/docs/reviews/integrate-actual-learning-progressions-20261001T162834Z-142f2df1/final-deliverable.md#F-002 remains.

**Actual corrective implementation and Developer checks**

DEV-022 DONE. The established builder copied the corrected Documenter-authored `backend/README.md` into a fresh retained stage and official locally packed archive; no production source, build recipe, documentation, tests or graph/config inputs edited. Current candidate: `data/source_artifacts/learning_progressions/recovery-final-dev022/kgfegmcp-0.3.1-final-recovery.mcpb` and sibling `bundle/`. This supersedes recovery-dev022 only as the current candidate; every earlier archive/stage/receipt remains unchanged. Package/MCPB 0.3.1, prompt 1.3.0 and all versioned profile/prompt configurations unchanged. No commit created.

Actual commands ran on 2026-10-03, repository cwd `/Users/tzz/Projects/private/idi/KGForEdGlobalMCP`, setting UV_OFFLINE=1, PYTHONDONTWRITEBYTECODE=1 and PATHS_PROJECT_DIR explicitly. Locked/no-sync uv Python cwd is backend. The separate checks/run_command.py captures exact argv, cwd, environment, exits, duration and stdout/stderr for each command:

```sh
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync kgfegmcp-build-mcpb --output /Users/tzz/Projects/private/idi/KGForEdGlobalMCP/data/source_artifacts/learning_progressions/recovery-final-dev022/kgfegmcp-0.3.1-final-recovery.mcpb --stage-output /Users/tzz/Projects/private/idi/KGForEdGlobalMCP/data/source_artifacts/learning_progressions/recovery-final-dev022/bundle
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync kgfegmcp-stdio-smoke --bundle-root /Users/tzz/Projects/private/idi/KGForEdGlobalMCP/data/source_artifacts/learning_progressions/recovery-final-dev022/bundle
python3 data/source_artifacts/learning_progressions/recovery-final-dev022/checks/final_checks.py
node .standards/bin/check.mjs
git diff --check
```

- Build exit 0 (10.82s), official MCPB validate/pack and existing builder archive verification passed. New archive **650 unique files, 82,154,417 bytes**, SHA256 `adb10a43258a1115bfd74732c7d85af367f75e082a50c73f91b75e67a6cd5e04`.
- Staged STDIO exit 0 (11.99s); new stage-owned locked environment installed 74 cached runtime dependencies offline. Factory bootstrap accepts all six active packages, zero exclusions. Surface remains 17 tools/nine prompts/one fixed resource/14 templates with 15 representative resource reads, five successful bounded progression operations and expected missing-edge error. Inventory, all tool schema identities, exact progression results and resource evidence equal the unchanged independent Tester stage receipt, whose stdout hash was independently checked before comparison. These fresh executions are Developer feedback, not new Tester acceptance.
- final_checks.py exit 0 (6.59s). Independently verifies the closed current recipe, each archive member against current source and post-startup stage bytes, duplicate-member absence and no raw/preparation/retired/cache/environment inclusion. All six complete accepted packages, original LP provenance maps and 64 declared shards per framework are present. Compared to prior recovery-dev022 candidate, **README.md is the only changed member; all 649 runtime/configuration/data/contract members are identical**.
- Shipped README SHA256 `197db6b11bdc6ad24988dd525dc7d8abca84c4632db0e9c249b9339076723b56` equals current backend README exactly. Checked updated 17/9/14/1 counts, stored-query/curriculum-review names and absence of the removed tool/hypothesis call and old bundle/inventory strings. Source, archive and stage now agree on those instructions.
- Preservation: **5,625 entry files unchanged**, including all current/retired/sealed packages and configurations, original/raw/prepared/rebuilt inputs, old distributions/stages, prior Developer/Tester receipts, all production/test/documentation sources, contract/context and Reviewer/Documenter/Tester records/supporting evidence. Inventory excludes environment/tool caches (.venv, __pycache__, .mypy_cache, .pytest_cache, .ruff_cache). Only new data lives under the separate recovery-final-dev022 root; source evidence, versioned inputs and prior artifacts were not overwritten.
- Reconciled all 823 relocated Tester input hashes: 819 unchanged. The four differences are STATE and Developer plan coordination/evidence plus the already updated backend and packaging READMEs. Thus production code, tests/fixtures, package/configuration/dependency/CI inputs remain byte-identical to independent full-verification content. Existing 78-case/static/package/HTTP/repository STDIO outcomes are prior independent evidence; no redundant Developer rerun is claimed for unchanged executable behavior. Tester decides valid reuse and current distribution acceptance.
- Workflow check initially found two Developer-owned missing record qualifiers for Reviewer finding mentions. Added explicit final-review record references in this section; no owner finding altered. Final workflow/diff checks pass and are repeated after handoff. No runtime/build/closure check failed.

Assessed HEAD `cbc3baf316347428140b61c6fb7e39b4a51e1139` plus Developer record/state writes and new ignored local archive/stage/receipts. Changed delivered bytes are only README; full member identities and protected-input map are persisted. Receipt hashes below are relative to `data/source_artifacts/learning_progressions/recovery-final-dev022/checks/`:

- `protected-inputs.json`: `sha256:32a2960163e3e3d41a0c1ba64571a7f49dde3d8394708e2d95f73ad52a7b746c`.
- `build-command.json`: `sha256:8e5c40eba453d34722f9104f882335ab49777c7242222183838a05fc3b184a1c`.
- `stage-stdio-command.json`: `sha256:7a84ca6777157cd769580b7bfccb5fe0fc3a8c7f9b03f447f0cfe3c6b3099e30`.
- `final-checks-command.json`: `sha256:3f72f11ddd0697a629263e88c99a81000843356a9c9da616b576206d467d22fc`.
- `final-checks.json`: `sha256:6da10eb559a4898e1bbb6e30763472ba4a4676c0d33bc58e4531d0b23989d0f6`.
- `final_checks.py`: `sha256:a9b3ad68afa34ce29c2fe5906804a77ca5803d3702ca4a1b97695ef69aebe68d`.
- `run_command.py`: `sha256:d6e39d99bce3a5320a0710541c60789f63c77ccc9da32262e95818bcc5d89af0`.
- `evidence-index.json`: `sha256:737d66d9112371bbb576c425af8e2e606d2835ce328d85925a19d3cf4ac09859`.

**Developer gate, affected downstream work and resumption**

All 17 approved DEV steps are DONE; plan COMPLETE, locked tony unchanged, STEPWISE, AFTER_IMPLEMENTATION, Current Increment NONE. The approved distribution correction and current Developer checks are complete; no Developer-owned obligation, material deviation or user blocker remains. This is readiness for independent re-establishment of affected evidence, not finding closure or final acceptance. Historical current-candidate/completion claims above are superseded by this newest recovery section.

Active frame 1 stays on the stack. Set RerunThrough DOCUMENTING and transition DEVELOPING -> TESTING by FORWARD. Earliest affected evidence is independent archive/stage acceptance; follow the standard route TESTING -> REVIEWING_IMPLEMENTATION -> DOCUMENTING, then pop at DOCUMENTING and RESUME REVIEWING_FINAL. The implementation-review gate may reconcile unchanged prior behavioral evidence with current distribution claims; it is not bypassed. Documenter owns correction of .standards/docs/reviews/integrate-actual-learning-progressions-20261001T162834Z-142f2df1/final-deliverable.md#F-002 and reconciliation of its completion record/count/example checker against final saved files and the new bundle. A changed backend README or other build input during that work invalidates this candidate's equality and must be routed appropriately; inspect final identities before relying on it. Reviewer alone reassesses and closes .standards/docs/reviews/integrate-actual-learning-progressions-20261001T162834Z-142f2df1/final-deliverable.md#F-001/.standards/docs/reviews/integrate-actual-learning-progressions-20261001T162834Z-142f2df1/final-deliverable.md#F-002 in its final-deliverable report. No artificial obligation, nested frame or owner-artifact edit was introduced.

Next Tester assignment: reload current Active Work, context/scope/design, this plan, COMPLETE FULL/NONE verification record and active recovery frame. Independently select REVERIFY, assess the fresh recovery-final-dev022 archive/stage and README byte closure, run applicable staged/assembly checks and justify unchanged behavior/static/package/transport reuse by current identities. This is a full-gate downstream rerun; do not overwrite old receipts or adopt Developer checks as Tester execution. Subsequent implementation review and Documenter correction must preserve the active frame until the DOCUMENTING boundary returns to FINAL_DELIVERABLE review. Use the existing independent Tester chat or a fresh chat separate from Developer authoring on this same checkout; no concurrent role work.

Limits: no remote/deployed endpoint, publication, external source reads, activation, producer/checker/evidence regeneration, live LLM/paid API or Claude Desktop installation/use. No semantic/pedagogical certification, external-link audit or client-model composition. Current documentation gate remains affected by Documenter-owned .standards/docs/reviews/integrate-actual-learning-progressions-20261001T162834Z-142f2df1/final-deliverable.md#F-002; sign-off and synchronization are not authorized. This Developer outcome does not resolve Reviewer finding statuses or another owner's evidence. Suggested Conventional Commit: `docs(development): record final MCPB distribution recovery`.

### Client-access recovery reconciliation — 2026-10-06

Entry HEAD 75fa26fc1e0349112a99b0113c005b69932959a5; clean tree before Developer records. Read protocol, persisted Active Work/frame, Auditor baseline, complete revised scope/design, relevant prior plan definitions/execution/recovery history, locked tony and STEPWISE instructions, current result encoder/query budget/resource/URI/renderer/registration/version/smoke boundaries and prior Tester report. Initial node .standards/bin/check.mjs passed. No conditional protocol chapter applies (STANDARD, no promotion/obligations/pending cadence/control-plane request).

Sufficiency: revised upstream contracts establish the two public tool names/schemas, canonical text encoding, both total-envelope ceilings, native source/whole-return policy before paging, exact URI allowlist/cursor binding/UTF-8 semantics, seven-workflow limits and renderer reuse, immutable identities, version boundaries, 19/9/1/14 inventory and local distribution targets. Existing ordinary services and thin adapters support them; focused helper/module factoring is a reversible Developer detail. No new design/scope/context decision is inferred.

This is a material plan revision: new typed evidence/workflow routes, character-bound whole-entry result selection and generic evidence instructions require explicit user approval. The earlier approval covers prior intent, not this added implementation. Status PROPOSED, User Style tony remains Locked true; collaboration STEPWISE and cadence AFTER_IMPLEMENTATION remain unchanged. Reopened only DEV-012/013/014/015/022. DEV-001..005, DEV-023, DEV-016..021 retain DONE for their still-valid original outcomes; added DEV-024/025 cover the additional evidence/workflow outcomes rather than relabel their old checks as new results. No recovery implementation self-check is asserted yet.

Existing package preparation/activation, accepted provenance resources, native prompt renderers and obsolete-surface removal remain reusable inputs. Historical 0.3.1/1.3.0/17-tool completion and distribution results below do not establish the revised 0.4.0/1.4.0/19-tool contract. Prior Tester report/tests/receipts remain untouched and are independent historical evidence; their owner must reconcile expanded acceptance and behavior. AC-020/032 are Architect-owned design prerequisites; AC-023..025/033..034 independent formal evidence is Tester-owned; AC-026/027/036/037 prose/walkthrough/strict/shipped-content outcomes are Documenter-owned. DEV-022 supports the current AC-037 distribution correspondence without owning those documents.

Recovery Frame 1 remains exactly SCOPING-owned through SYNCHRONIZING. The frame-specific reason is User requests REPLAN of the same Learning Progressions cycle for verified Desktop text/evidence access gaps and a supported local Desktop/public claude.ai connector surface; preserve native prompts/resources and valid requirements. It resumes AWAITING_USER_SIGNOFF. No Developer assignment was interrupted here, so do not fabricate a suspended assignment or choose/pop/reroute that owner's frame. After full current Developer completion, hand off FORWARD to independent TESTING under the preserved route; full Developer/Tester gates must hold before review.

Next action after explicit current-plan approval: set APPROVED with locked tony unchanged, clear only the plan-approval blocker, start DEV-012 and perform exactly that STEPWISE step. Persist actual evidence and then the next-step continuation blocker unless an assignment gate passes. No source copy, partition generation, cutover, formal test edits, user-documentation edit, upstream judgment rewrite, publication, deployment or sign-off has occurred in this reconciliation.

### Recovery approval for DEV-012 — 2026-10-06

User explicitly approved the current seven-assignment material recovery plan and directed DEV-012. Locked tony remains true, STEPWISE/AFTER_IMPLEMENTATION/Current Increment NONE unchanged. Clear only the matching plan-approval blocker; DEV-012 IN_PROGRESS. Preserve the SCOPING-owned recovery frame, all other role records and all later PENDING steps. Current approved assignment ends after DEV-012 checks and evidence; do not start DEV-013 without continuation.

### Client-access recovery for DEV-012 — completed 2026-10-06

Approved assignment completed within unchanged locked tony, STEPWISE, AFTER_IMPLEMENTATION and Current Increment NONE. Entry HEAD 327439a6818ee6a66ff4f2c6ceaa2c1120fb5769; existing dirty files were only the Developer plan/state. The earlier proposed-plan reconciliation records HEAD 75fa26fc1e0349112a99b0113c005b69932959a5; the user committed that proposal before this approved step. No commit is created here.

**Implementation and current outcome**

- Added ordinary kgfegmcp/tool_results.py below MCP: canonical alias-keyed compact JSON with sorted keys, ensure_ascii=False, original array order and nonfinite JSON rejection; shared typed byte/character limits and conservative complete-envelope measurement. Candidate accounting reserves text blocks, structuredContent, isError, metadata slot, JSON escaping and whitespace. The adapter additionally measures the actual SDK CallToolResult fields/content/metadata before return.
- All five LP adapters use the same canonical text as their complete bounded structured result. No retained non-LP tool text was rewritten. Existing query size hooks now enforce <=1,048,576 UTF-8 bytes AND <=100,000 Unicode code points; exact/single-entry overflow raises progression_result_too_large with an exact read_evidence request URI and unchanged native policy guidance. Unexpected-error masking and rights checks remain intact.
- Compatible result metadata reports maxResultCharacters; continuationNotice supplies actual page.nextCursor replay instructions for direct/search and explicit noncontinuation/full-evidence guidance for exact/traversal/paths. Collection absence-as-pedagogical-disconnection disclosure is preserved. Existing tables, requests, identities, judgments, disclosures, excerpt/omission flags and useful structuredContent remain intact. DEV-013..015 still own their operation-specific cursor/admission/frontier reconciliation; their files were not edited.
- The Nigeria diagnostic exact route uses the unchanged framework nigeria-nerdc-mathematics-primary-1-3, snapshot nigeria-nerdc-mathematics-primary-1-3@undated+bc5e769ed26f and relationship 0129f5d5-42fd-52cb-bcf2-ec07c47103e7. Ordinary text alone yields the accepted edge, both standard statements/IDs, stored judgment/warnings/evidence links and exact package/profile/manifest/artifact identities.

**Actual Developer self-checks**

All final commands exited 0 from /Users/tzz/Projects/private/idi/KGForEdGlobalMCP, using the existing locked/offline/no-sync Python environment (uv sets the Python tools' cwd to backend). No dependency install, formal test edit or model/paid/network call occurred. Local command recorder R/run_command.py retains exact argv, cwd, permitted environment settings, UTC start, duration, exit, stdout and stderr. R is data/source_artifacts/learning_progressions/client-recovery-dev012/checks/.

- /Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync python /Users/tzz/Projects/private/idi/KGForEdGlobalMCP/data/source_artifacts/learning_progressions/client-recovery-dev012/checks/feedback.py: 64 named ad hoc checks passed; R/final-feedback.command.json/stdout/stderr and feedback-results.json. Uses actual accepted data and real in-process FastMCP Client/SDK results. Ordinary JSON text equals structuredContent for nonempty exact/direct/search/traversal/path samples; real cursors and replay wording appear in ordinary direct/search text. Original edge object, judgment, snapshot and evidence identities match. Raw successful tool envelopes are retained with content hashes in wire-results.json.
- Actual compact wire sizes (UTF-8 bytes/Unicode code points; diagnostic text is ASCII): exact 73033/73033, direct 77591/77591, search 77593/77593, traversal 83999/83999 and paths 75815/75815. Each has exactly one text block, nonempty relationships/standards, effective character limit and a matching structured object. Shared conservative measurement is at least actual compact wire size. Exact missing-edge and synthetic oversized exact errors are bounded safe domain messages, with exact resource recovery URI and no private path.
- Independent synthetic envelope checks cover Unicode/non-BMP/control/quote/backslash escaping, array/alias/canonical equality, multiple text blocks, metadata/error-flag overhead, exactly 100000 characters and +1 rejection, and a character failure while bytes are below 1 MiB. The character ceiling normally dominates valid UTF-8 output; scratch temporarily relaxes only that constant to isolate exactly 1048576 bytes and +1 rejection, restoring it afterwards. No production limit is changed. Injected actual adapter metadata and extra text are counted and refused. Oversized Unicode projected content is refused.
- /Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync pytest -q -p no:cacheprovider tests/kgfegmcp/test_progression_lookup.py tests/kgfegmcp/test_progression_protocol.py tests/kgfegmcp/test_progression_traversal.py: 13 passed in 24.41 seconds; R/final-pytest.command.json/stdout/stderr. Existing exact test iterates all 8080 accepted LP edges across six curricula, checks source/hash/judgment/facet identity with source reopening forbidden, and now passes under both ceilings. Existing selectors/missing/unavailable/denied, MCP schemas/errors/masking/obsolete refusal/native prompts and first/later oversized traversal regressions pass. The existing pytest-asyncio unset fixture-loop warning is retained; it did not fail checks.
- For each static command the exact prefix is /Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync; the exact module list is src/kgfegmcp/tool_results.py src/kgfegmcp/services/learning_progressions.py src/kgfegmcp/services/lp_models.py src/kgfegmcp/mcp/tools/learning_progressions.py. black --check and isort --check-only passed; ruff check passed; mypy --cache-dir ../data/source_artifacts/learning_progressions/client-recovery-dev012/checks/mypy-cache passed (four files); pylint --persistent=n passed (10.00/10); interrogate --generate-badge ../data/source_artifacts/learning_progressions/client-recovery-dev012/checks/badge passed (100%). R/final-black, final-isort, final-ruff, final-mypy, final-pylint and final-interrogate command/stdout/stderr files preserve all executions. Earlier format/import runs are also retained; no hidden failed final check.
- Protected input verification passes for 1175 entry files in config, accepted packages, maintained preparation inputs, formal tests/fixtures, scope/design/context/protocol and other role records. R/protected-inputs.json holds exact entry hashes; feedback verifies every one unchanged. Required native resources and original judgment/configuration/package data remain untouched. New scratch data is confined to this separate ignored DEV-012 root.

**Limits and next assignment**

These are Developer implementation-level checks, not independent Tester acceptance for AC-028..037. No formal cases/reports or user documentation changed. Public inventory remains 17 tools/nine native prompts/one fixed resource/fourteen templates in this intermediate checkout; read_evidence and get_workflow_instructions are planned DEV-024/025 routes, not registered yet. No STDIO/local HTTP/MCPB refresh, Desktop model composition, public claude.ai acceptance, deployment, publication, activation, source copy or producer/checker regeneration is claimed here. DEV-013 must reconcile the character ceiling in cursor fingerprints and size-driven page replay; DEV-014/015 must re-establish affected frontier/path outcomes before full completion. Existing historical receipts/archives/stages are preserved.

DEV-012 DONE, plan IN_PROGRESS, six recovery assignments still PENDING (DEV-013, DEV-014, DEV-015, DEV-024, DEV-025, DEV-022). The full Developer gate does not pass; do not hand off to Tester or pop/change the SCOPING-owned Frame 1. Persist only the STEPWISE continuation blocker for DEV-013, then stop. Next step requires explicit user continuation; no duplicate plan approval. Suggested commit: feat(progressions): expose canonical bounded tool text.

**Assessed source and persistent receipt identities**

- backend/src/kgfegmcp/tool_results.py: sha256:6a81d1762f0c2c1241202c7630662bd4e5cadce817d224851217ffaac392b6a8
- backend/src/kgfegmcp/services/learning_progressions.py: sha256:e28e7e761b9902b90347b9c8458a718dd2da98d0df2f82f33d03d5c5c7a881ae
- backend/src/kgfegmcp/services/lp_models.py: sha256:516be82f72ce1b3f0574e62e6d677c7444b555c987665fa813487d490c7d2564
- backend/src/kgfegmcp/mcp/tools/learning_progressions.py: sha256:9e19246d5cd0a37656e36e2f277a168bc97a58333886b2c607d0da55ec72f445
- R/protected-inputs.json: sha256:ba254b893ba9637c2267a8da80d1e8283dc73d00d46464c4b236fd03828c7fc6
- R/feedback.py: sha256:d0d429cc71dcbc78075c518f7b82f0cbed6b63b2feb546375ea35bb23d3ffe3d
- R/feedback-results.json: sha256:34f2144101a0d232e8679408b5ffd61f40ab9ac4c87eabf98b56f41006cc4c8a
- R/wire-results.json: sha256:74cf127c5521efabdd86944b27e59db5433ec8612102bbe10a011d3f2b5dc089
- R/final-feedback.command.json: sha256:8f4dad82a1987eb86ba12f747f2cb31451aa021f1a088a0f0aef840cf0d87fac
- R/final-pytest.command.json: sha256:86735530967fff9845b98a6f3503c00e9b1bdd2995f273273344247667665f23
- R/evidence-index.json: sha256:fce19060c2c9da255b26dcda6808eb4bdbfe53bf6102b7bb14ef259edaba1acc

The final workflow check initially interpreted two DEV-012-prefixed Plan Notes headings as duplicate build-step definitions. Renamed only those notes headings to distinguish them from the single canonical step. No implementation/status/ownership was changed by that repair. Runtime/static/test results remain those recorded above; workflow and whitespace checks are rerun after repair.

### Recovery continuation for DEV-013 — 2026-10-06

User explicitly directed continuation with DEV-013. Locked tony, STEPWISE, AFTER_IMPLEMENTATION and Current Increment NONE remain unchanged. DEV-012 and its source changes are staged by the user but not committed at entry HEAD 327439a6818ee6a66ff4f2c6ceaa2c1120fb5769; preserve index and those exact bytes. Clear only the matching DEV-013 continuation blocker, mark DEV-013 IN_PROGRESS and do not start DEV-014. Keep the SCOPING-owned recovery frame and all other owners' artifacts intact.

### Client-access recovery for DEV-013 — implementation assessed 2026-10-06

User authorized only DEV-013. Entry HEAD 327439a6818ee6a66ff4f2c6ceaa2c1120fb5769, with the previous DEV-012 source/records staged by the user. Preserve that index; no commit or index write was performed. STEPWISE, locked tony, AFTER_IMPLEMENTATION and Current Increment NONE remain unchanged. DEV-013 remains IN_PROGRESS because three existing formal checks require Tester-owned correction before a satisfactory step gate. This section supersedes its historical PASS/DONE/next-step claims above. DEV-014 is not authorized or started.

**Implemented outcome**

- services/lp_discovery.py binds the common byte and character ceilings and canonical_full_text_v1 encoding identity into the normalized selection fingerprint. Existing strict cursor shape/checksum/canonical base64url, exact package/profile/manifest identity, route/operation/meaning/filter/limit matching and candidate-position checks remain. Correctly signed old summary/budget cursors are refused with restart guidance.
- services/lp_models.py adds compatible page.nextRequest: the original typed request with only cursor replaced by page.nextCursor, or null on exhaustion. Canonical ordinary text and structuredContent contain the complete replay request, actual cursor, bound limits and truthful stopping/completeness/count metadata. continuationNotice explains replay and that retained byte_limit terminology covers either output ceiling.
- Existing conservative trial/final assembly counts both text and structured tables plus all cursor/request/count metadata through the shared encoder. Aggregate overflow rewinds whole entries and dependent output rows. The new private single-entry check measures the deferred entry with its real resumed cursor/request overhead before returning continuation; an individually unreturnable later entry fails progression_result_too_large with its exact evidence URI instead of creating a no-progress chain. Existing whole-endpoint conjunctions, directional builds, canonical symmetric relates, deterministic stored order, nonmatch advancement, 5000 work/100 edge limits and rights routing are retained.

**Actual Developer feedback**

All commands use repository cwd /Users/tzz/Projects/private/idi/KGForEdGlobalMCP. R = data/source_artifacts/learning_progressions/client-recovery-dev013/checks/. R/run_command.py persists exact argv/cwd/environment/start/duration/exit/stdout/stderr per label. Existing environment only: /Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync; Python tool cwd becomes backend. Network connects/connect_ex are forbidden by scratch feedback. No source generation, package/configuration mutation, model/paid call or formal test edit occurred.

- final-independent-feedback: uv prefix plus python /Users/tzz/Projects/private/idi/KGForEdGlobalMCP/R/feedback.py (replace R with its stated repository-relative root). Exit 0, 303 named checks, 83.912073 seconds. Independent original accepted-record sort and endpoint/facet oracles verify all 8080 LP edges across six snapshots, exactly once and in stored type/ID order. 6084 exhaustive discovery pages, 2581 grade-filter pages and 40 directional/symmetric direct pages = 8705 complete service pages, each within both normal ceilings. Ordinary canonical text alone reconstructs every page and nextRequest; replay changes only cursor, terminates and preserves each whole edge. CBSE complete discovery needs 3193 pages; its grade selection needs 1634. These are finite advancing results, not looping cursors.
- Actual in-process FastMCP Client.call_tool_mcp at pinned Nigeria snapshot nigeria-nerdc-mathematics-primary-1-3@undated+bc5e769ed26f: search returns all 486 original edges over 243 pages, direct support target e399b510-48bb-58ee-abda-61460a5a853b returns all eight incident edges over four pages. Every ordinary text block equals structuredContent; successful complete serialized SDK envelopes remain within 100000 characters/1048576 bytes. Maximum actual compact sizes are 94430/94430 search and 92298/92298 direct (characters/bytes). Per-page ordered IDs and wire envelope hashes are retained in feedback-results.json.
- Unicode projected attribution (non-BMP/CJK/accent/quote/backslash/newline) forces four whole-entry pages without loss; actual conservative sizes distinguish bytes from characters. Individually oversized later entry is rejected before returning a cursor, with the exact linked evidence URI. Mutating either semantic ceiling invalidates an otherwise valid cursor; a correctly checksummed pre-full-text fingerprint is also rejected.
- Final metadata boundary: two initial matches followed by 5000 nonmatches grow cursor/examination/stopping metadata beyond a scratch character ceiling. Whole-entry rewind produces pages of 81348, 83433 and 67311 characters, examination counts 5000, 5000, 1; reasons byte_limit, work_limit, exhaustion. Both matching edges are returned once. The final complete empty page truthfully reports exhaustion; nonmatch work advancement is preserved.
- boundary-feedback independently passes 271 checks (a subset of the final full feedback). byte-feedback adds five named checks with only scratch byte ceiling 95000 and character ceiling 2000000: two entries at 92468 bytes stop with byte_limit, then the last entry completes at 78540 bytes; no loss/duplicate/no-progress. Production ceilings are unchanged; this isolates the UTF-8 byte predicate, while ordinary feedback exercises the normal character predicate.
- Formal existing command: uv prefix plus pytest -q -p no:cacheprovider tests/kgfegmcp/test_progression_discovery.py. Exit 1: 14 passed, three failed in 35.67 seconds. Passing outcomes cover incoming/outgoing/related records, all four endpoint scopes, no cross-endpoint facet mixing, normalized request/cursor identity, zero-match work advancement, individually oversized first entry and checksum/range/stale boundaries. The failures are recorded below and are not hidden by a selected passing subset.
- Final static commands against src/kgfegmcp/services/lp_discovery.py and src/kgfegmcp/services/lp_models.py all exit 0: black --check; isort --check-only; ruff check; mypy --cache-dir ../R/mypy-cache; pylint --persistent=n (10.00/10); interrogate --generate-badge ../R/badge (100%). Replace R with its stated root. Exact expanded paths/argv are in final-black/isort/ruff/mypy/pylint/interrogate command receipts.
- All 1175 protected entry files remain byte-identical: accepted packages, config, preparation inputs, formal tests/fixtures, scope/design/context/protocol and other role artifacts. preservation-results.json records current staged source hashes; this assignment never writes the index. The shared encoder is currently staged/worktree sha256:88a02e2e114a6df0ce8b165886b76d6f31ee22e366755b846654830403532eea, unlike its historical DEV-012 receipt 6a81d1762f0c2c1241202c7630662bd4e5cadce817d224851217ffaac392b6a8. A historical-hash comparison exposed this discrepancy; DEV-013 did not edit that file, and all current feedback assessed the current staged bytes. The other three staged DEV-012 source identities still match their persisted receipts. Do not assert the historical encoder hash identifies this current input.
- Initial scratch attempts failed on a misnamed ordered helper, the wrong service byte-constant name and a scratch ceiling too small for a later single entry; fixed only scratch code. Earlier isolated-byte trial at 100000 admitted the full three-entry final page, so the separate 95000-byte check establishes actual byte stopping. Initial static isort check failed and was corrected; the first formatting recorder invocations had missing-label/path errors before mutation. Final source/runtime/static checks above pass. Existing pytest-asyncio fixture-loop warning is retained and did not cause failures.

**Corrective ownership and return**

Three Tester-owned cases in backend/tests/kgfegmcp/test_progression_discovery.py are incompatible with the approved full-text envelope, not evidence of lost edges:
1. test_complete_pagination_matches_original_edges uses pages() with a fixed 400-iteration cap; Ghana English already requires 526 pages and CBSE 3193. Replace the obsolete cap with a finite dataset/work-derived bound while retaining ordering, uniqueness, cursor advancement and exhaustion assertions.
2. test_reused_profile_code_and_grade_facets uses the same obsolete cap; CBSE Class IX completes in 1634 pages. Preserve independent alias/code/facet and complete-selection assertions.
3. test_discovery_combination_bytes_preserve_continuation projects 600000 characters into each entry. Canonical text plus structured evidence now exceeds both ceilings for even one entry, so rejection is correct. Re-establish a genuinely individually returnable fixture that exceeds the envelope only in combination, retaining whole-entry replay assertions and both-ceiling checks. Keep the existing oversized-entry rejection case.

The formal file hash remains sha256:2918295e9e4a09674e29e2c608e8a23e53e1bda72787e83d30f1b804b54563e1. Developer may not alter formal tests/report or weaken the approved implementation to satisfy obsolete fixtures. Route VERIFICATION -> TESTING as a scoped correction, not CHECKPOINT/full assessment. Tester independently reconciles its historical COMPLETE report, preserves future approved implementation as awaiting implementation, corrects these affected tests, runs relevant regressions and selects the scoped return under the protocol. Full Developer/Tester acceptance is not claimed.

Persist nested Frame 2 while retaining the exact SCOPING-owned Frame 1 and its route through SYNCHRONIZING. No public inventory/version/stage refresh is claimed; it remains intermediate 17 tools/9 prompts/1 resource/14 templates. read_evidence/get_workflow_instructions and later DEV-014/015/024/025/022 remain future work. After Tester RESUME, Developer must reconcile corrected files/results, rerun the affected self-check and finalize DEV-013 only if satisfactory; STEPWISE then pauses before DEV-014. Suggested commit for the actual implementation: feat(progressions): add bounded replay requests and cursor budgets.

**Current assessed identities**

- backend/src/kgfegmcp/services/lp_discovery.py: sha256:56649b6160c048fb1da22f1df0f5c033134610913018730519cce7a6de8cbe56
- backend/src/kgfegmcp/services/lp_models.py: sha256:abf62dd32493729cf041441016156996fecfb172470ce1c24710abaaefece0fb
- R/feedback-results.json: sha256:3950039afa3dd59163c13803a934d05e6c4f52663a91d2f9c923e02018013c72
- R/evidence-index.json: sha256:7f292ca067edd3e010be0e317d835aaee07316a35185f19094eeb6dcbc8de8c8

### Suspended Assignment 1

`Recovery Frame`: `2` `Recovery Reason`: `Tester-owned discovery tests retain obsolete 400-page and 600000-character fixture assumptions under the approved canonical full-text 100000-character envelope; correct the three affected cases and re-establish bounded complete replay before Developer finalizes DEV-013.`
`Purpose`: `DEVELOPMENT`
`Target`: `NONE`
`Assessed Inputs`: `HEAD 327439a6818ee6a66ff4f2c6ceaa2c1120fb5769; DEV-013 discovery 56649b6160c048fb1da22f1df0f5c033134610913018730519cce7a6de8cbe56 and models abf62dd32493729cf041441016156996fecfb172470ce1c24710abaaefece0fb; test file 2918295e9e4a09674e29e2c608e8a23e53e1bda72787e83d30f1b804b54563e1; current shared encoder 88a02e2e114a6df0ce8b165886b76d6f31ee22e366755b846654830403532eea; full identities/commands in client-recovery-dev013/checks/evidence-index.json.`
`Next Action`: `On Tester RESUME, reload STATE/frame/plan/report, reconcile the corrected discovery tests and actual scoped assessment, rerun affected checks, finalize DEV-013 if satisfactory and stop before DEV-014 under STEPWISE. Restore the approved remaining implementation assignment; no additional plan approval for unchanged intent.`

This saves the interrupted overall approved DEVELOPMENT assignment, not a full verification request or a completed DEV-013 claim. It is associated with nested Frame 2 and its exact reason; Frame 1 remains intact.

Final handoff receipts: recorded-pre-handoff-workflow passed before transition. After the legal VERIFICATION handoff, the ordinary receiving-state check reports twelve problems solely in the unchanged Tester-owned historical report: reconcile COMPLETE/FULL into the assigned scoped correction and account for current AC-028..037. Those are explicitly part of this receiving Tester reconciliation, not deferred Developer fixes or new frames. The protocol turn-end runCheck(atTurnEnd=true), holding the handing-off Developer records, passes with no problems. Receipts handoff-workflow and handoff-turn-end retain actual outputs. Frame 1 and all other role files remain unchanged; Tester owns the active Frame 2.

### Developer resumption after DEV-013 Tester correction — 2026-10-06

User explicitly invoked Developer after Tester RESUME. Restore Suspended Assignment 1 (DEVELOPMENT/NONE, former Frame 2 and its exact persisted reason) to the unchanged approved seven-assignment recovery plan. Its next action is to finalize DEV-013 after satisfactory current checks, then honor STEPWISE before DEV-014. Tester corrected only its discovery test file and verification report; both are staged by the user. The current test is f8065e90c6aed3be94a77bd1bb97a91cb1e9971a94a063111d36e1c24a813844. All five assessed runtime hashes equal the previous DEV-013 evidence index, and all prior runtime/static receipt hashes still match. Comparing 1175 protected original inputs finds exactly the two authorized Tester-owned changes; all other protected inputs retain their identities. Current entry HEAD remains 327439a6818ee6a66ff4f2c6ceaa2c1120fb5769; preserve staged diff and existing source bytes.

Independent reconciliation: the finite original-candidate-count-plus-one replay bound supports one-edge pages and retains progress/repeated-cursor/order/uniqueness/exhaustion assertions; the 3000-character combination fixture proves all three individual entries returnable before asserting whole-entry continuation and full canonical text/structured envelope limits. Oversized-first-entry rejection remains. This preserves the approved contract and required assertions; it is not a material plan revision or new implementation authority. Tester reports CORRECTION/IN_PROGRESS with all 37 ACs accounted for, 26 offline cases and six test-static checks passing. Read the actual report/receipts and test diff; the independent scoped correction is applicable to current runtime identities. Preserve its historical target and records.

Developer now reruns that same affected 26-case discovery/exact/AS-LC suite. Reuse the previous 303-check text-only/runtime feedback, five isolated-byte checks and six production static passes only for their unchanged runtime identities; this is evidence reuse, not a claim of a new run. No full gate, future five-operation/access/distribution acceptance, later-step implementation, deployment or sign-off is asserted. SCOPING-owned Frame 1, its exact reason/resumption route, AFTER_IMPLEMENTATION/NONE and locked tony remain unchanged. Entry workflow check passed; no conditional protocol chapter applies.

**Resumed DEV-013 step gate — PASS**

No production code change was needed on this return. Developer's actual command, from /Users/tzz/Projects/private/idi/KGForEdGlobalMCP, was:

```sh
/Users/tzz/.local/bin/uv --directory backend run --locked --offline --no-sync pytest -q -p no:cacheprovider -m 'not costs-money' tests/kgfegmcp/test_progression_discovery.py tests/kgfegmcp/test_progression_lookup.py tests/kgfegmcp/test_progression_regressions.py
```

Exit 0: 26 passed in 67.36s; recorder outer duration 67.876627 seconds. R = data/source_artifacts/learning_progressions/client-recovery-dev013-resume/checks/. R/scoped-regression.command.json/stdout/stderr retain exact argv, repository cwd, UV_OFFLINE=1, PYTHONDONTWRITEBYTECODE=1, PATHS_PROJECT_DIR, start/duration/exit and full outputs. This is Developer implementation feedback, not a new formal Tester assessment. The pre-existing fixture-loop deprecation warning remains nonblocking. Pre-completion workflow and whitespace commands passed; final workflow checks run after persistence.

The corrected full discovery module passes, including all 8080 original ordered IDs, finite whole-entry replay without loss/duplication, directional/symmetric adjacency, four endpoint scopes, whole-endpoint facets, normalized selectors/grade/code aliases, exact snapshot/cursor integrity, work-limited empty advancement and oversized-entry rejection. The combination fixture remains individually returnable, returns all three edges exactly once and independently counts canonical text plus structured envelope under both ceilings. Exact and AS/LC regressions also pass. Tester-owned test/report content and their scoped evidence remain untouched. The previous 303 named runtime/text-only checks, five isolated-byte checks and six source static checks are explicitly reused for the same five runtime hashes; all old command/stream/script/result hashes still match.

R/entry-inputs.json reconciles the Tester test/report changes; R/preservation-results.json verifies all 1175 resumed protected files, all six assessed runtime/test hashes and the user-staged diff remain unchanged. R/evidence-index.json hashes new receipts and references the unchanged prior DEV-013 evidence index. Current corrected test SHA256 f8065e90c6aed3be94a77bd1bb97a91cb1e9971a94a063111d36e1c24a813844; runtime identities remain the ones listed above. No new source/test/configuration/package edits, commits, dependency synchronization, network/model/paid calls or archive/client acceptance claims.

DEV-013 DONE; restore and retain the approved overall DEVELOPMENT/NONE assignment. Plan remains IN_PROGRESS; DEV-014/015/024/025/022 are PENDING. Full Developer gate remains unmet solely because this authorized future implementation remains. Preserve Tester report CORRECTION/IN_PROGRESS and its historical assessment target, the latest TESTING RESUME handoff and the exact SCOPING-owned Frame 1/route. No new handoff/frame/pop is appropriate. Persist only the STEPWISE continuation request for DEV-014 and stop. No duplicate plan approval is needed; this return does not authorize DEV-014.

Final persistence gates passed: final-workflow (node .standards/bin/check.mjs), final-whitespace (git diff --check), each exit 0. Their full command/stream receipts are included in the resumed evidence index, SHA256 1f7b125dfe1f90b53ad68037223664c6115687e750d3b7941a86f0910f949214. DEV-013 completion and the DEV-014 STEPWISE continuation remain authoritative.

### Recovery continuation for DEV-014 — 2026-10-06

User explicitly authorized DEV-014 after DEV-013 completion. Preserve all user-staged prior source/test/report/state/plan bytes and index, locked tony, STEPWISE, AFTER_IMPLEMENTATION/NONE and the exact SCOPING-owned Frame 1. Clear only DEV-014 continuation blocker; DEV-014 IN_PROGRESS. DEV-015/024/025/022 remain unstarted. Shared DEV-012 encoder already applies both ceilings through the existing traversal hook; reconcile whole-entry/final metadata admission and frontier behavior against that current envelope rather than add a parallel size policy. Update traversal size/noncontinuation wording only as necessary and re-establish current offline feedback. Entry workflow check passed; current protocol/context/scope/design/styles were read in this continuing session and no conditional chapter applies. New retained scratch root is data/source_artifacts/learning_progressions/client-recovery-dev014/checks; entry-inputs.json records protected inputs, source/state/index identity.

### Client-access recovery for DEV-014 — implementation assessed 2026-10-06

User authorized only DEV-014. Current HEAD 327439a6818ee6a66ff4f2c6ceaa2c1120fb5769; the previous source/test/report/state/plan index staged by the user is preserved byte-for-byte, with staged-diff SHA256 e04aebc0d04b80a31effeb818873ec5dde41729a44969298694debf31a6e364c. Locked tony, STEPWISE, AFTER_IMPLEMENTATION and Current Increment NONE remain unchanged. DEV-014 stays IN_PROGRESS with a PARTIAL self-check pending the two formal fixture corrections below. This section supersedes historical DEV-014 PASS/DONE/readiness claims. DEV-015/024/025/022 remain future approved implementation, not deferred defects.

**Implemented outcome and preservation**

- The existing traversal whole-edge admission, conservative final-metadata reservation, exact-first-entry fallback and later-entry rollback already use the shared DEV-012 complete-envelope guard, including canonical text plus structured output. No executable traversal algorithm or parallel encoder was needed. Updated its comments/docstrings to describe both byte and character ceilings and updated traversal_notice to explain narrowing bounded inputs after truncation and byte_limit covering either complete-envelope ceiling.
- Preserve BFS branch/merge/cycle retention, minimum distances, original upstream edge orientation, no continuation, actual pending frontier/counters, individual oversize errors and exact immutable package/judgment/rights identities. The production 1,048,576-byte and 100,000-character complete serialized envelope ceilings are unchanged.
- All 1175 protected entry inputs retain exact bytes: six accepted packages and maintained inputs, configuration/profile/prompt configuration, formal tests/fixtures/report and other owners' records. No index, commit, package/source preparation, dependency, native prompt/resource, role-owned prose/test/report or distribution edit was made. Only models/traversal wording, Developer plan/state and new ignored scratch receipts changed.

**Actual implementation feedback**

R = data/source_artifacts/learning_progressions/client-recovery-dev014/checks. run_command.py records exact argv/cwd/environment/start/duration/exit and full stdout/stderr for every command. UV_OFFLINE=1, PYTHONDONTWRITEBYTECODE=1 and PATHS_PROJECT_DIR point at this checkout; uv uses locked/offline/no-sync. Runtime feedback blocks sockets and query-time source reads. These are Developer checks, not independent Tester acceptance.

- final-wire-feedback: exit 0; 3510 named assertions, 406 accepted-package queries across all six current runtimes, 20 synthetic outcomes. Independent reachable/induced-edge/distance oracles cover complete scopes; partial results verify whole-edge/node coherence, stored originals, exact counts, scopeComplete/graphExhausted, actual pending adjacency and examined work, canonical text equality, no continuation and both complete-envelope measurements.
- Compact in-memory synthetic metadata isolates topology without changing accepted records: both directions of the four-edge diamond, cycles/depth-only scope, node/edge/work budgets (including exact 5000 exhaustion), whole-entry Unicode combination stops, first/later individually oversized errors with provenance recovery, and exact-first-entry fallback. Normal character-limit checks include a fitting complete first envelope of 99999 characters and a fitting partial first envelope of 100000 characters; the next calibrated complete envelope is rejected. Byte-only diagnostic checks temporarily relax the character constant in scratch: 1048575 bytes fits and 1048577 is rejected; later whole-edge/node rollback remains coherent. Supplemental depth-12 and exact-100-edge checks use scratch-only nonbinding character limits. These supplemental isolated checks do not claim that every such topology fits normal production limits.
- Real FastMCP call_tool_mcp upstream/downstream results expose nonempty parseable canonical JSON equal to structuredContent and exact snapshot/evidence identity. Nigeria diagnostic snapshot nigeria-nerdc-mathematics-primary-1-3@undated+bc5e769ed26f and original edge 0129f5d5-42fd-52cb-bcf2-ec07c47103e7 are checked. Downstream actual wire envelope: 92457 bytes/characters, SHA256 0fef197939bcec1a4bb55cc0a56141be19b55abcd1e713ce0546b4d40e085a70; upstream: 92748 bytes/characters, SHA256 2ac79eb44bc1dd54ef6798b7ad00821c0081a40bd00f2a97be09c8a23832c28f.
- regression: eight existing traversal/protocol/Academic Standards/Learning Components cases pass in 13.86 seconds, including both oversized-edge rejection cases and existing tool/native prompt/schema/error/masking behavior.
- Six changed-module static checks pass: black, isort, ruff, mypy, pylint (10.00/10), interrogate (100 percent). No dependency install or paid/live model calls.
- Iteration receipts feedback, feedback-corrected and final-feedback failed respectively on scratch section extraction syntax, attribution-overhead calibration and an incorrect object-identity assertion for MCP-deserialized models. Only scratch feedback was corrected; current service original-reference assertions still use identity, while serialized wire results use value equality. Those failed iterations are retained and are not counted as passes.

**Required Tester-owned correction**

algorithm-regression ran all six formal traversal algorithm cases: four pass, two fail, ten nontraversal cases deselected, exit 1 in 18.06 seconds. Full failure streams are preserved. No formal test/fixture/report was edited.

1. test_traversal_combination_only_bytes in backend/tests/kgfegmcp/test_progression_algorithms.py uses two projections of 150000 emoji characters. Even its first complete entry exceeds the canonical text plus structured 100000-character ceiling, so the current individually oversized error is correct. Tester must independently construct/calibrate a genuinely individually fitting combination-only overflow fixture and assert whole-entry rollback, both ceilings and honest frontier/counters; preserve individually oversized rejection.
2. test_traversal_keeps_merging_edges uses shared Topology with copied full accepted metadata (86 artifact descriptors). That synthetic four-edge envelope exceeds the current character ceiling, yielding three whole edges plus truthful byte_limit. Tester must retain the full BFS branch/merge assertions using a returnable synthetic fixture, assess the size-stop case independently and avoid weakening the production ceiling or original evidence. Current compact synthetic diamond feedback preserves all four edges in both directions.

Topology is shared with path tests; if Tester changes it, assess affected shared-fixture regressions and reconcile the known similar test_paths_combination_only_bytes fixture (75000 emoji characters per path edge) under current ceilings as needed. This is fixture-dependency reconciliation, not Developer DEV-015 implementation or a full path acceptance claim. Tester independently chooses the appropriate bounded correction target and relevant regression set; its historical discovery CORRECTION report must be reconciled to this new assignment. No full Developer completion, Tester acceptance, Desktop model workflow, STDIO/HTTP/stage refresh, remote connector acceptance or deployment is claimed.

**Current command and assessed identities**

- final-wire-feedback: exit 0; argv ["/Users/tzz/.local/bin/uv", "--directory", "backend", "run", "--locked", "--offline", "--no-sync", "python", "/Users/tzz/Projects/private/idi/KGForEdGlobalMCP/data/source_artifacts/learning_progressions/client-recovery-dev014/checks/feedback.py"]; 10.51 seconds.
- regression: exit 0; argv ["/Users/tzz/.local/bin/uv", "--directory", "backend", "run", "--locked", "--offline", "--no-sync", "pytest", "-q", "-p", "no:cacheprovider", "-m", "not costs-money", "tests/kgfegmcp/test_progression_traversal.py", "tests/kgfegmcp/test_progression_protocol.py", "tests/kgfegmcp/test_progression_regressions.py"]; 14.53 seconds.
- algorithm-regression: exit 1; argv ["/Users/tzz/.local/bin/uv", "--directory", "backend", "run", "--locked", "--offline", "--no-sync", "pytest", "-q", "-p", "no:cacheprovider", "-m", "not costs-money", "tests/kgfegmcp/test_progression_algorithms.py", "-k", "traversal"]; 18.65 seconds.
- black: exit 0; argv ["/Users/tzz/.local/bin/uv", "--directory", "backend", "run", "--locked", "--offline", "--no-sync", "black", "--check", "src/kgfegmcp/services/lp_traversal.py", "src/kgfegmcp/services/lp_models.py"]; 0.18 seconds.
- isort: exit 0; argv ["/Users/tzz/.local/bin/uv", "--directory", "backend", "run", "--locked", "--offline", "--no-sync", "isort", "--check-only", "src/kgfegmcp/services/lp_traversal.py", "src/kgfegmcp/services/lp_models.py"]; 0.11 seconds.
- ruff: exit 0; argv ["/Users/tzz/.local/bin/uv", "--directory", "backend", "run", "--locked", "--offline", "--no-sync", "ruff", "check", "src/kgfegmcp/services/lp_traversal.py", "src/kgfegmcp/services/lp_models.py"]; 0.02 seconds.
- mypy: exit 0; argv ["/Users/tzz/.local/bin/uv", "--directory", "backend", "run", "--locked", "--offline", "--no-sync", "mypy", "--cache-dir", "../data/source_artifacts/learning_progressions/client-recovery-dev014/checks/mypy-cache", "src/kgfegmcp/services/lp_traversal.py", "src/kgfegmcp/services/lp_models.py"]; 3.19 seconds.
- pylint: exit 0; argv ["/Users/tzz/.local/bin/uv", "--directory", "backend", "run", "--locked", "--offline", "--no-sync", "pylint", "--persistent=n", "src/kgfegmcp/services/lp_traversal.py", "src/kgfegmcp/services/lp_models.py"]; 2.99 seconds.
- interrogate: exit 0; argv ["/Users/tzz/.local/bin/uv", "--directory", "backend", "run", "--locked", "--offline", "--no-sync", "interrogate", "--generate-badge", "../data/source_artifacts/learning_progressions/client-recovery-dev014/checks/badge", "src/kgfegmcp/services/lp_traversal.py", "src/kgfegmcp/services/lp_models.py"]; 0.1 seconds.

- backend/src/kgfegmcp/services/lp_models.py: sha256:919a377f7e273e3ccf3826958b5053b2fdd344827c8aed753a35c11a1dd9ce90
- backend/src/kgfegmcp/services/lp_traversal.py: sha256:41c6d8a4ed5327d0bfcaa34a1b868da1e7cd9f5d8745a8c4b8610442b2d51dc3
- backend/src/kgfegmcp/services/learning_progressions.py: sha256:e28e7e761b9902b90347b9c8458a718dd2da98d0df2f82f33d03d5c5c7a881ae
- backend/src/kgfegmcp/services/lp_discovery.py: sha256:56649b6160c048fb1da22f1df0f5c033134610913018730519cce7a6de8cbe56
- backend/src/kgfegmcp/mcp/tools/learning_progressions.py: sha256:9e19246d5cd0a37656e36e2f277a168bc97a58333886b2c607d0da55ec72f445
- backend/src/kgfegmcp/tool_results.py: sha256:88a02e2e114a6df0ce8b165886b76d6f31ee22e366755b846654830403532eea
- backend/tests/kgfegmcp/test_progression_algorithms.py: sha256:5687abe0a023bbdd374d5b052eac00328232c9ae8b287237222c3b73675dec39
- backend/tests/fixtures/progression_fixtures.py: sha256:4ff30f0446940b280fcbcf660f4c506875fd44674f28a89090d7b5a7bcda7170
- backend/tests/kgfegmcp/test_progression_traversal.py: sha256:188026117bfc0f91db12a9a2df613deee53cfff209a4bc02790a03abddda1af6
- backend/tests/kgfegmcp/test_progression_protocol.py: sha256:e3ccfcb143ed160c5294e1d4b1b91feb9fb30e4ca81a140aad20a9da2a95cc93
- backend/tests/kgfegmcp/test_progression_regressions.py: sha256:82865893b9983afcd2b929bdc9edf0f419cc7cc844ff56a602a594eb308bc611
- backend/tests/kgfegmcp/test_progression_discovery.py: sha256:f8065e90c6aed3be94a77bd1bb97a91cb1e9971a94a063111d36e1c24a813844
- .standards/docs/verification/integrate-actual-learning-progressions-20261001T162834Z-142f2df1.md: sha256:50ea8b36c1e58b3a491a25be50c57e706b31d9a04ee9a64ff104d4963eb0a105

R/feedback-results.json SHA256 1bfd047ab999812efdd81c5d72ef77055c714d37191f8fa3e63326dabffdf1f6; R/evidence-index.json initially SHA256 fdefbadde364ff578a9c3ee7cc310708d50205e582ff34a9aee62696490dd8a3. The evidence index binds all current runtime/test/report identities, exact package identities in feedback-results.json, command/stream receipts and protected/index preservation. It will include final workflow receipts after persistence.

### Suspended Assignment 2

`Recovery Frame`: `2` `Recovery Reason`: `Tester-owned traversal tests assume a full four-edge diamond with copied package metadata and a 150000-character combination fixture; correct those DEV-014 fixtures for canonical full-text 100000-character envelopes while preserving whole-edge BFS/frontier assertions.`
`Purpose`: `DEVELOPMENT`
`Target`: `NONE`
`Assessed Inputs`: `HEAD 327439a6818ee6a66ff4f2c6ceaa2c1120fb5769; models 919a377f7e273e3ccf3826958b5053b2fdd344827c8aed753a35c11a1dd9ce90; traversal 41c6d8a4ed5327d0bfcaa34a1b868da1e7cd9f5d8745a8c4b8610442b2d51dc3; algorithm tests 5687abe0a023bbdd374d5b052eac00328232c9ae8b287237222c3b73675dec39; shared fixture 4ff30f0446940b280fcbcf660f4c506875fd44674f28a89090d7b5a7bcda7170; shared encoder 88a02e2e114a6df0ce8b165886b76d6f31ee22e366755b846654830403532eea; all current sources/tests/receipts/package identities in client-recovery-dev014/checks/evidence-index.json and feedback-results.json.`
`Next Action`: `On Tester RESUME, reload STATE/frame/plan/report, restore DEVELOPMENT/NONE and reconcile the corrected traversal/shared-fixture inputs and actual scoped results. Rerun affected DEV-014 checks, finalize DEV-014 only if satisfactory and stop before DEV-015 under STEPWISE. Restore the unchanged approved remaining implementation assignment; no duplicate plan approval is needed.`

Save the interrupted overall Developer assignment before routing the scoped VERIFICATION defect to TESTING. Push only nested Frame 2, From/ResumeAt DEVELOPING, Owner TESTING, RerunThrough NONE; preserve the exact SCOPING-owned Frame 1 and its SYNCHRONIZING route. No CHECKPOINT/full verification request or frame pop is appropriate. All older suspended assignments and receipts remain intact. Suggested commit for current wording: feat(progressions): clarify bounded traversal outcomes.

Final routing receipts: the first pre-handoff-workflow run found escaped Markdown field delimiters in the new suspended assignment; corrected only those delimiters. pre-handoff-workflow-corrected then passed. After persisting the legal scoped TESTING/FAILURE/VERIFICATION handoff and nested Frame 2, handoff-workflow and handoff-turn-end (runCheck atTurnEnd=true) both passed with no problems. Tester still must reconcile its existing CORRECTION target/report to the new traversal assignment; mechanical gate success is not that assessment. Protected-input, current source/test/report hashes and staged-index comparison passed again after routing. Final evidence-index.json SHA256 6bfbad9975fb1ea60161d1f420ad4f1f363a4ff2ff3d2b8601e18ee23c850078. All full command/output receipts are retained; failed iterations remain explicitly nonpassing.

### Developer resumption after DEV-014 Tester correction — 2026-10-06

User explicitly invoked Developer after Tester RESUME (From TESTING, FailureType NONE). Restored Suspended Assignment 2 (DEVELOPMENT/NONE, former Frame 2 and its exact traversal VERIFICATION reason) to the unchanged approved recovery plan. Entry HEAD bd7c83ba0204e9d25a3d2611403a1fefef843ad7, clean tracked tree and empty index. Only SCOPING-owned Frame 1 remains, from/resuming AWAITING_USER_SIGNOFF with RerunThrough SYNCHRONIZING. Locked tony, STEPWISE, AFTER_IMPLEMENTATION and Current Increment NONE are unchanged. Entry workflow check passed; no conditional protocol chapter applies.

**Input reconciliation**

R = data/source_artifacts/learning_progressions/client-recovery-dev014-resume/checks. R/entry-inputs.json rehashes the same 1175 protected inputs as the suspended entry: exactly three changed, all Tester-owned — the verification report, backend/tests/kgfegmcp/test_progression_algorithms.py (cb17b350ad7d4225509f6b6b1c1cbe230b254ade6861685b2b5d4073f277117b) and backend/tests/fixtures/progression_fixtures.py (060ec5316c8304203ddc3e7e4db06c9a307fecd04b24738aba237716cb1c3486). Commits since c1cbf15 touch only those plus STATE. All six assessed runtime identities (lp_models, lp_traversal, learning_progressions, lp_discovery, MCP LP tools, tool_results) equal Suspended Assignment 2.

Independent review of Tester's diff: the shared synthetic Topology keeps one representative accepted artifact descriptor instead of the full 86-artifact inventory; real-package tests keep full metadata. The diamond BFS branch/merge assertions are unchanged. Both combination fixtures are recalibrated (20000/10000 emoji) so each single-entry control is individually complete and fitting, then assert whole-entry rollback, original-reference identity, distances, counters, frontier and both complete-envelope ceilings. Individually oversized rejection cases are unchanged; no production ceiling is relaxed. This preserves the approved contract and needs no plan revision or new implementation authority.

**Resumed DEV-014 step gate — PASS**

No production code change was needed on this return. Commands ran via R/run_command.py from the repository root with UV_OFFLINE=1, PYTHONDONTWRITEBYTECODE=1, PATHS_PROJECT_DIR and uv --locked --offline --no-sync. UV_CACHE_DIR pointed at the session temp directory because the sandbox blocks the default uv cache; the first three attempts failed for that reason and are retained as R/sandbox-denied-*. A first wire-feedback attempt failed only because the copied script needs a resume entry-inputs.json; retained as R/missing-entry-*. Neither failed iteration counts as a pass.

- algorithms: pytest -q -p no:cacheprovider -m 'not costs-money' tests/kgfegmcp/test_progression_algorithms.py — exit 0, 16 passed (6.38 s), including both corrected traversal cases and the reconciled shared path fixtures.
- regression: same pytest prefix on test_progression_traversal.py, test_progression_protocol.py and test_progression_regressions.py — exit 0, 8 passed (14.55 s).
- final-wire-feedback: python R/feedback.py (byte-identical copy of the suspended script, 105d93db0b03a971a0f84d30c55270ec4c812db1175445b944485f8b20e68281) — exit 0 (10.83 s); 3510 assertions, 406 accepted-package queries, 20 synthetic outcomes, all 1175 protected inputs match the resume entry. Upstream/downstream wire envelopes again measure 92748/92457 bytes and characters with unchanged SHA256 2ac79eb4…/0fef1979…; R/feedback-results.json is byte-identical to the suspended run (1bfd047ab999812efdd81c5d72ef77055c714d37191f8fa3e63326dabffdf1f6).
- Static: the six changed-module passes (black, isort, ruff, mypy, pylint 10.00/10, interrogate 100%) are reused from the suspended root for the same runtime hashes; this is evidence reuse, not a new run.

R/evidence-index.json (SHA256 716831640714a5fdce1a7b764bba97dd57795c08f5abb13f5dc99261601a6897) binds the receipts, assessed source/test identities, reused static receipts and the prior evidence index. Pre-existing pytest-asyncio loop-scope warning remains nonblocking. These are Developer feedback, not formal Tester acceptance.

DEV-014 DONE. Plan remains IN_PROGRESS; DEV-015/024/025/022 are PENDING approved work. Full Developer gate remains unmet solely because that work is unfinished. Preserve the Tester report CORRECTION/IN_PROGRESS and its historical target, the latest TESTING RESUME handoff and exact Frame 1. No new handoff, frame or pop applies. Persist only the STEPWISE continuation request for DEV-015 and stop; this return does not authorize DEV-015.

### Recovery continuation for DEV-015 — 2026-10-06

User explicitly authorized DEV-015 after DEV-014 completion. Cleared only the matching STEPWISE blocker; DEV-015 IN_PROGRESS. Entry HEAD bd7c83ba0204e9d25a3d2611403a1fefef843ad7 with clean index; Frame 1, locked tony, STEPWISE, AFTER_IMPLEMENTATION/NONE unchanged. Entry workflow check passed; no conditional protocol chapter applies. R = data/source_artifacts/learning_progressions/client-recovery-dev015/checks; R/entry-inputs.json records the same 1175 protected inputs and the intended edit set (lp_paths, lp_models, learning_progressions).

### Client-access recovery for DEV-015 — implementation assessed 2026-10-06

**Implemented outcome**

- Reconciliation found connecting paths already use the DEV-012 shared complete-envelope guard (canonical text plus structured content, both ceilings) for reservation, first-path fallback, whole-path rollback and the final result; the tool adapter already emits canonical text; metadata.limits already reports maxResultCharacters 100000. No parallel encoder was added.
- lp_models path_notice now states that no continuation exists, to narrow bounded inputs and rerun after truncation, and that byte_limit covers either complete-envelope ceiling (same wording as traversal).
- lp_paths standalone oversized-path check now measures the path alone with the byte_limit reason it carries while a frontier remains (traversal does the same), so returnable and unreturnable paths are distinguished consistently. Docstrings/comments describe both ceilings. require_paths_result_size docstring documents both ceilings and its error.
- Current identities: lp_paths 2aaa5d04fb0a8d036caff0630b9913e2e07fce5ab67048b61db504f48e4d1f1a; lp_models 68619102e50634262c51798f4daf19974dc0442a3b468ff51162b93d3fbb56c1; learning_progressions 50e204c735d3c8c2e08ec680e488b1d701a15cde77de053a52f778eb6dfb798c. lp_traversal, tool_results and the MCP LP tools are unchanged.

**Actual implementation feedback**

Commands ran via R/run_command.py from the repository root (UV_OFFLINE=1, PYTHONDONTWRITEBYTECODE=1, PATHS_PROJECT_DIR; uv --locked --offline --no-sync; UV_CACHE_DIR in the session temp directory because the sandbox blocks the default uv cache). Developer feedback, not Tester acceptance.

- feedback (python R/feedback.py, SHA256 72f9b61f88226053ab7d4ebeba624251571c7d4419245f7feac58376ad226a34): exit 0; 897 named checks, 412 accepted-package path queries, 27 synthetic outcomes; R/feedback-results.json SHA256 342e1a8fe0c13c9d209cde1439897305924e01b80a78e2ef564c836e1d63630f. Real paths equal the sorted prefix of an independent DFS oracle across all six packages; complete scopes return every oracle path; canonical text equals structured output; no cursor fields; both ceilings hold; selectors, same-standard, missing/root, unavailable-code, rights and exact-evidence agreement pass. Synthetic: merging alternatives in hop/edge-tuple order, export-order independence, reverse absence, per-path cycles, depth 6/12 frontier, path caps 1/3 (20 under scratch-relaxed size), work/queue 5000 boundaries, random DAG/cyclic oracle, Unicode character-ceiling whole-path rollback, oversized first/later failure with recovery, exact first-path fits at the character ceiling (complete and with pending frontier), and byte-only boundaries with the character constant relaxed in scratch. Real FastMCP calls: Nigeria two-hop result 84794 characters (SHA256 97d33663…), direct diagnostic edge 0129f5d5-42fd-52cb-bcf2-ec07c47103e7 result 75921 characters (SHA256 251fcde8…); ordinary text alone carries the full result. Retained nonpassing iterations: feedback-abort-oversized (real oversized path aborted the scratch run), -path20-expectation and -combination-expectation (my scratch expectations were wrong; code behavior correct), -wire-pair/-diagnostic-pair (diagnostic edge has no returnable two-hop extension), -receipt-serialization (read-only mapping in receipt).
- regression: pytest on test_progression_algorithms/traversal/protocol/regressions/acceptance — exit 0, 39 passed (14.67 s).
- Static on the three changed modules: black, isort, ruff, mypy (no issues), pylint 10.00/10, interrogate 100% — all exit 0. First attempts (unsplit-args-*) failed only because zsh did not split the file list.
- R/evidence-index.json SHA256 17227f17c6720d1fc3e350709a9a1475a7f56e09c9265b6b71ed4512fe134823 binds receipts, entry/current source identities and probes.

**Architecture defect discovered**

R/size-probe.json (SHA256 af50b6d28c92b3c91841b50da17028ee66fe87e0ea66496ee3cdf76ab9213dec): an empty LP result already measures 66093–72375 envelope characters because the required metadata (≈30–33k characters, 86 artifact identities, notices) appears in both canonical text and structuredContent. Each path hop adds ≈8.4k (edge evidence ≈3.4k and endpoint summary ≈0.8k, twice). Only 2–3 hops fit under 100000 characters in any package, far below the approved path depth default 6/maximum 12.

R/reach-probe.json (SHA256 4fe712c1110d300cd3e4b52e5e1053573786c3b51c6fdeb73227572847686dab): ordered pairs whose shortest stored builds connection is 4+ hops can never be returned by any request — 13/472 Ghana English, 36/500 Ghana Mathematics, 31/1395 CBSE, 114/990 Tamil Nadu, 21/355 Nigeria, 604/2810 Rwanda (21.5%). Some 3-hop paths also exceed the ceiling (Tamil Nadu, CBSE).

The approved oversized-path rule then fails a whole request that found shorter answers: Tamil Nadu b536c540-4b5d-5255-81e9-b061abfd42c6 → 4061ea8e-a99e-5043-a2d4-b6a0e537dd6f has oracle paths of 2, 3, 3 and 4 hops; with defaults (depth 6, paths 3) and with depth 6/paths 20 it returns progression_result_too_large (100437/100439 characters) instead of the 2-hop path. The actual MCP error text is explicit and recovers through read_evidence and narrowing, but the default request and the approved teaching-sequence workflow parameters (depth 6, at most 3 paths) fail on real data.

Resolving this requires a consequential design choice owned by Architect, for example: a compact per-result identity/metadata projection that links full metadata through read_evidence; a different text/structured duplication budget; byte_limit stopping before an individually oversized later path instead of failing the whole request; or path maxima/defaults that real envelopes can satisfy. Each changes approved contracts ("do not drop identity", "individually oversized entry fails", 6/12 maxima), so Developer does not choose one. The same metadata cost limits traversal to ≈3–4 edges and direct/search pages to ≈3–4 edges per page; those remain honest partial/paged results already accepted as a design risk, but Architect should account for them in the same decision. No accepted data, ceiling or formal test was changed.

### Suspended Assignment 3

`Recovery Frame`: `2` `Recovery Reason`: `Real accepted envelopes spend 66-72k of 100000 characters on duplicated metadata, so connecting paths beyond 2-3 hops (4+ hop pairs: 2-22% per package) can never be returned and an oversized later alternative fails default requests that found shorter paths; resolve metadata/size/oversized-path handling or path maxima.`
`Purpose`: `DEVELOPMENT`
`Target`: `NONE`
`Assessed Inputs`: `HEAD bd7c83ba0204e9d25a3d2611403a1fefef843ad7; lp_paths 2aaa5d04fb0a8d036caff0630b9913e2e07fce5ab67048b61db504f48e4d1f1a; lp_models 68619102e50634262c51798f4daf19974dc0442a3b468ff51162b93d3fbb56c1; learning_progressions 50e204c735d3c8c2e08ec680e488b1d701a15cde77de053a52f778eb6dfb798c; lp_traversal 41c6d8a4ed5327d0bfcaa34a1b868da1e7cd9f5d8745a8c4b8610442b2d51dc3; tool_results 88a02e2e114a6df0ce8b165886b76d6f31ee22e366755b846654830403532eea; receipts and probes in client-recovery-dev015/checks/evidence-index.json.`
`Next Action`: `On Architect return, reload STATE/frames/design/plan, reconcile the corrected size/metadata/path contract into DEV-015 and any affected completed steps (DEV-012/013/014) under plan approval rules, rerun affected feedback, finalize DEV-015 only if satisfactory and stop before DEV-024 under STEPWISE.`

Save the interrupted overall Developer assignment before routing. Push nested Frame 2, From/ResumeAt DEVELOPING, Owner ARCHITECTING, FailureType ARCHITECTURE, RerunThrough NONE; preserve SCOPING-owned Frame 1 and its SYNCHRONIZING route. DEV-015 stays IN_PROGRESS with its current source edits, which conform to the present design and pass their checks. Suggested commit for the current changes: feat(progressions): clarify bounded path outcomes.

### Architecture-finding triple check for DEV-015 — 2026-10-06

At the user's request the finding was re-verified exhaustively against the real service rather than estimated. R/triple-check.py (SHA256 388a5c4791ec0c4ba5885f31a3decdf2b164c5e288e4c3f66f87620e4c2e2d92) called get_learning_progression_paths for every ordered pair whose shortest stored builds connection is 3+ hops, using the most favourable request (max_paths 1, max_depth equal to that length). For each failure it reran with ceilings relaxed in scratch only and measured both the conservative shared envelope and the actual compact wire shape (text block plus structuredContent). Results in R/triple-check.json (SHA256 ea063650cab0c64a4ac2300cce806b01d38d0f65ee18ad9ec41b5aab2cecc4cc).

- Confirmed: every 4+ hop pair fails in all six packages (13, 36, 31, 114, 21, 604). The smallest failing compact wire is 101566 characters, so this is not an artifact of the conservative whitespace reserve.
- Correction (worse than first reported): all 138 three-hop Tamil Nadu pairs and 8/85 three-hop CBSE pairs also fail. Unreturnable totals: Tamil Nadu 252/990 (25.5%), Rwanda 604/2810 (21.5%), Ghana Mathematics 36/500 (7.2%), Nigeria 21/355 (5.9%), CBSE 39/1395 (2.8%), Ghana English 13/472 (2.8%). Nuance: the smallest failing three-hop compact wires are 99302 (Tamil Nadu) and 98976 (CBSE) characters, so some three-hop failures exceed only the conservative ~1000-character measurement reserve, not the compact wire itself.
- Correction: in the Tamil Nadu example b536c540… → 4061ea8e…, max_paths 1 returns the 2-hop path; max_paths 2 and 3 fail because the second path (3 hops) is individually oversized, not the third/fourth.
- Calibration: that returned 2-hop result has 44486 text characters, 90782 compact wire and 91736 conservative characters; its metadata alone is 33466 compact characters and is carried twice.

Frame 2's persisted reason remains accurate (4+ hop pairs are 2.8–21.5% per package; paths beyond 2–3 hops fail). Architect should use these corrected totals.

### Developer resumption after Frame 2 Architect correction — 2026-10-06

User explicitly invoked Developer after Architect RESUME (From ARCHITECTING). Restored Suspended Assignment 3 (DEVELOPMENT/NONE, former Frame 2 and its exact size reason). Entry HEAD ac0d300ea4e708f978094f73e90949eb6ba39189, clean tree; workflow check passed; no conditional protocol chapter applies. Read the corrected architecture diff, current metadata construction, artifact logical names (all four derivation artifacts exist in every package), ID type bounds (NodeId/RelationshipId up to 1,024 characters) and the domain error details mechanism. The correction materially changes approved DEV-012/DEV-015 behavior, so the plan is PROPOSED with the Frame 2 Size-Correction Revision and awaits explicit approval before implementation. No project implementation was changed in this session.

User explicitly approved the Frame 2 Size-Correction Revision on 2026-10-06, including the combined Tester correction route. Plan APPROVED then IN_PROGRESS; User Style Locked remains true (tony). Cleared only the matching approval blocker. DEV-012 IN_PROGRESS under STEPWISE.

### Frame 2 compact metadata for DEV-012 — completed 2026-10-06

**Implemented outcome**

- lp_models: PROGRESSION_DERIVATION_ARTIFACT_NAMES = learningProgressionProvenance, learningProgressionProvenanceIndex, nodes, relationships (sorted); ProgressionMetadata gains a fixed artifactInventoryNotice pointing to manifestUri/manifestSha256 and native resources/read_evidence.
- learning_progressions.evidence_metadata lists exactly those four accepted identities (logical name, sha256, artifact URI) in that order and fails with the existing capability_unavailable error if any is missing. Manifest hash/URI, package/profile identity, coverage, limits, notices and links are unchanged. All five tools share this metadata. Accepted packages still hold all 86 artifacts.
- Identities: lp_models d9dfb855da58a27d5f8c0f45bf874a7ae1f9811b303e23d57f67b5ecc2d0c260; learning_progressions b47a6c341436692f1af654627a6694346942c2a634dbc1070611048e45ab77b1. No other source changed.

**Actual implementation feedback**

R = data/source_artifacts/learning_progressions/client-recovery-dev012-frame2/checks; run via R/run_command.py with the established offline environment (UV_CACHE_DIR in the session temp directory because the sandbox blocks the default uv cache). Developer feedback, not Tester acceptance. R/evidence-index.json SHA256 e390b2cdf21708c37241648f29672c3a5b616f960110802c14bc64990f826602; all 1175 protected inputs unchanged.

- compact (R/compact.py): exit 0, 58 checks. Every package lists exactly the four derivation artifacts with accepted hashes; manifest hash binds the full inventory; notice present. Real FastMCP calls of all five tools (Nigeria) return ordinary text equal to structuredContent with the compact metadata, within both ceilings: exact lookup 20405 characters, direct page 93899 (8 edges), search page 94135 (7 edges), traversal 39829, path 23293.
- Size probe (R/size-probe.json): metadata now 4512–5182 compact characters (was 30336–33466); empty result envelope 12975–14347 characters (was 66093–72375); single paths of 8–9 hops now fit at maximum per-hop sizes.
- Reruns of earlier step feedback on the final bytes, copied byte-for-byte into R/dev012, R/dev013, R/dev014 with current protected-input lists: DEV-012 64 checks; DEV-013 121 checks with exhaustive replay of all 8080 edges in 1786 pages plus boundary 89 checks; DEV-014 3510 checks, 406 real queries, traversal wire 39829/55668 characters (was 92457/92748). All exit 0. DEV-013/014 outcomes still hold, so they stay DONE.
- DEV-013 byte isolation: its fixed 95000-byte scratch ceiling was calibrated to the old metadata, so three edges now fit and no byte stop occurred (retained as dev013-byte-old-calibration); 30000 made a single edge individually oversized (retained as dev013-byte-30000-oversized). The script now derives the ceiling from measured one- and two-edge pages (28146/39342 bytes → 34768) and passes with one whole edge per page and lossless cursor replay.
- regression: pytest tests/ — 76 passed, 2 failed, both expected superseded-contract cases (Tester-owned, not edited): test_progression_lookup::test_every_exact_edge_preserves_accepted_evidence expects all 86 artifacts in metadata; test_progression_discovery::test_discovery_combination_bytes_preserve_continuation uses a 3000-character projection fixture calibrated so only one edge fit per page under the old metadata (now three fit). Both are queued for the approved combined Tester correction after DEV-015.
- Static on both changed modules: black, isort (after applying import order; first run retained as isort-unsorted-import), ruff, mypy, pylint 10.00/10, interrogate 100% — exit 0. Feedback suites were rerun after the import reorder; pre-isort runs retained as pre-isort-*.

DEV-012 DONE. DEV-015 is next under STEPWISE and needs explicit continuation; DEV-024/025/022 remain PENDING. Suggested commit: feat(progressions): compact LP result metadata to derivation artifacts.

User explicitly authorized revised DEV-015 on 2026-10-06; cleared only its STEPWISE blocker. DEV-015 remains IN_PROGRESS.

### Frame 2 path size stop for DEV-015 — completed 2026-10-06

**Implemented outcome**

- lp_models: GetLearningProgressionPathsResult gains nextUnreturnedPath (ProgressionPath IDs only, default null); the path notice explains the size stop, that later paths may exist, and the recovery routes (get_learning_progression per edge, narrower maxDepth/maxPaths).
- lp_paths: when a completed path fails conservative reservation, the actual final envelope decides. If it fits, the path is kept and selection stops (byte_limit only while a frontier remains). Otherwise a later path is rolled back with its exclusive evidence, named in nextUnreturnedPath, kept in the queued frontier, and byte_limit is set; an unfittable first path raises progression_result_too_large whose details and recovery hint carry its ordered relationship IDs. Reservation includes a worst-case nextUnreturnedPath built from the package's longest JSON-encoded builds node/relationship IDs (PathIdBound), so emission cannot outgrow the budget. The former later-path standalone oversize check is removed.
- learning_progressions: PathIdBound per package is precomputed once at service construction beside the existing adjacency and passed to paths_result; paths_result derives it from adjacency when omitted (synthetic callers).
- Identities: lp_paths f5a1523fc60578cc383cfe396d1c86334b3073855df5787f0013bb217442abaf; lp_models 2e3c4ff225345812a56e76cba2aa1ac4a667aaa73feb60c8dfc2532142c4790e; learning_progressions e49b9f9d3c1e14dafd0cf759dfa1b82553705489dc89142b6e549a1cd341d20a.

**Actual implementation feedback**

R = data/source_artifacts/learning_progressions/client-recovery-dev015-frame2/checks (established offline environment; UV_CACHE_DIR in the session temp directory). Developer feedback, not Tester acceptance. R/evidence-index.json SHA256 93d8261f18d308d06a52d2d4b48b0191629a8a92721f6ffb112f52ec937e092a; all 1175 protected inputs unchanged.

- feedback (R/feedback.py SHA256 bd25673804ff6e9b5814b2c8d39bf3647a81337db8e006d1b1aaf8773788df92): exit 0; 955 checks, 6935 real queries, 29 synthetic outcomes; R/feedback-results.json SHA256 8d56dcd13ff0a044ec7f07ce4b3d7dc787c54d3464c2820072d7b67d235156f6.
  - Architect target met: every connected ordered pair in all six packages (6527 pairs, 1–8 hops) returns its complete shortest path with max_paths 1 and depth equal to that length; largest envelope 86045 characters (Rwanda 8 hops). Zero sampled real requests fail as oversized (was 2).
  - Sampled real requests match the sorted independent DFS prefix; whenever nextUnreturnedPath is present it equals the next oracle path. Size stops occurred in 10 sampled requests, 9 naming the next path.
  - Tamil Nadu b536c540… → 4061ea8e…: defaults return 2/3/3-hop paths with path_limit; depth 6/paths 20 returns all four paths (2/3/3/4 hops) complete in 91296 characters through MCP.
  - Real MCP size stop (Ghana Mathematics 0f38dcc7… → 6c083da5…, depth 6/paths 20): six paths returned, nextUnreturnedPath names the 3-hop path 7ea083dc…/176a5a58…/70fda556…, 94408 characters; ordinary text equals structuredContent.
  - Synthetic: whole-path combination rollback names ('b','c'); unfittable first path fails with details relationship_ids ('a',) and the IDs plus get_learning_progression/read_evidence in the hint; individually oversized later path is a partial result; binary-search boundary keeps a later path whole when its actual envelope fits and names it one character later; first-path fallback at the character ceiling keeps the pending frontier with no nextUnreturnedPath; isolated byte combination names the rolled-back path; existing topology/budget/random-oracle cases unchanged.
  - Retained nonpassing iterations: feedback-synthetic-metadata-assertion (verifier wrongly required four artifacts for empty synthetic metadata) and feedback-tamil-nadu-expectation (the request no longer stops on size).
- compact: rerun on final bytes, exit 0 (58 checks).
- regression: pytest tests/ — 76 passed, 2 failed: the same two superseded-contract cases recorded under DEV-012; all existing path algorithm cases pass unchanged.
- Static on the three changed modules: black, isort, ruff, mypy, pylint 10.00/10, interrogate 100% — exit 0.

DEV-015 DONE. Both Frame 2 steps are implemented; route the approved combined scoped VERIFICATION correction.

### Suspended Assignment 4

`Recovery Frame`: `2` `Recovery Reason`: `Tester-owned formal cases encode superseded Frame 2 contracts: test_every_exact_edge_preserves_accepted_evidence expects all 86 artifacts in LP metadata and test_discovery_combination_bytes_preserve_continuation uses a fixture calibrated to the old metadata size; correct them and assess compact metadata and the path size stop (nextUnreturnedPath) before Developer resumes.`
`Purpose`: `DEVELOPMENT`
`Target`: `NONE`
`Assessed Inputs`: `HEAD 172a2c85f7d9dca5157bb958976cdd1f54e5f587 plus working tree; lp_paths f5a1523fc60578cc383cfe396d1c86334b3073855df5787f0013bb217442abaf; lp_models 2e3c4ff225345812a56e76cba2aa1ac4a667aaa73feb60c8dfc2532142c4790e; learning_progressions e49b9f9d3c1e14dafd0cf759dfa1b82553705489dc89142b6e549a1cd341d20a; receipts in client-recovery-dev012-frame2/checks and client-recovery-dev015-frame2/checks evidence indexes.`
`Next Action`: `On Tester RESUME, reload STATE/frame/plan/report, reconcile the corrected formal tests and scoped assessment, rerun affected checks, and stop before DEV-024 under STEPWISE. DEV-012 and DEV-015 are DONE; restore the approved remaining DEV-024/025/022 assignment with no duplicate plan approval.`

Save the interrupted overall Developer assignment before routing. Push nested Frame 2, From/ResumeAt DEVELOPING, Owner TESTING, FailureType VERIFICATION, RerunThrough NONE; preserve SCOPING-owned Frame 1. Tester decides the bounded correction and whether new formal cases for nextUnreturnedPath, the first-path error IDs and compact metadata belong in this assessment. Suggested commit: feat(progressions): stop paths at size limit with next unreturned path.
