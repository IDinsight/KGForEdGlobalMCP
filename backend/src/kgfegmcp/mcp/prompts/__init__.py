"""This package provides shared FastMCP adapters for generic prompt workflows.

This package is the protocol-facing boundary between FastMCP and the ordinary prompt
application layer. It converts deterministic ``PromptRenderResult`` values into FastMCP
``PromptResult`` messages and attaches exact runtime metadata for framework, snapshot,
profile, prompt configuration, and prompt-version auditability.

The package does not select curriculum packages, load prompt configuration, merge
guidance, enforce rights policy, search standards, traverse graphs, call an LLM, or use
MCP sampling. Those responsibilities remain in the ordinary ``kgfegmcp.prompts``
package.
"""

# Third Party Library
from fastmcp.prompts import PromptResult

# Package Library
from kgfegmcp.prompts.models import PromptRenderResult


def build_prompt_result(result: PromptRenderResult) -> PromptResult:
    """Convert one ordinary rendered prompt into a FastMCP prompt result.

    Parameters
    ----------
    result
        Deterministic prompt text and exact accepted runtime identities.

    Returns
    -------
    PromptResult
        One user-role text message with runtime metadata for client auditability.
    """

    prompt_config = (
        {
            "configured": True,
            "promptConfigId": str(result.prompt_config_id),
            "promptConfigSha256": str(result.prompt_config_sha256),
            "promptConfigVersion": str(result.prompt_config_version),
        }
        if result.prompt_config_id is not None
        else {"configured": False}
    )
    metadata = {
        "epistemicStatus": "llm_inferred",
        "frameworkId": str(result.framework_id),
        "generatedContent": True,
        "graphPackageId": str(result.graph_package_id),
        "profileId": str(result.profile_id),
        "profileVersion": str(result.profile_version),
        "promptConfig": prompt_config,
        "promptVersion": result.prompt_version,
        "snapshotId": str(result.snapshot_id),
    }
    return PromptResult(
        description=result.description, messages=result.message, meta=metadata
    )


__all__ = ["build_prompt_result"]
