"""Parameter-search rescue task for BCW2011 Case II refinancing."""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - task module bootstrap
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import finhjb as fjb
import matplotlib.pyplot as plt
import numpy as np

from src.example import BCW2011Refinancing as refinancing
from src.example.bcw2011 import build_series, common_summary, finalize_axes, paper_figure, save_figure


PARAMETER_SEARCH_SPEC = {
    "task_name": "bcw2011-refinancing-parameter-search",
    "mode": "rescue",
    "fixed_parameters": {
        "sigma": 0.09,
    },
    "search_parameters": [
        {
            "name": "phi",
            "low": 0.004,
            "high": 0.016,
            "scale": "linear",
            "fixed": False,
            "initial_center": 0.010,
        },
    ],
    "hard_constraints": [
        {
            "name": "converged",
            "metric": "converged",
            "operator": "==",
            "target_or_interval": True,
            "tolerance": 0.0,
        },
        {
            "name": "boundary_error_small",
            "metric": "boundary_error",
            "operator": "<=",
            "target_or_interval": 1e-4,
            "tolerance": 0.0,
        },
        {
            "name": "value_monotone",
            "metric": "is_value_increasing",
            "operator": "==",
            "target_or_interval": True,
            "tolerance": 0.0,
        },
        {
            "name": "dv_monotone",
            "metric": "is_dv_decreasing",
            "operator": "==",
            "target_or_interval": True,
            "tolerance": 0.0,
        },
        {
            "name": "payout_boundary_reasonable",
            "metric": "payout_boundary",
            "operator": "between",
            "target_or_interval": [0.16, 0.22],
            "tolerance": 0.0,
        },
    ],
    "soft_preferences": [
        {
            "name": "payout_close_to_benchmark",
            "metric": "payout_boundary",
            "target": 0.19,
            "weight": 0.45,
            "scoring_rule": "distance",
            "scale": 0.03,
        },
        {
            "name": "return_cash_close_to_benchmark",
            "metric": "return_cash_ratio",
            "target": 0.06,
            "weight": 0.35,
            "scoring_rule": "distance",
            "scale": 0.03,
        },
        {
            "name": "investment_close_to_benchmark",
            "metric": "investment_at_payout",
            "target": 0.11,
            "weight": 0.20,
            "scoring_rule": "distance",
            "scale": 0.04,
        },
    ],
    "diagnostics_to_extract": [
        "converged",
        "boundary_error",
        "payout_boundary",
        "return_cash_ratio",
        "investment_at_payout",
        "is_value_increasing",
        "is_dv_decreasing",
    ],
    "search_budget": {
        "coarse_samples": 5,
        "shrink_rounds": 1,
        "keep_ratio": 0.4,
        "min_keep": 2,
        "max_candidates": 24,
    },
    "fallback_numeric_toggles": [
        {"boundary_search_method": "hybr", "number": 350},
        {"boundary_search_method": "hybr", "number": 500},
    ],
}


def build_solver(candidate_parameters, numeric_toggles, previous_trial=None):
    """Construct one BCW refinancing solver candidate."""
    phi = float(candidate_parameters["phi"])
    sigma = float(candidate_parameters["sigma"])
    parameter = refinancing.Parameter(
        phi=phi,
        sigma=sigma,
        v_left_guess=0.90 if phi > 0 else 1.05,
    )
    boundary = refinancing.Boundary(
        p=parameter,
        s_min=0.0,
        s_max=0.19 if phi >= 0.010 else 0.17,
    )
    solver = fjb.Solver(
        boundary=boundary,
        model=refinancing.Model(policy=refinancing.Policy()),
        policy_guess=True,
        number=int(numeric_toggles.get("number", 250)),
        config=refinancing.make_config(),
    )
    return {
        "solver": solver,
        "workflow": "boundary_search",
        "workflow_kwargs": {
            "method": numeric_toggles.get("boundary_search_method", "bisection"),
            "verbose": False,
        },
        "metadata": {
            "candidate_phi": phi,
            "candidate_sigma": sigma,
            "previous_trial_available": previous_trial is not None,
        },
    }


def extract_diagnostics(execution, candidate_parameters, numeric_toggles):
    """Extract searchable diagnostics from a solved BCW candidate."""
    state = execution["state"]
    grid = state.grid
    series = build_series(grid)
    summary = common_summary(grid, series)
    return_cash_ratio, idx = refinancing.return_cash_ratio_from_grid(grid)
    diagnostics = {
        "phi": float(candidate_parameters["phi"]),
        "sigma": float(candidate_parameters["sigma"]),
        "converged": bool(state.converged),
        "boundary_error": float(state.best_error),
        "payout_boundary": float(grid.boundary.s_max),
        "return_cash_ratio": float(return_cash_ratio),
        "dv_at_return_cash_ratio": float(series["dv"][int(idx)]),
        "investment_at_payout": float(summary["investment_at_payout"]),
        "is_value_increasing": bool(summary["is_value_increasing"]),
        "is_dv_decreasing": bool(summary["is_dv_decreasing"]),
        "boundary_search_method": numeric_toggles.get("boundary_search_method", "bisection"),
    }
    return diagnostics


def check_constraints(diagnostics, constraints, **kwargs):
    """Evaluate BCW hard constraints with explicit bool handling."""
    failed = []
    details = []
    for constraint in constraints:
        payload = constraint if isinstance(constraint, dict) else vars(constraint)
        actual = diagnostics[payload["metric"]]
        operator = payload["operator"]
        target = payload["target_or_interval"]
        tolerance = float(payload.get("tolerance", 0.0))

        if operator == "==":
            passed = bool(actual) is bool(target)
        elif operator == "<=":
            passed = float(actual) <= float(target) + tolerance
        elif operator == "between":
            low, high = target
            passed = float(low) - tolerance <= float(actual) <= float(high) + tolerance
        else:  # pragma: no cover - defensive branch
            raise ValueError(f"Unsupported operator in BCW task: {operator}")

        details.append(
            {
                "name": payload["name"],
                "actual": actual,
                "target_or_interval": target,
                "passed": passed,
            }
        )
        if not passed:
            failed.append(payload["name"])

    return {"feasible": not failed, "failed_constraints": failed, "details": details}


def score_preferences(diagnostics, preferences, **kwargs):
    """Rank feasible BCW candidates by closeness to benchmark diagnostics."""
    components = {}
    total = 0.0
    for preference in preferences:
        payload = preference if isinstance(preference, dict) else vars(preference)
        actual = float(diagnostics[payload["metric"]])
        target = float(payload["target"])
        scale = float(payload.get("scale", 1.0))
        weight = float(payload["weight"])
        component = weight / (1.0 + abs(actual - target) / scale)
        components[payload["name"]] = component
        total += component
    return {"total_score": total, "components": components}


def plot_best_result(best_trial, output_dir, **kwargs):
    """Write a simple 2x2 diagnostic figure for the best rescue candidate."""
    state = best_trial.execution["state"]
    grid = state.grid
    series = build_series(grid)

    fig, axes = paper_figure(figsize=(10, 7), top=0.90, hspace=0.36)
    panels = [
        ("v", "A. Value ratio"),
        ("dv", "B. Marginal value"),
        ("investment", "C. Investment ratio"),
        ("investment_sensitivity", "D. Investment sensitivity"),
    ]

    for ax, (metric, title) in zip(axes.flat, panels, strict=True):
        ax.plot(series["s"], series[metric], color="#1f1f1f", linewidth=2.0)
        finalize_axes(ax, title=title)

    fig.suptitle(
        f"Best rescue candidate: phi={best_trial.candidate_parameters['phi']:.4f}",
        y=0.98,
    )
    output_path = Path(output_dir) / "best_candidate_plot.png"
    return save_figure(fig, output_path)


if __name__ == "__main__":  # pragma: no cover - manual task preview
    phi_grid = np.linspace(0.004, 0.016, 5)
    print({"phi_grid": phi_grid.tolist()})
