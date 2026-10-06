# S.T.A.N.D.A.R.D.S. Workflow State

`WorkflowState`: `DEVELOPING` `CycleMode`: `STANDARD` `PendingCycleMode`: `UNSET`
`PendingCycleRequest`: `UNSET` `PendingCycleBlockedOn`: `NONE`

## Active Work

`Id`: `integrate-actual-learning-progressions-20261001T162834Z-142f2df1`
`Request`: `Integrate actual Learning Progressions (buildsTowards and relatesTo) relationships between Academic Standards into the existing read-only MCP server, including useful query tools, prompts/workflows/resources and synergy with existing Academic Standards and Learning Components functionality, with equivalent provenance, traceability and explainability. Completely remove obsolete inferred progression behavior and any other outdated progression implementations. End users are teachers, education ministry officials and ed-tech organizations including EIDU, Pratham, Madhi, Trackosaurus and Funda Wande. Scoper should recommend useful capabilities; prefer adapting existing machinery and explain significant structural changes in simple terms if needed. Deployment is user-owned and outside this work; backwards compatibility for obsolete behavior is unnecessary, while useful standards/components functionality remains. No tests may call live LLM APIs or paid services; mock them. Developer must first help copy the relevant Academic Standards, Learning Components and Learning Progressions files from /Users/tzz/Projects/private/idi/KGForEdGlobal/results/kg_for_ed into this project, to a temporary or permanent location. Ontology reference: https://docs.learningcommons.org/knowledge-graph/understanding-knowledge-graph/introduction. Start a STANDARD cycle, audit and save project context, then hand off to Scoper. Rework this same cycle in Scoper REPLAN mode: ordinary text from all five progression tools must expose complete bounded results and actual continuation information; provide a practical supported route to full permitted progression and affected Academic Standards/Learning Components provenance, supporting evidence, coverage, validation and unresolved records. Preserve working Desktop native prompts/resources, useful structuredContent, deterministic read-only retrieval/rendering, exact package/snapshot identity, stored judgments/semantics/disclosures, rights and finite limits with explicit partial/denied/oversized outcomes. Architect assesses least-disruptive reuse, text payloads, evidence access and only justified workflow fallback for local Claude Desktop and public claude.ai remote connector, without predetermined public names or blanket wrappers. Align discovery/schemas/counts/docs/retained MCPB; verify text-only consumption, shared STDIO/local HTTP, specific evidence, regressions/distribution and provide a practical user-run Desktop walkthrough. No teaching workflow was inspected end-to-end and public deployment/client behavior is untested. Actual claude.ai acceptance follows user deployment; neither deployment nor remote acceptance is a local completion prerequisite. Deployment and sign-off remain user-owned; no fixes in this Scoper session. Verified diagnostic evidence and exact IDs are preserved in the revised scope.` `Scope`: `.standards/docs/scope/integrate-actual-learning-progressions-20261001T162834Z-142f2df1.md` `Architecture`: `.standards/docs/specs/integrate-actual-learning-progressions-20261001T162834Z-142f2df1.md`
`Development`: `.standards/docs/development/integrate-actual-learning-progressions-20261001T162834Z-142f2df1.md` `PromotionReason`: `NONE` `AuditTarget`: `NONE`
`BlockedOn`: `DEV-022 evidence-links correction: user commits the text-derived smoke change; then Developer rebuilds the 0.4.0 candidate from HEAD and the user runs the three transport smokes.` `PendingVerificationCadence`: `NONE`

`BaselineReconciliation`: `NONE`

<!-- When non-NONE, use one Markdown list entry per source cycle:
- `SourceCycle`: `<cancelled-cycle-id>`
  `Request`: `<source-cycle request summary>`
Preserve existing entries; see PROTOCOL.md, Baseline Reconciliation Format.
-->

## Handoff

`Kind`: `FAILURE` `From`: `REVIEWING_IMPLEMENTATION` `FailureType`: `IMPLEMENTATION` `Reason`:
`Implementation review F-001: AS/LC evidence links (standard/LC provenance, LC, profile, validation, unresolved) reach tool-only clients only as resource_link blocks or not at all, and instructions give no construction rule (AC-029/AC-030). F-002 Tester evidence gap follows in the rerun.`

## Recovery

`Active`: `true`

### Frame 1

`From`: `AWAITING_USER_SIGNOFF` `Owner`: `SCOPING` `FailureType`: `SCOPING`
`Reason`: `User requests REPLAN of the same Learning Progressions cycle for verified Desktop text/evidence access gaps and a supported local Desktop/public claude.ai connector surface; preserve native prompts/resources and valid requirements.`
`ResumeAt`: `AWAITING_USER_SIGNOFF` `RerunThrough`: `SYNCHRONIZING`

### Frame 2

`From`: `REVIEWING_IMPLEMENTATION` `Owner`: `DEVELOPING` `FailureType`: `IMPLEMENTATION`
`Reason`: `Tool-only clients cannot obtain AS/LC evidence links: get_framework/get_standard/get_learning_component(s) expose them only as resource_link blocks (unresolved not at all) and workflow instructions say to copy URIs from tool results without a construction rule (review F-001, AC-029/AC-030).`
`ResumeAt`: `REVIEWING_IMPLEMENTATION` `RerunThrough`: `NONE`

## Outstanding Obligations

`Active`: `false`
