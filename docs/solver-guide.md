# Solver Guide

This guide explains the runtime workflow and solver-related APIs.

## Main Entrypoint

`Solver` coordinates grid initialization and all solving routines.

Constructor highlights:

- `boundary`: `AbstractBoundary` instance
- `model`: `AbstractModel` instance
- `grid`: optional prebuilt `Grid`
- `value_guess`: optional custom initial value guess
- `policy_guess`: whether to use direct policy initialization or run one update first
- `number`: grid size
- `config`: `Config`

If `grid` is provided, `boundary` and `model` are not required.

## Solve Policy Iteration

```python
state, history = solver.solve()
```

Returns:

- `state`: `PolicyIterationState` or `EvaluationState`
- `history`: array of update-step errors

`state.df` provides tabular output.

## Boundary Update

```python
state, history = solver.boundary_update()
```

Uses boundary update algorithm to iteratively adjust boundaries according to model-defined update rules.

## Boundary Search

```python
search_state = solver.boundary_search(method="hybr", verbose=False)
```

Supported `method` values:

- `gauss_newton`
- `lm`
- `broyden`
- `lbfgs`
- `bisection`
- `hybr`
- `broyden1`
- `krylov`

The return type is `BoundarySearchState` with fields such as:

- `grid`
- `optimal_boundary`
- `best_error`
- `converged`
- `iteration`
- `time`

## Sensitivity Analysis

```python
result = solver.sensitivity_analysis(
    method="hybr",
    param_name="sigma",
    param_values=jnp.linspace(0.05, 0.20, 10),
)
```

Returns `SensitivityResult`:

- `result.result`: dictionary of arrays (`param`, `boundary_error`, boundary values)
- `result.df`: pandas DataFrame view
- `result.grids`: solved grid snapshots (`Grids`)

## Configuration (`Config`)

### Grid

- `enable_x64`
- `derivative_method`: `central | forward | backward`

### Policy Iteration

- `policy_guess`
- `pi_method`: `scan | anderson`
- `pi_max_iter`
- `pi_tol`
- `pi_patience`

### Policy Evaluation

- `pe_max_iter`
- `pe_tol`
- `pe_patience`

### Boundary Search

- `bs_max_iter`
- `bs_tol`
- `bs_patience`

### Anderson Acceleration

- `aa_history_size`
- `aa_mixing_frequency`
- `aa_beta`
- `aa_ridge`

## Persistence

- `Grid.save(path)`
- `Grids.save(path)`
- `SensitivityResult.save(path)`
- `fjb.load(path)` to restore objects
