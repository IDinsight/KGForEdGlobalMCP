# Comparison tool

`compare_framework_evidence` assembles deterministic, independently bounded evidence
from two through eight frameworks. It does not merge source graphs and does not create
an official alignment.

For workflow guidance, see [Compare framework evidence](../guides/comparison.md).

## Request variants

The request is selected by `mode` and shares the following fields.

### Common fields

| Field                    | Type          | Default / bound | Meaning                                              |
|--------------------------|---------------|-----------------|------------------------------------------------------|
| `frameworkIds`           | array[string] | required; 2-8   | Distinct framework families to compare               |
| `snapshotIds`            | array[string] | empty; max 8    | Optional exact snapshots                             |
| `includeContextPaths`    | boolean       | true            | Attach bounded hierarchy context to retained matches |
| `includeGroupings`       | boolean       | false           | Permit `Standard Grouping` candidates                |
| `localGradeLabels`       | array[string] | empty; max 64   | Shared exact local grade/stage filters               |
| `normalizedGrades`       | array[string] | empty; max 64   | Shared normalized grade facets                       |
| `maxMatchesPerFramework` | integer       | 5; 1-10         | Independent candidate quota per framework            |

Framework IDs, snapshot IDs, and grade filters must not contain duplicate exact values.
When exact snapshots are supplied, selection must resolve consistently to the selected
frameworks; otherwise the tool returns `invalid_comparison_selection`.

## Text mode

```json
{
  "request": {
    "mode": "text",
    "query": "length measurement",
    "match": {
      "matchMode": "tokens",
      "operator": "all"
    },
    "frameworkIds": [
      "nigeria-nerdc-mathematics-primary-1-3",
      "rwanda-reb-mathematics-lower-primary-1-3"
    ],
    "includeContextPaths": true,
    "maxMatchesPerFramework": 5
  }
}
```

The `query` accepts at most 512 characters and at most 32 normalized lexical tokens.
`match` uses the same token or exact-phrase contract as `search_standards`.

## Exact-code mode

```json
{
  "request": {
    "mode": "code_exact",
    "query": "<statement-code>",
    "frameworkIds": ["<framework-a>", "<framework-b>"],
    "maxMatchesPerFramework": 5
  }
}
```

## Prefix-code mode

```json
{
  "request": {
    "mode": "code_prefix",
    "query": "<code-prefix>",
    "frameworkIds": ["<framework-a>", "<framework-b>"],
    "maxMatchesPerFramework": 5
  }
}
```

Code queries are limited to 256 characters. Code-mode availability is evaluated
independently for each selected package.

## Independent package processing

For every selected framework, the service:

1. resolves one accepted snapshot and Academic Standards package;
2. resolves the package-bound interpretation profile;
3. executes one package-local search with the same requested query and filters;
4. retains that package's original ranking, warnings, result bound, and cursor;
5. retrieves exact standards for retained hits; and
6. optionally attaches bounded hierarchy context.

One package's ranking or capability limitation does not change another package's
retrieval behavior.

## Result contract

The result contains:

| Field             | Meaning                                                   |
|-------------------|-----------------------------------------------------------|
| `request`         | Canonical resolved comparison request                     |
| `sections`        | One package-local evidence section per selected framework |
| `warnings`        | Canonically aggregated comparison warnings                |
| `disclosures`     | Fixed interpretation disclosures                          |
| `epistemicStatus` | `deterministic_derived`                                   |

Sections are returned in canonical framework/snapshot/package identity order.

Each `sections[]` item includes:

- framework, snapshot, graph-package, and profile identity;
- source metadata and local grades/stages;
- normalized grades;
- hierarchy, language, rights, source-role, and code-search policy;
- comparison dimensions and known source anomalies;
- required profile disclosures;
- retained `matches`;
- original package search warnings;
- comparison-specific warnings; and
- package-local `hasMore` / `nextCursor` state.

Each match has:

- the original `searchHit`;
- an exact `standard` result;
- `retrievalStatus: retrieval_candidate`; and
- optional bounded `context` plus `contextComplete`.

## Comparison warning codes

```text
code_search_unsupported
context_incomplete
no_matches
unresolved_evidence_present
```

`code_search_unsupported` is section-local. It allows comparison evidence to preserve a
package capability limitation without pretending that another package shares the same
limitation.

## Fixed disclosures

The result always carries disclosures that establish the main interpretation boundary:

- normalized grades are retrieval facets, not international equivalence;
- `hasChild` is structural, not progression or prerequisite evidence;
- standards do not prove learner mastery;
- code, identifier, grade, hierarchy, or text similarity does not establish official
  equivalence;
- cross-framework matches are exploratory retrieval evidence;
- generated comparative conclusions are model-inferred; and
- rights, attribution, and provenance remain package-local.

!!! danger "Do not promote retrieval evidence to official alignment"
    A result may support a human or model-authored comparison, but the server does not
    create an alignment, mapping, equivalence assertion, endorsement, or grade-equivalence
    record.

## Common errors

| Error code                     | Typical cause                                                           |
|--------------------------------|-------------------------------------------------------------------------|
| `invalid_comparison_selection` | Framework/snapshot selection cannot form the requested exact comparison |
| `framework_not_found`          | A selected framework or snapshot is unavailable                         |
| `capability_unavailable`       | Required package behavior cannot be performed                           |

Search limitations that can be represented as evidence are generally surfaced as
warnings inside the appropriate framework section rather than as cross-framework
inference.

---

**Next:** [Progression tool](progression-tool.md)
