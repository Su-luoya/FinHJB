# 快速开始

这一页的目标很明确：把你从“我刚 clone 了仓库”带到“我已经能跑一个真实 HJB 案例，而且知道结果大致对不对”。

如果你的环境还没准备好，请先看 [安装与环境](./installation-and-environment.md)。如果你想先了解整个 BCW 学习地图，请把 [BCW2011 案例总览](./bcw2011-case-study.md) 当作导航页。

## 目标

读完这一页后，你应该能做到：

- 安装项目并成功导入 `finhjb`，
- 跑通 BCW liquidation 示例，
- 跑通 BCW hedging 示例，
- 不靠猜测，而是用几个稳定的数值检查点判断“这次运行是不是正常”。

## 开始前确认

在仓库根目录先确认依赖和导入都正常：

```bash
uv sync
uv run python -c "import finhjb; print(finhjb.__all__[:5])"
```

如果你在服务器、远程 shell 或没有图形界面的环境下运行，请先设置：

```bash
export MPLBACKEND=Agg
```

这样可以避免 Matplotlib 的图形后端报错，但不会改变数值结果。

## 第一步：运行 BCW Liquidation 示例

liquidation 是最适合第一次上手的案例，因为它包含了 FinHJB 最核心的几件事：

- 一个状态变量，
- 一个主要控制变量，
- 一个右边界搜索问题，
- 一个很清晰的成功判据：支付边界的接触条件。

运行：

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011Liquidation.py
```

这个脚本会做什么：

1. 构造 BCW 的基准参数，
2. 创建 `Boundary`、`Policy` 和 `Model`，
3. 执行 `solver.boundary_search(method="bisection")`，
4. 打印最终状态与网格诊断信息。

### 什么样算成功

按当前仓库配置，一个健康的 liquidation 运行通常有这些特征：

| 检查项 | 你应该看到什么 |
|---|---|
| 左边界价值 | `grid.v[0]` 等于或非常接近 `0.9` |
| 右边界斜率 | `grid.dv[-1]` 非常接近 `1.0` |
| 右边界曲率 | `grid.d2v[-1]` 非常接近 `0` |
| 状态上边界 | 解出来的 `s_max` 会落在大约 `0.22`，而不是停留在初始猜测 |
| 投资策略 | 左端显著为负，随着现金增加逐渐上升，在右端附近转为小幅正值 |

本仓库一次代表性运行得到的结果大致是：

```text
{
  's_max': 0.22177,
  'v_left': 0.9,
  'v_right': 1.38000,
  'd2v_right': 6.26e-07,
  'investment_min': -0.64691,
  'investment_max': 0.10549
}
```

怎样解释这些数字：

- `d2v_right` 基本为零，说明右边界搜索成功满足了接触条件，
- `dv[-1]` 接近 `1`，与支付边界的斜率条件一致，
- 左端投资很负，符合融资受限时低现金企业大幅收缩投资的经济直觉。

## 第二步：运行 BCW Hedging 示例

当 liquidation 跑稳之后，再运行 hedging 扩展：

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011Hedging.py
```

这个案例在 liquidation 基础上增加了：

- 第二个控制变量 `psi`，
- 保证金账户占比 `kappa`，
- 与再融资相关的左边界更新逻辑，
- BCW 里讨论的三分区对冲策略结构。

### 什么样算成功

在当前仓库里，一个健康的 hedging 运行通常有以下特征：

| 检查项 | 你应该看到什么 |
|---|---|
| 左边界价值 | `v_left` 高于单纯 liquidation 的 `0.9` |
| 右边界曲率 | `grid.d2v[-1]` 再次非常接近 `0` |
| 对冲范围 | `psi` 处于 `-pi` 到 `0` 之间 |
| 低现金区域 | `psi` 基本贴着 `-5.0`（即 `-pi`） |
| 高现金区域 | `psi` 逐步靠近 `0.0` |
| 投资策略 | 左端仍为负，右端附近转为正值 |

本仓库一次代表性运行的结果大致为：

```text
{
  's_max': 0.13850,
  'v_left': 1.16119,
  'v_right': 1.31352,
  'd2v_right': -7.05e-07,
  'investment_min': -0.24094,
  'investment_max': 0.11668,
  'psi_min': -5.0,
  'psi_max': 0.0
}
```

这里最关键的不是记住某个单点数值，而是确认这三个稳健模式：

- `psi` 在低现金区域完全绑定，
- 随着现金增加，对冲需求逐步减弱，
- `d2v[-1]` 仍然收敛到零。

## 第三步：不要只“跑出来”，要会读输出

无论哪个示例，最值得你看的对象都是解出来的网格：

```python
grid = final_state.grid
print(grid.df.head())
print(grid.df.tail())
```

优先关注这些列：

- `s`：现金资本比状态网格，
- `v`：价值资本比，
- `dv`：现金的边际价值，
- `d2v`：曲率与边界接触条件诊断，
- `investment`、`psi` 这样的策略列。

如果你只想看一个最有信息量的数字，就先看：

```python
print(grid.d2v[-1])
```

它能直接告诉你右边界搜索有没有发挥作用。

## 第四步：把解保存下来

当你得到一个看起来可靠的结果后，保存对象会非常有帮助，这样就不必每次都重新求解。

```python
state.grid.save("outputs/liquidation_grid")
loaded = fjb.load_grid("outputs/liquidation_grid")
print(loaded.df.head())
```

三个 `load_*` 函数的快速选择：

- `load_grid(path)`：读取单个求解后的 `Grid`
- `load_grids(path)`：读取一组 continuation 的 `Grids`
- `load_sensitivity_result(path)`：读取完整敏感性分析结果

## 首次运行最常见的问题

### 脚本在求解前就失败

请直接去 [排障](./troubleshooting.md) 检查：

- 环境是否安装完整，
- JAX 是否能导入，
- Matplotlib 是否需要 headless 配置。

### 脚本能跑，但右边界看起来不对

先检查：

```python
print(grid.dv[-1], grid.d2v[-1])
```

如果 `grid.d2v[-1]` 没有接近零，优先回看：

- [BCW Liquidation 逐步讲解](./bcw2011-liquidation-walkthrough.md)
- [结果与诊断](./results-and-diagnostics.md)
- [求解器指南](./solver-guide.md)

### 策略值看起来很奇怪

第一次看到 BCW 输出时，这种感觉很正常。尤其是低现金区域的负投资，并不自动意味着代码错了。请先读完 walkthrough 里的经济解释，再决定要不要改代码。

## 下一步去哪里

- 把 [BCW2011 案例总览](./bcw2011-case-study.md) 当作完整学习地图。
- 继续看 [BCW Liquidation 逐步讲解](./bcw2011-liquidation-walkthrough.md)，理解方程与代码的映射。
- 再看 [BCW Hedging 逐步讲解](./bcw2011-hedging-walkthrough.md)，理解 `psi`、`kappa` 与三分区对冲。
- 当你已经能稳定复现基准案例后，再进入 [把 BCW 改成你自己的模型](./adapting-bcw-to-your-model.md)。
