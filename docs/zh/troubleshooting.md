# 排障

当 FinHJB 报错，或者脚本“能跑完但你不信它是对的”时，请用这一页做排查。

一个很重要的习惯是：把问题分成三层看。

1. 环境层问题；
2. 建模层问题；
3. 数值工作流和配置层问题。

如果三层混在一起，你很容易既不确定是导入错了，还是方程写错了，还是求解器配置不合适。

## 快速分诊

| 症状 | 大概率属于哪一层 | 建议同时打开哪一页 |
|---|---|---|
| 一开始导入就失败 | 环境层 | [安装与环境](./installation-and-environment.md) |
| 脚本能跑，但边界诊断不对 | 数值工作流层 | [结果与诊断](./results-and-diagnostics.md) |
| 自定义模型报键错误或 shape 错误 | 模型实现层 | [建模指南](./modeling-guide.md) |
| 不知道该用哪种求解流程 | 工作流选择层 | [求解器指南](./solver-guide.md) |

## 环境问题

### `ModuleNotFoundError: No module named 'finhjb'`

常见原因：

- 直接用了系统 `python`；
- 包根本没有装到当前环境里。

第一修复动作：

```bash
uv sync
uv run python -c "import finhjb as fjb; print(fjb.__all__[:5])"
```

### `ModuleNotFoundError: No module named 'jax'`

常见原因：

- 当前环境里依赖不完整。

第一修复动作：

```bash
uv sync
```

如果你之前一直在用裸 `python`，请统一换成 `uv run python`。

### Matplotlib 后端 / display 报错

典型现象：

- 脚本前半段导入正常，但在绘图相关步骤报错。

第一修复动作：

```bash
export MPLBACKEND=Agg
MPLBACKEND=Agg uv run python src/example/BCW2011Liquidation.py
```

## Loader 相关错误

### 用 `load_grid` / `load_grids` / `load_sensitivity_result` 时出现 `TypeError`

常见原因：

- 保存类型和读取函数不匹配。

正确配对关系如下：

| 保存方式 | 对应读取方式 |
|---|---|
| `state.grid.save(path)` | `load_grid(path)` |
| `result.grids.save(path)` | `load_grids(path)` |
| `result.save(path)` | `load_sensitivity_result(path)` |

这些 loader 会主动做类型校验，所以用错时本来就会显式失败。

## 工作流选择错误

### `NotImplementedError: Solver.boundary_update() requires the model class to implement update_boundary(grid)`

原因：

- 你在一个没有实现 `Model.update_boundary(grid)` 的模型上调用了 `boundary_update()`。

应该怎么做：

- 如果边界固定，使用 `solve()`；
- 如果边界要靠某个条件搜索出来，使用 `boundary_search()`；
- 只有当模型真的有“解完网格后可以直接推一个新边界”的外层规则时，才实现 `update_boundary(grid)` 并使用 `boundary_update()`。

这不是求解器故障，而是工作流保护。

## 边界搜索问题

### `boundary_search()` 返回了结果，但 `grid.d2v[-1]` 离零很远

这通常意味着下面几件事之一：

1. 目标条件写错了；
2. 固定边界下的 base solve 本身就不稳定；
3. 搜索 bracket 很差；
4. 网格太粗，右端曲率根本没被刻画清楚。

建议按下面顺序检查：

```python
print(grid.dv[-1], grid.d2v[-1])
print(grid.boundary)
```

然后问自己：

- `boundary_condition()` 里定义的 target 真的是你要的接触条件吗？
- 不做搜索时，固定边界求解是否至少形状合理？
- 对于 `bisection`，这个 bracket 真的可能包含根吗？

### Bisection 一直收敛不了

最常见的原因是：

- lower / upper bound 不够经济上合理；
- target 在 bracket 上根本没发生符号变化；
- 模型设定本身不支持在这一区间找到可行根。

第一批动作：

1. 手动在几个候选边界上打印 target；
2. 把 bracket 缩到更合理的经济区间；
3. 先验证 `solve()` 在固定边界下能稳定工作。

## 策略迭代问题

### 运行结束了，但策略值看起来“很奇怪”

不要把“出乎直觉”立刻等同于“代码有 bug”。

对 BCW 而言：

- liquidation 左端投资显著为负是正常的；
- hedging 里低现金区域 `psi` 贴在 `-pi` 也是正常的；
- 右端附近才出现小幅正投资。

在改代码之前，先与这两页对照：

- [BCW Liquidation 逐步讲解](./bcw2011-liquidation-walkthrough.md)
- [BCW Hedging 逐步讲解](./bcw2011-hedging-walkthrough.md)

### 收敛很慢或很不稳定

推荐的调整顺序：

1. 先检查方程和边界是否写对；
2. 简化初始策略猜测；
3. 先让一个更小、更简单的 baseline 稳定；
4. 最后再调 `number`、容忍度或搜索方法。

在没核对经济设定前就开始疯狂调容忍度，通常收益很低。

## 导数和网格问题

### `dv` 或 `d2v` 看起来爆炸

可能原因：

- 价值函数本身没有被稳定求出来；
- 网格太粗，无法解析尖锐曲率；
- 策略公式里不稳定地使用了 `dv` 或 `d2v` 做分母；
- 边界条件与经济设定不一致。

优先检查：

```python
df = grid.df
print(df[["s", "v", "dv", "d2v"]].head())
print(df[["s", "v", "dv", "d2v"]].tail())
```

重点问：

- `v` 是否随着现金增加而上升？
- `dv[-1]` 是否逼近预期右端斜率？
- `d2v[-1]` 是否在往零靠近？
- 极端值只集中在左尾，还是整个区间都在震荡？

### 什么时候该增加 `number`？

正确时机是：模型已经大体合理，只是曲线不够平滑。

好理由：

- 形状基本对，但有点锯齿。

坏理由：

- 模型根本不收敛，而你还没确认方程和边界有没有写错。

## `policy_guess` 相关困惑

### 为什么改 `policy_guess` 会影响收敛？

因为它改变了迭代的起点。

- `policy_guess=True`：直接使用初始化器返回的策略；
- `policy_guess=False`：先构造策略容器，再立刻做一次 improvement。

如果初始化器本来就很合理，`True` 往往更快；如果初始化器很差，`False` 反而可能更稳。

## `grid.aux` 报 `NotImplementedError`

原因：

- `Grid.aux` 会调用 `Model.auxiliary(grid)`；
- 而你的模型没有实现这个可选钩子。

这属于预期行为。

应对方法：

- 暂时不要用 `grid.aux`，先用 `grid.boundary` 和 `grid.df`；
- 如果确实需要自定义辅助诊断，再实现 `auxiliary(grid)`。

## 一条很稳的最小调试路径

当你的自定义模型失败时，建议按这个顺序排：

1. `uv run python -c "import finhjb"`，确认环境层；
2. 先让 `solver.solve()` 在固定边界下工作；
3. 看 `state.df.head()` 和 `state.df.tail()`；
4. 再加 `boundary_update()` 或 `boundary_search()`；
5. 最后才做 sensitivity analysis。

这样可以避免多个活动部件同时失败，把真正的问题藏起来。

## 什么时候该停止调参，回去重读模型

如果出现下面这些情况，就应该怀疑是模型设定问题，而不是“再调一下容忍度就好”：

- 右边界怎么都满足不了接触条件；
- 换了不同搜索方法也都同样失败；
- 策略公式需要经常除以接近零的量；
- 整个区间的经济形状都不合理，而不只是某个尾部有噪声。

## 下一步

- 想重新跑稳 BCW：回到 [快速开始](./getting-started.md)
- 想系统读对象输出：看 [结果与诊断](./results-and-diagnostics.md)
- 想搭自己的模型：看 [建模指南](./modeling-guide.md)

