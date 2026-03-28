# Library Quickstart

This page is for the package path.

Read it if you want the fastest route from a working installation to a first direct `finhjb` solve without going through the BCW examples.

## Goal

By the end of this page, you should be able to:

- define the smallest useful FinHJB model shape
- run one fixed-boundary solve
- inspect the returned objects instead of guessing what solved

## Before You Start

- Finish [Installation and Environment](./installation-and-environment.md)
- If you want the repository BCW examples instead, read [Getting Started](./getting-started.md)

## Smallest Useful Solve

The following example is intentionally tiny. It is not a research model. It is a package smoke test that shows the `Parameter` / `Boundary` / `PolicyDict` / `Policy` / `Model` split clearly.

```python
from dataclasses import dataclass

import jax.numpy as jnp
import finhjb as fjb


class Parameter(fjb.AbstractParameter):
    offset: float = 0.0


class PolicyDict(fjb.AbstractPolicyDict):
    control: object


@dataclass
class Boundary(fjb.AbstractBoundary[Parameter]):
    pass


@dataclass
class Policy(fjb.AbstractPolicy[Parameter, PolicyDict]):
    @staticmethod
    def initialize(grid: fjb.Grid, p: Parameter) -> PolicyDict:
        return PolicyDict(control=jnp.zeros_like(grid.s))

    @staticmethod
    @fjb.explicit_policy(order=1)
    def keep_zero(grid: fjb.Grid) -> fjb.Grid:
        grid.policy["control"] = jnp.zeros_like(grid.s)
        return grid


@dataclass
class Model(fjb.AbstractModel[Parameter, PolicyDict]):
    @staticmethod
    def hjb_residual(v, dv, d2v, s, policy, jump, boundary, p):
        return v - (s + p.offset)

    @staticmethod
    def auxiliary(grid: fjb.Grid):
        return {"value_mean": jnp.mean(grid.v)}


parameter = Parameter()
boundary = Boundary(
    p=parameter,
    s_min=0.0,
    s_max=1.0,
    v_left=0.0,
    v_right=1.0,
)
solver = fjb.Solver(
    boundary=boundary,
    model=Model(policy=Policy()),
    policy_guess=True,
    number=200,
    config=fjb.Config(derivative_method="central"),
)

state, history = solver.solve()
grid = state.grid

print(type(state).__name__)
print(history.shape)
print(grid.df.head())
print(grid.aux)
```

## What This Example Teaches

- `Parameter` holds model inputs.
- `Boundary` defines the state and value boundaries.
- `PolicyDict` declares the policy arrays the solver will manage.
- `Policy` provides initialization and policy updates.
- `Model.hjb_residual(...)` is the core equation the solver tries to drive to zero.

This is the minimum direct package workflow. It is the right starting point when you want to build your own model instead of reproducing BCW first.

## What To Inspect First

After a first solve, check these objects first:

- `type(state).__name__`
- `history`
- `state.grid.boundary`
- `state.grid.df.head()`
- `state.grid.df.tail()`
- `state.grid.aux` if your model implements `auxiliary(grid)`

## Where To Go Next

- [Modeling Guide](./modeling-guide.md) for the full object model
- [Solver Guide](./solver-guide.md) for workflow choice
- [Results and Diagnostics](./results-and-diagnostics.md) for how to read solves
- [API Reference](./api-reference.md) for exact exported names
