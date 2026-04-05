"""Template: parameter-search rescue adapter for FinHJB model-coder.

Copy this file when a model is implementable but the calibration or boundary
guesses are not yet reliable enough for a single hard-coded solve.
"""

from __future__ import annotations

from pathlib import Path


PARAMETER_SEARCH_SPEC = {
    "task_name": "replace-me",
    "mode": "rescue",
    "fixed_parameters": {
        # "sigma": 0.25,
    },
    "search_parameters": [
        {
            "name": "replace_parameter",
            "low": 0.05,
            "high": 0.25,
            "scale": "linear",
            "fixed": False,
            "initial_center": 0.10,
        },
    ],
    "hard_constraints": [
        {
            "name": "replace_constraint",
            "metric": "replace_metric",
            "operator": "between",
            "target_or_interval": [0.0, 1.0],
            "tolerance": 1e-6,
        },
    ],
    "soft_preferences": [
        {
            "name": "replace_preference",
            "metric": "replace_metric",
            "target": 0.5,
            "weight": 1.0,
            "scoring_rule": "distance",
            "scale": 0.1,
        },
    ],
    "diagnostics_to_extract": [
        "replace_metric",
    ],
    "search_budget": {
        "coarse_samples": 5,
        "shrink_rounds": 1,
        "keep_ratio": 0.4,
        "min_keep": 2,
        "max_candidates": 100,
    },
    "fallback_numeric_toggles": [
        {"boundary_search_method": "bisection", "number": 400},
        {"boundary_search_method": "hybr", "number": 600},
    ],
}


def build_solver(candidate_parameters, numeric_toggles, previous_trial=None):
    """Return {"solver", "workflow", "workflow_kwargs", "metadata"} for one candidate."""
    raise NotImplementedError


def extract_diagnostics(execution, candidate_parameters, numeric_toggles):
    """Return metric diagnostics used by hard constraints and soft preferences."""
    raise NotImplementedError


def check_constraints(diagnostics, constraints, **kwargs):
    """Return {"feasible": bool, "failed_constraints": [...], "details": [...]}."""
    raise NotImplementedError


def score_preferences(diagnostics, preferences, **kwargs):
    """Return {"total_score": float, "components": {...}} for feasible candidates."""
    raise NotImplementedError


def plot_best_result(best_trial, output_dir, **kwargs):
    """Optional: write a scholar-facing diagnostic figure for the best candidate."""
    return Path(output_dir) / "replace_me.png"
