# Solver Guide

This page is the shared workflow reference for the package path, the BCW path, and the Model Coder path.

Read it after [Modeling Guide](./modeling-guide.md) if you are building a model directly, or after [Getting Started](./getting-started.md) if you are still grounding yourself in the repository examples.

Read [Troubleshooting](./troubleshooting.md) instead if the workflow already fails and you need recovery steps more than workflow selection.

## Workflow Decision Table

| Use this workflow | When you should use it | What you get back |
|---|---|---|
| `solve()` | boundaries are already fixed | solved state + per-iteration error history |
| `boundary_update()` | the model can update boundaries from the solved grid | boundary-update state + per-iteration history |
| `boundary_search()` | one or more boundary values must satisfy a numerical contact/value condition | boundary-search state |
| `sensitivity_analysis()` | you want a path of solutions across parameter values | summary table + saved grids |

## `Solver(...)`: Construction Rules

You can initialize the solver in one of two ways:

1. from `boundary + model`,
2. from an existing solved `grid`.

The most common constructor is:

```python
solver = fjb.Solver(
    boundary=boundary,
    model=model,
    policy_guess=True,
    number=500,
    config=fjb.Config(pi_method="scan", derivative_method="central"),
)
```

Important options:

- `policy_guess`: if `True`, trust the policy initializer; if `False`, force an early improvement step.
- `number`: grid size. Larger grids are more accurate but more expensive.
- `config`: all iteration, tolerance, and derivative settings.

## `solve()`: Fixed-Boundary Policy Iteration

Use:

```python
state, history = solver.solve()
```

Best when:

- the problem has no endogenous boundary search,
- you want to debug the core HJB residual before introducing another moving part,
- you want the simplest possible success/failure signal.

Typical return:

- `state`: often a `PolicyIterationState`,
- `history`: a vector of iteration errors.

Useful first checks:

```python
print(type(state).__name__)
print(history.shape)
print(state.df.head())
```

In a typical liquidation fixed-boundary run from this repository:

- the state type is `PolicyIterationState`,
- the history length is around a few dozen iterations,
- the DataFrame columns include `s`, `v`, `dv`, `d2v`, and policy columns.

## `boundary_update()`: Re-Solve While Updating Boundaries

Use:

```python
state, history = solver.boundary_update()
```

Precondition:

- your model implements `update_boundary(grid)`.

This workflow is appropriate when:

- some boundary value is implied by the solved interior grid,
- the boundary can be updated directly from the current solution,
- you want an outer loop over "solve -> update boundary -> solve again."

Example use in the hedging script:

- locate a refinancing target `m` from `p'(m) = 1 + gamma`,
- update the left boundary value from value-matching.

Useful checks:

```python
print(type(state).__name__)
print(history.shape)
print(state.grid.boundary)
```

## `boundary_search()`: Search for a Boundary That Satisfies a Condition

Use:

```python
search_state = solver.boundary_search(method="bisection", verbose=False)
```

This is the core BCW workflow. Use it when:

- one boundary value is not known in advance,
- your model provides one or more `BoundaryConditionTarget` objects,
- you want the solver to search for a value where a contact condition holds.

Supported methods:

- `bisection`
- `hybr`
- `lm`
- `broyden`
- `gauss_newton`
- `lbfgs`
- `krylov`
- `broyden1`

### How The Methods Differ

- `bisection` is the only method that uses `BoundaryConditionTarget.low`, `high`, `tol`, and `max_iter`.
- With `bisection`, every searched target must provide `low` and `high`.
- With multi-boundary `bisection`, the order returned by `model.boundary_condition()` becomes the nested outer-to-inner search order.
- `hybr`, `lm`, `broyden`, `gauss_newton`, `krylov`, and `broyden1` treat the problem as a vector root-search problem and use `Config.bs_tol` and `Config.bs_max_iter`.
- `lbfgs` does not solve the root problem directly. It minimizes the sum of squared residuals and is best treated as a least-squares fallback.

### Practical Starting Rules

- if you have one scalar boundary target and a reliable bracket, start with `bisection`.
- if you have two boundary targets and reliable brackets, `bisection` is still a sensible first default.
- if you have three or more boundary targets and want a robust default, start with `hybr`.
- if the residual map is smooth and naturally least-squares-like, try `lm` or `gauss_newton`.
- if you want a quasi-Newton alternative, try `broyden` or `broyden1`.
- if you only want an approximate residual minimizer, try `lbfgs` last.

These are implementation-level rules of thumb for the current FinHJB search backends. They are good defaults, not universal mathematical guarantees.

For `finhjb-model-coder`, keep one more rule in mind: if the one- or two-target `bisection` default fails the post-generation solve loop, the final generated code should explicitly promote the search method to `hybr` or another supported fallback and record that repair.

### What To Inspect After Boundary Search

```python
state = solver.boundary_search(method="bisection", verbose=False)
grid = state.grid

print(grid.boundary)
print(grid.dv[-1], grid.d2v[-1])
```

For the BCW liquidation example, the high-value diagnostics are:

- solved `s_max` rather than the initial guess,
- `grid.dv[-1]` close to `1`,
- `grid.d2v[-1]` close to `0`.

## `sensitivity_analysis()`: Follow a Parameter Path

Use:

```python
result = solver.sensitivity_analysis(
    method="hybr",
    param_name="sigma",
    param_values=jnp.linspace(0.05, 0.20, 10),
)
```

This workflow is for comparative statics and continuation-style sweeps.

It returns a `SensitivityResult` with:

- `result.df`: summary table across parameter values,
- `result.grids`: a `Grids` container storing the solved grids.

In a small example from this repository, `result.df.columns` include:

- `sigma`,
- `boundary_error`,
- `converged`,
- `s_min`,
- `s_max`,
- `v_left`,
- `v_right`.

That means you can analyze both:

- whether the continuation succeeded numerically,
- how the boundary itself moved as the parameter changed.

## Configuration Tuning

`Config` controls both numerical stability and runtime.

### Good Default Starting Point

For a new model, start simple:

```python
config = fjb.Config(
    derivative_method="central",
    pi_method="scan",
    pi_max_iter=50,
    pi_tol=1e-6,
)
```

Why:

- `central` is usually the safest first derivative scheme,
- `scan` is a straightforward first policy-iteration method,
- moderate tolerances tell you whether the formulation is sane before you spend more time tuning.

### When Not To Use `central`

For theory-to-code work with `finhjb-model-coder`, do not treat `central` as a universal default.

- if the diffusion term becomes very small near the left boundary, prefer `forward`
- if the diffusion term becomes very small near the right boundary, prefer `backward`
- if diffusion stays materially positive at both edges, `central` remains the natural first choice

The point is not stylistic purity. The derivative scheme should reflect where the HJB becomes numerically delicate near the boundaries.

### What To Tune First

If the solve is unstable, adjust in this order:

1. verify the model equations and boundaries,
2. reduce model complexity or use a simpler initial guess,
3. increase `number` only after the base formulation is stable,
4. then tighten tolerances.

If boundary search is unstable:

1. verify the boundary target itself,
2. check the bracket for `bisection`,
3. inspect `grid.dv[-1]` and `grid.d2v[-1]`,
4. only then try a different root-search method.

## Common Failure Modes

### `solve()` runs but the result looks economically strange

Do not immediately blame the solver. First inspect:

- whether `Policy.initialize` is reasonable,
- whether `hjb_residual` signs are correct,
- whether `s_min`, `s_max`, `v_left`, and `v_right` are internally consistent.

### `boundary_search()` does not settle

Most often, one of these is wrong:

- the target function is not the one you actually want,
- the bracket does not contain a sign change,
- the fixed-boundary solve is already unstable before search starts.

### `sensitivity_analysis()` is slow

That is normal when each point requires a full nonlinear solve. Start with a short parameter grid and expand only after you trust the path.

## Next Step

- Read [Results and Diagnostics](./results-and-diagnostics.md) to interpret returned objects.
- Read [Troubleshooting](./troubleshooting.md) if a workflow fails numerically.
- Read [API Reference](./api-reference.md) if you need the full signatures and object members.
