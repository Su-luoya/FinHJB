# Modeling Guide

Read this page when you are ready to move from "I can run BCW" to "I can define my own model with the FinHJB abstractions."

If you have not yet reproduced the baseline examples, go back to [Getting Started](./getting-started.md). If you want a concrete migration recipe, pair this page with [Adapting BCW to Your Model](./adapting-bcw-to-your-model.md).

## The Four Core Components

Every FinHJB model is built from four ideas:

1. `AbstractParameter`: immutable economic or numerical parameters.
2. `AbstractBoundary`: state/value boundary values and their dependencies.
3. `AbstractPolicy`: how controls are initialized and updated.
4. `AbstractModel`: the HJB residual plus optional boundary helpers.

The best way to think about them is:

- `Parameter` says what the world is,
- `Boundary` says where the world starts and ends,
- `Policy` says what the agent chooses,
- `Model` says what equation must equal zero.

## `AbstractParameter`: Immutable Inputs

Use `AbstractParameter` for values that should be treated as part of the model specification.

Typical contents:

- discount rates,
- depreciation,
- volatility,
- adjustment-cost coefficients,
- financing friction parameters.

Example:

```python
class Parameter(fjb.AbstractParameter):
    r: float = 0.03
    sigma: float = 0.15
```

Good practice:

- keep fields numeric and immutable,
- use descriptive names,
- use `cached_property` for derived quantities,
- override `update(boundary)` only if boundary changes should update parameter-dependent derived values.

Common mistakes:

- putting mutable containers into parameters,
- hiding important model constants inside the policy or model class,
- forgetting that `update(boundary)` exists when a boundary change should alter a derived parameter.

## `AbstractBoundary`: All State and Value Endpoints

The boundary object manages:

- `s_min`,
- `s_max`,
- `v_left`,
- `v_right`.

You may provide boundaries in two ways:

1. directly in the constructor,
2. indirectly through `compute_<boundary_name>` methods.

Example:

```python
@dataclass
class Boundary(fjb.AbstractBoundary[Parameter]):
    @staticmethod
    def compute_v_left(p: Parameter) -> float:
        return 0.0

    @staticmethod
    def compute_v_right(p: Parameter, s_max: float) -> float:
        return 1.0 + 0.1 * s_max
```

How dependency inference works:

- the method name decides which boundary is being computed,
- the method signature decides which other boundaries it depends on,
- `p` is treated as the parameter object rather than another boundary.

That means `compute_v_right(p, s_max)` says: "to compute `v_right`, I need `p` and `s_max`."

### Boundary Rules To Remember

- Never provide both an explicit value and a `compute_*` method for the same boundary.
- `s_min < s_max` must hold.
- Circular dependencies are rejected.
- Missing dependencies are rejected early.

### When To Use `boundary_condition()`

Use `Model.boundary_condition()` when one or more boundary values must be chosen so that a numerical condition holds at the solved grid.

BCW uses this for the payout-side contact condition:

```python
def s_max_condition(grid) -> float:
    return grid.d2v[-1]
```

That tells the solver to search for a boundary where the right-tail curvature goes to zero.

In practice, `boundary_condition()` returns a list of `BoundaryConditionTarget` objects. That list does more than name the condition:

- only boundaries appearing in the list are optimized by `boundary_search()`,
- the list order defines the boundary-parameter order for multi-boundary searches,
- for `method="bisection"`, the same order becomes the nested outer-to-inner search order,
- `low` and `high` are required if you want `bisection`,
- `tol` and `max_iter` on the target are also specific to `bisection`.

For all the other boundary-search methods, the solver instead uses `Config.bs_tol` and `Config.bs_max_iter`.

## `AbstractPolicyDict`: Declare Control Variables

`AbstractPolicyDict` is the typed container for policy arrays.

Example:

```python
class PolicyDict(fjb.AbstractPolicyDict):
    investment: Array
    psi: Array
```

Rule of thumb:

- include every control or auxiliary policy array that later code will read from `grid.policy`.

If a variable appears in `Model.hjb_residual`, it usually belongs here.

## `AbstractPolicy`: Initialization and Policy Updates

The policy class has two main jobs:

1. create an initial guess,
2. update controls during iteration.

### `initialize(grid, p)`

This must return a full `PolicyDict`.

Checklist:

- every required key is present,
- every value has grid-compatible shape,
- the initial guess is numerically reasonable.

### `@explicit_policy`

Use this when the policy update can be written directly in closed form.

Example:

```python
@staticmethod
@fjb.explicit_policy(order=1)
def update_investment(grid: fjb.Grid) -> fjb.Grid:
    grid.policy["investment"] = ...
    return grid
```

Use explicit updates when:

- the FOC can be solved algebraically,
- the update is simple and stable,
- you want the easiest code path.

### `@implicit_policy`

Use this when the policy is defined by a residual equation or root problem.

BCW liquidation uses this form for the investment FOC:

```python
@staticmethod
@fjb.implicit_policy(order=2, solver="lm", policy_order=["investment"])
def cal_investment_without_explicit(policy, v, dv, d2v, s, p):
    investment = policy[0]
    return jnp.array([(1 / p.theta) * (v / dv - s - 1) - investment])
```

Use implicit updates when:

- the policy is most naturally written as `FOC(...) = 0`,
- you need a nonlinear root solver,
- you want a uniform residual-based implementation.

### Common Policy Mistakes

- returning only one control while the model expects two,
- using the wrong `policy_order` in implicit updates,
- forgetting to return the grid from explicit updates,
- writing unstable formulas without guarding denominators such as `dv` or `d2v`.

## `AbstractModel`: The HJB Residual

The minimum requirement is:

```python
hjb_residual(v, dv, d2v, s, policy, jump, boundary, p)
```

This function should return the pointwise residual on the interior grid. The solver wants that residual to approach zero.

Typical inputs:

- `v`, `dv`, `d2v`: the current value function and derivatives,
- `s`: the state grid,
- `policy`: the current control arrays,
- `jump`: optional jump term,
- `boundary`: frozen boundary values,
- `p`: parameters.

Optional model hooks:

- `jump(...)`: for problems with non-zero jump terms,
- `boundary_condition()`: for boundary-search targets,
- `update_boundary(grid)`: for iterative boundary update workflows,
- `auxiliary(grid)`: for user-defined diagnostics.

### When To Override `jump(...)`

Most models do not need this. The default implementation is zero.

Override it only if your HJB contains an extra jump term. The solver evaluates the hook through `Grid.jump_inter`, so in practice it is called on the interior-grid slices rather than the full boundary-including arrays.

### What `boundary_condition()` Should Return

The return value is a list of `BoundaryConditionTarget(...)` objects.

Each target provides:

- `boundary_name`: which field such as `s_max` or `v_left` should be searched,
- `condition_func(grid)`: the residual to drive toward zero,
- `low` / `high`: the bracket for `bisection`,
- `tol` / `max_iter`: per-target settings for `bisection`.

If you use `hybr`, `lm`, `broyden`, `gauss_newton`, `krylov`, `broyden1`, or `lbfgs`, the search instead uses `Config.bs_tol` and `Config.bs_max_iter`.

### What `auxiliary(grid)` Is For

`auxiliary(grid)` is the hook behind `grid.aux`.

Use it only when you want extra derived diagnostics that are not already in `grid.df` or `grid.boundary`. A simple and robust pattern is to return a dictionary:

```python
@staticmethod
def auxiliary(grid: fjb.Grid):
    return {"value_mean": jnp.mean(grid.v)}
```

If you leave it unimplemented, `grid.aux` raising `NotImplementedError` is normal.

## A Good Implementation Order

When building a new model, do it in this order:

1. define `Parameter`,
2. define `Boundary`,
3. define `PolicyDict`,
4. write `Policy.initialize`,
5. write a first version of `Model.hjb_residual`,
6. get `solver.solve()` running on a fixed boundary,
7. only then add `boundary_condition()` or `update_boundary()` if needed.

That order keeps debugging local. If you start with boundary search before the base solve works, you usually create two problems at once.

## Minimal Template

```python
class Parameter(fjb.AbstractParameter):
    r: float = 0.03


class PolicyDict(fjb.AbstractPolicyDict):
    investment: Array


@dataclass
class Boundary(fjb.AbstractBoundary[Parameter]):
    @staticmethod
    def compute_v_left(p: Parameter) -> float:
        return 0.0

    @staticmethod
    def compute_v_right(p: Parameter, s_max: float) -> float:
        return 1.0 + 0.1 * s_max


@dataclass
class Policy(fjb.AbstractPolicy[Parameter, PolicyDict]):
    @staticmethod
    def initialize(grid: fjb.Grid, p: Parameter) -> PolicyDict:
        return PolicyDict(investment=jnp.full_like(grid.s, 0.1))


@dataclass
class Model(fjb.AbstractModel[Parameter, PolicyDict]):
    @staticmethod
    def hjb_residual(v, dv, d2v, s, policy, jump, boundary, p):
        inv = policy["investment"]
        return -p.r * v + (s - inv) * dv + 0.5 * p.sigma**2 * d2v
```

## When To Leave This Page

- Go to [Solver Guide](./solver-guide.md) if you now want to choose a workflow.
- Go to [Adapting BCW to Your Model](./adapting-bcw-to-your-model.md) if you want a migration checklist.
- Go to [API Reference](./api-reference.md) if you want every method and property in one place.
