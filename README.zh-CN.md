# FinHJB

[English README](./README.md)

FinHJB 是一个基于 JAX 的一维 Hamilton-Jacobi-Bellman (HJB) 方程求解库。

它提供了类型化的建模接口和高层求解器，支持：

- 策略迭代求解，
- 边界更新与边界搜索，
- 参数延拓（敏感性分析），
- 结果保存与加载。

## 安装

- Python 版本：`>=3.10`
- 推荐使用 [`uv`](https://docs.astral.sh/uv/)

```bash
uv sync
```

也可以用 pip 可编辑安装：

```bash
pip install -e .
```

## 快速开始

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

## 主要 API

顶层导出包括：

- `Config`
- `Solver`
- `Grid`, `Grids`, `ImmutableBoundary`
- `AbstractBoundary`, `BoundaryConditionTarget`
- `AbstractModel`, `AbstractParameter`
- `AbstractPolicy`, `AbstractPolicyDict`
- `AbstractValueGuess`, `LinearInitialValue`, `QuadraticInitialValue`
- `explicit_policy`, `implicit_policy`
- `load_grid`, `load_grids`, `load_sensitivity_result`

## 求解工作流

- 求解：`state, history = solver.solve()`
- 边界更新（模型必须实现 `update_boundary(grid)`）：
  `state, history = solver.boundary_update()`
- 边界搜索：`state = solver.boundary_search(method="hybr")`
- 敏感性分析：
  `result = solver.sensitivity_analysis(method="hybr", param_name="sigma", param_values=...)`

## 保存与加载

```python
state.grid.save("solution_grid")
loaded_grid = fjb.load_grid("solution_grid")
```

同理支持：

- `grids.save(path)` + `fjb.load_grids(path)`
- `result.save(path)` + `fjb.load_sensitivity_result(path)`

## 配置项重点

`Config` 主要控制导数策略和收敛参数：

- `derivative_method`: `central | forward | backward`
- `pi_method`: `scan | anderson`
- `pe_*`, `pi_*`, `bs_*` 容忍度与迭代上限
- `aa_*` Anderson 加速参数

## 测试

```bash
uv run pytest
```

覆盖率门槛（项目配置）：

```bash
uv run pytest --cov=src/finhjb --cov-fail-under=85
```

## 文档

- 在线文档：<https://su-luoya.github.io/FinHJB/>
- 中文站点：<https://su-luoya.github.io/FinHJB/zh/>
- 英文文档：[docs/en/index.md](./docs/en/index.md)
- 中文文档：[docs/zh/index.md](./docs/zh/index.md)

本地构建 Sphinx 文档站：

```bash
uv sync --group docs
uv run sphinx-build -b dirhtml docs build/sphinx/dirhtml -c .sphinx -W --keep-going
```
