# BCW2011 案例总览

这一页是仓库 BCW 路径的总入口。

如果你已经读过 [快速开始](./getting-started.md)，并想系统理解 `src/example/` 里四个 BCW 案例分别在教什么，就从这里继续。

仓库现在提供四个与论文主图对应的案例：

- `src/example/BCW2011Liquidation.py`
- `src/example/BCW2011Refinancing.py`
- `src/example/BCW2011Hedging.py`
- `src/example/BCW2011CreditLine.py`

论文转录稿作为统一公式来源保存在：

- `src/example/A_unified_theory_of_tobin's_q,_corporate_investment,_financing,_and_risk_management.md`

## BCW 路径到底是用来干什么的

BCW 主线的价值，在于它把“连续时间公司金融论文”到“可运行的一维 FinHJB 实现”这段桥搭得非常完整。

它同时教你三件事：

- BCW 如何利用齐次性把二维问题降成一维；
- 这个降维后的问题如何映射到 FinHJB 的类接口；
- 论文里的内生边界条件如何变成数值搜索 target。

## 共同记号与对象映射

四个案例都使用同一个一维降维：

$$
P(K, W) = K p(w), \qquad w = W/K.
$$

论文里的对象和仓库对象一一对应如下：

| 论文对象 | 含义 | 仓库对象 |
|---|---|---|
| `w` | 现金资本比 | `grid.s` |
| `p(w)` | 价值资本比 | `grid.v` |
| `p'(w)` | 边际现金价值 | `grid.dv` |
| `p''(w)` | 曲率 | `grid.d2v` |
| `q_a = p-w` | 平均 q | 派生序列 `qa` |
| `q_m = p-wp'` | 边际 q | 派生序列 `qm` |
| 策略函数 | `i(w)`、`\psi(w)` | `grid.policy[...]` |

而 FinHJB 的类接口映射也在四个脚本里保持稳定：

| FinHJB 类 | 在 BCW 里的角色 |
|---|---|
| `Parameter` | Table I 原始参数和案例特有参数 |
| `Boundary` | 左右边界值与状态域限制 |
| `PolicyDict` | 网格上的控制变量容器 |
| `Policy` | FOC 或显式策略更新 |
| `Model` | HJB 残差与外层边界 target |

## 四个案例分别教什么

| 案例 | 脚本 | 论文图 | 主要数值结构 | 主要经济含义 |
|---|---|---|---|---|
| Case I | `BCW2011Liquidation.py` | Figure 2 | 单 target 的 payout-boundary 搜索 | 极端融资约束会触发大规模 asset sales |
| Case II | `BCW2011Refinancing.py` | Figure 3 | 同时搜索 `s_max` 和 `v_left` | 股权发行会把 liquidation region 变成 issuance region |
| Case IV | `BCW2011Hedging.py` | Figure 6 | 双控制 HJB 与 hedge-region 诊断 | 对冲和流动性管理是互补的 |
| Case V | `BCW2011CreditLine.py` | Figure 7 | 单一网格上的分段 HJB | 信用额度会显著降低边际流动性价值 |

## 论文边界条件如何变成数值 target

学习 BCW 的一个核心原因，就是看清楚论文里的边界语言怎样变成可执行代码。

反复出现的模式是：

1. 论文给出某个边界值公式；
2. 论文再给出某个最优性条件，用来钉住边界位置；
3. 求解器在外层搜索，直到网格满足这个 residual。

例如：

- liquidation：搜索 `\bar w`，直到 `p''(\bar w)=0`；
- refinancing：同时搜索 `p(0)` 与 `\bar w`，再用 `p'(m)=1+\gamma` 恢复 `m`；
- hedging：保留 refinancing 的边界逻辑，但内部策略问题更丰富；
- credit line：保留发行与 payout 逻辑，同时按区域切换 HJB residual。

## 推荐阅读顺序

如果你的目标不只是“把脚本跑通”，而是想通过 BCW 学会包的建模方法，推荐按这个顺序读：

1. [安装与环境](./installation-and-environment.md)
2. [快速开始](./getting-started.md)
3. [BCW2011 Liquidation 逐步讲解](./bcw2011-liquidation-walkthrough.md)
4. [BCW2011 Refinancing 逐步讲解](./bcw2011-refinancing-walkthrough.md)
5. [BCW2011 Hedging 逐步讲解](./bcw2011-hedging-walkthrough.md)
6. [BCW2011 Credit Line 逐步讲解](./bcw2011-credit-line-walkthrough.md)
7. [结果与诊断](./results-and-diagnostics.md)
8. [把 BCW 改成你自己的模型](./adapting-bcw-to-your-model.md)

这里四个 walkthrough 是“公式到代码”的主桥。`结果与诊断` 则是当你已经理解案例结构之后，用来从求解器对象角度读解的补充页。

## 稳定量级检查

仓库里健康运行通常满足：

| 案例 | 稳定量级 |
|---|---|
| Liquidation | `\bar w \approx 0.22`、`p'(0) \approx 30`、`i(\bar w) \approx 10.5%` |
| Refinancing | `phi=1%` 时 `\bar w \approx 0.19`、`m \approx 0.06`；`phi=0` 时 `\bar w \approx 0.14`、`m \approx 0` |
| Hedging | costly margin：`w_- \approx 0.07`、`w_+ \approx 0.11`、`\bar w \approx 0.14`、`\psi \in [-5, 0]` |
| Credit line | `c=20%` 时 `\bar w \approx 0.08`、`c+m \approx 0.10`、`p'(0) \approx 1.01` |

在纠结小的网格差异之前，先看这些 headline number 是否站得住。

## 以后应该把哪一页当模板

如果后面你要把 BCW 改成自己的模型，优先选择结构最接近的案例：

- liquidation：一个控制、一个内生 payout boundary；
- refinancing：带发行、value matching 和 interior smooth-pasting；
- hedging：多控制与控制进入扩散项；
- credit line：单一网格上的 regime-dependent residual。

## 下一步

- 从 [BCW2011 Liquidation 逐步讲解](./bcw2011-liquidation-walkthrough.md) 开始。
- 当你想从求解器对象角度读 `run_case()` 返回值时，再配合 [结果与诊断](./results-and-diagnostics.md) 一起看。
