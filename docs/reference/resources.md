# Resources and URI templates

The resource surface provides rights-aware, read-only access to accepted metadata,
exact graph records, provenance, and a closed set of manifest-declared artifacts.

For task-oriented guidance, see [Read resources and provenance](../guides/resources.md).

## Fixed resource

| Name      | URI                  | MIME type          | Representation             |
|-----------|----------------------|--------------------|----------------------------|
| `catalog` | `kgfegmcp://catalog` | `application/json` | Deterministic derived JSON |

The catalog resource returns the complete accepted package catalog.

## Resource templates

| Name                     | URI template                                                                                | Registered MIME type                                                                        |
|--------------------------|---------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| `framework`              | `kgfegmcp://framework/{framework_id}`                                                       | `application/json`                                                                          |
| `package_manifest`       | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/manifest`                       | `application/json`                                                                          |
| `validation_report`      | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/validation`                     | `application/json`                                                                          |
| `unresolved_items`       | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/unresolved`                     | `application/json`                                                                          |
| `interpretation_profile` | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/interpretation-profile`         | `application/json`                                                                          |
| `manifest_artifact`      | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/artifact/{artifact_name}`       | `application/octet-stream` at registration; actual approved MIME comes from artifact policy |
| `standard`               | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/standard/{node_id}`             | `application/json`                                                                          |
| `standard_provenance`    | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/standard/{node_id}/provenance`  | `application/json`                                                                          |
| `standard_learning_components` | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/standard/{node_id}/learning-components` | `application/json`                                                                    |
| `learning_component`     | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/learning-component/{node_id}`   | `application/json`                                                                          |
| `learning_component_provenance` | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/learning-component/{node_id}/provenance` | `application/json`                                                          |
| `relationship`           | `kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/relationship/{relationship_id}` | `application/json`                                                                          |

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

| Resource family                                                  | Main access requirement                                                                                |
|------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| Catalog, framework, manifest, validation, interpretation profile | Public metadata                                                                                        |
| Unresolved items                                                 | Approved or provisionally approved rights review + full-text permission                                |
| Standard, standard provenance, relationship                      | Approved or provisionally approved rights review + full-text permission + standard-resource permission |

For rights-gated content, approved review states are:

```text
approved
provisional_operator_approved
```

Other review states do not satisfy the reviewed-content gate.

## Manifest artifacts

A manifest declaration is necessary but not sufficient for generic artifact exposure.
The server uses a closed logical-name policy.

| Logical name              | MIME type              | Access class      |
|---------------------------|------------------------|-------------------|
| `validationReport`        | `application/json`     | `public_metadata` |
| `learningComponentSummary` | `application/json`    | `public_metadata` |
| `unresolvedItems`         | `application/json`     | `full_text`       |
| `learningComponentDedupGroups` | `application/json` | `full_text`       |
| `academicStandardsBundle` | `application/json`     | `bulk_content`    |
| `entityProvenance`        | `application/json`     | `bulk_content`    |
| `nodes`                   | `application/x-ndjson` | `bulk_content`    |
| `relationships`           | `application/x-ndjson` | `bulk_content`    |
| `relationshipsHasChild`   | `application/x-ndjson` | `bulk_content`    |
| `standardsFramework`      | `application/json`     | `bulk_content`    |
| `standardsFrameworkItems` | `application/x-ndjson` | `bulk_content`    |
| `learningComponentsBundle` | `application/json`    | `bulk_content`    |
| `learningComponentProvenance` | `application/json` | `bulk_content`    |

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
content.

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

Unexpected resource exceptions are masked as:

```text
internal_error: The server could not read the resource.
```

---

**Next:** [Prompts](prompts.md)
