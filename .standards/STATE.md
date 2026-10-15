# S.T.A.N.D.A.R.D.S. Workflow State

`WorkflowState`: `ARCHITECTING` `CycleMode`: `STANDARD` `PendingCycleMode`: `UNSET`
`PendingCycleRequest`: `UNSET` `PendingCycleBlockedOn`: `NONE`

## Active Work

`CompletionPolicy`: `FULL_DELIVERABLE` `Id`:
`integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3` `Request`:
`Integrate the CAPS English curriculum KG artifacts located at /Users/tzz/Projects/private/idi/KGForEdGlobal/results/kg_for_ed/c939a3a9dcce92ed61d970f4599ced6f2ddc425d1220eeeab9828472b878d24d into the MCP server. Also make the generic Learning Progression path search target-aware (prune partial paths that cannot reach the target within the requested depth, keeping the same results and ordering) and raise its max_depth ceiling to cover CAPS's 13-hop connections, so long CAPS connections can be found (user decisions, 2026-10-14: ceiling 16; every connected CAPS buildsTowards pair must return its complete shortest path with the queue and work budgets kept fixed). For path results that exceed the 100,000-character result envelope, the user wants the per-step boilerplate repeated in every relationship (attribution, description, author, provider, license, entity fields, confidence notice) moved to one shared place in the result (user direction, 2026-10-15). If the shortest path still does not fit after that, return it by relationship and node IDs with byte_limit instead of an error (user decision, 2026-10-15). Use the compact shared-place form for path results whenever possible, even when the full form fits, to save client tokens (user decision, 2026-10-15). Apply the same compact shared-place form to get_standard_progressions, search_learning_progressions, and traverse_learning_progressions (user decision, 2026-10-15).` `Scope`: `.standards/docs/scope/integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3.md`
`Architecture`: `.standards/docs/specs/integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3.md` `Development`: `.standards/docs/development/integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3.md` `PromotionReason`: `NONE`
`AuditTarget`: `NONE` `BlockedOn`: `NONE` `PendingVerificationCadence`: `NONE`

`BaselineReconciliation`: `NONE`

<!-- When non-NONE, use one Markdown list entry per source cycle:
- `SourceCycle`: `<cancelled-cycle-id>`
  `Request`: `<source-cycle request summary>`
Preserve existing entries; see PROTOCOL.md, Baseline Reconciliation Format.
-->

## Handoff

`Kind`: `FAILURE` `From`: `DEVELOPING` `FailureType`: `ARCHITECTURE` `Reason`:
`DEV-010 found the compact-form change boundary too narrow: cli/smoke_progressions.py asserts the full get_learning_progression edge is in each compacted tool's relationships (stdio smoke for AC-012/AC-014 would fail), and mcp/tools/learning_progressions.py plus that smoke CLI are typed against ProgressionEvidenceResult, so a compact result base needs changes outside the boundary.`

## Recovery

`Active`: `true`

### Frame 1

`From`: `DEVELOPING` `Owner`: `ARCHITECTING` `FailureType`: `ARCHITECTURE`
`Reason`: `DEV-010 found the compact-form change boundary too narrow: cli/smoke_progressions.py asserts the full get_learning_progression edge is in each compacted tool's relationships (stdio smoke for AC-012/AC-014 would fail), and mcp/tools/learning_progressions.py plus that smoke CLI are typed against ProgressionEvidenceResult, so a compact result base needs changes outside the boundary.`
`ResumeAt`: `DEVELOPING` `RerunThrough`: `NONE`

## Outstanding Obligations

`Active`: `false`
