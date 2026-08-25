# Progression tool

`collect_progression_evidence` returns a bounded, deterministic candidate set for
reviewing possible progression across explicit grade scopes in one framework.

It collects evidence only. It does not assert a prerequisite, learning sequence, or
learning progression.

For workflow guidance, see [Collect progression evidence](../guides/progression.md).

## Request

| Field              | Type           | Default / bound            | Meaning                                                  |
|--------------------|----------------|----------------------------|----------------------------------------------------------|
| `frameworkId`      | string         | required                   | Exact framework family                                   |
| `snapshotId`       | string or null | null                       | Exact snapshot or unique-current routing                 |
| `topicOrStandard`  | string         | required; 1-512 characters | Topic, code, or exact identifier selected by `focusMode` |
| `focusMode`        | enum           | `topic`                    | How to interpret `topicOrStandard`                       |
| `localGradeLabels` | array[string]  | empty; max 32              | Exact source-facing grade/stage scopes                   |
| `normalizedGrades` | array[string]  | empty; max 32              | Normalized grade retrieval facets                        |
| `candidateLimit`   | integer        | 8; 2-20                    | Hard maximum retained candidate count                    |

At least one `localGradeLabels` or `normalizedGrades` value is required. Values must be
unique and nonblank.

### Focus modes

```text
topic
statement_code
node_id
case_identifier_uuid
case_identifier_uri
```

`statement_code` remains subject to the selected package's code policy.

### Topic example

```json
{
  "request": {
    "frameworkId": "ghana-nacca-primary-english-language-basic-1-3",
    "focusMode": "topic",
    "topicOrStandard": "story structure",
    "localGradeLabels": ["BASIC 1", "BASIC 2", "BASIC 3"],
    "candidateLimit": 8
  }
}
```

### Exact-anchor example

```json
{
  "request": {
    "frameworkId": "<framework-id>",
    "focusMode": "node_id",
    "topicOrStandard": "<node-id>",
    "normalizedGrades": ["1", "2", "3"],
    "candidateLimit": 8
  }
}
```

## Scope validation and canonicalization

Requested grade values are validated against the selected accepted package. Retained
scope values are then placed in package-declared canonical order rather than caller
input order.

The response preserves both local source-facing labels and normalized retrieval facets.
Normalized grades remain discovery aids, not assertions of grade equivalence.

## Candidate discovery

The service can discover candidates through the selected focus plus grade-scoped search
and hierarchy evidence. It deduplicates candidates by exact node identity before applying
the hard retained-candidate bound.

Every retained candidate records its `discoveryMethods`, so downstream reasoning can see
how the node entered the candidate set instead of treating all candidates as equivalent
in provenance.

## Result contract

The result contains:

| Field                      | Meaning                                                        |
|----------------------------|----------------------------------------------------------------|
| `package`                  | Exact accepted graph package                                   |
| `sourceMetadata`           | Exact snapshot source metadata                                 |
| `request`                  | Canonical resolved request summary                             |
| `discoveredCandidateCount` | Unique candidates discovered before selection                  |
| `retainedCandidateCount`   | Candidates retained after deterministic selection              |
| `excludedCandidateCount`   | Candidates omitted by the bound                                |
| `excludedCandidateNodeIds` | Exact IDs of excluded candidates                               |
| `candidateLimitApplied`    | Whether the candidate bound excluded any discovered candidates |
| `discoveryComplete`        | Whether evidence discovery completed without limiting warnings |
| `scopeCoverage`            | Discovered and retained counts for every requested grade scope |
| `selectionPolicy`          | Deterministic selection-policy evidence                        |
| `retainedCandidates`       | Up to 20 selected candidate records                            |
| `warnings`                 | Progression-evidence warnings                                  |

Each retained candidate includes:

- exact `node` source evidence;
- local and normalized `facets`;
- `retrievalStatus: retrieval_candidate`;
- `selectionRank`;
- `matchedLocalGradeLabels` and `matchedNormalizedGrades`;
- one or more `discoveryMethods`;
- optional originating `searchHit`; and
- compact bounded hierarchy `context`.

The compact context reports ancestor and root-path completion independently and retains
non-empty relationship-resolution statuses.

## Warning codes

```text
context_incomplete
discovery_incomplete
no_candidates
scope_not_retained
scope_without_candidates
search_warning
```

A warning does not authorize the client to fill missing evidence by inference. Preserve
it in any downstream progression review.

## Candidate limit

`candidateLimit` is a hard server-enforced retained-candidate maximum from 2 through 20.
The response records whether the limit was applied and names excluded node IDs.

Increasing the bound changes the requested evidence set and should be treated as a new
request, not as continuation pagination.

## No progression assertion

!!! danger "Evidence order is not a source-authored progression"
    Grade-scoped candidate collection does not prove that one standard is prerequisite
    to another, that a learner should encounter them in a particular order, or that the
    framework defines a learning progression across them.

Use the `inferred_progression_hypothesis` prompt when you want the host model to perform
an explicitly labeled model inference over this evidence.

## Common errors

| Error code               | Typical cause                                    |
|--------------------------|--------------------------------------------------|
| `framework_not_found`    | Selected framework or snapshot is unavailable    |
| `standard_not_found`     | Exact focus identifier cannot be resolved        |
| `capability_unavailable` | Requested focus/search capability is unavailable |

Invalid grade scopes or missing required scope values can also fail strict request or
domain validation before evidence collection begins.

---

**Next:** [Resources and URI templates](resources.md)
