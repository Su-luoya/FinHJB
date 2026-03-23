# FinHJB

[简体中文 README](./README.zh-CN.md)

FinHJB is a Python library for solving one-dimensional Hamilton-Jacobi-Bellman (HJB) equations with JAX.

It provides typed interfaces for model construction and a high-level solver API for:

- policy iteration,
- boundary update/search,
- parameter continuation (sensitivity analysis),
- result serialization and reloading.

## Installation

- Python: `>=3.10`
- Recommended: [`uv`](https://docs.astral.sh/uv/)

```bash
uv sync
```

For editable installation with pip:

```bash
pip install -e .
```

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

## Main APIs

Top-level exports include:

- `Config`
- `Solver`
- `Grid`, `Grids`, `ImmutableBoundary`
- `AbstractBoundary`, `BoundaryConditionTarget`
- `AbstractModel`, `AbstractParameter`
- `AbstractPolicy`, `AbstractPolicyDict`
- `AbstractValueGuess`, `LinearInitialValue`, `QuadraticInitialValue`
- `explicit_policy`, `implicit_policy`
- `load_grid`, `load_grids`, `load_sensitivity_result`

## Solver Workflows

- Solve: `state, history = solver.solve()`
- Boundary update (model must implement `update_boundary(grid)`):
  `state, history = solver.boundary_update()`
- Boundary search: `state = solver.boundary_search(method="hybr")`
- Sensitivity analysis:
  `result = solver.sensitivity_analysis(method="hybr", param_name="sigma", param_values=...)`

## Save / Load

```python
state.grid.save("solution_grid")
loaded_grid = fjb.load_grid("solution_grid")
```

Similarly:

- `grids.save(path)` + `fjb.load_grids(path)`
- `result.save(path)` + `fjb.load_sensitivity_result(path)`

## Configuration Highlights

`Config` controls derivative rules and convergence behavior:

- `derivative_method`: `central | forward | backward`
- `pi_method`: `scan | anderson`
- `pe_*`, `pi_*`, `bs_*` tolerances and iteration limits
- `aa_*` settings for Anderson acceleration

## Testing

```bash
uv run pytest
```

Coverage gate (configured in project settings):

```bash
uv run pytest --cov=src/finhjb --cov-fail-under=85
```

## Documentation

- Online docs: <https://su-luoya.github.io/FinHJB/>
- Chinese site: <https://su-luoya.github.io/FinHJB/zh/>
- English docs: [docs/en/index.md](./docs/en/index.md)
- Chinese docs: [docs/zh/index.md](./docs/zh/index.md)

Recommended reading path for new users:

1. Start with [docs/en/installation-and-environment.md](./docs/en/installation-and-environment.md)
2. Run the BCW quickstart in [docs/en/getting-started.md](./docs/en/getting-started.md)
3. Use [docs/en/bcw2011-case-study.md](./docs/en/bcw2011-case-study.md) as the case-study map
4. Move to [docs/en/adapting-bcw-to-your-model.md](./docs/en/adapting-bcw-to-your-model.md) when you are ready to customize your own model

Build the Sphinx site locally:

```bash
uv sync --group docs
uv run sphinx-build -b dirhtml docs build/sphinx/dirhtml -c .sphinx -W --keep-going
```
