# Errors, cursors, and limits

This page documents protocol-wide behavior shared across tools, resources, and prompts:
strict validation, lower-camel-case aliases, stable public errors, pagination cursors,
warning evidence, bounded traversal, and result compatibility blocks.

## Strict input validation

The FastMCP server is created with strict input validation enabled.

Request fields therefore need to match the published schema exactly. In particular:

- use lower-camel-case public aliases;
- send booleans as booleans, not strings;
- send integers as integers, not numeric strings;
- use declared enum values exactly;
- do not add undeclared fields; and
- respect collection, string, and integer bounds.

Example:

```json
{
  "request": {
    "frameworkId": "ghana-nacca-primary-english-language-basic-1-3",
    "limit": 25
  }
}
```

Do not send `"limit": "25"` or an unknown field and expect coercion.

## Public error translation

Expected application failures use stable error codes. The public message format is:

```text
<error_code>: <message>
```

When a recovery hint is available:

```text
<error_code>: <message> Next action: <recovery hint>
```

Internal structured error details are retained for diagnostics but are not exposed
blindly at MCP boundaries.

### Domain error codes

| Error code                         | Typical domain                                            |
|------------------------------------|-----------------------------------------------------------|
| `alignment_not_found`              | Requested derived alignment unavailable                   |
| `ambiguous_framework`              | Framework selector matches multiple eligible snapshots    |
| `ambiguous_graph_node`             | Exact identifier resolves to multiple graph nodes         |
| `capability_unavailable`           | Selected package does not provide requested behavior      |
| `catalog_error`                    | Catalog loading/lookup inconsistency                      |
| `configuration_error`              | Runtime settings cannot be resolved safely                |
| `delivery_property_decoding_error` | Delivery record cannot be decoded                         |
| `framework_not_found`              | Framework or snapshot route unavailable                   |
| `graph_node_not_found`             | Graph node unavailable                                    |
| `invalid_comparison_selection`     | Cross-framework selection is inconsistent                 |
| `invalid_cursor`                   | Pagination cursor malformed, stale, or request-mismatched |
| `jsonl_parsing_error`              | Package JSONL record invalid                              |
| `manifest_build_error`             | Pending manifest cannot be built safely                   |
| `package_validation_error`         | Graph package fails validation                            |
| `profile_validation_error`         | Interpretation profile invalid                            |
| `prompt_access_denied`             | Rights block generated-derivative prompt                  |
| `prompt_configuration_error`       | Prompt configuration invalid                              |
| `prompt_rendering_error`           | Prompt rendering fails safely                             |
| `resource_access_denied`           | Rights/exposure/size policy blocks a resource             |
| `resource_not_found`               | Resource cannot be resolved or exposed                    |
| `standard_not_found`               | Exact standard cannot be resolved                         |
| `unsupported_search_mode`          | Requested search mode is unsupported                      |

Some build-time errors above normally occur before the server is available; they share
the same typed domain hierarchy even though they are not typical interactive MCP errors.

## Unexpected errors are masked

Unexpected exceptions are logged internally with an incident identifier and replaced by
fixed public messages:

| Boundary | Public message                                               |
|----------|--------------------------------------------------------------|
| Tool     | `internal_error: The server could not complete the request.` |
| Resource | `internal_error: The server could not read the resource.`    |
| Prompt   | `internal_error: The server could not render the prompt.`    |

This prevents local paths, stack traces, or implementation details from leaking through
the MCP surface.

## Cursor behavior

Only `list_frameworks` and `search_standards` expose caller-visible continuation
cursors.

Cursors are:

- opaque;
- unpadded base64url text at the public validation boundary;
- limited to 4096 characters;
- checksum-protected by the service;
- bound to the exact cursor-free request; and
- bound to the relevant accepted catalog/search state.

When another page is available, the tool includes a compatibility text block with:

```text
continuationPolicy
continuationTool
cursorField
hasMore
immutableFields
mutableFields
nextCursor
nextRequest
```

The policy is `repeat_exact_request`. Submit `nextRequest` unchanged.

!!! warning "Only the cursor is mutable during continuation"
    Do not change `limit`, filters, framework selectors, snapshots, search mode, query, or
    match policy while reusing a cursor. Start a new request instead.

## Search warnings versus errors

Warnings preserve package capability or evidence limitations without necessarily
failing the whole operation.

Search warning codes:

```text
code_prefix_unavailable
code_search_unavailable
derived_parent_code_multiple
derived_parent_code_not_found
multiple_code_matches
partial_code_coverage
text_search_unavailable
```

Comparison warning codes:

```text
code_search_unsupported
context_incomplete
no_matches
unresolved_evidence_present
```

Progression warning codes:

```text
context_incomplete
discovery_incomplete
no_candidates
scope_not_retained
scope_without_candidates
search_warning
```

A warning is part of the evidence contract. Clients should preserve it rather than
silently converting uncertainty or capability limits into a confident conclusion.

## Search limits

| Limit                                     | Bound                    |
|-------------------------------------------|--------------------------|
| `list_frameworks.limit`                   | 1-100; default 25        |
| `search_standards.limit`                  | 1-100; default 25        |
| Text query length                         | 1-512 characters         |
| Text query tokens                         | max 32 normalized tokens |
| Code query length                         | 1-256 characters         |
| Framework/snapshot search selector arrays | max 64 each              |
| Search facet arrays                       | max 64 each              |

Text search is deterministic lexical retrieval. A zero-result page means only that the
supplied lexical expression did not match under the selected filters and packages.

## Context limits

`get_standard_context` accepts caller-controlled bounds:

| Field                    | Default | Range    |
|--------------------------|---------|----------|
| `ancestorDepth`          | 16      | 0-64     |
| `childDepth`             | 1       | 0-64     |
| `maxNodes`               | 250     | 1-2000   |
| `maxPaths`               | 128     | 1-1000   |
| `maxPathNodeOccurrences` | 8192    | 1-100000 |

Traversal completion is explicit.

Node traversal truncation uses:

```text
max_nodes
```

Root-path truncation can use:

```text
max_paths
max_path_node_occurrences
```

Do not treat an incomplete traversal as complete hierarchy evidence.

## Comparison limits

| Field                    | Bound               |
|--------------------------|---------------------|
| `frameworkIds`           | 2-8 distinct values |
| `snapshotIds`            | max 8               |
| `maxMatchesPerFramework` | 1-10; default 5     |
| Grade filter arrays      | max 64 each         |

The candidate quota is applied independently per framework; it is not one global
cross-framework ranking limit.

## Progression limits

| Field              | Bound            |
|--------------------|------------------|
| `candidateLimit`   | 2-20; default 8  |
| `topicOrStandard`  | 1-512 characters |
| `localGradeLabels` | max 32           |
| `normalizedGrades` | max 32           |

At least one local or normalized grade scope is required.

## Prompt limits

| Argument                             | Bound / default       |
|--------------------------------------|-----------------------|
| `practice_count`                     | 1-10; default 5       |
| `lesson_duration_minutes`            | 10-240; default 45    |
| `target_word_count`                  | 150-1500; default 500 |
| Prompt progression `candidate_limit` | 2-20; default 8       |
| Comparison `matches_per_framework`   | 1-10; default 5       |
| `local_context`                      | max 4000 characters   |
| `available_materials`                | max 2000 characters   |
| `learner_context`                    | max 2000 characters   |

Complex prompt collection arguments are entered as JSON arrays by MCP prompt clients.

## Tool result compatibility

Every tool result contains machine-readable `structuredContent` plus a deterministic
text summary. Paginated tools add model-visible continuation data. Some tools also add
optional `resource_link` content blocks.

The structured result is authoritative for programmatic use. Human-readable text and
links exist for compatibility and navigation and do not add source claims beyond the
structured evidence.

## Deterministic ordering

The runtime deliberately uses stable ordering for catalog pages, search hits, graph
neighbors, traversals, root paths, comparison sections, warnings, and resource links.

Stable ordering supports repeatable review, but it should not be interpreted as an
instructional priority unless the source itself explicitly supplies that meaning.

---

**Next:** [Runtime inputs](../data/index.md)
