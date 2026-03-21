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
