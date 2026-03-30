"""BCW2011 Case IV (Dynamic Hedging) for FinHJB.

This repository example reproduces the main Figure 6 comparison from
Bolton, Chen, and Wang (2011): costly margin requirements versus
frictionless hedging.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - script entrypoint bootstrap
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import jax.numpy as jnp
import numpy as np
from jaxtyping import Array

import finhjb as fjb
from src.example.bcw2011 import (
    BCWBaseParameter,
    add_boundary_markers,
    build_series,
    case_output_dir,
    common_summary,
    finalize_axes,
    hedging_boundaries_from_series,
    make_config,
    paper_figure,
    payout_right_value,
    publish_docs_figure,
    refinancing_boundary_residual,
    return_cash_ratio_from_grid,
    save_figure,
    super_contact_residual,
    write_summary_json,
    write_test_report,
)

DOCS_ASSET_NAME = "bcw2011-hedging-main.svg"
CASE_SLUG = "hedging"
DEFAULT_SEARCH_METHOD = "hybr"


class Parameter(BCWBaseParameter):
    """BCW hedging parameters."""


class PolicyDict(fjb.AbstractPolicyDict):
    """Policy and auxiliary arrays for the BCW hedging case."""

    investment: Array
    psi: Array
    psi_interior: Array


@dataclass
class Boundary(fjb.AbstractBoundary[Parameter]):
    """Boundary conditions for the BCW hedging case."""

    @staticmethod
    def compute_v_left(p: Parameter) -> float:
        return p.v_left_guess

    @staticmethod
    def compute_v_right(p: Parameter, s_max: float) -> float:
        return payout_right_value(p, s_max)


@dataclass
class Policy(fjb.AbstractPolicy[Parameter, PolicyDict]):
    """Explicit two-control policy update for BCW hedging."""

    @staticmethod
    def initialize(grid: fjb.Grid, p: Parameter) -> PolicyDict:
        psi_seed = -p.rho * p.sigma / p.sigma_m
        return PolicyDict(
            investment=jnp.full_like(grid.s, p.first_best_investment),
            psi=jnp.full_like(grid.s, psi_seed),
            psi_interior=jnp.full_like(grid.s, psi_seed),
        )

    @staticmethod
    @fjb.explicit_policy(order=1)
    def cal_policy(grid: fjb.Grid) -> fjb.Grid:
        p = grid.p
        v = grid.v
        dv = grid.dv
        d2v = grid.d2v
        s = grid.s
        safe_s = jnp.where(s > 1e-8, s, 1e-8)
        safe_d2v = jnp.where(jnp.abs(d2v) < 1e-10, -1e-10, d2v)

        investment = (1.0 / p.theta) * (v / dv - s - 1.0)
        psi_interior = (1.0 / safe_s) * (
            (-p.rho * p.sigma / p.sigma_m)
            - (p.epsilon / p.pi) * (dv / safe_d2v) / (p.sigma_m**2)
        )
        psi = jnp.where(psi_interior < 0.0, jnp.maximum(psi_interior, -p.pi), 0.0)

        grid.policy["investment"] = investment
        grid.policy["psi_interior"] = psi_interior
        grid.policy["psi"] = psi
        return grid


@dataclass
class Model(fjb.AbstractModel[Parameter, PolicyDict]):
    """BCW dynamic hedging model with margin requirements."""

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
        investment = policy["investment"]
        psi = policy["psi"]
        kappa = jnp.minimum(jnp.abs(psi) / p.pi, 1.0)
        capital_drift = (investment - p.delta) * (v - s * dv)
        cash_flow = (
            (p.r - p.lambda_) * s
            + p.mu
            - investment
            - 0.5 * p.theta * investment**2
            - p.epsilon * kappa * s
        )
        total_variance = (
            p.sigma**2
            + psi**2 * p.sigma_m**2 * s**2
            + 2.0 * p.rho * p.sigma * p.sigma_m * psi * s
        )
        return capital_drift - p.r * v + cash_flow * dv + 0.5 * total_variance * d2v

    @staticmethod
    def boundary_condition():
        def v_left_condition(grid):
            return refinancing_boundary_residual(grid)

        return [
            fjb.BoundaryConditionTarget(
                boundary_name="s_max",
                condition_func=super_contact_residual,
                low=0.10,
                high=0.20,
                tol=1e-6,
                max_iter=80,
            ),
            fjb.BoundaryConditionTarget(
                boundary_name="v_left",
                condition_func=v_left_condition,
                low=0.90,
                high=1.50,
                tol=1e-6,
                max_iter=80,
            ),
        ]


def build_solver(
    *,
    number: int = 1000,
    parameter_overrides: dict | None = None,
    s_max_guess: float = 0.1385,
) -> fjb.Solver:
    """Construct the costly-margin hedging solver."""
    parameter_kwargs = {"v_left_guess": 0.9}
    if parameter_overrides:
        parameter_kwargs.update(parameter_overrides)
    parameter = Parameter(**parameter_kwargs)
    boundary = Boundary(p=parameter, s_min=0.0, s_max=s_max_guess)
    model = Model(policy=Policy())
    config = make_config(pi_max_iter=140, pi_tol=1e-8)
    return fjb.Solver(
        boundary=boundary,
        model=model,
        policy_guess=True,
        number=number,
        config=config,
    )


def summarize_results(result: dict) -> dict:
    """Extract stable diagnostics from one hedging scenario."""
    grid = result["grid"]
    series = result["series"]
    summary = common_summary(grid, series)
    m, idx = return_cash_ratio_from_grid(grid)
    summary.update(
        {
            "return_cash_ratio": float(m),
            "dv_at_m": float(series["dv"][int(idx)]),
            "boundary_search_method": result["boundary_search_method"],
            "derivative_method": result["derivative_method"],
        }
    )
    if result["scenario"] == "costly-margin":
        w_minus, w_plus = hedging_boundaries_from_series(series, pi=grid.p.pi)
        summary.update(
            {
                "max_hedging_boundary": w_minus,
                "zero_hedging_boundary": w_plus,
                "psi_min": float(np.min(series["psi"])),
                "psi_max": float(np.max(series["psi"])),
                "v_left_above_liquidation": bool(grid.boundary.v_left > grid.p.l),
            }
        )
    else:
        summary.update(
            {
                "max_hedging_boundary": None,
                "zero_hedging_boundary": None,
                "psi_min": float(np.min(series["psi"])),
                "psi_max": float(np.max(series["psi"])),
                "effective_sigma": float(result["effective_sigma"]),
            }
        )
    return summary


def solve_case(*, with_margin: bool = True, number: int = 1000) -> dict:
    """Solve the costly-margin or frictionless hedging comparison case."""
    if with_margin:
        solver = build_solver(number=number)
        state = solver.boundary_search(method=DEFAULT_SEARCH_METHOD, verbose=False)
        grid = state.grid
        series = build_series(grid)
        result = {
            "state": state,
            "grid": grid,
            "series": series,
            "label": "Costly margin requirement",
            "style": {
                "color": "#1f1f1f",
                "linestyle": "-",
                "marker_linestyle": ":",
            },
            "scenario": "costly-margin",
            "boundary_search_method": DEFAULT_SEARCH_METHOD,
            "derivative_method": "central",
        }
    else:
        comparison_parameter = Parameter(
            epsilon=0.0,
            pi=1.0e4,
            v_left_guess=1.0,
        )
        solver = build_solver(
            number=number,
            parameter_overrides={
                "epsilon": 0.0,
                "pi": 1.0e4,
                "v_left_guess": 1.0,
            },
            s_max_guess=0.11,
        )
        state = solver.boundary_search(method=DEFAULT_SEARCH_METHOD, verbose=False)
        grid = state.grid
        raw_psi = np.asarray(grid.policy["psi"], dtype=float)
        series = build_series(
            grid,
            extra={
                "psi": np.clip(raw_psi, -10.0, 0.0),
                "psi_raw": raw_psi,
            },
        )
        result = {
            "state": state,
            "grid": grid,
            "series": series,
            "label": "No margin requirement",
            "style": {
                "color": "#8a4f3d",
                "linestyle": "--",
                "marker_linestyle": "-.",
            },
            "scenario": "frictionless",
            "boundary_search_method": DEFAULT_SEARCH_METHOD,
            "derivative_method": "central",
            "effective_sigma": comparison_parameter.sigma_without_systematic_risk,
        }
    result["summary"] = summarize_results(result)
    return result


def plot_main_figure(results: dict[str, dict], output_path: str | Path) -> Path:
    """Create the Figure 6-style main panel figure."""
    fig, axes = paper_figure()
    panels = [
        ("psi", "A. Hedge ratio: psi(w)"),
        ("investment", "B. Investment-capital ratio: i(w)"),
        ("v", "C. Firm value-capital ratio: p(w)"),
        ("dv", "D. Marginal value of cash: p'(w)"),
    ]
    marker_keys = {
        "psi": ["max_hedging_boundary", "zero_hedging_boundary", "payout_boundary"],
        "investment": ["payout_boundary"],
        "v": ["return_cash_ratio", "payout_boundary"],
        "dv": ["return_cash_ratio", "payout_boundary"],
    }
    for ax, (metric, title) in zip(axes.flat, panels, strict=True):
        for result in results.values():
            series = result["series"]
            ax.plot(
                series["s"],
                series[metric],
                color=result["style"]["color"],
                linestyle=result["style"]["linestyle"],
                linewidth=2.0,
                label=result["label"],
            )
            add_boundary_markers(ax, result, marker_keys[metric])
        finalize_axes(ax, title=title)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False)
    return save_figure(fig, output_path)


def run_case(
    *,
    output_dir: str | Path | None = None,
    number: int = 1000,
    publish_docs_assets: bool = False,
) -> dict:
    """Run the hedging comparison and materialize artifacts."""
    output_dir = case_output_dir(CASE_SLUG, output_dir=output_dir)
    results = {
        "costly-margin": solve_case(with_margin=True, number=number),
        "frictionless": solve_case(with_margin=False, number=number),
    }
    figure_svg = plot_main_figure(results, output_dir / "figure_6_hedging.svg")
    summary_payload = {label: result["summary"] for label, result in results.items()}
    summary_path = write_summary_json(output_dir, summary_payload)
    report_payload = {
        "case": "BCW2011 Case IV",
        "environment": {"status": "repo-backed", "smoke_test": 'uv run python -c "import finhjb"'},
        "numerical_methods": {
            "derivative_method": "central",
            "boundary_search_method": {
                label: result["boundary_search_method"] for label, result in results.items()
            },
        },
        "artifacts": {
            "figure_svg": str(figure_svg),
            "summary_json": str(summary_path),
        },
        "results": summary_payload,
    }
    test_report_path = write_test_report(output_dir, report_payload)
    published_assets = None
    if publish_docs_assets:
        published_assets = publish_docs_figure(figure_svg, DOCS_ASSET_NAME)
    return {
        "case": CASE_SLUG,
        "results": results,
        "artifact_paths": {
            "figure_svg": figure_svg,
            "summary": summary_path,
            "test_report": test_report_path,
        },
        "published_assets": published_assets,
    }


if __name__ == "__main__":
    bundle = run_case()
    printable = {
        "artifacts": {k: str(v) for k, v in bundle["artifact_paths"].items()},
        "summaries": {
            label: result["summary"] for label, result in bundle["results"].items()
        },
    }
    print(json.dumps(printable, indent=2, sort_keys=True))
