"""BCW2011 Case II (Optimal Refinancing) for FinHJB.

This repository example reproduces the main Figure 3 comparison from
Bolton, Chen, and Wang (2011) using one-dimensional FinHJB code.
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
    investment_rule_residual,
    make_config,
    paper_figure,
    payout_right_value,
    publish_docs_figure,
    refinancing_boundary_residual,
    return_cash_ratio_from_grid,
    save_figure,
    standard_hjb_residual,
    super_contact_residual,
    write_summary_json,
    write_test_report,
)

DEFAULT_SEARCH_METHOD = "hybr"
DOCS_ASSET_NAME = "bcw2011-refinancing-main.svg"
CASE_SLUG = "refinancing"


class Parameter(BCWBaseParameter):
    """BCW refinancing parameters."""


class PolicyDict(fjb.AbstractPolicyDict):
    """Policy map for the BCW refinancing case."""

    investment: Array


@dataclass
class Boundary(fjb.AbstractBoundary[Parameter]):
    """Boundary conditions for the BCW refinancing case."""

    @staticmethod
    def compute_v_left(p: Parameter) -> float:
        return p.v_left_guess

    @staticmethod
    def compute_v_right(p: Parameter, s_max: float) -> float:
        return payout_right_value(p, s_max)


@dataclass
class Policy(fjb.AbstractPolicy[Parameter, PolicyDict]):
    """Single-control investment policy for BCW refinancing."""

    @staticmethod
    def initialize(grid: fjb.Grid, p: Parameter) -> PolicyDict:
        return PolicyDict(investment=jnp.full_like(grid.s, p.first_best_investment))

    @staticmethod
    @fjb.implicit_policy(
        order=1,
        solver="lm",
        policy_order=["investment"],
        implicit_diff=False,
        tol=1e-9,
        maxiter=20,
    )
    def cal_investment(policy, v, dv, d2v, s, p):
        investment = policy[0]
        return jnp.array([investment_rule_residual(v, dv, s, investment, p)])


@dataclass
class Model(fjb.AbstractModel[Parameter, PolicyDict]):
    """BCW refinancing model solved on the cash-capital ratio grid."""

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
        return standard_hjb_residual(v, dv, d2v, s, policy["investment"], p)

    @staticmethod
    def boundary_condition():
        def v_left_condition(grid):
            return refinancing_boundary_residual(grid)

        return [
            fjb.BoundaryConditionTarget(
                boundary_name="s_max",
                condition_func=super_contact_residual,
                low=0.10,
                high=0.26,
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
    phi: float = 0.01,
    number: int = 1000,
    sigma: float | None = None,
) -> fjb.Solver:
    """Construct a solver for one BCW refinancing scenario."""
    parameter_kwargs = {
        "phi": phi,
        "v_left_guess": 0.9 if phi > 0 else 1.05,
    }
    if sigma is not None:
        parameter_kwargs["sigma"] = sigma
    parameter = Parameter(**parameter_kwargs)
    boundary = Boundary(
        p=parameter,
        s_min=0.0,
        s_max=0.19 if phi > 0 else 0.14,
    )
    model = Model(policy=Policy())
    config = make_config()
    return fjb.Solver(
        boundary=boundary,
        model=model,
        policy_guess=True,
        number=number,
        config=config,
    )


def summarize_results(result: dict) -> dict:
    """Extract stable diagnostics from one solved refinancing scenario."""
    grid = result["grid"]
    series = result["series"]
    m, idx = return_cash_ratio_from_grid(grid)
    summary = common_summary(grid, series)
    summary.update(
        {
            "phi": float(grid.p.phi),
            "liquidation_value": float(grid.p.l),
            "p0_above_l": bool(series["v"][0] > float(grid.p.l)),
            "return_cash_ratio": float(m),
            "dv_at_m": float(series["dv"][int(idx)]),
            "max_investment_sensitivity": float(np.max(series["investment_sensitivity"])),
            "boundary_search_method": result["boundary_search_method"],
            "derivative_method": result["derivative_method"],
        }
    )
    return summary


def solve_case(
    *,
    phi: float = 0.01,
    number: int = 1000,
    sigma: float | None = None,
) -> dict:
    """Solve one BCW refinancing scenario."""
    solver = build_solver(phi=phi, number=number, sigma=sigma)
    state = solver.boundary_search(method=DEFAULT_SEARCH_METHOD, verbose=False)
    grid = state.grid
    series = build_series(grid)
    result = {
        "state": state,
        "grid": grid,
        "series": series,
        "label": "Fixed financing cost" if phi > 0 else "No fixed financing cost",
        "style": {
            "color": "#1f1f1f" if phi > 0 else "#8a4f3d",
            "linestyle": "-" if phi > 0 else "--",
            "marker_linestyle": ":" if phi > 0 else "-.",
        },
        "derivative_method": "central",
        "boundary_search_method": DEFAULT_SEARCH_METHOD,
    }
    result["summary"] = summarize_results(result)
    return result


def plot_main_figure(results: dict[str, dict], output_path: str | Path) -> Path:
    """Create the Figure 3-style main panel figure."""
    fig, axes = paper_figure()
    panels = [
        ("v", "A. Firm value-capital ratio: p(w)"),
        ("dv", "B. Marginal value of cash: p'(w)"),
        ("investment", "C. Investment-capital ratio: i(w)"),
        ("investment_sensitivity", "D. Investment-cash sensitivity: i'(w)"),
    ]
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
            add_boundary_markers(ax, result, ["return_cash_ratio", "payout_boundary"])
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
    """Run the full BCW refinancing comparison and write artifacts."""
    output_dir = case_output_dir(CASE_SLUG, output_dir=output_dir)
    results = {
        "fixed-cost": solve_case(phi=0.01, number=number),
        "no-fixed-cost": solve_case(phi=0.0, number=number),
    }
    figure_svg = plot_main_figure(results, output_dir / "figure_3_refinancing.svg")
    summary_payload = {label: result["summary"] for label, result in results.items()}
    summary_path = write_summary_json(output_dir, summary_payload)
    report_payload = {
        "case": "BCW2011 Case II",
        "environment": {"status": "repo-backed", "smoke_test": 'uv run python -c "import finhjb"'},
        "numerical_methods": {
            "derivative_method": "central",
            "boundary_search_method": DEFAULT_SEARCH_METHOD,
            "boundary_target_count": 2,
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
