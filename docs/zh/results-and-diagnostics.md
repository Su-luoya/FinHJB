# 结果与诊断

这一页的目标，是让你在看到求解输出时不必靠猜。

你应该能用它回答：

- 求解器到底返回了什么对象？
- 哪些属性总是安全可读的？
- 什么样的数值形状可以算“健康”？
- 哪些症状更像是建模错误，哪些更像是数值调参问题？

## 建议在什么之后阅读

- [快速开始](./getting-started.md)
- [BCW Liquidation 逐步讲解](./bcw2011-liquidation-walkthrough.md)
- [BCW Hedging 逐步讲解](./bcw2011-hedging-walkthrough.md)

## 求解器返回类型

在本仓库的代表性运行中，各工作流的返回对象如下：

| 工作流 | 返回对象 | 常见伴随输出 |
|---|---|---|
| `solve()` | `PolicyIterationState` | 一条 `history` 误差序列 |
| `boundary_update()` | `BoundaryUpdateState` | 一条边界更新误差序列 |
| `boundary_search()` | `BoundarySearchState` | 解出的 `grid` 与搜索诊断 |
| `sensitivity_analysis()` | `SensitivityResult` | summary DataFrame + `Grids` |

例子：

```python
state, history = solver.solve()
print(type(state).__name__)
print(len(history))
```

```python
search_state = solver.boundary_search(method="bisection", verbose=False)
print(type(search_state).__name__)
print(search_state.grid.boundary)
```

## 最值得先看的对象

## `state.grid`

这是完整的已求解网格对象，通常也是你后续分析时第一时间要拿到的对象：

```python
grid = state.grid
```

最常用成员有：

- `grid.boundary`
- `grid.s`
- `grid.v`
- `grid.dv`
- `grid.d2v`
- `grid.policy`
- `grid.df`

## `state.df`

每个 solver state 都暴露了：

```python
print(state.df.head())
print(state.df.tail())
```

它本质上就是 `state.grid.df` 的快捷入口。

本仓库里一次代表性 `solve()` 输出的前几列是：

```text
['s', 'v', 'dv', 'd2v', 'investment']
```

如果你的模型有更多控制变量，列会更多。

## `history`

对 `solve()` 和 `boundary_update()` 来说，第二个返回对象都是历史误差数组。

它的意义在于：

- 记录每步迭代误差有多大；
- 区分“很快失败”和“缓慢收敛”；
- 用来比较两套配置谁更稳。

不要把 `history` 当成经济结果本身。它是迭代诊断，不是价值函数。

## `grid.boundary`

这是读取最终边界值最直接、最整洁的地方：

```python
print(grid.boundary)
```

BCW 两个案例的一次代表性输出大致是：

```text
ImmutableBoundary(s_min=0.0, s_max=0.22176666, v_left=0.9, v_right=1.380003)
ImmutableBoundary(s_min=0.0, s_max=0.13850403, v_left=1.16119385, v_right=1.31352204)
```

重点不是逐位复现，而是确认量级和边界关系是否合理。

## `grid.df`：逐列解读

| 列名 | 含义 | 为什么重要 |
|---|---|---|
| `s` | 状态网格 | 告诉你当前处于哪个现金状态 |
| `v` | 价值资本比 | 价值函数本体 |
| `dv` | 一阶导数 | 现金的边际价值 |
| `d2v` | 二阶导数 | 曲率与右边界接触条件诊断 |
| `investment` | 投资策略 | 真实决策如何随现金变化 |
| `psi` | hedging 案例中的对冲策略 | 识别绑定区、内部区和零对冲区 |

## 三个信息量最高的诊断

如果你时间很少，优先看这三个：

1. `grid.boundary`
2. `grid.df.tail()`
3. `grid.d2v[-1]`

原因：

- `grid.boundary` 告诉你最终到底解了哪个边界问题；
- 尾部表格可以直观看出右端是否接近正确边界行为；
- `grid.d2v[-1]` 是 BCW 中最关键的接触条件指标。

## 边界诊断

### 左边界

要问的问题：

- `v[0]` 是否符合你定义的左边界条件？
- liquidation 中，它是否接近 liquidation value？
- hedging 中，它是否因为再融资而高于 liquidation 的值？

### 右边界

要问的问题：

- `dv[-1]` 是否逼近预期的支付边界斜率？
- `d2v[-1]` 是否逼近零？
- 曲线是否平滑地进入右边界，而不是在尾部震荡？

对 BCW 来说，一个健康的右尾通常意味着：

- 斜率逼近预期值，
- 曲率数值上消失。

## 策略诊断

### 投资策略

BCW 中比较典型的模式是：

- 左端：投资大幅收缩，甚至为负；
- 中间：逐步恢复；
- 右端：变成小幅正值。

关键在于经济形状是否合理，而不是曲线必须线性或特别平滑。

### 对冲策略 `psi`

在 hedging 案例中：

- 左端：`psi` 应该绑定在 `-pi`；
- 中间：出现内部解；
- 右端：回到 `0`。

如果这三个区域都没有出现，就该回查 hedging 逻辑。

## `grid.aux` 是可选的，不保证总能用

`grid.aux` 会调用模型中的可选钩子 `auxiliary(grid)`。

因此有一个重要后果：

- 如果你的模型没有实现 `auxiliary(grid)`，访问 `grid.aux` 会直接抛 `NotImplementedError`。

所以通用、安全的默认诊断对象是：

- `grid.boundary`
- `grid.df`
- `history`
- `Grid` / `Grids` / `SensitivityResult` 的保存结果

只有在你自己实现了 `auxiliary(grid)` 以后，才建议依赖 `grid.aux`。

## 敏感性分析结果怎么看

`sensitivity_analysis()` 返回的是 `SensitivityResult`：

```python
result = solver.sensitivity_analysis(
    method="hybr",
    param_name="sigma",
    param_values=...,
)
```

第一眼最值得看的两个对象是：

- `result.df`
- `result.grids`

本仓库代表性结果的列名包括：

```text
['sigma', 'boundary_error', 'converged', 's_min', 's_max', 'v_left', 'v_right']
```

这说明：

- `result.df` 是 continuation summary；
- `result.grids` 里则保存每个参数点的完整求解网格。

本仓库一次代表性 continuation 的参数键值为：

```text
[0.08, 0.09]
```

你因此既可以看：

- 边界如何随参数变化，
- 也可以回到每个参数点对应的完整 `Grid` 上看价值函数和策略函数。

## 保存、重载、再检查

推荐做法：

```python
state.grid.save("outputs/liquidation_grid")
grid = fjb.load_grid("outputs/liquidation_grid")
print(grid.df.tail())
```

```python
result.save("outputs/sigma_result")
loaded = fjb.load_sensitivity_result("outputs/sigma_result")
print(loaded.df)
```

当求解很耗时时，这样做尤其重要，因为你可以把“求解”和“解释结果”分开。

## 症状 -> 可能原因 -> 第一动作

| 症状 | 可能原因 | 第一动作 |
|---|---|---|
| `d2v[-1]` 不接近零 | 边界目标错或搜索不稳定 | 先看 `boundary_condition()` 和右尾表格 |
| `dv[-1]` 远离预期斜率 | 右边界不一致 | 先看 `grid.boundary` 与边界公式 |
| `investment` 剧烈振荡 | 策略更新不稳或网格太粗 | 先核对方程，再考虑增大 `number` |
| `psi` 一直停在 `-pi` | 对冲逻辑没进入内部区 | 回查 clipping 与 `should_hedge` |
| `grid.aux` 报错 | 可选钩子没实现 | 暂时忽略或实现 `auxiliary(grid)` |
| `history` 长时间卡在大误差 | 更可能是模型写错，不只是收敛慢 | 退回固定边界 baseline 重新检查 |

## 一个最小但非常有用的 BCW 诊断脚本

```python
grid = state.grid

print(grid.boundary)
print(grid.df.head())
print(grid.df.tail())
print("right slope:", grid.dv[-1])
print("right curvature:", grid.d2v[-1])
```

如果你不知道从哪里开始看结果，这几行代码的信息量是最高的。

## 什么时候应该停止调参，回去重读模型

如果出现下面这些情况，就不该继续盲调容忍度了，而应回到模型本身：

- 整个区间的经济形状都不合理；
- 换了不同求解器也都失败；
- 边界条件和模型故事本身对不上；
- 你的诊断结果与论文的定性图形完全相反。

这时最可能是建模问题，而不是数值微调问题。

## 下一步

- 如果你还在决定用哪种工作流：看 [求解器指南](./solver-guide.md)
- 如果你准备迁移到自己的模型：看 [把 BCW 改成你自己的模型](./adapting-bcw-to-your-model.md)
- 如果你想查精确成员和签名：看 [API 参考](./api-reference.md)

