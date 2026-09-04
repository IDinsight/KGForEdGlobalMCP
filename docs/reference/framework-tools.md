# Framework and capability tools

This page specifies the four tools used to discover accepted framework snapshots,
inspect one framework, report runtime capabilities, and calculate structural package
statistics.

For workflow guidance, see [Discover frameworks](../guides/framework-discovery.md).

## `get_capabilities`

Returns the implemented server-wide surface and package-specific runtime capabilities.
This tool has no caller-supplied arguments.

### Request

```json
{}
```

### Result

`structuredContent` contains:

| Field                             | Meaning                                   |
|-----------------------------------|-------------------------------------------|
| `serverName`                      | Server display name                       |
| `toolNames`                       | Exact registered tool names               |
| `promptNames`                     | Exact registered prompt names             |
| `resourceUris`                    | Fixed resource URIs                       |
| `resourceUriTemplates`            | Parameterized resource templates          |
| `resourceRepresentations`         | `deterministic_derived` and `raw_source`  |
| `availableGraphTypes`             | Graph types present in accepted runtimes  |
| `implementedFeatures`             | Server features implemented by this build |
| `unavailableFeatures`             | Explicitly unsupported features           |
| `frameworkPromptOverlaysOptional` | Whether prompt overlays are optional      |
| `promptConfigSchemaVersion`       | Prompt configuration schema version       |
| `packages`                        | Per-package capability evidence           |

Each `packages[]` entry includes the accepted package and source metadata plus:

- `implementedSearchModes`;
- package-local search index metadata;
- `availableResourceKinds`;
- `availableResourceArtifacts`; and
- `traversalRelationshipType`.

!!! warning "Generic schemas do not authorize package-specific modes"
    The `search_standards` schema contains `text`, `code_exact`, and `code_prefix`
    variants, but a selected package may not implement every mode. Check
    `packages[].implementedSearchModes` first.

## `list_frameworks`

Lists accepted immutable framework snapshots with deterministic filtering and
checksum-protected pagination.

### Request fields

All fields are optional.

| Field                | Type            | Default / bound                      | Meaning                                 |
|----------------------|-----------------|--------------------------------------|-----------------------------------------|
| `cursor`             | string or null  | null; 1-4096 characters when present | Opaque continuation cursor              |
| `graphTypes`         | array           | empty; max 16                        | Graph-type filters                      |
| `isCurrent`          | boolean or null | null                                 | Current/non-current snapshot filter     |
| `issuingAuthorities` | array[string]   | empty; max 64                        | Issuing-authority filters               |
| `jurisdictionTypes`  | array[string]   | empty; max 64                        | Jurisdiction-type filters               |
| `jurisdictions`      | array[string]   | empty; max 64                        | Jurisdiction filters                    |
| `languages`          | array[string]   | empty; max 64                        | Language-tag filters                    |
| `limit`              | integer         | 25; 1-100                            | Maximum snapshots on one page           |
| `localGrades`        | array[string]   | empty; max 64                        | Exact source-facing grade/stage filters |
| `normalizedGrades`   | array[string]   | empty; max 64                        | Normalized retrieval-facet filters      |
| `query`              | string or null  | null; max 256 characters             | Catalog discovery text                  |
| `subjects`           | array[string]   | empty; max 64                        | Source subject filters                  |
| `validationStatus`   | array           | empty; max 8                         | Validation-state filters                |

Tuple-valued filters reject duplicate exact values. A supplied `query` must contain
non-whitespace text.

Current `validationStatus` values are:

```text
failed
passed
pending
quarantined
```

A minimal request is:

```json
{
  "request": {}
}
```

A filtered request is:

```json
{
  "request": {
    "graphTypes": ["academic_standards"],
    "jurisdictions": ["Ghana"],
    "subjects": ["Mathematics"],
    "validationStatus": ["passed"],
    "limit": 25
  }
}
```

### Result fields

| Field                | Meaning                                                    |
|----------------------|------------------------------------------------------------|
| `catalogSha256`      | Checksum of the accepted catalog state used for pagination |
| `items`              | Returned accepted framework snapshots                      |
| `returnedCount`      | Number of items on the page                                |
| `totalMatchingCount` | Total snapshots matching the request                       |
| `hasMore`            | Whether another page exists                                |
| `nextCursor`         | Opaque cursor for the next page, or null                   |

When `hasMore` is true, the result text also contains a complete `nextRequest`.
Submit that request unchanged.

## `get_framework`

Returns one exact snapshot or one uniquely current snapshot in a framework family.

### Request fields

| Field         | Type           | Required | Meaning                                                        |
|---------------|----------------|----------|----------------------------------------------------------------|
| `frameworkId` | string         | Yes      | Conceptual framework family ID                                 |
| `snapshotId`  | string or null | No       | Exact immutable snapshot; omission uses unique-current routing |

```json
{
  "request": {
    "frameworkId": "ghana-nacca-primary-mathematics-basic-4-6"
  }
}
```

For reproducible work, pin the exact snapshot:

```json
{
  "request": {
    "frameworkId": "ghana-nacca-primary-mathematics-basic-4-6",
    "snapshotId": "<exact-snapshot-id>"
  }
}
```

### Result

The result contains one `framework` object with the complete accepted snapshot,
including exact source metadata and accepted graph-package metadata.

If snapshot omission does not resolve to one unique current snapshot, the tool returns
an `ambiguous_framework` error rather than choosing silently.

## `get_framework_statistics`

Returns deterministic structural statistics for one Academic Standards package.

### Request fields

| Field         | Type           | Default              | Meaning                                  |
|---------------|----------------|----------------------|------------------------------------------|
| `frameworkId` | string         | required             | Framework family ID                      |
| `graphType`   | enum           | `academic_standards` | Graph domain to select                   |
| `snapshotId`  | string or null | null                 | Exact snapshot or unique-current routing |

```json
{
  "request": {
    "frameworkId": "india-cbse-science-learning-framework-classes-9-10",
    "graphType": "academic_standards"
  }
}
```

### Result fields

The result contains `package`, `sourceMetadata`, and `statistics`.

`statistics` includes:

- `totalFrameworkNodes`, `totalItemNodes`, `totalNodes`, and `totalRelationships`.
  `totalNodes` counts every node in the package, including learning components;
  `totalItemNodes` counts standards framework items only;
- local grade, node grade-level, normalized grade, statement-type, normalized
  statement-type, and relationship-type counts;
- `codePresence` counts;
- `maximumStructuralDepth` and `minimumStructuralDepthCounts`;
- `multiParent` cardinality statistics;
- `unresolvedRelationships` counts; and
- `unreachableNodeCount`, counting nodes with no path to the framework root by any
  declared relationship; and
- `learningComponents`, a separate block reporting `totalLearningComponents`,
  `totalSupportsRelationships`, `multiStandardComponentCount`,
  `standardsWithoutComponents`, `tagVocabularySize`, the support-confidence range, and
  the components-per-standard and bridge-span distributions.

Standards counts and learning-component counts are never combined. A learning component
is generated content and is excluded from every standards count.

These values describe graph structure. They do not establish curriculum quality,
coverage quality, instructional sequence, or difficulty.

## Graph types

The domain vocabulary recognizes these graph-type values:

```text
academic_standards
assessment
curriculum
learning_components
learning_progressions
reviewed_alignment
```

Recognition in the enum is not the same as availability in the accepted catalog. Use
`get_capabilities.availableGraphTypes` to determine what the running server actually
serves.

## Common errors

| Error code            | Typical cause                                                             |
|-----------------------|---------------------------------------------------------------------------|
| `framework_not_found` | Framework or snapshot selector is unavailable                             |
| `ambiguous_framework` | Unique-current routing cannot select exactly one snapshot                 |
| `invalid_cursor`      | Cursor is malformed, stale, or bound to a different request/catalog state |
| `catalog_error`       | Accepted catalog evidence is internally inconsistent                      |

See [Errors, cursors, and limits](protocol-behavior.md) for boundary behavior.

---

**Next:** [Standards tools](standards-tools.md)
