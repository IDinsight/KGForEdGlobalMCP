# S.T.A.N.D.A.R.D.S. Protocol

<!-- standards:framework-owned -->

This file is the canonical contract for shared workflow vocabulary, state,
transitions, recovery, and installation behavior in S.T.A.N.D.A.R.D.S.

`README.md` explains the framework at a high level. Individual skills define
role-specific behavior. This protocol defines the rules those skills must share.

## Roles

```text
Role
- SCOPER
- TESTER
- ARCHITECT
- NAVIGATOR
- DEVELOPER
- AUDITOR
- REVIEWER
- DOCUMENTER
- SYNCHRONIZER
```

A role owns decisions or artifacts; it is not necessarily a workflow state.
Workflow role skills are invoked explicitly by the user. `WorkflowState`
determines whether an invoked role may perform role-owned workflow work; it does
not dispatch a skill automatically. Where supported, client installation must
prevent implicit model invocation of workflow role skills.

`NAVIGATOR` is explicitly invoked, strictly non-mutating, and outside the
workflow state machine. Its **Navigator Boundary** below applies instead of
workflow entry, persistence, completion, and handoff requirements.

State ownership governs role-owned work, not protocol coordination. An explicit
user instruction may authorize a control-plane transition even when another role
or the user owns the current state. The receiving agent may make only the
coordination changes required by the applicable cycle-selection, `PROMOTE`,
`USER_REWORK`, `NEW_CYCLE`, `SIGNOFF`, or `CANCEL` rule. It must not perform the
target role's work unless that skill was also explicitly invoked and owns the
resulting state. An active workflow role may also `PROMOTE` without separate
user authorization when an expedited cycle can no longer safely remain
expedited.

## Navigator Boundary

Navigator helps the user understand existing work, investigate questions, and
check comprehension. It may run in any workflow state, including user-owned and
terminal states, with any cycle mode or no active cycle. It owns no workflow
state or persisted artifact and has no workflow completion gate.

- Navigator never edits project files, installed runtime files, role artifacts,
  or client settings; stages or commits changes; suggests commits; or dispatches
  another role. It creates no persisted quiz scores, preferences, or summaries.
  Conversation context stays in the conversation.
- The control-plane permissions elsewhere in this protocol do not apply while
  Navigator runs. It never initializes cycles, allocates IDs, records blockers,
  selects or promotes cycle modes, signs off, cancels, or creates failure,
  recovery, or other state-changing handoffs. It may explain these actions and
  their owners, but performing them requires leaving Navigator.
- Read relevant installed protocol, state, and owner artifacts when available.
  Missing or invalid workflow metadata limits claims about workflow status; it
  does not prevent ordinary explanation supported by project evidence. Do not
  initialize, repair, or require an installed runtime or active cycle merely to
  answer a project question.
- Inspect commands and their relevant scripts, hooks, configuration, and side
  effects before execution. Use only diagnostics whose non-mutating behavior is
  established. Tests, builds, formatters, imports, and nominal dry runs may write
  files or affect external systems; their names alone do not make them safe.
  Prefer source inspection or existing evidence when safe execution cannot be
  established. Do not run a mutating check and undo its effects afterward.
- Explanations distinguish observed and intended behavior, hypotheses, and
  unknowns. Suspected defects may be explained with evidence and likely owners,
  but Navigator neither repairs them nor issues formal Reviewer verdicts,
  certifies Tester evidence, or satisfies acceptance conditions.
- For material conflicts, explain the conflicting evidence and the owner or
  user resolution needed under **Instruction Layering and Conflicts**, without
  applying its workflow routing. Continue explanations independent of the
  unresolved conflict; do not silently settle it.

Navigator has three local interaction modes: `EXPLAIN` (default), `INVESTIGATE`,
and `GRILL_ME`. They share the same boundaries and do not change `WorkflowState`
or `CycleMode`. Sufficient understanding in a quiz is bounded to the agreed
subject and depth; it is neither workflow approval nor complete mastery.

## Project Modes

```text
ProjectMode
- GREENFIELD
- BROWNFIELD
```

- `GREENFIELD`: no meaningful pre-existing project implementation must be
  treated as established baseline.
- `BROWNFIELD`: meaningful implementation already exists and workflow work must
  understand, preserve, extend, repair, or otherwise depend on it.

Choose the initial mode from project state at installation. `GREENFIELD` is
temporary: during the initial greenfield cycle, Developer must permanently
change `.standards/MODE.md` to `BROWNFIELD` as soon as Developer observes and
verifies that the active cycle has successfully created or materially modified a
project implementation artifact. The trigger is implementation existence, not
authorship: it applies equally to code written by Developer and code applied by
the user during Developer collaboration. Workflow metadata and role-owned
planning, context, test, review, or documentation artifacts do not count as
project implementation. The mode never reverts, including during recovery.

For a `STANDARD` cycle:

- `GREENFIELD` starts in `SCOPING`.
- `BROWNFIELD` starts in `AUDITING`.

Before the first greenfield audit, missing Auditor-produced project context is
intentional. Treat it as a `PROJECT_CONTEXT` failure only when the active role
actually requires context that cannot be established from completed upstream
artifacts and known project constraints.

Cancellation while still `GREENFIELD` follows **Greenfield Bootstrap
Cancellation**. Cancellation after the permanent transition to `BROWNFIELD`
retains the runtime and enters terminal `CANCELLED`.

## Cycle Modes

```text
CycleMode
- UNSET
- STANDARD
- EXPEDITED
```

`ProjectMode` describes the persistent implementation baseline. `CycleMode`
records the assurance topology of the active cycle only. `PendingCycleMode`
records an explicit user preference for the next cycle before that cycle exists.
`PendingCycleRequest` and `PendingCycleBlockedOn` durably hold a next-cycle
request only when a pre-cycle decision prevents that request from becoming an
active cycle. All are persisted in `.standards/STATE.md`.

- `CycleMode: UNSET`: no cycle is active yet. It is a coordination value, not an
  execution topology.
- `CycleMode: STANDARD`: the active cycle uses the full topology for the current
  `ProjectMode`.
- `CycleMode: EXPEDITED`: the active cycle uses the bounded brownfield path that
  intentionally omits Scoping, Architecture, Auditing, Testing, Documentation,
  Final Review, and Synchronization unless promoted.
- `PendingCycleMode: UNSET`: no explicit next-cycle preference is persisted.
- `PendingCycleMode: STANDARD | EXPEDITED`: explicit user preference for the
  next cycle. It is not an active topology and must be validated when consumed.
- `PendingCycleRequest: UNSET | <request>`: normally `UNSET`; stores the actual
  next-cycle request only while a pre-cycle decision blocks cycle creation.
- `PendingCycleBlockedOn: NONE | <question>`: unresolved pre-cycle user decision
  for `PendingCycleRequest`, otherwise `NONE`. `PendingCycleRequest` and
  `PendingCycleBlockedOn` are paired: the request is `UNSET` exactly when the
  blocker is `NONE`.

Cycle-mode rules:

1. Installation initializes `CycleMode: UNSET`, `PendingCycleMode: UNSET`,
   `PendingCycleRequest: UNSET`, and `PendingCycleBlockedOn: NONE`. Terminal
   `SIGNED_OFF` and retained `CANCELLED` states reset `CycleMode` to `UNSET`
   after the completed or cancelled cycle's mode-specific transition rules have
   been applied; all pending-cycle fields must be clear at that point.
2. No role-owned workflow work may proceed with `CycleMode: UNSET`. Before the
   first substantive work of a cycle, consume and validate `PendingCycleMode`
   when it is not `UNSET`; otherwise select the mode from the new request and
   entry path. Persist the result in `CycleMode`, clear all pending-cycle fields
   to their neutral values, and initialize the required active work before
   role-owned work.
3. `GREENFIELD` supports only `STANDARD`. A pending `EXPEDITED` preference is
   invalid in `GREENFIELD` and must not be persisted.
4. `BROWNFIELD` supports both execution modes. If no pending preference exists
   for a new request, the standard topology is the default except that an
   explicit Developer invocation for a sufficiently bounded brownfield
   implementation change may select `EXPEDITED` as defined below.
5. While no cycle is active and before a request has initialized the next cycle,
   the user may set, replace, or clear `PendingCycleMode`. The latest explicit
   preference survives across sessions but does not modify `Active Work` or
   activate a cycle. If a blocked `PendingCycleRequest` already exists, changing
   or clearing the mode triggers revalidation of that persisted request.
6. A pending `EXPEDITED` preference does not bypass the expedited contract. When
   the request arrives, validate eligibility before consuming it. If the request
   is not eligible, do not silently reinterpret the preference as `STANDARD`;
   persist the request in `PendingCycleRequest`, persist the required user
   decision in `PendingCycleBlockedOn`, and require the user to choose
   `STANDARD`, revise the request, or abandon the pending request.
7. `EXPEDITED` remains valid only while the request is a sufficiently bounded
   implementation contract and no omitted role or guarantee is required.
8. Skipping a role does not transfer its ownership, artifacts, or completion
   guarantees to Developer or Reviewer.
9. Promotion to `STANDARD` follows **Expedited Promotion** and is one-way for
   the active cycle.

## Workflow States

```text
WorkflowState
- SCOPING
- ARCHITECTING
- AUDITING
- DEVELOPING
- TESTING
- REVIEWING_IMPLEMENTATION
- DOCUMENTING
- REVIEWING_FINAL
- SYNCHRONIZING
- AWAITING_USER_SIGNOFF
- SIGNED_OFF
- CANCELLED
```

`.standards/STATE.md` records exactly one `WorkflowState`, one `CycleMode`, and
one set of pending-cycle coordination fields: `PendingCycleMode`,
`PendingCycleRequest`, and `PendingCycleBlockedOn`. `SIGNED_OFF` and `CANCELLED`
are terminal and mean there is no active cycle. In a terminal state, `CycleMode`
is `UNSET`; persisted `Active Work` data describe the most recent cycle for
traceability until `NEW_CYCLE` replaces them, while the pending-cycle fields may
independently describe an explicit next-cycle preference or a blocked next-cycle
request.

The owning role for each state is:

| Workflow state             | Owning role     |
|----------------------------|-----------------|
| `SCOPING`                  | `SCOPER`        |
| `ARCHITECTING`             | `ARCHITECT`     |
| `AUDITING`                 | `AUDITOR`       |
| `DEVELOPING`               | `DEVELOPER`     |
| `TESTING`                  | `TESTER`        |
| `REVIEWING_IMPLEMENTATION` | `REVIEWER`      |
| `DOCUMENTING`              | `DOCUMENTER`    |
| `REVIEWING_FINAL`          | `REVIEWER`      |
| `SYNCHRONIZING`            | `SYNCHRONIZER`  |
| `AWAITING_USER_SIGNOFF`    | User            |
| `SIGNED_OFF`               | User (terminal) |
| `CANCELLED`                | User (terminal) |

## Persisted Workflow State

`.standards/STATE.md` is the authoritative, branch-persisted, version-controlled
record needed to resume workflow work across sessions or agents. Before workflow
work, read `.standards/PROTOCOL.md`, `.standards/MODE.md`, and
`.standards/STATE.md`. Resume
from persisted state, active work, handoff, recovery context, and outstanding
corrective obligations; do not infer a different state from chat history or
artifact presence.

`STATE.md` uses this shape:

```markdown
# S.T.A.N.D.A.R.D.S. Workflow State

`WorkflowState`: `ARCHITECTING`
`CycleMode`: `STANDARD`
`PendingCycleMode`: `UNSET`
`PendingCycleRequest`: `UNSET`
`PendingCycleBlockedOn`: `NONE`

## Active Work

`Id`: `add-user-search-20260923T150000Z-a7f3` `Request`: `Add user search by name and email.` `Scope`:
`docs/scope/add-user-search.md` `Architecture`: `docs/specs/add-user-search.md`
`Development`: `docs/development/add-user-search-20260923T150000Z-a7f3.md` `PromotionReason`: `NONE`
`AuditTarget`: `NONE` `BlockedOn`: `NONE`

`BaselineReconciliation`: `NONE`

## Handoff

`Kind`: `FAILURE` `From`: `TESTING` `FailureType`: `ARCHITECTURE` `Reason`:
`Retry behavior is not defined by the current technical design.`

## Recovery

`Active`: `true`

### Frame 1

`From`: `TESTING` `Owner`: `ARCHITECTING` `FailureType`: `ARCHITECTURE`
`Reason`: `Retry behavior is not defined by the current technical design.`
`ResumeAt`: `TESTING` `RerunThrough`: `NONE`

## Outstanding Obligations

`Active`: `false`
```

### Active Work

- `Id`: stable, user-readable identifier allocated through **Cycle ID
  Registry**. While the current S.T.A.N.D.A.R.D.S. runtime remains installed,
  every allocated cycle ID is reserved permanently and must never be reused by
  another cycle. Generate every new ID with a request-derived slug plus a fresh
  collision-resistant token (for example a ULID, UUID fragment, or
  timestamp-plus-random suffix); never rely on a bare request slug. Never
  overwrite or repurpose an artifact belonging to another cycle.
- `Request`: persisted user request at enough fidelity for the entry role to
  understand the work.
- `Scope`, `Architecture`, and `Development`: repository-relative paths to the
  owning artifacts, or `NONE` until created. Scoper, Architect, and Developer
  must persist their artifact path before their normal completion gate passes.
  In expedited work `Scope` and `Architecture` normally remain `NONE` unless the
  cycle is promoted; `Development` is still Developer-owned and is created before
  implementation begins.
- `PromotionReason`: durable reason an expedited cycle was promoted, otherwise
  `NONE`. Preserve it for the remainder of the cycle; it is workflow context,
  not a user requirement, scope decision, architecture decision, or baseline
  fact.
- `BaselineReconciliation`: durable provenance for unresolved project changes
  retained from cancelled cycles, otherwise `NONE`. It must be resolved before
  the current cycle may rely on the affected repository state as established
  baseline. Use the **Baseline Reconciliation Format** below, with one entry
  per unique `SourceCycle` and its `Request` summary. Carry the list across
  handoffs, failures, rework, recovery, and cancellation until Auditor resolves
  every source and clears it. `Handoff.Reason` is not a substitute.
- `AuditTarget`: transient repository-relative path or area label for an
  in-progress targeted audit when that focus cannot otherwise be recovered from
  persisted active work, owned artifacts, or recovery context; otherwise
  `NONE`. Auditor must persist an ad-hoc user-directed target before relying on
  it and clear it when that targeted audit completes, is abandoned, or no longer
  needs separate persistence.
- `BlockedOn`: unresolved user question preventing completion, otherwise
  `NONE`.

Installation initializes `Id` and `Request` as `UNSET`. Before the first
workflow role performs substantive work, select and validate `CycleMode`
according to **Cycle Modes**, consuming `PendingCycleMode` when present; then
allocate the cycle ID through **Cycle ID Registry**. Only after the registry
append succeeds may the reserved ID, request, and selected mode be persisted as
the initialized cycle. Every later `NEW_CYCLE` follows the same allocation rule
as part of the transition.

### Baseline Reconciliation Format

Within `Active Work`, store `BaselineReconciliation` on its own line. When no
obligation exists, use exactly:

```markdown
`BaselineReconciliation`: `NONE`
```

Otherwise use a nonempty Markdown list with both required fields in each entry:

```markdown
`BaselineReconciliation`:

- `SourceCycle`: `invoice-cache-hotfix-20260923-a7f3`
  `Request`: `Change invoice-cache invalidation behavior.`
- `SourceCycle`: `admin-notes-20260924-b8e4`
  `Request`: `Add internal notes to admin records.`
```

`SourceCycle` is the cancelled source's exact cycle `Id`, not the new cycle's
ID. It is the unique key; `Request` is that source's brief persisted request
summary. Preserve entry order and existing entries when carrying the list into
another cycle. Append a newly obligated source only if its ID is absent; never
replace older sources with the latest cancellation or duplicate an existing ID.
Confirmation that the latest cycle left no changes does not clear older entries.
Keep the complete list while any source remains unresolved; only Auditor clears
it to `NONE` after reconciling every listed source. An empty list is represented
as `NONE`, not an empty string or `[]`.

A value that does not match this format is invalid workflow state. Report the
inconsistency and block work that depends on it until corrected; do not infer
entries or discard obligations.

### Cycle ID Registry

`.standards/CYCLE_IDS.md` is the protocol-owned, append-only registry of every
cycle ID allocated while the current S.T.A.N.D.A.R.D.S. runtime remains
installed. It exists only to reserve cycle identifiers; it is not workflow
history and must not duplicate requests, states, handoffs, or artifact metadata.
Store one allocated ID per Markdown list entry:

```markdown
# S.T.A.N.D.A.R.D.S. Cycle ID Registry

- <cycle-id>
```

Allocate a new cycle ID in this order:

1. Generate a request-derived, collision-resistant candidate.
2. Verify that the candidate does not already appear in `CYCLE_IDS.md`.
3. As defense in depth, also verify that it does not collide with an existing
   cycle-owned artifact path or STANDARDS provenance marker, including
   `docs/development/<candidate>.md`, `docs/verification/<candidate>.md`,
   `docs/reviews/<candidate>/`, `docs/documentation/<candidate>.md`, and
   `docs/synchronization/<candidate>.md`.
4. Append the candidate to `CYCLE_IDS.md` and persist that registry change.
5. Only after the registry append succeeds may the candidate be written to
   `Active Work.Id` and cycle initialization continue.

Registry entries are immutable while the runtime remains installed: never edit,
remove, reorder for deduplication, or reuse an existing entry. If cycle
initialization fails after the append, leave the ID reserved; a burned ID is
safe, while reuse is not. The registry is the authoritative no-reuse record;
artifact-path and provenance checks are additional collision protection, not a
replacement for the registry.

Initialize `CYCLE_IDS.md` empty on first installation. Preserve it across normal
reinstall, framework upgrade, and explicit workflow reinitialization.

If `CYCLE_IDS.md` is unexpectedly missing from an installed runtime, treat the
runtime as incomplete: stop cycle allocation and workflow work that would
require a new cycle ID, report the missing registry, and require restoration of
the registry or intentional runtime removal followed by a fresh installation.
Never recreate an empty registry or best-effort reconstruct one in place,
because doing so would silently break the installed-runtime no-reuse guarantee.

Intentional removal of the S.T.A.N.D.A.R.D.S. runtime may remove the registry
with `.standards/`; that removal ends the registry-backed lifetime guarantee. A
later fresh installation starts a new registry, while existing artifact and
provenance collision checks still apply.

### Workflow Artifact Provenance

Cycle ownership must be recoverable from the artifact itself whenever STANDARDS
creates a Scope, Architecture, Development, Verification, Review, Documentation,
or Synchronization artifact.
Every such newly created artifact must begin with this provenance block, using
exactly one concrete artifact type and the exact current cycle ID. Review reports
also require the `ReviewKind` extension defined below:

```markdown
<!-- STANDARDS
Artifact: SCOPE | ARCHITECTURE | DEVELOPMENT | VERIFICATION | REVIEW | DOCUMENTATION | SYNCHRONIZATION
Cycle: <Active Work.Id>
-->
```

A valid provenance block makes the file a STANDARDS cycle-owned artifact even if
it is later renamed or moved. A different cycle may read that artifact as prior
evidence when a role contract permits, but it must never overwrite, repurpose,
or adopt the file as its own cycle artifact.

An existing unmarked project document remains project-owned merely because
Scoper or Architect selects it as the active scope or architecture location.
Those roles may update an appropriate unmarked canonical project document, and
must not add STANDARDS provenance solely because the document is referenced by
`Active Work.Scope` or `Active Work.Architecture`. If either role instead creates
a new workflow artifact, it must add the current-cycle provenance block. If the
natural target path already contains a STANDARDS artifact owned by another
cycle, choose a distinct path rather than overwriting it.

Developer's development plan is always a STANDARDS cycle-owned artifact. Its
path must be unique to the active cycle and include `Active Work.Id`; use
`docs/development/<Active Work.Id>.md` unless the repository requires another
development-plan directory, in which case preserve the same cycle-specific
filename. Its provenance block and the plan's visible `Cycle` field must both
match `Active Work.Id`.

Tester's verification report is always a STANDARDS cycle-owned artifact at
`docs/verification/<Active Work.Id>.md`. Its `VERIFICATION` provenance block
and visible `Cycle` field must match `Active Work.Id`. This fixed path is
recoverable from the cycle ID; do not add a verification-path field to
`STATE.md`. Preserve reports from other cycles. If the required path contains
an unrelated or incorrectly marked file, report the collision and block
dependent work until it is resolved; do not overwrite or adopt it. Test suites
and fixtures remain reusable project assets and do not require report provenance.

Reviewer owns two fixed cycle-specific report paths:

- `docs/reviews/<Active Work.Id>/implementation.md` for `IMPLEMENTATION`;
- `docs/reviews/<Active Work.Id>/final-deliverable.md` for `FINAL_DELIVERABLE`.

Every review report begins with this specialized provenance block:

```markdown
<!-- STANDARDS
Artifact: REVIEW
Cycle: <Active Work.Id>
ReviewKind: IMPLEMENTATION | FINAL_DELIVERABLE
-->
```

Use exactly one concrete `ReviewKind` matching the path and current review
state. The visible `Cycle` and `ReviewKind` fields must match the block. These
paths are derived from cycle ID and kind; do not add a review-path state field.
Preserve reports from other cycles and the other review kind. Before creating
or editing a report, inspect its path and provenance. An unrelated, unmarked,
incorrectly marked, or different-cycle/kind file at the required path is a
collision: report it and block dependent work until resolved without overwriting,
relabeling, adopting it, or silently choosing an alternate path. The same applies
when a non-directory or unsafe path prevents the required report location.

The following records have fixed cycle-specific paths:

| Owner        | Path                                       | Artifact type     |
|--------------|--------------------------------------------|-------------------|
| Documenter   | `docs/documentation/<Active Work.Id>.md`   | `DOCUMENTATION`   |
| Synchronizer | `docs/synchronization/<Active Work.Id>.md` | `SYNCHRONIZATION` |

For each record, use the listed artifact type; its provenance block's `Cycle`
and visible `Cycle` field must match `Active Work.Id`. Derive the path from
the cycle ID; do not add documentation-path or synchronization-path state
fields. Inspect the path and provenance before creating or editing the record.
An unrelated, unmarked, incorrectly marked, or different-cycle file is a
collision; a non-directory or unsafe path is also a blocker. Preserve existing
content, report the collision, and block dependent work until resolved without
relabeling, adopting, overwriting, or silently choosing another path. Preserve
other cycles' records, including moved artifacts whose provenance still names
their original cycle.

Ordinary project documentation, comments, and docstrings remain reusable
project assets and do not acquire cycle provenance merely because Documenter
updates them.

Before editing the verification report or an artifact referenced by
`Active Work.Scope`, `Active Work.Architecture`, or `Active Work.Development`,
the owning role must
inspect any STANDARDS provenance block. If the block records a different cycle,
do not overwrite or silently repair the artifact; the persisted reference is
inconsistent with the active cycle and must be corrected without mutating the
other cycle's artifact.

### Handoff

`Handoff.Kind` is one of `INITIAL`, `FORWARD`, `FAILURE`, `RESUME`, `PROMOTE`,
`USER_REWORK`, `NEW_CYCLE`, `SIGNOFF`, or `CANCEL`. Use `NONE` for inapplicable
fields. `Reason` describes only the latest transition and must remain concise;
it is not durable storage for outstanding recovery or baseline obligations.

Use `RESUME` whenever a recovery frame returns to `ResumeAt`, and for any other
recovery-directed transition that is not the normal forward handoff.

### Recovery

`Recovery` is a stack ordered oldest to newest; the last frame is active. A
frame preserves one corrective defect together with the routing needed to return
to interrupted work. A role owns the active frame only when the current
`WorkflowState` equals its `Owner`.

`RerunThrough` is `NONE` until the frame owner resolves the defect. If previously
completed downstream work must be re-established before `ResumeAt`, the owner
sets it to the last state in that rerun sequence. Merely running during recovery
does not make a role responsible for the frame.

### Outstanding Obligations

`Outstanding Obligations` preserves unresolved corrective work when the recovery
routing that carried it is no longer valid. It is ordered oldest to newest. Each
obligation records `Owner`, `FailureType`, and `Reason`; it deliberately has no
`From`, `ResumeAt`, or `RerunThrough`.

Normally the recovery frame itself is the durable corrective obligation and no
duplicate outstanding obligation is created. `RerunThrough: NONE` means the
frame's owner has not yet completed its correction; a non-`NONE` `RerunThrough`
means the owner already passed its corrective gate and the frame remains only to
finish downstream rerun/resume routing. During **Expedited Promotion**, convert
each recovery frame whose `RerunThrough` is `NONE` into one outstanding obligation
before clearing the expedited recovery stack. Do not convert frames whose
`RerunThrough` is non-`NONE`. Preserve converted obligations in recovery-stack
order, keep each distinct defect separate, and do not collapse defects merely
because they share an owner or failure type.

When one or more obligations exist, set `Active: true` and record each as a
numbered `Obligation N` containing `Owner`, `FailureType`, and `Reason`. When the
last obligation is removed, set `Active: false` and remove the numbered entries.

An outstanding obligation remains until its owning state is reached and the
owner corrects and verifies the specific defect recorded by the obligation.
Remove a corrected obligation as soon as that corrective outcome is verified;
removing it records only that the obligation itself is satisfied and does not
imply that the owning role is otherwise complete. The owner must still pass its
normal completion gate, including the requirement that no unresolved obligation
owned by its current state remains, before any normal forward handoff. User
sign-off is unavailable while any outstanding obligation remains.

### State-update rules

1. Installation initializes from the selected mode template: `SCOPING` for
   `GREENFIELD`, `AUDITING` for `BROWNFIELD`, `CycleMode: UNSET`,
   `PendingCycleMode: UNSET`, `PendingCycleRequest: UNSET`,
   `PendingCycleBlockedOn: NONE`, `Handoff.Kind: INITIAL`, unset active work,
   and inactive recovery.
2. Before substantive work on an initialized cycle, select and persist the cycle
   mode and initialize active work according to **Cycle Modes**, **Active Work**,
   and **User Decisions and Intervention**.
3. Every legal state-changing transition updates all applicable `CycleMode`,
   pending-cycle coordination fields, `Active Work`, `Handoff`, `Recovery`, and
   `Outstanding Obligations` fields as part of the transition.
4. Blocking questions during an active cycle do not change workflow state. Set
   `Active Work.BlockedOn` before asking and clear it after incorporating the
   answer. Pre-cycle control-plane questions must not modify
   `Active Work.BlockedOn`; persist the blocked request and question in
   `PendingCycleRequest` and `PendingCycleBlockedOn` instead.
5. Failure/recovery, promotion, and user-control transitions follow their
   canonical sections below rather than redefining their mechanics here.
6. During the initial greenfield cycle, Developer performs the permanent mode
   change defined in **Project Modes**.

`STATE.md` coordinates the workflow; it does not replace role-owned artifacts.
Role-owned artifacts remain authoritative for their own content.

### Project context lifecycle

`.standards/CONTEXT.md` is the canonical Auditor-owned project-context artifact.
Installation does not fabricate it. Auditor creates or refreshes it when
`AUDITING` runs.

For a `STANDARD` cycle, refreshed context is the project baseline for downstream
roles, subject to ownership and freshness rules. In an `EXPEDITED` cycle,
existing context is prior evidence only; it is not presumed refreshed.

Any **Active-Cycle Non-Baseline Work** entry is scoped to the `Active Work.Id`
that produced it and applies only while that same cycle is nonterminal. It is
stale in `SIGNED_OFF`, `CANCELLED`, and later cycles. A later audit must
reconcile each prior-cycle exclusion against current repository and
version-control evidence, removing or reclassifying it rather than copying it
forward. If baseline status cannot be established safely, Auditor blocks for
user clarification.

Greenfield status does not require context to be absent. Before the first
scheduled greenfield audit, Scoping and Architecture may run or rerun without
`CONTEXT.md` when the facts required for their owned work are otherwise
established; absence of context by itself is not a defect. If either role needs
project facts that cannot safely be established without Auditor-owned context,
it routes a `PROJECT_CONTEXT` failure to Auditor. Once `CONTEXT.md` exists,
later Scoping or Architecture work must use it when relevant and must not ignore
it merely because `ProjectMode` remains `GREENFIELD`. The permanent change to
`BROWNFIELD` follows **Project Modes**.

`.standards/MODE.md` and `.standards/STATE.md` are protocol-owned coordination
artifacts. A role or user may change them only as required by a legal protocol
transition or a protocol-required coordination update defined here, including
initializing `Active Work`, recording artifact paths, selecting or promoting
`CycleMode`, and setting or clearing `PromotionReason`,
`BaselineReconciliation`, `AuditTarget`, or `BlockedOn`.
`.standards/PROTOCOL.md` is framework-owned and may be changed only by framework
installation or upgrade.

## Instruction Layering and Conflicts

Role-specific precedence may order **compatible** guidance, such as applying a
repository formatter before generic style preferences. Precedence must never be
used to silently resolve a material conflict among the protocol or installed
integration contract, explicit user constraints, completed role-owned workflow
artifacts, project-specific instructions, or repository-enforced/toolchain
constraints.

When authorities materially conflict:

1. If the conflict is a defect or changed requirement owned by a workflow role,
   route it through the protocol's normal failure, recovery, or `USER_REWORK`
   mechanics to that owner.
2. If no workflow owner can resolve the contradiction without overriding another
   authority, or project instructions conflict with the protocol/integration
   contract, stop workflow work and require user resolution.
3. Do not weaken an authority, invent an exception, or choose a winner merely
   because one source appears earlier in a role-specific precedence list.

Role skills should reference these rules rather than redefine conflict-resolution
semantics locally.

## Acceptance Traceability

These obligations apply only to `STANDARD` cycles and do not create a shared
traceability artifact or add acceptance data to `STATE.md`. `EXPEDITED` cycles
do not fabricate Scoper-owned acceptance conditions or substitute identifiers.
If an expedited cycle is promoted, Scoper establishes them when the standard
topology reaches `SCOPING`.

1. Scoper represents every verifiable in-scope completion obligation as one or
   more acceptance conditions with stable, unique `AC-NNN` identifiers for the
   active cycle. Do not combine separable obligations under one identifier when
   their satisfaction or verification evidence is established in different
   workflow phases. The identifier is a reference, not an ordering guarantee.
2. During REPLAN, preserve an identifier when meaning is unchanged. New or
   materially replaced conditions receive previously unused identifiers.
   Removed or replaced identifiers remain in the scope's retired-identifier
   record. Never renumber surviving identifiers or reuse retired ones within
   the cycle.
3. Scoper owns acceptance wording and meaning. Downstream roles reference IDs
   but do not redefine intent; material defects route to Scoper.
4. Architect accounts for every current ID with technical design coverage or an
   explicit no-architectural-impact disposition when satisfaction depends
   entirely on established nontechnical behavior or work owned by another
   workflow phase. Group IDs only when the same disposition applies; do not
   invent architecture or claim ownership of satisfaction that belongs to
   another workflow phase.
5. All downstream coverage, work, and evidence references the same current IDs;
   downstream roles do not invent substitute requirement IDs.
6. Tester accounts for every current ID with verification evidence, a blocker,
   or—when satisfaction explicitly depends on a later role—a pending dependency.
   Pending is not verification evidence and must be resolved downstream under
   the same ID.
7. `AWAITING_USER_SIGNOFF` is forbidden while any current ID lacks sufficient
   evidence or has an unresolved blocker. Route defects to their owning roles
   through normal failure and recovery rules; never treat an unevidenced
   condition as satisfied by assumption.
8. Acceptance changes during recovery or rework invalidate any completed
   downstream artifact whose completion contract requires accounting for every
   current ID. Include those states when computing downstream invalidation even
   if underlying behavior or technical decisions remain otherwise valid.

## Expedited Cycle Contract

An `EXPEDITED` cycle provides a deliberately narrower completion contract:

1. It is valid only in `BROWNFIELD`.
2. `Active Work.Request` is the change contract. `Scope` and `Architecture`
   remain `NONE` unless promotion later causes their owners to create them.
3. Existing project context may be consulted as prior evidence but is not
   refreshed by default. Prior-cycle non-baseline entries are stale for the
   current cycle. If safe completion depends on baseline status that requires
   Auditor-owned context, promote instead of assigning that work to Developer.
4. Active-cycle implementation remains tentative. Promotion does not make it
   established baseline. Auditor must distinguish pre-cycle baseline from
   active-cycle changes using authoritative evidence and block rather than guess
   when materially ambiguous.
5. Developer owns implementation and normal implementation-level self-checks;
   these are not Tester-owned formal verification.
6. Reviewer still owns `REVIEWING_IMPLEMENTATION` and may route implementation
   defects through normal recovery.
7. Scoper, Architect, Auditor, Tester, Documenter, `REVIEWING_FINAL`, and
   Synchronizer are absent from the expedited forward topology. Their missing
   artifacts or gates are not failures.
8. The cycle may reach `AWAITING_USER_SIGNOFF` after Developer and implementation
   Reviewer pass their gates, recovery is empty, and no blocking user question
   remains. Scope-level acceptance traceability does not apply.
9. If safe completion requires an omitted role or guarantee, use **Expedited
   Promotion** instead of weakening ownership or fabricating skipped work.

## Review Kinds

```text
ReviewKind
- IMPLEMENTATION
- FINAL_DELIVERABLE
```

`IMPLEMENTATION` corresponds to `REVIEWING_IMPLEMENTATION`.
`FINAL_DELIVERABLE` corresponds to `REVIEWING_FINAL`. A review handoff must
identify the requested kind.

### Review Gates

Critical, independent assessment is required in both review kinds. Scope and
architecture are authoritative statements of intended behavior, not proof that
those statements are consistent or complete. Reviewer examines relevant claims
from all roles and repository evidence without inheriting completion conclusions
or silently replacing owned decisions.

`IMPLEMENTATION` assesses implementation against the active contract, upstream
consistency, Developer claims, and, in `STANDARD`, Tester coverage and evidence.
Account for every current `AC-NNN` and relevant technical criterion. Explicit
later-phase dependencies may remain only when satisfaction belongs to that later
role; record the owner, required evidence, and the same AC ID. Pending is not
evidence and cannot defer a present-phase defect or verification gap.

`FINAL_DELIVERABLE` is available only in `STANDARD`. It assesses the assembled
work after documentation: current acceptance evidence, documentation accuracy,
unresolved findings, and consistency across artifacts. Every current acceptance
condition and relevant technical criterion must have sufficient current evidence;
unresolved dependencies or material evidence gaps cannot pass this gate.

In `EXPEDITED`, implementation review assesses the bounded `Active Work.Request`
and Developer evidence under **Expedited Cycle Contract**. Do not demand
intentionally skipped artifacts, fabricate acceptance IDs, perform final review,
or claim skipped guarantees. Promote when an omitted guarantee becomes necessary.

A review passes only when no unresolved material finding or material assessment
gap remains, no blocking user question or obligation owned by the current review
state remains, and the applicable gate above is satisfied. No material findings
is a valid outcome; there is no finding quota. A report with no established
defects but insufficient material evidence is still incomplete. Reviewer defines
severity and evidence details in its shared procedure and report template.

Passing a review gate does not complete the cycle. Apply **Recovery Mechanics**
when active; otherwise follow **Forward Transitions**. Before entering
`AWAITING_USER_SIGNOFF`, all applicable cycle completion requirements, including
an empty recovery stack and inactive outstanding obligations, must hold.

## Synchronization Gate

Synchronizer reconciles completed assessments, the current deliverable, and
workflow records in `SYNCHRONIZING` during `STANDARD` only. Reviewer owns the
assessment of soundness; Synchronizer establishes whether that assessment and
its supporting evidence still apply to the work being offered for sign-off.
Initial work, resumption, and reconciliation after corrections share this full
completion gate. A corrective return below does not declare this gate passed.

Synchronization passes when:

- the current-cycle synchronization record has matching provenance and current
  assessed input identities, with references to the existing completion and
  evidence artifacts;
- cycle identities, artifact references, current files, and completion claims
  agree, and implementation and final review conclusions remain applicable;
- every current acceptance condition and relevant technical criterion has
  sufficient current evidence under **Acceptance Traceability**, including
  evidence resolving any earlier later-role dependencies under the same IDs;
- no unresolved material discrepancy or reconciliation gap remains, and no
  blocking user question or obligation owned by `SYNCHRONIZING` remains;
- limitations, remaining work, and a concise conclusion with resume/handoff
  context are persisted. A sufficiently assessed no-change result is valid.

The record references evidence; it is not another authoritative acceptance
ledger. File presence or a `COMPLETE` label alone proves neither completion nor
continued applicability. Synchronizer owns its record and corrections to its
reconciliation, not another role's evidence, findings, or completion markers.

Project-facing documentation and agent guidance are Documenter-owned, including
project instructions outside managed framework blocks. Their completion evidence
must identify the relevant documents and assessed content, checks performed and
results or limits, and any current AC or technical criterion they satisfy.
Documenter persists this evidence and resumable progress in its documentation
record under **Workflow Artifact Provenance**, referencing supporting evidence
where it already exists rather than copying it. The record also preserves
collaboration mode, target and editing boundary, explicitly selected user style
(or `NONE`), remaining work, discrepancies, dependencies, and the completion
conclusion. It is not an authoritative acceptance ledger and does not certify
another role's work. Reviewer and Synchronizer consume it independently; neither
manufactures its evidence or rewrites documentation. Managed framework blocks,
installed protocol, and installation metadata retain installer/protocol ownership.
Preserve user-authored instructions and apply **Instruction Layering and
Conflicts** when necessary.

Passing this gate is not cycle completion or user acceptance. Apply **Recovery
Mechanics** after owned correction and the gate: an active recovery stack does
not by itself prevent the Synchronizer gate from passing. A correction or rerun
may need to return to `ResumeAt` instead of advancing toward sign-off.

### Synchronizer Corrective Return

An interrupted role may need a Synchronizer-owned reconciliation error corrected
before it can finish its assessment. Do not require that unfinished assessment
as a prerequisite for returning its verified correction. This is a narrow
recovery outcome, not another mode or a passing synchronization conclusion.

Synchronizer may plan resumption without passing its full gate only when:

- it owns the active recovery frame, whose `RerunThrough` is `NONE`, and
  `ResumeAt` is another workflow role's state, not a user-owned state;
- its record has valid current-cycle provenance, the frame's specific correction
  has been verified against current inputs, and no unresolved Synchronizer-owned
  defect, obligation, or blocking question prevents that corrective outcome;
- the remaining full-gate gaps are exclusively unfinished assessments or work
  already assigned to the interrupted role or preserved recovery route. Record
  each dependency, its owner, and the evidence still required. An open Reviewer
  finding awaiting reassessment of this correction remains Reviewer-owned;
- any newly discovered independent defect or gap is handled through normal
  failure/blocking rules instead of being deferred by this exception.

Persist the correction evidence and remaining work, leaving the synchronization
record `IN_PROGRESS` or `BLOCKED` while its full gate is unmet. Then use
**Recovery Mechanics** to determine reruns and return; preserve older frames.
Do not close another role's findings or claim synchronization complete. A
same-state correction, a downstream rerun that does not own the active frame,
or a return to `AWAITING_USER_SIGNOFF` cannot use this exception. Once the
interrupted work is complete, full synchronization must still pass before
**Standard Cycle Completion** permits sign-off readiness.

## Documenter Corrective Return

An earlier role may need a documentation or project-guidance defect corrected
before it can finish its work. Requiring documentation of that unfinished work
before returning the correction would prevent either role from proceeding.
This is a narrow recovery outcome in `STANDARD`, not another mode or a passing
Documenter completion conclusion.

Documenter may plan resumption without passing its full gate only when:

- it owns the active recovery frame in `DOCUMENTING`, whose `RerunThrough` is
  `NONE`, and `ResumeAt` is another workflow role's state, not a user-owned state;
- its record has valid current-cycle provenance and the frame's specific
  correction has been verified in saved content against current inputs with
  sufficient actual evidence; no unverified corrective edit, unresolved
  actionable documentation defect, Documenter-owned outstanding obligation, or
  blocking user question remains;
- every remaining full-gate gap is documentation work or assessment that cannot
  yet be completed because necessary work already assigned to the interrupted
  role or preserved recovery route is unfinished. Persist each remaining item,
  its prerequisite and owner, the evidence still needed, and when documentation
  must be revisited. Preserve current AC references where they exist; do not
  fabricate future scope, design, implementation, verification, or review
  artifacts, or acceptance identifiers;
- missing evidence needed to verify the correction, independent defects or
  gaps, and currently actionable documentation outside a selected editing
  boundary are handled through normal failure/blocking rules rather than
  deferred by this exception. A selected target or collaboration mode does not
  waive those requirements.

Persist correction evidence, applicability limits, remaining work, and resume
context, leaving the documentation record `IN_PROGRESS` or `BLOCKED`. Then use
**Recovery Mechanics** to determine necessary reruns and return, preserving
older frames and outstanding obligations. Do not mark documentation `COMPLETE`,
close another role's findings, or take a normal forward handoff on the strength
of this correction. A same-state correction, a downstream rerun that does not
own the active frame, or a return to `AWAITING_USER_SIGNOFF` cannot use this
exception. GUIDED work must have an inspected saved correction; supplying a
snippet is insufficient. On re-entry, reconcile current inputs and the retained
work. The full Documenter gate still applies before normal forward handoff, and
**Standard Cycle Completion** still requires completed documentation before
sign-off readiness.

## Standard Cycle Completion

Before a `STANDARD` cycle enters `AWAITING_USER_SIGNOFF`, all applicable
standard role gates must be satisfied for the current work, including final
review and synchronization. Every current AC and relevant technical criterion
must have sufficient current evidence, with no unresolved material findings,
discrepancies, dependencies, or blocking user question. Required project context
must be valid and `Active Work.BaselineReconciliation` must be `NONE`.
Recovery must be complete (empty stack) and outstanding obligations inactive.
Apply recovery routing first; neither a report label nor correction of one
owned obligation bypasses these requirements.

`AWAITING_USER_SIGNOFF` means ready for the user's decision, not accepted or
`SIGNED_OFF`. User acceptance follows **User Decisions and Intervention**;
revalidate these requirements at sign-off against current inputs. `EXPEDITED`
uses **Expedited Cycle Contract** instead and never fabricates synchronization.

## Failure Types

```text
FailureType
- SCOPING
- ARCHITECTURE
- PROJECT_CONTEXT
- IMPLEMENTATION
- VERIFICATION
- DOCUMENTATION
- REVIEW
- SYNCHRONIZATION
```

| Failure type      | Owning role    |
|-------------------|----------------|
| `SCOPING`         | `SCOPER`       |
| `ARCHITECTURE`    | `ARCHITECT`    |
| `PROJECT_CONTEXT` | `AUDITOR`      |
| `IMPLEMENTATION`  | `DEVELOPER`    |
| `VERIFICATION`    | `TESTER`       |
| `DOCUMENTATION`   | `DOCUMENTER`   |
| `REVIEW`          | `REVIEWER`     |
| `SYNCHRONIZATION` | `SYNCHRONIZER` |

The discoverer of a failure does not automatically own the fix. Route it to the
owner of the defective artifact or decision.

## Forward Transitions

A forward transition occurs only after the current state's completion gate
passes.

### Standard Greenfield

```text
SCOPING
-> ARCHITECTING
-> AUDITING
-> DEVELOPING
-> TESTING
-> REVIEWING_IMPLEMENTATION
-> DOCUMENTING
-> REVIEWING_FINAL
-> SYNCHRONIZING
-> AWAITING_USER_SIGNOFF
```

### Standard Brownfield

```text
AUDITING
-> SCOPING
-> ARCHITECTING
-> DEVELOPING
-> TESTING
-> REVIEWING_IMPLEMENTATION
-> DOCUMENTING
-> REVIEWING_FINAL
-> SYNCHRONIZING
-> AWAITING_USER_SIGNOFF
```

For brownfield standard work, `ARCHITECTING -> DEVELOPING` requires valid
project context for the active cycle. Missing, materially incomplete, incorrect,
or unexpectedly invalidated context routes to `AUDITING`. Planned active-cycle
implementation changes do not alone make context stale.

### Expedited Brownfield

```text
DEVELOPING
-> REVIEWING_IMPLEMENTATION
-> AWAITING_USER_SIGNOFF
```

This topology is valid only for `ProjectMode: BROWNFIELD` and
`CycleMode: EXPEDITED`. Skipped standard work must not be synthesized inside
Developer or Reviewer.

## Expedited Promotion

Promotion changes a nonterminal `EXPEDITED` brownfield cycle to `STANDARD` when
the bounded contract is no longer sufficient. It is a topology change, not a
failure handoff.

Promote when safe completion requires formal Scoping, consequential
Architecture, authoritative Auditor-owned context, Tester-owned verification,
Documentation, Final Review, Synchronization, or another intentionally omitted
guarantee.

1. Promotion is valid only from a nonterminal expedited brownfield cycle.
2. An active workflow role may promote when required. At
   `AWAITING_USER_SIGNOFF`, user authorization is required. An explicit promote
   request qualifies; so does an explicit rework request whose changed contract
   necessarily requires an omitted standard role or guarantee.
3. Set `CycleMode: STANDARD`, `WorkflowState: AUDITING`, and
   `Handoff.Kind: PROMOTE`; set `From` to the interrupted state,
   `FailureType: NONE`, and record a concise reason identifying which omitted
   standard guarantee is now required. Persist the same reason in
   `Active Work.PromotionReason`.
4. Preserve cycle `Id`, `Request`, and role-owned artifacts. Do not fabricate
   `Scope` or `Architecture`. Existing expedited implementation remains
   tentative active-cycle work, not baseline.
5. Auditor establishes or refreshes context without laundering tentative work
   into pre-existing baseline. Material ambiguity requires a user question.
6. Before clearing recovery, persist the frame-to-obligation conversion defined
   in **Outstanding Obligations**, preserving each converted frame's `Owner`,
   `FailureType`, and `Reason`. Then clear the expedited recovery stack. The
   standard brownfield topology restarts at `AUDITING`.
7. Promotion is one-way for the active cycle.
8. All standard forward, failure, recovery, outstanding-obligation, traceability,
   and sign-off rules apply afterward.

## Failure Handoffs

A failure handoff routes a defect to its owning state:

```text
SCOPING failure         -> SCOPING
ARCHITECTURE failure    -> ARCHITECTING
PROJECT_CONTEXT failure -> AUDITING
IMPLEMENTATION failure  -> DEVELOPING
VERIFICATION failure    -> TESTING
DOCUMENTATION failure   -> DOCUMENTING
REVIEW failure          -> REVIEWING_IMPLEMENTATION or REVIEWING_FINAL, matching the affected review
SYNCHRONIZATION failure -> SYNCHRONIZING
```

In `STANDARD`, use this routing directly. In `EXPEDITED`, only
`IMPLEMENTATION -> DEVELOPING` and implementation `REVIEW ->
REVIEWING_IMPLEMENTATION` are valid failure routes because only those states
exist in the expedited topology. A defect or guarantee owned by a skipped role
requires **Expedited Promotion**, not a failure transition into a skipped state.

If routing changes state, apply **Recovery Mechanics**. A same-state failure
records the handoff but does not create a recovery frame.

## Recovery Mechanics

This is the canonical recovery algorithm. Skills define only how their role
corrects its owned work, evaluates its completion gate, and identifies which
previously completed downstream states its correction invalidates.

Recovery follows the active `CycleMode` topology. Expedited recovery reruns only
expedited states; a newly required skipped role or guarantee triggers
**Expedited Promotion**, which preserves unresolved corrective obligations as
`Outstanding Obligations` and clears only the now-obsolete expedited recovery
routing.

1. **Push only when corrective routing changes state.** For `FAILURE` or
   `USER_REWORK` moving to a different state, push a frame with `From` =
   interrupted state, `Owner` = corrective target, applicable `FailureType` and
   `Reason`, `ResumeAt` = interrupted state, and `RerunThrough: NONE`.
   Same-state correction creates no frame.
2. **Preserve nesting.** New failure or rework during recovery pushes another
   frame. Never overwrite older frames. The last frame is active.
3. **Only the active frame owner plans resumption.** After correcting the defect
   and passing its normal gate, that owner decides whether previously completed
   downstream states must be re-established before `ResumeAt`. The only
   exceptions are **Documenter Corrective Return** and **Synchronizer Corrective
   Return**. Their conditions allow the respective owner to plan resumption
   without declaring its full gate passed; the routing algorithm below remains
   unchanged.
4. **No rerun:** pop the frame and transition directly to `ResumeAt` with
   `Handoff.Kind: RESUME`.
5. **Rerun required:** set `RerunThrough` to the last required state and
   transition to the earliest required rerun state. Keep the frame on the
   stack.
6. **Rerun states use normal gates and legal forward handoffs** while preserving
   the stack. They do not own the frame unless a nested defect creates a new one.
7. **At the rerun boundary**, after `RerunThrough` passes its gate, pop the frame
   and transition to `ResumeAt` with `Handoff.Kind: RESUME` instead of taking
   the normal forward handoff. This explicit return is valid even when
   `ResumeAt` lies outside the project's normal forward topology.
8. Recovery ends only when the stack is empty.

Examples:

```text
Architecture defect discovered during testing:
TESTING -> ARCHITECTING                 # push frame, ResumeAt TESTING
ARCHITECTING -> DEVELOPING              # set RerunThrough DEVELOPING
DEVELOPING -> TESTING                   # boundary completes, pop, resume TESTING

Scoping defect discovered during implementation review:
REVIEWING_IMPLEMENTATION -> SCOPING     # push frame
SCOPING -> ARCHITECTING                 # set RerunThrough TESTING
ARCHITECTING -> DEVELOPING -> TESTING
TESTING -> REVIEWING_IMPLEMENTATION     # pop, explicit resume

Invalid project context discovered during architecture:
ARCHITECTING -> AUDITING                # push frame
AUDITING -> ARCHITECTING                # no rerun; pop and resume

Nested recovery:
TESTING -> AUDITING                     # outer frame, ResumeAt TESTING
AUDITING -> SCOPING                     # nested rework frame, ResumeAt AUDITING
SCOPING -> ARCHITECTING                 # set nested RerunThrough DEVELOPING
ARCHITECTING -> DEVELOPING
DEVELOPING -> AUDITING                  # pop nested frame, explicit resume
```

## Commit Message Guidance

After role work, if the role produced a meaningful atomic set of repository
changes, provide a suggested Git commit message. Do not create the commit unless
the user explicitly requests it. Coordination-only changes such as advancing
`STATE.md` do not justify a suggestion by themselves.

Use Conventional Commits:

```text
<type>(<optional-scope>): <description>
```

Choose type and scope from the actual changes, not the role or workflow state.
Common types include `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `build`,
`ci`, and `chore`. Keep the description concise, imperative, and specific. Use
breaking-change syntax or footers only for genuinely breaking changes.

Examples:

```text
docs(scope): define user search requirements
docs(architecture): define user search contracts
chore(context): capture authentication project baseline
feat(search): implement user search
test(search): cover user search behavior
docs(search): document user search
fix(search): address implementation review findings
```

`NAVIGATOR` never suggests a commit. Other roles omit the suggestion when they
produced no meaningful committable changes. When both a commit suggestion and a
next-role invocation are emitted, present the commit suggestion first.

## Handoff Rules

1. Forward handoff requires the current completion gate to pass.
2. A role does not repair work it does not own; failures route under **Failure
   Handoffs**.
3. A handoff identifies its target role or workflow state. A failure handoff
   also identifies `FailureType`; `REVIEW` targets the Reviewer state matching
   the affected `ReviewKind`.
4. No role silently changes another role's artifact or decision.
5. Corrective routing and reruns follow **Recovery Mechanics**; skills must not
   redefine that algorithm.
6. User sign-off, rework, cancellation, and new-cycle transitions follow **User
   Decisions and Intervention**.
7. Promotion follows **Expedited Promotion** and is not encoded as `FAILURE`.
8. Every state-changing handoff persists the applicable state, active-work,
   handoff, recovery, and outstanding-obligation changes before further role
   work. Persist the state
   change before presenting any next-role invocation.
9. After a legal transition to a different workflow role, provide a concise
   copy/paste invocation for that role unless the same user instruction already
   explicitly invoked it and it will continue immediately. Do not emit one when
   the workflow remains with the same role, a blocking question is unresolved,
   the result is `AWAITING_USER_SIGNOFF`, `SIGNED_OFF`, or `CANCELLED`, or
   Navigator is used.
10. The invocation is convenience only; `STATE.md` and role-owned artifacts
    remain authoritative. Use the active client's syntax and avoid duplicating
    authoritative workflow content unless needed for disambiguation:

```text
Next role: <Role>

Codex:       $<skill> Continue the active workflow from `.standards/STATE.md`. Read the persisted Active Work, relevant project context and owned artifacts, and recovery context before proceeding.
Claude Code: /<skill> Continue the active workflow from `.standards/STATE.md`. Read the persisted Active Work, relevant project context and owned artifacts, and recovery context before proceeding.
```

Emit only the active-client line. When recovery is active, replace “active
workflow” with “active recovery” and explicitly direct the role to read the
active recovery frame.

At `AWAITING_USER_SIGNOFF`, present the applicable user actions rather than a
next-role invocation.

### Independent Assessment Sessions

Tester and Reviewer reconstruct assessments from persisted artifacts and
repository evidence. Before a handoff to either role, persist the applicable
state, owned artifacts, claims, assessed content identities, actual commands and
results, limitations, unresolved findings/dependencies, and resume context.
Record detail in the owning artifact, not in `Handoff.Reason`. The receiving
role must be able to work without the authoring conversation.

Every handoff entering `TESTING`, `REVIEWING_IMPLEMENTATION`, or
`REVIEWING_FINAL`, including recovery and corrections, explicitly requests the
independent session described below. Keep the normal active-client invocation,
persisted-input directions, and active-recovery-frame directions. Name the review
kind when entering Reviewer. The immediate-continuation exception must not run
an assessment in a conversation containing the prohibited authoring history,
even when the user invoked both roles together.

A skill cannot erase chat history or certify session freshness without client
support. Known prohibited authoring history requires stopping before the formal
assessment and requesting a fresh session after persisting missing context
within existing ownership. If history or client metadata is unavailable, state
that visibility limitation and proceed from persisted evidence; do not invent an
attestation or an automatic blocker or require routine user confirmation.
Resuming the assessing role's own interrupted assessment is allowed when its
conversation is separate from the prohibited authoring work.

### Independent Tester Session

Apply **Independent Assessment Sessions**. Prefix a Tester invocation with
“Open a fresh chat separate from Developer's implementation conversation, then
run:”. Developer implementation history is prohibited for formal Tester work.

### Independent Reviewer Session

Apply **Independent Assessment Sessions**. Prefix a Reviewer invocation with
“Open a fresh chat separate from the conversations that produced the artifacts
under review, then run:”. This separation covers requirements, design, context,
implementation, tests/evidence, and documentation authoring, not just Developer.
Reviewer may resume its own assessment and correct its own findings; that review
history alone does not constitute prohibited authoring history.

Recommend that the user ideally select a different model of equal or higher
capability than the model that produced the work, where known. This is advisory:
do not switch models automatically, guess model identities or capability
rankings, or add a routine author-model confirmation gate. Unknown model metadata
is a stated limitation, not a blocker. Session separation remains required even
when a different model is unavailable.

## User Decisions and Intervention

These are user-authorized control-plane transitions, subject to **Navigator
Boundary**. An explicit, unambiguous user instruction may authorize the receiving
agent to persist the coordination
change regardless of current state ownership. That exception authorizes only
the protocol transition itself. Resulting role-owned work may proceed only when
that role was explicitly invoked and owns the resulting state; otherwise stop
after persisting the transition and provide the next-role invocation when the
handoff rules require one.

### Select a pending mode before a cycle begins

While no cycle is active, or before the initialized first cycle has received its
request, an explicit user instruction may set `PendingCycleMode` to a mode
supported by the current `ProjectMode`, replace an earlier pending preference,
or clear it to `UNSET`. Leave `CycleMode: UNSET` and leave `Active Work.Id` and
`Active Work.Request` unchanged. The latest pending selection remains
authoritative across sessions until consumed, replaced, or cleared.

When the first real request arrives, determine the legal mode before creating
the cycle. If the same instruction explicitly requests a mode that the current
`ProjectMode` does not support, do not persist that mode; persist the request and
required decision in the pending request/blocker fields and ask for a supported
mode, revision, or abandonment. If `PendingCycleMode` is already set, validate
it against the request and current `ProjectMode`. If it is invalid, leave `CycleMode`,
`Active Work`, and `PendingCycleMode` unchanged; persist the request in
`PendingCycleRequest`, set `PendingCycleBlockedOn` to the specific decision required,
and ask the user to replace or clear the preference, revise the request, or abandon the
pending request. Do not write `Active Work.BlockedOn`.

While `PendingCycleRequest` is not `UNSET`, a later mode replacement/clear or a
revised request must revalidate the persisted pending request before asking the
user to repeat it. A revised request replaces `PendingCycleRequest`. If the
pending request becomes legal from `SIGNED_OFF` or retained `CANCELLED`, do not
initialize `Active Work` through this generic path; continue through **Start a
new cycle** using `PendingCycleRequest` as the new request so terminal handoff
and baseline-reconciliation requirements are preserved. Otherwise, for the
initialized first cycle, allocate the ID through **Cycle ID Registry** first;
after that registry append succeeds, persist the reserved `Active Work.Id`, that
request, and the validated/defaulted mode in the cycle-state update; clear
`PendingCycleMode` to `UNSET`, `PendingCycleRequest` to `UNSET`, and
`PendingCycleBlockedOn` to `NONE`; then enter the legal workflow state. If the
user abandons the blocked pre-cycle request, clear `PendingCycleRequest` and
`PendingCycleBlockedOn` without modifying `Active Work` or starting a cycle.

If no pending preference exists for a new request, invoking the standard entry
role selects `STANDARD` by default. Use the standard entry state for the current
`ProjectMode`: `SCOPING` for `GREENFIELD` and `AUDITING` for `BROWNFIELD`.

### Select expedited mode for the initialized cycle

Before substantive work, while `Active Work.Id` and `Active Work.Request` are
both `UNSET` and `CycleMode` is `UNSET`, a brownfield request may start an
`EXPEDITED` cycle when either `PendingCycleMode: EXPEDITED` is valid for the
request or Developer is explicitly invoked with a new sufficiently bounded
implementation request while `PendingCycleMode: UNSET`. A pending
`STANDARD` preference prevents Developer from inferring `EXPEDITED`.

After expedited eligibility is validated, allocate the new ID through **Cycle
ID Registry** before assigning it to `Active Work`. Then set `CycleMode:
EXPEDITED`; clear `PendingCycleMode` to `UNSET`, `PendingCycleRequest` to `UNSET`,
and `PendingCycleBlockedOn` to `NONE`; set `WorkflowState: DEVELOPING`;
initialize `Active Work` with the reserved ID/request plus `Scope: NONE`,
`Architecture: NONE`, `Development: NONE`, `PromotionReason: NONE`, and
`BaselineReconciliation: NONE`; keep `Handoff.Kind: INITIAL`, set `From: NONE`
and `FailureType: NONE`, record a concise expedited-entry reason, and keep
recovery and outstanding obligations inactive. This is unavailable in
`GREENFIELD`.

### Promote an expedited cycle

An explicit user instruction may authorize **Expedited Promotion** from any
nonterminal expedited brownfield state, including `AWAITING_USER_SIGNOFF`.
After persisting promotion, stop and hand off to Auditor unless Auditor was also
explicitly invoked. Active workflow roles may promote without separate user
instruction when the expedited contract becomes insufficient.

### Rework an active cycle

From any nonterminal state, update `Active Work.Request` when the request
changed, identify the earliest owned artifact or decision invalidated, record
`Handoff.Kind: USER_REWORK` with its `FailureType`, and route to that owner. If
state changes, push the recovery frame defined by **Recovery Mechanics** with
`ResumeAt` equal to the interrupted state; preserve older frames. User-requested
changes are not agent-discovered failures.

In `EXPEDITED`, bounded implementation rework routes to `DEVELOPING`. If the new
contract requires a skipped standard role or guarantee, the rework request
itself authorizes **Expedited Promotion** instead.

### Cancel an active cycle

- If `ProjectMode: GREENFIELD`, follow **Greenfield Bootstrap Cancellation**.
- If `ProjectMode: BROWNFIELD`, transition to `CANCELLED`, set
  `CycleMode: UNSET`, leave all pending-cycle fields clear, record
  `Handoff.Kind: CANCEL`, set `From` to the
  interrupted state, `FailureType: NONE`, preserve `Active Work`, and clear
  recovery plus outstanding obligations. Residual project-change provenance is
  handled through `BaselineReconciliation` when a later cycle starts.

Cancellation never reverts project artifacts and does not by itself establish
cancelled-cycle project changes as baseline.

### Sign off

From `AWAITING_USER_SIGNOFF`, sign-off is legal only when the `Outstanding Obligations`
section is inactive. Validate the completion contract using the current
`STANDARD` or `EXPEDITED` mode, then transition to `SIGNED_OFF`, set
`CycleMode: UNSET`, leave all pending-cycle fields clear, record
`Handoff.Kind: SIGNOFF`,
`From: AWAITING_USER_SIGNOFF`, `FailureType: NONE`, and clear recovery. The
cycle is complete.

For `STANDARD`, all standard gates and acceptance-traceability obligations must
be satisfied before the reset. For `EXPEDITED`, sign-off covers only the
narrower **Expedited Cycle Contract**; skipped standard phases must not be
represented as completed.

### Start a new cycle

From `SIGNED_OFF` or retained `CANCELLED`:

1. Determine the reconciliation obligation that the new cycle would carry. From
   `SIGNED_OFF`, it is `NONE`. From retained `CANCELLED`, preserve any existing
   obligation and, unless the user explicitly confirms that the just-cancelled
   cycle left no project changes because none were produced or they were
   reverted, append a `SourceCycle`/`Request` entry for that cycle under
   **Baseline Reconciliation Format**. Preserve older entries; add the source
   only if its exact cycle ID is not already listed.
2. Determine the legal mode before mutating terminal state. If
   `PendingCycleRequest` is not `UNSET`, treat it as the new request for this
   transition unless the user explicitly revises it; do not require the user to
   restate it. When `PendingCycleMode` is set, validate it against that request,
   current `ProjectMode`, and the reconciliation obligation. Otherwise `STANDARD` is the
   default, except that a brownfield `EXPEDITED` cycle may be inferred from
   Developer entry as defined in **Cycle Modes**. Any unresolved reconciliation
   requires `STANDARD`. If a pending preference is invalid, leave the terminal
   state, `Active Work`, `CycleMode`, and `PendingCycleMode` unchanged; persist
   the new request in `PendingCycleRequest`, persist the required user decision
   in `PendingCycleBlockedOn`, do not write `Active Work.BlockedOn`, and ask the
   user to replace or clear the preference, revise the pending request, or
   abandon it. A later resolution must use the persisted pending request rather
   than requiring the user to restate it.
3. After mode validation succeeds, allocate the new ID through **Cycle ID
   Registry**. If the registry append cannot be persisted, leave terminal state
   unchanged and do not start the cycle. Once appended, the ID is reserved even
   if a later state write fails.
4. Record `Handoff.Kind: NEW_CYCLE`, `Handoff.From` = prior terminal state,
   `FailureType: NONE`, and a concise reason. Persist the reserved ID and new
   `Request` into `Active Work`; reset `Scope`, `Architecture`, `Development`,
   `PromotionReason`, `AuditTarget`, and `BlockedOn` to `NONE`; clear recovery
   and outstanding obligations; persist the reconciliation obligation determined
   in step 1.
5. Persist the validated mode into `CycleMode`; clear `PendingCycleMode` to
   `UNSET`, `PendingCycleRequest` to `UNSET`, and `PendingCycleBlockedOn` to
   `NONE`. If reconciliation is unresolved or cancelled-cycle changes are being
   retained or adopted, set `WorkflowState: AUDITING` so Auditor can establish
   baseline status first and mention the obligation concisely in
   `Handoff.Reason` without duplicating its source-cycle provenance there.
6. Otherwise initialize a standard cycle from `ProjectMode`, or an allowed
   expedited brownfield cycle at `DEVELOPING`. `CycleMode` must not remain
   `UNSET` after this transition. The prior cycle is not reopened.

A greenfield bootstrap cancellation removes the runtime, so future workflow work
requires fresh installation and a fresh project-mode decision.

At `AWAITING_USER_SIGNOFF`, available actions are sign off, rework, or cancel;
for expedited work, explicit promotion is also available. Bounded expedited
rework follows normal recovery back to sign-off. Rework requiring a skipped
standard guarantee promotes and restarts the standard brownfield topology at
`AUDITING`.

### Greenfield Bootstrap Cancellation

If cancellation occurs while `ProjectMode` is still `GREENFIELD`, first verify
that the active cycle has not successfully created or materially modified a
project implementation artifact. If such implementation exists, persist the
permanent `BROWNFIELD` transition and use retained brownfield `CANCELLED`
semantics instead. Only when no such implementation exists should cancellation
be treated as a S.T.A.N.D.A.R.D.S. reset rather than a reusable terminal cycle.

The reset must:

- read `.standards/INSTALLATION.json` before removal and revert only
  client-setting mutations recorded there as framework-created; remove a setting
  only when its current value still exactly matches the recorded installed
  value; preserve all others;
- remove the `.standards/` runtime and project-local S.T.A.N.D.A.R.D.S. skill or
  framework files injected by the installer;
- remove only the bounded S.T.A.N.D.A.R.D.S. integration block from `AGENTS.md`
  and `CLAUDE.md`; delete either file only if no non-whitespace content remains;
- leave all project files and role-owned workflow artifacts outside the runtime
  untouched.

S.T.A.N.D.A.R.D.S. does not restore the project working tree. Reverting project
changes is the user's responsibility.

Managed block boundaries define framework ownership; do not decide whether to
delete `AGENTS.md` or `CLAUDE.md` based on who originally created the file. An
existing unbounded `@AGENTS.md` import is user-owned and preserved.

The reset removes `STATE.md` and `CYCLE_IDS.md`, so no persisted `CANCELLED`
state or runtime cycle-ID registry remains. Removal of the runtime ends the
registry-backed no-reuse guarantee. The next workflow attempt requires fresh
installation, which re-evaluates project mode from then-current state and starts
a new cycle-ID registry. Do not carry the cancelled bootstrap's former
`GREENFIELD` classification across reinstall.

This exception ends permanently once Developer observes and verifies that the
active cycle has successfully created or materially modified a project
implementation artifact, regardless of authorship; cancellation after that point
uses retained brownfield `CANCELLED` semantics even if recovery has moved to an
earlier workflow state.

## Installed Runtime Contract

An installed project should provide:

- `AGENTS.md`: project-facing entrypoint to the protocol and role skills;
- `CLAUDE.md`: Claude Code compatibility entrypoint importing `AGENTS.md`;
- `.standards/PROTOCOL.md`: installed canonical protocol;
- `.standards/VERSION.json`: installed framework version used to check upgrade
  eligibility;
- `.standards/INSTALLATION.json`: installer-owned metadata for the client-setting
  mutations and client paths S.T.A.N.D.A.R.D.S. actually created;
- `.standards/CYCLE_IDS.md`: protocol-owned append-only registry of allocated
  cycle IDs for the lifetime of the installed runtime;
- `.standards/MODE.md`: current `ProjectMode`;
- `.standards/STATE.md`: current workflow/cycle state and resumable coordination
  context;
- the S.T.A.N.D.A.R.D.S. workflow skills installed in the location required by
  the selected coding agent;
- explicit-invocation controls: Codex adapters use
  `allow_implicit_invocation: false`; Claude Code project settings use
  `skillOverrides.<skill>: "user-invocable-only"` for installed role skills,
  including Navigator despite its position outside the workflow state machine.

`.standards/MODE.md` contains exactly one canonical `ProjectMode`; its
greenfield-to-brownfield transition follows **Project Modes**.
`.standards/STATE.md` contains exactly one canonical `WorkflowState` and
`CycleMode` and follows **Persisted Workflow State**.
`.standards/INSTALLATION.json` is installer metadata, not workflow state: create
it on first installation, preserve/update it across normal reinstall or upgrade,
and record only mutations the installer actually created. Never retroactively
claim compatible pre-existing settings. `.standards/CYCLE_IDS.md` is protocol
coordination data, not installer metadata; preserve it for the entire lifetime
of the installed runtime as defined by **Cycle ID Registry**.

Record a client directory or settings file in `createdPaths` only if that exact
path was absent before installation created it. Supported paths are `.agents`,
`.agents/skills`, `.claude`, `.claude/skills`, and `.claude/settings.json`.
Preserve this record across reinstall and upgrade.

`.standards/VERSION.json` records the installed framework release separately
from settings ownership and workflow state. Reinstallation with the same version
is allowed. An installer may upgrade to a newer minor or patch release within
the same major version after verifying the existing runtime; it must preserve
workflow data and update the recorded version with the framework assets. Reject
older versions and cross-major upgrades. A major release may be installed into
a fresh project, but moving an existing runtime to another major version needs
an explicit migration process; ordinary installation must not attempt one. The
framework maintainer is responsible for choosing the release version based on
whether changes are backward compatible.

### Installer File Preservation

Installation must be idempotent and preserve project-owned instructions.
Before creating, replacing, updating, or removing a framework-controlled runtime
path or installed skill package, verify ownership deterministically.

Ownership rules:

- `.standards/` is framework-owned only when `.standards/PROTOCOL.md` contains
  `<!-- standards:framework-owned -->`. Otherwise report a path collision and
  do not adopt, overwrite, or remove it.
- An installed skill package is framework-owned only when its root `SKILL.md`
  carries the same marker. Otherwise report a skill collision and do not
  overwrite, merge, or remove it.
- Framework source `PROTOCOL.md` and root workflow `SKILL.md` files must retain
  the marker. Never infer ownership from names, paths, or similar content.

After ownership checks:

- Create `AGENTS.md` from `templates/common/AGENTS.md` if absent. Otherwise
  preserve existing content and add or update only the bounded block between
  `<!-- standards:start -->` and `<!-- standards:end -->`.
- Create `CLAUDE.md` from `templates/common/CLAUDE.md` if absent. If an existing
  user-owned unbounded `@AGENTS.md` import exists, preserve it and do not add a
  framework duplicate. Otherwise add or update a bounded integration block. If
  multiple unbounded imports exist, preserve them and report the conflict.
- Before replacing `.standards/PROTOCOL.md` during an upgrade, require the
  existing cycle-ID registry to be present and valid enough to preserve. If it
  is missing or invalid, stop and report the incomplete runtime.
- Update `.standards/PROTOCOL.md` from the installed framework version only
  after runtime ownership verification and the registry check above. Install or
  update each skill definition only after that destination skill package passes
  its ownership check. Keep the installed protocol aligned with the installed
  skills.
- Preserve Codex `allow_implicit_invocation: false`.
- For Claude Code, safely merge `.claude/settings.json` while preserving
  unrelated settings: add each missing required
  `skillOverrides.<skill>: "user-invocable-only"` and record that exact created
  key/value in `.standards/INSTALLATION.json`; preserve an already-compatible
  unowned value without claiming it; report conflicting values rather than
  overriding them. Existing manifest ownership remains valid only for the exact
  path and installed value recorded.
- Record ownership of newly created client directories and the Claude settings
  file separately from individual setting keys. Never record a pre-existing
  file or directory as created by the installer, even when it is empty or has
  only compatible values.
- Preserve an existing verified `.standards/INSTALLATION.json` and update only
  installer-owned metadata. If it is unexpectedly missing from an otherwise
  verified runtime, stop and report the incomplete runtime; never reconstruct
  ownership by inference.
- Require a valid `.standards/VERSION.json` in an existing verified runtime
  before replacing framework assets. If it is missing or invalid, stop and
  report the incomplete runtime; do not infer a version from file contents.
- Preserve existing `.standards/MODE.md` and `.standards/STATE.md` on normal
  reinstall; initialize them only on first install or explicit reinitialization.
  Do not reset, reinterpret, or discard existing workflow state during upgrades.
  Missing required fields or invalid formats are runtime inconsistencies, not
  permission to add inferred defaults.
- Initialize `.standards/CYCLE_IDS.md` on first install. Thereafter preserve it
  across reinstall, upgrade, and explicit workflow reinitialization; never clear
  or rewrite existing entries while the runtime remains installed. If it is
  unexpectedly missing from a verified runtime, stop and report the incomplete
  runtime; do not recreate it empty or reconstruct it by inference.
- Preserve `.standards/CONTEXT.md`; it is Auditor-owned, not installer-owned.
- Preserve project-level instructions. When they materially conflict with the
  protocol, integration contract, workflow artifacts, or other authoritative
  constraints, follow **Instruction Layering and Conflicts**.
- Reinstallation must not duplicate managed blocks/imports, reset workflow
  mode/state, or erase project instructions.

Installation does not fabricate completed workflow artifacts such as scope,
technical design, project context, tests, reviews, or documentation.

### Project Uninstallation

An explicit `standards uninstall` removes the project's installed runtime and
all verified STANDARDS skill packages for Codex and Claude Code. It is allowed
in either project mode, with or without an active cycle. Removal ends the
runtime's lifetime; it does not complete, sign off, cancel, or revert project
work. The globally installed CLI is unaffected.

- Default to the current directory; accept `--project <path>` for an existing
  project directory. Offer `--dry-run` to report every planned path removal or
  shared-file update without writing files. Help and preview output must explain
  that removing `.standards/` deletes saved workflow state, Auditor context,
  cycle-ID history, and any other content in that directory.
- Require the runtime ownership marker and a valid, supported
  `.standards/INSTALLATION.json` before removal. Do not infer settings ownership
  from current values. Unknown ownership records require an uninstaller that
  understands them. Missing or invalid workflow metadata does not prevent
  explicit removal when ownership is established; uninstall does not need a
  valid version, mode, state, or cycle-ID registry and is not an upgrade.
- Discover marked skill packages under `.agents/skills/` and `.claude/skills/`,
  including marked roles absent from the current distribution. Remove their
  entire verified directories. Remove a recorded client parent directory only
  if it is empty after planned removals. Preserve unrecorded or nonempty client
  directories and unrelated skills; stop on a collision at a known framework
  role rather than adopting it.
- Remove only the bounded STANDARDS block from `AGENTS.md` and `CLAUDE.md`.
  Preserve all text outside it, including unbounded `@AGENTS.md` imports. Delete
  either file only when its remaining content is whitespace. Malformed or
  duplicate boundaries must stop removal before mutation.
- Remove each recorded client setting only if its current value exactly matches
  the recorded installed value. Preserve changed values and report them; leave
  absent settings absent. Preserve compatible settings not recorded as owned,
  unrelated settings, and files or containers whose creation was not recorded.
  Remove `.claude/settings.json` only if its creation was recorded and, after
  reverting owned settings, it contains exactly the installer-created `$schema`
  and an empty `skillOverrides` object. Otherwise retain the file and preserve
  unrelated or changed content. If `createdPaths` is absent, retain the file and
  parent directories even if they look like installer output.
- Validate all affected paths and settings before making changes. Refuse symlinks
  in affected paths or within directories to be removed. Do not follow unrelated
  skill symlinks. A missing runtime with remaining marked skills or integration
  blocks is an incomplete installation requiring ownership recovery, not
  permission to guess. With no runtime or identifiable remnants, report a no-op.
- Apply shared-file changes and skill removals before removing `.standards/`.
  Retain backups during the operation and restore prior files on an ordinary
  failure. If recovery fails, retain backups and report their location. An
  interrupted process may leave a partial operation; retain a mapping from
  backups to original paths and block both install and uninstall until it is
  resolved. Do not claim atomicity across process interruption.
- Preserve implementation, plans, reports, tests, and documentation outside the
  removed runtime and verified skill directories. A later fresh installation
  starts a new runtime and registry; existing artifacts and cycle markers still
  require collision checks when allocating new cycle IDs.

There is no force removal or client-only uninstall. Removing one client while
retaining shared runtime ownership requires a separate contract.

## Canonical Terms

Use these terms consistently across all skills:

- **completed scope**: scope artifact that passed Scoper's completion gate; it
  does not imply separate user approval unless the project adds such a gate.
- **scope-level acceptance conditions**: observable outcomes owned by Scoper,
  each identified by a stable `AC-NNN` for the active cycle.
- **acceptance identifier**: Scoper's stable `AC-NNN` reference reused by
  downstream artifacts.
- **retired acceptance identifier**: an ID whose condition was removed or
  materially replaced; retained so it cannot be reused and no longer a current
  coverage or verification obligation.
- **technical acceptance criteria**: Architect-derived technical conditions
  linked to scope-level acceptance identifiers.
- **development plan**: Developer-owned persisted implementation plan for the
  active cycle. It decomposes the active contract into stable `DEV-NNN` steps,
  records collaboration mode and resumable progress, and never replaces scope,
  architecture, Tester verification, review, or documentation.
- **verification report**: Tester-owned cycle-specific assessment at
  `docs/verification/<Active Work.Id>.md`, recording acceptance coverage, scenario
  allocations, actual execution evidence, gaps, and later-phase dependencies.
  It does not replace scope, design, or workflow coordination state.
- **review report**: Reviewer-owned cycle- and kind-specific assessment at
  `docs/reviews/<Active Work.Id>/implementation.md` or `final-deliverable.md`
  within that same directory. It records inspected inputs, checks, findings,
  limitations, dependencies, and resumable progress under **Review Gates**.
- **documentation record**: Documenter-owned cycle-specific evidence and
  progress at `docs/documentation/<Active Work.Id>.md`, identifying assessed
  documents/content, actual checks and limits, current AC/technical criterion
  references, collaboration mode, target, user style, remaining work, and
  resumable completion context. It is distinct from reusable project
  documentation and does not replace another role's evidence or an acceptance
  authority.
- **synchronization record**: Synchronizer-owned cycle-specific reconciliation
  at `docs/synchronization/<Active Work.Id>.md`, recording assessed identities,
  references to completion/evidence artifacts, discrepancies and their owners,
  limitations, and a resumable conclusion under **Synchronization Gate**. It is
  not an acceptance ledger or user sign-off.
- **project context**: Auditor-owned baseline stored at `.standards/CONTEXT.md`.
  It may persist as evidence across cycles, but cycle-scoped non-baseline entries
  follow the lifecycle in **Persisted Workflow State**. Planned implementation
  does not automatically stale the baseline. `PROJECT_CONTEXT` failure means
  context is materially incomplete, incorrect, or unexpectedly invalidated.
- **completion gate**: conditions required before a role may make a forward
  handoff.
- **failure handoff**: routing a defect to the owner of the affected artifact or
  decision.
- **forward handoff**: advancing after the current completion gate succeeds.
- **resume handoff**: completing a recovery frame by returning to `ResumeAt`, or
  another recovery-directed non-forward transition.
- **cycle mode**: persisted cycle-topology selection, distinct from
  `ProjectMode`; `UNSET` means no topology is currently selected, while
  `STANDARD` and `EXPEDITED` are executable assurance topologies.
- **expedited cycle**: bounded brownfield cycle consisting of Developer then
  implementation Reviewer, with possible sign-off without fabricated skipped
  standard roles or artifacts.
- **promotion handoff**: one-way `PROMOTE` transition from expedited to standard
  that restarts brownfield workflow at `AUDITING` because an omitted guarantee
  is required.
- **recovery frame**: one corrective defect plus routing, preserving owner,
  reason, interrupted `ResumeAt`, and any `RerunThrough` boundary.
- **outstanding obligation**: unresolved corrective work detached from obsolete
  recovery routing, preserving only its owner, failure type, and reason until the
  owning state resolves it.
- **active work**: persisted cycle identity, request, scope/architecture/
  development artifact references, promotion reason, baseline-reconciliation
  provenance, transient audit target, and blocking question; in terminal states
  it describes the latest cycle until `NEW_CYCLE` replaces it.

Do not introduce alternate names for these concepts inside individual skills
unless this protocol is updated first.
