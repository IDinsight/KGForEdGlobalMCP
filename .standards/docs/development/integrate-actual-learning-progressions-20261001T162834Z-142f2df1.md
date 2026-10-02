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
`Acceptance`: `AC-005, AC-009, AC-010, AC-012, AC-018`

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
`Acceptance`: `AC-006, AC-007, AC-009, AC-010, AC-012`

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

- Approval: user approved the revised 17-step plan and persisted tony style, explicitly directed DEV-001, and subsequently authorized DEV-002, DEV-003, DEV-004, DEV-005, DEV-023, DEV-012 and DEV-013. Style is locked for this cycle; STEPWISE pauses remain in effect.
- Entry: STANDARD/BROWNFIELD, DEVELOPING from Architect; no recovery frames, baseline-reconciliation entries or outstanding obligations. Initial workflow check passed. DEV-001 through DEV-005, DEV-023, DEV-012 and DEV-013 are DONE with persisted implementation feedback; STEPWISE is paused before DEV-014; no later step has started.
- Sufficiency: scope/design establish LP meanings, attribution, eligibility, package/profile revisions, normalization/partition algorithm, five query schemas, selectors/facets, bounds/cursors/completeness/errors, rights/resources, prompt workflows, removal and operational boundaries. Existing package/catalog/GraphStore/standard selection/resource/prompt/CLI machinery supports the chosen boundaries. Helper/module factoring remains reversible Developer work.
- STEPWISE: explicit approval covers this plan and user style tony. First approval locks that style. Execute exactly one dependency-ready step, record its outcome/self-check, then persist a continuation blocker and wait. Verification remains AFTER_IMPLEMENTATION, independent of these pauses.
- Preflight: all 23 required files are present for each of six source mappings (138 files, 933,392,640 bytes total), with no selected source symlinks. Copy-time exact hashes and edge reconciliation remain DEV-001 work; this preflight is not copy/acceptance evidence. The local backend Python environment exists.
- Plan revision: user requested replacing the legacy data/input_artifacts sets and build specifications. DEV-023 runs after DEV-005 and before DEV-012, preserving the architecture-prescribed raw-copy location and accepted-package boundaries. The revised 17-step plan was explicitly approved before DEV-001 began.
- Preserve source files and old sealed package/profile identities. Raw preparation copies stay outside runtime/distribution roots. Required runtime evidence is retained in accepted packages. During schema migration the incomplete development checkout may not bootstrap until replacement activation; do not deploy partial work or introduce legacy decoders/aliases to hide that boundary.
- Developer owns production implementation and executable integration/CI commands, not formal test suites or user documentation. Use local temporary/ad hoc implementation sanity checks; Tester creates meaningful offline formal cases and owns AC-023 through AC-025 evidence. Architecture requests for synthetic cases are exercised as implementation feedback here and independently formalized by Tester. AC-020 is established by Architect; AC-026/AC-027 remain Documenter-owned, supported by these persisted contracts/receipts/actual evidence.
- Identifier gaps are retained: the ID tool reserved numbers referenced in the draft before those headings were written. Preserve existing step identities; dependency order is the heading order, not an assumption of contiguous numbering.
- No live LLM/paid-service calls, producer/checker regeneration, model sampling, deployed endpoint changes or publication. Existing LC/comparison generated-origin evidence stays intact.
- Resume: DEV-001 through DEV-005, DEV-023, DEV-012 and DEV-013 are DONE. Next approved dependency-ready step is DEV-014; user continuation is required before starting it. Re-read bounded builds-only BFS traversal, branching/merging, upstream orientation, depth/frontier/work/byte bounds and scopeComplete/graphExhausted contracts; reuse existing GraphStore label adjacency and DEV-012/DEV-013 route/selector/rights/evidence/model helpers with accepted DEV-023 rebuilt runtimes. Maintained data/input_artifacts now rebuild the same six replacements directly; isolated rebuilt packages are under data/source_artifacts/learning_progressions/rebuilt_packages. Keep all source/prepared/accepted packages and version 1.0 configs intact; activation/retirement remains DEV-017. No later step has started.
- Full handoff requires all steps DONE, locked style, satisfactory self-checks, resolved owned blockers/obligations and workflow check. Save current identities and actual evidence for a separate independent Tester chat. Do not fabricate tests or claim formal acceptance based on Developer checks.
