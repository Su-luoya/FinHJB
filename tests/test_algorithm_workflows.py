import jax.numpy as jnp
import pytest

import finhjb as fjb
from finhjb.algorithm.boundary_search import get_boundary_search_solver
from finhjb.algorithm.improvement import NewtonRaphson
from tests.helpers import SimpleModel, SimpleParameter, StablePolicy


def test_policy_evaluation_runs_and_returns_history(solver):
    evaluator = fjb.algorithm.PolicyEvaluation(config=solver.config)
    final_state, history = evaluator.policy_evaluation(solver._grid)

    assert history.shape[0] == solver.config.pe_max_iter
    assert final_state.grid.v.shape == solver._grid.v.shape
    assert bool(jnp.all(jnp.isfinite(final_state.grid.v)))


def test_policy_iteration_scan_runs(solver):
    state, history = solver.solve()
    assert history.shape[0] == solver.config.pi_max_iter
    assert state.grid.v.shape == solver._grid.v.shape


def test_policy_iteration_anderson_runs(boundary):
    config = fjb.Config(
        pi_method="anderson",
        pi_max_iter=4,
        pe_max_iter=2,
        bs_max_iter=4,
        derivative_method="central",
    )
    solver = fjb.Solver(
        boundary=boundary,
        model=SimpleModel(policy=StablePolicy()),
        policy_guess=True,
        number=24,
        config=config,
    )
    state, history = solver.solve()

    assert state.grid.v.shape == solver._grid.v.shape
    assert history.ndim == 1


def test_boundary_search_bisection_runs(solver):
    state = solver.boundary_search(method="bisection", verbose=False)
    assert state.grid.v.shape == solver._grid.v.shape
    assert state.optimal_boundary.shape[0] == 1


def test_boundary_search_hybr_runs(solver):
    state = solver.boundary_search(method="hybr", verbose=False)
    assert state.grid.v.shape == solver._grid.v.shape


def test_boundary_update_requires_model_update_boundary_implementation(solver):
    with pytest.raises(NotImplementedError, match="requires the model class"):
        solver.boundary_update()


def test_boundary_update_runs_when_model_implements_it(updating_solver):
    state, history = updating_solver.boundary_update()
    assert history.shape[0] == updating_solver.config.bs_max_iter
    assert state.grid.v.shape == updating_solver._grid.v.shape


def test_sensitivity_analysis_runs_with_small_parameter_path(solver):
    result = solver.sensitivity_analysis(
        method="bisection",
        param_name="offset",
        param_values=jnp.array([0.1, 0.2]),
    )
    assert result.result["offset"].shape[0] == 2
    assert len(result.grids.data) == 2


def test_newton_raphson_scalar_root_find():
    def residual(params, v, dv, d2v, s, p):
        return jnp.array([params[0] - 1.0])

    solver = NewtonRaphson(residual_fun=residual, maxiter=8, tol=1e-10)
    out = solver.run(
        init_params=jnp.array([0.0]),
        v=jnp.array([0.0]),
        dv=jnp.array([0.0]),
        d2v=jnp.array([0.0]),
        s=jnp.array([0.0]),
        p=SimpleParameter(),
    )
    assert float(out.params[0]) == pytest.approx(1.0)


def test_get_boundary_search_solver_rejects_unknown_method(solver):
    with pytest.raises(ValueError, match="Unknown boundary search method"):
        get_boundary_search_solver(
            method="unknown",  # type: ignore[arg-type]
            config=solver.config,
            policy_iteration=solver.policy_iteration,
            verbose=False,
        )


def test_save_and_load_roundtrip_in_workflow(tmp_path, solver):
    state, _ = solver.solve()
    path = tmp_path / "workflow_grid"
    state.grid.save(path)

    loaded = fjb.load_grid(path)
    assert loaded.s.shape == state.grid.s.shape
