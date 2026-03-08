# Modeling Guide

This document describes how to implement problem-specific components required by FinHJB.

## Core Interfaces

You must provide four pieces:

1. `AbstractParameter`
2. `AbstractBoundary`
3. `AbstractPolicy`
4. `AbstractModel`

## Parameter

`AbstractParameter` is a Flax PyTree node and should contain immutable model parameters.

Pattern:

```python
class Parameter(fjb.AbstractParameter):
    r: float = 0.06
    sigma: float = 0.10
```

If needed, override `update(self, boundary)` to sync derived quantities with boundary updates.

## Boundary

`AbstractBoundary` supports mixed modes:

- direct values provided at construction
- computed values via `compute_<name>` methods

Example:

```python
@dataclass
class Boundary(fjb.AbstractBoundary[Parameter]):
    @staticmethod
    def compute_s_max(p: Parameter) -> float:
        return 0.25

    @staticmethod
    def compute_v_right(p: Parameter, s_max: float) -> float:
        return 1.0 + s_max
```

Rules:

- Do not provide both a direct value and a compute method for the same boundary.
- Dependencies are inferred from method arguments.
- Circular dependencies raise an error.

## Policy

### Policy dictionary

Declare all policy variables used in your model.

```python
class PolicyDict(fjb.AbstractPolicyDict):
    investment: Array
    hedge: Array
```

### Initialization

`initialize(grid, p)` must return all required keys.

```python
@staticmethod
def initialize(grid: fjb.Grid, p: Parameter) -> PolicyDict:
    return PolicyDict(
        investment=jnp.full_like(grid.s, 0.1),
        hedge=jnp.zeros_like(grid.s),
    )
```

### Explicit update

Use for closed-form policy updates.

```python
@staticmethod
@fjb.explicit_policy(order=1)
def update_investment(grid: fjb.Grid) -> fjb.Grid:
    grid.policy["investment"] = ...
    return grid
```

### Implicit update

Use for first-order conditions solved numerically.

```python
@staticmethod
@fjb.implicit_policy(
    order=2,
    solver="lm",
    policy_order=["investment"],
    maxiter=20,
    tol=1e-8,
)
def foc(policy, v, dv, d2v, s, p):
    investment = policy[0]
    return jnp.array([your_equation(investment, v, dv, d2v, s, p)])
```

Supported implicit solvers:

- `gauss_newton`
- `broyden`
- `lm`
- `newton_raphson`

## Model

`hjb_residual` is required.

```python
@staticmethod
def hjb_residual(v, dv, d2v, s, policy, jump, boundary, p):
    return ...
```

Inputs are interior-point arrays. Return shape must match interior grid length.

Optional methods:

- `jump(v, s, policy, boundary, p)`
- `boundary_condition()`
- `update_boundary(grid)`
- `auxiliary(grid)`

## Boundary Conditions for Search

Return a list of `BoundaryConditionTarget` from `boundary_condition()`:

```python
@staticmethod
def boundary_condition():
    return [
        fjb.BoundaryConditionTarget(
            boundary_name="s_max",
            condition_func=lambda grid: grid.d2v[-1],
            low=0.1,
            high=0.5,
            tol=1e-6,
            max_iter=50,
        )
    ]
```

`low` and `high` are required for `bisection`.

## Value Function Initial Guess

You can pass custom value guess objects to `Solver` through `value_guess`:

- `LinearInitialValue` (default)
- `QuadraticInitialValue`

Or implement your own by subclassing `AbstractValueGuess`.
