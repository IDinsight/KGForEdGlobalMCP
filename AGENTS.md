<!-- standards:start -->

# S.T.A.N.D.A.R.D.S.

This project uses the S.T.A.N.D.A.R.D.S. agent workflow.

Navigator is explicitly invoked and stays outside workflow work. Apply the
installed protocol's **Navigator Boundary** when available. Its EXPLAIN
(default), INVESTIGATE, and GRILL_ME modes never edit files, persist questions
or quiz results, dispatch roles, or perform control-plane transitions. Keep its
context in the conversation. Missing runtime metadata or an inactive cycle does
not prevent ordinary explanation from available project evidence; do not
initialize or repair the runtime for Navigator. Inspect diagnostics for side
effects before running them and use only established non-mutating operations.

For workflow roles other than Navigator, before performing workflow work:

1. Read `.standards/PROTOCOL.md` for the canonical roles, states, transitions,
   failure types, and shared terminology.
2. Read `.standards/MODE.md` for the project's current `ProjectMode`.
3. Read `.standards/STATE.md` for the branch's active `WorkflowState`,
   `CycleMode`, pending-cycle coordination fields, `Active Work` (including any
   persisted `PromotionReason` or `BaselineReconciliation`), handoff/recovery
   context, and the `Outstanding Obligations` section. Fresh installations begin
   with `CycleMode: UNSET`. If this is the first real request and `Active Work`
   is `UNSET`, allocate the cycle ID through `.standards/CYCLE_IDS.md` as
   defined by the protocol, persist the request, and persist the legal
   cycle-mode selection before substantive workflow work. If `CYCLE_IDS.md` is
   unexpectedly missing from the installed runtime, stop and report the
   incomplete runtime rather than recreating it. Append the new ID to the
   registry before writing it to `Active Work.Id`; never reuse or remove a
   registered ID while the runtime remains installed. Consume a persisted
   `PendingCycleMode` when present. If a pre-cycle request is blocked, use
   `PendingCycleRequest` and `PendingCycleBlockedOn` rather than asking the user
   to restate it. Clear all pending-cycle fields when the cycle starts; a
   pending `STANDARD` preference prevents Developer from inferring `EXPEDITED`.
   From `SIGNED_OFF` or retained `CANCELLED`, resolve any persisted pending
   request through the protocol's `NEW_CYCLE` transition rather than directly
   replacing terminal `Active Work`.
4. Read `.standards/CONTEXT.md` when it exists and the active role depends on
   project context. Initial greenfield Scoping/Architecture may run before it
   exists, but later reruns must not ignore an existing context file merely
   because the project is still `GREENFIELD`. Auditor owns this file; other
   roles must not silently rewrite it.
5. Workflow role skills are invoked explicitly by the user; do not auto-dispatch
   or model-invoke a role solely from `WorkflowState`. Use `$skill-name` in
   Codex and `/skill-name` in Claude Code. A workflow role may perform
   role-owned work only when it owns the active state. Explicit user
   instructions may authorize the protocol's narrow control-plane transitions
   (pending/initial cycle-mode selection, user-authorized `PROMOTE`,
   `USER_REWORK`, `NEW_CYCLE`, `SIGNOFF`, or `CANCEL`) even from another role's
   or a user-owned state; after recording that transition, perform role work
   only if the invoked skill owns the resulting state. An active role may also
   perform the protocol-defined `PROMOTE` transition without a separate user
   instruction when an expedited cycle requires a skipped standard guarantee.
   Navigator is the exception and may be invoked from any state without
   mutation.
6. If the state is `AWAITING_USER_SIGNOFF`, do not advance until the user signs
   off, requests rework, cancels the cycle, or explicitly promotes an
   `EXPEDITED` cycle to `STANDARD`. If the state is `SIGNED_OFF` or `CANCELLED`,
   there is no active cycle; further requested work starts a new cycle.
7. Respect artifact ownership. Route defects and corrective reruns through
   `.standards/PROTOCOL.md` **Failure Handoffs** and **Recovery Mechanics**; do
   not redefine those mechanics in role-specific behavior. Resolve any
   outstanding obligation owned by the current state before its normal forward
   handoff. In `EXPEDITED`, a skipped role remains skipped rather than
   transferring its ownership; use **Expedited Promotion** if that role becomes
   necessary.
8. During an active cycle, persist blocking user questions in
   `Active Work.BlockedOn`. Pre-cycle control-plane questions must leave
   `Active Work` unchanged and persist any blocked next-cycle request/question
   in the protocol's pending-cycle fields. Do not advance past a role until its
   completion gate succeeds. Update all required `.standards/STATE.md` fields on
   every legal state-changing handoff.
9. Follow `.standards/PROTOCOL.md` for role-completion output rules, including
   commit suggestions and next-role invocations. Apply **Independent Assessment
   Sessions** when entering `TESTING` or either review state, plus **Independent
   Tester Session** or **Independent Reviewer Session** as appropriate. Request
   the required fresh chat; Reviewer handoffs name the review kind and give the
   advisory model recommendation. Persist sufficient context in owned artifacts.
   Verification, review, documentation, and synchronization records are
   discoverable through **Workflow Artifact Provenance**; their paths and
   contents do not add fields to state. Documenter persists checked
   documentation evidence and collaboration/target/style choices in its own
   record; ordinary documentation and agent guidance outside managed blocks
   remain project assets. Apply **Synchronization Gate** and **Standard Cycle
   Completion** before standard sign-off readiness, after canonical recovery
   routing. Synchronizer reconciles evidence and routes stale documentation or
   guidance; it does not rewrite another owner's artifacts or managed framework
   blocks.

Navigator may explain workflow status and likely defect owners, but never
applies failure/recovery routing or gives workflow approval.

Project-specific agent instructions may be added outside the S.T.A.N.D.A.R.D.S.
integration block. Apply `.standards/PROTOCOL.md` **Instruction Layering and
Conflicts** whenever project instructions, workflow artifacts, repository
constraints, or the installed runtime contract materially contradict one
another.
<!-- standards:end -->
