<!-- STANDARDS
Artifact: SCOPE
Cycle: integrate-actual-learning-progressions-20261001T162834Z-142f2df1
-->

# Learning Progressions in the Education MCP Server

## Goal

Enable teachers, education ministry officials, and ed-tech organizations such as EIDU, Pratham, Madhi, Trackosaurus, and Funda Wande to discover, follow, and explain the supplied buildsTowards and relatesTo relationships between Academic Standards. Connect that evidence to existing standards, Learning Components, and teaching workflows, replacing the obsolete client-generated progression-hypothesis feature.

The recommended capability set covers exact relationship inspection, per-standard connections, filtered relationship discovery, and bounded progression paths; the recommended prompt set covers teaching sequences, support planning, and curriculum review. These are required user outcomes below. Architect chooses the public names, schemas, component grouping, data representation, and implementation approach.

Rework also establishes a usable evidence and workflow surface for local Claude Desktop and the public claude.ai remote connector: ordinary tool text must carry bounded progression results, and clients must have practical access to the permitted evidence needed to use them.

Scope authority: the persisted Active Work request, the user-authorized rework and verified observations below, and `.standards/CONTEXT.md` for this cycle. The stored upstream relationships are IDinsight-generated artifacts with producer/checker provenance, not publisher-endorsed progressions. Removing the obsolete hypothesis feature must preserve that truthful origin disclosure.

## Constraints

- Keep the existing server deterministic and read-only, with no server-side LLM calls, MCP sampling, or curriculum-specific Python behavior. Retain established rights, exposure limits, immutable accepted-package/profile identity, and package-local isolation.
- Preserve useful Academic Standards and Learning Components behavior. Backwards compatibility for removed progression behavior and old public inventory counts is unnecessary; do not maintain obsolete aliases or inferred-hypothesis fallback workflows.
- Developer's first step is to help copy the relevant files from `/Users/tzz/Projects/private/idi/KGForEdGlobal/results/kg_for_ed` into a temporary or permanent location in this repository. The external source must not be modified or become a runtime dependency.
- Prefer adaptation of the existing machinery. Architect must explain any significant structural changes in simple language and recommend the least disruptive viable approach.
- Tests must not call live LLM APIs or paid services. Such dependencies, if encountered, must be mocked; the `costs-money` marker does not waive this rule.
- Deployment and sign-off are user-owned. Verification of local startup/transports/distribution content and the shared server contracts intended for the public claude.ai connector is in scope; updating or publishing the deployed service is excluded. Actual claude.ai acceptance follows the user's deployment update and is not a prerequisite for completing local rework. Local HTTP evidence must never be described as public-client acceptance.
- Preserve useful structured results and native MCP resources/prompts, including Desktop's demonstrated native prompt route. Do not assume native prompts or all resource reads are broken. Preserve stored graph judgments, exact identity, generated-origin disclosures and relationship semantics; choose any additional access/fallback only to meet the established client needs. All emitted representations count toward applicable finite byte limits; additional routes cannot bypass rights, safe-artifact policy or bounds.

## Non-goals

- Generate, regenerate, independently certify, edit, or approve upstream learning-progressions judgments; add a human review/authoring system; persist generated client suggestions as graph edges.
- Infer new progression edges from hierarchy, grade/code order, text similarity, Learning Component overlap, or an LLM. Preserve disclosures of generated origin in the stored artifacts and useful generated LC/comparison content.
- Create cross-framework or cross-snapshot progression edges, equivalence/alignment overlays, automatic curriculum mappings, or a new global merged source graph.
- Diagnose learner mastery/readiness, prescribe mandatory prerequisites, optimize a personalized learning path, or claim pedagogical correctness from structural validation.
- Add embeddings/semantic search, learner-data storage, a new UI, hosted deployment changes, unrelated refactors, or exhaustive repair of pre-existing repository/test/documentation deficiencies.
- Regenerate stored judgments, invent missing edges, restore obsolete hypotheses, add server-side LLM calls, or add blanket workflow wrappers without a demonstrated client-access need. Public deployment updates and actual remote acceptance testing remain separate user-run follow-up work.

## Work

### 1. Establish complete, locally retained progression evidence

**Intent:** Make all six supplied curricula usable through the existing server while preserving their standards/components and the evidence behind every added relationship.

**Done when:**

- `AC-001`: Before implementation changes, Developer helps make repository-local copies of the relevant Academic Standards, Learning Components, and Learning Progressions inputs for all six audited curricula, records the selected source paths and exact-byte checksums, verifies the copies, and leaves the external source files unchanged.
- `AC-002`: All six curricula load accepted buildsTowards and relatesTo relationships whose identifiers and endpoints agree with the copied source. The audited baseline is 3,039 buildsTowards and 5,041 relatesTo edges, with per-framework counts in CONTEXT.md; copy-time reconciliation accounts for every exported edge and any changed input explicitly rather than silently dropping or inventing relationships. Runtime startup and queries work with only repository/package inputs, without access to the external project.
- `AC-003`: Package acceptance validates progression types, identifiers, standard endpoints, count agreement, declared artifacts/checksums, and relationship-provenance coverage. It detects malformed/duplicate relationships and buildsTowards cycles separately from hasChild hierarchy validation, exposes clear findings, and never publishes invalid inputs as accepted evidence. Valid standards/component hierarchy and supports data remain intact.
- `AC-004`: Upstream validation notices, eligibility/coverage limitations, relationship judgment warnings, unresolved items, and the CBSE needs_review claim remain inspectable. Unresolved/rejected/no_relation claims are not returned as accepted progression edges; an absent edge is not advertised as proof that no pedagogical relationship exists.

**Depends on:** None. The audited source mapping and baseline are in `.standards/CONTEXT.md`.

### 2. Query and navigate stored relationships

**Intent:** Answer practical questions such as what supports this target, what it builds towards, what else it relates to, and how two standards are connected, without asking the client to invent edges.

**Done when:**

- `AC-005`: An MCP tool capability retrieves one exact progression relationship by its relationship identifier within an exact framework/snapshot route, returning its type, stored direction/endpoints, both standards, and evidence identity; unknown relationship IDs are distinguished from a valid empty query.
- `AC-006`: An MCP tool capability retrieves direct connections of a selected standard: incoming and outgoing buildsTowards, and relatesTo links from either endpoint of the canonically stored pair. It distinguishes the three meanings, deduplicates returned relationships, preserves their original IDs/direction, and supports unambiguous exact-standard selection using the existing identifier conventions.
- `AC-007`: An MCP tool capability discovers stored progression relationships within a selected framework/snapshot using relationship-type and endpoint grade/stage and statement-type filters. Results state which endpoint scope the filters apply to and retain local versus normalized grade distinctions. Existing topic/standard/component search can lead to this capability; lexical matches never become progression evidence unless a stored edge exists.
- `AC-008`: MCP tool capabilities support bounded upstream/downstream buildsTowards traversal and bounded directed connecting paths between two selected standards in the same framework/snapshot. Every returned hop cites an existing relationship in the correct direction; relatesTo and hasChild are not substituted for progression hops. Multi-hop reachability is explicitly derived path evidence, not a newly asserted direct relationship or compulsory teaching order.
- `AC-009`: Relationship collections and path/traversal requests enforce finite service and protocol bounds on returned evidence and search effort, return deterministic results for identical accepted inputs/requests, and report limits, truncation/completeness, and continuation where applicable. Invalid routes/filters/bounds, unavailable progression capability, missing standards, complete empty results, and incomplete searches are distinguishable; a bounded search that finds no path does not assert global disconnection.

**Depends on:** 1.

### 3. Provide provenance, traceability, and accurate explanation

**Intent:** Let a teacher or official inspect why a relationship exists and trace it back to its exact retained artifacts without overstating its authority.

**Done when:**

- `AC-010`: Progression results and prompt evidence preserve relationship/endpoint IDs, exact framework/snapshot/package identity, author/provider/attribution/license, and generated epistemic origin. buildsTowards is described as directional support for success, not a mandatory prerequisite; relatesTo expresses a meaningful conceptual/skill link without sequence/dependency. Neither is presented as publisher-endorsed or pedagogically certified.
- `AC-011`: Read-only MCP resources provide exact progression relationship content and per-relationship provenance, addressable by stable package-local identity and linked from query results. Provenance exposes the retained rationale, confidence as a model judgment rather than a calibrated success probability, warnings, candidate evidence/references, and producer/checker trace with source/config/content hashes. Available retained evidence is accessible without silently synthesizing missing provenance.
- `AC-012`: Progression provenance, validation, unresolved/coverage evidence, and any exposed progression artifacts obey the same rights/full-text/bulk/byte-limit and safe-artifact policies as existing resources. Resource metadata identifies content hashes, source-artifact hashes, and exact package/profile identity; denied or oversized content is explicitly reported rather than bypassed or presented as complete.

**Depends on:** 1 and 2.

### 4. Make progression evidence useful in educational workflows

**Intent:** Offer three focused prompt workflows and extend existing teaching/study workflows with stored relationships and supporting Learning Components.

**Done when:**

- `AC-013`: A distinct invocable teaching-sequence prompt workflow retrieves stored progression links/paths for selected standards or a topic resolved through existing search, separates directional steps from related concepts, retrieves supporting Learning Components, and instructs the client to produce a cited, adaptable teaching sequence. Suggested activities and ordering choices are labeled as generated pedagogy; no unsupported edge is added when coverage is sparse.
- `AC-014`: A distinct invocable support-planning prompt workflow starts from a target standard and teacher-supplied learning context, retrieves incoming progression evidence and relevant supporting components, and instructs the client to propose cited review/practice options and alternative next steps. It distinguishes reported observations from generated suggestions and makes no automatic mastery diagnosis or mandatory prerequisite claim.
- `AC-015`: A distinct invocable curriculum-review prompt workflow supports ministry/ed-tech inspection of a bounded framework, grade/stage, or standards scope: relationship coverage/counts, directional connections, conceptual links, warnings/unresolved evidence, and exact provenance citations. It distinguishes limited candidate coverage and structural/process validation from curriculum omission or pedagogical validation and never invents cross-framework progression/alignment.
- `AC-016`: Existing teacher-guide, student-study, student-handbook, and multigrade prompts can retrieve applicable stored progression evidence together with Academic Standards and Learning Components. They cite the relationships they use, keep generated pedagogy/LC evidence and source standards distinct, explain unavailable/empty/incomplete progression evidence, and preserve their useful existing outputs without reverting to an inferred-edge fallback. Shared disclosures remain accurate in administrator/comparison workflows.

**Depends on:** 2 and 3.

### 5. Retire obsolete progression behavior and preserve useful features

**Intent:** Complete replacement rather than retaining parallel hypothesis machinery, while keeping the established standards/components server reliable.

**Done when:**

- `AC-017`: The old collect_progression_evidence tool and inferred_progression_hypothesis prompt, their candidate-hypothesis logic/models, dedicated registration/bootstrap/exports, progression heuristics, per-framework hypothesis overlays, and obsolete active configuration/reference expectations are removed or replaced. No callable alias, dormant hypothesis implementation, or inferred-edge fallback remains. Generated-origin disclosures, LC generation metadata, and unrelated useful comparison inference are retained.
- `AC-018`: Framework discovery, standard/component search and exact lookup, hierarchy/context, standard-component support links, existing provenance/rights enforcement, statistics, and cross-framework comparison remain usable across all six curricula. Adding LP edges does not contaminate hasChild parents/root paths or LC supports, change standard/component identity or source text, flatten multi-parent DAGs, or treat relatesTo as structural ancestry.
- `AC-019`: Framework/capability discovery truthfully reports progression availability for exact packages and the current tool/prompt/resource surface. Framework statistics include separately identified buildsTowards and relatesTo counts consistent with queryable stored edges; existing hierarchy/component counts retain their original meaning.

**Depends on:** 1–4.

### 6. Keep integration proportionate and operationally complete

**Intent:** Make the change understandable and usable through the existing local interfaces and distribution boundary.

**Done when:**

- `AC-020`: Before implementation, the architecture artifact identifies which existing machinery will be reused and recommends an approach consistent with the read-only, curriculum-agnostic server. Any significant change to storage/runtime boundaries, package/profile contracts, or service structure is justified with a simple explanation of the need, alternatives, and user impact; broad restructuring is not assumed necessary merely because LP is a new graph type.
- `AC-021`: STDIO and local Streamable HTTP expose the same revised tools, prompts, resources, schema/error behavior, and accepted data. Registration, advertised capabilities, and shared smoke expectations agree; startup/representative queries do not depend on the obsolete hypothesis service or external source folder.
- `AC-022`: The existing MCPB distribution includes the revised runtime, required configuration, and complete locally accepted progression/provenance artifacts, and its retained staged runtime passes the relevant local smoke checks. No deployed endpoint or published distribution is updated as part of this cycle.

**Depends on:** Architecture justification precedes implementation; completed interface/distribution outcomes depend on 1–5.

### 7. Establish independent, deterministic verification

**Intent:** Prove the new relationship behavior and relevant regressions despite the current absence of test cases.

**Done when:**

- `AC-023`: Meaningful automated tests cover the current progression contracts: directed and symmetric lookup, filters, branches/multiple paths, finite limits/truncation and cycle safety, empty/missing/unavailable distinctions, provenance/hash/rights failures, invalid input rejection, obsolete-surface removal, and affected standards/component regressions. Real cases are collected and executed; no-test collection or a marker alone cannot count as verification.
- `AC-024`: All tests and acceptance fixtures operate without live LLM APIs or paid-service calls. Any such boundary is mocked, including negative/error paths; local MCP client/server protocol checks require no model invocation.
- `AC-025`: Independent Tester evidence accounts for every current acceptance condition, with executed local package acceptance, affected service/static checks, revised STDIO/local HTTP and retained-stage smoke checks, and justified phase dependencies. Results identify the assessed inputs, commands, pass/fail outcomes, and limitations; unresolved required checks or material defects cannot be treated as completion.

**Depends on:** 1–6 for executable evidence. Documentation outcomes in 8 may remain explicit later-role dependencies until Documenter completes them.

### 8. Document the usable replacement

**Intent:** Help teachers, officials, and integrators discover and correctly use the new capabilities and maintain the copied package evidence.

**Done when:**

- `AC-026`: User-facing guides/reference and examples describe the implemented relationship queries/resources and all three new workflows, including exact identity, direction versus relatedness, grades/filters, bounds/continuation, generated origin, provenance/confidence/warnings, rights, and absent-edge/coverage limits. Examples show teaching/support/curriculum-review use with standards and components. Old hypothesis instructions and stale inventory counts are replaced; affected documentation passes its strict build.
- `AC-027`: Maintainer-facing documentation explains the selected source-copy inventory, verification/normalization and accepted-package update process, LP validation/provenance artifacts, mock-only test rule, and local verification commands. It records significant integration changes in simple language where applicable and distinguishes local preparation from user-owned deployment.

**Depends on:** 1–6 and current implementation/verification evidence from 7; Documenter owns the resulting documentation.

### 9. Make bounded results, evidence and workflows accessible to intended clients

**Intent:** Close the verified Desktop text and inspected resource-access gaps while establishing a supported server surface for local Desktop and the public claude.ai remote connector.

**Done when:**

- `AC-028`: A client consuming ordinary tool text without structuredContent can inspect the complete bounded result returned by each of the five progression operations: exact framework/snapshot/package and relationship/endpoint identifiers, endpoint statements, stored types/direction, confidence and warnings with their disclosures, direct connections or ordered path/traversal evidence, evidence URIs, effective selection/limits, counts and completeness/truncation reasons. Text supplies actual continuation cursor values and how to use them where pagination exists, and explicitly identifies noncontinuable operations. Bounded excerpts/omitted fields are labeled and linked to the supported full-evidence route; summary counts or links alone do not satisfy this condition.
- `AC-029`: Clients using the intended tool-access path can retrieve the full permitted retained provenance and supporting evidence required by progression and affected Academic Standards/Learning Components workflows, including full endpoint/standard/component content where permitted, exact relationship and standard/component provenance, rationale, all warnings, candidate references, producer/checker traces, coverage/eligibility, validation and unresolved records. Returned identities/links are usable in that supported path without depending on arbitrary resource-URI search in Desktop's attachment menu. Complete permitted content remains distinguishable from excerpts, absent evidence, denied content and oversized content; missing trace is never synthesized.
- `AC-030`: The three progression workflows and affected existing standards/components workflows have a supported way to obtain their deterministic instructions on local Claude Desktop and the intended public claude.ai remote connector surface. Desktop retains its working native prompt discovery/retrieval route and all nine native prompt registrations remain useful. Any additional workflow-instruction access is limited to the assessed client need, preserves the same exact route, rights, bounds, citations and generated-pedagogy disclosures, and supplies usable retrieval steps through that client's supported evidence path; unsupported client features are explicitly identified.
- `AC-031`: The revised text, evidence and any workflow-access surfaces preserve useful structuredContent and native resources/prompts, deterministic rendering/retrieval, exact package/snapshot/profile and source/content-hash identity, stored graph judgments, original relationship semantics and generated-origin disclosures. Rights/full-text/bulk/safe-artifact policy and finite output/search/source-read limits apply consistently across every access route and all emitted representations, including combined text plus structured tool output. Denied, oversized, partial and unavailable results are explicit; alternate access cannot silently clip full evidence, bypass policy, loop without progress or infer additional edges.

**Depends on:** 1–6; client-support assessment in 10 precedes any implementation choice.

### 10. Assess the least disruptive client compatibility design

**Intent:** Let Architect resolve the client-access contract using demonstrated support and existing services, without imposing public names or unnecessary wrappers in scope.

**Done when:**

- `AC-032`: Before rework implementation, Architect records a client-support assessment that respects the verified Desktop observations, distinguishes known support from untested public claude.ai behavior, and defines how the required results/evidence/workflow instructions can be obtained on each intended surface. It evaluates bounded ordinary result text with combined byte accounting, reuse of existing resource services through appropriate tool-accessible evidence, and whether any workflow-instruction fallback is actually necessary. It recommends the least disruptive viable option, explains meaningful alternatives/user impact simply, and leaves no required workflow dependent solely on an inaccessible client feature. These candidates do not predetermine public names, schemas or designs.

**Depends on:** Existing cycle contracts, current implementation/evidence records and the rework observations below; precedes implementation for 9.

### 11. Verify the revised consumption and distribution boundaries

**Intent:** Establish locally reproducible compatibility evidence beyond the earlier structured-result smoke checks.

**Done when:**

- `AC-033`: Meaningful offline automated cases consume only ordinary tool text from all five progression tools and establish the observable result contract in 9, including nonempty exact/direct/search/traversal/path evidence, returned identifiers and statements, confidence/warnings/evidence links, real cursor replay without loss/duplication, complete empty versus partial outcomes, and byte-boundary/oversized behavior counting all emitted representations. StructuredContent is retained and assessed separately; parsing only it cannot establish text-only consumption. No live model or paid service is called.
- `AC-034`: Independent verification executes the revised shared STDIO and local Streamable HTTP contracts, including text-only consumption and the chosen evidence/workflow access routes, and records exact inputs, commands, outcomes and limits. It checks the supplied Nigeria diagnostic relationship/target at the exact snapshot, full original provenance and representative standards/component supporting evidence, coverage/validation/unresolved access including CBSE needs_review and Ghana warning records, rights/source/return-size/error boundaries, actual pagination, preserved native prompt/resource behavior and affected AS/LC/workflow/discovery/schema regressions. Rendered instructions and protocol reads are distinguished from an end-to-end teaching workflow or actual public claude.ai acceptance.
- `AC-035`: The final retained MCPB archive/stage is refreshed as required to reflect the chosen revised surface, with accurate shipped instructions and complete permitted runtime evidence. Its own staged runtime exercises text consumption, evidence access and workflow invocation/discovery with the final schemas/counts and preserves native prompts/resources. Current source/archive/stage identities and applicable regression evidence are reconciled; older candidates/receipts remain historical. No bundle is published or deployed.

**Depends on:** Implemented outcomes in 9, design assessment in 10 and the existing local verification obligations in 7; later documentation claims require current 8 and 12 evidence.

### 12. Give users practical client walkthroughs and honest compatibility claims

**Intent:** Make the revised surface usable and distinguish prepared local evidence from user-run client acceptance.

**Done when:**

- `AC-036`: Current documentation provides a practical user-run Claude Desktop walkthrough with exact diagnostic framework/snapshot/relationship/target identifiers and observable expected results: discovery, progression search/exact/direct/traversal/path text, actual pagination, full permitted provenance/supporting evidence and coverage/validation/unresolved access, Catalog attachment and the preserved native support-planning prompt route. It includes at least one bounded teaching/support workflow through evidence retrieval and cited output, explains policy/size/partial outcomes, and records whether steps are prepared, actually run, passed or limited. Prior prompt rendering, Catalog read and structured smoke success are not presented as an end-to-end workflow pass.
- `AC-037`: User/integrator documentation describes the final supported local Desktop and intended public claude.ai connector invocation/evidence paths and actual public schemas/counts, plus a practical remote acceptance checklist for use after the user updates deployment. It clearly separates verified shared-server STDIO/local HTTP/stage behavior, user-reported Desktop observations, prepared walkthroughs and untested public-client behavior. Deployment timing, actual remote acceptance and sign-off remain user-owned follow-up; completing local rework requires an honest checklist and local contract evidence, not a deployment update or fabricated remote pass. Affected documentation and retained shipped instructions agree and pass the strict documentation build.

**Depends on:** 8–11 and the final chosen interfaces; Documenter owns the guides/checklists and saved-content evidence.

## Assumptions

- This cycle covers the six audited curricula and their retained upstream exports. Exact copy-time bytes must be reconciled; a material change in source identity/content or eligibility is surfaced before depending on the audit totals, rather than silently changing the feature contract.
- Stored, provenance-backed generated LP relationships are suitable inputs for retrieval/planning with accurate disclosures. The requested removal concerns the obsolete on-demand hypothesis machinery, not truthful attribution in those stored artifacts.
- Topic entry can reuse existing lexical standard/component discovery; a new semantic relationship search engine is unnecessary for the requested outcomes. Exact endpoint matching/filter rules, traversal budgets, public names/schemas, resource grouping, and immutable package-version strategy belong to Architect.
- Normal finite queries should be useful on the supplied six curricula. There is no user-specified latency/concurrency benchmark or requirement for unlimited path enumeration; Architect establishes practical finite bounds and technical checks.

## Rework Evidence and Recovery — 2026-10-03

Scoper REPLAN preserves this cycle and the unchanged meanings/wording of all 27 earlier acceptance conditions. Ten new conditions cover client access, Architect's support assessment, independent local verification/distribution and Documenter's walkthrough/remote checklist. No acceptance identifier is retired or reused. The original Auditor context remains the established baseline; planned active-cycle implementation and new user-supplied compatibility observations do not alone require an audit rerun. This session changes only Scoper-owned scope and protocol coordination, with no fixes, tests, design or other owner-record edits.

### Verified observations supplied by the user

- Local STDIO smoke passed. The inspected shared smoke checks structured results from all five progression tools and representative resources including progression provenance; that pass does not prove text-only client consumption.
- Local Desktop connected, discovered six frameworks/current capabilities, and successfully searched and exactly looked up progression evidence. Claude reported summary-only text; expanded exact-lookup output showed counts, disclosures, snapshot identity and summary URI, without inspectable edge records, endpoint statements, confidence/warnings, evidence URIs or continuation cursors. Source inspection found detailed structuredContent alongside summary-only text in all five tools.
- Desktop supports native prompts: all nine appear under “Add from curriculum-knowledge-graph”; support planning rendered an attachment using an exact standard/snapshot. Desktop also supports resource reads: Catalog produced an attachment containing six frameworks. Logs recorded actual prompts/get and resources/read during these checks.
- The inspected resource menu offered only Catalog. Searching the returned progression-summary URI gave “No results”; per-edge provenance was not offered. This is a gap in the inspected access path, not evidence that Desktop universally lacks resource support.
- No teaching workflow was executed end-to-end in the inspection. The public deployment has not been tested for these compatibility issues. No new Desktop/public-client execution is claimed by Scoper.

Diagnostic identifiers (preserve exactly):

- frameworkId: `nigeria-nerdc-mathematics-primary-1-3`
- snapshotId: `nigeria-nerdc-mathematics-primary-1-3@undated+bc5e769ed26f`
- relationshipId: `0129f5d5-42fd-52cb-bcf2-ec07c47103e7`
- support-plan target nodeId: `e399b510-48bb-58ee-abda-61460a5a853b`

### Downstream invalidation and recovery route

Entry STATE was AWAITING_USER_SIGNOFF / STANDARD, with no recovery, outstanding obligation or blocker. Its FORWARD handoff from SYNCHRONIZING claimed all earlier contracts/assessments/documentation/distribution applicable and awaited explicit sign-off, rework or cancellation. User explicitly requested rework, so USER_REWORK from AWAITING_USER_SIGNOFF routed the earliest changed contract to SCOPING with FailureType SCOPING; Frame 1 preserves that interrupted state as ResumeAt. Existing cycle ID, artifact references, baseline and completed historical evidence remain intact. Active Work.Request retains the original request plus this authorized change.

Acceptance Traceability and Recovery Mechanics require re-establishing completed downstream contracts/evidence for the new identifier set. The following records are invalidated as current full-completion claims, while their valid decisions, stable identifiers, findings and execution history remain available for selective reuse under their owners:

- ARCHITECTING — `.standards/docs/specs/integrate-actual-learning-progressions-20261001T162834Z-142f2df1.md`: account for every current condition and revise the summary-only/evidence/workflow client contract; public names/design remain Architect-owned.
- DEVELOPING — `.standards/docs/development/integrate-actual-learning-progressions-20261001T162834Z-142f2df1.md`: reconcile the revised design and new implementation/distribution work under the existing plan, retaining valid DONE steps, historical evidence, locked style, collaboration/approval and cadence rules.
- TESTING — `.standards/docs/verification/integrate-actual-learning-progressions-20261001T162834Z-142f2df1.md`: account for the expanded current set and independently establish text/client-access/regression/transport/distribution evidence; prior structured-only smoke cannot satisfy the new text condition.
- REVIEWING_IMPLEMENTATION — `.standards/docs/reviews/integrate-actual-learning-progressions-20261001T162834Z-142f2df1/implementation.md`: reassess the revised contract, implementation and full verification; retain earlier assessment/findings history.
- DOCUMENTING — `.standards/docs/documentation/integrate-actual-learning-progressions-20261001T162834Z-142f2df1.md`: reconcile final access routes, examples/counts/shipped content, walkthrough/checklist and strict/current-content evidence.
- REVIEWING_FINAL — `.standards/docs/reviews/integrate-actual-learning-progressions-20261001T162834Z-142f2df1/final-deliverable.md`: independently re-establish every current condition and assembled-deliverable consistency; earlier resolved findings stay historical owner dispositions.
- SYNCHRONIZING — `.standards/docs/synchronization/integrate-actual-learning-progressions-20261001T162834Z-142f2df1.md`: reconcile all refreshed assessments, current evidence/distribution and complete expanded contract.

After Scoper's full gate passes, the earliest required rerun is ARCHITECTING and RerunThrough is SYNCHRONIZING. Preserve the Scoper-owned frame through ARCHITECTING → DEVELOPING → TESTING → REVIEWING_IMPLEMENTATION → DOCUMENTING → REVIEWING_FINAL → SYNCHRONIZING. Only at the successful SYNCHRONIZING boundary pop this frame and return by RESUME to AWAITING_USER_SIGNOFF; apply nested failure/recovery rules for any newly discovered defect. Other owners reopen/reconcile their own records; Scoper does not relabel their statuses, certify fresh evidence or bypass their gates. No new cycle, cancellation, sign-off, public deployment or actual remote acceptance is performed by this route.

### Scoper completion gate

Completed in REPLAN on 2026-10-03. Current-cycle provenance and the same canonical Scope path are valid; the required Goal/Constraints/Non-goals/outcome-oriented Work/Dependencies/Assumptions shape is preserved. All verifiable original and rework outcomes have current scope-level acceptance conditions, with Architect, implementation/verification and documentation obligations represented separately. Every original condition is byte-identical to the entry scope; all ten new IDs were allocated sequentially with the runtime ID tool and persisted before the next allocation. There are 37 unique current conditions, no retired/reused IDs, and no unresolved scope question. The checker reports no Scoper-owned problem and git diff --check passes. The completed scope authorizes the Architect recovery rerun, not implementation or deployment in this session.
