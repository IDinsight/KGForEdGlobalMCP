# PLAN Mode

Use PLAN when the active workflow cycle does not yet have a persisted scope for
`Active Work`.

PLAN creates the first completed scope for the current cycle. It does not mean
the project itself is greenfield; a brownfield cycle normally reaches Scoper
after Auditor and can still use PLAN when the new cycle has no current scope
yet.

## Inputs

Apply the Scoper skill's shared **Inputs**, **Ownership**, and **Invariants**.

## Procedure

1. Establish the requested outcome, boundaries, constraints, non-goals, and
   non-blocking assumptions.
2. Resolve only ambiguities that materially change scope. Persist a blocking
   user question in `Active Work.BlockedOn` before asking it.
3. Break the work into coarse, outcome-oriented work items with observable
   completion conditions and meaningful dependencies. Ensure the acceptance
   conditions cover every verifiable in-scope obligation that must be proven at
   completion. Keep separable obligations in different acceptance conditions
   when their satisfaction or evidence will be established in different workflow
   phases, and assign each condition a unique `AC-NNN` identifier for the active
   cycle.
4. Keep implementation choices out of the scope unless they are already
   established project constraints or requirements.
5. Select the artifact path under the shared provenance rules. Reuse an
   appropriate unmarked project-owned canonical scope document when applicable;
   otherwise create a feature- or change-specific file under `docs/scope/` with
   a `SCOPE` provenance block whose `Cycle` matches `Active Work.Id`. If the
   natural target path is a STANDARDS artifact owned by another cycle, choose a
   distinct path instead of overwriting it.
6. Record the repository-relative artifact path in `Active Work.Scope`.
7. Apply the Scoper completion gate and protocol-defined handoff behavior.

## Result

PLAN succeeds only when the active cycle now has one clear persisted scope that
defines what must be built and what counts as done.

After success, follow the shared Scoper completion, recovery, and handoff rules
in `SKILL.md` and the protocol. PLAN does not independently choose the next
workflow state.
