#!/usr/bin/env python3
"""Generic parameter-search runner for FinHJB model-coder tasks.

This runner executes a two-stage parameter-search rescue workflow:

1. build candidate solves from a task-specific adapter
2. filter by hard constraints
3. score feasible candidates with soft preferences
4. shrink the search box around the top feasible region and rerun

Task adapters are regular Python modules that define a
`PARAMETER_SEARCH_SPEC` dictionary plus the adapter hooks documented in
`references/parameter-search-protocol.md`.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import inspect
import itertools
import json
import math
import sys
import traceback
from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class SearchParameter:
    """One searchable parameter and its admissible range."""

    name: str
    low: float
    high: float
    scale: str = "linear"
    fixed: bool = False
    initial_center: float | None = None


@dataclass(frozen=True)
class HardConstraint:
    """Machine-checkable condition that must be satisfied."""

    name: str
    metric: str
    operator: str
    target_or_interval: Any
    tolerance: float = 0.0


@dataclass(frozen=True)
class SoftPreference:
    """Scored preference used to rank feasible candidates."""

    name: str
    metric: str
    target: Any
    weight: float
    scoring_rule: str
    scale: float | None = None


@dataclass(frozen=True)
class SearchBudget:
    """Sampling budget for the rescue search."""

    coarse_samples: int = 5
    shrink_rounds: int = 1
    keep_ratio: float = 0.4
    min_keep: int = 2
    early_stop_score: float | None = None
    max_candidates: int = 200


@dataclass
class SolverBuild:
    """Normalized solver build returned by a task adapter."""

    solver: Any
    workflow: str = "solve"
    workflow_kwargs: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParameterSearchSpec:
    """Normalized parameter-search configuration."""

    task_name: str
    mode: str
    fixed_parameters: dict[str, Any]
    search_parameters: list[SearchParameter]
    hard_constraints: list[HardConstraint]
    soft_preferences: list[SoftPreference]
    diagnostics_to_extract: list[str]
    search_budget: SearchBudget
    fallback_numeric_toggles: list[dict[str, Any]]


@dataclass
class TrialRecord:
    """One evaluated search candidate."""

    round_index: int
    candidate_index: int
    candidate_parameters: dict[str, Any]
    used_numeric_toggles: dict[str, Any] | None
    feasible: bool
    total_score: float | None
    score_components: dict[str, float]
    diagnostics: dict[str, Any]
    failed_constraints: list[str]
    failure_reason: str | None = None
    workflow: str | None = None
    build_metadata: dict[str, Any] = field(default_factory=dict)
    retries: list[dict[str, Any]] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)
    execution: Any = field(default=None, repr=False)

    def sort_score(self) -> float:
        """Return a sortable score value."""
        return float("-inf") if self.total_score is None else float(self.total_score)


def _load_module_from_path(module_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load task module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_path.stem] = module
    spec.loader.exec_module(module)
    return module


def _call_with_supported_kwargs(func: Callable[..., Any], **kwargs: Any) -> Any:
    signature = inspect.signature(func)
    accepts_var_kwargs = any(
        param.kind == inspect.Parameter.VAR_KEYWORD
        for param in signature.parameters.values()
    )
    if accepts_var_kwargs:
        return func(**kwargs)

    filtered_kwargs = {
        name: value for name, value in kwargs.items() if name in signature.parameters
    }
    return func(**filtered_kwargs)


def _normalize_search_parameter(raw: SearchParameter | Mapping[str, Any]) -> SearchParameter:
    if isinstance(raw, SearchParameter):
        return raw
    return SearchParameter(**dict(raw))


def _normalize_hard_constraint(raw: HardConstraint | Mapping[str, Any]) -> HardConstraint:
    if isinstance(raw, HardConstraint):
        return raw
    return HardConstraint(**dict(raw))


def _normalize_soft_preference(raw: SoftPreference | Mapping[str, Any]) -> SoftPreference:
    if isinstance(raw, SoftPreference):
        return raw
    payload = dict(raw)
    payload.setdefault("weight", 1.0)
    payload.setdefault("scoring_rule", "distance")
    return SoftPreference(**payload)


def _normalize_budget(raw: SearchBudget | Mapping[str, Any] | None) -> SearchBudget:
    if raw is None:
        return SearchBudget()
    if isinstance(raw, SearchBudget):
        return raw
    return SearchBudget(**dict(raw))


def _normalize_build(raw: SolverBuild | Mapping[str, Any]) -> SolverBuild:
    if isinstance(raw, SolverBuild):
        return raw
    payload = dict(raw)
    return SolverBuild(
        solver=payload["solver"],
        workflow=payload.get("workflow", "solve"),
        workflow_kwargs=dict(payload.get("workflow_kwargs", {})),
        metadata=dict(payload.get("metadata", {})),
    )


def _normalize_spec(module: ModuleType) -> ParameterSearchSpec:
    raw = getattr(module, "PARAMETER_SEARCH_SPEC", None)
    if raw is None:
        raise RuntimeError(
            "Task adapter must define PARAMETER_SEARCH_SPEC for parameter-search rescue mode."
        )

    spec = dict(raw)
    return ParameterSearchSpec(
        task_name=spec.get("task_name", module.__name__),
        mode=spec.get("mode", "rescue"),
        fixed_parameters=dict(spec.get("fixed_parameters", {})),
        search_parameters=[
            _normalize_search_parameter(item) for item in spec.get("search_parameters", [])
        ],
        hard_constraints=[
            _normalize_hard_constraint(item) for item in spec.get("hard_constraints", [])
        ],
        soft_preferences=[
            _normalize_soft_preference(item) for item in spec.get("soft_preferences", [])
        ],
        diagnostics_to_extract=list(spec.get("diagnostics_to_extract", [])),
        search_budget=_normalize_budget(spec.get("search_budget")),
        fallback_numeric_toggles=[dict(item) for item in spec.get("fallback_numeric_toggles", [])],
    )


def _serialize(value: Any) -> Any:
    if isinstance(value, TrialRecord):
        return {
            "round_index": value.round_index,
            "candidate_index": value.candidate_index,
            "candidate_parameters": _serialize(value.candidate_parameters),
            "used_numeric_toggles": _serialize(value.used_numeric_toggles),
            "feasible": value.feasible,
            "total_score": value.total_score,
            "score_components": _serialize(value.score_components),
            "diagnostics": _serialize(value.diagnostics),
            "failed_constraints": list(value.failed_constraints),
            "failure_reason": value.failure_reason,
            "workflow": value.workflow,
            "build_metadata": _serialize(value.build_metadata),
            "retries": _serialize(value.retries),
            "artifacts": _serialize(value.artifacts),
        }
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if is_dataclass(value):
        return {k: _serialize(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): _serialize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def _get_metric_value(diagnostics: Mapping[str, Any], metric: str) -> Any:
    if metric not in diagnostics:
        raise KeyError(f"Metric '{metric}' was not produced by diagnostics extraction.")
    return diagnostics[metric]


def evaluate_constraints(
    diagnostics: Mapping[str, Any],
    constraints: Sequence[HardConstraint | Mapping[str, Any]],
) -> dict[str, Any]:
    """Evaluate generic hard constraints from metric diagnostics."""

    failed: list[str] = []
    details: list[dict[str, Any]] = []
    for raw in constraints:
        constraint = _normalize_hard_constraint(raw)
        actual = _get_metric_value(diagnostics, constraint.metric)
        tolerance = float(constraint.tolerance)
        operator = constraint.operator
        target = constraint.target_or_interval

        if operator == "<=":
            passed = float(actual) <= float(target) + tolerance
        elif operator == ">=":
            passed = float(actual) >= float(target) - tolerance
        elif operator == "==":
            passed = math.isclose(float(actual), float(target), abs_tol=tolerance)
        elif operator == "between":
            low, high = target
            passed = float(low) - tolerance <= float(actual) <= float(high) + tolerance
        elif operator == "in":
            passed = actual in target
        else:
            raise ValueError(f"Unsupported hard-constraint operator: {operator}")

        details.append(
            {
                "name": constraint.name,
                "metric": constraint.metric,
                "operator": operator,
                "target_or_interval": _serialize(target),
                "tolerance": tolerance,
                "actual": _serialize(actual),
                "passed": bool(passed),
            }
        )
        if not passed:
            failed.append(constraint.name)

    return {"feasible": not failed, "failed_constraints": failed, "details": details}


def _distance_to_target(actual: float, target: Any) -> float:
    if isinstance(target, (list, tuple)) and len(target) == 2:
        low, high = float(target[0]), float(target[1])
        if low <= actual <= high:
            return 0.0
        if actual < low:
            return low - actual
        return actual - high
    return abs(actual - float(target))


def score_preferences(
    diagnostics: Mapping[str, Any],
    preferences: Sequence[SoftPreference | Mapping[str, Any]],
) -> dict[str, Any]:
    """Score generic soft preferences from metric diagnostics."""

    components: dict[str, float] = {}
    total = 0.0
    for raw in preferences:
        preference = _normalize_soft_preference(raw)
        actual = float(_get_metric_value(diagnostics, preference.metric))
        weight = float(preference.weight)

        if preference.scoring_rule == "distance":
            scale = 1.0 if preference.scale in {None, 0} else float(preference.scale)
            distance = _distance_to_target(actual, preference.target)
            component = weight / (1.0 + distance / scale)
        elif preference.scoring_rule == "maximize":
            scale = 1.0 if preference.scale in {None, 0} else float(preference.scale)
            component = weight * (actual / scale)
        elif preference.scoring_rule == "minimize":
            scale = 1.0 if preference.scale in {None, 0} else float(preference.scale)
            component = weight / (1.0 + max(actual, 0.0) / scale)
        elif preference.scoring_rule == "boolean":
            component = weight if bool(actual) == bool(preference.target) else 0.0
        else:
            raise ValueError(f"Unsupported soft-preference scoring rule: {preference.scoring_rule}")

        components[preference.name] = float(component)
        total += float(component)

    return {"total_score": float(total), "components": components}


def _value_grid(search_parameter: SearchParameter, sample_count: int) -> np.ndarray:
    if sample_count < 2:
        return np.array([search_parameter.initial_center or search_parameter.low], dtype=float)

    if search_parameter.scale == "linear":
        values = np.linspace(search_parameter.low, search_parameter.high, sample_count)
    elif search_parameter.scale == "log":
        if search_parameter.low <= 0 or search_parameter.high <= 0:
            raise ValueError(
                f"log-scale search requires positive bounds for '{search_parameter.name}'."
            )
        values = np.geomspace(search_parameter.low, search_parameter.high, sample_count)
    else:
        raise ValueError(f"Unsupported search scale: {search_parameter.scale}")

    if search_parameter.initial_center is not None:
        values = np.unique(
            np.concatenate([values, np.array([search_parameter.initial_center], dtype=float)])
        )
        values.sort()
    return values


def _generate_candidates(
    search_parameters: Sequence[SearchParameter],
    ranges: Mapping[str, tuple[float, float]],
    sample_count: int,
    max_candidates: int,
) -> list[dict[str, float]]:
    if not search_parameters:
        return [{}]

    value_lists: list[list[float]] = []
    for item in search_parameters:
        low, high = ranges[item.name]
        parameter = SearchParameter(
            name=item.name,
            low=low,
            high=high,
            scale=item.scale,
            fixed=item.fixed,
            initial_center=item.initial_center,
        )
        value_lists.append([float(value) for value in _value_grid(parameter, sample_count)])

    total_candidates = 1
    for values in value_lists:
        total_candidates *= len(values)
    if total_candidates > max_candidates:
        raise ValueError(
            "Search space is too large for the current deterministic runner. "
            f"Got {total_candidates} candidates, max allowed is {max_candidates}."
        )

    candidates = []
    for combination in itertools.product(*value_lists):
        candidates.append(
            {param.name: float(value) for param, value in zip(search_parameters, combination, strict=True)}
        )
    return candidates


def _dedupe_key(candidate_parameters: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted((name, f"{float(value):.12g}") for name, value in candidate_parameters.items())
    )


def _execute_build(build: SolverBuild) -> dict[str, Any]:
    workflow = build.workflow
    solver = build.solver
    kwargs = dict(build.workflow_kwargs)

    if workflow == "solve":
        raw = solver.solve(**kwargs)
        if isinstance(raw, tuple) and len(raw) == 2:
            state, history = raw
            return {
                "workflow": workflow,
                "state": state,
                "history": history,
                "raw_result": raw,
            }
        return {"workflow": workflow, "state": raw, "raw_result": raw}
    if workflow == "boundary_search":
        state = solver.boundary_search(**kwargs)
        return {"workflow": workflow, "state": state, "raw_result": state}
    if workflow == "boundary_update":
        raw = solver.boundary_update(**kwargs)
        if isinstance(raw, tuple) and len(raw) == 2:
            state, history = raw
            return {
                "workflow": workflow,
                "state": state,
                "history": history,
                "raw_result": raw,
            }
        return {"workflow": workflow, "state": raw, "raw_result": raw}
    raise ValueError(f"Unsupported workflow: {workflow}")


def _normalize_constraint_result(raw: Any) -> dict[str, Any]:
    if isinstance(raw, bool):
        return {"feasible": raw, "failed_constraints": [] if raw else ["unspecified"]}
    result = dict(raw)
    result.setdefault("feasible", not result.get("failed_constraints"))
    result.setdefault("failed_constraints", [])
    return result


def _normalize_score_result(raw: Any) -> dict[str, Any]:
    if isinstance(raw, (int, float)):
        return {"total_score": float(raw), "components": {}}
    result = dict(raw)
    result.setdefault("total_score", 0.0)
    result.setdefault("components", {})
    return result


def _evaluate_candidate(
    module: ModuleType,
    spec: ParameterSearchSpec,
    round_index: int,
    candidate_index: int,
    search_values: dict[str, float],
    previous_trial: TrialRecord | None,
) -> TrialRecord:
    candidate_parameters = dict(spec.fixed_parameters)
    candidate_parameters.update(search_values)

    toggles = spec.fallback_numeric_toggles or [{}]
    retries: list[dict[str, Any]] = []
    build_solver = getattr(module, "build_solver")
    extract_diagnostics_fn = getattr(module, "extract_diagnostics")
    constraint_fn = getattr(module, "check_constraints", evaluate_constraints)
    score_fn = getattr(module, "score_preferences", score_preferences)

    for toggle_index, numeric_toggles in enumerate(toggles):
        try:
            raw_build = _call_with_supported_kwargs(
                build_solver,
                candidate_parameters=candidate_parameters,
                numeric_toggles=numeric_toggles,
                previous_trial=previous_trial,
                search_spec=spec,
            )
            build = _normalize_build(raw_build)
            execution = _execute_build(build)
            diagnostics = _call_with_supported_kwargs(
                extract_diagnostics_fn,
                execution=execution,
                candidate_parameters=candidate_parameters,
                numeric_toggles=numeric_toggles,
                search_spec=spec,
            )
            diagnostics = dict(diagnostics)

            constraint_result = _normalize_constraint_result(
                _call_with_supported_kwargs(
                    constraint_fn,
                    diagnostics=diagnostics,
                    constraints=spec.hard_constraints,
                    candidate_parameters=candidate_parameters,
                    numeric_toggles=numeric_toggles,
                    execution=execution,
                    search_spec=spec,
                )
            )
            feasible = bool(constraint_result["feasible"])
            score_result = {"total_score": None, "components": {}}
            if feasible:
                score_result = _normalize_score_result(
                    _call_with_supported_kwargs(
                        score_fn,
                        diagnostics=diagnostics,
                        preferences=spec.soft_preferences,
                        candidate_parameters=candidate_parameters,
                        numeric_toggles=numeric_toggles,
                        execution=execution,
                        search_spec=spec,
                    )
                )

            return TrialRecord(
                round_index=round_index,
                candidate_index=candidate_index,
                candidate_parameters=candidate_parameters,
                used_numeric_toggles=dict(numeric_toggles),
                feasible=feasible,
                total_score=score_result["total_score"],
                score_components=dict(score_result["components"]),
                diagnostics=diagnostics,
                failed_constraints=list(constraint_result.get("failed_constraints", [])),
                workflow=build.workflow,
                build_metadata=dict(build.metadata),
                retries=retries,
                execution=execution,
            )
        except Exception as exc:  # pragma: no cover - exercised via integration tests
            retries.append(
                {
                    "toggle_index": toggle_index,
                    "numeric_toggles": dict(numeric_toggles),
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "traceback": traceback.format_exc(limit=5),
                }
            )

    failure_reason = retries[-1]["error_message"] if retries else "Candidate evaluation failed."
    return TrialRecord(
        round_index=round_index,
        candidate_index=candidate_index,
        candidate_parameters=candidate_parameters,
        used_numeric_toggles=None,
        feasible=False,
        total_score=None,
        score_components={},
        diagnostics={},
        failed_constraints=[],
        failure_reason=failure_reason,
        retries=retries,
    )


def _shrink_ranges(
    current_ranges: Mapping[str, tuple[float, float]],
    top_trials: Sequence[TrialRecord],
    search_parameters: Sequence[SearchParameter],
) -> dict[str, tuple[float, float]]:
    updated: dict[str, tuple[float, float]] = {}
    for parameter in search_parameters:
        values = [float(trial.candidate_parameters[parameter.name]) for trial in top_trials]
        if not values:
            updated[parameter.name] = tuple(current_ranges[parameter.name])
            continue
        low = min(values)
        high = max(values)
        if math.isclose(low, high):
            updated[parameter.name] = tuple(current_ranges[parameter.name])
        else:
            updated[parameter.name] = (low, high)
    return updated


def _summary_row(trial: TrialRecord) -> dict[str, Any]:
    row = {
        "round_index": trial.round_index,
        "candidate_index": trial.candidate_index,
        "feasible": trial.feasible,
        "total_score": trial.total_score,
        "failure_reason": trial.failure_reason,
        "workflow": trial.workflow,
        "failed_constraints": ",".join(trial.failed_constraints),
        "used_numeric_toggles": json.dumps(_serialize(trial.used_numeric_toggles), sort_keys=True),
    }
    for key, value in sorted(trial.candidate_parameters.items()):
        row[f"param__{key}"] = value
    for key, value in sorted(trial.diagnostics.items()):
        row[f"diag__{key}"] = value if isinstance(value, (int, float, str, bool)) else json.dumps(
            _serialize(value), sort_keys=True
        )
    return row


def _write_artifacts(
    output_dir: Path,
    task_path: Path,
    spec: ParameterSearchSpec,
    rounds: list[dict[str, Any]],
    trials: list[TrialRecord],
    best_trial: TrialRecord | None,
    top_feasible: list[TrialRecord],
    plot_artifact: Path | None,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    history_json_path = output_dir / "search_history.json"
    history_csv_path = output_dir / "search_history.csv"
    summary_path = output_dir / "search_summary.json"
    best_path = output_dir / "best_parameters.json"
    feasible_path = output_dir / "top_feasible.json"

    history_payload = [_serialize(trial) for trial in trials]
    history_json_path.write_text(json.dumps(history_payload, indent=2, sort_keys=True))

    rows = [_summary_row(trial) for trial in trials]
    fieldnames = sorted({field for row in rows for field in row}) if rows else []
    with history_csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    summary_payload = {
        "task_name": spec.task_name,
        "task_module": str(task_path),
        "parameter_search": _serialize(spec),
        "rounds": _serialize(rounds),
        "trial_count": len(trials),
        "feasible_count": len(top_feasible),
        "best_trial": _serialize(best_trial) if best_trial else None,
        "top_feasible": _serialize(top_feasible[:5]),
        "artifacts": {
            "history_json": str(history_json_path),
            "history_csv": str(history_csv_path),
            "top_feasible_json": str(feasible_path),
            "best_parameters_json": str(best_path),
            "plot": str(plot_artifact) if plot_artifact else None,
        },
        "reproduce_command": (
            f"python {Path(__file__).resolve()} --task {task_path.resolve()} --output-dir {output_dir.resolve()}"
        ),
    }
    summary_path.write_text(json.dumps(summary_payload, indent=2, sort_keys=True))

    best_payload = (
        {
            "candidate_parameters": _serialize(best_trial.candidate_parameters),
            "used_numeric_toggles": _serialize(best_trial.used_numeric_toggles),
            "diagnostics": _serialize(best_trial.diagnostics),
            "total_score": best_trial.total_score,
            "score_components": _serialize(best_trial.score_components),
        }
        if best_trial
        else {"candidate_parameters": None}
    )
    best_path.write_text(json.dumps(best_payload, indent=2, sort_keys=True))
    feasible_path.write_text(json.dumps(_serialize(top_feasible[:10]), indent=2, sort_keys=True))

    return {
        "history_json": history_json_path,
        "history_csv": history_csv_path,
        "summary_json": summary_path,
        "best_parameters_json": best_path,
        "top_feasible_json": feasible_path,
    }


def run_parameter_search(task_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    """Run the rescue search for one task-adapter module."""

    task_path = Path(task_path).resolve()
    output_dir = (task_path.parent / "search_artifacts") if output_dir is None else Path(output_dir)
    output_dir = output_dir.resolve()

    module = _load_module_from_path(task_path)
    spec = _normalize_spec(module)
    if spec.mode != "rescue":
        raise ValueError(
            f"parameter-search runner only supports mode='rescue', got {spec.mode!r}."
        )
    if not spec.search_parameters:
        raise ValueError("parameter-search rescue mode requires at least one search parameter.")

    current_ranges = {
        item.name: (float(item.low), float(item.high)) for item in spec.search_parameters
    }
    seen_candidates: set[tuple[tuple[str, str], ...]] = set()
    all_trials: list[TrialRecord] = []
    round_summaries: list[dict[str, Any]] = []
    previous_trial: TrialRecord | None = None
    plot_artifact: Path | None = None

    for round_index in range(spec.search_budget.shrink_rounds + 1):
        search_values = _generate_candidates(
            search_parameters=spec.search_parameters,
            ranges=current_ranges,
            sample_count=spec.search_budget.coarse_samples,
            max_candidates=spec.search_budget.max_candidates,
        )

        if len(spec.search_parameters) == 1:
            parameter_name = spec.search_parameters[0].name
            search_values = sorted(search_values, key=lambda item: item[parameter_name])

        round_trials: list[TrialRecord] = []
        for candidate_index, candidate in enumerate(search_values):
            key = _dedupe_key({**spec.fixed_parameters, **candidate})
            if key in seen_candidates:
                continue
            seen_candidates.add(key)
            trial = _evaluate_candidate(
                module=module,
                spec=spec,
                round_index=round_index,
                candidate_index=candidate_index,
                search_values=candidate,
                previous_trial=previous_trial if len(spec.search_parameters) == 1 else None,
            )
            round_trials.append(trial)
            all_trials.append(trial)
            if trial.feasible and len(spec.search_parameters) == 1:
                previous_trial = trial

        feasible_trials = sorted(
            [trial for trial in round_trials if trial.feasible],
            key=lambda trial: trial.sort_score(),
            reverse=True,
        )
        keep_n = 0
        shrunk_ranges = dict(current_ranges)
        if feasible_trials and round_index < spec.search_budget.shrink_rounds:
            keep_n = max(
                spec.search_budget.min_keep,
                math.ceil(len(feasible_trials) * spec.search_budget.keep_ratio),
            )
            keep_n = min(keep_n, len(feasible_trials))
            shrunk_ranges = _shrink_ranges(
                current_ranges=current_ranges,
                top_trials=feasible_trials[:keep_n],
                search_parameters=spec.search_parameters,
            )

        round_summary = {
            "round_index": round_index,
            "search_ranges": _serialize(current_ranges),
            "candidate_count": len(round_trials),
            "feasible_count": len(feasible_trials),
            "keep_n": keep_n,
            "best_score": feasible_trials[0].total_score if feasible_trials else None,
            "shrunk_ranges": _serialize(shrunk_ranges),
        }
        round_summaries.append(round_summary)

        if (
            feasible_trials
            and spec.search_budget.early_stop_score is not None
            and feasible_trials[0].total_score is not None
            and feasible_trials[0].total_score >= spec.search_budget.early_stop_score
        ):
            break

        if round_index == spec.search_budget.shrink_rounds:
            continue
        if not feasible_trials or shrunk_ranges == current_ranges:
            break
        current_ranges = shrunk_ranges

    feasible_trials = sorted(
        [trial for trial in all_trials if trial.feasible],
        key=lambda trial: trial.sort_score(),
        reverse=True,
    )
    best_trial = feasible_trials[0] if feasible_trials else None

    plot_fn = getattr(module, "plot_best_result", None)
    if plot_fn is not None and best_trial is not None:
        raw_plot = _call_with_supported_kwargs(
            plot_fn,
            best_trial=best_trial,
            output_dir=output_dir,
            search_spec=spec,
        )
        if raw_plot is not None:
            plot_artifact = Path(raw_plot)

    artifacts = _write_artifacts(
        output_dir=output_dir,
        task_path=task_path,
        spec=spec,
        rounds=round_summaries,
        trials=all_trials,
        best_trial=best_trial,
        top_feasible=feasible_trials,
        plot_artifact=plot_artifact,
    )

    return {
        "task_name": spec.task_name,
        "task_module": task_path,
        "output_dir": output_dir,
        "artifacts": artifacts,
        "rounds": round_summaries,
        "best_trial": best_trial,
        "top_feasible": feasible_trials[:5],
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the FinHJB parameter-search rescue runner on a task adapter.",
    )
    parser.add_argument(
        "--task",
        required=True,
        help="Path to the task adapter module that defines PARAMETER_SEARCH_SPEC.",
    )
    parser.add_argument(
        "--output-dir",
        help="Optional artifact directory. Defaults to <task_dir>/search_artifacts.",
    )
    return parser


def main() -> int:
    args = _build_arg_parser().parse_args()
    bundle = run_parameter_search(task_path=args.task, output_dir=args.output_dir)
    printable = {
        "task_name": bundle["task_name"],
        "task_module": str(bundle["task_module"]),
        "output_dir": str(bundle["output_dir"]),
        "artifacts": {key: str(value) for key, value in bundle["artifacts"].items()},
        "best_trial": _serialize(bundle["best_trial"]),
    }
    print(json.dumps(printable, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
