# 库快速上手

这一页服务 package 路径。

如果你希望在不经过 BCW 示例的情况下，直接从一个可用环境走到第一次 `finhjb` 求解，就从这里开始。

## 目标

读完这一页后，你应该能做到：

- 明白 FinHJB 最小可用模型结构长什么样
- 跑通一次固定边界的直接求解
- 不靠猜，而是知道求解后先看哪些对象

## 开始前

- 先完成 [安装与环境](./installation-and-environment.md)
- 如果你想先跑仓库里的 BCW 示例，请改读 [快速开始](./getting-started.md)

## 最小可用求解示例

下面这个例子是故意压到最小的。它不是研究模型，而是一个 package smoke test，用来清楚展示 `Parameter` / `Boundary` / `PolicyDict` / `Policy` / `Model` 这五层结构。

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

## 这个例子在教你什么

- `Parameter` 放模型输入
- `Boundary` 定义状态和值函数边界
- `PolicyDict` 声明求解器要维护哪些策略数组
- `Policy` 负责初始化和策略更新
- `Model.hjb_residual(...)` 是求解器要逼近为零的核心方程

这就是最小直接 package 工作流。若你的目标是自己写模型，而不是先复现 BCW，它就是更合适的起点。

## 求解后先看什么

第一次求解后，优先检查：

- `type(state).__name__`
- `history`
- `state.grid.boundary`
- `state.grid.df.head()`
- `state.grid.df.tail()`
- 如果你实现了 `auxiliary(grid)`，再看 `state.grid.aux`

## 下一步去哪里

- [建模指南](./modeling-guide.md)：完整对象分工
- [求解器指南](./solver-guide.md)：怎么选工作流
- [结果与诊断](./results-and-diagnostics.md)：怎么读求解结果
- [API 参考](./api-reference.md)：精确导出名称
