# S.T.A.N.D.A.R.D.S. Workflow State

`WorkflowState`: `ARCHITECTING` `CycleMode`: `STANDARD` `PendingCycleMode`: `UNSET`
`PendingCycleRequest`: `UNSET` `PendingCycleBlockedOn`: `NONE`

## Active Work

`CompletionPolicy`: `FULL_DELIVERABLE` `Id`:
`integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3` `Request`:
`Integrate the CAPS English curriculum KG artifacts located at /Users/tzz/Projects/private/idi/KGForEdGlobal/results/kg_for_ed/c939a3a9dcce92ed61d970f4599ced6f2ddc425d1220eeeab9828472b878d24d into the MCP server. Also make the generic Learning Progression path search target-aware (prune partial paths that cannot reach the target within the requested depth, keeping the same results and ordering) and raise its max_depth ceiling to cover CAPS's 13-hop connections, so long CAPS connections can be found (user decisions, 2026-10-14: ceiling 16; every connected CAPS buildsTowards pair must return its complete shortest path with the queue and work budgets kept fixed). For path results that exceed the 100,000-character result envelope, the user wants the per-step boilerplate repeated in every relationship (attribution, description, author, provider, license, entity fields, confidence notice) moved to one shared place in the result (user direction, 2026-10-15). If the shortest path still does not fit after that, return it by relationship and node IDs with byte_limit instead of an error (user decision, 2026-10-15).` `Scope`: `.standards/docs/scope/integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3.md`
`Architecture`: `.standards/docs/specs/integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3.md` `Development`: `.standards/docs/development/integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3.md` `PromotionReason`: `NONE`
`AuditTarget`: `NONE` `BlockedOn`: `NONE` `PendingVerificationCadence`: `NONE`

`BaselineReconciliation`: `NONE`

<!-- When non-NONE, use one Markdown list entry per source cycle:
- `SourceCycle`: `<cancelled-cycle-id>`
  `Request`: `<source-cycle request summary>`
Preserve existing entries; see PROTOCOL.md, Baseline Reconciliation Format.
-->

## Handoff

`Kind`: `RESUME` `From`: `SCOPING` `FailureType`: `NONE` `Reason`:
`Scope replanned for long-path results: AC-025 retired; AC-028..AC-031 add shared-place compaction and an ID-only fallback within the fixed envelope.`

## Recovery

`Active`: `true`

### Frame 1

`From`: `DEVELOPING` `Owner`: `ARCHITECTING` `FailureType`: `ARCHITECTURE`
`Reason`: `DEV-008 disproved AC-025 as designed: target-aware search finds every CAPS pair within budgets, but the fixed 100,000-character result envelope rejects all 492 CAPS pairs of 10-13 hops (progression_result_too_large) and reports byte_limit on 26,062 of 86,290 all-pairs requests.`
`ResumeAt`: `DEVELOPING` `RerunThrough`: `NONE`

## Outstanding Obligations

`Active`: `false`
