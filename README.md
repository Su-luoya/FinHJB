# FinHJB

[简体中文 README](./README.zh-CN.md) | **[📖 Documentation](./docs/en/index.md)**

FinHJB is a Python library for solving one-dimensional Hamilton-Jacobi-Bellman (HJB) equations with JAX.

## Installation

Install with `uv`:

```bash
uv add finhjb
```

Or with `pip`:

```bash
pip install finhjb
```

**Note**: Installation defaults to CPU. For GPU support, please install JAX separately with the appropriate CUDA/Metal backend.

## Quick Start

```python
from dataclasses import dataclass

import jax.numpy as jnp
from jaxtyping import Array

import finhjb as fjb


class Parameter(fjb.AbstractParameter):
    r: float = 0.03
    sigma: float = 0.15


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


solver = fjb.Solver(
    boundary=Boundary(p=Parameter(), s_min=0.0, s_max=0.2),
    model=Model(policy=Policy()),
    policy_guess=True,
    number=400,
    config=fjb.Config(pi_method="scan", derivative_method="central"),
)

state, history = solver.solve()
print(state.converged, state.best_error)
```

See the [full documentation](./docs/en/index.md) for more details, examples, and API reference.
