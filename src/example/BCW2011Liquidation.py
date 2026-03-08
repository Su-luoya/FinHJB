from dataclasses import dataclass

import jax.numpy as jnp
import matplotlib.pyplot as plt
from jaxtyping import Array
from panel_print import pp

import finhjb as fjb


class Parameter(fjb.AbstractParameter):
    r: float = 0.06
    delta: float = 0.1007
    mu: float = 0.18
    sigma: float = 0.09
    theta: float = 1.5
    lambda_: float = 0.01
    l: float = 0.9  # noqa: E741


class PolicyDict(fjb.AbstractPolicyDict):
    investment: Array


@dataclass
class Boundary(fjb.AbstractBoundary[Parameter]):
    @staticmethod
    def compute_v_left(p: Parameter) -> float:
        return p.l

    @staticmethod
    def compute_v_right(p: Parameter, s_max: float) -> float:
        sqrt_term_val = (p.r + p.delta + (s_max + 1) / p.theta) ** 2 - (2 / p.theta) * (
            p.mu
            + (p.r + p.delta - p.lambda_) * s_max
            + (s_max + 1) ** 2 / (2 * p.theta)
        )
        # if sqrt_term_val < 0:
        #     raise ValueError(
        #         "Invalid parameters or s_max guess: square root term is negative."
        #     )
        v_right = p.theta * (
            (p.r + p.delta + (s_max + 1) / p.theta) - (sqrt_term_val) ** 0.5
        )
        return v_right


@dataclass
class Policy(fjb.AbstractPolicy):
    @staticmethod
    def initialize(grid: fjb.Grid, p: Parameter):
        inv_first_best = (
            p.r
            + p.delta
            - ((p.r + p.delta) ** 2 - 2 * (p.mu - (p.r + p.delta)) / p.theta) ** 0.5
        )
        return PolicyDict(
            investment=jnp.full_like(grid.s, inv_first_best),
        )

    @staticmethod
    @fjb.implicit_policy(
        order=2,
        # solver="lm",
        solver="lm",
        policy_order=["investment"],
        implicit_diff=False,
    )
    def cal_investment_without_explicit(
        policy,
        v,
        dv,
        d2v,
        s,
        p,
    ):
        investment = policy[0]

        return jnp.array(
            [
                (1 / p.theta) * (v / dv - s - 1) - investment,
            ]
        )

    # @staticmethod
    # @fjb.explicit_policy(order=1)
    # def cal_investment(grid):
    #     p = grid.p
    #     v = grid.v
    #     dv = grid.dv
    #     s = grid.s
    #     investment = (1 / p.theta) * (v / dv - s - 1)
    #     grid.policy["investment"] = investment
    #     return grid


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
        inv = policy["investment"]
        term1 = (inv - p.delta) * (v - s * dv)
        term2 = -p.r * v
        term3 = ((p.r - p.lambda_) * s + p.mu - inv - 0.5 * p.theta * inv**2) * dv
        term4 = 0.5 * p.sigma**2 * d2v
        return term1 + term2 + term3 + term4

    @staticmethod
    def boundary_condition():
        def s_max_condition(grid) -> float:
            return grid.d2v[-1]

        def v_right_condition(grid) -> float:
            p = grid.p
            s_max_val = grid.boundary.s_max
            sqrt_term_val = (p.r + p.delta + (s_max_val + 1) / p.theta) ** 2 - (
                2 / p.theta
            ) * (
                p.mu
                + (p.r + p.delta - p.lambda_) * s_max_val
                + (s_max_val + 1) ** 2 / (2 * p.theta)
            )
            # Ensure the term under the square root is non-negative
            sqrt_term_val = jnp.maximum(sqrt_term_val, 1e-12)
            pwr = p.theta * (
                (p.r + p.delta + (s_max_val + 1) / p.theta) - (sqrt_term_val) ** 0.5
            )
            return grid.boundary.v_right - pwr

        return [
            # 这个目标既可以用于梯度法，也可以用于二分法
            fjb.BoundaryConditionTarget(
                boundary_name="s_max",
                condition_func=s_max_condition,
                # --- 为二分法提供以下参数 ---
                low=0.1,
                high=0.5,
                # tol=1e-7,
            ),
            # fjb.BoundaryConditionTarget(
            #     boundary_name="v_right",
            #     condition_func=v_right_condition,
            #     # --- 为二分法提供以下参数 ---
            #     # low=0.5,
            #     # high=2.0,
            #     # tol=1e-7,
            # ),
        ]


if __name__ == "__main__":
    # from jax import config
    # config.update("jax_debug_nans", True)

    parameter = Parameter()
    boundary = Boundary(
        p=parameter,
        s_min=0.0,
        s_max=0.2,  # 0.22198886076863805
    )
    pp(boundary)

    model = Model(policy=Policy())
    config = fjb.Config(
        derivative_method="central",
        # Policy Evaluation
        pe_max_iter=10,
        pe_tol=1e-7,
        pe_patience=100,
        # Policy Iteration
        pi_method="scan",
        policy_guess=True,
        pi_max_iter=100,
        pi_tol=1e-10,
        pi_patience=100,
        # Boundary Search
        bs_max_iter=20,
        bs_tol=1e-6,
        bs_patience=5,
    )
    solver = fjb.Solver(
        boundary=boundary,
        model=model,
        policy_guess=False,
        # search_value_boundary=True,
        number=1000,
        config=config,
    )
    pp(solver._grid)

    # final_state, history_of_errors = solver.solve()
    final_state = solver.boundary_search(method="bisection", verbose=True)
    pp(final_state)
    pp(final_state.grid.d2v[-1])
    df = final_state.df
    grid = final_state.grid
    pp(grid)

    # grid = final_state.grid
    plt.plot(df["s"], df["d2v"], label="$c(s) \\xi$")
