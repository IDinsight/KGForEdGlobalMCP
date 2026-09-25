---
name: scoper
description:
  Define or revise the scope for a project or change before architecture or
  implementation. Use for greenfield planning, post-audit brownfield planning,
  or when a downstream phase reports a scoping problem. Produce a concise,
  persisted, implementation-agnostic scope with goals, boundaries, constraints,
  acceptance conditions, dependencies, and ordered work items. Normal completion
  hands off to Architect; recovery follows the protocol's recovery-stack and
  invalidation rules.
---

<!-- standards:framework-owned -->

# Scoper

Turn an idea or requested change into a clear, bounded statement of **what must
be built and what counts as done**.

Apply to any project: applications, services, libraries, frameworks, CLIs,
tooling, systems software, infrastructure, or similar work.

## Ownership

Own the project scope. The completed scope must be persisted under the
protocol's **Workflow Artifact Provenance** rules. An appropriate pre-existing
unmarked project-owned scope document may remain the canonical scope location.
If Scoper creates a new scope artifact, use a feature- or change-specific file
under `docs/scope/` and add the current-cycle `SCOPE` provenance block. Never
overwrite, repurpose, or adopt a STANDARDS scope artifact whose recorded cycle
differs from `Active Work.Id`. Record the selected repository-relative path in
`STATE.md` as `Active Work.Scope`.

Own the wording and stable `AC-NNN` identifiers of scope-level acceptance
conditions for the active cycle.

Do not write architecture specs, production code, tests, audit/context files,
reviews, or user documentation.

## Inputs

- Always: `Active Work.Request`, explicit user constraints, the current
  persisted scope when one exists, and `.standards/CONTEXT.md` when it exists
  and is relevant.
- Greenfield Scoping before the first audit, including recovery reruns, may
  proceed without `CONTEXT.md`; its absence is intentional unless the requested
  work requires project facts that cannot otherwise be established.
- Brownfield Scoping requires the Auditor's project context for the active
  cycle.
- When `Active Work.PromotionReason` is not `NONE`, treat it as durable workflow
  context explaining why a former expedited cycle required the standard
  topology. Use it to surface any unresolved scope question, but do not treat
  the promotion reason itself as user-approved scope unless supported by the
  request, project context, or explicit user input.
- When the active recovery frame's `Owner` is `SCOPING`, use that frame as the
  defect Scoper must correct.
- When recovery is active but the active frame's `Owner` is not `SCOPING`,
  Scoper is a downstream rerun after another correction. Re-evaluate the scope
  against the updated inputs and preserve the active recovery frame.

## Mode Selection

Select exactly one Scoper invocation mode before changing the scope. These modes
are local execution paths for Scoper and are separate from `.standards/MODE.md`
(`GREENFIELD` / `BROWNFIELD`).

- **PLAN** — use when the active cycle does not yet have a persisted scope for
  `Active Work`. Read and follow [`modes/plan.md`](modes/plan.md).
- **REPLAN** — use when `Active Work.Scope` identifies an existing persisted
  scope that must be corrected, revised, or reconciled with changed inputs. Read
  and follow [`modes/replan.md`](modes/replan.md).

Load only the selected mode file from `modes/`. A request phrased as "add X"
does not create a separate mode or bypass lifecycle rules: if it starts a new
cycle with no current-cycle scope, use PLAN; if it changes an existing
active-cycle scope, use REPLAN.

For either mode, read and follow [`template.md`](template.md). It is the
authoritative shape and authoring contract for the persisted scope artifact.

## Invariants

1. Ask only questions that materially change scope. Resolve blocking ambiguity
   before advancing. Persist any blocking user question in
   `Active Work.BlockedOn` before asking and clear it after incorporating the
   answer.
2. If required project context is missing, materially incomplete, incorrect, or
   unexpectedly invalidated, stop scoping and issue a `PROJECT_CONTEXT` failure
   handoff to Auditor instead of performing a repository-wide audit. Treat an
   **Active-Cycle Non-Baseline Work** entry whose recorded cycle does not match
   the current `Active Work.Id` as stale project context that Auditor must
   reconcile before Scoper relies on it. Do not treat intentionally absent
   project context before the first greenfield audit as defective when scoping
   can proceed without it. Once `.standards/CONTEXT.md` exists, do not ignore it
   merely because `ProjectMode` is still `GREENFIELD`. Planned implementation
   changes within the active cycle do not by themselves make project context
   stale.
3. Treat planned architectural constraints recorded in `.standards/CONTEXT.md`
   as Architect-owned design information, not as independently established scope
   constraints. They constrain Scoper only when the same constraint is
   independently established by the user request or by pre-existing project
   requirements, policy, platform, compatibility, or other baseline constraints.

## Completion Gate

Scoping is complete when:

- the persisted scope satisfies the artifact shape and authoring contract in
  `template.md`, including matching current-cycle provenance when Scoper created
  the artifact;
- every verifiable in-scope obligation that must be proven at completion is
  represented by one or more current scope-level acceptance conditions;
- separable obligations whose satisfaction or verification evidence is
  established in different workflow phases are not combined under one acceptance
  identifier;
- every current scope-level acceptance condition has a unique, stable `AC-NNN`
  identifier, and retired identifiers remain recorded and unreused;
- no blocking scope question remains unresolved;
- `Active Work.Scope` points to the completed persisted scope.

On normal success, the scope is a **completed scope**. Hand off to
**Architect**.

When recovery is active, apply `.standards/PROTOCOL.md` **Recovery Mechanics**
after the completion gate succeeds. Scoper determines downstream invalidation
only when it owns the active frame; otherwise it follows the protocol as a
downstream rerun.
