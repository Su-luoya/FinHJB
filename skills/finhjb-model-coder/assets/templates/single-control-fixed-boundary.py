"""Template: single-control FinHJB model with fixed boundaries.

Use this template when the model has:
- one continuous state variable
- one control variable
- no endogenous boundary search or outer boundary update
"""

from dataclasses import dataclass

import jax.numpy as jnp
from jaxtyping import Array

import finhjb as fjb


class Parameter(fjb.AbstractParameter):
    """Replace with calibrated parameters and any derived quantities."""

    discount_rate: float = 0.05
    volatility: float = 0.10
    # Add model-specific parameters here.


class PolicyDict(fjb.AbstractPolicyDict):
    """Rename `control` to the economically meaningful control name."""

    control: Array


@dataclass
class Boundary(fjb.AbstractBoundary[Parameter]):
    @staticmethod
    def compute_v_left(p: Parameter) -> float:
        # Replace with the left value boundary formula.
        raise NotImplementedError

    @staticmethod
    def compute_v_right(p: Parameter, s_max: float) -> float:
        # Replace with the right value boundary formula.
        raise NotImplementedError


@dataclass
class Policy(fjb.AbstractPolicy):
    @staticmethod
    def initialize(grid: fjb.Grid, p: Parameter) -> PolicyDict:
        # Replace with a numerically meaningful initial policy guess.
        return PolicyDict(control=jnp.zeros_like(grid.s))

    @staticmethod
    @fjb.explicit_policy(order=1)
    def update_control(grid: fjb.Grid) -> fjb.Grid:
        # Replace with the model's explicit policy update.
        grid.policy["control"] = jnp.zeros_like(grid.s)
        return grid

    # If the control is defined by an FOC residual instead, replace the
    # explicit update above with an @fjb.implicit_policy method.


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

        # Split the residual into economically meaningful terms.
        drift_term = jnp.zeros_like(v)
        diffusion_term = 0.5 * p.volatility**2 * d2v
        discount_term = -p.discount_rate * v
        return drift_term + diffusion_term + discount_term


if __name__ == "__main__":
    parameter = Parameter()
    boundary = Boundary(
        p=parameter,
        s_min=0.0,
        s_max=1.0,
    )
    model = Model(policy=Policy())
    config = fjb.Config(
        derivative_method="central",
        pi_method="scan",
        pi_max_iter=50,
        pi_tol=1e-6,
    )
    solver = fjb.Solver(
        boundary=boundary,
        model=model,
        number=500,
        policy_guess=True,
        config=config,
    )
    state, history = solver.solve()
    print(type(state).__name__)
    print(history.shape)
    print(state.df.head())
