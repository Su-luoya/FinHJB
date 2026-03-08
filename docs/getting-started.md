# Getting Started

This guide shows the standard FinHJB workflow from model definition to solver execution.

## 1. Define Parameter Class

Create a parameter container by subclassing `AbstractParameter`.

```python
import finhjb as fjb


class Parameter(fjb.AbstractParameter):
    r: float = 0.06
    sigma: float = 0.10
    theta: float = 1.5
```

Notes:

- Keep parameters immutable.
- Use `replace(...)` when you need updated values in sensitivity analysis.

## 2. Define Boundary Class

Subclass `AbstractBoundary` and either:

- provide boundary values directly in constructor, or
- implement `compute_<boundary_name>` methods.

Boundary names are fixed:

- `s_min`
- `s_max`
- `v_left`
- `v_right`

```python
from dataclasses import dataclass

import finhjb as fjb


@dataclass
class Boundary(fjb.AbstractBoundary[Parameter]):
    @staticmethod
    def compute_v_left(p: Parameter) -> float:
        return 0.9

    @staticmethod
    def compute_v_right(p: Parameter, s_max: float) -> float:
        return 1.0 + 0.1 * s_max
```

`AbstractBoundary` resolves dependencies between compute methods automatically using method signatures.

## 3. Define Policy Container and Update Rules

Declare policy variables with a `TypedDict` based on `AbstractPolicyDict`.

```python
from jaxtyping import Array

import finhjb as fjb


class PolicyDict(fjb.AbstractPolicyDict):
    investment: Array
```

Then implement a policy class based on `AbstractPolicy`.

```python
from dataclasses import dataclass

import jax.numpy as jnp

import finhjb as fjb


@dataclass
class Policy(fjb.AbstractPolicy):
    @staticmethod
    def initialize(grid: fjb.Grid, p: Parameter) -> PolicyDict:
        return PolicyDict(investment=jnp.full_like(grid.s, 0.1))

    @staticmethod
    @fjb.explicit_policy(order=1)
    def update_investment(grid: fjb.Grid) -> fjb.Grid:
        grid.policy["investment"] = jnp.maximum(1e-6, 0.5 * grid.v / grid.dv)
        return grid
```

You can also use `@implicit_policy(...)` to solve first-order conditions with `jaxopt`.

## 4. Define Model Residual

Subclass `AbstractModel` and implement `hjb_residual`.

```python
from dataclasses import dataclass

import finhjb as fjb


@dataclass
class Model(fjb.AbstractModel[Parameter, PolicyDict]):
    @staticmethod
    def hjb_residual(v, dv, d2v, s, policy, jump, boundary, p):
        inv = policy["investment"]
        return -p.r * v + (s - inv) * dv + 0.5 * p.sigma**2 * d2v
```

Optional methods:

- `jump(...)`
- `boundary_condition()`
- `update_boundary(grid)`
- `auxiliary(grid)`

## 5. Build and Run Solver

```python
import finhjb as fjb

parameter = Parameter()
boundary = Boundary(p=parameter, s_min=0.0, s_max=0.2)
model = Model(policy=Policy())

config = fjb.Config(
    pi_method="scan",
    pi_max_iter=50,
    pi_tol=1e-8,
)

solver = fjb.Solver(
    boundary=boundary,
    model=model,
    policy_guess=True,
    number=500,
    config=config,
)

state, history = solver.solve()
print(state.converged, state.best_error)
```

## 6. Inspect Results

- `state.grid`: solved grid object
- `state.df`: pandas DataFrame with `s`, `v`, `dv`, `d2v`, and policy variables
- `history`: per-iteration update magnitudes

## 7. Save and Reload

```python
state.grid.save("solution_grid")
loaded_grid = fjb.load("solution_grid")
```
