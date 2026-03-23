# 求解器指南

这一页帮助你回答两个很实际的问题：

1. 我现在到底该用哪一种工作流？
2. 这个工作流返回的对象应该怎么读？

如果你还在尝试第一次跑通案例，请先回到 [快速开始](./getting-started.md)。如果你已经知道自己的数学问题，只是还不确定怎么接到 FinHJB 接口上，请配合 [建模指南](./modeling-guide.md) 一起读。

## 工作流选择表

| 什么时候用 | 适合场景 | 返回什么 |
|---|---|---|
| `solve()` | 边界已经固定 | 求解状态 + 迭代误差历史 |
| `boundary_update()` | 模型能从当前解直接更新边界 | 边界更新状态 + 历史误差 |
| `boundary_search()` | 边界必须满足某个数值接触条件 | 边界搜索状态 |
| `sensitivity_analysis()` | 你要沿参数路径求一串解 | summary 表 + `Grids` 集合 |

## `Solver(...)`：构造规则

求解器最常见的构造方式是：

```python
solver = fjb.Solver(
    boundary=boundary,
    model=model,
    policy_guess=True,
    number=500,
    config=fjb.Config(pi_method="scan", derivative_method="central"),
)
```

几个最重要的参数：

- `policy_guess`：是否直接使用策略初始化器给出的起点；
- `number`：网格点数，越大越精细，也越耗时；
- `config`：控制导数方法、迭代上限、容忍度、边界搜索参数等。

## `solve()`：固定边界下的策略迭代

用法：

```python
state, history = solver.solve()
```

适合在这些时候用：

- 边界本来就是固定的；
- 你想先验证 HJB 方程本身是否成立；
- 你希望先得到最简单、最容易解释的成功/失败信号。

在本仓库的一次代表性运行中：

- 返回状态类型是 `PolicyIterationState`，
- `history` 长度大约几十步，
- `state.df` 的列包含 `s`、`v`、`dv`、`d2v` 和策略列。

可以先这样检查：

```python
print(type(state).__name__)
print(history.shape)
print(state.df.head())
```

## `boundary_update()`：解完以后更新边界，再继续解

用法：

```python
state, history = solver.boundary_update()
```

前提条件：

- 你的模型实现了 `update_boundary(grid)`。

这是一个外层循环工作流：

1. 在当前边界下求解；
2. 从解出来的网格里读出新的边界信息；
3. 更新边界；
4. 再求解。

hedging 案例就展示了这种逻辑的典型用法：

- 通过 `p'(m) = 1 + gamma` 找到再融资阈值 `m`，
- 再用 value-matching 更新左边界值。

本仓库一次代表性运行中，`boundary_update()` 返回：

- 类型 `BoundaryUpdateState`
- `history` 长度 `50`

### 一个很重要的保护机制

如果模型没有实现 `update_boundary(grid)`，直接调用 `boundary_update()` 会报：

```text
NotImplementedError: `Solver.boundary_update()` requires the model class to implement `update_boundary(grid)`.
```

这不是 bug，而是刻意设计的保护。它告诉你：当前模型并不适合这个工作流。

## `boundary_search()`：搜索满足条件的边界

用法：

```python
state = solver.boundary_search(method="bisection", verbose=False)
```

这正是 BCW 主线最关键的工作流。适合在这些时候用：

- 某个边界值事先不知道；
- 模型通过 `BoundaryConditionTarget` 定义了待满足的条件；
- 你希望求解器自动寻找使接触条件成立的边界。

常见方法：

- `bisection`：一维有 bracket 的问题，优先首选；
- `hybr`、`lm`、`broyden`、`gauss_newton`：常见的非线性根搜索方法；
- `lbfgs`、`krylov`、`broyden1`：更偏数值实验型的方法。

一个很实用的经验法则是：

- 如果你只有一个标量边界目标，而且有可信 bracket，先用 `bisection`。

BCW 两个示例都遵循这个原则。

### 边界搜索后应该先看什么

```python
state = solver.boundary_search(method="bisection", verbose=False)
grid = state.grid

print(grid.boundary)
print(grid.dv[-1], grid.d2v[-1])
```

对于 BCW liquidation，最有信息量的检查是：

- 解出来的 `s_max` 是否脱离初始猜测并落在合理区间；
- `grid.dv[-1]` 是否接近 `1`；
- `grid.d2v[-1]` 是否接近 `0`。

## `sensitivity_analysis()`：沿参数路径求一串解

用法：

```python
result = solver.sensitivity_analysis(
    method="hybr",
    param_name="sigma",
    param_values=jnp.linspace(0.05, 0.20, 10),
)
```

这是做比较静态和 continuation 的工作流。

它返回 `SensitivityResult`，其中最重要的两个对象是：

- `result.df`：参数路径上的 summary 表；
- `result.grids`：保存每个参数点的完整 `Grid`。

本仓库一次代表性运行中，`result.df.columns` 包含：

- `sigma`
- `boundary_error`
- `converged`
- `s_min`
- `s_max`
- `v_left`
- `v_right`

这意味着你既可以看：

- continuation 是否数值收敛，
- 也可以看边界如何随参数变化而移动。

## `Config`：你最先该调什么

`Config` 同时决定稳定性和耗时。

### 一个稳妥的起点

对于新模型，建议先从简单配置开始：

```python
config = fjb.Config(
    derivative_method="central",
    pi_method="scan",
    pi_max_iter=50,
    pi_tol=1e-6,
)
```

原因：

- `central` 通常是最稳妥的导数方案；
- `scan` 是一个清晰直接的策略迭代路径；
- 中等容忍度能先帮你判断模型写法有没有大问题，再决定是否加严。

### 如果不稳定，先按什么顺序排查

如果 `solve()` 不稳定，推荐的排查顺序是：

1. 先检查模型方程和边界是否写对；
2. 简化模型或给更合理的初始策略；
3. 模型本身稳定后，再增加 `number`；
4. 最后再调更严格的容忍度。

如果 `boundary_search()` 不稳定，推荐顺序是：

1. 先确认 target 函数本身是不是你真的要的条件；
2. 再看 `bisection` 的 bracket 是否包含根；
3. 检查 `grid.dv[-1]` 和 `grid.d2v[-1]`；
4. 最后才考虑换根搜索方法。

## 常见失败模式

### `solve()` 能跑完，但结果经济上看起来很怪

不要第一反应就怪求解器。先检查：

- `Policy.initialize` 是否合理；
- `hjb_residual` 的符号是否正确；
- `s_min`、`s_max`、`v_left`、`v_right` 是否自洽。

### `boundary_search()` 一直找不到稳定结果

最常见的几个原因是：

- 目标函数不是你真正想满足的边界条件；
- bracket 根本没把根包进去；
- 固定边界下的 base solve 本来就不稳定。

### `sensitivity_analysis()` 很慢

这很正常，因为每个参数点本质上都要做一次完整求解。建议先用很短的参数网格确认路径是可信的，再扩展样本点。

## 下一步去哪里

- 想系统读返回对象和诊断量：看 [结果与诊断](./results-and-diagnostics.md)
- 工作流跑不稳：看 [排障](./troubleshooting.md)
- 想查精确签名和对象成员：看 [API 参考](./api-reference.md)
