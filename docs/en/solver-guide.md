# Solver Guide

Use this page when the equations are already on the page and the remaining question is numerical workflow: `solve()`, `boundary_update()`, `boundary_search()`, or `sensitivity_analysis()`.

Read it after [Modeling Guide](./modeling-guide.md) for direct model construction, or after [Getting Started](./getting-started.md) once the repository examples are running. If the workflow already fails and you mainly need recovery steps, go straight to [Troubleshooting](./troubleshooting.md).

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

## How FinHJB Solves a One-Dimensional HJB

The table above tells you which workflow to call. This section fills in the missing layer: what those workflows are actually doing to a one-dimensional HJB.

At the most abstract level, the repository solves problems of the form

$$
0 = \sup_{\pi \in \Pi} \mathcal{H}\bigl(V(s), V_s(s), V_{ss}(s), s; \pi\bigr),
$$

where the control can be scalar or vector-valued. If the model has a jump term, the implementation passes it into `Model.hjb_residual(...)` separately as `jump`.

### Step 1: Discretize The Continuous Problem On The Interior Grid

`Grid.reset()` first discretizes the state interval as

$$
s_0 = s_{\min} < s_1 < \cdots < s_{N-2} < s_{N-1} = s_{\max},
$$

then fixes the boundary values

$$
v_0 = v_{\text{left}}, \qquad v_{N-1} = v_{\text{right}},
$$

so the actual unknown solved by iteration is the interior vector

$$
v_{\text{inter}} = (v_1, \dots, v_{N-2}).
$$

At each interior point $s_i$, the code builds a discrete residual

$$
F_i(v_{i-1}, v_i, v_{i+1}; \pi_i) = 0.
$$

For the first derivative, the current implementation uses the scheme selected by `Config.dv_func`, with central difference as the default:

$$
D_h v_i = \frac{v_{i+1} - v_{i-1}}{2h}.
$$

For the second derivative, it uses the centered stencil

$$
D_{hh} v_i = \frac{v_{i+1} - 2v_i + v_{i-1}}{h^2}.
$$

When `Grid.update_with_v_inter()` reconstructs the full `v`, `dv`, and `d2v`, it also computes boundary derivatives with second-order one-sided stencils, so the reported boundary diagnostics and the interior solve remain consistent:

```python
v = [v_left, *v_inter, v_right]
dv = [left one-sided, dv_func(interior), right one-sided]
d2v = [left one-sided, centered interior, right one-sided]
```

That is why the main numerical unknown in FinHJB is not the full `v` array but `v_inter` with fixed endpoint values.

### Step 2: Hold Policy Fixed And Run Policy Evaluation

Given a current policy $\pi$, `PolicyEvaluation` solves the discrete fixed-policy HJB system

$$
F(v; \pi) = 0.
$$

The implementation does not treat this as a naive pointwise replacement rule. It takes Newton-style steps:

$$
J(v^{(k)}; \pi)\,\Delta v^{(k)} = -F(v^{(k)}; \pi),
\qquad
v^{(k+1)} = v^{(k)} + \Delta v^{(k)}.
$$

The Jacobian is tridiagonal because each $F_i$ depends only on the neighboring triple $(v_{i-1}, v_i, v_{i+1})$. In code, this maps to:

- `residual_pointwise(...)`: evaluates `Model.hjb_residual(...)` at one interior point;
- `jax.jacrev(..., argnums=(0, 1, 2))`: obtains $\partial F_i / \partial v_{i-1}$, $\partial F_i / \partial v_i$, and $\partial F_i / \partial v_{i+1}$;
- `jax.vmap(...)`: applies that local system across all interior points;
- `jax.lax.linalg.tridiagonal_solve(...)`: solves the Newton step.

Mechanically, the update is:

```python
residuals, dl, d, du = vmapped_pointwise_system(grid)
dv_update = tridiagonal_solve(dl, d, du, -residuals)
grid = grid.replace(v_inter=grid.v_inter + dv_update)
```

`EvaluationState` stores the numerical status of that inner loop, including:

- `hjb_residuals`: pointwise residuals on the interior grid;
- `last_update_step`: the norm of the latest Newton step;
- `best_error` and `patience_counter`: whether the iteration is still improving;
- `converged`: whether the loop met `pe_tol`.

Stopping is defined at this layer: the loop stops when the update norm falls below `pe_tol`, or when improvement stalls for `pe_patience` rounds.

### Step 3: Update Policy And Run Policy Improvement

The outer `PolicyIteration` loop is:

1. hold the current policy fixed and run policy evaluation;
2. update the policy using the new `v`, `dv`, and `d2v`;
3. check whether the policy change is already small enough.

Mathematically, this is

$$
v^{k+1} = \operatorname{Eval}(\pi^k), \qquad
\pi^{k+1} = \operatorname{Improve}(v^{k+1}),
$$

until

$$
\max_j \lVert \pi^{k+1}_j - \pi^k_j \rVert
$$

falls below `pi_tol`.

Implementation-wise, `AbstractPolicy.update()` executes two kinds of ordered policy steps:

- `@explicit_policy`: closed-form updates that write directly into `grid.policy[...]`;
- `@implicit_policy`: FOCs written as local nonlinear root problems at each grid point.

For the latter, the current repository supports pointwise `GaussNewton`, `Broyden`, `LevenbergMarquardt`, and the custom `NewtonRaphson`. So policy improvement is not a hard-coded formula. It is whatever inverse mapping from value derivatives to controls the `Policy` class declares.

`PolicyIteration` currently exposes two backends:

- `scan`: an explicit evaluation $\rightarrow$ improvement loop with a full history of outer errors;
- `anderson`: the same fixed-point map, but accelerated as a `grid -> next_grid` fixed-point problem.

In both cases, the default outer-loop error is the maximum norm across policy-array changes.

### Step 4: If The Boundary Is Unknown, Wrap It As Boundary Search

When the boundary itself is unknown, FinHJB does not merge boundary updates into policy iteration. Instead it builds an outer residual map

$$
G(b) = C\bigl(\mathrm{Solve}(b)\bigr),
$$

where $b$ is the candidate boundary vector, `Solve(b)` means "solve the interior HJB under that boundary," and $C$ comes from `BoundaryConditionTarget.condition_func`.

The actual `_create_objective_func(...)` pipeline inside `boundary_search()` is:

1. overwrite the searched boundary fields with the candidate `b`;
2. call `reset()` to rebuild the grid, value guess, and policy start;
3. run the inner HJB solver;
4. re-read `boundary_condition()` on the solved grid;
5. evaluate each target residual and return both the residual vector and the solved grid.

The code skeleton is:

```python
def residual_func(boundary_params):
    boundary = initial_grid.boundary.update_boundaries(...)
    temp_grid = initial_grid.replace(boundary=boundary).reset()
    pi_state, _ = inner_func(temp_grid)
    solved_grid = pi_state.grid
    residuals = jnp.array([
        target.condition_func(solved_grid) for target in final_targets
    ])
    return residuals, solved_grid
```

So `boundary_search()` is solving an outer zero-residual boundary problem, not modifying the HJB algebra itself.

### Step 5: What The Boundary Search Methods Are Actually Doing

The current methods fall into three algorithmic roles:

- `bisection`: scalar bracket search. With multiple targets, the implementation performs nested recursion in the order returned by `boundary_condition()`, so that list order is also the outer-to-inner search order. It uses each target's own `low`, `high`, `tol`, and `max_iter`.
- `hybr`, `broyden`, `broyden1`, `krylov`: vector root solvers for $G(b)=0$, all controlled by `Config.bs_tol` and `Config.bs_max_iter`.
- `lm`, `gauss_newton`, `lbfgs`: least-squares-style methods. The first two use the residual map in least-squares form, while `lbfgs` minimizes $\sum_k G_k(b)^2$, so it is not a direct root solver in the strict sense.

So switching methods inside `boundary_search()` means switching how the outer boundary residual is solved, not switching how the interior HJB is discretized.

### How `boundary_update()` Differs From `boundary_search()`

Both workflows let boundaries move, but they are not solving the same outer problem.

`boundary_search()` solves

$$
G(b) = 0,
$$

which means "find a boundary that makes a contact or smooth-pasting condition hold."

`boundary_update()` is different. It does not run a root search on a residual map. It expects the model to return

```python
boundary_dict, boundary_error = model.update_boundary(grid)
```

so its outer logic is closer to:

1. solve under the current boundary;
2. read off a new boundary directly from the solved grid;
3. use `boundary_error` to decide whether to continue.

If the solved grid directly implies what the next boundary should be, `boundary_update()` is the natural workflow. If you only know that some boundary condition must equal zero, use `boundary_search()`.

## `solve()`: Fixed-Boundary Policy Iteration

Use:

```python
state, history = solver.solve()
```

If you want the discretization and inner/outer iteration logic behind this call first, read the section above: [How FinHJB Solves a One-Dimensional HJB](#how-finhjb-solves-a-one-dimensional-hjb).

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

If you want to see how a candidate boundary becomes a residual map for an outer search solver, read the section above: [How FinHJB Solves a One-Dimensional HJB](#how-finhjb-solves-a-one-dimensional-hjb).

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

## Related Pages

- Read [Results and Diagnostics](./results-and-diagnostics.md) to interpret returned objects.
- Read [Troubleshooting](./troubleshooting.md) if a workflow fails numerically.
- Read [API Reference](./api-reference.md) if you need the full signatures and object members.
