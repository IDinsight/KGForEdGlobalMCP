"""This module defines generic server-level prompt text and soft defaults.

The constants in this module are curriculum-agnostic, versioned through the public
prompt version, and deterministic. Framework-local configuration may replace or append
only the declared soft-guidance blocks. Correctness-critical rights, attribution,
evidence, privacy, routing, and disclosure policy remains outside these definitions.

Importing this module performs no filesystem access, application bootstrap, package
loading, prompt rendering, or FastMCP registration.
"""

# Future Library
from __future__ import annotations

# Standard Library
from typing import Final

# Package Library
from kgfegmcp.prompts.models import PromptName

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
    PromptName.INFERRED_PROGRESSION_HYPOTHESIS: PROGRESSION_DEFAULT_GUIDANCE,
    PromptName.STUDENT_HANDBOOK_SECTION: STUDENT_HANDBOOK_DEFAULT_GUIDANCE,
    PromptName.STUDENT_STUDY_SUPPORT: STUDENT_STUDY_DEFAULT_GUIDANCE,
    PromptName.TEACHER_GUIDE_DRAFT: TEACHER_GUIDE_DEFAULT_GUIDANCE,
}

__all__ = [
    "COMMON_EVIDENCE_STATUS_RULES",
    "COMMON_UNSUPPORTED_CLAIMS",
    "PROGRESSION_DISCLOSURE",
    "PROMPT_DESCRIPTIONS",
    "PROMPT_SPECIFIC_DEFAULTS",
    "SHARED_DEFAULT_GUIDANCE",
]
