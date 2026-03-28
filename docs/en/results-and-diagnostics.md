# Results and Diagnostics

This page is the shared diagnostics reference for the package path and the BCW path.

Read it after [Library Quickstart](./quickstart-library.md) or [Getting Started](./getting-started.md), once you already have a solve and want to inspect it cleanly.

Read [API Reference](./api-reference.md) instead if you only need exact object members.

The main purpose is to help you answer:

- what object did the solver return?
- which attributes are always safe to inspect?
- what does a "healthy" solution look like numerically?
- which symptoms point to modeling errors versus numerical tuning issues?

## Read This After

- [Library Quickstart](./quickstart-library.md)
- [Getting Started](./getting-started.md)
- [BCW2011 Liquidation Walkthrough](./bcw2011-liquidation-walkthrough.md)
- [BCW2011 Hedging Walkthrough](./bcw2011-hedging-walkthrough.md)

## Solver Return Types

In this repository, representative runs produced the following return objects:

| Workflow | Return object | Typical companion output |
|---|---|---|
| `solve()` | `PolicyIterationState` | `history` array of update errors |
| `boundary_update()` | `BoundaryUpdateState` | `history` array of boundary-update errors |
| `boundary_search()` | `BoundarySearchState` | solved grid plus search diagnostics |
| `sensitivity_analysis()` | `SensitivityResult` | summary DataFrame plus `Grids` collection |

Examples:

```python
state, history = solver.solve()
print(type(state).__name__)
print(len(history))
```

```python
search_state = solver.boundary_search(method="bisection", verbose=False)
print(type(search_state).__name__)
print(search_state.grid.boundary)
```

## The Most Useful Objects

## `state.grid`

This is the full solved grid object. For most practical inspection, it is the first thing to grab.

```python
grid = state.grid
```

Useful members:

- `grid.boundary`
- `grid.s`
- `grid.v`
- `grid.dv`
- `grid.d2v`
- `grid.policy`
- `grid.df`

## `state.df`

Every solver state exposes:

```python
print(state.df.head())
print(state.df.tail())
```

This is a convenience wrapper for `state.grid.df`.

Representative `solve()` output columns in this repository start with:

```text
['s', 'v', 'dv', 'd2v', 'investment']
```

If your model has more controls, you will see more columns.

## `history`

For `solve()` and `boundary_update()`, the second returned object is a history array.

Interpretation:

- it records per-iteration error magnitudes,
- it helps distinguish "failed immediately" from "converged slowly,"
- it is useful for comparing two configurations.

Do not confuse `history` with the actual economic solution. It is an iteration diagnostic, not the value function itself.

## `grid.boundary`

This is the cleanest place to read the solved boundary values:

```python
print(grid.boundary)
```

For the BCW examples, healthy representative outputs look like:

```text
ImmutableBoundary(s_min=0.0, s_max=0.22176666, v_left=0.9, v_right=1.380003)
ImmutableBoundary(s_min=0.0, s_max=0.13850403, v_left=1.16119385, v_right=1.31352204)
```

The point is not exact replication. The point is to recognize the right order of magnitude and the right boundary relationships.

## `grid.df`: Column-By-Column Interpretation

| Column | Meaning | Why you should care |
|---|---|---|
| `s` | state grid | tells you where you are in cash-space |
| `v` | value-capital ratio | the solved value function |
| `dv` | first derivative | marginal value of cash |
| `d2v` | second derivative | curvature and right-boundary contact diagnostic |
| `investment` | investment policy | shows how real decisions vary with cash |
| `psi` | hedge policy in hedging case | shows constrained vs interior vs zero hedge regions |

## The Three Highest-Value Diagnostics

If you are short on time, inspect these first:

1. `grid.boundary`
2. `grid.df.tail()`
3. `grid.d2v[-1]`

Why these three:

- `grid.boundary` tells you what problem was actually solved,
- the tail tells you whether the payout-side boundary behavior looks right,
- `grid.d2v[-1]` directly tests the BCW contact condition.

## Boundary Diagnostics

### Left boundary

Ask:

- does `v[0]` match the intended left-boundary condition?
- in liquidation, is it near the liquidation value?
- in hedging, is it higher once refinancing is active?

### Right boundary

Ask:

- is `dv[-1]` approaching the intended payout-side slope?
- is `d2v[-1]` approaching zero?
- does the last part of the curve approach the boundary smoothly?

For the BCW examples, a healthy tail looks like "close to the expected slope, and curvature numerically vanishing."

## Policy Diagnostics

### Investment

Typical BCW interpretation:

- low cash: investment is sharply reduced or negative,
- middle region: investment recovers,
- right tail: investment becomes mildly positive.

You are looking for a smooth economic pattern, not a perfectly linear curve.

### Hedge policy (`psi`)

In the hedging case:

- low cash: `psi` should bind at `-pi`,
- middle region: interior values should appear,
- high cash: `psi` should go to `0`.

If all three regions are absent, re-check the hedging implementation.

## `grid.aux`: Optional, Not Guaranteed

`grid.aux` calls the model's optional `auxiliary(grid)` hook.

Important consequence:

- if your model does not implement `auxiliary(grid)`, `grid.aux` raises `NotImplementedError`.

So the safe default diagnostics are:

- `grid.boundary`,
- `grid.df`,
- `history`,
- saved `Grid` / `Grids` / `SensitivityResult`.

Only use `grid.aux` after your model explicitly defines custom auxiliary outputs.

A robust pattern is to let `auxiliary(grid)` return a small dictionary of derived summaries, for example:

```python
@staticmethod
def auxiliary(grid: fjb.Grid):
    return {"value_mean": jnp.mean(grid.v)}
```

## Sensitivity Analysis Results

`sensitivity_analysis()` returns a `SensitivityResult`:

```python
result = solver.sensitivity_analysis(
    method="hybr",
    param_name="sigma",
    param_values=...,
)
```

Two objects matter immediately:

- `result.df`
- `result.grids`

Representative columns from this repository:

```text
['sigma', 'boundary_error', 'converged', 's_min', 's_max', 'v_left', 'v_right']
```

Interpretation:

- `result.df` is the continuation summary,
- `result.grids` stores the full solved grid at each parameter value.

Representative grid keys:

```text
[0.08, 0.09]
```

That means you can inspect both:

- how the boundary moved across parameters,
- what the full value/policy objects looked like at each point.

## Save, Reload, Re-Inspect

Recommended patterns:

```python
state.grid.save("outputs/liquidation_grid")
grid = fjb.load_grid("outputs/liquidation_grid")
print(grid.df.tail())
```

```python
result.save("outputs/sigma_result")
loaded = fjb.load_sensitivity_result("outputs/sigma_result")
print(loaded.df)
```

This is especially useful when your solve is expensive and you want to separate "solving" from "interpreting."

## Symptom -> Likely Cause -> First Action

| Symptom | Likely cause | First action |
|---|---|---|
| `d2v[-1]` not near zero | wrong boundary target or unstable search | inspect `boundary_condition()` and tail diagnostics |
| `dv[-1]` far from expected slope | inconsistent right boundary | inspect `grid.boundary` and boundary formulas |
| `investment` oscillates wildly | unstable policy update or coarse grid | verify equations before increasing `number` |
| `psi` never leaves `-pi` | hedge logic never enters interior region | inspect clipping and `should_hedge` logic |
| `grid.aux` fails | optional hook not implemented | ignore `aux` or implement `auxiliary(grid)` |
| `history` flatlines at large error | formulation likely wrong, not merely slow | simplify to a fixed-boundary baseline solve |

## A Minimal BCW Diagnostic Script

```python
grid = state.grid

print(grid.boundary)
print(grid.df.head())
print(grid.df.tail())
print("right slope:", grid.dv[-1])
print("right curvature:", grid.d2v[-1])
```

If you are unsure where to start, this small block gives the highest information per line of code.

## When You Should Stop Tuning And Re-Read The Model

Stop adjusting tolerances and go back to the equations if:

- the solution is economically implausible across the entire grid,
- different solvers all fail in similar ways,
- the boundary conditions do not match the story of the model,
- your diagnostics contradict the paper's qualitative shape.

That is usually a modeling issue, not a numerical fine-tuning issue.

## Next Step

- Read [Solver Guide](./solver-guide.md) if you want to choose the right workflow for your own model.
- Read [Adapting BCW to Your Model](./adapting-bcw-to-your-model.md) if you are ready to migrate away from the BCW baselines.
- Read [Troubleshooting](./troubleshooting.md) if the diagnostics already tell you the solve is unhealthy.
