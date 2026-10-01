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

- Approval: user approved the revised 17-step plan and persisted tony style, explicitly directed DEV-001, and subsequently authorized DEV-002, DEV-003 and DEV-004. Style is locked for this cycle; STEPWISE pauses remain in effect.
- Entry: STANDARD/BROWNFIELD, DEVELOPING from Architect; no recovery frames, baseline-reconciliation entries or outstanding obligations. Initial workflow check passed. DEV-001 through DEV-004 are DONE with persisted implementation feedback; STEPWISE is paused before DEV-005. No later step has started.
- Sufficiency: scope/design establish LP meanings, attribution, eligibility, package/profile revisions, normalization/partition algorithm, five query schemas, selectors/facets, bounds/cursors/completeness/errors, rights/resources, prompt workflows, removal and operational boundaries. Existing package/catalog/GraphStore/standard selection/resource/prompt/CLI machinery supports the chosen boundaries. Helper/module factoring remains reversible Developer work.
- STEPWISE: explicit approval covers this plan and user style tony. First approval locks that style. Execute exactly one dependency-ready step, record its outcome/self-check, then persist a continuation blocker and wait. Verification remains AFTER_IMPLEMENTATION, independent of these pauses.
- Preflight: all 23 required files are present for each of six source mappings (138 files, 933,392,640 bytes total), with no selected source symlinks. Copy-time exact hashes and edge reconciliation remain DEV-001 work; this preflight is not copy/acceptance evidence. The local backend Python environment exists.
- Plan revision: user requested replacing the legacy data/input_artifacts sets and build specifications. DEV-023 runs after DEV-005 and before DEV-012, preserving the architecture-prescribed raw-copy location and accepted-package boundaries. The revised 17-step plan was explicitly approved before DEV-001 began.
- Preserve source files and old sealed package/profile identities. Raw preparation copies stay outside runtime/distribution roots. Required runtime evidence is retained in accepted packages. During schema migration the incomplete development checkout may not bootstrap until replacement activation; do not deploy partial work or introduce legacy decoders/aliases to hide that boundary.
- Developer owns production implementation and executable integration/CI commands, not formal test suites or user documentation. Use local temporary/ad hoc implementation sanity checks; Tester creates meaningful offline formal cases and owns AC-023 through AC-025 evidence. Architecture requests for synthetic cases are exercised as implementation feedback here and independently formalized by Tester. AC-020 is established by Architect; AC-026/AC-027 remain Documenter-owned, supported by these persisted contracts/receipts/actual evidence.
- Identifier gaps are retained: the ID tool reserved numbers referenced in the draft before those headings were written. Preserve existing step identities; dependency order is the heading order, not an assumption of contiguous numbering.
- No live LLM/paid-service calls, producer/checker regeneration, model sampling, deployed endpoint changes or publication. Existing LC/comparison generated-origin evidence stays intact.
- Resume: DEV-001 through DEV-004 are DONE. Next approved dependency-ready step is DEV-005; user continuation is required before starting it. Re-read fresh profile/prompt schema/version contracts, the complete LP acceptance/projection boundary and six-framework preparation receipts. Publish fresh configurations and build/accept/revalidate replacements in a separate root, preserving sealed baseline directories. Temporary DEV-004 packages were removed; no replacement has been retained or activated.
- Full handoff requires all steps DONE, locked style, satisfactory self-checks, resolved owned blockers/obligations and workflow check. Save current identities and actual evidence for a separate independent Tester chat. Do not fabricate tests or claim formal acceptance based on Developer checks.
