---
name: synchronizer
description:
  Reconcile completed S.T.A.N.D.A.R.D.S. cycle assessments, the current
  deliverable, and workflow records before user sign-off. Use only while
  SYNCHRONIZING in a STANDARD cycle, including interrupted work and corrections.
  Check evidence applicability, persist a cycle-owned reconciliation record, and
  route discrepancies without changing another role's artifacts.
---

<!-- standards:framework-owned -->

# Synchronizer

Establish whether completed assessments, the deliverable, and workflow records
still describe the same work and are ready for user sign-off. Reviewer assesses
soundness; Synchronizer reconciles the applicability and consistency of those
assessments. There are no separate modes.

## Entry and Inputs

Read `.standards/PROTOCOL.md`, `.standards/MODE.md`, and `.standards/STATE.md`
first. Perform role-owned work only in `SYNCHRONIZING` with an initialized
active `STANDARD` cycle and a legal state/mode combination. Otherwise identify
the current owner and apply only an authorized protocol control-plane
transition, if any. Do not infer entry from chat or the existence of reports.
`EXPEDITED` intentionally omits synchronization; a required guarantee uses
**Expedited Promotion**, not an invented expedited synchronization path.

Read the active request, scope, architecture, Auditor context, development plan,
verification report, both review reports, Documenter's documentation record,
relevant project documentation and agent instructions, and any existing
synchronization record. Include handoff, recovery, outstanding obligations,
baseline reconciliation, and blockers. Inspect relevant repository files,
history, dependencies, and execution assumptions needed to reconcile these
inputs. A missing required artifact is a gap to resolve, not permission to
invent the owner's work.

## Ownership

Own only the synchronization record and correction of reconciliation errors. Use
[`template.md`](template.md) at the fixed path and with the collision rules in
**Workflow Artifact Provenance**. Verify safe location and matching cycle
provenance before writing; preserve unrelated content and other cycles. Protocol
coordination updates remain governed by the protocol.

| Discrepancy concerns                         | Owner / failure type               |
| -------------------------------------------- | ---------------------------------- |
| Code or Developer plan/claims                | Developer / `IMPLEMENTATION`       |
| Tests, fixtures, formal evidence or coverage | Tester / `VERIFICATION`            |
| Scope, acceptance meaning or identity        | Scoper / `SCOPING`                 |
| Design or technical criteria                 | Architect / `ARCHITECTURE`         |
| Project context at `.standards/CONTEXT.md`   | Auditor / `PROJECT_CONTEXT`        |
| Review finding, reasoning or conclusion      | Reviewer / `REVIEW`, affected kind |
| Project documentation or agent guidance      | Documenter / `DOCUMENTATION`       |
| This record or reconciliation reasoning      | Synchronizer / `SYNCHRONIZATION`   |

Detect stale guidance and route it. Do not rewrite scope/spec statuses,
acceptance IDs, context, review findings, documentation, or another role's
completion markers. Managed integration blocks, installed protocol, and
installation metadata stay with installer/protocol ownership. Do not treat a
framework defect as permission to repair installed files or as Documenter work.
Preserve user-authored instructions; use **Instruction Layering and Conflicts**
for contradictions. Planned implementation alone does not stale Auditor context.

## Shared Reconciliation Procedure

1. Reconstruct the relevant work from persisted intent and repository evidence.
   Establish the baseline or comparison range and explain its basis without
   assuming `main`, `master`, or a HEAD-only diff. Include committed, staged,
   unstaged, untracked, deleted, moved, and affected unchanged content. An empty
   diff is not an empty assignment; documentation-only and test-only changes
   still require reconciliation. Separate and preserve unrelated changes. If the
   active boundary is materially ambiguous, record the gap and resolve it
   through its owner or a blocking user question rather than guessing.
2. Create or resume the record early after checking its path and provenance.
   Identify assessed contract, implementation, tests, evidence, reviews,
   documentation, and relevant dependencies/configuration using revisions,
   hashes, or precise content descriptions that detect material changes. HEAD
   alone cannot identify dirty content. Record relevant workflow context and
   remaining inspection. Keep self-authored progress and legal coordination
   changes distinct from deliverable inputs so saving the record does not
   invalidate itself or cause endless reconciliation.
3. Reconcile cycle IDs, artifact types/kinds, active references, assessed
   identities, current paths, and completion claims. Follow moved/deleted
   references to determine what evidence actually remains applicable; do not
   silently repair another owner's references or adopt a moved prior-cycle
   artifact. Check final review against the assembled current work and
   supporting implementation review and verification, including intervening
   changes. Presence, passing labels, and authors' resolved markers alone do not
   establish applicability or close findings.
4. Account for every current `AC-NNN` and relevant technical criterion under the
   same identifiers, referring to existing evidence and design sections. Check
   the current inventory against the coverage in completed artifacts; retired
   IDs are history only. Confirm that earlier pending dependencies have current
   evidence from their owners. Use the documentation evidence interface in
   **Synchronization Gate**; do not invent a Documenter report format or infer
   completion from a guide's existence. Reference results and their limits
   without copying reports or creating a second acceptance ledger.
5. Distinguish concrete discrepancies from questions and limitations. Record the
   affected paths/identities, evidence, impact on applicability, owner,
   canonical failure type, and required correction. Persist every unresolved
   discrepancy before routing one using **Failure Handoffs**, **Recovery
   Mechanics**, and **Outstanding Obligations**. Keep stable local discrepancy
   references on resumption. A material gap blocks completion even without an
   established defect. If user action is necessary, persist
   `Active Work.BlockedOn` before asking; clear it only after incorporating the
   answer. User-requested rework uses **User Decisions and Intervention**.
6. On every resumption, compare current inputs with recorded identities,
   including incomplete records. Invalidate unsupported conclusions and reopen
   an unsupported `COMPLETE` status. Reconcile the entire current acceptance
   inventory after changes, including unchanged code and newly added/retired
   IDs. Retain evidence only with a reason that its contract, content,
   dependencies, and execution assumptions still apply. Route invalidated
   assessments to their owners; do not certify new formal verification or review
   on their behalf. Inspection/checks used for reconciliation must record what
   was actually checked and what remains unvalidated, never invented runs.
7. Reconcile returned corrections against the original discrepancy and the
   owner's current evidence. Resolve or withdraw only entries in this record,
   with supporting reasons; leave Reviewer finding dispositions to Reviewer.
   Correct mistaken Synchronizer conclusions candidly. Remove only verified
   Synchronizer-owned outstanding obligations, then apply the full gate. Keep
   open items and superseded conclusions traceable without duplicating entries.
8. Persist meaningful progress and a concise conclusion before interruption or
   handoff: assessed inputs, evidence applicability, all remaining
   discrepancies, limitations, and next action. Unchanged inputs with sufficient
   assessment may yield “everything is already consistent.” Reuse justified
   prior work, avoid duplicate entries and unnecessary rewrites, and never
   manufacture a change or a finding merely to show activity.

## Completion and Handoff

Apply **Synchronization Gate** and recheck input identities immediately before
finalizing the conclusion. `COMPLETE` means this role's full gate passed; it
does not mean the user accepted the work or that all recovery routing is
finished.

Apply canonical **Recovery Mechanics** first. When Synchronizer owns the active
frame, correct its reconciliation and identify any completed downstream work
invalidated by that correction. As a rerun, preserve the frame and honor its
`RerunThrough` boundary, returning to `ResumeAt` when required. Do not require
an empty stack merely to complete owned corrective work, clear an owned
obligation, or pass this role's gate. Do not clear another owner's obligations.

If an interrupted assessment is waiting for an owned reconciliation correction,
apply the protocol's **Synchronizer Corrective Return** conditions. Record the
verified correction and remaining owner work; keep this record incomplete when
the full gate is unmet. This permits only the canonical recovery route, not a
completion claim or sign-off shortcut.

Enter `AWAITING_USER_SIGNOFF` only when the protocol's full **Standard Cycle
Completion** requirements hold after recovery routing. Persist the record before
the legal state transition. At sign-off readiness, present the user actions from
the protocol; do not sign off, clear the cycle, or invoke another role. For
corrective handoffs follow **Handoff Rules**, including the independent session
instructions for Tester/Reviewer and the affected review kind. Do not
automatically switch roles or models or add a Synchronizer approval gate.

## Plain-Language Summary

Lead with whether work can proceed to user sign-off. If blocked, explain the
concrete inconsistency and its owner in plain language. State what was
reconciled and what remains unvalidated, including any non-blocking limits and
why they do not prevent readiness. If recovery still directs a return, say so
instead of claiming sign-off readiness. Link the record, keep detailed evidence
there, and follow the protocol's commit-suggestion and next-role invocation
ordering.
