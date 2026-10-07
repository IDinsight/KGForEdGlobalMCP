# S.T.A.N.D.A.R.D.S. Workflow State

`WorkflowState`: `ARCHITECTING` `CycleMode`: `STANDARD` `PendingCycleMode`: `UNSET`
`PendingCycleRequest`: `UNSET` `PendingCycleBlockedOn`: `NONE`

## Active Work

`Id`: `integrate-actual-learning-progressions-20261001T162834Z-142f2df1`
`Request`: `Integrate actual Learning Progressions (buildsTowards and relatesTo) relationships between Academic Standards into the existing read-only MCP server, including useful query tools, prompts/workflows/resources and synergy with existing Academic Standards and Learning Components functionality, with equivalent provenance, traceability and explainability. Completely remove obsolete inferred progression behavior and any other outdated progression implementations. End users are teachers, education ministry officials and ed-tech organizations including EIDU, Pratham, Madhi, Trackosaurus and Funda Wande. Scoper should recommend useful capabilities; prefer adapting existing machinery and explain significant structural changes in simple terms if needed. Deployment is user-owned and outside this work; backwards compatibility for obsolete behavior is unnecessary, while useful standards/components functionality remains. No tests may call live LLM APIs or paid services; mock them. Developer must first help copy the relevant Academic Standards, Learning Components and Learning Progressions files from /Users/tzz/Projects/private/idi/KGForEdGlobal/results/kg_for_ed into this project, to a temporary or permanent location. Ontology reference: https://docs.learningcommons.org/knowledge-graph/understanding-knowledge-graph/introduction. Start a STANDARD cycle, audit and save project context, then hand off to Scoper. Rework this same cycle in Scoper REPLAN mode: ordinary text from all five progression tools must expose complete bounded results and actual continuation information; provide a practical supported route to full permitted progression and affected Academic Standards/Learning Components provenance, supporting evidence, coverage, validation and unresolved records. Preserve working Desktop native prompts/resources, useful structuredContent, deterministic read-only retrieval/rendering, exact package/snapshot identity, stored judgments/semantics/disclosures, rights and finite limits with explicit partial/denied/oversized outcomes. Architect assesses least-disruptive reuse, text payloads, evidence access and only justified workflow fallback for local Claude Desktop and public claude.ai remote connector, without predetermined public names or blanket wrappers. Align discovery/schemas/counts/docs/retained MCPB; verify text-only consumption, shared STDIO/local HTTP, specific evidence, regressions/distribution and provide a practical user-run Desktop walkthrough. No teaching workflow was inspected end-to-end and public deployment/client behavior is untested. Actual claude.ai acceptance follows user deployment; neither deployment nor remote acceptance is a local completion prerequisite. Deployment and sign-off remain user-owned; no fixes in this Scoper session. Verified diagnostic evidence and exact IDs are preserved in the revised scope. User rework 2026-10-07 after Claude Desktop testing of 0.4.0 (issues confirmed by read-only code inspection and an offline in-process probe; owners re-verify): F1 (AC-019) list_frameworks and get_capabilities text report only `Graph types: academic_standards` and no per-package LP availability, and list_frameworks graphTypes [learning_progressions] returns 0 frameworks, because graph types derive only from each package's primary type (catalog/repository.py) although structured hasLearningProgressions is true; F2 (AC-016/AC-029) workflow instructions require citing component/support relationship IDs/URIs (prompts/learning_progressions.py) but get_learning_components_for_standard text omits them (only structuredContent has them); F3 (AC-015) the curriculum review cannot reach relatesTo links: discovery orders by type label so buildsTowards comes first, pages stop at about 7 edges under the size limit, the 3-page cap yields about 21 buildsTowards-only edges (Ghana BASIC 5 observed), the prompt has no relationship-type argument and still says 3 pages of 25 / at most 75; D1 (AC-036) walkthrough says Ghana unresolved needs three windows without stating that holds only at the default 16,384-byte window (11 at 4,096), presents the Ghana /unresolved record (AS hierarchy unresolved edges) among progression coverage evidence, and step 11's classroom note (equal-sized parts) does not fit its target standard (write correctly number 6-9). Fix these within existing acceptance meanings, preserving everything else; rebuild the retained 0.4.0-line candidate as needed. No deployment or sign-off in this rework. User decisions 2026-10-07 on the revised design: keep server/MCPB version 0.4.0; also fix the similar relatesTo-starvation gap in the teaching-sequence workflow and the shared optional progression step of the four existing teaching/study workflows. User decision 2026-10-07 during DEVELOPING: also align the support-planning workflow's page-limit wording (it still promises one page of 25 for its incoming/related calls) with the other workflows.` `Scope`: `.standards/docs/scope/integrate-actual-learning-progressions-20261001T162834Z-142f2df1.md` `Architecture`: `.standards/docs/specs/integrate-actual-learning-progressions-20261001T162834Z-142f2df1.md`
`Development`: `.standards/docs/development/integrate-actual-learning-progressions-20261001T162834Z-142f2df1.md` `PromotionReason`: `NONE` `AuditTarget`: `NONE`
`BlockedOn`: `NONE` `PendingVerificationCadence`: `NONE`

`BaselineReconciliation`: `NONE`

<!-- When non-NONE, use one Markdown list entry per source cycle:
- `SourceCycle`: `<cancelled-cycle-id>`
  `Request`: `<source-cycle request summary>`
Preserve existing entries; see PROTOCOL.md, Baseline Reconciliation Format.
-->

## Handoff

`Kind`: `USER_REWORK` `From`: `DEVELOPING` `FailureType`: `ARCHITECTURE` `Reason`:
`User asked to align support-planning page-limit wording with the other workflows; the design says support planning is unchanged.`

## Recovery

`Active`: `true`

### Frame 1

`From`: `AWAITING_USER_SIGNOFF` `Owner`: `ARCHITECTING` `FailureType`: `ARCHITECTURE`
`Reason`: `User rework after Desktop testing: LP availability missing from discovery text/filter (AC-019), component support relationship IDs absent from tool text (AC-016/AC-029), curriculum review cannot reach relatesTo (AC-015), walkthrough wording (AC-036).`
`ResumeAt`: `AWAITING_USER_SIGNOFF` `RerunThrough`: `SYNCHRONIZING`

### Frame 2

`From`: `DEVELOPING` `Owner`: `ARCHITECTING` `FailureType`: `ARCHITECTURE`
`Reason`: `User rework 2026-10-07: support-planning workflow still promises one page of 25 for its incoming/related calls; align its page-limit wording with the other workflows (design currently says support planning is unchanged).`
`ResumeAt`: `DEVELOPING` `RerunThrough`: `NONE`

## Outstanding Obligations

`Active`: `false`
