# API 参考

这一页是教程页的“精确接口补充”，不是最推荐的第一站。

如果你还在熟悉工作流，建议先读这些教程，再回来查名字和成员：

| 如果你现在想做的是…… | 先读这一页 |
|---|---|
| 安装并跑通第一个案例 | [安装与环境](./installation-and-environment.md) |
| 复现 BCW 基准案例 | [快速开始](./getting-started.md) |
| 看懂返回对象和数值诊断 | [结果与诊断](./results-and-diagnostics.md) |
| 把 BCW 改成自己的模型 | [把 BCW 改成你自己的模型](./adapting-bcw-to-your-model.md) |
| 决定使用哪种求解工作流 | [求解器指南](./solver-guide.md) |

当你需要确认精确导出名、类成员、方法签名或 loader 行为时，再回到这里。

## 顶层导出（`finhjb`）

### 核心对象

- `Config`
- `Solver`
- `Grid`
- `Grids`
- `ImmutableBoundary`

### 接口类型

- `AbstractBoundary`
- `BoundaryConditionTarget`
- `AbstractModel`
- `AbstractParameter`
- `AbstractPolicy`
- `AbstractPolicyDict`
- `AbstractValueGuess`

### 辅助

- `explicit_policy(order: int)`
- `implicit_policy(...)`
- `LinearInitialValue`
- `QuadraticInitialValue`

### 加载函数

- `load_grid(path)`
- `load_grids(path)`
- `load_sensitivity_result(path)`

## 按任务找 API

| 任务 | 你最先会碰到的对象 |
|---|---|
| 定义模型 | `AbstractParameter`、`AbstractBoundary`、`AbstractPolicy`、`AbstractModel` |
| 跑一次固定边界求解 | `Solver`、`Config` |
| 搜索内生边界 | `BoundaryConditionTarget`、`Solver.boundary_search()` |
| 检查一个解 | `Grid`、`Grid.df`、`Grid.aux` |
| 保存与重载结果 | `Grid.save`、`load_grid`、`Grids.save`、`load_grids`、`load_sensitivity_result` |

## 加载函数详解

三个 `load_*` 的核心区别，是你到底想恢复：

- 单个 `Grid`，
- 一组 `Grids`，
- 还是完整的 `SensitivityResult`。

| 函数 | 恢复对象类型 | 对应保存方法 | 典型用途 |
|---|---|---|---|
| `load_grid(path)` | `Grid` | `state.grid.save(path)` | 单次求解的完整网格 |
| `load_grids(path)` | `Grids` | `result.grids.save(path)` | 一组参数点上的网格集合 |
| `load_sensitivity_result(path)` | `SensitivityResult` | `result.save(path)` | continuation summary + 全部网格 |

保证行为：

- 路径会自动补 `.pkl`；
- 加载后会做类型校验；
- 用错 loader 会明确抛出 `TypeError`。

### `load_grid` 示例

```python
import finhjb as fjb

state, _ = solver.solve()
state.grid.save("outputs/baseline_grid")

grid = fjb.load_grid("outputs/baseline_grid")
print(type(grid).__name__)
print(grid.df.head())
```

### `load_grids` 示例

```python
import finhjb as fjb
import jax.numpy as jnp

result = solver.sensitivity_analysis(
    method="hybr",
    param_name="sigma",
    param_values=jnp.array([0.09, 0.10, 0.11]),
)
result.grids.save("outputs/sigma_grids")

grids = fjb.load_grids("outputs/sigma_grids")
print(type(grids).__name__)
print(list(grids.values))
```

### `load_sensitivity_result` 示例

```python
import finhjb as fjb

result.save("outputs/sigma_result")
loaded = fjb.load_sensitivity_result("outputs/sigma_result")

print(type(loaded).__name__)
print(loaded.df.head())
```

### 常见加载错误

1. 用 `load_grid` 去读取 continuation 或 sensitivity 的保存结果；
2. 忘了 loader 会自动补 `.pkl`；
3. 其实只想要单点网格，却误用了整个 `SensitivityResult`。

## `Solver` 的主要方法

- `Solver.solve() -> (PolicyIterationState | EvaluationState, history)`
- `Solver.boundary_update() -> (BoundaryUpdateState, history)`
- `Solver.boundary_search(method, verbose=False) -> BoundarySearchState`
- `Solver.sensitivity_analysis(method, param_name, param_values) -> SensitivityResult`

什么时候该用哪个方法，请配合 [求解器指南](./solver-guide.md) 阅读。

## `boundary_search` 方法备注

`Solver.boundary_search(method=...)` 当前支持：

- `bisection`
- `hybr`
- `lm`
- `broyden`
- `gauss_newton`
- `lbfgs`
- `krylov`
- `broyden1`

关键行为：

- `boundary_condition()` 返回的就是实际会被搜索的边界列表。
- 这个列表的顺序，就是非线性方法使用的边界参数顺序。
- 对 `bisection` 来说，同样的顺序还会变成嵌套搜索的外层到内层顺序。
- `BoundaryConditionTarget.low` 和 `high` 只对 `bisection` 有意义。
- `BoundaryConditionTarget.tol` 和 `max_iter` 也主要只对 `bisection` 有意义。
- 其他方法主要使用 `Config.bs_tol` 和 `Config.bs_max_iter`。
- `lbfgs` 做的是残差平方和最小化，而不是直接解 root problem。

## `AbstractModel` 可选钩子速查

最重要的几个可选钩子是：

- `jump(...)`：可选，默认是零，由求解器通过 `Grid.jump_inter` 调用。
- `boundary_condition()`：为 `boundary_search()` 返回 `BoundaryConditionTarget` 列表。
- `update_boundary(grid)`：只在 `boundary_update()` 工作流里使用。
- `auxiliary(grid)`：通过 `Grid.aux` 暴露；如果没实现，`grid.aux` 抛 `NotImplementedError` 是正常的。

## `Grid` 的便捷属性

`Grid` 常用属性：

- `s`, `v`, `dv`, `d2v`
- `s_inter`, `policy_inter`, `number_inter`, `jump_inter`
- `df`, `aux`

补充说明：

- `jump_inter` 是 `Model.jump(...)` 在内部网格上的求值结果。
- `aux` 只是 `Model.auxiliary(grid)` 的代理入口。
- `auxiliary(grid)` 一个很常见的写法，是返回一个小字典来保存派生诊断量。

`Grid` 常用方法：

- `reset()`
- `update_grid(boundary)`
- `update_with_v_inter(v_inter)`
- `save(path)`

`Grids` 常用方法：

- `get`
- `select_grids`
- `add`
- `merge`
- `save`

如何解释这些对象，请看 [结果与诊断](./results-and-diagnostics.md)。

## API 详细文档

### Config

```{eval-rst}
.. autoclass:: finhjb.Config
   :members:
   :no-index:
```

### Solver

```{eval-rst}
.. autoclass:: finhjb.Solver
   :members:
   :no-index:
```

### 数据结构

```{eval-rst}
.. autoclass:: finhjb.Grid
   :members:
   :no-index:

.. autoclass:: finhjb.Grids
   :members:
   :no-index:

.. autoclass:: finhjb.ImmutableBoundary
   :members:
   :no-index:
```

### 接口类型

```{eval-rst}
.. autoclass:: finhjb.AbstractBoundary
   :members:
   :no-index:

.. autoclass:: finhjb.BoundaryConditionTarget
   :members:
   :no-index:

.. autoclass:: finhjb.AbstractModel
   :members:
   :no-index:

.. autoclass:: finhjb.AbstractParameter
   :members:
   :no-index:

.. autoclass:: finhjb.AbstractPolicy
   :members:
   :no-index:

.. autoclass:: finhjb.AbstractPolicyDict
   :members:
   :no-index:

.. autoclass:: finhjb.AbstractValueGuess
   :members:
   :no-index:

.. autoclass:: finhjb.LinearInitialValue
   :members:
   :no-index:

.. autoclass:: finhjb.QuadraticInitialValue
   :members:
   :no-index:
```

### 辅助函数

```{eval-rst}
.. autofunction:: finhjb.explicit_policy
   :no-index:

.. autofunction:: finhjb.implicit_policy
   :no-index:
```

### 加载函数

```{eval-rst}
.. autofunction:: finhjb.load_grid
   :no-index:

.. autofunction:: finhjb.load_grids
   :no-index:

.. autofunction:: finhjb.load_sensitivity_result
   :no-index:
```
