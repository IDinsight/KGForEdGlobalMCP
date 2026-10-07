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
| `academicStandardsBundle`      | `application/json`     | `bulk_content`    |
| `entityProvenance`             | `application/json`     | `bulk_content`    |
| `nodes`                        | `application/x-ndjson` | `bulk_content`    |
| `relationships`                | `application/x-ndjson` | `bulk_content`    |
| `relationshipsHasChild`        | `application/x-ndjson` | `bulk_content`    |
| `standardsFramework`           | `application/json`     | `bulk_content`    |
| `standardsFrameworkItems`      | `application/x-ndjson` | `bulk_content`    |
| `learningComponentsBundle`     | `application/json`     | `bulk_content`    |
| `learningComponentProvenance`  | `application/json`     | `bulk_content`    |

LP artifact policies extend this closed list:

| Logical names                                                                                                                                                       | Access class                                                               |
|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| `learningProgressionValidation`, `learningProgressionProvenanceIndex`, `learningProgressionNormalization`                                                           | `public_metadata`                                                          |
| `learningProgressionUnresolved`                                                                                                                                     | `full_text`                                                                |
| `learningProgressionBuildsTowards`, `learningProgressionRelatesTo`, `learningProgressionProvenance`, `learningProgressionSummary`, `learningProgressionFinalClaims` | `bulk_content`                                                             |
| `learningProgressionProvenanceShard00` … `63`                                                                                                                       | `bulk_content`, only when present in both the validated index and manifest |

The public LP summary is a sanitized projection with its own content hash, distinct from the unchanged original generation-summary artifact/hash. It excludes candidate text, rationale, private paths and model prompts. Unknown extra artifacts fail closed; a similar name prefix grants no access.

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

The provenance resource returns one accepted detailed provenance entry containing the
outer `nodeId`, `caseIdentifierUuid`, and retained provenance object.

## Learning progression resources

The existing relationship URI returns exact stored LP content. Its `/provenance` resource returns the complete original per-edge claim/judgment/trace, including rationale, confidence, warnings, candidate evidence/references and source/config/content/model/producer/checker hashes. It requires reviewed rights, full-text and standard-resource permission; it does not grant bulk access.

The server resolves an accepted ID to its validated partition without a caller-selected path. Metadata identifies canonical returned content hash and original map, selected partition, index, delivery/manifest and exact package/profile identity. The original map is retained; one-edge reads do not require reading it wholesale.

The `/learning-progressions` summary reports availability, stored per-type counts, structural/process-only scope, retained candidate/claim/needs-review/unresolved counts and eligibility/coverage notices, plus artifact links. Missing denominators remain unknown. Accepted edge tables exclude unresolved/rejected/no-relation/needs-review claims. A zero warning-pair count does not erase individual edge warnings.

Defaults are 32 MiB source-read and 8 MiB returned content. Lower operator limits still apply to partition reads; denied/oversized evidence produces an explicit error, never fabricated or silently clipped full provenance. Query results have separate tool-result ceilings (1 MiB and 100,000 characters for text plus structured output). See [LP tool reference](progression-tool.md).

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
