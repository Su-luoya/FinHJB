# FinHJB

FinHJB is a Python library for solving one-dimensional Hamilton-Jacobi-Bellman (HJB) problems with JAX.

It provides a structured workflow for:

- defining model parameters, boundaries, policy rules, and residual equations,
- solving with policy iteration,
- searching for optimal boundaries,
- running parameter sensitivity analysis.

The package is built around typed interfaces (`AbstractModel`, `AbstractPolicy`, `AbstractBoundary`, `AbstractParameter`) and a high-level orchestrator (`Solver`).

## Features

- JAX-based numerical core with optional JIT compilation
- Flexible policy updates via `@explicit_policy` and `@implicit_policy`
- Multiple boundary search methods (`gauss_newton`, `lm`, `broyden`, `lbfgs`, `bisection`, `hybr`, `broyden1`, `krylov`)
- Built-in continuation workflow for parameter paths (`sensitivity_analysis`)
- Serializable result containers (`Grid`, `Grids`, `SensitivityResult`)

## Installation

This project requires Python `>=3.10`.

Install from source in editable mode:

```bash
pip install -e .
```

If you use `uv`:

```bash
uv sync
```

To include the development dependency group with `uv`:

```bash
uv sync --group dev
```

## Quick Start

The minimal workflow has 4 pieces:

1. `Parameter`: immutable model parameters
2. `Boundary`: state/value boundaries
3. `Policy`: policy variable initialization and update rules
4. `Model`: HJB residual and optional boundary conditions

Then pass them to `Solver`.

```python
from dataclasses import dataclass

import jax.numpy as jnp
from jaxtyping import Array

import finhjb as fjb


class Parameter(fjb.AbstractParameter):
  r: float = 0.06
  sigma: float = 0.10
  theta: float = 1.5


class PolicyDict(fjb.AbstractPolicyDict):
  investment: Array


@dataclass
class Boundary(fjb.AbstractBoundary[Parameter]):
  @staticmethod
  def compute_v_left(p: Parameter) -> float:
    return 0.9

  @staticmethod
  def compute_v_right(p: Parameter, s_max: float) -> float:
    return 1.0 + 0.1 * s_max


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


@dataclass
class Model(fjb.AbstractModel[Parameter, PolicyDict]):
  @staticmethod
  def hjb_residual(v, dv, d2v, s, policy, jump, boundary, p):
    inv = policy["investment"]
    return -p.r * v + (s - inv) * dv + 0.5 * p.sigma**2 * d2v


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
df = state.df
```

## Boundary Search

If your model provides `boundary_condition()` targets, you can search for boundaries directly:

```python
search_state = solver.boundary_search(method="bisection", verbose=True)
print(search_state.optimal_boundary)
print(search_state.best_error)
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

Run path-following continuation on one parameter:

```python
import jax.numpy as jnp

result = solver.sensitivity_analysis(
  method="hybr",
  param_name="sigma",
  param_values=jnp.linspace(0.05, 0.20, 10),
)

print(result.df.head())
```

## Save and Load

Main objects support pickle-based save/load:

- `Grid.save(path)`
- `Grids.save(path)`
- `SensitivityResult.save(path)`
- `fjb.load_grid(path)`
- `fjb.load_grids(path)`
- `fjb.load_sensitivity_result(path)`

```python
state.grid.save("single_grid")
loaded = fjb.load_grid("single_grid")
```

## Public API

Top-level exports include:

- `Config`
- `Solver`
- `Grid`, `Grids`, `ImmutableBoundary`
- `AbstractBoundary`, `BoundaryConditionTarget`
- `AbstractModel`, `AbstractParameter`
- `AbstractPolicy`, `AbstractPolicyDict`
- `explicit_policy`, `implicit_policy`
- `LinearInitialValue`, `QuadraticInitialValue`
- `load_grid`, `load_grids`, `load_sensitivity_result`

## Examples

Two complete examples are available in:

- `src/example/BCW2011Liquidation.py`
- `src/example/BCW2011Hedging.py`

They show full model construction, solver configuration, and boundary search.

## Documentation

Additional guides are in `docs/`:

- `docs/getting-started.md`
- `docs/modeling-guide.md`
- `docs/solver-guide.md`
- `docs/api-reference.md`
