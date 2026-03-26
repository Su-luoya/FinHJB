"""BCW Case II: Refinancing evaluation fixture for `finhjb-model-coder`.

This file is intentionally stored inside the skill-local test bundle. It is the
artifact used to evaluate whether the skill can translate the BCW paper's
refinancing case into executable one-dimensional FinHJB code after a small
amount of paper-grounded interaction.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import jax.numpy as jnp
import matplotlib.pyplot as plt
import numpy as np
from jaxtyping import Array

import finhjb as fjb

ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = ROOT / "artifacts"
DEFAULT_DERIVATIVE_METHOD = "central"
DEFAULT_SEARCH_METHOD = "hybr"
BISSECTION_OVERRIDE_NOTE = (
    "Two endogenous boundary targets would normally start from bisection, "
    "but the post-generation test loop promoted the final fixture to `hybr` "
    "because the phi=0 comparison under-shot the Figure 3 payout boundary "
    "under the default search choice."
)


class Parameter(fjb.AbstractParameter):
    """BCW baseline parameters for the refinancing case."""

    r: float = 0.06
    delta: float = 0.1007
    mu: float = 0.18
    sigma: float = 0.09
    theta: float = 1.5
    lambda_: float = 0.01
    l: float = 0.9  # noqa: E741
    phi: float = 0.01
    gamma: float = 0.06


class PolicyDict(fjb.AbstractPolicyDict):
    """Single-control policy map for BCW refinancing."""

    investment: Array


@dataclass
class Boundary(fjb.AbstractBoundary[Parameter]):
    @staticmethod
    def compute_v_left(p: Parameter) -> float:
        # Start from the liquidation value and let boundary search move it upward
        # when refinancing is preferred to liquidation.
        return p.l

    @staticmethod
    def compute_v_right(p: Parameter, s_max: float) -> float:
        # BCW payout-side closed form reused from the liquidation benchmark.
        sqrt_term_val = (p.r + p.delta + (s_max + 1) / p.theta) ** 2 - (2 / p.theta) * (
            p.mu
            + (p.r + p.delta - p.lambda_) * s_max
            + (s_max + 1) ** 2 / (2 * p.theta)
        )
        sqrt_term_val = jnp.maximum(sqrt_term_val, 1e-12)
        return p.theta * (
            (p.r + p.delta + (s_max + 1) / p.theta) - sqrt_term_val**0.5
        )


@dataclass
class Policy(fjb.AbstractPolicy):
    @staticmethod
    def initialize(grid: fjb.Grid, p: Parameter) -> PolicyDict:
        inv_first_best = (
            p.r
            + p.delta
            - ((p.r + p.delta) ** 2 - 2 * (p.mu - (p.r + p.delta)) / p.theta) ** 0.5
        )
        return PolicyDict(investment=jnp.full_like(grid.s, inv_first_best))

    @staticmethod
    @fjb.implicit_policy(
        order=1,
        solver="lm",
        policy_order=["investment"],
        implicit_diff=False,
    )
    def cal_investment_without_explicit(policy, v, dv, d2v, s, p):
        investment = policy[0]
        return jnp.array([(1 / p.theta) * (v / dv - s - 1) - investment])


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
        capital_drift = (inv - p.delta) * (v - s * dv)
        discount = -p.r * v
        cash_drift = ((p.r - p.lambda_) * s + p.mu - inv - 0.5 * p.theta * inv**2) * dv
        diffusion = 0.5 * p.sigma**2 * d2v
        return capital_drift + discount + cash_drift + diffusion

    @staticmethod
    def boundary_condition():
        def payout_condition(grid: fjb.Grid) -> float:
            # BCW Eq. (17): p''(w_bar) = 0
            return grid.d2v[-1]

        def refinancing_value_match(grid: fjb.Grid):
            # BCW Eq. (20): locate the return cash-capital ratio m by p'(m)=1+gamma.
            idx = jnp.argmin(jnp.abs(grid.dv - (1 + grid.p.gamma)))
            m = grid.s[idx]
            v_m = grid.v[idx]
            # BCW Eq. (19): p(0)=p(m)-phi-(1+gamma)m.
            new_v_left = v_m - grid.p.phi - (1 + grid.p.gamma) * m
            return new_v_left - grid.v[0]

        return [
            fjb.BoundaryConditionTarget(
                boundary_name="s_max",
                condition_func=payout_condition,
                low=0.10,
                high=0.26,
                tol=1e-6,
                max_iter=80,
            ),
            fjb.BoundaryConditionTarget(
                boundary_name="v_left",
                condition_func=refinancing_value_match,
                low=0.90,
                high=1.50,
                tol=1e-6,
                max_iter=80,
            ),
        ]


def build_solver(phi: float, number: int = 1000) -> fjb.Solver:
    """Construct a solver for the BCW refinancing comparison case."""
    parameter = Parameter(phi=phi)
    boundary = Boundary(
        p=parameter,
        s_min=0.0,
        s_max=0.19 if phi > 0 else 0.14,
    )
    model = Model(policy=Policy())
    config = fjb.Config(
        # BCW Eq. (13) keeps the diffusion term at 0.5 * sigma^2 * p''(w), with
        # sigma > 0 throughout the state interval, so `central` is the stable
        # first choice for this refinancing fixture.
        derivative_method=DEFAULT_DERIVATIVE_METHOD,
        pe_max_iter=20,
        pe_tol=1e-8,
        pe_patience=100,
        pi_method="scan",
        policy_guess=True,
        pi_max_iter=120,
        pi_tol=1e-10,
        pi_patience=60,
        bs_max_iter=120,
        bs_tol=1e-6,
        bs_patience=40,
    )
    return fjb.Solver(
        boundary=boundary,
        model=model,
        policy_guess=True,
        number=number,
        config=config,
    )


def solve_case(phi: float, number: int = 1000) -> dict:
    """Solve one refinancing case and return the raw objects needed for tests."""
    solver = build_solver(phi=phi, number=number)
    # The two-target default would start from `bisection`, but the archived
    # forward test for this fixture promoted the final implementation to `hybr`
    # so both Figure 3 comparison cases remain stable under one shared script.
    state = solver.boundary_search(method=DEFAULT_SEARCH_METHOD, verbose=False)
    grid = state.grid
    summary = summarize_results(
        {
            "state": state,
            "grid": grid,
            "phi": phi,
            "derivative_method": DEFAULT_DERIVATIVE_METHOD,
            "boundary_search_method": DEFAULT_SEARCH_METHOD,
        }
    )
    return {
        "phi": phi,
        "state": state,
        "grid": grid,
        "summary": summary,
    }


def summarize_results(result: dict) -> dict:
    """Extract stable economic diagnostics from one solved refinancing case."""
    grid = result["grid"]
    phi = float(result["phi"])
    derivative_method = result["derivative_method"]
    boundary_search_method = result["boundary_search_method"]
    s = np.asarray(grid.s)
    v = np.asarray(grid.v)
    dv = np.asarray(grid.dv)
    investment = np.asarray(grid.policy["investment"])
    investment_sensitivity = np.gradient(investment, s)

    m_idx = int(np.argmin(np.abs(dv - (1 + grid.p.gamma))))
    m = float(s[m_idx])

    summary = {
        "phi": phi,
        "payout_boundary": float(grid.boundary.s_max),
        "left_value": float(grid.boundary.v_left),
        "right_value": float(grid.boundary.v_right),
        "liquidation_value": float(grid.p.l),
        "p0_above_l": bool(v[0] > float(grid.p.l)),
        "return_cash_ratio": m,
        "dv_at_m": float(dv[m_idx]),
        "investment_at_payout": float(investment[-1]),
        "marginal_value_at_zero": float(dv[0]),
        "derivative_method": derivative_method,
        "boundary_search_method": boundary_search_method,
        "is_value_increasing": bool(np.all(np.diff(v) >= -1e-6)),
        "is_dv_decreasing": bool(np.all(np.diff(dv[: max(m_idx + 1, 2)]) <= 5e-3)),
        "is_investment_increasing": bool(np.all(np.diff(investment) >= -5e-3)),
        "max_investment_sensitivity": float(np.max(investment_sensitivity)),
    }
    return summary


def plot_figure_3_style(results: dict[str, dict], output_dir: Path) -> Path:
    """Create a Figure 3-style refinancing comparison plot."""
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    metric_map = [
        ("v", "Firm value-capital ratio: p(w)"),
        ("dv", "Marginal value of cash: p'(w)"),
        ("investment", "Investment-capital ratio: i(w)"),
        ("investment_sensitivity", "Investment-cash sensitivity: i'(w)"),
    ]

    for index, (label, result) in enumerate(results.items()):
        grid = result["grid"]
        summary = result["summary"]
        s = np.asarray(grid.s)
        values = {
            "v": np.asarray(grid.v),
            "dv": np.asarray(grid.dv),
            "investment": np.asarray(grid.policy["investment"]),
            "investment_sensitivity": np.gradient(np.asarray(grid.policy["investment"]), s),
        }
        style = "-" if index == 0 else "--"
        legend_label = f"{label} (phi={result['phi']:.2%})"

        for ax, (metric, title) in zip(axes.flat, metric_map, strict=True):
            ax.plot(s, values[metric], style, linewidth=2, label=legend_label)
            ax.set_title(title)
            ax.set_xlabel("w")
            ax.axvline(summary["return_cash_ratio"], color="gray", linestyle=":", alpha=0.7)
            ax.axvline(summary["payout_boundary"], color="black", linestyle="-.", alpha=0.5)

    for ax in axes.flat:
        ax.legend()

    figure_path = output_dir / "figure_3_refinancing.png"
    fig.savefig(figure_path, dpi=200)
    plt.close(fig)
    return figure_path


def write_summary(results: dict[str, dict], output_dir: Path) -> Path:
    """Write the case summaries as JSON for manual inspection."""
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {label: result["summary"] for label, result in results.items()}
    output_path = output_dir / "summary.json"
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return output_path


def write_test_report(results: dict[str, dict], output_dir: Path, figure_path: Path, summary_path: Path) -> Path:
    """Record the executed test loop and the repair that shaped the fixture."""
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "environment": {
            "status": "ready",
            "type": "repo-backed",
            "smoke_test": 'uv run python -c "import finhjb"',
        },
        "numerical_methods": {
            "derivative_method": DEFAULT_DERIVATIVE_METHOD,
            "derivative_reason": (
                "The diffusion term stays at 0.5 * sigma^2 * p''(w) with "
                "sigma > 0, so this fixture keeps `central`."
            ),
            "target_count": 2,
            "target_default": "bisection",
            "final_boundary_search_method": DEFAULT_SEARCH_METHOD,
            "repair_note": BISSECTION_OVERRIDE_NOTE,
        },
        "executed_checks": [
            "fixture imports",
            "solver constructs for phi=0.01",
            "solver constructs for phi=0.0",
            "boundary-search solve for phi=0.01",
            "boundary-search solve for phi=0.0",
            "Figure 3-style plot written",
            "summary JSON written",
        ],
        "artifacts": {
            "figure": str(figure_path),
            "summary": str(summary_path),
        },
        "residual_risks": [
            "The fixture is calibrated for the BCW Figure 3 comparison rather than general-purpose comparative statics.",
            "The archived repair note should be revisited if future solver changes make two-target bisection robust for both phi cases.",
        ],
    }
    output_path = output_dir / "test_report.json"
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return output_path


def run_fixture(output_dir: Path | None = None, number: int = 1000) -> dict[str, dict]:
    """Run the full Figure 3 comparison and materialize the runtime artifacts."""
    output_dir = ARTIFACTS_DIR if output_dir is None else Path(output_dir)
    results = {
        "fixed-cost": solve_case(phi=0.01, number=number),
        "no-fixed-cost": solve_case(phi=0.0, number=number),
    }
    figure_path = plot_figure_3_style(results, output_dir=output_dir)
    summary_path = write_summary(results, output_dir=output_dir)
    test_report_path = write_test_report(
        results,
        output_dir=output_dir,
        figure_path=figure_path,
        summary_path=summary_path,
    )
    results["artifact_paths"] = {
        "figure": figure_path,
        "summary": summary_path,
        "test_report": test_report_path,
    }
    return results


if __name__ == "__main__":
    run_results = run_fixture()
    print("Generated artifacts:")
    print(run_results["artifact_paths"]["figure"])
    print(run_results["artifact_paths"]["summary"])
    print(run_results["artifact_paths"]["test_report"])
    for label in ("fixed-cost", "no-fixed-cost"):
        print(label, run_results[label]["summary"])
