# Learning component tools

This page specifies the four tools that search learning components, return one exact
component, and traverse the `supports` relationship in both directions.

A learning component is model-generated content decomposed from a published standards
framework item. It is never source-asserted curriculum. Components are kept separate
from standards at every level, so these tools never return a standards node, and
`search_standards` never returns a component.

## What a learning component carries

| Present | Absent |
|---------|--------|
| `description` | `caseIdentifierUUID` / `caseIdentifierURI` |
| `tags` | `gradeLevel` |
| `identityKey` | `statementCode` |
| `author`, `provider`, `license`, `attributionStatement` | `statementType` |

Grade, code, and statement taxonomy belong to published standards. They are recovered by
following the component's `supports` relationships, which every tool on this page does
for you.

`identityKey` is build-relative, not a citable identity. Two components with the same
`identityKey` and generator version are the same component; components built under
different dedup scopes are not comparable.

## `search_learning_components`

Searches components with package-governed modes and checksum-protected pagination.

### Modes

| Mode | Matches | Availability |
|------|---------|--------------|
| `learning_component_text` | Normalized description tokens or a contiguous phrase | Package `textSearch` capability |
| `learning_component_tag` | One controlled tag, matched whole | Always implemented |
| `learning_component_supported_code_exact` | Exact statement code of a supported standard | Profile code coverage |
| `learning_component_supported_code_prefix` | Delimiter-bounded code prefix of a supported standard | Profile code coverage plus prefix support |

Check `get_capabilities.packages[].implementedLearningComponentSearchModes` before using
a supported-code mode. See [Framework and capability tools](framework-tools.md).

### Request fields

Package selection is identical to `search_standards`, because these fields describe the
package rather than the node.

| Field | Type | Default / bound | Meaning |
|-------|------|-----------------|---------|
| `cursor` | string or null | null | Opaque continuation cursor |
| `frameworkIds` | array[string] | empty; max 64 | Framework family filters |
| `jurisdictions` | array[string] | empty; max 64 | Jurisdiction filters |
| `languages` | array[string] | empty; max 64 | Language-tag filters |
| `limit` | integer | 25; 1-100 | Maximum hits on one page |
| `mode` | enum | required | One of the four modes above |
| `query` | string | required | Text, tag, or code query |
| `snapshotIds` | array[string] | empty; max 64 | Exact snapshot filters |
| `subjects` | array[string] | empty; max 64 | Source subject filters |

`match` is required for `learning_component_text` only, and takes the same
`tokens`/`exact_phrase` shape as `search_standards`.

!!! note "No facet filters"
    There is no `normalizedGrades`, `statementTypes`, or `localGradeLabels` field. A
    component has no facets of its own, and a component supporting standards in several
    grades has no single grade to filter on.

```json
{
  "request": {
    "mode": "learning_component_tag",
    "query": "fractions",
    "jurisdictions": ["Ghana"],
    "limit": 25
  }
}
```

### Result fields

The result contains `effectiveScope`, `page`, and `selectedSnapshots`.

Each hit in `page.hits` reports:

- `node`, the exact learning component;
- `packageIdentity`, `retrievalMethod`, `epistemicStatus`, and `score`;
- `matchedFields` and `matchedTerms`;
- `matchedCodes`, the supported standards that satisfied the query, present only for the
  supported-code modes; and
- `supportedStandards`, **every** standard the component supports.

Each entry in `matchedCodes` and `supportedStandards` carries `nodeId`, `statementCode`,
`description`, `gradeLevels`, and `supportConfidence`. Grade and description are
projected from the supported standard, not stored on the component, so a component
supporting standards in several grades reports each grade against the standard that
declares it, and an uncoded standard is readable without a `get_standard` call:

```json
"supportedStandards": [
  {"nodeId": "76fe...", "statementCode": "B5.2.3.1.3", "description": "...", "gradeLevels": ["5"], "supportConfidence": 0.97},
  {"nodeId": "53d8...", "statementCode": "B6.2.3.1.3", "description": "...", "gradeLevels": ["6"], "supportConfidence": 0.97}
]
```

This is why the tool needs no grade filter: every hit already states the grades it
serves, so a caller narrows client-side from one response rather than one call per hit.

`supportedStandards` is always complete, including standards that carry no statement
code. A component supporting a coded and an uncoded standard reports both, so a bridge
is never flattened into a single-standard result.

!!! tip "Reading a bridge"
    When `supportedStandards` is longer than `matchedCodes`, the component also serves
    standards your query did not match — frequently in another grade. Of 230 components
    in the Ghana mathematics package, 37 support more than one standard and 34 of those
    span more than one grade.

### Mode semantics

Text mode matches exact normalized tokens. It performs no stemming, lemmatization, fuzzy
matching, or synonym expansion, so `fractions` does not match `fraction`.

Tag mode matches a whole normalized facet value. Partial words do not match, and
compatibility-equivalent forms such as `cm²` and `cm2` normalize to one key.

Supported-code modes match against the standards' codes, then return the components
supporting those standards. Components attach to the codes the pipeline decomposed, so
an exact query against a parent content standard returns nothing when only its children
carry components. Use the prefix mode for that question.

A zero-match page establishes only that this exact query did not match. It does not
establish that no component covers the concept.

## `get_learning_component`

Returns one exact component by node identifier, with the hierarchy placement of every
standard it supports.

### Request fields

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| `ancestorDepth` | integer | 16; 0-64 | Maximum hierarchy depth walked per supported standard |
| `frameworkId` | string | required | Framework family ID |
| `graphType` | enum | `academic_standards` | Graph domain to select |
| `nodeId` | string | required | Exact learning-component node identifier |
| `snapshotId` | string or null | null | Exact snapshot or unique-current routing |

Components take a node identifier only. They carry no CASE identity, so there is no
CASE UUID or URI form.

### Result

`node`, `package`, `sourceMetadata`, and `placements`. Each placement gives the
supported standard's `nodeId`, `statementCode`, `description`, `gradeLevels`,
`supportConfidence`, and
a labelled `hierarchyPath` from the framework root down to the standard.

```text
Mathematics Curriculum for Primary Schools (Basic 4 - 6) > BASIC 5 >
Strand 2. ALGEBRA > Sub-Strand 3: Variables and Equations > B5.2.3.1 > B5.2.3.1.3
```

The path is a list of labels, not embedded node records, which keeps a multi-standard
component small enough to read.

## `get_learning_component_context`

Returns one component together with the complete source record of every standard it
supports — statement type, grade levels, description, and support confidence.

Takes the same request fields as `get_learning_component`. Use it to traverse from
generated content back to the published curriculum it was decomposed from.

## `get_learning_components_for_standard`

Returns every component supporting one exact standard. This is the other direction of
the same edge.

### Request fields

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| `frameworkId` | string | required | Framework family ID |
| `graphType` | enum | `academic_standards` | Graph domain to select |
| `identifier` | object | required | Node ID, CASE UUID, or CASE URI |
| `snapshotId` | string or null | null | Exact snapshot or unique-current routing |

The standard accepts all three identifier forms, because a published standard does have
CASE identity.

```json
{
  "request": {
    "frameworkId": "ghana-nacca-primary-mathematics-basic-4-6",
    "identifier": {
      "identifierType": "case_identifier_uuid",
      "caseIdentifierUuid": "<uuid>"
    }
  }
}
```

### Result

`standard`, `components`, `package`, and `sourceMetadata`. Each component reports
`supportedStandards` — every standard it supports, not only the requested one — so a
component shared across grades is visible as such.

The text result names the standard's statement type and normalized statement type, so
an empty result can be read correctly: a grouping node, or a statement type the pipeline
never decomposed (compare `supportedStatementTypes` in `get_framework_statistics`),
legitimately has no components. Standard wording is printed whole; nothing in the
learning-component text output is truncated.

## Traversal directions

```text
search_learning_components ─┐
                            ├─> get_learning_component ──> placements
get_learning_components_for_standard                        (labelled paths)
        ▲                   │
        │                   └─> get_learning_component_context
        │                              │
        └────── supports edge ─────────┘
```

`search_*` is the entry point, `get_*` lands on one node, and `*_context` traverses.
The two directional tools are the two ends of the `supports` relationship: teaching
workflows read standard to components; grade and bridge analysis reads component to
standards.

## Common errors

| Error code | Typical cause |
|------------|---------------|
| `learning_component_not_found` | Identifier is unavailable or selects another node kind |
| `capability_unavailable` | Selected package does not implement the requested mode |
| `invalid_cursor` | Cursor is malformed, stale, or bound to a different request |
| `framework_not_found` | Framework or snapshot selector is unavailable |
| `ambiguous_framework` | Unique-current routing cannot select exactly one snapshot |

A cursor from `search_standards` is never valid for `search_learning_components`; the
two tools use disjoint mode values and separate cursor bindings.

See [Errors, cursors, and limits](protocol-behavior.md) for boundary behavior.

---

**Next:** [Comparison tool](comparison-tool.md)
