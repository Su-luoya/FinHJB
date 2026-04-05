import importlib.util
import json
import sys
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_FILE = ROOT / "skills" / "finhjb-model-coder" / "scripts" / "parameter_search_runner.py"


def load_runner_module():
    spec = importlib.util.spec_from_file_location("parameter_search_runner_test", RUNNER_FILE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_fake_task(task_path: Path) -> None:
    task_path.write_text(
        textwrap.dedent(
            """
            PARAMETER_SEARCH_SPEC = {
                "task_name": "fake-parameter-search",
                "mode": "rescue",
                "fixed_parameters": {"shift": 1.0},
                "search_parameters": [
                    {
                        "name": "x",
                        "low": 0.0,
                        "high": 10.0,
                        "scale": "linear",
                        "fixed": False,
                        "initial_center": 7.0,
                    }
                ],
                "hard_constraints": [
                    {
                        "name": "x_high_enough",
                        "metric": "x_value",
                        "operator": ">=",
                        "target_or_interval": 4.0,
                        "tolerance": 0.0,
                    }
                ],
                "soft_preferences": [
                    {
                        "name": "near_target",
                        "metric": "distance_to_target",
                        "target": 0.0,
                        "weight": 1.0,
                        "scoring_rule": "minimize",
                        "scale": 1.0,
                    }
                ],
                "diagnostics_to_extract": [
                    "x_value",
                    "distance_to_target",
                    "shift",
                    "toggle_mode",
                ],
                "search_budget": {
                    "coarse_samples": 5,
                    "shrink_rounds": 1,
                    "keep_ratio": 0.5,
                    "min_keep": 2,
                    "max_candidates": 50,
                },
                "fallback_numeric_toggles": [
                    {"mode": "strict"},
                    {"mode": "relaxed"},
                ],
            }


            class FakeSolver:
                def __init__(self, x, mode):
                    self.x = x
                    self.mode = mode

                def solve(self):
                    if self.mode == "strict" and self.x < 5.0:
                        raise RuntimeError("strict mode rejected low-x candidate")
                    return {"x": self.x, "mode": self.mode}, None


            def build_solver(candidate_parameters, numeric_toggles, previous_trial=None):
                solver = FakeSolver(
                    x=float(candidate_parameters["x"]),
                    mode=numeric_toggles.get("mode", "strict"),
                )
                return {
                    "solver": solver,
                    "workflow": "solve",
                    "workflow_kwargs": {},
                    "metadata": {
                        "previous_trial_available": previous_trial is not None,
                    },
                }


            def extract_diagnostics(execution, candidate_parameters, numeric_toggles):
                state = execution["state"]
                x = float(state["x"])
                return {
                    "x_value": x,
                    "distance_to_target": abs(x - 7.0),
                    "shift": float(candidate_parameters["shift"]),
                    "toggle_mode": state["mode"],
                }
            """
        )
    )


def test_parameter_search_runner_filters_scores_and_shrinks(tmp_path):
    runner = load_runner_module()
    task_path = tmp_path / "fake_task.py"
    write_fake_task(task_path)

    bundle = runner.run_parameter_search(task_path=task_path, output_dir=tmp_path / "artifacts")

    best_trial = bundle["best_trial"]
    assert best_trial is not None
    assert best_trial.feasible
    assert best_trial.candidate_parameters["shift"] == 1.0
    assert abs(best_trial.candidate_parameters["x"] - 7.0) < 1e-8

    rounds = bundle["rounds"]
    assert rounds
    assert rounds[0]["search_ranges"]["x"] == [0.0, 10.0] or rounds[0]["search_ranges"]["x"] == (
        0.0,
        10.0,
    )
    shrunk_low, shrunk_high = rounds[0]["shrunk_ranges"]["x"]
    assert shrunk_high - shrunk_low < 10.0

    history = json.loads(bundle["artifacts"]["history_json"].read_text())
    feasible_x = [entry["candidate_parameters"]["x"] for entry in history if entry["feasible"]]
    assert feasible_x
    assert all(x >= 4.0 for x in feasible_x)

    failed_entries = [
        entry for entry in history if entry["candidate_parameters"]["x"] < 4.0 and not entry["feasible"]
    ]
    assert failed_entries
    assert all("x_high_enough" in entry["failed_constraints"] for entry in failed_entries)


def test_parameter_search_runner_uses_only_declared_numeric_fallbacks(tmp_path):
    runner = load_runner_module()
    task_path = tmp_path / "fake_task.py"
    write_fake_task(task_path)

    bundle = runner.run_parameter_search(task_path=task_path, output_dir=tmp_path / "artifacts")

    history = json.loads(bundle["artifacts"]["history_json"].read_text())
    used_modes = {
        entry["used_numeric_toggles"]["mode"]
        for entry in history
        if entry["used_numeric_toggles"] is not None
    }
    assert used_modes <= {"strict", "relaxed"}
    assert "relaxed" in used_modes

    retried = [entry for entry in history if entry["retries"]]
    assert retried
    first_retry = retried[0]["retries"][0]
    assert first_retry["numeric_toggles"]["mode"] == "strict"
