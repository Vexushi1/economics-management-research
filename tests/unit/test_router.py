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
