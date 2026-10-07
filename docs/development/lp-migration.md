# Staged learning-progression rollout

The feature was introduced through a code-first PR followed by per-framework runtime
and input-artifact PRs. The runtime continues to support legacy package formats;
stored LP queries on an unmigrated package return capability_unavailable.

## Current rollout status

**6 of 6 runtime packages migrated.** All six frameworks now provide stored LPs,
with matching profiles and prompt configurations bound to profile version 2.0.

| Framework | buildsTowards | relatesTo |
| --- | ---: | ---: |
| Nigeria Mathematics | 189 | 297 |
| Ghana Mathematics | 299 | 300 |
| Tamil Nadu Mathematics | 472 | 435 |
| Ghana English Language | 250 | 801 |
| Rwanda Mathematics | 938 | 893 |
| CBSE Science | 891 | 2315 |
| **Total** | **3039** | **5041** |

Matching maintained input artifacts and build specifications are included for five
frameworks. CBSE Science's input set remains deferred to a separate PR; its complete
runtime package is installed.

See the [framework catalog](../data/framework-catalog.md) for active snapshots and
counts. All dataset acceptance tests must now run; the legacy-only package test may
skip because no legacy packages remain.

## Legacy and current formats

| Layer | Legacy packages | Current LP packages |
| --- | --- | --- |
| Manifest / delivery schema | 1.0 / 1.1 | 1.1 / 1.2 |
| Profile version / schema | 1.0 / 1.0 | 2.0 / 1.1 |
| Prompt config version / schema | 2.0.0 / 1.1 | 2.0.0 / 1.1 |
| Prompt config profile binding | 1.0 | 2.0 |
| Stored LP relationships | None | Retained edges and provenance |

The runtime supports both package formats. It validates exact profile bytes and
rejects unsupported version combinations. No LPs are inferred from hierarchy or
learning-component relationships.

## Verify the complete runtime dataset

With the locked development environment installed, run from the repository root:

    uv --directory backend run --locked --no-sync pytest -q -rs -m "not costs-money" --require-lp-dataset tests

The strict option fails if any baseline LP package is missing. Algorithm tests use
synthetic evidence; dataset tests exercise the installed packages. No dataset
acceptance tests should skip. The legacy-only package test may skip.

Then run the real STDIO protocol smoke:

    uv --directory backend run --locked --no-sync kgfegmcp-stdio-smoke

The smoke starts a separate locked server process and verifies its MCP surface and
representative resource reads. It may resynchronize the runtime environment; reinstall
development/docs extras before running further development commands if needed.
For distribution or hosted changes, also run the applicable bundle or HTTP checks in
[Testing and acceptance](testing.md).

The complete dataset has 3,039 buildsTowards and 5,041 relatesTo edges. These are
model-generated judgments with retained provenance, not publisher-endorsed pedagogy.

## Future package updates

Keep each replacement graph package, exact profile version, and matching prompt
configuration consistent. Validate the replacement read-only before activation.
Switch the active package atomically and keep exactly one current snapshot per
framework. Never rewrite a sealed package to preserve an old snapshot ID.

Maintained input artifacts can be introduced separately when a framework's data needs
more than one reviewable PR. Include every required runtime artifact before activating
its manifest; do not split an active package into an incomplete intermediate state.
Choose PR boundaries by diff size, not only file count.

Update the framework catalog with each activation. Discovery and get_capabilities
report the installed data; LP examples require the corresponding accepted package.
