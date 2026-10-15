# Learning progression tools

Five read-only tools retrieve accepted, stored `buildsTowards` and `relatesTo` edges between standards in one framework/snapshot. They do not infer missing relationships. See the [guide and examples](../guides/progression.md) for educational use.

## Routing and selectors

Every call uses a nested `request` object with lower-camel-case fields. `frameworkId` is required; `snapshotId` is optional. Omission resolves the unique current package once. Pin the returned snapshot for subsequent calls and citations. A route cannot span packages or frameworks.

`identifier`, `sourceIdentifier`, `targetIdentifier` and discovery's `standardIdentifiers` accept these exact selectors:

| `identifierType`       | Value field          | Meaning                                            |
|------------------------|----------------------|----------------------------------------------------|
| `node_id`              | `nodeId`             | Exact outer standard node ID                       |
| `case_identifier_uuid` | `caseIdentifierUuid` | Exact CASE UUID                                    |
| `case_identifier_uri`  | `caseIdentifierUri`  | Exact CASE URI                                     |
| `statement_code`       | `statementCode`      | Exact profile-enabled code, at most 512 characters |

Ambiguous codes are rejected; codes are not globally unique identities. All selected endpoints must resolve to standards in the same package.

## Operations

| Tool                             | Required selection                                 | Optional fields and defaults                                                                                                                           |
|----------------------------------|----------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| `get_learning_progression`       | `relationshipId`                                   | Exact LP ID; returns one edge and both endpoints                                                                                                       |
| `get_standard_progressions`      | `identifier`                                       | `connectionKind`: `all`, `incoming_builds`, `outgoing_builds`, `related`; default `all`. `limit`: 25; `cursor`: null                                   |
| `search_learning_progressions`   | Framework route                                    | `relationshipTypes`: empty means both types; `standardIdentifiers`: empty; facet arrays: empty; `endpointScope`: `either`; `limit`: 25; `cursor`: null |
| `traverse_learning_progressions` | `identifier`                                       | `direction`: `downstream` or `upstream`, default downstream; `maxDepth`: 8; `maxNodes`: 100; `maxEdges`: 100                                           |
| `get_learning_progression_paths` | Distinct `sourceIdentifier` and `targetIdentifier` | Directed builds-only paths; `maxDepth`: 6 (1–16); `maxPaths`: 3 (1–20)                                                                                 |

Incoming builds support the selected target; outgoing builds describe what it supports. Related links are accessible from either endpoint, deduplicated by original relationship ID. Their source/target retain canonical stored orientation and imply no instructional direction. Traversal and paths use only `buildsTowards`, preserving each stored edge direction even when traversing upstream. `hasChild`, `supports` and `relatesTo` never become progression hops.

## Discovery filters

Arrays `localGradeLabels`, `normalizedGrades`, `statementTypes`, and `normalizedStatementTypes` each accept at most 32 unique, nonblank profile-valid values (each at most 512 characters). `relationshipTypes` permits `buildsTowards` and `relatesTo`; `standardIdentifiers` accepts at most 20 unique selectors. Unsupported facets, duplicates and missing/ambiguous selectors fail explicitly.

Values within a field are OR; fields and selected-standard membership are AND on one endpoint. `endpointScope` applies that whole conjunction:

- `either`: at least one endpoint matches;
- `both`: each endpoint matches;
- `source` or `target`: the stored endpoint matches.

Grade and type criteria cannot be split between endpoints to satisfy one conjunction. Results report effective filters, `resolvedStandardNodeIds`, and per-endpoint `sourceMatch`/`targetMatch`. Local grades preserve curriculum terminology; normalized grades are retrieval facets, not international equivalence. For `relatesTo`, source/target filtering uses canonical storage order.

## Ordinary text and structured content

Each tool returns one text block holding the complete result as canonical JSON (sorted keys, compact separators, Unicode preserved) and the same object as `structuredContent`. Parsing the text gives exactly the structured result: edges, endpoint statements, judgments, warnings, links, effective request, limits, counts, completeness and real cursor values. A client that reads only text loses nothing. There are no extra resource-link blocks; copy URIs from the JSON and read them natively or with [`read_evidence`](access-tools.md#read_evidence).

Every result also carries a `continuationNotice`. Collections tell the client to replay `page.nextRequest`; exact lookup, traversal and paths state that they have no continuation.

## Evidence and result fields

All results contain `request`, `metadata`, deduplicated `nodes` and `relationships`. `metadata.package.packageIdentity` pins framework/snapshot/package/profile identity and profile hash. `metadata.manifestUri` and `manifestSha256` identify the accepted manifest, which lists the checksum of every package file. `metadata.artifacts` lists only the four artifacts a result is derived from (`learningProgressionProvenance`, `learningProgressionProvenanceIndex`, `nodes`, `relationships`), as `artifactInventoryNotice` explains; read the manifest for the package's full file inventory. `learningProgressionProvenance` is the original provenance map, which is archived, not served: its SHA-256 comes from the package's evidence archive record, and reading its URI returns `resource_not_found`. Each edge's `provenanceUri` serves that edge's own record. The remaining `metadata` fields hold stored per-type totals, coverage notices, the result `limits`, and summary/validation/unresolved URIs. Edge rows retain IDs, author, provider, attribution, license and exact endpoints; `relationshipUri` and `provenanceUri` link to retained evidence. In the four tools that can return many edges, fields that every edge shares are stated once instead; see [Shared evidence in multi-edge results](#shared-evidence-in-multi-edge-results).

Endpoint `statementExcerpt` is capped at 2,048 characters, with `statementExcerpted` and `standardUri`. Judgment rationale is an excerpt of at most 512 characters; up to five warning excerpts of 512 characters retain total/omitted indicators. Read the edge's `provenanceUri` for the full rationale, confidence, all warnings, the checker outcome and producer/checker trace hashes; candidate evidence text stays in the archive and is not served. Confidence is a model judgment, not a calibrated probability of learner success.

Stored edges have `epistemicStatus: llm_inferred`: IDinsight-generated evidence, without publisher endorsement or certified pedagogy. `buildsTowards` means directional support for success, not a mandatory prerequisite. `relatesTo` means a conceptual or skill link without sequence or dependency. Derived traversals/paths have `deterministic_derived` status and cite original generated edges; they assert no new direct edge or compulsory teaching order.

## Shared evidence in multi-edge results

`get_standard_progressions`, `search_learning_progressions`, `traverse_learning_progressions` and `get_learning_progression_paths` use a compact form. Many fields are the same for every edge in a result: the attribution text, author, provider, license, the relationship description and the confidence notice, for example. These tools state such a field once, in the result's `sharedRelationshipEvidence` object, and leave it out of each edge entry. This saves client tokens and leaves room for more edges, or longer paths, within the size limit. Nothing is lost: every field can be restored. `get_learning_progression` returns a single edge and keeps the full form, with every field on the entry.

Only these fields can move to `sharedRelationshipEvidence`:

- `epistemicStatus`;
- `judgment.confidenceNotice`;
- in `relationship`: `attributionStatement`, `author`, `description`, `label`, `license`, `provider`, `relationshipType`, `sourceEntity`, `sourceEntityKey`, `sourceLabels`, `targetEntity`, `targetEntityKey` and `targetLabels`.

A field moves only when every edge in the result has the same, non-null value for it. Otherwise each entry keeps its own value. A null value is left out wherever it would appear. So on a page that mixes `buildsTowards` and `relatesTo` edges, `label`, `relationshipType` and `description` stay on each entry, and the other fields are still shared. All other fields always stay on each entry, even when two entries happen to share a value: relationship and endpoint IDs, `sourceExportOrder`, `resolutionStatus`, `supportConfidence`, confidence, rationale and warning excerpts and their flags, and both URIs.

`sharedRelationshipEvidence` is always present. It is `{}` when nothing is shared, which includes a result with no edges. Abridged, a CAPS `get_standard_progressions` page of outgoing `buildsTowards` edges looks like this (only the first entry is shown, and `…` marks text cut for this page):

```json
{
  "sharedRelationshipEvidence": {
    "epistemicStatus": "llm_inferred",
    "judgment": {"confidenceNotice": "Confidence is a model judgment, not a calibrated probability of learner success or validated pedagogical correctness."},
    "relationship": {"attributionStatement": "Learning progression relationship generated by IDinsight using an LLM producer/checker workflow. …", "author": "LLM generated", "label": "buildsTowards", "license": "Unknown", "provider": "IDinsight", "relationshipType": "buildsTowards", "sourceEntity": "StandardsFrameworkItem", "…": "…"}
  },
  "relationships": [
    {
      "judgment": {"confidence": 0.68, "rationaleExcerpt": "…", "warningCount": 11, "…": "…"},
      "provenanceUri": "kgfegmcp://framework/…/relationship/00090dab-9dc9-55f0-a9a0-2f7bca237a9a/provenance",
      "relationship": {"relationshipId": "00090dab-9dc9-55f0-a9a0-2f7bca237a9a", "sourceNodeId": "ee045978-4d81-5fad-b809-f283d1e81fbe", "targetNodeId": "309b1c92-3cd5-5a83-b884-e7af94b959ed", "…": "…"},
      "relationshipUri": "kgfegmcp://framework/…/relationship/00090dab-9dc9-55f0-a9a0-2f7bca237a9a"
    }
  ]
}
```

To restore an entry's full evidence, take each of the fields listed above from the entry if it is there, otherwise from `sharedRelationshipEvidence`, otherwise use null. The result is the same entry that `get_learning_progression` returns for that relationship. Each of the four tools' output schemas states this rule too. In Python:

```python
import copy

# Fields that may be stated once in sharedRelationshipEvidence, by nesting level.
SHARED_FIELDS = {
    None: ["epistemicStatus"],
    "judgment": ["confidenceNotice"],
    "relationship": [
        "attributionStatement", "author", "description", "label", "license",
        "provider", "relationshipType", "sourceEntity", "sourceEntityKey",
        "sourceLabels", "targetEntity", "targetEntityKey", "targetLabels",
    ],
}


def full_relationships(result: dict) -> list[dict]:
    """Return each relationship entry of a compact result with every field restored."""
    shared = result["sharedRelationshipEvidence"]
    entries = []
    for entry in result["relationships"]:
        entry = copy.deepcopy(entry)
        for level, names in SHARED_FIELDS.items():
            own = entry if level is None else entry.setdefault(level, {})
            common = shared if level is None else shared.get(level, {})
            for name in names:
                if own.get(name) is None:
                    own[name] = common.get(name)
        entries.append(entry)
    return entries
```

Pass the parsed JSON text or `structuredContent` of one tool result. Other progression fields, such as `nodes`, are not affected.

## Bounds and continuation

| Budget                                        | Default | Maximum |
|-----------------------------------------------|---------|---------|
| Direct/discovery returned edges               | 25      | 100     |
| Direct/discovery examined candidates per page | 5,000   | 5,000   |
| Traversal depth                               | 8       | 12      |
| Traversal nodes                               | 100     | 250     |
| Traversal edges                               | 100     | 100     |
| Path depth                                    | 6       | 16      |
| Returned paths                                | 3       | 20      |
| Traversal/path examined adjacency edges       | 5,000   | 5,000   |
| Path partial paths created                    | 5,000   | 5,000   |
| Whole tool result (text plus structured copy) | 1 MiB and 100,000 characters | same |

Caller bounds are strict positive integers; booleans, fractions and numeric strings are rejected. Work, queue and size ceilings are fixed. The size ceiling applies to the whole emitted result, counting the JSON text and the structured copy together, in both UTF-8 bytes and characters. It is kept below the roughly 150,000-character tool-result limit Anthropic documents for connectors.

Collections are ordered by `(relationship type, relationship ID)`, so `buildsTowards` comes first. If a request covers both types, a page that stops at the size limit can end before any `relatesTo` link appears. To read each type fully, send one `relationshipTypes` value per search request, or one `connectionKind` (not `all`) per direct request, as the workflows do. `page` reports `returnedCount`, `examinedCount`, `candidateCount`, `hasMore`, `isComplete`, `stoppingReason` and `nextCursor`. `candidateCount` is not a filtered match count. `totalMatchingCount` is exact only when the entire candidate stream was examined in the current page; otherwise it is null. Package stored totals are separate from page/subset counts.

To continue, call the same tool with `page.nextRequest` exactly as returned: it is the effective request with `cursor` set to `page.nextCursor`. Equivalently, replay the same request, including limit and resolved route, with that cursor. Tokens are opaque, at most 4,096 characters, checksum protected and bound to package/manifest/profile and effective operation/filters/bounds. Changed or stale requests yield `invalid_cursor`. Page/work/byte limits can leave more results; a work-limited page may contain zero matches and still have continuation. When the next whole edge would exceed either size ceiling, the page stops before it with `stoppingReason: byte_limit` and keeps that edge for the next page. Because each edge carries its endpoints, judgment excerpts and links twice (text and structured copy), a page can hold far fewer edges than `limit`: on Nigeria Mathematics, the 189 stored `buildsTowards` edges arrive in 24 pages, nearly all of eight or nine edges, at `limit` 25.

Traversal is breadth-first with relationship-ID neighbor ordering and preserves branching/merging edges. Paths are described [below](#paths). Results expose `scopeComplete`, `graphExhausted`, `truncationReasons`, counters and frontier. Requested-depth completeness does not mean the whole graph is exhausted. These operations have no cursor: narrow the bounded inputs and rerun. Do not retry indefinitely to evade service ceilings.

Traversal adds whole edges until the size ceiling, then reports `byte_limit` with `scopeComplete` false.

## Paths

`get_learning_progression_paths` returns directed paths from the source to the target that use only stored `buildsTowards` edges. Paths come shortest first; paths of the same length are ordered by their relationship IDs. `maxDepth` (1–16, default 6) is the most hops a path may have, and `maxPaths` (1–20, default 3) the most paths returned. Validation rejects any package whose `buildsTowards` edges form a cycle, so a path never visits a standard twice.

The search is target-aware. It first works back from the target to find which standards can reach it, and in exactly how many hops. It then grows a path from the source only along edges that can still reach the target within the hops left. Because it does not grow paths that cannot reach the target, it finds long connections within the same fixed budgets of 5,000 inspected edges and 5,000 partial paths. This is why the depth limit could rise from 12 to 16: CAPS has connections of up to 13 hops, longer than any in the other packages (at most 8 hops, in Rwanda). For any request the earlier search answered completely, with no truncation reasons, the paths and their order are the same as before.

`truncationReasons` lists why a result may be missing paths:

- `depth_limit`: a path from the source to the target longer than `maxDepth` exists. A source that cannot reach the target never reports it.
- `path_limit`: `maxPaths` paths were returned and at least one more path within `maxDepth` exists.
- `byte_limit`: the next path did not fit within the size ceiling.
- `work_limit` or `queue_limit`: the search reached its fixed edge or path budget.

`counters` and `frontier` describe how much work the search did. They are not part of the result's meaning and are usually smaller than with the earlier search, so do not rely on their exact values.

Paths are admitted whole in order; a path is never clipped. If a later path does not fit after at least one path was selected, the result returns the paths already selected, adds `byte_limit`, sets `scopeComplete` and `graphExhausted` false, and names the path that did not fit in `nextUnreturnedPath` (its ordered node and relationship IDs only; its edges are not in the tables). Inspect those edges with `get_learning_progression`, or rerun with a smaller `maxDepth` or `maxPaths`.

If even the first, shortest path does not fit in the compact form, the tool still returns a normal result that identifies that path by its IDs:

- `paths` and `relationships` are empty, and `sharedRelationshipEvidence` is `{}`;
- `nodes` holds only the source and target standards;
- `nextUnreturnedPath` holds the shortest path's ordered node and relationship IDs;
- `truncationReasons` includes `byte_limit`, plus `depth_limit` or `path_limit` when they apply.

In CAPS this happens only for the longest connections, the five 13-hop pairs; every shorter shortest path comes back with its edges. That was checked for every connected CAPS pair, with the default `maxPaths` and with `maxDepth` both at the shortest length and at 16. In the other six packages, every shortest path (at most 8 hops) comes back with its edges when `maxDepth` equals its length. To read the full evidence of each hop of a path named by IDs, call `get_learning_progression` with each relationship ID in `nextUnreturnedPath.relationshipIds`. Each result has the edge, both standards and the edge's `provenanceUri`, which you can read natively or with [`read_evidence`](access-tools.md#read_evidence) for the full record.

On the current packages, every connected pair's shortest path comes back first when `maxDepth` is at least its length: in `paths`, or in `nextUnreturnedPath` for the five 13-hop CAPS pairs, and never with `work_limit` or `queue_limit`. This was checked for every pair at `maxDepth` equal to the shortest length in all seven packages, and also at 16 for CAPS.

## Empty, unavailable and failed requests

Valid complete empty results succeed. Zero paths in an incomplete search do not establish disconnection. Even exhausted absence means no stored connection, not no pedagogical relationship: candidate coverage is limited. Unresolved, rejected, `no_relation` and `needs_review` claims are not accepted edges.

| Error                                        | Meaning                                                                        |
|----------------------------------------------|--------------------------------------------------------------------------------|
| `framework_not_found`, `ambiguous_framework` | Route missing or unique-current selection ambiguous                            |
| `standard_not_found`, `ambiguous_graph_node` | Exact endpoint missing or ambiguous                                            |
| `learning_progression_not_found`             | ID missing or belongs to a non-LP edge                                         |
| `capability_unavailable`                     | Package does not declare LP, or selected code capability unavailable           |
| `invalid_progression_request`                | Invalid semantic filters/selection, including identical path endpoints         |
| `invalid_cursor`                             | Invalid, stale or mismatched continuation                                      |
| `progression_result_too_large`               | An exact result or a single edge cannot fit within the size ceiling. For paths, only when even the IDs-only result cannot fit; otherwise paths stop with `byte_limit` (see [Paths](#paths)) |
| `resource_access_denied`                     | Reviewed/full-text/standard exposure policy denies query evidence              |

Malformed protocol types/enums/bounds are rejected by MCP validation. The tool result ceilings and resource source/return limits are distinct; resources can also deny or exceed limits. See [resources](resources.md) and [protocol behavior](protocol-behavior.md).
