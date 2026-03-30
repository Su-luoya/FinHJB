# Troubleshooting

This page is the shared failure-recovery page for every documentation path.

Read it when something fails or when the output "runs" but does not look trustworthy.

Read [Installation and Environment](./installation-and-environment.md) instead if you are setting up for the first time rather than debugging a failure.

The best troubleshooting habit in FinHJB is to separate three layers:

1. environment problems,
2. modeling mistakes,
3. numerical configuration problems.

If you mix them together, it becomes hard to tell whether the problem is import-related, equation-related, or solver-related.

## Quick Triage

| Symptom | Most likely layer | First page to pair with this one |
|---|---|---|
| import fails before solving starts | environment | [Installation and Environment](./installation-and-environment.md) |
| example runs but boundary diagnostics look wrong | numerical workflow | [Results and Diagnostics](./results-and-diagnostics.md) |
| your custom model raises key or shape errors | model implementation | [Modeling Guide](./modeling-guide.md) |
| you are unsure whether to use `solve`, `boundary_update`, or `boundary_search` | workflow choice | [Solver Guide](./solver-guide.md) |

## Environment Failures

### `ModuleNotFoundError: No module named 'finhjb'`

Cause:

- you are running `python` directly instead of the project environment,
- or the package was not installed.

First fix:

```bash
uv sync
uv run python -c "import finhjb as fjb; print(fjb.__all__[:5])"
```

### `ModuleNotFoundError: No module named 'jax'`

Cause:

- dependencies are missing in the active environment.

First fix:

```bash
uv sync
```

If you were using plain `python`, switch to `uv run python`.

### Matplotlib display / backend errors

Typical symptom:

- the script imports successfully and then crashes on display or backend setup.

First fix:

```bash
export MPLBACKEND=Agg
MPLBACKEND=Agg uv run python src/example/BCW2011Liquidation.py
```

## Loader Errors

### `TypeError` when using `load_grid`, `load_grids`, or `load_sensitivity_result`

Cause:

- the file was saved as one type but loaded with the wrong loader.

Correct mapping:

| Saved with | Load with |
|---|---|
| `state.grid.save(path)` | `load_grid(path)` |
| `result.grids.save(path)` | `load_grids(path)` |
| `result.save(path)` | `load_sensitivity_result(path)` |

The loaders validate types on load, so a wrong pairing fails loudly by design.

## Workflow Selection Errors

### `NotImplementedError: Solver.boundary_update() requires the model class to implement update_boundary(grid)`

Cause:

- `boundary_update()` was called on a model that does not implement `Model.update_boundary(grid)`.

What to do:

- use `solve()` if boundaries are fixed,
- use `boundary_search()` if you want a root/search condition,
- implement `update_boundary(grid)` only if your model has an explicit outer update rule.

This is not a solver bug. It is the guardrail for the boundary-update workflow.

## Boundary Search Problems

### `boundary_search()` returns but `grid.d2v[-1]` is not close to zero

This usually means one of the following:

1. the target condition is wrong,
2. the fixed-boundary solve is already unstable,
3. the search bracket is poor,
4. the grid is too coarse to resolve the right tail cleanly.

Check in this order:

```python
print(grid.dv[-1], grid.d2v[-1])
print(grid.boundary)
```

Then ask:

- does the target in `boundary_condition()` really encode the desired contact condition?
- does the fixed-boundary solve behave reasonably before search?
- for bisection, does the bracket plausibly contain the root?

### Bisection does not settle

Most common causes:

- the lower and upper bounds are not economically meaningful,
- the target does not switch sign over the bracket,
- the model equations are mis-specified, so no sensible root exists in that range.

What to try:

1. inspect the target value at a few candidate boundaries manually,
2. narrow the bracket around a region that looks economically plausible,
3. confirm the base `solve()` problem is stable before searching.

## Policy Iteration Problems

### The run finishes, but policy values look surprising

Do not assume "surprising" means "wrong."

For BCW:

- liquidation investment is strongly negative at low cash,
- hedging `psi` is pinned at `-pi` in distressed states,
- positive investment only appears toward the healthier right side of the grid.

Before editing the code, compare your pattern to:

- [BCW Liquidation Walkthrough](./bcw2011-liquidation-walkthrough.md)
- [BCW Refinancing Walkthrough](./bcw2011-refinancing-walkthrough.md)
- [BCW Hedging Walkthrough](./bcw2011-hedging-walkthrough.md)
- [BCW Credit Line Walkthrough](./bcw2011-credit-line-walkthrough.md)

Also remember the case-specific patterns:

- refinancing should raise `p(0)` above liquidation value and create an interior issuance target `m`,
- credit lines can push `p'(0)` close to `1` and keep investment positive around `w=0`,
- frictionless hedging should move the payout boundary left relative to costly margin.

### Convergence is slow or unstable

Things to adjust in order:

1. verify equations and boundary formulas,
2. simplify the initial policy guess,
3. reduce ambition and get a smaller, stable baseline run first,
4. only then change `number`, tolerances, or search method.

Changing tolerances before checking the economics usually wastes time.

## Derivative and Grid Problems

### `dv` or `d2v` looks explosive

Possible causes:

- the value function is not being solved consistently,
- the grid is too coarse in a region with sharp curvature,
- denominators such as `dv` or `d2v` are used unstably in policy formulas,
- boundaries are inconsistent with the economics.

What to inspect:

```python
df = grid.df
print(df[["s", "v", "dv", "d2v"]].head())
print(df[["s", "v", "dv", "d2v"]].tail())
```

Questions to ask:

- is `v` increasing with cash?
- is `dv[-1]` approaching the right-boundary target?
- is `d2v[-1]` moving toward zero when it should?
- are the extreme values confined to the left tail, or are they everywhere?

### When should I increase `number`?

Increase the grid size after the formulation is already sensible, not before.

Good reason:

- the curves are qualitatively correct but too jagged.

Bad reason:

- the model does not converge at all and you have not checked the equations.

## `policy_guess` Confusion

### Why does changing `policy_guess` affect convergence?

Because it changes the starting point.

- `policy_guess=True` means "use the initializer exactly as the initial policy."
- `policy_guess=False` means "construct a policy container, then immediately push it through an improvement step."

If your initializer is already strong, `True` may converge faster.
If your initializer is weak or economically poor, `False` can rescue the run.

## `grid.aux` Raises `NotImplementedError`

Cause:

- `Grid.aux` calls `Model.auxiliary(grid)`,
- and your model has not implemented that optional hook.

This is expected behavior.

What to do:

- ignore `grid.aux` until you actually need custom diagnostics,
- or implement `auxiliary(grid)` in your model.

## A Good Minimal Debugging Loop

When your custom model fails, debug in this order:

1. `uv run python -c "import finhjb"` to confirm environment,
2. get `solver.solve()` working on fixed boundaries,
3. inspect `state.df.head()` and `state.df.tail()`,
4. only then add `boundary_update()` or `boundary_search()`,
5. only after that run sensitivity analysis.

This sequence prevents "stacked failures" where multiple moving parts hide the real problem.

## When To Stop Debugging And Rethink The Formulation

Step back and re-check the model if:

- the right boundary never approaches its intended contact condition,
- different search methods all fail in similar ways,
- the policy formulas require dividing by values that routinely approach zero,
- the solution shape is economically implausible everywhere, not just at one tail.

That usually signals a formulation problem, not a tuning problem.

## Next Step

- Return to [Getting Started](./getting-started.md) if you want to re-run the BCW baseline cleanly.
- Read [Results and Diagnostics](./results-and-diagnostics.md) if the solve now runs and you need to inspect it.
- Read [Modeling Guide](./modeling-guide.md) if the real issue is in your custom model design.
