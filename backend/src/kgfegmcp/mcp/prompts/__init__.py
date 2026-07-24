"""This package contains thin FastMCP adapters for generic prompt workflows.

The adapters retrieve immutable lifespan state, delegate deterministic rendering to the
ordinary prompt service, translate application failures at the MCP boundary, and return
one user-role text message with dynamic prompt metadata. They do not load files, search
standards, traverse graphs, enforce rights independently, call an LLM, or use sampling.
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
