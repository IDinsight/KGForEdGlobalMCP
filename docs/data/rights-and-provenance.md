# Rights and provenance

**KGForEdGlobalMCP** separates **source rights metadata**, **operator exposure decisions**,
and **evidentiary provenance**. A package may contain an artifact that the MCP resource
layer is not permitted to expose.

This separation prevents filesystem presence from being treated as authorization.

## Rights policy contract

Profiles and package manifests use the shared `RightsPolicy` model:

| Field                       | Meaning                                                                                |
|-----------------------------|----------------------------------------------------------------------------------------|
| `sourceLicense`             | Source-facing license/copyright statement retained by the package                      |
| `licenseUri`                | Optional license URI                                                                   |
| `attributionStatement`      | Required source attribution text                                                       |
| `reviewStatus`              | Operator review state for the rights policy                                            |
| `allowStandardResources`    | Permit single-standard/relationship/provenance resource families when other gates pass |
| `allowFullText`             | Permit rights-gated full-text content when other gates pass                            |
| `allowBulkResource`         | Permit approved bulk artifact exposure when other gates pass                           |
| `allowGeneratedDerivatives` | Operator policy for generated derivative workflows                                     |

`allowGeneratedDerivatives` is independent from raw/full-text/bulk resource exposure. A
host being allowed to generate a derivative does not automatically authorize bulk
source extraction.

## Rights review states

Supported review states are:

```text
approved
provisional_operator_approved
restricted
review_required
unreviewed
```

For rights-gated content, the current resource policy treats only these as sufficiently
reviewed:

```text
approved
provisional_operator_approved
```

## Resource access classes

Dedicated resource families use these gates:

| Resource family                                                  | Access rule                                                  |
|------------------------------------------------------------------|--------------------------------------------------------------|
| Catalog, framework, manifest, validation, interpretation profile | Public metadata; no full-text gate                           |
| Unresolved-items report                                          | Reviewed rights + `allowFullText`                            |
| Standard, standard provenance, relationship                      | Reviewed rights + `allowFullText` + `allowStandardResources` |

Generic manifest artifacts use a closed access-class policy:

| Logical artifact          | Access class      | Additional permissions                                           |
|---------------------------|-------------------|------------------------------------------------------------------|
| `validationReport`        | `public_metadata` | None                                                             |
| `unresolvedItems`         | `full_text`       | Reviewed rights + `allowFullText`                                |
| `academicStandardsBundle` | `bulk_content`    | Reviewed rights + full text + standard resources + bulk resource |
| `entityProvenance`        | `bulk_content`    | Same bulk gate                                                   |
| `nodes`                   | `bulk_content`    | Same bulk gate                                                   |
| `relationships`           | `bulk_content`    | Same bulk gate                                                   |
| `relationshipsHasChild`   | `bulk_content`    | Same bulk gate                                                   |
| `standardsFramework`      | `bulk_content`    | Same bulk gate                                                   |
| `standardsFrameworkItems` | `bulk_content`    | Same bulk gate                                                   |

An `additionalArtifacts` entry that lacks an explicit exposure contract fails closed
with resource-not-found behavior rather than inheriting a permissive default.

## Current repository rights posture

All six supplied packages currently declare:

```text
reviewStatus = provisional_operator_approved
allowFullText = true
allowStandardResources = true
allowBulkResource = false
allowGeneratedDerivatives = allowed
```

Therefore single-standard, relationship, provenance, and eligible full-text resource
families can pass their rights gates, while the built-in bulk-content artifact class is
not authorized by the current package rights.

Source license text still differs by framework. For example, several packages retain
`Unknown` or `Not specified in source PDF`, while Rwanda retains an explicit
`© 2025 Rwanda Basic Education Board ... All rights reserved.` source-license statement.
The operator review state does not rewrite the source license.

## Resource size policy is a separate gate

Even when rights allow a resource, the request must fit configured limits:

- maximum bytes read from a source artifact; and
- maximum bytes returned to the client.

The default limits are 32 MiB source-read and 8 MiB returned content. Exceeding a limit
produces access denial rather than silent truncation.

See [Resources and URI templates](../reference/resources.md) for the exact resource
surface.

## Detailed provenance

Every supplied manifest currently declares `hasDetailedProvenance: true` and an
`entityProvenance` artifact.

Detailed provenance is useful for tracing a package-local standard back to retained
source-extraction evidence. The standard-provenance resource addresses one exact outer
`nodeId`:

```text
kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/standard/{node_id}/provenance
```

This is evidence about where the accepted graph statement came from. It does not turn a
later model interpretation into a source-authored claim.

## Resource integrity evidence

Returned resource metadata can include source-artifact evidence such as:

- graph-package ID;
- logical artifact name;
- exact artifact SHA-256; and
- exact artifact size.

Returned resource documents also identify their own canonical URI, byte length,
content SHA-256, MIME type, and representation.

Representations distinguish:

| Representation          | Meaning                                                               |
|-------------------------|-----------------------------------------------------------------------|
| `raw_source`            | Exact retained artifact bytes                                         |
| `deterministic_derived` | Canonical server-generated representation from accepted runtime state |

Local filesystem paths are not exposed as public resource metadata.

## Epistemic status

The broader domain vocabulary distinguishes evidence/claim states such as:

```text
source_asserted
source_extracted
deterministic_derived
accepted_derived
human_reviewed
retrieval_candidate
llm_inferred
unresolved
```

These statuses support a central documentation rule: **where information came from and
how it was produced matters**. Retrieved source evidence, deterministic server output,
and host-model inference should not be collapsed into one undifferentiated claim.

## Attribution and generated material

When generated material uses curriculum evidence, clients should preserve the package's
attribution requirements and clearly separate:

- exact or paraphrased source-backed curriculum evidence;
- deterministic retrieval/context supplied by the server; and
- generated explanation, synthesis, pedagogy, examples, alignment judgments, or
  progression hypotheses produced by the host model.

The framework-local prompt configs reinforce this separation, but they do not override
the resource rights policy.

---

**Next:** [Available frameworks](framework-catalog.md)
