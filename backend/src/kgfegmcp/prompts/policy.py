"""This module enforces correctness-critical policy for generated prompt workflows.

``PromptPolicy`` applies the non-overridable checks required before a rendered workflow
may be returned. It requires explicit permission to generate derivative material,
requires an accepted rights-review state, verifies that code-focused requests are
supported by the selected curriculum profile, and enforces the maximum rendered-prompt
size.

These checks are implemented as ordinary application logic so that rights, capability,
and size enforcement cannot be weakened or replaced by framework-local prompt text or
caller-supplied context.

This module does not resolve frameworks, load configuration files, merge guidance,
search standards, traverse graphs, generate educational content, register FastMCP
components, call an LLM, or use MCP sampling.
"""

# Future Library
from __future__ import annotations

# Standard Library
from dataclasses import dataclass
from typing import Final

# Package Library
from kgfegmcp.domain.enums import (
    CodeAvailability,
    DerivativeGenerationPolicy,
    RightsReviewStatus,
)
from kgfegmcp.domain.models import RightsPolicy
from kgfegmcp.errors import (
    CapabilityUnavailableError,
    PromptAccessDeniedError,
    PromptRenderingError,
)
from kgfegmcp.profiles.models import CurriculumProfile
from kgfegmcp.prompts.models import (
    MAX_RENDERED_PROMPT_BYTES,
    PromptFocusMode,
    PromptName,
)

_ALLOWED_RIGHTS_REVIEW_STATUSES: Final[frozenset[RightsReviewStatus]] = frozenset(
    {RightsReviewStatus.APPROVED, RightsReviewStatus.PROVISIONAL_OPERATOR_APPROVED}
)


@dataclass(frozen=True, slots=True)
class PromptPolicy:
    """Enforce rights, capability, and size policy before returning a prompt."""

    max_rendered_prompt_bytes: int = MAX_RENDERED_PROMPT_BYTES

    def __post_init__(self) -> None:
        """Require a positive rendered-prompt byte limit.

        Raises
        ------
        ValueError
            If the configured limit is not positive.
        """

        if self.max_rendered_prompt_bytes < 1:
            raise ValueError("max_rendered_prompt_bytes must be positive.")

    @classmethod
    def require_all_derivative_generation_allowed(
        cls, *, prompt_name: PromptName, rights_policies: tuple[RightsPolicy, ...]
    ) -> None:
        """Require independent derivative authorization for every selected package.

        Parameters
        ----------
        prompt_name
            Exact multi-framework generated-content workflow being requested.
        rights_policies
            Exact rights policy for every selected package in deterministic order.

        Raises
        ------
        PromptAccessDeniedError
            If any selected package lacks explicit generated-derivative authorization.
        ValueError
            If no package rights were supplied.
        """

        if not rights_policies:
            raise ValueError("At least one package rights policy is required.")

        for rights in rights_policies:
            cls.require_derivative_generation_allowed(
                prompt_name=prompt_name, rights=rights
            )

    @staticmethod
    def require_derivative_generation_allowed(
        *, prompt_name: PromptName, rights: RightsPolicy
    ) -> None:
        """Require explicit derivative permission and an accepted review status.

        Parameters
        ----------
        prompt_name
            Exact generated-content workflow being requested.
        rights
            Accepted package rights policy already retained in application state.

        Raises
        ------
        PromptAccessDeniedError
            If derivative generation is prohibited, still requires review, or has an
            unapproved rights-review status.
        """

        if (
            rights.allow_generated_derivatives is not DerivativeGenerationPolicy.ALLOWED
            or rights.review_status not in _ALLOWED_RIGHTS_REVIEW_STATUSES
        ):
            raise PromptAccessDeniedError(
                details={
                    "allow_generated_derivatives": (
                        rights.allow_generated_derivatives.value
                    ),
                    "prompt_name": prompt_name.value,
                    "rights_review_status": rights.review_status.value,
                },
                message=(
                    "This prompt is unavailable because the selected framework has "
                    "not been approved for generated derivative material."
                ),
            )

    @staticmethod
    def require_focus_supported(
        *,
        focus_mode: PromptFocusMode,
        profile: CurriculumProfile,
        prompt_name: PromptName,
    ) -> None:
        """Require a selected focus mode to be supported by the exact profile.

        Parameters
        ----------
        focus_mode
            Caller-selected topic, code, or identifier namespace.
        profile
            Exact accepted interpretation profile for the routed package.
        prompt_name
            Exact prompt workflow being rendered.

        Raises
        ------
        CapabilityUnavailableError
            If statement-code focus is requested for an uncoded framework.
        """

        if (
            focus_mode is PromptFocusMode.STATEMENT_CODE
            and profile.code_search_policy.availability is CodeAvailability.NONE
        ):
            raise CapabilityUnavailableError(
                details={
                    "focus_mode": focus_mode.value,
                    "profile_id": str(profile.profile_id),
                    "prompt_name": prompt_name.value,
                    "supported_focus_modes": (
                        PromptFocusMode.CASE_IDENTIFIER_URI.value,
                        PromptFocusMode.CASE_IDENTIFIER_UUID.value,
                        PromptFocusMode.NODE_ID.value,
                        PromptFocusMode.TOPIC.value,
                    ),
                },
                message=(
                    f"Prompt '{prompt_name.value}' cannot use "
                    f"focus_mode='statement_code' because the selected framework "
                    f"does not provide stable statement codes."
                ),
                recovery_hint=(
                    "Reopen the prompt and set focus_mode='topic' when "
                    "topic_or_standard contains a title or visible label. Use "
                    "focus_mode='node_id', 'case_identifier_uuid', or "
                    "'case_identifier_uri' when topic_or_standard contains the "
                    "corresponding exact identifier. Keep the remaining inputs "
                    "unchanged."
                ),
            )

    def require_rendered_size(self, message: str) -> None:
        """Require the final deterministic prompt to fit the approved byte limit.

        Parameters
        ----------
        message
            Complete rendered prompt text encoded to UTF-8 for the size check.

        Raises
        ------
        PromptRenderingError
            If the prompt exceeds the configured maximum and would require truncation.
        """

        rendered_bytes = len(message.encode("utf-8"))

        if rendered_bytes > self.max_rendered_prompt_bytes:
            raise PromptRenderingError(
                details={
                    "max_rendered_prompt_bytes": self.max_rendered_prompt_bytes,
                    "rendered_prompt_bytes": rendered_bytes,
                },
                message=(
                    "The rendered prompt exceeds the configured size limit and cannot "
                    "be returned without losing required guidance."
                ),
            )
