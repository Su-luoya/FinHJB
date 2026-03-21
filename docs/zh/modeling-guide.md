# 建模指南

## 参数（`AbstractParameter`）

将模型参数定义为不可变字段：

```python
class Parameter(fjb.AbstractParameter):
    r: float = 0.03
    sigma: float = 0.15
```

如果边界变化会影响派生参数，可重写 `update(boundary)`。

## 边界（`AbstractBoundary`）

支持混合方式：

- 构造时直接给值；
- 用 `compute_<boundary_name>` 自动计算。

依赖由方法签名自动推断。

规则：

- 同一边界不能同时“显式给值+compute 方法”；
- 循环依赖会抛错；
- 会校验 `s_min < s_max`。

## 策略（`AbstractPolicy`）

1. `initialize(grid, p)` 必须返回完整策略字典。
2. 用 `@explicit_policy(order=...)` 写显式更新。
3. 用 `@implicit_policy(...)` 写隐式方程更新。

隐式求解器支持：

- `gauss_newton`
- `broyden`
- `lm`
- `newton_raphson`

## 模型（`AbstractModel`）

必需实现：

- `hjb_residual(v, dv, d2v, s, policy, jump, boundary, p)`

可选实现：

- `jump(...)`
- `boundary_condition()`
- `update_boundary(grid)`
- `auxiliary(grid)`

若要调用 `solver.boundary_update()`，模型必须实现 `update_boundary(grid)`。
