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
| `get_learning_progression_paths` | Distinct `sourceIdentifier` and `targetIdentifier` | Directed builds-only paths; `maxDepth`: 6; `maxPaths`: 3                                                                                               |

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

All results contain `request`, `metadata`, deduplicated `nodes` and `relationships`. `metadata.package.packageIdentity` pins framework/snapshot/package/profile identity and profile hash. `metadata.manifestUri` and `manifestSha256` identify the accepted manifest, which lists every artifact checksum. `metadata.artifacts` lists only the four artifacts a result is derived from (`learningProgressionProvenance`, `learningProgressionProvenanceIndex`, `nodes`, `relationships`), as `artifactInventoryNotice` explains; read the manifest for the full inventory. The remaining `metadata` fields hold stored per-type totals, coverage notices, the result `limits`, and summary/validation/unresolved URIs. Edge rows retain IDs, author, provider, attribution, license and exact endpoints; `relationshipUri` and `provenanceUri` link to retained evidence.

Endpoint `statementExcerpt` is capped at 2,048 characters, with `statementExcerpted` and `standardUri`. Judgment rationale is an excerpt of at most 512 characters; up to five warning excerpts of 512 characters retain total/omitted indicators. Read full provenance for rationale, confidence, warnings, candidate references and producer/checker hashes. Confidence is a model judgment, not a calibrated probability of learner success.

Stored edges have `epistemicStatus: llm_inferred`: IDinsight-generated evidence, without publisher endorsement or certified pedagogy. `buildsTowards` means directional support for success, not a mandatory prerequisite. `relatesTo` means a conceptual or skill link without sequence or dependency. Derived traversals/paths have `deterministic_derived` status and cite original generated edges; they assert no new direct edge or compulsory teaching order.

## Bounds and continuation

| Budget                                        | Default | Maximum |
|-----------------------------------------------|---------|---------|
| Direct/discovery returned edges               | 25      | 100     |
| Direct/discovery examined candidates per page | 5,000   | 5,000   |
| Traversal depth                               | 8       | 12      |
| Traversal nodes                               | 100     | 250     |
| Traversal edges                               | 100     | 100     |
| Path depth                                    | 6       | 12      |
| Returned paths                                | 3       | 20      |
| Traversal/path examined adjacency edges       | 5,000   | 5,000   |
| Path cumulative queue admissions              | 5,000   | 5,000   |
| Whole tool result (text plus structured copy) | 1 MiB and 100,000 characters | same |

Caller bounds are strict positive integers; booleans, fractions and numeric strings are rejected. Work, queue and size ceilings are fixed. The size ceiling applies to the whole emitted result, counting the JSON text and the structured copy together, in both UTF-8 bytes and characters. It is kept below the roughly 150,000-character tool-result limit Anthropic documents for connectors.

Collections are ordered by `(relationship type, relationship ID)`, so `buildsTowards` comes first. If a request covers both types, a page that stops at the size limit can end before any `relatesTo` link appears. To read each type fully, send one `relationshipTypes` value per search request, or one `connectionKind` (not `all`) per direct request, as the workflows do. `page` reports `returnedCount`, `examinedCount`, `candidateCount`, `hasMore`, `isComplete`, `stoppingReason` and `nextCursor`. `candidateCount` is not a filtered match count. `totalMatchingCount` is exact only when the entire candidate stream was examined in the current page; otherwise it is null. Package stored totals are separate from page/subset counts.

To continue, call the same tool with `page.nextRequest` exactly as returned: it is the effective request with `cursor` set to `page.nextCursor`. Equivalently, replay the same request, including limit and resolved route, with that cursor. Tokens are opaque, at most 4,096 characters, checksum protected and bound to package/manifest/profile and effective operation/filters/bounds. Changed or stale requests yield `invalid_cursor`. Page/work/byte limits can leave more results; a work-limited page may contain zero matches and still have continuation. When the next whole edge would exceed either size ceiling, the page stops before it with `stoppingReason: byte_limit` and keeps that edge for the next page. Because each edge carries its endpoints, judgment excerpts and links twice (text and structured copy), a page can hold far fewer edges than `limit`: on Nigeria Mathematics, the 189 stored `buildsTowards` edges arrive in 27 pages of seven at `limit` 25.

Traversal is breadth-first with relationship-ID neighbor ordering and preserves branching/merging edges. Paths are directed simple paths ordered by hop count then relationship-ID tuple, with per-path cycle protection so alternatives survive. Results expose `scopeComplete`, `graphExhausted`, `truncationReasons`, counters and frontier. Requested-depth completeness does not mean the whole graph is exhausted. These operations have no cursor: narrow the bounded inputs and rerun. Do not retry indefinitely to evade service ceilings.

Traversal adds whole edges until the size ceiling, then reports `byte_limit` with `scopeComplete` false. Paths are admitted whole in order. If a later path does not fit after at least one path was selected, the result returns the paths already selected, adds `byte_limit`, sets `scopeComplete` and `graphExhausted` false, and names the path that did not fit in `nextUnreturnedPath` (its ordered node and relationship IDs only; its edges are not in the tables). Inspect those edges with `get_learning_progression`, or rerun with a smaller `maxDepth` or `maxPaths`. A path is never clipped. On all six packages, a `maxPaths: 1` request with enough depth returns the shortest stored path for every connected pair; the longest such path is 8 hops (Rwanda).

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
| `progression_result_too_large`               | An exact result, a single edge, or the first path cannot fit within the size ceiling; later paths stop with `byte_limit` instead |
| `resource_access_denied`                     | Reviewed/full-text/standard exposure policy denies query evidence              |

Malformed protocol types/enums/bounds are rejected by MCP validation. The tool result ceilings and resource source/return limits are distinct; resources can also deny or exceed limits. See [resources](resources.md) and [protocol behavior](protocol-behavior.md).
