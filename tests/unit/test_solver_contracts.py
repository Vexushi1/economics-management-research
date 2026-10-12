"""The solver is a deliberately non-executing, clean-room skeleton."""

import pytest

from emr.core.contracts import SolveResult, SolveStatus, VerificationReport, VerificationStatus
from emr.solver import PendingEquilibriumSolver
from emr.solver.base import ModelSpec


def test_pending_solver_cannot_fabricate_result() -> None:
    model = ModelSpec("synthetic-stackelberg", ("leader", "follower"), ("leader", "follower"))
    solver = PendingEquilibriumSolver()
    with pytest.raises(NotImplementedError):
        solver.solve(model)
    with pytest.raises(NotImplementedError):
        solver.verify(model, SolveResult())


def test_default_math_and_proof_status_are_unresolved() -> None:
    assert SolveResult().status == SolveStatus.UNRESOLVED
    assert VerificationReport().status == VerificationStatus.NOT_VERIFIED


def test_untrusted_input_is_not_executed(tmp_path) -> None:
    sentinel = tmp_path / "must-not-exist"
    hostile = f"__import__('pathlib').Path('{sentinel}').touch()"
    model = ModelSpec(hostile, ("leader",), ("leader",))
    assert model.model_id == hostile
    assert not sentinel.exists()
