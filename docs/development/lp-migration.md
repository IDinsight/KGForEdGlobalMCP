# Staged learning-progression rollout

The feature is being merged in two stages: code first, then smaller data PRs.
The code-first revision retains the six existing standards and learning-component
packages. LP tools and prompts are registered, but querying stored LPs on an
unmigrated package returns capability_unavailable. Existing standards, components,
comparison, and prompt workflows remain usable.

## Current rollout status

**5 of 6 runtime packages migrated:** Nigeria Mathematics supplies 189 buildsTowards
and 297 relatesTo relationships; Ghana Mathematics supplies 299 buildsTowards and
300 relatesTo relationships; Tamil Nadu Mathematics supplies 472 buildsTowards and
435 relatesTo relationships; Ghana English Language supplies 250 buildsTowards and
801 relatesTo relationships; Rwanda Mathematics supplies 938 buildsTowards and
893 relatesTo relationships. All five use matching profiles and prompt configurations
bound to profile version 2.0. CBSE Science retains its existing standards and
learning-component data. Matching maintained input artifacts and build specifications
are now included for all five migrated frameworks. Only CBSE Science's runtime
package and input set await LP migration.

See the [framework catalog](../data/framework-catalog.md) for the active snapshot
and installed counts. Dataset acceptance tests still skip until all six migrations
are complete; package validation and the offline regression suite cover this stage.

## Current and target formats

| Layer | Code-first checkout | LP package after migration |
| --- | --- | --- |
| Manifest / delivery schema | 1.0 / 1.1 | 1.1 / 1.2 |
| Profile version / schema | 1.0 / 1.0 | 2.0 / 1.1 |
| Prompt config version / schema | 2.0.0 / 1.1 | 2.0.0 / 1.1 |
| Prompt config profile binding | 1.0 | 2.0 |
| Stored LP relationships | None | Retained edges and provenance |

The runtime supports both package formats during the transition. It validates exact
profile bytes and rejects unsupported version combinations. No LPs are inferred from
hierarchy or learning-component relationships.

## Verify the code stage

With the locked development environment installed, run from the repository root:

    uv --directory backend run --locked --no-sync pytest -q -rs -m "not costs-money" tests

Algorithm tests use synthetic evidence. Dataset acceptance tests explicitly skip
until all six LP packages are installed. This is partial acceptance, not verification
of the deferred data. Full STDIO/HTTP smoke commands use fixed LP snapshot IDs
and require the later dataset; the offline suite covers the current in-process MCP
surface and backward compatibility.

## Merge data incrementally

For each framework, keep its replacement graph package, exact profile version, and
matching prompt configuration consistent. Validate the replacement read-only before
activating it. Switch the active package atomically and keep exactly one current
snapshot per framework. Never rewrite a sealed package to preserve an old snapshot ID.

Maintained input artifacts can be introduced separately from active packages when a
framework's data needs more than one reviewable PR. Include every required runtime
artifact before activating its manifest; do not split an active package into an
incomplete intermediate state. Choose PR boundaries by diff size, not only file count.

Update the framework catalog with each activation. Discovery and get_capabilities
report the installed subset; LP examples only work for migrated packages.

## Complete acceptance

After all six migrations, require full dataset acceptance:

    uv --directory backend run --locked --no-sync pytest -q -rs -m "not costs-money" --require-lp-dataset tests

Then run full STDIO smoke and applicable bundle or hosted checks described in
[Testing and acceptance](testing.md). No dataset acceptance tests should skip.
The legacy-only package test may skip once no legacy packages remain.

The target dataset has 3,039 buildsTowards and 5,041 relatesTo edges. These are
model-generated judgments with retained provenance, not publisher-endorsed pedagogy.
