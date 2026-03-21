"""BCW2011 Case I (Liquidation) for FinHJB.

本文件复现论文：
Bolton, Chen, Wang (2011), *A Unified Theory of Tobin's q, Corporate
Investment, Financing, and Risk Management*。

为避免公式版本差异，本文档中的公式编号与术语均以同目录原文转录文件为准：
`src/example/A_unified_theory_of_tobin's_q,_corporate_investment,_financing,_and_risk_management.md`。

核心映射（公式编号 + 功能名称）：
- Eq.(7)  first-best investment rule -> `Policy.initialize`
- Eq.(13) HJB ODE in internal-financing region -> `Model.hjb_residual`
- Eq.(14) investment-capital ratio rule -> `Policy.cal_investment_without_explicit`
- Eq.(18) liquidation boundary p(0)=l -> `Boundary.compute_v_left`
- Eq.(16)(17) payout/super-contact conditions -> `boundary_condition` 中 d2v[-1]≈0

状态变量说明：
- 代码中的 `s` 对应论文 `w=W/K`（cash-capital ratio）。
- 代码中的 `v, dv, d2v` 分别对应 `p(w), p'(w), p''(w)`。
"""

from dataclasses import dataclass

import jax.numpy as jnp
import matplotlib.pyplot as plt
from jaxtyping import Array
from panel_print import pp

import finhjb as fjb


class Parameter(fjb.AbstractParameter):
    # --- Baseline parameters in BCW Table I ---
    # r: risk-free rate
    r: float = 0.06
    # delta: depreciation rate of capital
    delta: float = 0.1007
    # mu: risk-neutral mean productivity shock
    mu: float = 0.18
    # sigma: volatility of productivity shock
    sigma: float = 0.09
    # theta: quadratic adjustment-cost coefficient in g(i)=theta*i^2/2
    theta: float = 1.5
    # lambda: proportional cash-carrying cost
    lambda_: float = 0.01
    # l: liquidation value ratio, i.e. p(0)=l in Eq.(18)
    l: float = 0.9  # noqa: E741


class PolicyDict(fjb.AbstractPolicyDict):
    """Policy variables for the liquidation case."""

    investment: Array


@dataclass
class Boundary(fjb.AbstractBoundary[Parameter]):
    @staticmethod
    def compute_v_left(p: Parameter) -> float:
        # Eq.(18): liquidation region value matching, p(0)=l
        return p.l

    @staticmethod
    def compute_v_right(p: Parameter, s_max: float) -> float:
        # Right boundary uses the closed-form root for p(w_bar) under the
        # asymptotic payout-side condition (see BCW Section II and figures).
        sqrt_term_val = (p.r + p.delta + (s_max + 1) / p.theta) ** 2 - (2 / p.theta) * (
            p.mu
            + (p.r + p.delta - p.lambda_) * s_max
            + (s_max + 1) ** 2 / (2 * p.theta)
        )
        v_right = p.theta * (
            (p.r + p.delta + (s_max + 1) / p.theta) - (sqrt_term_val) ** 0.5
        )
        return v_right


@dataclass
class Policy(fjb.AbstractPolicy):
    @staticmethod
    def initialize(grid: fjb.Grid, p: Parameter):
        # Eq.(7) / first-best investment rule:
        # i_FB = r+delta - sqrt((r+delta)^2 - 2*(mu-(r+delta))/theta)
        # 该值作为策略迭代初值，可提高收敛稳定性。
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

        # Eq.(14) / investment-capital ratio rule:
        # i(w) = (1/theta) * (p(w)/p'(w) - w - 1)
        # 这里写成隐式残差形式 [i*(w) - investment = 0] 交给 LM 求解器。
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

        # Eq.(13) / HJB ODE for p(w):
        # r p(w) = (i-delta)*(p-wp') + ((r-lambda)w + mu - i - g(i))*p' + 0.5*sigma^2*p''
        # 将右侧减去 r p(w) 后得到残差，目标是 residual -> 0。
        capital_drift = (inv - p.delta) * (v - s * dv)
        discount = -p.r * v
        cash_drift = ((p.r - p.lambda_) * s + p.mu - inv - 0.5 * p.theta * inv**2) * dv
        diffusion = 0.5 * p.sigma**2 * d2v
        return capital_drift + discount + cash_drift + diffusion

    @staticmethod
    def boundary_condition():
        def s_max_condition(grid) -> float:
            # Eq.(17) / super-contact condition at payout boundary:
            # p''(w_bar)=0. Numerically we enforce d2v[-1]≈0 on right boundary.
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
            # 该目标可用于 bisection / gradient-like methods.
            fjb.BoundaryConditionTarget(
                boundary_name="s_max",
                condition_func=s_max_condition,
                # 为 bisection 提供 bracket 区间。
                low=0.1,
                high=0.5,
            ),
            # fjb.BoundaryConditionTarget(
            #     boundary_name="v_right",
            #     condition_func=v_right_condition,
            #     # low=0.5,
            #     # high=2.0,
            #     # tol=1e-7,
            # ),
        ]


if __name__ == "__main__":
    # Step 1) Parameter / boundary setup for Case I (liquidation).
    parameter = Parameter()
    boundary = Boundary(
        p=parameter,
        s_min=0.0,
        s_max=0.2,
    )
    pp(boundary)

    # Step 2) Build model and solver configuration.
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

    # Step 3) Search s_max that satisfies Eq.(17) numerically.
    final_state = solver.boundary_search(method="bisection", verbose=True)
    pp(final_state)
    pp(final_state.grid.d2v[-1])

    # Step 4) Inspect solved objects.
    df = final_state.df
    grid = final_state.grid
    pp(grid)

    # A quick diagnostic plot: right-tail curvature should approach zero.
    plt.plot(df["s"], df["d2v"], label="$c(s) \\xi$")
