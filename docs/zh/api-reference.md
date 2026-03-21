# API 参考

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

## 加载函数详解

三种 `load_*` 的核心区别是：你想恢复的是单个解、解集合，还是完整敏感性结果。

| 函数 | 恢复对象类型 | 应该搭配的保存方法 | 典型用途 |
|---|---|---|---|
| `load_grid(path)` | `Grid` | `state.grid.save(path)` | 只关心某一次求解的网格与策略 |
| `load_grids(path)` | `Grids` | `result.grids.save(path)` | 关心一组参数点对应的一批网格 |
| `load_sensitivity_result(path)` | `SensitivityResult` | `result.save(path)` | 要同时恢复 summary 表和全部网格 |

关键行为（来自实现）：

- 路径会自动补 `.pkl` 后缀（`Path(path).with_suffix(".pkl")`）。
- 会做类型校验；如果你用错了加载函数，会抛 `TypeError`。

### 1) `load_grid`: 恢复单个 `Grid`

```python
import finhjb as fjb

state, _ = solver.solve()
state.grid.save("outputs/baseline_grid")  # 实际文件: outputs/baseline_grid.pkl

grid = fjb.load_grid("outputs/baseline_grid")
print(type(grid).__name__)  # Grid
print(grid.df.head())
```

### 2) `load_grids`: 恢复 `Grids`（参数路径上的网格集合）

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
print(type(grids).__name__)  # Grids
print(list(grids.values))     # 已保存的参数值
g010 = grids.get(0.10)
print(g010.df.head())
```

### 3) `load_sensitivity_result`: 恢复完整 `SensitivityResult`

```python
import finhjb as fjb

result.save("outputs/sigma_result")
loaded = fjb.load_sensitivity_result("outputs/sigma_result")

print(type(loaded).__name__)  # SensitivityResult
print(loaded.df.head())       # continuation summary
print(loaded.grids.get(0.10).df.head())  # 对应参数点的完整 Grid
```

### 常见错误

1. 用 `load_grid` 去读 `result.save(...)` 的文件：会报类型错误（期望 `Grid`，实际是 `SensitivityResult`）。
2. 路径写成 `.pkl` 也可以，但建议统一不写后缀，避免重复命名困惑。
3. 只需要 summary 表时，优先 `load_sensitivity_result(...).df`；只需要单点网格时，优先 `load_grid(...)`。

## Solver 方法

- `Solver.solve() -> (PolicyIterationState | EvaluationState, history)`
- `Solver.boundary_update() -> (BoundaryUpdateState, history)`
- `Solver.boundary_search(method, verbose=False) -> BoundarySearchState`
- `Solver.sensitivity_analysis(method, param_name, param_values) -> SensitivityResult`

## Grid 便捷属性

`Grid` 属性：

- `s`, `v`, `dv`, `d2v`
- `s_inter`, `policy_inter`, `number_inter`, `jump_inter`
- `df`, `aux`

`Grid` 方法：

- `reset()`
- `update_grid(boundary)`
- `update_with_v_inter(v_inter)`
- `save(path)`

`Grids` 方法：

- `get`, `select_grids`, `add`, `merge`, `save`
