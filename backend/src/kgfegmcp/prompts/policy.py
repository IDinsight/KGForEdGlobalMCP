"""This module enforces correctness-critical policy for generated prompt workflows.

The policy requires explicit permission for generated derivative works, an approved
rights-review state, compatible profile capabilities for code-focused requests, and a
bounded final rendered prompt. These checks are ordinary application logic so they do
not exist only as advisory text inside an MCP prompt.

The policy does not resolve frameworks, read configuration files, search standards,
traverse graphs, generate educational content, or register FastMCP components.
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
                },
                message=(
                    "The selected framework does not support statement-code lookup; "
                    "use topic or an explicit standard identifier instead."
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
