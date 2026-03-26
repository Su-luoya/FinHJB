"""Template: multi-control FinHJB model with residual-based boundary search.

Use this template when the model has:
- one continuous state variable
- multiple controls
- one or more endogenous boundaries solved through `boundary_search()`
"""

from dataclasses import dataclass

import jax.numpy as jnp
from jaxtyping import Array

import finhjb as fjb


class Parameter(fjb.AbstractParameter):
    discount_rate: float = 0.05
    volatility: float = 0.10


class PolicyDict(fjb.AbstractPolicyDict):
    control_a: Array
    control_b: Array


@dataclass
class Boundary(fjb.AbstractBoundary[Parameter]):
    @staticmethod
    def compute_v_left(p: Parameter) -> float:
        raise NotImplementedError

    @staticmethod
    def compute_v_right(p: Parameter, s_max: float) -> float:
        raise NotImplementedError


@dataclass
class Policy(fjb.AbstractPolicy):
    @staticmethod
    def initialize(grid: fjb.Grid, p: Parameter) -> PolicyDict:
        return PolicyDict(
            control_a=jnp.zeros_like(grid.s),
            control_b=jnp.zeros_like(grid.s),
        )

    @staticmethod
    @fjb.explicit_policy(order=1)
    def update_controls(grid: fjb.Grid) -> fjb.Grid:
        grid.policy["control_a"] = jnp.zeros_like(grid.s)
        grid.policy["control_b"] = jnp.zeros_like(grid.s)
        return grid


@dataclass
class Model(fjb.AbstractModel[Parameter, PolicyDict]):
    @staticmethod
    def hjb_residual(
        v: Array,
        dv: Array,
        d2v: Array,
        s: Array,
        policy: PolicyDict,
        jump: Array,
        boundary: fjb.ImmutableBoundary,
        p: Parameter,
    ) -> Array:
        control_a = policy["control_a"]
        control_b = policy["control_b"]
        drift_term = jnp.zeros_like(v)
        diffusion_term = 0.5 * p.volatility**2 * d2v
        discount_term = -p.discount_rate * v
        return drift_term + diffusion_term + discount_term

    @staticmethod
    def boundary_condition() -> list[fjb.BoundaryConditionTarget]:
        def right_target(grid: fjb.Grid) -> float:
            return float(grid.d2v[-1])

        def left_target(grid: fjb.Grid) -> float:
            return float(grid.v[0] - grid.boundary.v_left)

        return [
            fjb.BoundaryConditionTarget(
                boundary_name="s_max",
                condition_func=right_target,
                low=0.1,
                high=1.0,
            ),
            fjb.BoundaryConditionTarget(
                boundary_name="v_left",
                condition_func=left_target,
                low=0.0,
                high=2.0,
            ),
        ]


if __name__ == "__main__":
    parameter = Parameter()
    boundary = Boundary(
        p=parameter,
        s_min=0.0,
        s_max=0.5,
    )
    model = Model(policy=Policy())
    solver = fjb.Solver(
        boundary=boundary,
        model=model,
        number=500,
        policy_guess=True,
        config=fjb.Config(derivative_method="central", pi_method="scan"),
    )
    state = solver.boundary_search(method="hybr", verbose=False)
    print(state.grid.boundary)
    print(state.grid.dv[-1], state.grid.d2v[-1])
