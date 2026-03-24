# BCW2011 案例总览

这一页是通过 BCW 示例学习 FinHJB 的总入口。

仓库里包含两个基于 Bolton, Chen, and Wang (2011) 的完整案例：

- `src/example/BCW2011Liquidation.py`
- `src/example/BCW2011Hedging.py`

仓库同时附带了论文原文的转录稿，便于对照公式：

- `src/example/A_unified_theory_of_tobin's_q,_corporate_investment,_financing,_and_risk_management.md`

## 为什么要从 BCW 学 FinHJB

BCW 这两份示例几乎把 FinHJB 最关键的概念都串在了一起：

- 如何组织参数和边界；
- 如何把策略写成显式更新或隐式残差；
- 如何搜索内生边界；
- 如何解释 `v`、`dv`、`d2v`；
- 融资摩擦如何改变低现金状态下的策略；
- 加入对冲扩展后，第二个控制变量如何改变数值工作流。

对研究者和学生来说，这是一条非常自然的学习主线：

- 先复现文献中的经典结构，
- 再逐步改造成自己的模型。

## 推荐阅读顺序

如果你是第一次接触本项目，建议按这个顺序阅读：

1. [安装与环境](./installation-and-environment.md)
2. [快速开始](./getting-started.md)
3. [BCW Liquidation 逐步讲解](./bcw2011-liquidation-walkthrough.md)
4. [结果与诊断](./results-and-diagnostics.md)
5. [BCW Hedging 逐步讲解](./bcw2011-hedging-walkthrough.md)
6. [把 BCW 改成你自己的模型](./adapting-bcw-to-your-model.md)

## 两个案例，对应两层学习目标

| 案例 | 脚本 | 主要数值思想 | 主要经济思想 |
|---|---|---|---|
| Liquidation | `BCW2011Liquidation.py` | 用 super-contact 条件搜索右边界 | 低现金状态下投资大幅受限 |
| Hedging | `BCW2011Hedging.py` | 两个控制变量，并通过边界搜索直接解 `s_max` 和 `v_left`，同时附带一个可复用的 boundary-update-compatible helper | 对冲需求在困境状态最强，内部流动性改善后逐步消失 |

## 你应该期待看到什么样的结果模式

你不需要逐字复现脚本打印出的每一行，但应该知道哪些模式才算“跑得对”。

### Liquidation

健康运行通常表现为：

- `v_left = 0.9`；
- 解出来的 `s_max` 大约在 `0.22`；
- `p'(0)` 大约在 `30`；
- `d2v[-1]` 接近零；
- 投资在左端显著为负，在右端转为正值。

### Hedging

健康运行通常表现为：

- 左边界价值高于纯 liquidation 的值；
- `s_max` 大约在 `0.14`；
- `w_-` 大约在 `0.067`；
- `w_+` 大约在 `0.115`；
- `psi` 落在 `-5` 到 `0` 之间；
- 对冲策略呈现“三分区”结构：先完全绑定，再进入内部区间，最后收敛到零对冲。

## 其他 BCW 页面各自负责什么

请有意识地分工阅读：

- [BCW Liquidation 逐步讲解](./bcw2011-liquidation-walkthrough.md)
  负责逐段解释 liquidation 脚本、右边界搜索目标和结果形状。
- [BCW Hedging 逐步讲解](./bcw2011-hedging-walkthrough.md)
  负责解释 `psi`、`kappa`、再融资逻辑和三分区对冲。
- [结果与诊断](./results-and-diagnostics.md)
  负责告诉你 `state`、`grid`、`history`、continuation 输出到底怎么看。

## 方程到代码的地标

BCW 在本仓库里本来就是以“方程映射到代码”为主线组织的。几个最值得先记住的地标是：

| 方程含义 | 代码位置 |
|---|---|
| 一阶最优投资初值 | liquidation 的 `Policy.initialize` |
| liquidation 左边界价值 | `Boundary.compute_v_left` |
| 支付端接触条件 | `boundary_condition()` 中的 `grid.d2v[-1]` |
| hedge FOC 与 clipping | hedging 的 `Policy.cal_policy` |
| 保证金账户占比 | hedging 模型里的 `kappa = min(|psi| / pi, 1)` |

## 什么时候可以离开 BCW 主线

建议你至少能用自己的话回答下面四个问题，再开始大规模改模型：

1. 为什么 `d2v[-1]` 是右边界最关键的诊断量？
2. 为什么低现金状态下投资可能大幅为负？
3. 为什么 hedging 案例里 `psi` 会在左端贴着 `-pi`？
4. `solve`、`boundary_update`、`boundary_search` 三者分别适用于什么场景？

一旦这些问题你都能回答，就可以自然转向：

- [建模指南](./modeling-guide.md)
- [把 BCW 改成你自己的模型](./adapting-bcw-to-your-model.md)
