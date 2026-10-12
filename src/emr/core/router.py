"""Build explainable static plans; no computation, LLM call or network I/O."""

from __future__ import annotations

from emr.core.contracts import ExecutionNode, ExecutionPlan, ResearchRequest
from emr.core.registry import SkillRegistry


def route_request(request: ResearchRequest, registry: SkillRegistry) -> ExecutionPlan:
    """Create a two-node planning DAG only.

    The selected research branch is metadata. Subsequent research Skills are
    deliberately not invoked or claimed to exist during Phase 1.
    """
    registry.validate()
    registry.get("research-orchestrator")
    return ExecutionPlan(
        research_type=request.research_type,
        nodes=(
            ExecutionNode(
                id="intake",
                skill_name="research-orchestrator",
                output_types=("request-summary",),
            ),
            ExecutionNode(
                id="plan",
                skill_name="research-orchestrator",
                input_refs=("intake",),
                output_types=("static-research-plan",),
                deps=("intake",),
            ),
        ),
    )
