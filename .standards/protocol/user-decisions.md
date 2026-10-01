# S.T.A.N.D.A.R.D.S. Protocol: User Decisions

This chapter is part of `.standards/PROTOCOL.md`. Read that file first; its
reading guide says when this chapter applies.

## Choose the next cycle's mode

While no cycle is active, or before the initialized first cycle has received its
request, an explicit user instruction may set `PendingCycleMode` to a mode
supported by the current `ProjectMode`, replace an earlier pending preference,
or clear it to `UNSET`. Leave `CycleMode: UNSET` and `Active Work` unchanged;
the selection does not activate a cycle. The latest selection survives across
sessions until a cycle consumes it or the user replaces or clears it. While a
blocked `PendingCycleRequest` exists, a mode change or clear revalidates that
request under **Start a cycle** without asking the user to repeat it.

## Start a cycle

A cycle starts from the installed state, where `Active Work.Id`,
`Active Work.Request`, and `CycleMode` are `UNSET`, or from `SIGNED_OFF` or
retained `CANCELLED`; a finished cycle is never reopened. The request is the
user's new request or, when one exists, the persisted `PendingCycleRequest`: use
it without asking the user to restate it, and let a revised request replace it.

1. **Determine the reconciliation obligation** the new cycle would carry,
   without writing it yet. For the first cycle and from `SIGNED_OFF`, it is
   `NONE`. From retained `CANCELLED`, it preserves any existing
   `BaselineReconciliation` and, unless the user explicitly confirms that the
   just-cancelled cycle left no project changes because none were produced or
   they were reverted, adds a `SourceCycle`/`Request` entry for that cycle under
   **Baseline Reconciliation Format** if its exact cycle ID is not already
   listed.
2. **Choose the mode before changing any state.** A pending preference must be
   valid for the request, the current `ProjectMode`, and the reconciliation
   obligation; a pending `STANDARD` preference also prevents Developer from
   inferring `EXPEDITED`. Without a pending preference, `STANDARD` is the
   default, except that in `BROWNFIELD` an explicit Developer invocation with a
   sufficiently bounded implementation request may select `EXPEDITED`.
   `GREENFIELD` supports only `STANDARD`, and unresolved reconciliation requires
   `STANDARD`. A pending `EXPEDITED` preference does not bypass the **Expedited
   Cycle Contract** in `.standards/protocol/expedited.md`: validate eligibility
   before consuming it.
3. **Block instead of starting when the mode is not legal**, whether because of
   an invalid pending preference or an explicitly requested mode the current
   `ProjectMode` does not support. Never silently reinterpret the mode as
   `STANDARD` or persist an unsupported mode. Leave `WorkflowState`,
   `Active Work`, `CycleMode`, and `PendingCycleMode` unchanged; persist the
   request in `PendingCycleRequest` and the specific decision required in
   `PendingCycleBlockedOn`, not in `Active Work.BlockedOn`; and ask the user to
   choose a supported mode, replace or clear the preference, revise the request,
   or abandon it. Abandoning clears `PendingCycleRequest` and
   `PendingCycleBlockedOn` without modifying `Active Work` or starting a cycle.
4. **Generate the ID** as **Cycle IDs** describes. If the tool refuses, leave
   the state unchanged and do not start the cycle.
5. **Persist the cycle** in one state update:
   - `Active Work`: the new ID and request; `Scope`, `Architecture`,
     `Development`, `PromotionReason`, `AuditTarget`, and `BlockedOn` set to
     `NONE`; `PendingVerificationCadence: NONE`; and `BaselineReconciliation`
     from step 1.
   - `CycleMode`: the chosen mode. `PendingCycleMode` and `PendingCycleRequest`
     become `UNSET`, and `PendingCycleBlockedOn` becomes `NONE`.
   - `Handoff`: for the first cycle, keep `Kind: INITIAL` with `From: NONE` and
     `FailureType: NONE`; from a terminal state, record `Kind: NEW_CYCLE`,
     `From` set to that state, `FailureType: NONE`, and a concise reason. An
     expedited first cycle records a concise expedited-entry reason. Mention an
     unresolved reconciliation obligation concisely, without copying its
     source-cycle provenance.
   - Recovery and outstanding obligations inactive.
   - `WorkflowState`: `AUDITING` when reconciliation is unresolved or
     cancelled-cycle changes are being retained or adopted, so Auditor
     establishes baseline status first. Otherwise `DEVELOPING` for an allowed
     `EXPEDITED` cycle, or the standard entry state for the current
     `ProjectMode`: `SCOPING` for `GREENFIELD` or `AUDITING` for `BROWNFIELD`.

`CycleMode` never remains `UNSET` once a cycle has started.

## Switch verification cadence

An explicit user instruction may select `INCREMENTAL` or `AFTER_IMPLEMENTATION`
for the active cycle under **Verification Cadence**. Record and apply it as
follows, preserving collaboration-mode permissions and pauses. The coordination
rules in **State-update rules** apply throughout.

1. **Promote when needed.** `EXPEDITED` supports only `AFTER_IMPLEMENTATION`. An
   explicit `INCREMENTAL` request authorizes **Expedited Promotion** in
   `.standards/protocol/expedited.md`. Preserve the request as pending during
   promotion and follow the Auditor handoff. Evaluate remaining scheduling after
   the standard contract is established.
2. **Check whether there is work to schedule.** Accept the request during an
   active cycle while implementation or its increment scheduling remains
   unfinished, including before a development plan exists or during recovery.
   Once the current contract and recovery route establish that no implementation
   or increment scheduling remains, clear pending intent and explain why the
   switch has no remaining effect. Do not rely on completion claims invalidated
   by rework or promotion, or reopen work solely to change cadence. No request
   is retained for an unset, signed-off, or cancelled cycle.
3. **Persist the latest request.** Any current role may record the explicit
   request in `Active Work.PendingVerificationCadence`. Replace an earlier
   pending choice with the latest one. A request matching the effective cadence
   cancels an opposite pending choice; if no plan exists, retain the explicit
   selection for Developer to apply when creating it.
4. **Apply only at a safe Developer boundary.** Developer applies the pending
   choice during normal `DEVELOPING`, before its next implementation action or
   checkpoint assignment. Finish any already assigned Tester assessment and its
   required return first. During recovery, defer application until the preserved
   route returns to normal development. Until then, the saved effective setting
   governs the assignment.
5. **Reconcile scheduling under existing approval rules.** When enabling
   `INCREMENTAL`, group planned work into testable outcomes and select the next
   increment, including implemented work still needing assessment. When enabling
   `AFTER_IMPLEMENTATION` at the safe boundary, clear `Current Increment`,
   including an increment selected but not yet handed to Tester, and schedule
   remaining implementation before full verification. Retain previous increment
   definitions and evidence; reconcile changed inputs under normal ownership.
   Pure cadence selection and grouping of unchanged approved steps do not
   require duplicate approval. Material changes to steps, dependencies,
   behavior, or technical approach still require plan approval.
6. **Save effective selection before clearing pending intent.** Persist the
   plan's cadence and reconciled scheduling first, then clear
   `Active Work.PendingVerificationCadence` to `NONE`. If interrupted between
   those writes, Developer reconciles the matching request and clears it
   idempotently. Report whether the switch was applied or remains pending.

Cycle lifecycle rules clear pending intent on cancellation, sign-off, reset, or
new-cycle initialization; it never becomes a preference for a later cycle.

## Promote an expedited cycle

An explicit user instruction may authorize **Expedited Promotion** in
`.standards/protocol/expedited.md` from any nonterminal expedited brownfield
state, including `AWAITING_USER_SIGNOFF`. After persisting promotion, stop and
hand off to Auditor unless Auditor was also explicitly invoked.

## Sign off

From `AWAITING_USER_SIGNOFF`, sign-off is legal only when the
`Outstanding Obligations` section is inactive. Revalidate the current mode's
completion contract: **Standard Cycle Completion**, including every standard
gate and the acceptance-traceability obligations, or, for `EXPEDITED`, only the
narrower **Expedited Cycle Contract** in `.standards/protocol/expedited.md`;
skipped standard phases must not be represented as completed. Then transition to
`SIGNED_OFF`, set `CycleMode: UNSET`, leave all pending-cycle fields clear,
record `Handoff.Kind: SIGNOFF`, `From: AWAITING_USER_SIGNOFF`, and
`FailureType: NONE`, clear `Active Work.PendingVerificationCadence` to `NONE`,
and clear recovery. The cycle is complete.

## Cancel an active cycle

- If `ProjectMode: GREENFIELD`, follow **Greenfield Bootstrap Cancellation**,
  including explicit approval of the reset before it runs.
- If `ProjectMode: BROWNFIELD`, transition to `CANCELLED`, set
  `CycleMode: UNSET`, leave all pending-cycle fields clear, record
  `Handoff.Kind: CANCEL`, set `From` to the interrupted state,
  `FailureType: NONE`, preserve `Active Work` except for clearing
  `PendingVerificationCadence` to `NONE`, and clear recovery plus outstanding
  obligations. Residual project-change provenance is handled through
  `BaselineReconciliation` when a later cycle starts.

Cancellation never reverts project artifacts and does not by itself establish
cancelled-cycle project changes as baseline.

## Greenfield Bootstrap Cancellation

If cancellation occurs while `ProjectMode` is still `GREENFIELD`, first verify
that the active cycle has not successfully created or materially modified a
project implementation artifact, regardless of authorship. If it has, persist
the permanent `BROWNFIELD` transition and use retained brownfield `CANCELLED`
semantics instead, even if recovery has moved to an earlier workflow state. Only
when no such implementation exists is cancellation a reset of the workflow
rather than a reusable terminal cycle.

The agent performs the reset with **Project Reset**, following **Running the
CLI**, both in `.standards/protocol/installation.md`:

1. Use `standards reset --mode greenfield` if a globally installed STANDARDS CLI
   has the version recorded in `.standards/VERSION.json`; otherwise use
   `npx @idinsight/standards@<that version> reset --mode greenfield`. The cycle
   produced no implementation, so the project stays `GREENFIELD`; do not let the
   reset choose the mode from the project's files.
2. Preview it with `--dry-run`, which may run before approval. Also warn that
   the reset deletes the saved workflow state, the Auditor's project context,
   and every cycle record under `.standards/docs/`, and that the skills, hooks,
   client settings, and user styles stay installed.
3. Ask for explicit approval to run the exact command with `--yes`. A generic
   cancellation request does not grant it. Record the target, command, and
   pending approval in `Active Work.BlockedOn`, preserving any other unresolved
   questions, and keep the workflow state, cycle mode, recovery, and outstanding
   obligations intact while waiting. Do not record `CANCELLED` or continue role
   work while approval is pending. A resumed chat must resolve the saved
   question; silence or a request to continue is not approval.
4. After approval, recheck bootstrap eligibility and the preview. If
   implementation now exists, persist `BROWNFIELD` and use retained cancellation
   instead. If the target, command, planned changes, or warnings changed, obtain
   fresh approval for the updated preview. Otherwise run the approved command
   with `--yes`; the flag avoids a second CLI prompt and never substitutes for
   user approval.
5. Confirm that the reset succeeded before reporting the cancellation complete.
   Do not edit `STATE.md` afterwards to record it; the fresh state is the
   result. Reset approval authorizes only the reset, not starting a new cycle or
   resuming role work. After reporting success, stop and wait for a new request.

If approval is declined, clear only the approval question, keep the active
cycle, and report that cancellation was not completed; further role work
requires a user instruction to continue. If a matching CLI is unavailable, the
preview fails, or the reset refuses or fails, stop and report that cancellation
did not complete, including any backups the CLI reports, and do not work around
a refusal by switching commands or by deleting or rewriting the files yourself.
A retry requires a valid preview and approval covering it.

The reset leaves no `CANCELLED` state or cycle record behind, so the next
request starts a first greenfield cycle from the fresh state. S.T.A.N.D.A.R.D.S.
does not revert the project working tree; reverting project changes is the
user's responsibility.

## Cycle IDs

Every cycle has a unique ID. Get it only from
`node .standards/bin/cycle.mjs new --request "<request>"`. The tool:

1. builds an ID from the request, the UTC time, and eight random hex digits, for
   example `add-user-search-20260927T190146Z-7bef0f04`;
2. checks that no cycle-owned artifact path or STANDARDS provenance block uses
   it; and
3. prints it without changing any file.

It refuses while a cycle is active (`Active Work.Id` is set and the state is not
terminal), when `STATE.md` has a merge conflict, and when `STATE.md` is invalid.
Only after the tool succeeds may the printed ID be written to `Active Work.Id`
and cycle initialization continue. If initialization fails afterwards, run the
tool again for the next attempt; an unused ID needs no cleanup.

Never write a cycle ID yourself or reuse one. `check` reports an
`Active Work.Id` that does not have the generated form, and a cycle that is
active under the ID of a cycle that the last commit ended in `SIGNED_OFF` or
`CANCELLED`: a new cycle always gets a new ID, and a finished cycle is never
reopened.
