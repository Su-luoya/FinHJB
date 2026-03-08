from dataclasses import dataclass

import jax
import jax.numpy as jnp
import matplotlib.pyplot as plt
from jaxtyping import Array
from panel_print import pp

import finhjb as fjb


class Parameter(fjb.AbstractParameter):
    r: float = 0.06  # Risk-free rate
    delta: float = 0.1007  # Rate of depreciation
    mu: float = 0.18  # Risk-neutral mean productivity shock
    sigma: float = 0.09  # Volatility of productivity shock
    theta: float = 1.5  # Adjustment cost parameter
    lambda_: float = 0.01  # Proportional cash-carrying cost
    l: float = 0.9  # Capital liquidation value  # noqa: E741
    phi: float = 0.01  # Fixed financing cost
    gamma: float = 0.06  # Proportional financing cost

    # rho (ρ): Correlation between the firm's productivity shock and the market return.
    rho: float = 0.8
    # sigma_m (σm): Volatility of the aggregate market portfolio (futures price).
    sigma_m: float = 0.20
    # pi (π): A constant multiple defining the margin requirement. The hedge position cannot exceed π times the cash in the margin account.
    pi: float = 5.0
    # epsilon (ε): The additional flow cost per unit of cash held in the margin account.
    epsilon: float = 0.005


class PolicyDict(fjb.AbstractPolicyDict):
    investment: Array
    psi: Array


@dataclass
class Boundary(fjb.AbstractBoundary[Parameter]):
    @staticmethod
    def compute_v_left(p: Parameter) -> float:
        return p.l

    @staticmethod
    def compute_v_right(p: Parameter, s_max: float) -> float:
        # Since the calculation of v_right depends on s_max, we ensure s_max is provided

        # This term corresponds to the discriminant of the quadratic equation for p(w_bar) derived from the HJB equation.
        # It gathers all the model parameters (r, delta, mu, theta, lambda) evaluated at the boundary s_max.
        sqrt_term_val = (p.r + p.delta + (s_max + 1) / p.theta) ** 2 - (2 / p.theta) * (
            p.mu
            + (p.r + p.delta - p.lambda_) * s_max
            + (s_max + 1) ** 2 / (2 * p.theta)
        )
        # Solves the quadratic equation for p(w_bar), which is denoted here as v_right.
        # The negative sign before the square root is chosen to select the economically relevant root for the firm value.
        v_right = p.theta * (
            (p.r + p.delta + (s_max + 1) / p.theta) - (sqrt_term_val) ** 0.5
        )
        return v_right


@dataclass
class Policy(fjb.AbstractPolicy):
    @staticmethod
    def initialize(grid: fjb.Grid, p: Parameter) -> PolicyDict:
        # The optimal investment rate in the frictionless case (without financing frictions), from Equation (7).
        inv_first_best = (
            p.r
            + p.delta
            - ((p.r + p.delta) ** 2 - 2 * (p.mu - (p.r + p.delta)) / p.theta) ** 0.5
        )
        # Initialize the hedge ratio with the optimal frictionless hedge ratio from Equation (27).
        # In the frictionless case (no margin costs/requirements), the optimal hedge is constant.
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
        new_investment = (1 / p.theta) * (v / dv - s - 1)

        # Calculate the optimal hedge ratio for the interior region, as defined in Equation (30).
        # This balances the risk-reduction benefits of hedging against the costs from margin requirements (ε).
        # 's' is the cash-capital ratio w, 'dv' is p'(w), and 'd2v' is p''(w).
        psi_interior = (
            1
            / s
            * (
                (-p.rho * p.sigma / p.sigma_m)
                - ((p.epsilon * dv) / (p.pi * d2v * p.sigma_m**2))
            )
        )

        # Apply the maximum-hedging boundary (w-). When cash is very low, the firm hedges at the maximum allowed level, ψ = -π.
        # This clips the hedge ratio at -π, ensuring it doesn't exceed the constraint.
        psi_clipped = jnp.maximum(psi_interior, -p.pi)

        # This logic determines the zero-hedging boundary (w+).
        # 'marginal_benefit' represents the absolute benefit of hedging from risk reduction (the frictionless component).
        marginal_benefit = p.rho * p.sigma / p.sigma_m
        # 'marginal_cost' represents the absolute marginal cost of hedging due to margin requirements.
        # Note: The variable naming might be counter-intuitive; this term captures the cost.
        marginal_cost = jnp.abs((p.epsilon * dv) / (p.pi * d2v * p.sigma_m**2))
        # The firm should hedge only if the benefit outweighs the cost.
        should_hedge = marginal_cost < marginal_benefit

        # Combine the three hedging regions:
        # 1. If 'should_hedge' is False (cost > benefit), set hedge ratio to 0 (zero-hedging region).
        # 2. If 'should_hedge' is True, use the clipped value, which covers both the interior solution and the maximum-hedging boundary.
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

        # Calculate kappa (κ), the fraction of cash held in the margin account, from Equation (29).
        # This is the minimum required to satisfy the margin constraint |ψ| ≤ πκ.
        kappa = jnp.minimum(jnp.abs(psi) / p.pi, 1.0)

        # Drift term from capital accumulation
        drift_K = (inv - p.delta) * (v - s * dv)

        # Drift term from cash evolution.
        # This includes the flow cost of holding cash in the margin account (-ε * κ * w), as seen in Equation (26).
        cash_flow_drift = (
            (p.r - p.lambda_) * s
            + p.mu
            - inv
            - 0.5 * p.theta * inv**2
            - p.epsilon * kappa * s
        )
        drift_W = cash_flow_drift * dv

        # The total variance term (diffusion) from the HJB Equation (28) after normalization.
        # It includes the firm's idiosyncratic variance (σ²), the variance from hedging (ψ²σm²w²),
        # and the covariance term.
        total_variance = (
            p.sigma**2
            + (psi**2) * (p.sigma_m**2) * (s**2)
            + 2 * p.rho * p.sigma * p.sigma_m * psi * s
        )
        diffusion = 0.5 * total_variance * d2v

        # Discounting term from the HJB equation
        discount = -p.r * v

        # The HJB residual combines all components.
        # A correct solution should have this residual close to zero.
        return drift_K + drift_W + diffusion + discount

    @staticmethod
    def update_boundary(grid: fjb.Grid):
        # Find the index where dv is closest to 1 + gamma
        i = jnp.argmin(jnp.abs(grid.dv - (1 + grid.p.gamma)))
        # Compute the corresponding m and v(m)
        m = grid.s[i]
        v_m = grid.v[i]
        # Update v_left using the smooth-pasting condition
        new_v_left = v_m - grid.p.phi - (1 + grid.p.gamma) * m
        return {"v_left": new_v_left}, new_v_left - grid.boundary.v_left

    @staticmethod
    def boundary_condition():
        def s_max_condition(grid) -> float:
            return grid.d2v[-1]

        def v_left_condition(grid):
            # Find the index where dv is closest to 1 + gamma
            i = jax.numpy.argmin(jnp.abs(grid.dv - (1 + grid.p.gamma)))
            # Compute the corresponding m and v(m)
            m = grid.s[i]
            v_m = grid.v[i]
            # Update v_left using the smooth-pasting condition
            new_v_left = v_m - grid.p.phi - (1 + grid.p.gamma) * m
            return new_v_left - grid.v[0]  # current left boundary value

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
    parameter = Parameter()
    boundary = Boundary(
        p=parameter,
        s_min=0.0,
        s_max=0.13,  # 0.22198886076863805
    )
    # pp(boundary)
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
    # final_state, history_of_errors = solver.solve()
    # pp(final_state)
    # final_state, history_of_errors = solver.boundary_update()

    final_state = solver.boundary_search(method="bisection", verbose=True)

    df = final_state.df
    grid = final_state.grid
    pp(final_state)
    pp(grid)
    # pp(history_of_errors)
    pp(grid.d2v[-1])
    plt.plot(grid.s, grid.policy["psi"], label="before")
    # plt.plot(grid.s, grid.d2v, label="before")
