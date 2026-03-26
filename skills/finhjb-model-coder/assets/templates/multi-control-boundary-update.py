"""Template: multi-control FinHJB model with direct boundary updates.

Use this template when the model has:
- one continuous state variable
- multiple controls
- an outer update rule that reads the solved grid and returns new boundaries
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
    def update_boundary(grid: fjb.Grid):
        # Replace with the rule that reads the solved grid and updates boundaries.
        new_v_left = float(grid.v[0])
        return {"v_left": new_v_left}, new_v_left - grid.boundary.v_left


if __name__ == "__main__":
    parameter = Parameter()
    boundary = Boundary(
        p=parameter,
        s_min=0.0,
        s_max=1.0,
    )
    model = Model(policy=Policy())
    solver = fjb.Solver(
        boundary=boundary,
        model=model,
        number=500,
        policy_guess=True,
        config=fjb.Config(derivative_method="central", pi_method="scan"),
    )
    state, history = solver.boundary_update()
    print(type(state).__name__)
    print(history.shape)
    print(state.grid.boundary)
