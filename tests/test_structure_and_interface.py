from dataclasses import dataclass

import jax.numpy as jnp
import pytest

import finhjb as fjb
from tests.helpers import ManualBoundary, SimpleParameter


@dataclass
class DependentBoundary(fjb.AbstractBoundary[SimpleParameter]):
    """Boundary class used to verify dependency graph construction."""

    @staticmethod
    def compute_s_max(p: SimpleParameter) -> float:
        return 2.0

    @staticmethod
    def compute_v_left(p: SimpleParameter) -> float:
        return -1.0

    @staticmethod
    def compute_v_right(p: SimpleParameter, s_max: float) -> float:
        return 10.0 + s_max


@dataclass
class InvalidBoundary(fjb.AbstractBoundary[SimpleParameter]):
    """Boundary with conflicting explicit and computed values (invalid)."""

    @staticmethod
    def compute_s_max(p: SimpleParameter) -> float:
        return 3.0


class GuessPolicyDict(fjb.AbstractPolicyDict):
    """Policy dict placeholder for serialization tests."""

    u: object


@dataclass
class GuessPolicy(fjb.AbstractPolicy[SimpleParameter, GuessPolicyDict]):
    """Minimal policy for load/save tests."""

    @staticmethod
    def initialize(grid: fjb.Grid, p: SimpleParameter) -> GuessPolicyDict:
        return GuessPolicyDict(u=jnp.zeros_like(grid.s))

    @staticmethod
    @fjb.explicit_policy(order=1)
    def keep(grid: fjb.Grid) -> fjb.Grid:
        grid.policy["u"] = jnp.zeros_like(grid.s)
        return grid


@dataclass
class GuessModel(fjb.AbstractModel[SimpleParameter, GuessPolicyDict]):
    """Model for serialization and loader tests."""

    @staticmethod
    def hjb_residual(v, dv, d2v, s, policy, jump, boundary, p):
        return v - s

def test_immutable_boundary_helper_methods(boundary):
    frozen = boundary.frozen_boundary
    assert frozen.get_boundaries() == (
        frozen.s_min,
        frozen.s_max,
        frozen.v_left,
        frozen.v_right,
    )
    assert set(frozen.get_boundary_dict().keys()) == {
        "s_min",
        "s_max",
        "v_left",
        "v_right",
    }


def test_dependent_boundary_computes_values_in_dependency_order():
    boundary = DependentBoundary(p=SimpleParameter(), s_min=0.0)
    frozen = boundary.frozen_boundary
    assert frozen.s_max == pytest.approx(2.0)
    assert frozen.v_left == pytest.approx(-1.0)
    assert frozen.v_right == pytest.approx(12.0)


def test_boundary_rejects_explicit_value_plus_compute_method():
    with pytest.raises(ValueError, match='cannot be defined simultaneously'):
        InvalidBoundary(p=SimpleParameter(), s_min=0.0, s_max=2.0)


def test_grids_collection_operations(solver):
    grid = solver._grid
    grids = fjb.Grids(param_name="alpha")
    grids.add(0.1, grid).add(0.2, grid)

    selected = grids.select_grids([0.1])
    assert len(selected) == 1

    merged = grids.merge(fjb.Grids(param_name="alpha", data={0.3: grid}))
    assert len(merged) == 3


def test_load_helpers_roundtrip_and_type_validation(tmp_path):
    parameter = SimpleParameter()
    boundary = ManualBoundary(
        p=parameter,
        s_min=0.0,
        s_max=1.0,
        v_left=0.0,
        v_right=1.0,
    )
    solver = fjb.Solver(
        boundary=boundary,
        model=GuessModel(policy=GuessPolicy()),
        policy_guess=True,
        number=8,
    )

    grid_path = tmp_path / "grid"
    grids_path = tmp_path / "grids"
    result_path = tmp_path / "result"

    solver._grid.save(grid_path)
    loaded_grid = fjb.load_grid(grid_path)
    assert loaded_grid.number == solver._grid.number

    grids = fjb.Grids(param_name="alpha", data={0.1: solver._grid})
    grids.save(grids_path)
    loaded_grids = fjb.load_grids(grids_path)
    assert len(loaded_grids.data) == 1

    result = fjb.algorithm.SensitivityResult(result={"x": jnp.array([1.0])}, grids=grids)
    result.save(result_path)
    loaded_result = fjb.load_sensitivity_result(result_path)
    assert "x" in loaded_result.result

    with pytest.raises(TypeError, match="Expected Grids"):
        fjb.interface.load._validate_type(loaded_grid, fjb.structure._grid.Grids)


def test_linear_and_quadratic_value_guess(boundary):
    s = jnp.linspace(0.0, 1.0, 11)

    linear = fjb.LinearInitialValue(boundary.p, boundary.frozen_boundary).guess_value(s)
    quadratic = fjb.QuadraticInitialValue(
        boundary.p,
        boundary.frozen_boundary,
        a_sign=1,
        curvature=0.5,
    ).guess_value(s)

    assert linear.shape == s.shape
    assert quadratic.shape == s.shape
    assert float(linear[0]) == pytest.approx(float(boundary.frozen_boundary.v_left))
    assert float(linear[-1]) == pytest.approx(float(boundary.frozen_boundary.v_right))
