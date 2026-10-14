# S.T.A.N.D.A.R.D.S. Workflow State

`WorkflowState`: `ARCHITECTING` `CycleMode`: `STANDARD` `PendingCycleMode`: `UNSET`
`PendingCycleRequest`: `UNSET` `PendingCycleBlockedOn`: `NONE`

## Active Work

`CompletionPolicy`: `FULL_DELIVERABLE` `Id`:
`integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3` `Request`:
`Integrate the CAPS English curriculum KG artifacts located at /Users/tzz/Projects/private/idi/KGForEdGlobal/results/kg_for_ed/c939a3a9dcce92ed61d970f4599ced6f2ddc425d1220eeeab9828472b878d24d into the MCP server. Also make the generic Learning Progression path search target-aware (prune partial paths that cannot reach the target within the requested depth, keeping the same results and ordering) and raise its max_depth ceiling to cover CAPS's 13-hop connections, so long CAPS connections can be found (user decisions, 2026-10-14: ceiling 16; every connected CAPS buildsTowards pair must return its complete shortest path with the queue and work budgets kept fixed).` `Scope`: `.standards/docs/scope/integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3.md`
`Architecture`: `.standards/docs/specs/integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3.md` `Development`: `.standards/docs/development/integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3.md` `PromotionReason`: `NONE`
`AuditTarget`: `NONE` `BlockedOn`: `NONE` `PendingVerificationCadence`: `NONE`

`BaselineReconciliation`: `NONE`

<!-- When non-NONE, use one Markdown list entry per source cycle:
- `SourceCycle`: `<cancelled-cycle-id>`
  `Request`: `<source-cycle request summary>`
Preserve existing entries; see PROTOCOL.md, Baseline Reconciliation Format.
-->

## Handoff

`Kind`: `FORWARD` `From`: `SCOPING` `FailureType`: `NONE` `Reason`:
`Scope replanned for target-aware path search (ceiling 16); AC-016 retired, AC-022..AC-027 added; design must account for the changed AC set.`

## Recovery

`Active`: `true`

### Frame 1

`From`: `DEVELOPING` `Owner`: `SCOPING` `FailureType`: `SCOPING`
`Reason`: `User chose target-aware LP path search plus a higher max_depth ceiling for long CAPS connections; this changes generic code and a public tool limit the scope keeps fixed.`
`ResumeAt`: `DEVELOPING` `RerunThrough`: `ARCHITECTING`

## Outstanding Obligations

`Active`: `false`
