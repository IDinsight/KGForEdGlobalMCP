# Available frameworks

The repository snapshot reviewed for this documentation contains seven terminal `passed`
Academic Standards graph packages. All seven are marked `isCurrent: true` within their
framework families.

This page summarizes the accepted package/profile metadata included in the repository.
For runtime discovery, use `list_frameworks` and `get_framework`.

## Catalog summary

| Framework              | Jurisdiction      | Local scope       | Subject          | Adoption       | Code search         | Hierarchy        |    Items | hasChild |      LCs | supports | buildsTowards | relatesTo | All relationships |
|------------------------|-------------------|-------------------|------------------|----------------|---------------------|------------------|---------:|---------:|---------:|---------:|--------------:|----------:|------------------:|
| Ghana English Language | Ghana             | BASIC 1–3         | English Language | Adopted        | Partial + prefix    | Tree             |      430 |      430 |      272 |      307 |           250 |       801 |              1788 |
| Ghana Mathematics      | Ghana             | BASIC 4–6         | Mathematics      | Adopted        | Partial + prefix    | Tree             |      302 |      302 |      230 |      273 |           299 |       300 |              1174 |
| CBSE Science           | India             | Class IX–X        | Science          | Unknown        | Partial, exact only | Multi-parent DAG |      874 |     1109 |      853 |      858 |           891 |      2315 |              5173 |
| Tamil Nadu Mathematics | Tamil Nadu, India | Class-1–5         | Mathematics      | Proposed Draft | Partial + prefix    | Tree             |      255 |      255 |      399 |      419 |           472 |       435 |              1581 |
| Nigeria Mathematics    | Nigeria           | PRIMARY ONE–THREE | Mathematics      | Adopted        | None                | Tree             |      242 |      242 |      186 |      204 |           189 |       297 |               932 |
| Rwanda Mathematics     | Rwanda            | P1–P3             | Mathematics      | Adopted        | None                | Tree             |      626 |      626 |      716 |      797 |           938 |       893 |              3254 |
| CAPS English Home Language | South Africa  | Grade R–3         | English Home Language | Adopted   | None                | Tree             |     1144 |     1144 |      912 |     1204 |          2879 |      6708 |             11935 |
| **Total**              |                   |                   |                  |                |                     |                  | **3873** | **4108** | **3568** | **4062** |      **5918** | **11749** |         **25837** |

Across the seven manifests there are **1,439 coded items**, **15 unresolved
relationships**, and **235 multi-parent targets**. The multi-parent targets are all in
the CBSE Science package; the unresolved relationships are in the two Ghana packages.
CAPS adds none of these: it has no statement codes, no unresolved relationships and a
strict tree.

!!! warning "Normalized grade numbers are discovery facets"
    Similar normalized numbers across frameworks do not establish official grade
    equivalence, curricular alignment, or instructional interchangeability.

LP totals are **5,918 buildsTowards** and **11,749 relatesTo**. All-relationship totals
include hasChild, supports and both LP labels; hierarchy/component counts retain their
own meaning. These are stored generated judgments with selected candidate coverage,
not publisher endorsement or exhaustive pedagogy. See [LP usage](../guides/progression.md).

## Ghana — English Language, Basic 1–3

**Framework ID**

```text
ghana-nacca-primary-english-language-basic-1-3
```

**Current snapshot**

```text
ghana-nacca-primary-english-language-basic-1-3@2019+f2a9ab5922a1
```

| Property                 | Value                                                                         |
|--------------------------|-------------------------------------------------------------------------------|
| Official title           | English Language Curriculum for Primary Schools (Basic 1 - 3)                 |
| Issuing authority        | National Council for Curriculum and Assessment (NaCCA), Ministry of Education |
| Local subject            | English Language                                                              |
| Normalized subject       | English Language Arts                                                         |
| Local grades             | BASIC 1, BASIC 2, BASIC 3                                                     |
| Code search              | Partial; exact and prefix                                                     |
| Detailed provenance      | Yes                                                                           |
| Unresolved relationships | 2                                                                             |
| Coded items              | 319                                                                           |

Hierarchy:

```text
Grade > Strand > Sub-Strand > Content Standard > Indicator
```

Important profile caveat: the accepted source preserves printed code anomalies and
explicit unresolved-root fallback relationships. Code/hierarchy matches can require
source-path review.

## Ghana — Mathematics, Basic 4–6

**Framework ID**

```text
ghana-nacca-primary-mathematics-basic-4-6
```

**Current snapshot**

```text
ghana-nacca-primary-mathematics-basic-4-6@2019+ed3b9450718a
```

| Property                 | Value                                                    |
|--------------------------|----------------------------------------------------------|
| Official title           | Mathematics Curriculum for Primary Schools (Basic 4 - 6) |
| Issuing authority        | NaCCA, Ministry of Education                             |
| Local subject            | Mathematics                                              |
| Local grades             | BASIC 4, BASIC 5, BASIC 6                                |
| Code search              | Partial; exact and prefix                                |
| Detailed provenance      | Yes                                                      |
| Unresolved relationships | 13                                                       |
| Coded items              | 254                                                      |

Hierarchy:

```text
Grade > Strand > Sub-Strand > Content Standard > Indicator
```

Important profile caveat: reused codes, same-code/different-content records, and
editorial duplicates mean code equality is retrieval evidence rather than guaranteed
identity.

## India — CBSE Science, Classes IX–X

**Framework ID**

```text
india-cbse-science-learning-framework-classes-9-10
```

**Current snapshot**

```text
india-cbse-science-learning-framework-classes-9-10@undated+21ece81a7ac5
```

| Property             | Value                                                                  |
|----------------------|------------------------------------------------------------------------|
| Official title       | Learning Framework - Science                                           |
| Issuing authority    | Central Board of Secondary Education (CBSE) and Azim Premji University |
| Local subject        | Science                                                                |
| Local grades         | Class IX, Class X                                                      |
| Adoption status      | Unknown                                                                |
| Code search          | Partial; exact only                                                    |
| Detailed provenance  | Yes                                                                    |
| Multi-parent targets | 235                                                                    |
| Coded items          | 831                                                                    |

This framework is the repository's explicit multi-parent example. Source statement types
include Class, Content Domain, Chapter, NCERT Learning Outcome, Content Domain Specific
Learning Outcome, and Indicator. A CLO can have a Chapter parent and one or more NCERT
Learning Outcome parents.

Code families include `LO`, `CLO`, and indicator-style codes, scoped by Class. Numeric
code ranges must not be used to infer hierarchy.

## India — Tamil Nadu Mathematics, Classes 1–5

**Framework ID**

```text
india-tamil-nadu-tnscert-mathematics-classes-1-5
```

**Current snapshot**

```text
india-tamil-nadu-tnscert-mathematics-classes-1-5@2025-proposed-draft+82b183ba9acc
```

| Property            | Value                                                           |
|---------------------|-----------------------------------------------------------------|
| Official title      | Tamil Nadu Curriculum Framework 2025: Mathematics - Classes 1-5 |
| Issuing authority   | TNSCERT                                                         |
| Local grades/stages | Class-1 through Class-5                                         |
| Adoption status     | Proposed Draft                                                  |
| Code search         | Partial; exact and prefix                                       |
| Detailed provenance | Yes                                                             |
| Coded items         | 35                                                              |

Graph hierarchy:

```text
Curricular Goal > Competency > Content
```

Class applicability is a scope dimension on content rather than an additional graph
hierarchy level. The profile preserves authored code surfaces while allowing configured
canonicalization for deterministic lookup.

## Nigeria — Mathematics, Primary 1–3

**Framework ID**

```text
nigeria-nerdc-mathematics-primary-1-3
```

**Current snapshot**

```text
nigeria-nerdc-mathematics-primary-1-3@undated+424e546e2284
```

| Property            | Value                                                         |
|---------------------|---------------------------------------------------------------|
| Official title      | 9-Year Basic Education Mathematics Curriculum for Primary 1-3 |
| Issuing authority   | Nigerian Educational Research and Development Council (NERDC) |
| Local grades        | PRIMARY ONE, PRIMARY TWO, PRIMARY THREE                       |
| Adoption status     | Adopted                                                       |
| Code search         | None                                                          |
| Detailed provenance | Yes                                                           |
| Coded items         | 0                                                             |

Hierarchy:

```text
Grade > Theme > Sub-Theme > Topic > Performance Objective
```

The profile explicitly records that there are no stable statement codes. Repeated local
labels and visible topic ordinals must remain scoped to their source context rather than
being treated as global IDs.

## Rwanda — Mathematics, P1–P3

**Framework ID**

```text
rwanda-reb-mathematics-lower-primary-1-3
```

**Current snapshot**

```text
rwanda-reb-mathematics-lower-primary-1-3@2025+7c2d6f401157
```

| Property            | Value                                                   |
|---------------------|---------------------------------------------------------|
| Official title      | Mathematics Syllabus for Lower Primary \| Primary 1 - 3 |
| Issuing authority   | Rwanda Basic Education Board (REB)                      |
| Local grades        | P1, P2, P3                                              |
| Adoption status     | Adopted                                                 |
| Code search         | None                                                    |
| Detailed provenance | Yes                                                     |
| Coded items         | 0                                                       |

Primary grouping hierarchy:

```text
Grade > Topic Area > Sub-Topic Area > Unit > Key Unit Competence
```

The profile also models Grade Key Competence plus Knowledge, Skills, and Attitudes and
Values objectives under their configured parents.

Important caveat: the accepted upstream configuration contains a scoped repair for a
visible P3 Unit 5 Sub-Topic Area whose Topic Area heading is absent from the source. The
MCP layer must not synthesize the missing source node; configured scope repair remains a
deterministic derivation rather than a source-visible statement.

## South Africa — CAPS English Home Language, Grades R–3

**Framework ID**

```text
south-africa-dbe-caps-english-home-language-grades-r-3
```

**Current snapshot**

```text
south-africa-dbe-caps-english-home-language-grades-r-3@2011+95ab377d1619
```

| Property                 | Value                                                                                                  |
|--------------------------|--------------------------------------------------------------------------------------------------------|
| Official title           | Curriculum and Assessment Policy Statement (CAPS): English Home Language, Foundation Phase, Grades R-3 |
| Issuing authority        | Department of Basic Education                                                                          |
| Local subject            | English Home Language                                                                                  |
| Normalized subject       | English Language Arts                                                                                  |
| Local grades             | Grade R, Grade 1, Grade 2, Grade 3                                                                     |
| Normalized grades        | `K`, `1`, `2`, `3`                                                                                     |
| Source version           | `2011` (from the source's "© 2011"; no exact publication date is recorded)                             |
| Adoption status          | Adopted                                                                                                |
| Code search              | None                                                                                                   |
| Detailed provenance      | Yes                                                                                                    |
| Coded items              | 0                                                                                                      |
| Source license           | Unknown                                                                                                |

Hierarchy:

```text
Grade > Term > Skill Area > Sub-strand > Skill
```

Each grade has Terms 1–4. The source's skill areas are Listening and Speaking (Oral),
Emergent Reading, Emergent Writing, Reading and Phonics, and Writing.

**Grade R.** The source stores Grade R items with the grade value `K`. Clients see these
items labelled "Grade R", and you can filter them by the local label `Grade R` or by the
normalized grade `K`. The profile discloses that `K` is only the source's encoding: it
does not make Grade R equivalent to kindergarten or to any other system's grade. Of the
1,144 items, 385 are Grade R, 237 Grade 1, 262 Grade 2 and 260 Grade 3.

**No statement codes.** CAPS prints no statement codes, and the same Skill wording often
repeats across sub-strands, terms and grades. The profile therefore turns code search off
and discloses: "Code search is unavailable; text and hierarchy context are used for
retrieval." A code search limited to CAPS fails with `capability_unavailable`, and a code
search across all frameworks returns no CAPS matches. Search CAPS by text and keep each
item's Grade, Term, Skill Area and Sub-strand with it. A repeated Skill statement is a
different item in each place it appears.

**Rights.** CAPS uses the same rights posture as the other six packages (see
[Shared package properties](#shared-package-properties)): `provisional_operator_approved`
review, generated derivatives allowed, full text allowed, and no bulk resources. The
source license is recorded as `Unknown`, exactly as the source states it. The attribution
statement is copied from the source:

```text
Source curriculum: Curriculum and Assessment Policy Statement (CAPS), English Home Language, Foundation Phase, Grades R-3. © 2011 Department of Basic Education, Republic of South Africa.
```

**Learning progressions.** CAPS carries 2,879 `buildsTowards` and 6,708 `relatesTo`
edges, the most of any package. As for every framework, these are IDinsight-generated
judgments (`epistemicStatus: llm_inferred`), not statements or endorsements by the
Department of Basic Education, and the tools return the same disclosures for CAPS as for
the other frameworks. Their confidence values are model judgments, not calibrated
probabilities of learner success. CAPS also has the longest stored connections: the
shortest `buildsTowards` path between two standards can be up to 13 hops, compared with
at most 8 in the other packages. See
[Learning progression tools](../reference/progression-tool.md#paths) for how long paths
are returned.

## Shared package properties

All seven supplied packages currently share these properties:

- graph type: `academic_standards`;
- package revision: `1`;
- manifest schema `1.2`, delivery schema `1.2`, source schema `1.0`;
- included domains: `academic_standards`, `learning_components`, `learning_progressions`;
- profile version `2.0` and prompt-config version `2.0.0`;
- terminal validation state: `passed`;
- text search: enabled;
- detailed provenance: present;
- official activity capability: false;
- official assessment-guidance capability: false;
- rights review: `provisional_operator_approved`;
- full-text permission: true;
- standard-resource permission: true;
- bulk-resource permission: false; and
- generated derivatives policy: `allowed`.

For exact runtime metadata, use [Discover frameworks](../guides/framework-discovery.md)
and [Framework and capability tools](../reference/framework-tools.md).

---

**Next:** [Environment variables](../operations/configuration.md)
