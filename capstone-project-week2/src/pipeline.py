"""End-to-end mask-agent-demask orchestration for AfyaPlus inquiries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from src.agent.runner import build_agent_with_memory
from src.privacy.masking import MaskResult, PrivacyCompliancePipeline, PrivacyLeakError

_agent = None
_privacy = PrivacyCompliancePipeline()


@dataclass
class InquiryResult:
    """Structured response from the AfyaPlus pipeline."""

    final_answer: str
    masked_input: str
    vault_tokens: list[str] = field(default_factory=list)
    intermediate_output: str = ""


def _get_agent():
    global _agent
    if _agent is None:
        _agent = build_agent_with_memory()
    return _agent


def handle_inquiry(
    raw_input: str,
    session_id: str = "default",
    *,
    verbose: bool = False,
) -> InquiryResult:
    """Run the full compliance pipeline: mask, agent, de-mask."""
    mask_result: MaskResult = _privacy.mask(raw_input)
    _privacy.assert_clean(mask_result.masked_text)

    if verbose:
        print(f"[privacy] masked payload dispatched:\n{mask_result.masked_text}\n")

    agent = _get_agent()
    config = {"configurable": {"session_id": session_id}}
    response: Dict[str, Any] = agent.invoke(
        {"input": mask_result.masked_text},
        config=config,
    )
    intermediate = str(response.get("output", "")).strip()
    final_answer = _privacy.demask(intermediate, mask_result.vault)

    return InquiryResult(
        final_answer=final_answer,
        masked_input=mask_result.masked_text,
        vault_tokens=list(mask_result.vault.keys()),
        intermediate_output=intermediate,
    )


def mask_only(raw_input: str) -> MaskResult:
    """Expose masking for tests and diagnostics."""
    result = _privacy.mask(raw_input)
    _privacy.assert_clean(result.masked_text)
    return result
