# 求解器指南

## Solver 构造

`Solver` 可以通过以下两种方式初始化：

- `boundary + model`，或
- 已有的 `grid`。

常用参数：

- `policy_guess`：是否直接使用策略初值
- `number`：网格数（`>= 4`）
- `config`：迭代与导数设置

## 策略迭代

```python
state, history = solver.solve()
```

返回最终状态和每轮更新误差历史。

## 边界更新

```python
state, history = solver.boundary_update()
```

前置条件：模型实现 `update_boundary(grid)`。

## 边界搜索

```python
search_state = solver.boundary_search(method="hybr", verbose=False)
```

支持方法：

- `gauss_newton`
- `lm`
- `broyden`
- `lbfgs`
- `bisection`
- `hybr`
- `broyden1`
- `krylov`

## 敏感性分析

```python
result = solver.sensitivity_analysis(
    method="hybr",
    param_name="sigma",
    param_values=jnp.linspace(0.05, 0.20, 10),
)
```

## 配置项重点

- `derivative_method`: `central | forward | backward`
- `pi_method`: `scan | anderson`
- `pe_*`, `pi_*`, `bs_*`, `aa_*`
