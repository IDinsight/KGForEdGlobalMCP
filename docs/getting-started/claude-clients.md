# Use with Claude Desktop and claude.ai

This page explains how to get query results, full evidence and workflow instructions in
local Claude Desktop and through a claude.ai custom connector, and how to check that a
setup actually works. Set up the connection first with
[Connect an MCP client](mcp-clients.md).

## What has and has not been checked

Be clear about which claims rest on which evidence:

| Surface | What was checked | Status |
|---|---|---|
| Server version 0.4.0, over local STDIO and local Streamable HTTP | Automated offline tests and smoke checks: tool text for all five progression tools, `read_evidence`, `get_workflow_instructions`, native prompts and resources, paging, size limits, progression details in framework listings, citation links in component text, and one request per link type in workflows | Passed locally, 2026-10-07. This tests the server, not a client. |
| MCPB bundle, version 0.4.0 | STDIO smoke test run from the unpacked bundle | Passed locally, 2026-10-07; not an installation in Desktop |
| MCPB installation in Claude Desktop, version 0.4.0 | Install, enable, removal and same-version replacement steps | Not checked in Desktop on any OS; see the [installation guide](../operations/mcpb.md#claude-desktop-installation) for sources and unverified steps |
| Claude Desktop, earlier development build | Observed by a user on 2026-10-03: the connector started and listed six frameworks; all nine prompts appeared under **Add from curriculum-knowledge-graph**, and the support-planning prompt rendered as an attachment; the **Catalog** resource attached; the resource menu offered only Catalog and could not find a progression link. | User observations, not a test of this version |
| Claude Desktop, version 0.4.0 | The [walkthrough below](#claude-desktop-walkthrough) | Prepared; not yet run in Desktop |
| claude.ai custom connector | Nothing yet: the hosted service has not been updated to 0.4.0 | Untested; use the [remote checklist](#claudeai-remote-acceptance-checklist) after deployment |

The local setup guide is written for macOS. The earlier observations and
2026-10-07 smoke evidence above do not record an OS, so they establish no
OS-specific Desktop pass. Windows and Linux Desktop setup is undocumented and
untested here; the manifest's three declared platforms do not change that.

No end-to-end teaching workflow (retrieval followed by a cited, composed answer) has been
run and checked in any client. Rendering a prompt, reading a resource or passing a smoke
test is not the same as a completed workflow.

## Supported routes

| You need | Claude Desktop (local) | claude.ai custom connector |
|---|---|---|
| Progression query results | Ordinary tool text. Each of the five progression tools returns its complete bounded result as JSON text, including edges, statements, confidence, warnings, links and cursors. | Same tools and text. |
| Next page of a search or direct-connections result | Ask Claude to call the same tool with `page.nextRequest` unchanged. | Same. |
| Full provenance and supporting evidence | Attach a resource from the connector's menu where it is offered (Catalog was observed). For any other link, ask Claude to call `read_evidence` with the exact URI. | Ask Claude to call `read_evidence`. Whether claude.ai lets you attach server resources has not been tested. |
| Standard and learning-component evidence | Workflow instructions list exact links and per-record link patterns (**EVIDENCE LINKS**); Claude fills in IDs from tool text and reads them with `read_evidence`. | Same. |
| Workflow instructions | Native prompt from **Add from curriculum-knowledge-graph** (observed working). Alternative: ask Claude to call `get_workflow_instructions`. | The server advertises all nine prompts; whether claude.ai shows them is untested. `get_workflow_instructions` covers the seven teaching, study and progression workflows. |

`get_workflow_instructions` does not cover `administrator_alignment_review` or
`cross_framework_comparison`; use those as native prompts. See
[Evidence and workflow access tools](../reference/access-tools.md) for both tools.

Known client limits that matter here:

- The Desktop resource menu observed on 2026-10-03 listed only Catalog and could not find
  a progression link by URI. Use `read_evidence` for links returned by tools.
- Anthropic documents a tool-result limit of roughly 150,000 characters for connectors.
  This server keeps each tool result, text and structured copy combined, under 100,000
  characters and 1 MiB. Pages and paths stop early rather than exceed that, and say so.
- Remote connections come from Anthropic's cloud, not your machine, so the hosted
  endpoint must be reachable from the internet.

## Claude Desktop walkthrough

Run this in a new Desktop conversation with the **curriculum-knowledge-graph** connector
enabled, against the 0.4.0 server from this repository or a 0.4.0 bundle. Each step
gives a message to send and what you should see. Claude may summarise in its reply; to
check details, expand the tool call to see the raw result, or ask Claude to quote the
fields named.

The walkthrough uses one fixed diagnostic case from the Nigeria curriculum:

| Item | Value |
|---|---|
| Framework ID | `nigeria-nerdc-mathematics-primary-1-3` |
| Snapshot ID | `nigeria-nerdc-mathematics-primary-1-3@undated+bc5e769ed26f` |
| Relationship ID | `0129f5d5-42fd-52cb-bcf2-ec07c47103e7` ("write correctly number 1-5" builds towards "write correctly number 6-9") |
| Target standard node ID | `e399b510-48bb-58ee-abda-61460a5a853b` ("write correctly number 6-9", PRIMARY ONE) |

**Run status.** Every tool call below was replayed against the same server code and data
through an in-process MCP client on 2026-10-07, and the expected results were checked.
None of the steps has been run in Claude Desktop yet; record your own results in the
[table at the end](#record-your-results).

**Before you start, check that Desktop runs the current server.** In step 1, each
framework should show `Routing graph types:` and `Included graph types:` lines. If it
shows a single `Graph types:` line instead, Desktop is running an older copy.
For a bundle, follow the removal and reinstall steps in
[Claude Desktop installation](../operations/mcpb.md#claude-desktop-installation)
(unverified in this project). For a checkout added in Desktop's configuration
file, verify its paths, fully quit Desktop and reopen it.

### 1. Discovery

> Use curriculum-knowledge-graph to list all available frameworks.

Expected: six framework snapshots, including Nigeria Mathematics with the snapshot ID
above. Each snapshot shows `Routing graph types: academic_standards` and
`Included graph types: academic_standards, learning_components, learning_progressions`.
Each package line shows `learning_progressions=available` and its stored link counts; for
Nigeria these are `builds_towards=189` and `relates_to=297`.

> Call list_frameworks with graphTypes ["learning_progressions"] and list the snapshot IDs.

Expected: the same six snapshots. The filter matches the graph types a package
*includes*. The routing type stays `academic_standards`: it is the type tools use to pick a
package, not a list of what the package contains.

> Call get_capabilities and tell me how many tools, prompts and resource templates it reports, and which graph types are included.

Expected: 19 tools (including `read_evidence` and `get_workflow_instructions`), nine
prompts, one fixed resource and 14 templates. `Included graph types:` lists all three
types, and each package has a `Learning progressions:` block with
`hasLearningProgressions: true` and its two stored counts.

### 2. Exact relationship

> Call get_learning_progression with `{"request":{"frameworkId":"nigeria-nerdc-mathematics-primary-1-3","snapshotId":"nigeria-nerdc-mathematics-primary-1-3@undated+bc5e769ed26f","relationshipId":"0129f5d5-42fd-52cb-bcf2-ec07c47103e7"}}` and show me the relationship type, both endpoint statements, the confidence, the warnings and the provenance link.

Expected in the JSON text:

- `relationshipType` `buildsTowards`, from `12b603df-b6f0-50b3-914d-5d655a2dbaf1`
  ("Pupils should be able to: write correctly number 1-5;") to the target standard;
- `judgment.confidence` 0.72 with the notice that it is a model judgment;
- `warningCount` 9, five `warningExcerpts` and `warningsOmitted: true`, and
  `rationaleExcerpted: true` — the tool shows excerpts, and the full record is in step 7;
- `relationshipUri`, `provenanceUri`, `standardUri` for both endpoints, the generated-origin
  notice and a `continuationNotice` saying this operation has no continuation.

### 3. Direct connections

> Call get_standard_progressions for node e399b510-48bb-58ee-abda-61460a5a853b in that snapshot three times, with connectionKind "outgoing_builds", "incoming_builds" and "related", and list each connection with its kind and relationship ID.

Expected: no `outgoing_builds`; two `incoming_builds` (`0129f5d5…` from `12b603df…`, and
`c0155efa…` from `c4885674…`, "Count and read correctly from 1-9"); and six `related`.
Each page has `isComplete` true and no cursor.

Asking for `connectionKind` `"all"` returns the same eight connections here in one page.
For a standard with many links, an `all` page lists builds first and can stop at the
result-size limit before any related links appear. That is why the workflows ask for each
kind separately.

### 4. Search and pagination

> Call search_learning_progressions with `{"request":{"frameworkId":"nigeria-nerdc-mathematics-primary-1-3","snapshotId":"nigeria-nerdc-mathematics-primary-1-3@undated+bc5e769ed26f","relationshipTypes":["buildsTowards"],"endpointScope":"either","limit":25}}`. Report page.returnedCount, page.stoppingReason and whether page.nextCursor is present.

Expected: 7 relationships, `stoppingReason` `byte_limit`, `isComplete` false, and both
`page.nextCursor` and `page.nextRequest` present. `limit` is a maximum; the page stopped
early to stay within the result-size limit.

> Call search_learning_progressions again with page.nextRequest exactly as returned, and list the new relationship IDs.

Expected: seven different relationship IDs. Following every page gives 27 pages and
189 distinct `buildsTowards` edges, with no repeats.

### 5. Upstream traversal

> Call traverse_learning_progressions upstream from node e399b510-48bb-58ee-abda-61460a5a853b in that snapshot with maxDepth 3, maxNodes 20 and maxEdges 30.

Expected: five standards and five stored edges, `scopeComplete` and `graphExhausted`
true, an empty frontier and no truncation reasons. The deepest supports are
"count correctly up to 5" (`ec0c6a6d…`) and "sort and classify number of objects"
(`b193d5b5…`).

### 6. Connecting paths

> Call get_learning_progression_paths from node ec0c6a6d-0a48-5aa8-bdfe-72260dd3b559 to node e399b510-48bb-58ee-abda-61460a5a853b in that snapshot with maxDepth 3 and maxPaths 3.

Expected: two two-hop paths, through `c4885674…` (`41ec8cba…`, `c0155efa…`) and
through `12b603df…` (`7fc3c0e1…`, `0129f5d5…`); `scopeComplete` true, `graphExhausted`
false, `truncationReasons` `["depth_limit"]`, `nextUnreturnedPath` null. A path is
derived from stored edges; it is not a compulsory teaching order.

### 7. Full provenance

> Call read_evidence with the provenanceUri from step 2. If page.isComplete is false, keep calling with page.nextRequest until it is true. Then summarise the full rationale, all warnings and the producer/checker trace.

Expected: one window, `contentStatus` `full`, 12,275 bytes, holding the full
rationale, confidence, all nine warnings and the producer/checker trace with hashes.
To see continuation in action, ask for `"maxContentBytes":4096`: the same record then
arrives in three windows.

### 8. Standard and learning-component evidence

> Call get_learning_components_for_standard for node e399b510-48bb-58ee-abda-61460a5a853b in that snapshot.

Expected: one supporting learning component, `20507dfe-4d56-575c-b7ea-33b1f9072300`,
"Write correctly the numbers 6 to 9", support confidence 0.97, labelled as a
model-generated decomposition. The text also gives what you need to cite it: the
`Standard URI`, and for the component `Support relationship ID:
5f89e75a-70c5-5260-b325-31fcba940574`, its `Support relationship URI`,
`Direction: component -> standard`, the `Component URI` and the
`Component provenance URI`.

> Read the Support relationship URI and the Component provenance URI from that result with read_evidence, and also `kgfegmcp://framework/nigeria-nerdc-mathematics-primary-1-3/snapshot/nigeria-nerdc-mathematics-primary-1-3%40undated%2Bbc5e769ed26f/standard/e399b510-48bb-58ee-abda-61460a5a853b/provenance`.

Expected: all three complete in one window (1,049, 541 and 3,077 bytes). The support
relationship record is a `supports` relationship from the component to the standard. The
standard provenance link follows the patterns in the workflow's **EVIDENCE LINKS** block
(step 11).

### 9. Progression coverage, validation and unresolved claims

> Call read_evidence for the summaryUri, validationUri and unresolvedUri from step 2. Then read the learning-progressions summary for snapshot india-cbse-science-learning-framework-classes-9-10@undated+576740bed2d1.

The CBSE link is:

```text
kgfegmcp://framework/india-cbse-science-learning-framework-classes-9-10/snapshot/india-cbse-science-learning-framework-classes-9-10%40undated%2B576740bed2d1/learning-progressions
```

Expected: all four are progression records, each complete in one window. The Nigeria
summary (4,577 bytes) reports stored counts, eligibility limits and that validation is
structural only. The progression validation report is 1,806 bytes. The progression
unresolved record (214 bytes) lists no unresolved claims for Nigeria (`claims` empty,
`total_needs_review` 0). The CBSE summary reports one `needs_review` claim kept out of
accepted edges.

### 9a. Optional: a long record in several windows

This step only shows paging on a long record. The record is **not** progression evidence:
the `/unresolved` resource is the standards-hierarchy report, listing parent–child links
in the Ghana Mathematics source that could not be resolved.

> Call read_evidence for `kgfegmcp://framework/ghana-nacca-primary-mathematics-basic-4-6/snapshot/ghana-nacca-primary-mathematics-basic-4-6%402019%2B0b768f7cfaf9/unresolved`, keep calling with page.nextRequest until page.isComplete is true, and tell me how many calls it took.

Expected: 42,831 bytes in three windows at the default window size of 16,384 bytes
(`contentStatus` `partial` until all are joined). The number of windows depends on the
window size: with `"maxContentBytes":4096` the same record takes 11.

### 10. A policy outcome

> Call read_evidence for the learningProgressionProvenance artifact URI listed in metadata.artifacts from step 2.

Expected: `resource_access_denied` — this package does not allow bulk artifact reads.
Claude should report the denial, not invent the content. Per-edge provenance (step 7)
remains readable.

### 11. Support plan through the native prompt

1. Open **Add from curriculum-knowledge-graph** and choose
   `learning_progression_support_plan`.
2. Enter `framework_id` `nigeria-nerdc-mathematics-primary-1-3`, `snapshot_id`
   `nigeria-nerdc-mathematics-primary-1-3@undated+bc5e769ed26f`, `identifier`
   `{"identifierType":"node_id","nodeId":"e399b510-48bb-58ee-abda-61460a5a853b"}`,
   `local_context` `Learners can count to 9 but often write 6 and 9 the wrong way round.` and
   `output_language` `en`.
3. Check the attachment: prompt version 1.4.0, the pinned snapshot, an **EVIDENCE
   ACCESS** section and an **EVIDENCE LINKS** block.
4. Send it, and let Claude make the listed calls and evidence reads.

Expected answer: it starts from the target standard; cites the incoming edges
(`0129f5d5…`, `c0155efa…`) as `[GENERATED-EVIDENCE / llm_inferred]` with their
provenance links; keeps related concepts separate; cites component `20507dfe…` with its
support relationship `5f89e75a…`; labels
review and practice ideas as generated; treats the classroom note as a teacher report,
not a diagnosis; and repeats the NERDC attribution. It reads at most ten distinct
edge-provenance records and at most 32 evidence windows, and says so if it had to stop.

### 12. Same workflow through tools only

> Call get_workflow_instructions with `{"request":{"workflowName":"learning_progression_support_plan","frameworkId":"nigeria-nerdc-mathematics-primary-1-3","snapshotId":"nigeria-nerdc-mathematics-primary-1-3@undated+bc5e769ed26f","identifier":{"identifierType":"node_id","nodeId":"e399b510-48bb-58ee-abda-61460a5a853b"},"localContext":"Learners can count to 9 but often write 6 and 9 the wrong way round.","outputLanguage":"en"}}`, then follow rendered.message exactly.

Expected: `rendered.message` is the same text as the native prompt in step 11, and
`instructionsNotice` says the server has not run it. Claude then performs the same
retrieval and composition.

### 13. Curriculum review covers both link types

> Call get_workflow_instructions with `{"request":{"workflowName":"learning_progression_curriculum_review","frameworkId":"ghana-nacca-primary-mathematics-basic-4-6","snapshotId":"ghana-nacca-primary-mathematics-basic-4-6@2019+0b768f7cfaf9","localGradeLabels":["BASIC 5"],"endpointScope":"either","outputLanguage":"en"}}`, then follow rendered.message exactly.

Expected: step 3 of `rendered.message` lists two separate scans, a `buildsTowards scan`
and a `relatesTo scan`, each allowed up to three pages. Each page returns
seven relationships (`stoppingReason` `byte_limit`), so Claude reviews 21 links of each
type, and both scans still have a cursor after their third page. The answer should
report the two types separately (Ghana Mathematics stores 299 `buildsTowards` and 300
`relatesTo` links), say the review is incomplete for both, not add the counts together,
and fully inspect at most ten relationships, up to five of each type.

To review one type only, add `"relationshipTypes":["relatesTo"]` to the request; the
native prompt takes `relationship_types` `["relatesTo"]`. The instructions then contain a
single `relatesTo` scan.

### Record your results

| Step | Status before your run | Your result (date, client version, pass/limited/fail, notes) |
|---|---|---|
| 1–10 (and 9a) | Tool calls replayed locally and passed, 2026-10-07; not run in Desktop | |
| 11 | Prompt appeared and rendered in Desktop on an earlier build; rendering of this version checked locally; retrieval and composed answer not run | |
| 12 | Rendering checked locally (identical to native); retrieval and composed answer not run | |
| 13 | Rendering and the six scan pages checked locally; composed review not run | |

Mark a step **limited** if it worked but Claude only summarised, needed extra
instructions, or a client feature was unavailable.

## claude.ai remote acceptance checklist

Use this only after the hosted service is updated to 0.4.0 (see
[Hosted deployment](../operations/deployment.md)). Deployment timing and sign-off are
the operator's decision; none of these items has been run yet.

1. From a repository checkout, run the HTTP smoke against the endpoint:

    ```bash
    uv --directory backend run --locked --no-dev kgfegmcp-http-smoke \
      --url https://<service-domain>/mcp
    ```

    It must pass before testing in claude.ai. This proves the deployed server, not the
    claude.ai client.

2. Add or refresh the custom connector (endpoint URL including `/mcp`, no
   authentication) and enable it in a new conversation.
3. Repeat walkthrough steps 1–10 in claude.ai. Confirm that `get_capabilities` reports
   19 tools, that frameworks show `Included graph types:` with `learning_progressions`,
   and that step 2's tool text shows the edge, statements, confidence, warnings and
   links, not just a summary.
4. Check pagination (step 4) by having Claude replay `page.nextRequest`, and check that
   the result does not appear cut off.
5. Check full evidence through `read_evidence` (steps 7–9a), including a multi-window
   record.
6. Record whether claude.ai offers the server's prompts or resources in its interface.
   If it does, try step 11; if not, note it as an unsupported client feature.
7. Run step 12 (`get_workflow_instructions`) and let Claude complete the support plan.
   Check the answer against the expectations in step 11.
8. Check the denial in step 10.
9. Run step 13 and check that the review includes `relatesTo` links and reports each
   type separately.
10. Write down the date, endpoint, connector name, plan type and each result, keeping
    server results, client observations and untested items separate.

---

**Next:** [First queries](first-queries.md)
