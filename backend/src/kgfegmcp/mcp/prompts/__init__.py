"""This package provides shared FastMCP adapters for generic prompt workflows.

This package is the protocol-facing boundary between FastMCP and the ordinary prompt
application layer. It converts deterministic single- and multi-context prompt render
results into FastMCP ``PromptResult`` messages and attaches exact runtime metadata for
framework, snapshot, profile, prompt configuration, and prompt-version auditability.

The package does not select curriculum packages, load prompt configuration, merge
guidance, enforce rights policy, search standards, traverse graphs, call an LLM, or use
MCP sampling. Those responsibilities remain in the ordinary ``kgfegmcp.prompts``
package.
"""

# Third Party Library
from fastmcp.prompts import PromptResult

# Package Library
from kgfegmcp.prompts.models import MultiContextPromptRenderResult, PromptRenderResult


def build_multi_context_prompt_result(
    result: MultiContextPromptRenderResult,
) -> PromptResult:
    """Convert one multi-package ordinary workflow to a FastMCP prompt result.

    Parameters
    ----------
    result
        Deterministic prompt text and exact audit context for every selected package.

    Returns
    -------
    PromptResult
        One user-role text message with canonically ordered package metadata.
    """

    contexts = tuple(
        {
            "attributionStatement": context.attribution_statement,
            "frameworkId": str(context.framework_id),
            "graphPackageId": str(context.graph_package_id),
            "graphType": context.graph_type.value,
            "profileId": str(context.profile_id),
            "profileSha256": str(context.profile_sha256),
            "profileVersion": str(context.profile_version),
            "promptConfig": (
                {
                    "configured": True,
                    "promptConfigId": str(context.prompt_config_id),
                    "promptConfigSha256": str(context.prompt_config_sha256),
                    "promptConfigVersion": str(context.prompt_config_version),
                }
                if context.prompt_config_id is not None
                else {"configured": False}
            ),
            "rights": context.rights.model_dump(by_alias=True, mode="json"),
            "snapshotId": str(context.snapshot_id),
            "sourceMetadata": context.source_metadata.model_dump(
                by_alias=True, mode="json"
            ),
        }
        for context in result.contexts
    )
    metadata = {
        "contexts": contexts,
        "epistemicStatus": "llm_inferred",
        "generatedContent": True,
        "promptVersion": result.prompt_version,
    }
    return PromptResult(
        description=result.description, messages=result.message, meta=metadata
    )


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


__all__ = ["build_multi_context_prompt_result", "build_prompt_result"]
