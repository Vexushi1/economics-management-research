"""Static research task router; it never executes skills or model expressions."""

from __future__ import annotations

from emr.core.contracts import ExecutionNode, ExecutionPlan, ResearchRequest, ResearchType
from emr.core.registry import SkillRegistry


def route_request(
    request: ResearchRequest, registry: SkillRegistry, *, include_model_design: bool = False
) -> ExecutionPlan:
    """Build an opt-in design DAG, preserving the original two-node API default.

    Only analytical, stochastic and hybrid work asks for model design. Empirical
    and replication routing remain planning-only until their dedicated phases.
    Nodes describe future work; this function never runs a plugin or solver.
    """
    registry.validate()
    registry.get("research-orchestrator")
    nodes = [
        ExecutionNode(id="intake", skill_name="research-orchestrator", output_types=("request-summary",)),
        ExecutionNode(
            id="plan", skill_name="research-orchestrator", input_refs=("intake",),
            output_types=("static-research-plan",), deps=("intake",),
        ),
    ]
    if include_model_design and request.research_type in {
        ResearchType.ANALYTICAL_GAME, ResearchType.STOCHASTIC_OPERATIONS, ResearchType.HYBRID
    }:
        registry.get("economic-model-design")
        nodes.append(
            ExecutionNode(
                id="model-design", skill_name="economic-model-design", input_refs=("plan",),
                output_types=("unverified-model-spec",), deps=("plan",),
                approval_required=True,
            )
        )
    return ExecutionPlan(research_type=request.research_type, nodes=tuple(nodes))
