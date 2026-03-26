"""Template: single-control FinHJB model with residual-based boundary search.

Use this template when the model has:
- one continuous state variable
- one control variable
- at least one endogenous boundary pinned down by a solved-grid condition
"""

from dataclasses import dataclass

import jax.numpy as jnp
from jaxtyping import Array

import finhjb as fjb


class Parameter(fjb.AbstractParameter):
    """Replace with calibrated parameters and any derived quantities."""

    discount_rate: float = 0.05
    volatility: float = 0.10


class PolicyDict(fjb.AbstractPolicyDict):
    control: Array


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
        return PolicyDict(control=jnp.zeros_like(grid.s))

    @staticmethod
    @fjb.explicit_policy(order=1)
    def update_control(grid: fjb.Grid) -> fjb.Grid:
        grid.policy["control"] = jnp.zeros_like(grid.s)
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
        control = policy["control"]
        drift_term = jnp.zeros_like(v)
        diffusion_term = 0.5 * p.volatility**2 * d2v
        discount_term = -p.discount_rate * v
        return drift_term + diffusion_term + discount_term

    @staticmethod
    def boundary_condition() -> list[fjb.BoundaryConditionTarget]:
        def target_condition(grid: fjb.Grid) -> float:
            # Replace with the model-specific smooth-pasting or super-contact condition.
            return float(grid.d2v[-1])

        return [
            fjb.BoundaryConditionTarget(
                boundary_name="s_max",
                condition_func=target_condition,
                low=0.1,
                high=1.0,
            )
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
        # Keep `central` only when the diffusion term is not edge-degenerate.
        config=fjb.Config(derivative_method="central", pi_method="scan"),
    )
    # For one-target problems with a credible bracket, start from `bisection`.
    # If the post-generation test loop fails badly, promote the final code to
    # `hybr` or another supported root solver and document that repair.
    state = solver.boundary_search(method="bisection", verbose=False)
    print(state.grid.boundary)
    print(state.grid.dv[-1], state.grid.d2v[-1])
