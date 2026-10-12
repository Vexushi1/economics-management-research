"""Explicit, offline Skill registry. The registry never loads or runs plugins."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SkillSpec:
    """Metadata for a proposed Skill. `dependencies` are registry names."""

    name: str
    dependencies: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("skill name must not be blank")


class SkillRegistry:
    """Validate a DAG of Skill descriptions without loading arbitrary files."""

    def __init__(self) -> None:
        self._skills: dict[str, SkillSpec] = {}

    def register(self, skill: SkillSpec) -> None:
        """Insert unique Skill metadata; reject overwrites."""
        if skill.name in self._skills:
            raise ValueError(f"duplicate Skill: {skill.name}")
        self._skills[skill.name] = skill

    def get(self, name: str) -> SkillSpec:
        """Return registered metadata or raise a descriptive KeyError."""
        return self._skills[name]

    def validate(self) -> None:
        """Reject missing references and cycles in the declared Skill DAG."""
        visiting: set[str] = set()
        visited: set[str] = set()

        def walk(name: str) -> None:
            if name in visiting:
                raise ValueError(f"cyclic Skill dependency: {name}")
            if name in visited:
                return
            visiting.add(name)
            for dependency in self._skills[name].dependencies:
                if dependency not in self._skills:
                    raise ValueError(f"missing Skill dependency: {dependency}")
                walk(dependency)
            visiting.remove(name)
            visited.add(name)

        for name in self._skills:
            walk(name)


def default_registry() -> SkillRegistry:
    """Phase 1 includes one planning Skill, not an implemented research engine."""
    result = SkillRegistry()
    result.register(SkillSpec("research-orchestrator"))
    return result
