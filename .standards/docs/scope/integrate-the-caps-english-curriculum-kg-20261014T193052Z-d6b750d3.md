<!-- STANDARDS
Artifact: SCOPE
Cycle: integrate-the-caps-english-curriculum-kg-20261014T193052Z-d6b750d3
-->

# Integrate CAPS English Home Language (Grades R-3)

## Goal

Serve the South African CAPS English Home Language, Foundation Phase, Grades R-3
curriculum knowledge graph as a seventh framework in the MCP server. The source
is the external KGForEdGlobal export at
`/Users/tzz/Projects/private/idi/KGForEdGlobal/results/kg_for_ed/c939a3a9dcce92ed61d970f4599ced6f2ddc425d1220eeeab9828472b878d24d/`.

MCP clients should be able to discover CAPS and use its Academic Standards,
Learning Components, and stored Learning Progressions with the same tools,
resources, prompts, rights gating, and disclosures as the six existing
frameworks. The six existing packages and the server's set of tools,
resources, and prompts stay as they are.

CAPS connections are longer than any in the existing corpus, up to 13 hops
compared with 8. So that clients can find them, Learning Progression path search
becomes target-aware and its maximum path depth rises. Path search still finds
the same paths, in the same order, that it already finds completely. To save
client tokens and fit long paths within the shared result size limit, path
results always use a compact form. Per-hop boilerplate appears once instead of
in every relationship. As a last resort, a result identifies the path by IDs.
The other Learning Progression tools that return several relationships use the
same compact form: standard progressions, progression search, and traversal.

## Constraints

- The external source export is read-only. It must not be modified.
- Onboarding follows the established data-and-configuration route for adding a
  framework (`docs/development/framework-package.md`). Generic code must not
  branch on the CAPS framework ID, and validation must not be weakened to admit
  it.
- Sealed packages are immutable and builds are deterministic. The six existing
  packages must keep their snapshot IDs and bytes.
- Rights posture (user decision, 2026-10-14): CAPS is served under the same
  posture as the six existing frameworks. That means `reviewStatus`
  `provisional_operator_approved`, generated derivatives allowed, full text
  allowed, and bulk resources not allowed. The source license stays recorded as
  it appears in the source ("Unknown").
- Footprint (user decision, 2026-10-14): a committed CAPS package of roughly
  85–90 MB is acceptable, even though it roughly doubles
  `data/graph_packages/`, the Docker image, and the MCPB bundle. No size budget
  applies beyond existing per-file limits: GitHub's 100 MB, and the server's
  resource limits in `config.py`.
- Grade R (user decision, 2026-10-14): MCP clients see the grade the source
  encodes as `"K"` labelled as "Grade R".
- Path search (user decisions, 2026-10-14): `get_learning_progression_paths`
  becomes target-aware. It stops extending partial paths that cannot reach the
  target within the requested depth. Its maximum `max_depth` rises from 12 to
  16. Every connected CAPS `buildsTowards` pair must be found while the
  existing queue and work budgets stay fixed. The change is generic, applying
  to every framework.
- Path results (user decisions, 2026-10-15): the shared tool-result envelope
  of 100,000 characters and 1 MiB stays fixed. Every path result, including
  one whose full form would fit, uses a compact form. It moves the per-hop
  boilerplate repeated in every relationship to one shared place in the
  result, to save client tokens. That boilerplate includes attribution,
  description, author, provider, license, entity fields, and the confidence
  notice. If the shortest path still does not fit, the result identifies it
  by relationship and node IDs and reports `byte_limit` instead of failing.
- Other Learning Progression results (user decision, 2026-10-15):
  `get_standard_progressions`, `search_learning_progressions`, and
  `traverse_learning_progressions` use the same compact shared-place form.
  `get_learning_progression` keeps its current form.
- Archive-only build inputs stay out of Git. Uploading them to the IDinsight
  Google Drive evidence archive is a manual, user-owned step.
- Tests must not call live or paid LLM services.

## Non-goals

- Changing CAPS curriculum content, Learning Components, or Learning
  Progression judgments. This includes regenerating them or reviewing them
  pedagogically.
- Rebuilding, revising, or re-validating the six existing packages.
- Adding, removing, or renaming MCP tools, resources, resource templates, or
  prompts.
- Changing traversal limits, the default path depth, the path queue and work
  budgets, or any other tool's bounds.
- Changing the shared tool-result envelope or the result form of any tool
  other than `get_learning_progression_paths`, `get_standard_progressions`,
  `search_learning_progressions`, and `traverse_learning_progressions`.
- Adopting Git LFS, external package hosting, or any other way of storing
  packages.
- Changing catalog loading so it tolerates stray non-framework directories
  under `data/graph_packages/`.
- Deploying, publishing, or cutting a release. This includes uploading to the
  Google Drive evidence archive and editing `CHANGELOG.md` by hand.
- Supporting other CAPS phases, subjects, or languages.

## Work

### 1. Verified local copy of the CAPS source

**Intent:** The package must come from a faithful, verifiable copy of the
external export. Builds accept only inputs inside the repository, and the
source project must stay untouched.

**Done when:**

- `AC-001`: The required CAPS copy set has been copied into the repository's
  local preparation area. A verified record of each copied file's hash and size
  matches the external export, and the external export is unchanged.

**Depends on:** None.

### 2. Sealed, accepted CAPS package

**Intent:** Produce an immutable CAPS graph package that passes the same
acceptance standard as the existing six.

**Done when:**

- `AC-002`: A new CAPS package is committed under `data/graph_packages/` with
  terminal `passed` status, and its committed build inputs are in a new input
  set under `data/input_artifacts/`.
- `AC-003`: The package's node and relationship counts match the source
  export: 1 framework, 1,144 framework items, 912 Learning Components, 1,144
  `hasChild`, 1,204 `supports`, 2,879 `buildsTowards`, and 6,708 `relatesTo`.
  Any difference is documented and justified by an existing normalization
  rule.
- `AC-004`: Rebuilding the package from its committed and archived inputs
  produces an identical package.
- `AC-005`: Every committed CAPS file is within GitHub's 100 MB per-file limit,
  and every served CAPS resource is within the server's resource size limits.
  Archive-only inputs are git-ignored and are listed in the package's evidence
  archive record.
- `AC-006`: With the archive-only inputs present locally, evidence-archive
  verification and full (evidence-tier) package validation both pass for CAPS.

**Depends on:** 1, 3.

### 3. CAPS interpretation profile

**Intent:** Tell the server how to interpret and gate CAPS, consistently with
the source and with the user's rights and grade decisions.

**Done when:**

- `AC-007`: The CAPS profile's rights posture is `provisional_operator_approved`,
  with generated derivatives allowed, full text allowed, and bulk resources not
  allowed. Its subject, license, and attribution exactly match the source
  framework root.
- `AC-008`: Every CAPS item's grade is mapped. Clients see the source's `"K"`
  items as "Grade R" and the rest as Grades 1, 2, and 3. Grade filters return
  the matching CAPS items.
- `AC-009`: The source has no statement codes, and clients are told that code
  lookup is unavailable for CAPS. Code-based searches return no false CAPS
  matches.
- `AC-010`: CAPS is identified to clients with its source title, South Africa
  as its jurisdiction, the Department of Basic Education as its author, English
  Home Language as its subject, and Grades R-3 as its grade span.

**Depends on:** None.

### 4. CAPS available through the MCP server

**Intent:** Clients can actually use CAPS through the existing MCP surface.

**Done when:**

- `AC-011`: The framework catalog lists seven frameworks, including CAPS, and
  catalog and framework statistics reflect CAPS.
- `AC-012`: In a real STDIO MCP session, a client can retrieve CAPS
  frameworks, standards, and Learning Components, search them, and get their
  context through the existing tools, resources, and prompts.
- `AC-013`: In a real STDIO MCP session, a client can look up, search, and
  traverse CAPS Learning Progressions. Responses carry the same Learning
  Progression disclosures as the existing frameworks.
- `AC-014`: The MCPB stage built from the repository includes CAPS, and the
  STDIO smoke test passes against that bundle.
- `AC-015`: The Docker build context includes the CAPS package and profile
  without any per-framework list.

**Depends on:** 2, 3.

### 5. No regression to the existing server

**Intent:** Adding CAPS must not change what already ships.

**Done when:**

- `AC-036`: The six existing packages and their profiles are byte-identical to
  the cycle baseline and keep their snapshot IDs. They serve the same results,
  with two exceptions. `get_learning_progression_paths`,
  `get_standard_progressions`, `search_learning_progressions`, and
  `traverse_learning_progressions` return their results in the compact form.
  A request to one of these tools that a size limit or truncation previously
  cut short may now return more items or complete paths.
- `AC-017`: The public MCP surface is unchanged: 19 tools, 1 fixed resource, 14
  resource templates, and 9 prompts.
- `AC-018`: Generic runtime, build, and validation code contains no
  CAPS-specific branching, and no validation rule is relaxed.
- `AC-019`: The full offline test suite passes with the seven-package corpus,
  including progression baselines and rights assertions that cover CAPS.

**Depends on:** 2, 3, 4, 7, 8.

### 6. Project documentation

**Intent:** Hand-maintained documentation should describe the seven-framework
corpus accurately.

**Done when:**

- `AC-020`: Documentation that lists frameworks or states corpus counts,
  totals, sizes, or input sets reflects the seven-framework corpus with CAPS,
  with no stale six-framework statements left.
- `AC-021`: The framework catalog documentation describes CAPS: identity,
  grades including the Grade R labelling, missing statement codes, rights
  posture with the "Unknown" source license, and Learning Progression
  disclosures.
- `AC-027`: The path-search reference documentation states the new maximum
  path depth of 16 and describes target-aware path search.
- `AC-031`: The path-search reference documentation describes when path
  results use the shared-place compact form and when they identify the
  shortest path by IDs only. It also says how clients read each hop's full
  evidence.
- `AC-037`: The Learning Progression reference documentation describes the
  compact shared-place form for `get_standard_progressions`,
  `search_learning_progressions`, and `traverse_learning_progressions`.

**Depends on:** 2, 3, 4, 7, 8.

### 7. Target-aware path search for long connections

**Intent:** Clients can find CAPS's long Learning Progression connections
(up to 13 hops) through the existing path tool, within the existing fixed work
budgets and result envelope, without changing which paths the tool already finds
completely. Path results cost clients fewer tokens.

**Done when:**

- `AC-023`: `get_learning_progression_paths` accepts a `max_depth` of up to 16
  and rejects larger values the same way it rejects out-of-range values today.
  The default path depth stays 6.
- `AC-024`: For every request that the cycle-baseline path search answers
  without truncation, on any of the seven packages, the target-aware search
  returns the same paths in the same order.
- `AC-028`: Take every connected CAPS `buildsTowards` source–target pair
  (43,145 pairs, with shortest paths of up to 13 hops), requested with a
  `max_depth` from that pair's shortest-path length up to 16. Each request
  returns a non-error result that identifies the pair's complete shortest
  path first, without a `queue_limit` or `work_limit` stop, within the fixed
  queue and work budgets. Further paths may be cut by `byte_limit`.
- `AC-032`: Every path result, on any of the seven packages, carries the
  evidence fields that are identical across all its returned relationships
  once, in one shared place, instead of in every relationship, and no
  information is lost. This applies even when the full form would fit. A
  shortest path that fits in this form is returned with its evidence.
- `AC-030`: Take any path result whose shortest path does not fit even in the
  compacted form. It is a normal result, not a `progression_result_too_large`
  error, and identifies the complete shortest path by its relationship and
  node IDs with `byte_limit` reported.
- `AC-026`: Path search never returns a wrong, partial, or wrong-length path.
  Any result that is incomplete reports non-empty truncation reasons.

**Depends on:** 2, 3.

### 8. Compact results for other Learning Progression tools

**Intent:** Reduce client token cost for the other Learning Progression tools
that return several relationships. Their results drop the same repeated
boilerplate that path results drop.

**Done when:**

- `AC-034`: Every result from `get_standard_progressions`,
  `search_learning_progressions`, and `traverse_learning_progressions`, on any
  of the seven packages, carries the evidence fields that are identical across
  all its returned relationships once, in one shared place, instead of in
  every relationship. No information is lost.
- `AC-035`: Each of those three tools returns the same relationships and
  nodes, in the same order, as the cycle baseline for the same request. The
  only exception is where a size limit cut the baseline result: there, a page
  or traversal may now hold more items, and continuation cursors may differ.

**Depends on:** 2, 3.

## Retired Acceptance Identifiers

- `AC-016`: Retired on 2026-10-14 because the target-aware path-search change
  makes "serve the same results" too strict. Replaced by `AC-022`.
- `AC-025`: Retired on 2026-10-15 because a complete shortest path with full
  per-hop evidence cannot fit the fixed result envelope for 10–13 hop CAPS
  pairs. Replaced by `AC-028`, `AC-029`, and `AC-030`.
- `AC-029`: Retired on 2026-10-15 because the compact form now applies to
  every path result, not only to results whose full form does not fit.
  Replaced by `AC-032`.
- `AC-022`: Retired on 2026-10-15 because path results now change form for
  all frameworks. Replaced by `AC-033`.
- `AC-033`: Retired on 2026-10-15 because three more Learning Progression
  tools now use the compact form. Replaced by `AC-036`.

## Assumptions

- The CAPS export is complete and final. Its validation reports pass with no
  errors and no needs-review claims, and its pending-completions file is empty,
  so the empty `.lp_generation.lock` left from 2026-10-10 is treated as
  leftover.
- The framework ID, version token, input-set name, and source publication date
  are design decisions. The attribution's © 2011 is a candidate date, not an
  established one.
- The untracked `data/graph_packages/.claude/` directory is outside this
  cycle's deliverable. Local verification runs in a checkout without it, or
  after the user removes it.
- Grade-R labelling is a presentation requirement. Which normalized value
  represents it is a design decision, as long as AC-008 holds.
