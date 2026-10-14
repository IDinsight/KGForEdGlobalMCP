# Resources and URI templates

The resource surface provides rights-aware, read-only access to accepted metadata,
exact graph records, provenance, and a closed set of manifest-declared artifacts.

For task-oriented guidance, see [Read resources and provenance](../guides/resources.md).
Clients that cannot open resources directly can read the same content with the
[`read_evidence`](access-tools.md#read_evidence) tool.

## Fixed resource

| Name      | URI                  | MIME type          | Representation             |
|-----------|----------------------|--------------------|----------------------------|
| `catalog` | `kgfegmcp://catalog` | `application/json` | Deterministic derived JSON |

The catalog resource returns the complete accepted package catalog.

## Resource templates

| Name                            | URI template                                                                                           | Registered MIME type                                                                        |
|---------------------------------|--------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| `framework`                     | `kgfegmcp://framework/{framework_id}`                                                                  | `application/json`                                                                          |
| `package_manifest`              | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/manifest`                                  | `application/json`                                                                          |
| `validation_report`             | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/validation`                                | `application/json`                                                                          |
| `unresolved_items`              | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/unresolved`                                | `application/json`                                                                          |
| `interpretation_profile`        | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/interpretation-profile`                    | `application/json`                                                                          |
| `manifest_artifact`             | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/artifact/{artifact_name}`                  | `application/octet-stream` at registration; actual approved MIME comes from artifact policy |
| `standard`                      | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/standard/{node_id}`                        | `application/json`                                                                          |
| `standard_provenance`           | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/standard/{node_id}/provenance`             | `application/json`                                                                          |
| `standard_learning_components`  | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/standard/{node_id}/learning-components`    | `application/json`                                                                          |
| `learning_component`            | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/learning-component/{node_id}`              | `application/json`                                                                          |
| `learning_component_provenance` | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/learning-component/{node_id}/provenance`   | `application/json`                                                                          |
| `relationship`                  | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/relationship/{relationship_id}`            | `application/json`                                                                          |
| `relationship_provenance`       | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/relationship/{relationship_id}/provenance` | `application/json`                                                                          |
| `learning_progressions`         | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/learning-progressions`                     | `application/json`                                                                          |

The three learning-component templates mirror the standards pair. They duplicate
`get_learning_component` and `get_learning_components_for_standard` deliberately: a
resource serves clients driven by a resource browser, while the tool works everywhere.
`learning_component_provenance` is keyed by outer node identifier rather than CASE UUID,
because a learning component carries no CASE identity.

Identifier values constructed by the server are percent-encoded as individual URI path
segments.

## Resource representations

Every returned resource document carries metadata identifying its representation as:

```text
deterministic_derived
raw_source
```

`ResourceMetadata` includes:

- `canonicalUri`;
- `resourceKind`;
- `representation`;
- `mimeType`;
- `byteLength`;
- `contentSha256`;
- applicable framework, snapshot, graph-package, graph-type, and profile identity; and
- `sourceArtifacts` with logical name, checksum, size, and package identity evidence.

The server never exposes local filesystem paths as resource metadata.

## Rights classes

Dedicated resource families apply the following policy:

| Resource family                                                              | Main access requirement                                                                                |
|------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| Catalog, framework, manifest, validation, interpretation profile, LP summary | Public metadata                                                                                        |
| Unresolved items                                                             | Approved or provisionally approved rights review + full-text permission                                |
| Standard, standard provenance, relationship, per-edge LP provenance          | Approved or provisionally approved rights review + full-text permission + standard-resource permission |

For rights-gated content, approved review states are:

```text
approved
provisional_operator_approved
```

Other review states do not satisfy the reviewed-content gate.

## Manifest artifacts

A manifest declaration is necessary but not sufficient for generic artifact exposure.
The server uses a closed logical-name policy.

| Logical name                   | MIME type              | Access class      |
|--------------------------------|------------------------|-------------------|
| `validationReport`             | `application/json`     | `public_metadata` |
| `learningComponentSummary`     | `application/json`     | `public_metadata` |
| `unresolvedItems`              | `application/json`     | `full_text`       |
| `learningComponentDedupGroups` | `application/json`     | `full_text`       |
| `entityProvenance`             | `application/json`     | `bulk_content`    |
| `nodes`                        | `application/x-ndjson` | `bulk_content`    |
| `relationships`                | `application/x-ndjson` | `bulk_content`    |
| `standardsFramework`           | `application/json`     | `bulk_content`    |
| `learningComponentProvenance`  | `application/json`     | `bulk_content`    |

LP artifact policies extend this closed list:

| Logical names                                                                                             | Access class                                                               |
|-----------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| `learningProgressionValidation`, `learningProgressionProvenanceIndex`, `learningProgressionNormalization` | `public_metadata`                                                          |
| `learningProgressionUnresolved`                                                                           | `full_text`                                                                |
| `learningProgressionSummary`                                                                              | `bulk_content`                                                             |
| `learningProgressionProvenanceShard00` … `63`                                                             | `bulk_content`, only when present in both the validated index and manifest |

The public LP summary is a sanitized projection with its own content hash, distinct from the unchanged original generation-summary artifact/hash. It excludes candidate text, rationale, private paths and model prompts. Unknown extra artifacts fail closed; a similar name prefix grants no access. The `evidenceArchiveRecord` artifact has no exposure contract and is never served.

Archive-only evidence is not part of the package. A URI for one of those names, such as
`learningProgressionProvenance` or `academicStandardsBundle`, returns
`resource_not_found`, not `resource_access_denied`. See
[Runtime files and archived evidence](../data/graph-packages.md#runtime-files-and-archived-evidence).

`full_text` requires reviewed rights plus `allowFullText`.

`bulk_content` requires reviewed rights plus all of:

- `allowFullText`;
- `allowStandardResources`; and
- `allowBulkResource`.

An unknown logical artifact name fails closed with `resource_not_found` until an explicit
future exposure contract defines its access class and MIME type.

## Size policy

The resource layer enforces two independent limits:

- maximum source bytes the server may read for a resource; and
- maximum bytes the server may return.

The configured source-read limit must be greater than or equal to the return limit.
Requests exceeding either limit return `resource_access_denied` rather than partial
content. `read_evidence` applies these limits to the whole resource before returning any
window, so paging cannot be used to read a resource that is too large natively.

See [Environment variables](../operations/configuration.md) for configured limits.

## Exact standard and provenance resources

Standard and standard-provenance URIs use the package-local outer `nodeId` namespace:

```text
kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/standard/{node_id}
kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/standard/{node_id}/provenance
```

Use `get_standard` instead of a standard resource when you need to resolve by CASE UUID
or CASE URI.

The standard-provenance resource returns:

| Field                      | Content                                                                                       |
|----------------------------|-----------------------------------------------------------------------------------------------|
| `nodeId`                   | Outer node ID                                                                                 |
| `caseIdentifierUuid`       | CASE UUID used to find the entry                                                              |
| `provenance`               | The slim provenance item: the extraction record without `candidate_source_refs`, plus `original_item_sha256` |
| `sourceDocument`           | The source document object from the framework's provenance                                   |
| `attributionStatement`     | The package's `rights.attributionStatement`                                                   |
| `archivedProvenanceSha256` | SHA-256 of the full `as_entity_provenance.json` kept in the archive                          |

The learning-component-provenance resource returns `nodeId`, the slim component record
(kept whole, plus `original_component_sha256`), `sourceDocument` (`doc_key` and
`pdf_name`), `attributionStatement` and `archivedProvenanceSha256`.

`metadata.sourceArtifacts` for both cites the slim artifact and `evidenceArchiveRecord`.

## Learning progression resources

The existing relationship URI returns exact stored LP content. Its `/provenance` resource returns one edge's slim provenance record. It requires reviewed rights, full-text and standard-resource permission; it does not grant bulk access.

| Field                      | Content                                                                                       |
|----------------------------|-----------------------------------------------------------------------------------------------|
| `relationshipId`           | The edge ID                                                                                   |
| `provenance`               | The slim record (below)                                                                       |
| `archivedProvenanceSha256` | SHA-256 of the full original provenance map kept in the archive                               |
| `epistemicStatus`          | Always `llm_inferred`                                                                          |
| Notices                    | Generated-origin, confidence, coverage and semantic notices                                   |

The slim record keeps the edge's identity and endpoints, the full judgment (decision, direction, confidence, full rationale and all warnings), candidate warnings, the checker outcome, producer and checker trace hashes, model configuration and settings, attribution fields and every content hash. It leaves out three fields, which stay in the archive: the candidate evidence text (`claim.candidate.evidence`), the admissible decisions (`claim.candidate.admissible_decisions`) and the producer judgment (`claim.provenance.producer_judgment`). The producer judgment equals the final judgment when `checker_outcome` is `accepted`. When it is `corrected` (434 of the 8,080 edges in the current packages), the producer judgment is the model's judgment before the checker corrected it, and its decision, direction, confidence and rationale can differ from the final ones; that earlier judgment is now available only in the archive. Its `original_entry_sha256` is the SHA-256 of the full original record, so the edge can be matched to the archive.

The server resolves an accepted ID to its validated slim shard without a caller-selected path. `metadata.sourceArtifacts` lists the manifest, the selected slim shard, the slim index, `relationships` and `evidenceArchiveRecord`, with the returned content hash and exact package/profile identity. One-edge reads open a single shard.

The `/learning-progressions` summary reports availability, stored per-type counts, structural/process-only scope, retained candidate/claim/needs-review/unresolved counts and eligibility/coverage notices, plus links to the declared LP artifacts (normalization receipt, slim index, summary, unresolved and validation). Missing denominators remain unknown. Accepted edge tables exclude unresolved/rejected/no-relation/needs-review claims. A zero warning-pair count does not erase individual edge warnings.

Progression tool results cite four artifacts in `metadata.artifacts`: `learningProgressionProvenance`, `learningProgressionProvenanceIndex`, `nodes` and `relationships`. The first is the archived original provenance map, cited by its SHA-256 from the evidence archive record. Its URI is an identifier only: reading it returns `resource_not_found`. Use each edge's `provenanceUri` instead.

Defaults are 32 MiB source-read and 8 MiB returned content. Lower operator limits still apply to shard reads; denied/oversized evidence produces an explicit error, never fabricated or silently clipped provenance. Query results have separate tool-result ceilings (1 MiB and 100,000 characters for text plus structured output). See [LP tool reference](progression-tool.md).

## Relationship resource

```text
kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/relationship/{relationship_id}
```

This addresses one exact package-local relationship. A `hasChild` relationship remains
structural graph evidence and must not be rewritten as prerequisite or progression
semantics.

## Resource errors

| Error code               | Typical cause                                                        |
|--------------------------|----------------------------------------------------------------------|
| `resource_not_found`     | Resource, artifact, or approved exposure contract cannot be resolved |
| `resource_access_denied` | Rights, exposure class, or size policy blocks access                 |
| `framework_not_found`    | Framework/snapshot route is unavailable                              |

`read_evidence` adds `invalid_evidence_uri`, `unsupported_evidence_format`,
`evidence_result_too_large` and `invalid_cursor`; see
[its error table](access-tools.md#errors).

Unexpected resource exceptions are masked as:

```text
internal_error: The server could not read the resource.
```

---

**Next:** [Prompts](prompts.md)
