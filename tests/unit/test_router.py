"""Tests that route selection remains deterministic and side-effect free."""

import pytest

from emr.core.contracts import ResearchRequest, ResearchType
from emr.core.registry import SkillRegistry, default_registry
from emr.core.router import route_request


@pytest.mark.parametrize("research_type", list(ResearchType))
def test_each_research_type_only_generates_intake_plan(research_type: ResearchType) -> None:
    request = ResearchRequest(research_type, "A research problem")
    plan = route_request(request, default_registry())
    assert plan.research_type == research_type
    assert tuple(node.id for node in plan.nodes) == ("intake", "plan")
    assert plan.nodes[1].deps == ("intake",)
    assert all(node.skill_name == "research-orchestrator" for node in plan.nodes)


def test_unknown_research_type_rejected() -> None:
    with pytest.raises(ValueError, match="research_type"):
        ResearchRequest("illegal", "A study")  # type: ignore[arg-type]


def test_empty_request_rejected() -> None:
    with pytest.raises(ValueError, match="description"):
        ResearchRequest(ResearchType.REPLICATION, "  ")


def test_missing_orchestrator_fails() -> None:
    with pytest.raises(KeyError):
        route_request(ResearchRequest(ResearchType.HYBRID, "Test"), SkillRegistry())


@pytest.mark.parametrize('research_type,should_route', [
    (ResearchType.ANALYTICAL_GAME, True),
    (ResearchType.STOCHASTIC_OPERATIONS, True),
    (ResearchType.HYBRID, True),
    (ResearchType.EMPIRICAL_ECONOMETRICS, False),
    (ResearchType.REPLICATION, False),
])
def test_phase3_design_routing_is_opt_in_and_inert(research_type,should_route):
    request = ResearchRequest(research_type, 'Synthetic test question')
    plan = route_request(request, default_registry(), include_model_design=True)
    assert ('model-design' in [n.id for n in plan.nodes]) is should_route
    if should_route:
        assert plan.nodes[-1].approval_required is True
        assert plan.nodes[-1].deps == ('plan',)
        assert plan.nodes[-1].output_types == ('unverified-model-spec',)
