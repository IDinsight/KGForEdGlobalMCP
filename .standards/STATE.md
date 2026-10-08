# S.T.A.N.D.A.R.D.S. Workflow State

`WorkflowState`: `SYNCHRONIZING` `CycleMode`: `DOCUMENTATION` `PendingCycleMode`:
`UNSET` `PendingCycleRequest`: `UNSET` `PendingCycleBlockedOn`: `NONE`

## Active Work

`CompletionPolicy`: `NONE` `Id`:
`document-local-claude-desktop-setup-for-20261008T004926Z-6feb67d3` `Request`:
`Standalone Documenter entry (user invoked /documenter on 2026-10-07). Documenter choices: collaboration AUTONOMOUS; target VERTICAL_SLICE, capability "local Claude Desktop setup for the 0.4.0 STDIO server, from a checkout and from the mcpb bundle"; user style tony. Request: close the documentation gaps a Navigator review found on 2026-10-07 at commit fed4ad4 on main. Editing boundary: the docs folder only; do not change code, the MCPB manifest, pyproject, the lock file, data or config. Do not mark anything as tested without evidence; Desktop runs of 0.4.0 and bundle installs in Desktop are still untested; keep the "What has and has not been checked" table in docs/getting-started/claude-clients.md accurate. Gap 1, installing the bundle in Desktop: docs/operations/mcpb.md section "Claude Desktop installation" (about lines 269-288) explains building the bundle but not how to install it in Desktop, enable it, or remove an older installed extension (needed before reinstalling a bundle with the same version number); add these steps, citing an external Anthropic source or labelling the steps unverified, then ask the user. Gap 2, where the bundle gets uv: packaging/mcpb/manifest.json line 38 launches a bare uv command (server type uv); document what the evidence supports about whether Desktop provides uv or the user must install it and put it on PATH, or name it as a known unknown; do not guess. Gap 3, OS coverage: docs cover macOS only (config path, jq, osascript, Claude logs folder; docs/getting-started/mcp-clients.md lines 42-128 and 264-272) while the manifest declares darwin, linux and win32 (lines 7-11); say plainly which platforms are documented and tested; add Windows or Linux steps only with a cited source, labelled untested. Gap 4, disk space: add an estimate to the prerequisites in docs/getting-started/index.md and docs/getting-started/local-installation.md; user measured about 1.3 GB tracked files (data/graph_packages about 640 MB, needed by the server; data/input_artifacts about 640 MB, not needed, per "What the image contains" in docs/operations/deployment.md) plus about 280 MB git history (local pack size; fresh clone may differ) plus the uv Python environment; re-measure before writing numbers. Gap 5, jq is not a listed prerequisite though used to check the config JSON (docs/getting-started/mcp-clients.md lines 111-113, docs/operations/troubleshooting.md lines 215-219); add it or offer a way to check the JSON without it. Gap 6, typo: docs/getting-started/mcp-clients.md line 172 reads "intact Launching", missing a full stop. Gap 7: add a short Troubleshooting entry to docs/getting-started/mcp-clients.md for the old-copy check (currently only in docs/getting-started/claude-clients.md lines 70-74 and docs/operations/mcpb.md lines 284-288): a single "Graph types:" line instead of separate "Routing graph types:" and "Included graph types:" lines means Desktop is running an old copy. Also consider (Documenter's judgment): say why the smoke test must run after uv sync, since it runs uv with the offline flag (backend/src/kgfegmcp/cli/stdio_smoke.py line 137). Done means each gap is fixed with cited evidence or explicitly left as a known unknown; the macOS checkout path in docs/getting-started/mcp-clients.md still matches the code (absolute uv path, python -m kgfegmcp.mcpb_server, nine path replacements); the docs build cleanly if the project has a docs build check.`
`Scope`:
`.standards/docs/scope/document-local-claude-desktop-setup-for-20261008T004926Z-6feb67d3.md`
`Architecture`:
`.standards/docs/specs/document-local-claude-desktop-setup-for-20261008T004926Z-6feb67d3.md` `Development`: `NONE` `PromotionReason`: `NONE`
`AuditTarget`: `NONE` `BlockedOn`: `NONE` `PendingVerificationCadence`: `NONE`

`BaselineReconciliation`: `NONE`

<!-- When non-NONE, use one Markdown list entry per source cycle:
- `SourceCycle`: `<cancelled-cycle-id>`
  `Request`: `<source-cycle request summary>`
Preserve existing entries; see PROTOCOL.md, Baseline Reconciliation Format.
-->

## Handoff

`Kind`: `FORWARD` `From`: `REVIEWING_FINAL` `FailureType`: `NONE` `Reason`:
`FINAL_DELIVERABLE review passed with no material findings for AC-001 to AC-014; ready for synchronization.`

## Recovery

`Active`: `false`

## Outstanding Obligations

`Active`: `false`
