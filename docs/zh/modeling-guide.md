# 建模指南

当你已经从“我能跑 BCW”进入“我想定义自己的模型”时，就该读这一页了。

如果你还没有稳定复现 BCW 基准案例，请先回到 [快速开始](./getting-started.md)。如果你已经想把 BCW 改造成自己的研究问题，请配合 [把 BCW 改成你自己的模型](./adapting-bcw-to-your-model.md) 一起读。

## 四个核心组件

每一个 FinHJB 模型，本质上都由四部分组成：

1. `AbstractParameter`：不可变的经济参数和数值参数；
2. `AbstractBoundary`：状态边界和值边界；
3. `AbstractPolicy`：控制变量如何初始化、如何更新；
4. `AbstractModel`：HJB 残差方程，以及可选的边界辅助逻辑。

一个很好记的理解方式是：

- `Parameter` 说“世界是什么样的”，
- `Boundary` 说“世界从哪里开始，到哪里结束”，
- `Policy` 说“主体怎么决策”，
- `Model` 说“需要满足哪一个 HJB 方程”。

## `AbstractParameter`：不可变输入

把所有应当被视为“模型设定”的量都放进 `AbstractParameter`：

- 利率，
- 折旧率，
- 波动率，
- 调整成本参数，
- 融资摩擦参数，
- 以及任何你希望在 continuation 里逐步变化的标量参数。

例子：

```python
class Parameter(fjb.AbstractParameter):
    r: float = 0.03
    sigma: float = 0.15
```

好的做法：

- 字段尽量保持数值型、不可变；
- 命名要有经济含义；
- 派生量可以用 `cached_property`；
- 如果边界变化会影响派生参数，可重写 `update(boundary)`。

常见错误：

- 把可变容器塞进参数对象；
- 把重要经济常数偷偷写在 `Policy` 或 `Model` 里；
- 明明边界变化会影响参数，却忘了使用 `update(boundary)`。

## `AbstractBoundary`：统一管理状态和值边界

边界对象要管理四个量：

- `s_min`
- `s_max`
- `v_left`
- `v_right`

这些边界有两种定义方式：

1. 直接在构造函数里显式给定；
2. 通过 `compute_<boundary_name>` 方法间接计算。

例如：

```python
@dataclass
class Boundary(fjb.AbstractBoundary[Parameter]):
    @staticmethod
    def compute_v_left(p: Parameter) -> float:
        return 0.0

    @staticmethod
    def compute_v_right(p: Parameter, s_max: float) -> float:
        return 1.0 + 0.1 * s_max
```

FinHJB 会自动根据方法签名推断依赖关系：

- 方法名决定“你在算哪个边界”，
- 参数名决定“它依赖哪些已有边界”，
- `p` 被识别为参数对象，而不是另外一个边界。

因此 `compute_v_right(p, s_max)` 的含义就是：

“要算 `v_right`，我需要参数对象 `p` 和状态上边界 `s_max`。”

### 关于边界，有几个规则必须记住

- 同一个边界不能既显式赋值，又定义 `compute_*` 方法；
- 必须满足 `s_min < s_max`；
- 循环依赖会被拒绝；
- 缺失依赖会在很早阶段就报错。

### 什么情况下要用 `boundary_condition()`

当某个边界值不是事先已知的，而是要让“解出来的网格满足某个条件”时，就要在 `Model.boundary_condition()` 里定义目标。

BCW liquidation 的典型例子就是：

```python
def s_max_condition(grid) -> float:
    return grid.d2v[-1]
```

含义是：搜索一个边界，使得右端曲率趋于零。

在实际接口里，`boundary_condition()` 返回的是一个 `BoundaryConditionTarget` 列表。这个列表不只是“把条件写出来”这么简单，它还决定了：

- 只有出现在列表里的边界，才会进入 `boundary_search()`；
- 多边界搜索时，列表顺序就是边界参数向量顺序；
- 对 `method="bisection"` 而言，这个顺序还会变成嵌套搜索的外层到内层顺序；
- 如果要用 `bisection`，每个 target 都必须给 `low` 和 `high`；
- `tol` 和 `max_iter` 这两个字段也主要是给 `bisection` 用的。

如果你用的是其他 boundary-search 方法，则主要使用 `Config.bs_tol` 和 `Config.bs_max_iter`。

## `AbstractPolicyDict`：声明控制变量

`AbstractPolicyDict` 是一个类型化容器，用来声明策略数组有哪些键。

例如：

```python
class PolicyDict(fjb.AbstractPolicyDict):
    investment: Array
    psi: Array
```

经验法则：

- 后续会从 `grid.policy[...]` 中读取的变量，都应该写在这里。

如果一个变量会出现在 `Model.hjb_residual` 中，它通常就应该在 `PolicyDict` 里有一席之地。

## `AbstractPolicy`：策略初始化与策略更新

策略类主要负责两件事：

1. 提供初始猜测；
2. 在迭代中更新控制变量。

### `initialize(grid, p)`

这是必须实现的方法，而且必须返回一个完整的 `PolicyDict`。

你需要检查：

- 每个必需键都存在；
- 每个数组都和网格长度匹配；
- 初值至少在经济上和数值上说得过去。

### `@explicit_policy`

当策略更新可以直接写成闭式表达时，用 `@explicit_policy` 最自然。

例子：

```python
@staticmethod
@fjb.explicit_policy(order=1)
def update_investment(grid: fjb.Grid) -> fjb.Grid:
    grid.policy["investment"] = ...
    return grid
```

适用场景：

- 一阶条件能直接化简成显式公式；
- 更新逻辑简单而稳定；
- 你希望代码路径最直接、最容易读。

### `@implicit_policy`

当策略更自然地写成残差方程或根问题时，用 `@implicit_policy`。

BCW liquidation 中投资策略就是这种形式：

```python
@staticmethod
@fjb.implicit_policy(order=2, solver="lm", policy_order=["investment"])
def cal_investment_without_explicit(policy, v, dv, d2v, s, p):
    investment = policy[0]
    return jnp.array([(1 / p.theta) * (v / dv - s - 1) - investment])
```

适用场景：

- 你更容易把策略写成 `FOC(...) = 0`；
- 需要非线性根求解器；
- 想让多个控制共享统一的残差式实现。

### 策略层的常见错误

- 模型需要两个控制，但 `initialize` 只返回了一个；
- `policy_order` 与残差返回顺序不一致；
- `@explicit_policy` 更新完后忘记返回 `grid`；
- 在公式里直接除以 `dv` 或 `d2v`，却没意识到这些量可能在某些状态下非常小。

## `AbstractModel`：HJB 残差的主体

最少必须实现的方法是：

```python
hjb_residual(v, dv, d2v, s, policy, jump, boundary, p)
```

这个函数需要返回每个内部网格点上的残差，求解器的任务就是让它逼近零。

常见输入：

- `v`, `dv`, `d2v`：当前价值函数及导数；
- `s`：状态网格；
- `policy`：当前控制变量；
- `jump`：跳跃项；
- `boundary`：冻结后的边界值；
- `p`：参数对象。

可选钩子包括：

- `jump(...)`：如果模型有非零跳跃项；
- `boundary_condition()`：如果需要边界搜索；
- `update_boundary(grid)`：如果需要外层边界更新；
- `auxiliary(grid)`：如果想自定义额外诊断量。

### 什么时候需要重写 `jump(...)`

大多数模型都不需要，默认实现就是零。

只有当你的 HJB 里真的存在额外的跳跃项时，才需要重写它。求解器是通过 `Grid.jump_inter` 来调用这个钩子的，所以实际上传进去的是内部网格切片，而不是包含两端边界点的整条数组。

### `boundary_condition()` 应该返回什么

返回值是一个 `BoundaryConditionTarget(...)` 列表。

每个 target 至少给出：

- `boundary_name`：要搜索哪个边界字段，比如 `s_max` 或 `v_left`；
- `condition_func(grid)`：你想逼近零的残差；
- `low` / `high`：给 `bisection` 用的 bracket；
- `tol` / `max_iter`：给 `bisection` 用的单目标设置。

如果你使用的是 `hybr`、`lm`、`broyden`、`gauss_newton`、`krylov`、`broyden1` 或 `lbfgs`，则主要使用 `Config.bs_tol` 和 `Config.bs_max_iter`。

### `auxiliary(grid)` 是干什么的

`auxiliary(grid)` 就是 `grid.aux` 背后的钩子。

只有当你想返回 `grid.df` 和 `grid.boundary` 之外的额外派生诊断量时，才建议实现它。一个很稳妥的模式是返回字典：

```python
@staticmethod
def auxiliary(grid: fjb.Grid):
    return {"value_mean": jnp.mean(grid.v)}
```

如果你没有实现它，那么 `grid.aux` 抛出 `NotImplementedError` 是正常行为。

## 一个很稳妥的实现顺序

自己搭新模型时，建议按下面顺序来：

1. 先写 `Parameter`；
2. 再写 `Boundary`；
3. 再写 `PolicyDict`；
4. 实现 `Policy.initialize`；
5. 写 `Model.hjb_residual` 的第一版；
6. 先让 `solver.solve()` 在固定边界下跑起来；
7. 最后才加 `boundary_condition()` 或 `update_boundary()`。

这个顺序的好处是：每次只调一个层面。如果你一开始就把边界搜索也加上，往往会把“模型错”和“搜索错”混在一起。

## 最小模板

```python
class Parameter(fjb.AbstractParameter):
    r: float = 0.03


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


@dataclass
class Model(fjb.AbstractModel[Parameter, PolicyDict]):
    @staticmethod
    def hjb_residual(v, dv, d2v, s, policy, jump, boundary, p):
        inv = policy["investment"]
        return -p.r * v + (s - inv) * dv + 0.5 * p.sigma**2 * d2v
```

## 什么时候可以离开这一页

当你已经明确知道：

- 每个接口分别负责什么，
- 哪些方法必须实现，
- 什么时候该用显式策略、什么时候该用隐式策略，
- 为什么应该先做固定边界求解再做边界搜索，

就可以继续去：

- [求解器指南](./solver-guide.md)：决定工作流；
- [把 BCW 改成你自己的模型](./adapting-bcw-to-your-model.md)：按步骤迁移；
- [API 参考](./api-reference.md)：查精确成员和签名。
