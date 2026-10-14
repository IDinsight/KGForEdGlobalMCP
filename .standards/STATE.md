# S.T.A.N.D.A.R.D.S. Workflow State

`WorkflowState`: `SIGNED_OFF` `CycleMode`: `UNSET` `PendingCycleMode`: `UNSET`
`PendingCycleRequest`: `UNSET` `PendingCycleBlockedOn`: `NONE`

## Active Work

`CompletionPolicy`: `FULL_DELIVERABLE` `Id`:
`slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15` `Request`:
`Slim the six existing frameworks' graph packages to a runtime-only set so large evidence files no longer need to be committed. The server should load only what it needs to serve requests: delivery nodes and relationships, a slimmed per-edge LP relationship provenance (sharded), the provenance index, and small summary, report and resource files. Full evidence (final claims, original provenance, detailed LP relationship files, KG bundles, entity provenance, hierarchy and framework items, and large input-set files) is validated at build or acceptance time, recorded by hash, and kept git-ignored and archived outside GitHub. Decide which provenance fields to keep, how acceptance works without full evidence at load, and where the archive lives. No legacy behavior or backward compatibility needs to be maintained; drop manifest 1.1 support.`
`Scope`:
`.standards/docs/scope/slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15.md`
`Architecture`:
`.standards/docs/specs/slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15.md` `Development`:
`.standards/docs/development/slim-the-six-frameworks-graph-packages-20261013T232953Z-1f3c4a15.md` `PromotionReason`: `NONE`
`AuditTarget`: `NONE` `BlockedOn`: `NONE` `PendingVerificationCadence`: `NONE`

`BaselineReconciliation`: `NONE`

<!-- When non-NONE, use one Markdown list entry per source cycle:
- `SourceCycle`: `<cancelled-cycle-id>`
  `Request`: `<source-cycle request summary>`
Preserve existing entries; see PROTOCOL.md, Baseline Reconciliation Format.
-->

## Handoff

`Kind`: `SIGNOFF` `From`: `AWAITING_USER_SIGNOFF` `FailureType`: `NONE` `Reason`:
`User signed off after completion requirements were revalidated against unchanged inputs.`

## Recovery

`Active`: `false`

## Outstanding Obligations

`Active`: `false`
