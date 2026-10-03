# S.T.A.N.D.A.R.D.S. Workflow State

`WorkflowState`: `TESTING` `CycleMode`: `STANDARD` `PendingCycleMode`: `UNSET`
`PendingCycleRequest`: `UNSET` `PendingCycleBlockedOn`: `NONE`

## Active Work

`Id`: `integrate-actual-learning-progressions-20261001T162834Z-142f2df1`
`Request`: `Integrate actual Learning Progressions (buildsTowards and relatesTo) relationships between Academic Standards into the existing read-only MCP server, including useful query tools, prompts/workflows/resources and synergy with existing Academic Standards and Learning Components functionality, with equivalent provenance, traceability and explainability. Completely remove obsolete inferred progression behavior and any other outdated progression implementations. End users are teachers, education ministry officials and ed-tech organizations including EIDU, Pratham, Madhi, Trackosaurus and Funda Wande. Scoper should recommend useful capabilities; prefer adapting existing machinery and explain significant structural changes in simple terms if needed. Deployment is user-owned and outside this work; backwards compatibility for obsolete behavior is unnecessary, while useful standards/components functionality remains. No tests may call live LLM APIs or paid services; mock them. Developer must first help copy the relevant Academic Standards, Learning Components and Learning Progressions files from /Users/tzz/Projects/private/idi/KGForEdGlobal/results/kg_for_ed into this project, to a temporary or permanent location. Ontology reference: https://docs.learningcommons.org/knowledge-graph/understanding-knowledge-graph/introduction. Start a STANDARD cycle, audit and save project context, then hand off to Scoper.` `Scope`: `.standards/docs/scope/integrate-actual-learning-progressions-20261001T162834Z-142f2df1.md` `Architecture`: `.standards/docs/specs/integrate-actual-learning-progressions-20261001T162834Z-142f2df1.md`
`Development`: `.standards/docs/development/integrate-actual-learning-progressions-20261001T162834Z-142f2df1.md` `PromotionReason`: `NONE` `AuditTarget`: `NONE`
`BlockedOn`: `NONE` `PendingVerificationCadence`: `NONE`

`BaselineReconciliation`: `NONE`

<!-- When non-NONE, use one Markdown list entry per source cycle:
- `SourceCycle`: `<cancelled-cycle-id>`
  `Request`: `<source-cycle request summary>`
Preserve existing entries; see PROTOCOL.md, Baseline Reconciliation Format.
-->

## Handoff

`Kind`: `FORWARD` `From`: `DEVELOPING` `FailureType`: `NONE` `Reason`:
`Refreshed shipped README; re-establish verification and documentation before final review.`

## Recovery

`Active`: `true`

### Frame 1

`From`: `REVIEWING_FINAL` `Owner`: `DEVELOPING` `FailureType`: `IMPLEMENTATION`
`Reason`: `Current retained MCPB ships removed progression-tool instructions; refresh final distribution (AC-022/AC-026).`
`ResumeAt`: `REVIEWING_FINAL` `RerunThrough`: `DOCUMENTING`

## Outstanding Obligations

`Active`: `false`
