"""Tests for registry consistency; no dynamic imports or execution."""

import pytest

from emr.core.registry import SkillRegistry, SkillSpec, default_registry


def test_default_registry_valid() -> None:
    registry = default_registry()
    registry.validate()
    assert registry.get("research-orchestrator").name == "research-orchestrator"


def test_duplicate_registry_entries_rejected() -> None:
    registry = SkillRegistry()
    registry.register(SkillSpec("a"))
    with pytest.raises(ValueError, match="duplicate"):
        registry.register(SkillSpec("a"))


def test_missing_dependency_rejected() -> None:
    registry = SkillRegistry()
    registry.register(SkillSpec("a", dependencies=("missing",)))
    with pytest.raises(ValueError, match="missing"):
        registry.validate()


def test_cycle_rejected() -> None:
    registry = SkillRegistry()
    registry.register(SkillSpec("a", dependencies=("b",)))
    registry.register(SkillSpec("b", dependencies=("a",)))
    with pytest.raises(ValueError, match="cyclic"):
        registry.validate()
