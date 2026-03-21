"""BCW2011 Case II extension: Dynamic hedging with margin requirements.

本文件基于 BCW (2011) 的 Dynamic Hedging 章节，展示在融资摩擦下，
投资、现金管理与衍生品对冲如何联立决定。

公式真源：同目录原文转录
`src/example/A_unified_theory_of_tobin's_q,_corporate_investment,_financing,_and_risk_management.md`

核心映射（公式编号 + 功能名称）：
- Eq.(27) frictionless hedge ratio -> `Policy.initialize` 中 `psi_frictionless`
- Eq.(30) interior hedge FOC solution -> `Policy.cal_policy` 中 `psi_interior`
- Eq.(29) margin-account allocation rule -> `Model.hjb_residual` 中 `kappa`
- Eq.(28) hedging HJB with covariance term -> `Model.hjb_residual`
- Eq.(26) cash dynamics with margin cost term -> `cash_flow_drift`

三分区（BCW Section IV.B）在代码中的实现：
- low-cash maximum-hedging region (w <= w_-): `psi=-pi` (via clipping)
- interior region (w_- < w < w_+): use Eq.(30)
- high-cash zero-hedging region (w >= w_+): `psi=0` (via cost-benefit test)
"""

from dataclasses import dataclass

import jax
import jax.numpy as jnp
import matplotlib.pyplot as plt
from jaxtyping import Array
from panel_print import pp

import finhjb as fjb


class Parameter(fjb.AbstractParameter):
    # --- Baseline (Table I) ---
    r: float = 0.06  # risk-free rate
    delta: float = 0.1007  # depreciation rate
    mu: float = 0.18  # risk-neutral mean productivity shock
    sigma: float = 0.09  # productivity volatility
    theta: float = 1.5  # adjustment-cost coefficient in g(i)=theta*i^2/2
    lambda_: float = 0.01  # proportional cash-carrying cost
    l: float = 0.9  # liquidation value ratio  # noqa: E741
    phi: float = 0.01  # fixed external financing cost
    gamma: float = 0.06  # proportional external financing cost

    # --- Hedging extension (Section IV, Table I) ---
    # rho (ρ): corr(productivity shock, market return)
    rho: float = 0.8
    # sigma_m (σ_m): volatility of market index futures
    sigma_m: float = 0.20
    # pi (π): margin multiplier, i.e. |psi| <= pi * kappa
    pi: float = 5.0
    # epsilon (ε): extra flow cost per unit of cash held in margin account
    epsilon: float = 0.005


class PolicyDict(fjb.AbstractPolicyDict):
    """Policy variables for the hedging case."""

    investment: Array
    psi: Array


@dataclass
class Boundary(fjb.AbstractBoundary[Parameter]):
    @staticmethod
    def compute_v_left(p: Parameter) -> float:
        # Left value boundary inherited from liquidation/refinancing setup.
        return p.l

    @staticmethod
    def compute_v_right(p: Parameter, s_max: float) -> float:
        # Right boundary value from the asymptotic payout-side closed form.
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
    def initialize(grid: fjb.Grid, p: Parameter) -> PolicyDict:
        # Eq.(7) / first-best investment in neoclassical benchmark.
        inv_first_best = (
            p.r
            + p.delta
            - ((p.r + p.delta) ** 2 - 2 * (p.mu - (p.r + p.delta)) / p.theta) ** 0.5
        )
        # Eq.(27) / frictionless hedge ratio (functionally mapped as initial guess):
        # psi*(w) = -(rho*sigma)/(w*sigma_m). Because our `psi` here is normalized by `s`,
        # we initialize with a constant benchmark -rho*sigma/sigma_m.
        psi_frictionless = -p.rho * p.sigma / p.sigma_m
        return PolicyDict(
            investment=jnp.full_like(grid.s, inv_first_best),
            psi=jnp.full_like(grid.s, psi_frictionless),
        )

    @staticmethod
    @fjb.explicit_policy(order=1)
    def cal_policy(grid: fjb.Grid) -> fjb.Grid:
        v = grid.v
        p = grid.p
        dv = grid.dv
        s = grid.s
        d2v = grid.d2v

        # Eq.(14) / investment rule under financing frictions.
        new_investment = (1 / p.theta) * (v / dv - s - 1)

        # Eq.(30) / interior hedge FOC solution:
        # psi*(w)=1/w * (-(rho*sigma)/sigma_m - (epsilon/pi)*(p'(w)/p''(w))/sigma_m^2)
        # 代码映射：s -> w, dv -> p'(w), d2v -> p''(w)。
        psi_interior = (
            1
            / s
            * (
                (-p.rho * p.sigma / p.sigma_m)
                - ((p.epsilon * dv) / (p.pi * d2v * p.sigma_m**2))
            )
        )

        # w_- (maximum-hedging boundary): in low-cash states the margin constraint binds,
        # hence psi is truncated at -pi.
        psi_clipped = jnp.maximum(psi_interior, -p.pi)

        # w_+ (zero-hedging boundary): when marginal hedging benefit is below marginal cost,
        # the firm sets psi=0.
        marginal_benefit = p.rho * p.sigma / p.sigma_m
        marginal_cost = jnp.abs((p.epsilon * dv) / (p.pi * d2v * p.sigma_m**2))
        should_hedge = marginal_cost < marginal_benefit

        # Three-region policy stitching:
        # - no hedge region -> 0
        # - interior region -> Eq.(30)
        # - low-cash constrained region -> -pi
        new_psi = jnp.where(should_hedge, psi_clipped, 0.0)
        grid.policy["investment"] = new_investment
        grid.policy["psi"] = new_psi
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
        inv = policy["investment"]
        psi = policy["psi"]

        # Eq.(29) / margin account allocation:
        # kappa = min{|psi|/pi, 1}
        kappa = jnp.minimum(jnp.abs(psi) / p.pi, 1.0)

        # Eq.(28), PK-channel: (i-delta)*(p-wp')
        drift_K = (inv - p.delta) * (v - s * dv)

        # Eq.(26) + Eq.(28), PW-channel:
        # cash drift includes margin flow cost term -epsilon*kappa*w.
        cash_flow_drift = (
            (p.r - p.lambda_) * s
            + p.mu
            - inv
            - 0.5 * p.theta * inv**2
            - p.epsilon * kappa * s
        )
        drift_W = cash_flow_drift * dv

        # Eq.(28), PWW-channel:
        # sigma^2 + psi^2*sigma_m^2*w^2 + 2*rho*sigma*sigma_m*psi*w
        total_variance = (
            p.sigma**2
            + (psi**2) * (p.sigma_m**2) * (s**2)
            + 2 * p.rho * p.sigma * p.sigma_m * psi * s
        )
        diffusion = 0.5 * total_variance * d2v

        discount = -p.r * v

        # Residual target: close to zero at convergence.
        return drift_K + drift_W + diffusion + discount

    @staticmethod
    def update_boundary(grid: fjb.Grid):
        # Eq.(20) smooth pasting for refinancing target m: p'(m)=1+gamma.
        i = jnp.argmin(jnp.abs(grid.dv - (1 + grid.p.gamma)))
        m = grid.s[i]
        v_m = grid.v[i]
        # Eq.(19) value matching at issuance boundary w=0:
        # p(0)=p(m)-phi-(1+gamma)m.
        new_v_left = v_m - grid.p.phi - (1 + grid.p.gamma) * m
        return {"v_left": new_v_left}, new_v_left - grid.boundary.v_left

    @staticmethod
    def boundary_condition():
        def s_max_condition(grid) -> float:
            # Eq.(17) super-contact at payout boundary.
            return grid.d2v[-1]

        def v_left_condition(grid):
            # Eq.(20) -> locate m through p'(m)=1+gamma.
            i = jax.numpy.argmin(jnp.abs(grid.dv - (1 + grid.p.gamma)))
            m = grid.s[i]
            v_m = grid.v[i]
            # Eq.(19) -> value-matching for left boundary.
            new_v_left = v_m - grid.p.phi - (1 + grid.p.gamma) * m
            return new_v_left - grid.v[0]

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
            sqrt_term_val = jnp.maximum(sqrt_term_val, 1e-12)
            pwr = p.theta * (
                (p.r + p.delta + (s_max_val + 1) / p.theta) - (sqrt_term_val) ** 0.5
            )
            return grid.boundary.v_right - pwr

        return [
            fjb.BoundaryConditionTarget(
                boundary_name="s_max",
                condition_func=s_max_condition,
                low=0.1,
                high=0.2,
            ),
            fjb.BoundaryConditionTarget(
                boundary_name="v_left",
                condition_func=v_left_condition,
                low=0.0,
                high=2.0,
            ),
            # BoundaryConditionTarget(
            #     boundary_name="v_right",
            #     condition_func=v_right_condition,
            # ),
        ]


if __name__ == "__main__":
    # Step 1) Set benchmark parameters for hedging case.
    parameter = Parameter()
    boundary = Boundary(
        p=parameter,
        s_min=0.0,
        s_max=0.13,
    )

    # Step 2) Build model + solver config.
    model = Model(policy=Policy())
    config = fjb.Config(
        derivative_method="central",
        # Policy Evaluation
        pe_max_iter=100,
        pe_tol=1e-10,
        pe_patience=100,
        # Policy Iteration
        pi_method="scan",
        policy_guess=True,
        pi_max_iter=100,
        pi_tol=1e-8,
        pi_patience=20,
        # Boundary Search
        bs_max_iter=100,
        bs_tol=1e-6,
        bs_patience=30,
    )

    solver = fjb.Solver(
        boundary=boundary,
        model=model,
        policy_guess=True,
        number=1000,
        config=config,
    )
    pp(solver._grid.boundary)

    # Step 3) Boundary search (bisection) to satisfy right-side contact condition.
    final_state = solver.boundary_search(method="bisection", verbose=True)

    # Step 4) Inspect solved policy/value objects.
    df = final_state.df
    grid = final_state.grid
    pp(final_state)
    pp(grid)
    pp(grid.d2v[-1])
    plt.plot(grid.s, grid.policy["psi"], label="before")
