from dataclasses import dataclass

import jax.numpy as jnp
import pytest

import finhjb as fjb


class Parameter(fjb.AbstractParameter):
    alpha: float = 1.0


class PolicyDict(fjb.AbstractPolicyDict):
    control: object


@dataclass
class Boundary(fjb.AbstractBoundary[Parameter]):
    @staticmethod
    def compute_v_left(p: Parameter) -> float:
        return 0.0

    @staticmethod
    def compute_v_right(p: Parameter, s_max: float) -> float:
        return float(s_max)


@dataclass
class FailingPolicy(fjb.AbstractPolicy[Parameter, PolicyDict]):
    @staticmethod
    def initialize(grid: fjb.Grid, p: Parameter) -> PolicyDict:
        return PolicyDict(control=jnp.ones_like(grid.s))

    def update(self, grid: fjb.Grid) -> fjb.Grid:
        raise RuntimeError("boom-from-policy-update")


@dataclass
class StablePolicy(fjb.AbstractPolicy[Parameter, PolicyDict]):
    @staticmethod
    def initialize(grid: fjb.Grid, p: Parameter) -> PolicyDict:
        return PolicyDict(control=jnp.ones_like(grid.s))

    @staticmethod
    @fjb.explicit_policy(order=1)
    def update_control(grid: fjb.Grid) -> fjb.Grid:
        grid.policy["control"] = jnp.ones_like(grid.s)
        return grid


@dataclass
class ModelWithoutBoundaryUpdate(fjb.AbstractModel[Parameter, PolicyDict]):
    @staticmethod
    def hjb_residual(
        v,
        dv,
        d2v,
        s,
        policy,
        jump,
        boundary,
        p,
    ):
        return dv - p.alpha


def test_policy_update_error_is_wrapped_as_keyerror() -> None:
    solver_kwargs = {
        "boundary": Boundary(p=Parameter(), s_min=0.0, s_max=1.0),
        "model": ModelWithoutBoundaryUpdate(policy=FailingPolicy()),
        "policy_guess": False,
        "number": 6,
    }
    with pytest.raises(KeyError, match="requires a initialized policy"):
        fjb.Solver(**solver_kwargs)


def test_boundary_update_requires_model_implementation() -> None:
    solver = fjb.Solver(
        boundary=Boundary(p=Parameter(), s_min=0.0, s_max=1.0),
        model=ModelWithoutBoundaryUpdate(policy=StablePolicy()),
        policy_guess=True,
        number=8,
    )
    with pytest.raises(
        NotImplementedError,
        match=r"requires the model class to implement `update_boundary\(grid\)`",
    ):
        solver.boundary_update()
