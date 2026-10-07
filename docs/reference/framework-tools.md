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
| `availableGraphTypes`             | Primary (routing) graph types of accepted packages |
| `includedGraphTypes`              | Every graph type the accepted packages include |
| `implementedFeatures`             | Server features implemented by this build |
| `unavailableFeatures`             | Explicitly unsupported features           |
| `frameworkPromptOverlaysOptional` | Whether prompt overlays are optional      |
| `promptConfigSchemaVersion`       | Prompt configuration schema version       |
| `packages`                        | Per-package capability evidence           |

Each `packages[]` entry includes:

- `packageIdentity`, `rights`, `counts`, and `capabilities` (code coverage, text
  search, detailed provenance, multi-parent, official source roles, and
  learning-progression availability and provenance);
- `includedGraphTypes`;
- `implementedSearchModes`;
- `implementedLearningComponentSearchModes`;
- `searchIndex`, the package-local index counts: `codedNodeCount`,
  `lexicalDocumentCount`, `learningComponentDocumentCount`, and `tagVocabularySize`;
- `availableResourceKinds`;
- `availableResourceArtifacts`; and
- `traversalRelationshipType`.

Source metadata is reported by `list_frameworks` and `get_framework`. Build metadata
and the artifact table are in each package's `package_manifest` resource.

The text result prints `Routing graph types:` and `Included graph types:` for the server,
and for each package its included graph types and a `Learning progressions:` block with
`hasLearningProgressions`, `hasLearningProgressionProvenance`, `buildsTowards` and
`relatesTo` (stored counts).

Standards and learning-component modes are reported separately because they are
governed differently. Learning-component modes carry a `learning_component_` prefix so
a mode value is never ambiguous between the two surfaces:

```text
learning_component_text
learning_component_tag
learning_component_supported_code_exact
learning_component_supported_code_prefix
```

`learning_component_text` follows the package's `textSearch` capability, and the two
supported-code modes follow the same profile code coverage that governs
`code_exact` and `code_prefix`, because they match against the codes of the standards a
component supports. `learning_component_tag` needs neither, so it is always implemented;
a package whose components carry no tags returns no hits rather than reporting the mode
unavailable.

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
| `graphTypes`         | array           | empty; max 16                        | Match snapshots that include any listed type (`includedGraphTypes`) |
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
| `items`              | Returned accepted framework snapshots, summarised          |
| `returnedCount`      | Number of items on the page                                |
| `totalMatchingCount` | Total snapshots matching the request                       |
| `hasMore`            | Whether another page exists                                |
| `nextCursor`         | Opaque cursor for the next page, or null                   |

Each item carries the snapshot's identity, source metadata, relations,
`availableGraphTypes` (routing) and `includedGraphTypes`, and a summary of each graph
package: `packageIdentity`, `includedGraphTypes`, `capabilities`, `counts`,
`profileFacets`, `rights`, and `validationStatus`. Build timestamps, schema and manifest
versions, and the artifact table are in the package's `package_manifest` resource.

The text result prints, per snapshot, `Routing graph types:` and `Included graph types:`
lines, and one line per package that ends with
`learning_progressions=available|unavailable | builds_towards=<n> | relates_to=<n> |
validation=<status>`. The `graphTypes` filter matches included types, so
`["learning_progressions"]` finds every snapshot whose packages contain progressions
even though they route as `academic_standards`.

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

The result contains one `framework` object with the accepted snapshot's identity,
source metadata, relations, routing and included graph types, and the same package
summaries as `list_frameworks`. Its text prints, per package, `Included graph types:`,
`Learning progressions:` and `LP provenance:` flags, and adds
`learning_progressions[builds_towards=<n>, relates_to=<n>]` to the counts.

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

The result contains `package`, `sourceMetadata`, and `statistics`. `package` identifies
the package the record comes from and carries its rights: `packageIdentity` and
`rights`. The package's counts, capabilities, and profile facets are reported by
`get_framework`; build metadata and the artifact table are in the `package_manifest`
resource.

`statistics` includes:

- `totalFrameworkNodes`, `totalItemNodes`, `totalNodes`, and `totalRelationships`.
  These count the standards hierarchy only: `totalNodes` is the framework root plus
  the framework items, and `totalRelationships` excludes `supports`, `buildsTowards`
  and `relatesTo` edges. Learning components and their edges are counted in the
  `learningComponents` block below;
- local grade, node grade-level, normalized grade, statement-type, normalized
  statement-type, and relationship-type counts, all over the standards hierarchy only,
  so `supports` or LP edges never appear in the relationship-type or resolution counts;
- `codePresence` counts;
- `maximumStructuralDepth` and `minimumStructuralDepthCounts`;
- `multiParent` cardinality statistics;
- `unresolvedRelationships` counts; and
- `unreachableNodeCount`, counting nodes with no path to the framework root by any
  declared relationship; and
- `learningComponents`, a separate block reporting `totalLearningComponents`,
  `totalSupportsRelationships`, `multiStandardComponentCount`,
  `supportedStatementTypes`, `standardsWithoutComponents`, `tagVocabularySize`, the
  support-confidence range, and the components-per-standard and bridge-span
  distributions. `supportedStatementTypes` lists the source statement types that
  `supports` edges land on in this package; `standardsWithoutComponents` and the
  components-per-standard distribution count only items of those types, so grouping
  headings and node types the pipeline never decomposed are not reported as gaps.

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

Recognition in the enum is not the same as availability in the accepted catalog.
`availableGraphTypes` reports primary package routing types; these mixed packages still
route as `academic_standards`. `includedGraphTypes` (on capabilities, snapshots and
packages) lists every type the packages contain, and the `list_frameworks` `graphTypes`
filter matches it. Check `includedGraphTypes` and package flags
`hasLearningProgressions`/`hasLearningProgressionProvenance` for LP availability.
`statistics.learningProgressions` separately reports `buildsTowardsRelationships` and
`relatesToRelationships` plus those flags; hierarchy/LC blocks retain their meanings.

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
