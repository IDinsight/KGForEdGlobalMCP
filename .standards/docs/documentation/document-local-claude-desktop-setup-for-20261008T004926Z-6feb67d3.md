<!-- STANDARDS
Artifact: DOCUMENTATION
Cycle: document-local-claude-desktop-setup-for-20261008T004926Z-6feb67d3
-->

# Documentation Record

`Cycle`: `document-local-claude-desktop-setup-for-20261008T004926Z-6feb67d3` `Status`: `COMPLETE`
`Collaboration`: `AUTONOMOUS` `Target`: `VERTICAL_SLICE` `Target Detail`:
`local Claude Desktop setup for the 0.4.0 STDIO server, from a checkout and from the mcpb bundle`
`User Style`: `tony`

## Assessed Inputs and Boundary

Resumed on 2026-10-08 (America/Detroit) at commit
`c4e78102044fa911299f0aba62daa5c07e8d8f67` on `tz6/doc-updates`.
The comparison baseline is `57f8036`, identified by Scope; its project content
matches the request's `fed4ad4`. Entry git status was clean. Diff from baseline
contains only STATE, scope and architecture records. No recovery, obligations,
baseline reconciliation or blocker is active; STATE remains authoritative.

This DOCUMENTATION cycle edits existing `docs/` pages and necessary owned
workflow records only. Code, config, data, manifest, lock, pyproject, mkdocs
configuration, root README and packaging README are excluded. The selected
capability covers all required documentation surfaces; no additional target
work has been identified. Developer, Tester and implementation Reviewer records
are intentionally omitted. Source inspection is documentation evidence only.

Entry identities (progress and coordination writes are excluded):

- `.standards/CONTEXT.md`: SHA-256 `3656a6a0693ec6b096f36c463e8eb403757212ce981ebc1d55dacdd1d1291621`.
- `.standards/docs/scope/document-local-claude-desktop-setup-for-20261008T004926Z-6feb67d3.md`: SHA-256 `d9fb43943992a2c533a5f16c65e362222e31b80dfcc158bfe3042919ae18de71`.
- `.standards/docs/specs/document-local-claude-desktop-setup-for-20261008T004926Z-6feb67d3.md`: SHA-256 `c6d6b72aa13da15150b4d1e3c4c04f85c147969940fe927aab672f797c0cebac`.
- `packaging/mcpb/manifest.json`: SHA-256 `3b40f967deee21edffb04df15b7c23e44bca4838eb6aa5ba3fc9e953588f6f46`.
- `backend/pyproject.toml`: SHA-256 `373ed7910d12bf92072db1cb314d5699a9bc65891e1415cbc305176afa7f6a26`.
- `backend/uv.lock`: SHA-256 `fedd18633ffbb7336c62bda269bc3d649b273be2c588d7ed73950b21619a6fd3`.
- `backend/src/kgfegmcp/mcpb_server.py`: SHA-256 `b22739a59e5bd107477fe6f290789d9ac55191e480339110f1e1b39c3d71e34e`.
- `backend/src/kgfegmcp/cli/stdio_smoke.py`: SHA-256 `60aa908529d9ca7263b81ff9e47561f70275099d8a4e2b75634746435add1227`.
- `backend/src/kgfegmcp/cli/build_mcpb.py`: SHA-256 `3676404a4a96f5c19c7642f96470128033c634d2c16d9b9417a130c5bc27a97b`.
- `backend/src/kgfegmcp/mcp/tools/frameworks.py`: SHA-256 `985c6c97296a72820496479f2b0b64425400b2347bc99b842a4379428d501d72`.
- `backend/src/kgfegmcp/mcp/tools/capabilities.py`: SHA-256 `4793f64026401794c682c3bcebcfefc44dcccc37e9f8c55519b34eb6d0f55f35`.
- `mkdocs.yml`: SHA-256 `83d47198b28e1d4fc03f7a2575475a7524d4c07a06f042bdfa87a861f1aefbcb`.
- `.agents/skills/documenter/styles/universal.md`: SHA-256 `21dce31e96694331cfe5a7d00678840dc0f2dc9128ce914a78e6be556ff76f43`.
- `.agents/skills/documenter/styles/python.md`: SHA-256 `b1da1c75af72581edd3d0a8076b96450b98777bd07d7a4ce92269f6f709914f2`.
- `.standards/user-styles/documenter/tony.md`: SHA-256 `dd6b47df4a5597cbefcb39a087284b32dd14ad1f3dbb1342b23412884fcd30f6`.
- `docs/getting-started/index.md`: SHA-256 `ec636a749548c0ee21bb35b7ec2b50db7a433549e6354282b2edd12e5c2c7d2e`.
- `docs/getting-started/local-installation.md`: SHA-256 `88cc7f68617273b82d36d1cce9f8036f762e94e984bfe184210e8d9d4d54980a`.
- `docs/getting-started/mcp-clients.md`: SHA-256 `596e12a24c43172c25689ee25ea4c14971eaac155ef0508adea08f33db739131`.
- `docs/getting-started/claude-clients.md`: SHA-256 `6a2762d8fefeb678fd0788534e50db1cc00bc082ba03ccec08456de93729cf0e`.
- `docs/operations/mcpb.md`: SHA-256 `29525cfb204d27706fa096fe3b0135f00b6684cd5fbf106782fb21d716f295c7`.
- `docs/operations/troubleshooting.md`: SHA-256 `8f7e091b96662b0685771fe6c9dca296073a408730442c5daa5d2cbfdd8a2801`.
- `docs/operations/deployment.md`: SHA-256 `69bbc98b4f1762361d98df98972adef06128d3bd89eeb0ea3d3430f90421a1e3`.

## Documentation Work and Evidence

Readers are people connecting a checkout locally and maintainers installing a
bundle. Scope and Architecture remain the authorities for acceptance/technical
criteria. This table records documentation dispositions, not a new acceptance
contract or certification of other roles.

| References | Saved work and evidence | Disposition |
|---|---|---|
| AC-001 | `docs/operations/mcpb.md`, Claude Desktop installation: cited custom install navigation, explicitly unverified enable controls and removal/same-version replacement procedure | Saved and inspected; source/uncertainty technical criterion met |
| AC-002 | Concrete saved steps offered for user review on 2026-10-08; question below | User requested online research; findings incorporated, unsupported details stay labelled unverified; no test confirmation inferred |
| AC-003 | `mcpb.md`, Where does the bundle get uv?: manifest's bare command and absent executable/venv distinguished from MCPB's host-managed Python/dependencies contract | Known unknown explicitly published; no claim that Desktop supplies uv or requires a user install for bundles |
| AC-004, AC-005 | `mcp-clients.md`, `claude-clients.md`, `mcpb.md`, `troubleshooting.md`: macOS-only steps, prior OS unspecified, Desktop 0.4.0 untested on every OS, manifest declarations separated from testing | Inspected; no Windows/Linux setup commands added, so no unsupported platform instructions |
| AC-006 | Quickstart prerequisites and Local installation/Disk space: fresh figures, runtime/preparation data roles, history/environment/download limits | Measurement below; graph and input figures separated; ignored local source tree excluded |
| AC-007 | `mcp-clients.md` and `troubleshooting.md`: project's Python JSON syntax check, quoted config path, stdout discarded and exit meanings explained | Actual valid/invalid runs below; all config-check jq uses under docs replaced; optional archive jq requirement now listed in mcpb.md |
| AC-008 | `mcp-clients.md`: full stop and line wrap after “intact” | Saved diff inspected; changed-line trailing whitespace corrected |
| AC-009 | `mcp-clients.md`, Desktop is running an old copy, with matching cross-references/remedy in `claude-clients.md` and `mcpb.md` | Exact three graph-type strings checked against current source; bundle removal remedy consistently unverified |
| AC-010 | Quickstart smoke introduction explains offline child and normal outer uv synchronization | Added accurate explanation. The stronger claim that skipping a separate sync necessarily fails was not added: code and uv docs show outer run synchronizes first. Architecture explicitly covers this distinction; Scope permits a recorded reason rather than that explanation. No fresh smoke execution or clean-cache experiment claimed |
| AC-011 | `claude-clients.md` evidence table adds Desktop bundle-install row, preserves all prior dates and no new client pass, and notes OS evidence absent | Prior server/unpacked-bundle checks retained with their original scope; they do not become Desktop or OS-specific passes |
| AC-012 | Checkout JSON untouched; path-count explanation added | Parsed and compared exact args, absolute command placeholder, all nine env keys, fixed values and six root mappings against manifest; pass |
| AC-013 | Strict MkDocs build using installed docs tooling, temporary output, plus generated HTML anchor inspection | Exit 0; no changed-page warnings |
| AC-014 | Baseline 57f8036, current full diff and git status (including untracked record) | Only six existing docs pages plus STANDARDS records differ; no code/config/data/manifest/lock/pyproject edits |

No additional required surface is outside the selected capability. Existing
`docs/operations/deployment.md` remains unchanged: its image-content section
already establishes runtime-only graph data. Project agent guidance needs no
change for this documentation-only setup clarification. Reference/API/hosted
server docs have no changed contracts and need no edits.

Saved documentation identities after the final researched edit and checks:

- `docs/getting-started/index.md`: SHA-256 `3b5187263a2dbd0af82fb833874676fec6d895530da0303f461c2ae71c78c64c`.
- `docs/getting-started/local-installation.md`: SHA-256 `dd8add7967eaccb78dc4ef3187aff8ec11155e2eb15041fbccf3884128d66e0a`.
- `docs/getting-started/mcp-clients.md`: SHA-256 `9868dd800b2f5391f221391b23d81bdabd16181736d1b111a1b3c8e4561e5680`.
- `docs/getting-started/claude-clients.md`: SHA-256 `e2ee803d8d92dcb49b443047a8e771b38dd5e23444dcad1e3670ded988ddca03`.
- `docs/operations/mcpb.md`: SHA-256 `dce5b66c91b8b92454f54b2c14577f9afca0eca993163e0eb5620310e88804e4`.
- `docs/operations/troubleshooting.md`: SHA-256 `ad8b300e12a99960731a6221416cc15ad2d3ae44e37cd4920c8d0e6aebb55a73`.

All unchanged contract, source, configuration and selected-style entry hashes
were rechecked against current files and still match. Dirty documentation is
identified by the hashes above, rather than HEAD alone. Progress/state writes
are not deliverable identities.

## Checks and Applicability

Checks on 2026-10-08 (America/Detroit), repository root unless noted:

- Environment: macOS 26.6.2, Darwin arm64; Python 3.13.9;
  MkDocs 1.6.1 in `backend/.venv`. This names the OS for these documentation
  checks only, not for prior smokes or any Desktop observation.
- `node .standards/bin/check.mjs`: entry and post-edit checks exit 0,
  `STANDARDS check passed.`
- Fresh tracked measurement: Python obtains the NUL-separated paths using
  `git ls-files -z`, then sums `Path(path).stat().st_size` for regular existing
  tracked files, and separately sums `data/graph_packages/` and
  `data/input_artifacts/` prefixes. Exit 0; raw results:
  1,463 files, 1,360,275,704 total bytes; graph packages 671,449,871 bytes;
  input artifacts 671,370,714 bytes. This includes the current tracked workflow
  records; their small size does not affect the published rounded estimate.
  It excludes ignored `data/source_artifacts/`, `.venv` and caches.
- `git count-objects -vH`: exit 0; raw output: count 346; size 3.76 MiB;
  in-pack 4989; packs 3; size-pack 281.43 MiB; prune-packable 0;
  garbage 0; size-garbage 0 bytes. Only pack size is published;
  loose objects do not materially change the rounded estimate.
- `du -sk backend/.venv`: exit 0; `328208 backend/.venv` (KiB), about
  320.5 MiB. The measured environment includes dev/docs packages; runtime-only
  size is not established. `du -sk .git`: `292820 .git` (about 286 MiB);
  the guide specifically calls the 281 MiB number Git packs, not the whole tree.
  Fresh-clone pack size, runtime-only environment, uv cache, uv-managed Python,
  built bundle/stage and installed extension footprints were not measured.
  Published “about 2 GB plus downloads/cache” is a sample estimate, not a
  universal minimum. Measurements were not made by summing ignored work trees.
- Config syntax check actually executed from repository root through the shell:
  `backend/.venv/bin/python -m json.tool "<temporary directory>/Application Support/Claude/claude_desktop_config.json" > /dev/null`.
  The temporary directory was
  `/var/folders/_l/vwsxs0q97j7cq6l9rhr4m7rw0000gn/T/kgfegmcp-docs-json-a3a5pe45`.
  Valid synthetic JSON exited 0, empty stdout/stderr. Invalid
  `{"mcpServers": {},}` exited 1, empty stdout and stderr:
  `Illegal trailing comma before end of object: line 1 column 18 (char 17)`.
  This checks the same published interpreter/options/redirection and quoting
  with spaces, substituting a temporary config path; no real client config was
  read or changed. No jq, plutil or uv cache mutation was required.
- Parsed the saved JSON block with Python's json module and asserted the
  absolute uv placeholder, all eight argument tokens in checkout order, nine
  environment keys with exact fixed values and root-relative path mappings.
  Exit 0. The JSON has eight absolute-path placeholders: command, backend
  and six env paths. Source/builder/smoke inspection supports module launch,
  data roots, offline child and exact graph-type output strings.
- From `backend/`, `.venv/bin/mkdocs build --strict --config-file ../mkdocs.yml --site-dir /var/folders/_l/vwsxs0q97j7cq6l9rhr4m7rw0000gn/T/kgfegmcp-docs-site-z9o0dbpy`:
  exit 0, `Documentation built in 0.87 seconds`. The output was temporary and
  removed afterward. Inspected built HTML for seven section IDs: old-copy,
  JSON validation, disk-space, Desktop installation, uv provisioning,
  install/enable and remove/reinstall. All exist. The pre-existing upstream
  Material notice about MkDocs 2.0 appeared; there were no strict-mode link
  or changed-page warnings. This does not test external anchors or Desktop.
- `git diff --check`: first run reported inherited trailing whitespace on the
  typo line newly edited. Fixed that line; the final independent invocation
  exited 0 with no findings. Read-only git emitted sandbox xcrun cache warnings,
  but returned the expected results; escalated checks returned cleanly.
- `git diff --name-only 57f8036 --` and `git status --porcelain=v1`:
  inspected and programmatically asserted every change is one of the six docs
  paths above or `.standards/`. Entry status was clean. No staged edits,
  moved/deleted files or unrelated project changes appeared.

External sources read on 2026-10-08:

- [Anthropic local MCP/Desktop extensions guide](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop):
  custom install navigation and Connectors-menu inspection. It does not supply
  the removal control/same-version claim or this bundle's enable labels.
- [MCPB manifest specification, UV runtime](https://github.com/modelcontextprotocol/mcpb/blob/main/MANIFEST.md#uv-runtime-v04):
  host management of Python/dependencies; no definitive executable-provisioning
  answer for this project's explicit bare-uv launch on the user's Desktop build.
- [uv project command documentation](https://docs.astral.sh/uv/concepts/projects/run/):
  default environment synchronization before running a project command.

No new Desktop, bundle installation, Windows/Linux execution, server smoke,
backend test or formal Tester pass is claimed. Prior evidence remains applicable
because code, data, manifest, dependency lock and configuration identities are
unchanged; it retains its recorded limits. New docs checks cannot expand it.

## Discrepancies, Dependencies, and Remaining Work

No actionable documentation defect remains after the saved fixes and checks.
The explicitly labelled Desktop controls, same-version behavior and uv
provisioning unknowns are allowed scope outcomes, not implementation blockers.

AC-002 question and response are accounted for below. The user requested
online research instead of offering Desktop observations. Research was completed
and incorporated; unsourced details retain their required labels. No approval,
confirmation or client pass is inferred. No further user decision is needed to
meet the scope's permitted sourced-or-unverified documentation outcome. The
question is not a request to approve the Documenter plan or test Desktop;
its recorded outcome does not require a new confirmation gate.

Root README and packaging README still repeat setup claims outside the editing
boundary. This is a non-blocking scope exclusion; downstream review should not
mistake them for edited evidence. Final Reviewer and Synchronizer have not been
invoked or assessed; their normal work follows after the Documenter gate.

### Follow-up research, 2026-10-08

The user's reply requests deeper research, not a Desktop test or confirmation.
Resumption verified all recorded unchanged contract/source/style hashes and all
six saved docs hashes before editing. The first read-only shell here-document
attempt failed with `can't create temp file for here document: operation not
permitted` (exit 1); the escalated retry succeeded. Runtime check passed at entry.

Primary sources rechecked/read:

- [Anthropic local MCP guide](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop):
  confirms custom file installation, inspection of connected servers through
  +/Connectors, and restart/settings checks if tools are absent. No definitive
  separate enable-switch or uninstall/same-version procedure found.
- [Anthropic Desktop Extensions introduction](https://www.anthropic.com/engineering/desktop-extensions):
  confirms double-clicking a bundle opens an installation route and clicking
  Install. It is an introduction, not evidence that this bundle ran.
- [Anthropic allowlist/update guide](https://support.claude.com/en/articles/12592343-enabling-and-using-the-desktop-extension-allowlist),
  dated 2026-03-16: owner upload/Add to team for organization-managed installs;
  allowlisting can block direct file installs. New-version organization updates
  preserve name and increase version, using Upload new version without removal.
  Removing from an organization allowlist is not a local uninstall procedure;
  that control was not substituted into our local instructions.
- [MCPB README](https://github.com/modelcontextprotocol/mcpb/blob/main/README.md),
  manifest specification and hello-world-uv example still establish automatic
  host management of Python/dependencies, not how a particular Desktop build
  supplies/resolves the explicit uv command here. uv provisioning remains unknown.
- [MCPB issue 84](https://github.com/modelcontextprotocol/mcpb/issues/84): an
  Anthropic collaborator's 2026-03-12 reply supports use of server.type uv
  instead of system-Python dependency checks. This does not settle executable
  provisioning. [Issue 291](https://github.com/modelcontextprotocol/mcpb/issues/291)
  is an individual failure report, not a universal install/runtime contract.

Searches for local uninstall and same-version replacement in Anthropic/MCPB
sources did not produce authoritative steps. Other authors' setup guides and
unrelated Claude Code/plugin issues were not promoted to Anthropic instructions.

Saved refinement in mcpb.md: explicit Install dialog and cited double-click
alternative; no assumed mandatory enable switch; no manifest user-config fields;
restart/settings troubleshooting; separate organization-managed route and
versioned-update behavior. Local removal/same-version steps remain unverified.
AC-001/AC-003/AC-004/AC-005/AC-011 dispositions retain their uncertainty/test limits;
AC-002's review outcome is the user's research request, now incorporated.
No contract or other owner's artifact was changed. The initial checked mcpb.md
hash was `e8e4f04ebf239f8f72fccba919619d588c5c92b31ab48607e469475d6924b4cc`;
its prior build is superseded for that page. Other docs and unchanged inputs
retain their checked identities and evidence.

Final checks after the researched edit: strict MkDocs build from backend,
`.venv/bin/mkdocs build --strict --config-file ../mkdocs.yml --site-dir /var/folders/_l/vwsxs0q97j7cq6l9rhr4m7rw0000gn/T/kgfegmcp-docs-research-3i1sd8ze`:
exit 0, `Documentation built in 0.90 seconds`, no changed-page/link warnings.
The same upstream Material notice appeared. Generated HTML contains the four
installation/runtime section anchors. Temporary output was removed. Final
`git diff --check` and boundary assertions over baseline diff plus untracked
status pass. Unchanged contract/source/style input hashes were rechecked;
current documentation hashes appear above. Final runtime checker passed before
the handoff. All earlier unaffected JSON/launch/measurement checks remain
applicable because their assessed inputs are unchanged.

## Resume and Conclusion

On 2026-10-08 the user was asked to review the concrete saved installation
steps (AC-002), with options to retain uncertainty, provide dated observations
or give corrections. The user replied:
“let's do some research online to see what the proper .mcpb installation process is”.
Outcome: deeper online research completed and documented, refining the saved
installation steps. The user supplied no Desktop observations; all unsupported
controls, local same-version replacement and uv-provisioning details remain
explicitly unverified/unknown. This honors the scope's rule that a step without
a source or user confirmation retains its label, and is not approval or testing.

Remaining Documenter work/dependencies/blocking question: NONE. Selected target
and full Documenter gate are complete for the current recorded inputs: all
14 current ACs have dispositions/evidence, required saved edits exist, strict
build and focused checks pass, and there is no actionable owned defect,
pending guided step or obligation. Permitted known unknowns are non-blocking
because scope explicitly accepts their labels and does not require Desktop
execution. All work remained within existing docs pages and owned workflow
records. CompletionPolicy stays NONE. Recovery and obligations are inactive.

Normal handoff: FORWARD to REVIEWING_FINAL, FINAL_DELIVERABLE review in a fresh
independent chat. Exact author-model metadata is unavailable; a different model
of equal or higher capability is advisory. No role is auto-dispatched. Final
Reviewer and Synchronizer assessments, cycle completion and sign-off are not
claimed. On resumption, compare current contract/source/docs identities above;
reassess affected conclusions if changed, preserving prior evidence and labels.
