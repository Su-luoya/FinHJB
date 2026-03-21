# Solver Guide

## Solver Construction

`Solver` can be initialized either from:

- `boundary + model`, or
- an existing `grid`.

Common options:

- `policy_guess`: use policy initializer directly (`True`) or run one policy update first (`False`)
- `number`: grid size (`>= 4`)
- `config`: convergence and differentiation settings

## Policy Iteration

```python
state, history = solver.solve()
```

Returns final state plus per-iteration update history.

## Boundary Update

```python
state, history = solver.boundary_update()
```

Precondition: model must implement `update_boundary(grid)`.

## Boundary Search

```python
search_state = solver.boundary_search(method="hybr", verbose=False)
```

Supported methods:

- `gauss_newton`
- `lm`
- `broyden`
- `lbfgs`
- `bisection`
- `hybr`
- `broyden1`
- `krylov`

## Sensitivity Analysis

```python
result = solver.sensitivity_analysis(
    method="hybr",
    param_name="sigma",
    param_values=jnp.linspace(0.05, 0.20, 10),
)
```

## Config Highlights

- `derivative_method`: `central | forward | backward`
- `pi_method`: `scan | anderson`
- `pe_*`, `pi_*`, `bs_*`, `aa_*`
