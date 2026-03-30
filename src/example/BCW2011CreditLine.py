"""BCW2011 Case V (Credit Line) for FinHJB.

This repository example reproduces the main Figure 7 comparison from
Bolton, Chen, and Wang (2011): no credit line versus a 20% credit line.
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
    credit_line_hjb_residual,
    finalize_axes,
    investment_rule_residual,
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

DEFAULT_SEARCH_METHOD = "hybr"
DOCS_ASSET_NAME = "bcw2011-credit-line-main.svg"
CASE_SLUG = "credit-line"


class Parameter(BCWBaseParameter):
    """BCW credit-line parameters."""


class PolicyDict(fjb.AbstractPolicyDict):
    """Policy map for the BCW credit-line case."""

    investment: Array


@dataclass
class Boundary(fjb.AbstractBoundary[Parameter]):
    """Boundary conditions for the BCW credit-line case."""

    @staticmethod
    def compute_s_min(p: Parameter) -> float:
        return -p.c

    @staticmethod
    def compute_v_left(p: Parameter) -> float:
        return p.v_left_guess

    @staticmethod
    def compute_v_right(p: Parameter, s_max: float) -> float:
        return payout_right_value(p, s_max)


@dataclass
class Policy(fjb.AbstractPolicy[Parameter, PolicyDict]):
    """Single-control investment policy for BCW credit lines."""

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
    """BCW credit-line model with a piecewise HJB residual."""

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
        return credit_line_hjb_residual(v, dv, d2v, s, policy["investment"], p)

    @staticmethod
    def boundary_condition():
        def v_left_condition(grid):
            return refinancing_boundary_residual(grid, extra_raise=grid.p.c)

        return [
            fjb.BoundaryConditionTarget(
                boundary_name="s_max",
                condition_func=super_contact_residual,
                low=0.05,
                high=0.20,
                tol=1e-6,
                max_iter=80,
            ),
            fjb.BoundaryConditionTarget(
                boundary_name="v_left",
                condition_func=v_left_condition,
                low=0.70,
                high=1.40,
                tol=1e-6,
                max_iter=80,
            ),
        ]


def build_solver(*, c: float = 0.2, number: int = 1000) -> fjb.Solver:
    """Construct the BCW credit-line solver."""
    parameter = Parameter(c=c, v_left_guess=0.86 if c > 0 else 0.9)
    boundary = Boundary(
        p=parameter,
        s_max=0.08 if c > 0 else 0.19,
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
    """Extract stable diagnostics from one credit-line scenario."""
    grid = result["grid"]
    series = result["series"]
    m, idx = return_cash_ratio_from_grid(grid)
    zero_idx = int(np.argmin(np.abs(series["s"])))
    summary = common_summary(grid, series)
    summary.update(
        {
            "credit_limit": float(grid.p.c),
            "credit_line_spread": float(grid.p.alpha),
            "return_cash_ratio": float(m),
            "equity_raise_amount": float(m + grid.p.c),
            "dv_at_m": float(series["dv"][int(idx)]),
            "dv_at_zero": float(series["dv"][zero_idx]),
            "investment_at_zero": float(series["investment"][zero_idx]),
            "investment_at_left_boundary": float(series["investment"][0]),
            "boundary_search_method": result["boundary_search_method"],
            "derivative_method": result["derivative_method"],
        }
    )
    return summary


def solve_case(*, c: float = 0.2, number: int = 1000) -> dict:
    """Solve one BCW credit-line scenario."""
    solver = build_solver(c=c, number=number)
    state = solver.boundary_search(method=DEFAULT_SEARCH_METHOD, verbose=False)
    grid = state.grid
    series = build_series(grid)
    result = {
        "state": state,
        "grid": grid,
        "series": series,
        "label": "Credit line c=20%" if c > 0 else "No credit line",
        "style": {
            "color": "#1f1f1f" if c > 0 else "#8a4f3d",
            "linestyle": "-" if c > 0 else "--",
            "marker_linestyle": ":" if c > 0 else "-.",
        },
        "derivative_method": "central",
        "boundary_search_method": DEFAULT_SEARCH_METHOD,
    }
    result["summary"] = summarize_results(result)
    return result


def plot_main_figure(results: dict[str, dict], output_path: str | Path) -> Path:
    """Create the Figure 7-style main panel figure."""
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
        ax.axvline(0.0, color="#7b7b7b", linestyle=":", linewidth=1.0, alpha=0.35)
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
    """Run the credit-line comparison and materialize artifacts."""
    output_dir = case_output_dir(CASE_SLUG, output_dir=output_dir)
    results = {
        "credit-line": solve_case(c=0.2, number=number),
        "no-credit-line": solve_case(c=0.0, number=number),
    }
    figure_svg = plot_main_figure(results, output_dir / "figure_7_credit_line.svg")
    summary_payload = {label: result["summary"] for label, result in results.items()}
    summary_path = write_summary_json(output_dir, summary_payload)
    report_payload = {
        "case": "BCW2011 Case V",
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
