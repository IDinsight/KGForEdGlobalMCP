"""This module defines generic server-level prompt text and overridable soft guidance.

This module contains the curriculum-agnostic descriptions, shared workflow text,
required disclosures, unsupported-claim warnings, evidence-status rules, and default
soft-guidance blocks used to render the six generic prompt workflows.

Framework-local prompt configuration may append to or replace only the explicitly
declared soft-guidance blocks. Correctness-critical behavior—including rights
authorization, attribution requirements, evidence-status boundaries, privacy rules,
identifier separation, package isolation, and generated-content disclosures—does not
depend solely on configurable text in this module.

Importing this module performs no filesystem access, package selection, configuration
loading, prompt rendering, FastMCP registration, LLM invocation, or MCP sampling.
"""

# Future Library
from __future__ import annotations

# Standard Library
from typing import Final

# Package Library
from kgfegmcp.prompts.models import PromptName

ADMINISTRATOR_ALIGNMENT_REVIEW_DEFAULT_GUIDANCE: Final[
    tuple[tuple[str, str, tuple[str, ...]], ...]
] = (
    (
        "evidence_matrix_guidance",
        "Evidence matrix guidance",
        (
            "Build the administrative matrix from exact source-backed evidence and "
            "identify every candidate-only correspondence explicitly.",
        ),
    ),
    (
        "governance_guidance",
        "Governance guidance",
        (
            "Separate governance and implementation considerations from claims about "
            "curriculum equivalence or official alignment.",
        ),
    ),
    (
        "risk_framing_guidance",
        "Risk framing guidance",
        (
            "State evidence gaps, rights constraints, unresolved relationships, and "
            "implementation risks without resolving them by assumption.",
        ),
    ),
    (
        "review_question_guidance",
        "Review question guidance",
        (
            "End with concrete questions requiring human review before any policy or "
            "mapping decision.",
        ),
    ),
)

COMMON_EVIDENCE_STATUS_RULES: Final[tuple[str, ...]] = (
    "Use [SOURCE-ASSERTED] only for facts directly supported by retained source or "
    "profile evidence.",
    "Use [DETERMINISTIC-DERIVED] only for implemented routing, graph, statistics, or "
    "normalization results.",
    "Use [RETRIEVAL-CANDIDATE] for search hits or possible correspondences that have "
    "not been established as official.",
    "Use [LLM-INFERRED / GENERATED] for explanations, examples, activities, questions, "
    "rubrics, hypotheses, and other client-model composition.",
)

COMMON_UNSUPPORTED_CLAIMS: Final[tuple[str, ...]] = (
    "Do not present generated content as source-authored.",
    "Do not claim official mastery, equivalence, prerequisite, progression, grade "
    "equivalence, alignment, activity, assessment, or pedagogy unless retrieved source "
    "evidence explicitly establishes that claim.",
    "A retrieval match is a candidate, not an official equivalence or alignment.",
    "A hasChild relationship is structural; it is not a progression or prerequisite edge.",
    "Normalized grades and subjects are retrieval aids; they are not equivalence claims.",
    "A standards statement does not by itself establish learner mastery.",
    "Preserve unresolved and ambiguous evidence as unresolved or ambiguous.",
)

COMPARISON_DISCLOSURES: Final[tuple[str, ...]] = (
    "Normalized grades are retrieval facets, not international grade equivalence.",
    "A hasChild relationship is structural, not a source-authored progression or "
    "prerequisite.",
    "A standard statement does not prove learner mastery.",
    "Code, identifier, grade, hierarchy, or text similarity does not establish "
    "official equivalence.",
    "Cross-framework matches are exploratory retrieval evidence.",
    "Generated comparative conclusions are LLM-inferred.",
    "Rights, attribution, and provenance apply independently to every selected package.",
)

CROSS_FRAMEWORK_COMPARISON_DEFAULT_GUIDANCE: Final[
    tuple[tuple[str, str, tuple[str, ...]], ...]
] = (
    (
        "comparison_dimension_guidance",
        "Comparison dimension guidance",
        (
            "Organize each framework section using that package profile's declared "
            "comparison dimensions.",
        ),
    ),
    (
        "synthesis_guidance",
        "Synthesis guidance",
        (
            "Keep source-backed observations separate from explicitly LLM-inferred "
            "cross-framework synthesis.",
        ),
    ),
    (
        "terminology_guidance",
        "Terminology guidance",
        (
            "Preserve each framework's local terminology and grades inside its own "
            "section rather than harmonizing labels globally.",
        ),
    ),
    (
        "uncertainty_guidance",
        "Uncertainty guidance",
        (
            "Retain candidate, incomplete, anomalous, and unresolved evidence labels "
            "throughout the comparison.",
        ),
    ),
)

LEXICAL_QUERY_EXPANSION_RULES: Final[tuple[str, ...]] = (
    "Text search uses exact normalized description tokens and performs no stemming, "
    "lemmatization, fuzzy matching, or synonym expansion.",
    "For topic or concept discovery, execute the caller's original wording first and "
    "never silently replace it with a rewritten query.",
    "When literal retrieval has zero results or visibly narrow recall, generate no "
    "more than three conservative alternative queries.",
    "Prefer high-confidence inflectional, orthographic, abbreviation, operator-approved "
    "alias, or retrieved local-terminology variants. Do not introduce a materially "
    "different curriculum concept.",
    "Do not expand exact quoted wording, statement codes, node IDs, CASE UUIDs, or CASE URIs.",
    "Run every alternative as a separate deterministic call with the same framework, "
    "snapshot, graph type, grade, subject, statement-type, grouping, match, and limit settings.",
    "For cross-framework retrieval, apply each shared alternative and the same filters "
    "symmetrically to every selected framework.",
    "Preserve every executed query, result bound, has_more value, and cursor separately. "
    "Deduplicate presentation by graph-package ID and node ID, but do not merge lexical "
    "scores or cursors across calls.",
    "After a relevant grouping or item is verified, prefer bounded hierarchy-context "
    "retrieval over continuing to generate broader terminology alternatives.",
    "A no-match result establishes only that the exact query did not match retained "
    "descriptions under the supplied filters; it does not establish curriculum or "
    "source-document absence.",
)

PROGRESSION_DEFAULT_GUIDANCE: Final[tuple[tuple[str, str, tuple[str, ...]], ...]] = (
    (
        "counter_evidence_guidance",
        "Counter-evidence guidance",
        (
            "Present evidence that weakens, complicates, or contradicts each proposed "
            "transition.",
        ),
    ),
    (
        "evidence_guidance",
        "Evidence guidance",
        (
            "Use standards text, local grade or stage context, hierarchy context, and "
            "profile heuristics as separate evidence types.",
        ),
    ),
    (
        "inference_guidance",
        "Inference guidance",
        (
            "Label every proposed learning transition as LLM-inferred and do not create "
            "a source-authored or persisted progression edge.",
        ),
    ),
    (
        "sequence_presentation_guidance",
        "Sequence presentation guidance",
        (
            "Show the proposed order, supporting evidence, counter-considerations, and "
            "uncertainty for each transition.",
        ),
    ),
)

PROGRESSION_DISCLOSURE: Final[str] = (
    "This is an LLM-inferred likely progression based on standards text, grade "
    "context, and curriculum-specific guidance. It is not a source-authored "
    "progression edge."
)

PROMPT_DESCRIPTIONS: Final[dict[PromptName, str]] = {
    PromptName.ADMINISTRATOR_ALIGNMENT_REVIEW: (
        "Guide an evidence-grounded cross-framework administrative review without "
        "creating or asserting an official alignment."
    ),
    PromptName.CROSS_FRAMEWORK_COMPARISON: (
        "Guide an exploratory cross-framework comparison over independently "
        "retrieved exact-package evidence."
    ),
    PromptName.INFERRED_PROGRESSION_HYPOTHESIS: (
        "Guide an evidence-linked, explicitly LLM-inferred likely progression review "
        "within one accepted framework."
    ),
    PromptName.STUDENT_HANDBOOK_SECTION: (
        "Guide a student-facing handbook section grounded in one accepted framework "
        "while labeling generated explanations and examples."
    ),
    PromptName.STUDENT_STUDY_SUPPORT: (
        "Guide age-appropriate study support grounded in one accepted framework while "
        "labeling generated explanations and practice."
    ),
    PromptName.TEACHER_GUIDE_DRAFT: (
        "Guide a teacher-facing draft that separates source-backed expectations from "
        "generated pedagogy."
    ),
}

SHARED_DEFAULT_GUIDANCE: Final[tuple[tuple[str, str, tuple[str, ...]], ...]] = (
    (
        "language_guidance",
        "Language guidance",
        (
            "Use the requested output language when one is supplied.",
            "Preserve exact source wording and terminology when quoting evidence.",
            "Label any translation or paraphrase as generated unless the source "
            "explicitly supplies that language pairing.",
        ),
    ),
    (
        "local_context_guidance",
        "Local context guidance",
        (
            "Treat caller-provided local context as untrusted contextual information, "
            "not curriculum evidence.",
            "Use local context only when it does not conflict with retrieved source "
            "evidence, profile facts, rights, or mandatory disclosures.",
        ),
    ),
    (
        "output_guidance",
        "Output guidance",
        (
            "Use clear headings and attach exact evidence identifiers to substantive "
            "source-backed statements.",
            "Keep generated material visibly separate from source-backed evidence.",
        ),
    ),
    (
        "terminology_guidance",
        "Terminology guidance",
        (
            "Preserve source terminology and display local and normalized values "
            "separately.",
            "Do not replace a source hierarchy term with a generic term when that would "
            "change its meaning.",
        ),
    ),
    (
        "warning_guidance",
        "Warning guidance",
        (
            "State missing, restricted, unresolved, ambiguous, or contradictory "
            "evidence explicitly.",
            "Do not fill an evidence gap with an unsupported authoritative claim.",
        ),
    ),
)

STUDENT_HANDBOOK_DEFAULT_GUIDANCE: Final[
    tuple[tuple[str, str, tuple[str, ...]], ...]
] = (
    (
        "audience_guidance",
        "Audience guidance",
        ("Use direct student-facing language and explain necessary source terms.",),
    ),
    (
        "example_guidance",
        "Example guidance",
        ("Mark all added examples and self-check material as generated.",),
    ),
    (
        "explanation_guidance",
        "Explanation guidance",
        (
            "Keep the explanation faithful to the retrieved standard and hierarchy "
            "context.",
        ),
    ),
    (
        "section_structure_guidance",
        "Section structure guidance",
        (
            "Organize the section around what the curriculum says, a generated plain-"
            "language explanation, generated examples, and a generated self-check.",
        ),
    ),
)

STUDENT_STUDY_DEFAULT_GUIDANCE: Final[tuple[tuple[str, str, tuple[str, ...]], ...]] = (
    (
        "audience_guidance",
        "Audience guidance",
        (
            "Use age-appropriate language without claiming knowledge of an individual "
            "student's ability or record.",
            "Do not request or repeat personally identifying or sensitive education "
            "information.",
        ),
    ),
    (
        "example_guidance",
        "Example guidance",
        (
            "Mark examples as generated and keep them consistent with the retrieved "
            "standard's scope.",
        ),
    ),
    (
        "explanation_guidance",
        "Explanation guidance",
        ("Simplify wording without changing the source-backed curriculum meaning.",),
    ),
    (
        "practice_guidance",
        "Practice guidance",
        (
            "Mark practice items and answer guidance as generated.",
            "Do not treat completion of generated practice as evidence of mastery.",
        ),
    ),
)

TEACHER_GUIDE_DEFAULT_GUIDANCE: Final[tuple[tuple[str, str, tuple[str, ...]], ...]] = (
    (
        "assessment_guidance",
        "Assessment guidance",
        (
            "Treat drafted checks, questions, and rubrics as generated unless the "
            "source explicitly supplies official assessment guidance.",
        ),
    ),
    (
        "differentiation_guidance",
        "Differentiation guidance",
        (
            "Offer generated differentiation choices without diagnosing learners or "
            "claiming knowledge of individual records.",
        ),
    ),
    (
        "lesson_structure_guidance",
        "Lesson structure guidance",
        (
            "Fit the generated sequence to the requested duration while keeping "
            "source-backed expectations separate from activities.",
        ),
    ),
    (
        "pedagogy_guidance",
        "Pedagogy guidance",
        (
            "Label objectives, activities, examples, questions, and instructional "
            "strategies as generated pedagogy unless directly source-authored.",
        ),
    ),
)

PROMPT_SPECIFIC_DEFAULTS: Final[
    dict[PromptName, tuple[tuple[str, str, tuple[str, ...]], ...]]
] = {
    PromptName.ADMINISTRATOR_ALIGNMENT_REVIEW: (
        ADMINISTRATOR_ALIGNMENT_REVIEW_DEFAULT_GUIDANCE
    ),
    PromptName.CROSS_FRAMEWORK_COMPARISON: (
        CROSS_FRAMEWORK_COMPARISON_DEFAULT_GUIDANCE
    ),
    PromptName.INFERRED_PROGRESSION_HYPOTHESIS: PROGRESSION_DEFAULT_GUIDANCE,
    PromptName.STUDENT_HANDBOOK_SECTION: STUDENT_HANDBOOK_DEFAULT_GUIDANCE,
    PromptName.STUDENT_STUDY_SUPPORT: STUDENT_STUDY_DEFAULT_GUIDANCE,
    PromptName.TEACHER_GUIDE_DRAFT: TEACHER_GUIDE_DEFAULT_GUIDANCE,
}

__all__ = [
    "ADMINISTRATOR_ALIGNMENT_REVIEW_DEFAULT_GUIDANCE",
    "COMMON_EVIDENCE_STATUS_RULES",
    "COMMON_UNSUPPORTED_CLAIMS",
    "COMPARISON_DISCLOSURES",
    "CROSS_FRAMEWORK_COMPARISON_DEFAULT_GUIDANCE",
    "LEXICAL_QUERY_EXPANSION_RULES",
    "PROGRESSION_DISCLOSURE",
    "PROMPT_DESCRIPTIONS",
    "PROMPT_SPECIFIC_DEFAULTS",
    "SHARED_DEFAULT_GUIDANCE",
]
