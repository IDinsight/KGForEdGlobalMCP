# Standards tools

This page specifies `search_standards`, `get_standard`, and
`get_standard_context`.

For task-oriented guidance, see [Search and retrieve standards](../guides/standards-search.md)
and [Navigate hierarchies](../guides/hierarchy-context.md).

## `search_standards`

Searches accepted package-local indexes using deterministic lexical or profile-governed
code matching.

The request is a discriminated union selected by `mode`.

### Common request fields

| Field                      | Type           | Default / bound                      | Meaning                                      |
|----------------------------|----------------|--------------------------------------|----------------------------------------------|
| `cursor`                   | string or null | null; 1-4096 characters when present | Opaque continuation cursor                   |
| `frameworkIds`             | array[string]  | empty; max 64                        | Framework selectors for federated search     |
| `includeGroupings`         | boolean        | false                                | Include normalized `Standard Grouping` nodes |
| `jurisdictions`            | array[string]  | empty; max 64                        | Jurisdiction filters                         |
| `languages`                | array[string]  | empty; max 64                        | Language filters                             |
| `limit`                    | integer        | 25; 1-100                            | Maximum hits on one page                     |
| `localGradeLabels`         | array[string]  | empty; max 64                        | Exact source-facing grade/stage filters      |
| `normalizedGrades`         | array[string]  | empty; max 64                        | Normalized grade retrieval facets            |
| `normalizedStatementTypes` | array[enum]    | empty; max 64                        | `Standard` or `Standard Grouping`            |
| `normalizedSubjects`       | array[string]  | empty; max 64                        | Normalized subject filters                   |
| `snapshotIds`              | array[string]  | empty; max 64                        | Exact snapshot selectors                     |
| `statementTypes`           | array[string]  | empty; max 64                        | Source statement-type filters                |
| `subjects`                 | array[string]  | empty; max 64                        | Source subject filters                       |

Duplicate exact values are rejected. If `normalizedStatementTypes` includes
`Standard Grouping`, `includeGroupings` must be true.

### Text mode

Required fields:

| Field   | Value                                                                    |
|---------|--------------------------------------------------------------------------|
| `mode`  | `text`                                                                   |
| `query` | Non-empty lexical query, max 512 characters and max 32 normalized tokens |
| `match` | Token or exact-phrase match policy                                       |

Token mode:

```json
{
  "request": {
    "mode": "text",
    "query": "structure story",
    "match": {
      "matchMode": "tokens",
      "operator": "all"
    },
    "frameworkIds": [
      "ghana-nacca-primary-english-language-basic-1-3"
    ],
    "includeGroupings": false,
    "limit": 25
  }
}
```

`operator` is `all` or `any`.

Exact phrase mode:

```json
{
  "request": {
    "mode": "text",
    "query": "structure of a story",
    "match": {
      "matchMode": "exact_phrase"
    },
    "frameworkIds": [
      "ghana-nacca-primary-english-language-basic-1-3"
    ]
  }
}
```

Text matching operates over normalized description text. It performs no stemming,
lemmatization, fuzzy search, embedding search, or hidden synonym expansion.

### Exact-code mode

```json
{
  "request": {
    "mode": "code_exact",
    "query": "B1.2.7.2.6",
    "frameworkIds": [
      "ghana-nacca-primary-english-language-basic-1-3"
    ],
    "limit": 25
  }
}
```

The code query is limited to 256 characters and must contain substantive content after
validation.

### Prefix-code mode

```json
{
  "request": {
    "mode": "code_prefix",
    "query": "B1.2.7",
    "frameworkIds": [
      "ghana-nacca-primary-english-language-basic-1-3"
    ],
    "limit": 25
  }
}
```

Prefix behavior is profile-governed and may be unavailable even when a package has some
statement codes.

!!! warning "Check capabilities before code search"
    Inspect `get_capabilities.packages[].implementedSearchModes` for the selected package.
    A generic request variant in the schema does not imply that every package supports it.

### Search result

`structuredContent` has three top-level fields:

| Field               | Meaning                                            |
|---------------------|----------------------------------------------------|
| `effectiveScope`    | Exact or federated package scope actually searched |
| `selectedSnapshots` | Exact accepted snapshots selected for the search   |
| `page`              | Hits, warnings, mode, count, and cursor state      |

Each `page.hits[]` entry contains:

- exact `node` source evidence;
- immutable `packageIdentity`;
- local and normalized `facets`;
- `retrievalMethod`;
- `epistemicStatus: retrieval_candidate`;
- deterministic `score` and scoring algorithm;
- `matchedTerms` and `matchedFields`;
- optional `codeMatch` scope/derivation evidence; and
- hit-local `warnings`.

The page also exposes package-level `warnings`, `returnedCount`, `hasMore`, and
`nextCursor`.

### Search warning codes

```text
code_prefix_unavailable
code_search_unavailable
derived_parent_code_multiple
derived_parent_code_not_found
multiple_code_matches
partial_code_coverage
text_search_unavailable
```

Warnings are evidence, not fatal errors. For example, a federated search can return hits
from packages that support a mode while also warning about packages that do not.

## `get_standard`

Returns one exact standard or grouping from one selected package.

### Request fields

| Field         | Type           | Default              | Meaning                                 |
|---------------|----------------|----------------------|-----------------------------------------|
| `frameworkId` | string or null | null                 | Framework family route                  |
| `snapshotId`  | string or null | null                 | Exact snapshot route                    |
| `graphType`   | enum           | `academic_standards` | Graph domain                            |
| `identifier`  | object         | required             | Explicit identifier namespace and value |

At least one of `frameworkId` or `snapshotId` is required.

#### Node ID

```json
{
  "request": {
    "frameworkId": "ghana-nacca-primary-english-language-basic-1-3",
    "identifier": {
      "identifierType": "node_id",
      "nodeId": "<node-id>"
    }
  }
}
```

#### CASE UUID

```json
{
  "request": {
    "frameworkId": "<framework-id>",
    "identifier": {
      "identifierType": "case_identifier_uuid",
      "caseIdentifierUuid": "<case-uuid>"
    }
  }
}
```

#### CASE URI

```json
{
  "request": {
    "frameworkId": "<framework-id>",
    "identifier": {
      "identifierType": "case_identifier_uri",
      "caseIdentifierUri": "<case-uri>"
    }
  }
}
```

The result contains `node`, `facets`, `package`, and `sourceMetadata`.

## `get_standard_context`

Returns direct and bounded hierarchy context for one exact outer `nodeId`.

### Request fields

| Field                    | Type           | Default / bound      | Meaning                                           |
|--------------------------|----------------|----------------------|---------------------------------------------------|
| `nodeId`                 | string         | required             | Exact package-local outer node ID                 |
| `frameworkId`            | string or null | null                 | Framework family route                            |
| `snapshotId`             | string or null | null                 | Exact snapshot route                              |
| `graphType`              | enum           | `academic_standards` | Graph domain                                      |
| `ancestorDepth`          | integer        | 16; 0-64             | Ancestor traversal depth                          |
| `childDepth`             | integer        | 1; 0-64              | Descendant depth when requested                   |
| `includeAllRootPaths`    | boolean        | true                 | Enumerate complete bounded root paths             |
| `includeDescendants`     | boolean        | false                | Include descendant traversal                      |
| `includeDirectChildren`  | boolean        | true                 | Include direct children                           |
| `includeUnresolved`      | boolean        | true                 | Retain relationship-resolution evidence           |
| `maxNodes`               | integer        | 250; 1-2000          | Node bound for ancestor/descendant traversal      |
| `maxPathNodeOccurrences` | integer        | 8192; 1-100000       | Aggregate node-occurrence bound across root paths |
| `maxPaths`               | integer        | 128; 1-1000          | Maximum root paths                                |
| `relationshipTypes`      | array[string]  | empty; max 1         | Optional explicit hierarchy relationship type     |

At least one of `frameworkId` or `snapshotId` is required.

```json
{
  "request": {
    "frameworkId": "ghana-nacca-primary-english-language-basic-1-3",
    "nodeId": "<node-id>",
    "includeAllRootPaths": true,
    "includeDirectChildren": true,
    "includeDescendants": false
  }
}
```

### Result fields

| Field                  | Meaning                                                 |
|------------------------|---------------------------------------------------------|
| `standard`             | Exact `get_standard`-equivalent evidence for the origin |
| `directParents`        | Direct parent nodes and authored relationships          |
| `directChildren`       | Direct children, or null when not requested             |
| `ancestors`            | Bounded ancestor traversal                              |
| `descendants`          | Bounded descendant traversal, or null                   |
| `rootPaths`            | Complete bounded root-to-origin paths, or null          |
| `relationshipStatuses` | Non-empty relationship-resolution statuses              |

Traversal results explicitly report `isComplete` and `truncationReason`. Node traversal
can truncate at `max_nodes`; root-path enumeration can truncate at `max_paths` or
`max_path_node_occurrences`.

!!! warning "Hierarchy is structural"
    Returned parents, children, ancestors, descendants, and root paths preserve source
    graph structure. They do not establish prerequisite, mastery, difficulty, or learning
    progression semantics.

## Common errors

| Error code                | Typical cause                                                         |
|---------------------------|-----------------------------------------------------------------------|
| `standard_not_found`      | Exact standard identifier is unavailable in the selected package      |
| `ambiguous_graph_node`    | Exact identifier resolves to more than one node                       |
| `graph_node_not_found`    | Context origin node is unavailable                                    |
| `unsupported_search_mode` | Requested search mode is not supported                                |
| `capability_unavailable`  | Selected package cannot perform a requested capability                |
| `invalid_cursor`          | Search continuation does not match the original request/catalog state |

---

**Next:** [Comparison tool](comparison-tool.md)
