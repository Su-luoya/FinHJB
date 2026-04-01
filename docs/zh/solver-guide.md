# 求解器指南

当方程已经写清楚，剩下的问题变成“现在该用哪一种数值工作流”时，就应该看这一页。

直接建模时，请在 [建模指南](./modeling-guide.md) 后阅读；还在借助仓库示例建立直觉时，请在 [快速开始](./getting-started.md) 后阅读。如果当前问题已经变成“命令能跑，但结果不可信”，请优先看 [排障](./troubleshooting.md)。

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

## 一维 HJB 在 FinHJB 中是怎么被求解的

前面的表告诉你“该用哪个工作流”，这一节补的是“这些工作流在一维 HJB 上到底做了什么”。

抽象地说，仓库要解的是这一类问题：

$$
0 = \sup_{\pi \in \Pi} \mathcal{H}\bigl(V(s), V_s(s), V_{ss}(s), s; \pi\bigr),
$$

其中控制变量可以是一维，也可以是多维；如果模型有 jump 项，代码会把它作为 `jump` 单独传进 `Model.hjb_residual(...)`。

### 第一步：把连续问题离散成内部网格方程

`Grid.reset()` 先把状态区间离散成

$$
s_0 = s_{\min} < s_1 < \cdots < s_{N-2} < s_{N-1} = s_{\max},
$$

然后把边界值固定为

$$
v_0 = v_{\text{left}}, \qquad v_{N-1} = v_{\text{right}},
$$

真正作为未知量迭代的是内部向量

$$
v_{\text{inter}} = (v_1, \dots, v_{N-2}).
$$

对每个内部点 $s_i$，代码都会构造一个离散残差

$$
F_i(v_{i-1}, v_i, v_{i+1}; \pi_i) = 0.
$$

当前实现里，一阶导在内部点使用 `Config.dv_func` 指定的差分格式，默认是 central：

$$
D_h v_i = \frac{v_{i+1} - v_{i-1}}{2h}.
$$

二阶导在内部点使用中心差分：

$$
D_{hh} v_i = \frac{v_{i+1} - 2v_i + v_{i-1}}{h^2}.
$$

而 `Grid.update_with_v_inter()` 在重建整条 `v`、`dv`、`d2v` 时，会在左右边界额外使用二阶单边 stencil，所以边界导数诊断和内部差分是连在一起的：

```python
v = [v_left, *v_inter, v_right]
dv = [left one-sided, dv_func(interior), right one-sided]
d2v = [left one-sided, centered interior, right one-sided]
```

这也是为什么 FinHJB 的主要求解未知量不是整条 `v`，而是边界已经给定后的 `v_inter`。

### 第二步：固定策略，做 policy evaluation

给定当前策略 $\pi$ 后，`PolicyEvaluation` 解的是固定策略下的离散 HJB 系统：

$$
F(v; \pi) = 0.
$$

当前实现不是把它当成简单的逐点替换，而是做 Newton 型更新：

$$
J(v^{(k)}; \pi)\,\Delta v^{(k)} = -F(v^{(k)}; \pi),
\qquad
v^{(k+1)} = v^{(k)} + \Delta v^{(k)}.
$$

这里 Jacobian 会是三对角矩阵，因为每个 $F_i$ 只依赖相邻的三个值点 $(v_{i-1}, v_i, v_{i+1})$。代码对应关系就是：

- `residual_pointwise(...)`：在单个内部点上调用 `Model.hjb_residual(...)`；
- `jax.jacrev(..., argnums=(0, 1, 2))`：自动拿到 $\partial F_i / \partial v_{i-1}$、$\partial F_i / \partial v_i$、$\partial F_i / \partial v_{i+1}$；
- `jax.vmap(...)`：把这个单点计算复制到全部内部点；
- `jax.lax.linalg.tridiagonal_solve(...)`：解 Newton 步对应的三对角线性系统。

机制上可以把它读成：

```python
residuals, dl, d, du = vmapped_pointwise_system(grid)
dv_update = tridiagonal_solve(dl, d, du, -residuals)
grid = grid.replace(v_inter=grid.v_inter + dv_update)
```

`EvaluationState` 记录的是这一内层循环的数值状态，包括：

- `hjb_residuals`：当前内部网格上的点态残差；
- `last_update_step`：本轮 Newton 更新的范数；
- `best_error` 和 `patience_counter`：是否还在继续改善；
- `converged`：是否满足 `pe_tol`。

停止规则也在这一层定义：更新步长小于 `pe_tol`，或者长期没有改善达到 `pe_patience`，都会触发 early stop。

### 第三步：更新策略，做 policy improvement

`PolicyIteration` 的外层循环是：

1. 固定当前策略，先做一次 policy evaluation；
2. 用新的 `v`、`dv`、`d2v` 更新策略；
3. 比较新旧策略变化是否已经足够小。

数学上可以写成

$$
v^{k+1} = \operatorname{Eval}(\pi^k), \qquad
\pi^{k+1} = \operatorname{Improve}(v^{k+1}),
$$

直到

$$
\max_j \lVert \pi^{k+1}_j - \pi^k_j \rVert
$$

小于 `pi_tol`。

实现上，`AbstractPolicy.update()` 会按声明顺序执行两类更新：

- `@explicit_policy`：直接把闭式控制更新写进 `grid.policy[...]`；
- `@implicit_policy`：把 FOC 写成根问题，在每个网格点上解局部非线性系统。

对后一类，当前仓库支持的点态求解器包括 `GaussNewton`、`Broyden`、`LevenbergMarquardt` 和自定义 `NewtonRaphson`。因此 policy improvement 不是“固定写死一条公式”，而是“由 `Policy` 类决定控制怎么从值函数里反推出来”。

`PolicyIteration` 目前有两个 backend：

- `scan`：显式地做 evaluation $\rightarrow$ improvement 循环，并保留逐轮误差历史；
- `anderson`：把整个映射视为固定点问题，再对 `grid -> next_grid` 做 Anderson acceleration。

无论用哪一种，当前默认的外层误差量都是“每个策略数组变化范数的最大值”。

### 第四步：如果边界未知，把它变成 boundary search

当边界本身未知时，FinHJB 不是直接把边界塞进 policy iteration 里一起更新，而是额外构造外层 residual map：

$$
G(b) = C\bigl(\mathrm{Solve}(b)\bigr),
$$

其中 $b$ 是候选边界向量，`Solve(b)` 表示“在该边界下先把内部 HJB 解出来”，而 $C$ 来自 `BoundaryConditionTarget.condition_func`。

`boundary_search()` 在 `_create_objective_func(...)` 里的真实流程就是：

1. 用候选边界 `b` 覆盖当前待搜索的边界字段；
2. 对新边界调用 `reset()`，重建网格、值函数猜测和策略起点；
3. 运行内层 HJB 求解器；
4. 在已求解的 `solved_grid` 上重新读取 `boundary_condition()`；
5. 计算各个 target 的 residual，并把 residual 向量和 `solved_grid` 一起返回。

对应的代码骨架可以概括成：

```python
def residual_func(boundary_params):
    boundary = initial_grid.boundary.update_boundaries(...)
    temp_grid = initial_grid.replace(boundary=boundary).reset()
    pi_state, _ = inner_func(temp_grid)
    solved_grid = pi_state.grid
    residuals = jnp.array([
        target.condition_func(solved_grid) for target in final_targets
    ])
    return residuals, solved_grid
```

这意味着 `boundary_search()` 真正求解的是“边界条件 residual 为零”的外层问题，而不是直接改写 HJB 本体。

### 第五步：不同 boundary search 方法到底在做什么

当前方法可以按算法角色分成三类：

- `bisection`：标量 bracket search。如果有多个 target，当前实现会按 `boundary_condition()` 列表顺序做嵌套递归，因此这个顺序就是从外层到内层的搜索顺序。它使用的是每个 `BoundaryConditionTarget` 自带的 `low`、`high`、`tol`、`max_iter`。
- `hybr`、`broyden`、`broyden1`、`krylov`：把 $G(b)=0$ 当成向量 root problem，统一使用 `Config.bs_tol` 和 `Config.bs_max_iter`。
- `lm`、`gauss_newton`、`lbfgs`：更接近 least-squares 风格。前两者直接利用残差映射做 least-squares root search，`lbfgs` 则最小化 $\sum_k G_k(b)^2$，所以它不是严格意义上的“直接求根”。

因此，`boundary_search()` 里的方法切换，本质上是在换“外层边界 residual 怎么解”，而不是在换内部 HJB 的离散化方式。

### `boundary_update()` 和 `boundary_search()` 的区别

这两个工作流的外层逻辑看起来都像“边界在动”，但数学结构并不一样。

`boundary_search()` 解的是

$$
G(b) = 0,
$$

也就是“找到一个边界，让某个接触条件或光滑贴合条件成立”。

而 `boundary_update()` 不是对残差做 root search。它要求模型直接返回

```python
boundary_dict, boundary_error = model.update_boundary(grid)
```

所以外层逻辑更接近：

1. 先在当前边界下求解；
2. 直接从已求解网格读出新的边界值；
3. 用 `boundary_error` 判断是否继续迭代。

如果你的模型能从当前解直接推出“下一轮边界应该是多少”，`boundary_update()` 就更自然；如果你只有一个“某个条件必须等于零”的 target，应该用 `boundary_search()`。

## `solve()`：固定边界下的策略迭代

用法：

```python
state, history = solver.solve()
```

如果你想先理解它背后的离散化和内外层迭代逻辑，请先看上一节“[一维 HJB 在 FinHJB 中是怎么被求解的](#一维-hjb-在-finhjb-中是怎么被求解的)”。

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

如果你想先看“候选边界如何被包装成 residual map，再交给外层搜索器”，请先看上一节“[一维 HJB 在 FinHJB 中是怎么被求解的](#一维-hjb-在-finhjb-中是怎么被求解的)”。

这正是 BCW 主线最关键的工作流。适合在这些时候用：

- 某个边界值事先不知道；
- 模型通过 `BoundaryConditionTarget` 定义了待满足的条件；
- 你希望求解器自动寻找使接触条件成立的边界。

当前支持的方法：

- `bisection`
- `hybr`
- `lm`
- `broyden`
- `gauss_newton`
- `lbfgs`
- `krylov`
- `broyden1`

### 这些方法的关键区别

- `bisection` 是唯一会使用 `BoundaryConditionTarget.low`、`high`、`tol`、`max_iter` 的方法。
- 如果你用 `bisection`，每个被搜索的 target 都必须提供 `low` 和 `high`。
- 多边界 `bisection` 时，`model.boundary_condition()` 返回列表的顺序，会变成嵌套搜索的外层到内层顺序。
- `hybr`、`lm`、`broyden`、`gauss_newton`、`krylov`、`broyden1` 会把问题当成向量 root-search，并使用 `Config.bs_tol` 和 `Config.bs_max_iter`。
- `lbfgs` 不是严格意义上的 root solver，而是最小化残差平方和，更适合作为 least-squares fallback。

### 实用的起步规则

- 如果你只有一个标量边界目标，而且有可信 bracket，先用 `bisection`。
- 如果你有两个边界目标，而且 bracket 可信，`bisection` 依然是合理的第一默认值。
- 如果边界目标达到 3 个及以上，而且想先用一个稳健默认值，先试 `hybr`。
- 如果残差映射比较平滑，而且天然像 least-squares，试 `lm` 或 `gauss_newton`。
- 如果你想要拟牛顿型替代，可以试 `broyden` 或 `broyden1`。
- 如果你只想把问题当成近似残差最小化，最后再考虑 `lbfgs`。

这些建议是针对当前 FinHJB 实现和底层搜索器的实用经验法则，不代表它们对所有模型都一定最优。

对 `finhjb-model-coder` 还要再加一条：如果 1-2 个目标下默认的 `bisection` 在生成后的 solve-loop 里表现不好，最终生成代码应该显式升级到 `hybr` 或其他支持的方法，并把这一步修复写出来。

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

### 什么时候不该继续用 `central`

如果你是通过 `finhjb-model-coder` 做“理论到代码”，不要把 `central` 当成永远安全的默认值。

- 如果扩散项在左边界附近变得很小，优先考虑 `forward`
- 如果扩散项在右边界附近变得很小，优先考虑 `backward`
- 只有当扩散项在两端都保持明显为正时，`central` 才是自然的第一选择

关键不在于写法习惯，而在于差分格式要和 HJB 在边界附近的数值脆弱点匹配。

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

## 相关页面

- 想系统读返回对象和诊断量：看 [结果与诊断](./results-and-diagnostics.md)
- 工作流跑不稳：看 [排障](./troubleshooting.md)
- 想查精确签名和对象成员：看 [API 参考](./api-reference.md)
