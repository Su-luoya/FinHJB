# BCW2011 Liquidation 逐步讲解

建议在 [快速开始](./getting-started.md) 和 [BCW2011 案例总览](./bcw2011-case-study.md) 之后阅读这一页。

这一页是下面这个仓库脚本的“公式到代码”讲解：

- `src/example/BCW2011Liquidation.py`

## 目标

读完以后，你应该能够双向理解这个案例：

- 从 BCW 论文里的 liquidation 方程走到 FinHJB 实现；
- 从 FinHJB 里的类和求解流程，反推它们各自对应的经济含义。

这是最适合入门的一页，因为这个案例只有：

- 一个状态变量，
- 一个控制变量，
- 一个内生边界 target，
- 没有再融资，也没有分段 regime。

## 运行约定

请在仓库根目录执行：

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011Liquidation.py
```

这套 BCW 示例按“仓库根目录运行”的方式维护，不再围绕 `src/example` 内部本地直跑做兼容。

## 经济设定与状态降维

BCW 原始问题写在资本 `K` 和现金 `W` 上。FinHJB 当前解的是利用齐次性降维后的单状态版本：

$$
P(K, W) = K p(w), \qquad w = W/K.
$$

正是这一步，把原来的二维公司金融问题变成了当前包可以直接求解的一维 HJB。

论文里的核心对象对应为：

$$
P_K = p(w) - w p'(w), \qquad P_W = p'(w), \qquad P_{WW} = p''(w) / K.
$$

在仓库对象里，这些量对应到：

- `grid.s`：状态网格 `w`，
- `grid.v`：价值资本比 `p(w)`，
- `grid.dv`：现金的边际价值 `p'(w)`，
- `grid.d2v`：曲率 `p''(w)`。

## 这个案例用到的论文方程

Liquidation 案例使用的是 BCW 的内部融资 HJB，加上 liquidation / payout 边界。

### HJB：Eq. (13)

$$
r p(w) =
\left(i(w) - \delta\right)\left(p(w) - w p'(w)\right)
+ \left((r-\lambda)w + \mu - i(w) - g(i(w))\right)p'(w)
+ \frac{\sigma^2}{2} p''(w).
$$

在 BCW 的二次调整成本下，

$$
g(i) = \frac{\theta i^2}{2}.
$$

### 投资 FOC：Eq. (14)

$$
i(w) = \frac{1}{\theta}\left(\frac{p(w)}{p'(w)} - w - 1\right).
$$

### 边界条件：Eq. (16)-(18)

在 payout 边界 `\bar w`：

$$
p'(\bar w) = 1, \qquad p''(\bar w) = 0.
$$

在 liquidation 边界：

$$
p(0) = l.
$$

## 这些方程如何变成 FinHJB 对象

仓库实现遵循一套很稳定的对象映射：

| 经济对象 | FinHJB 对象 | 在本案例中的作用 |
|---|---|---|
| 基准参数 | `Parameter` | 保存 Table I 参数，如 `r`、`delta`、`mu`、`sigma`、`theta`、`lambda_`、`l` |
| 左右边界值 | `Boundary` | 固定 `p(0)=l`，并提供 payout 侧的闭式 value |
| 控制容器 | `PolicyDict` | 这里只保存单个控制 `investment` |
| 投资更新 | `Policy` | 用隐式策略残差表达 Eq. (14) |
| HJB 残差 | `Model` | 在内部网格上实现 Eq. (13) |

更具体地说：

- Eq. (14) 通过 `investment_rule_residual(...)` 和 `Policy.cal_investment(...)` 实现；
- Eq. (13) 通过 `standard_hjb_residual(...)` 和 `Model.hjb_residual(...)` 实现；
- `Boundary.compute_v_left(...)` 返回 liquidation value `l`；
- `Boundary.compute_v_right(...)` 使用与 Eq. (16) 一致的 payout 侧闭式。

这也是 FinHJB 里一维单控制模型最标准的组织方式：

1. `Parameter` 放原始参数；
2. `Boundary` 放边界值；
3. `PolicyDict` 放控制变量；
4. `Policy` 放 FOC 或显式控制更新；
5. `Model` 放 HJB 本体。

## 为什么数值工作流是 `boundary_search(method="bisection")`

Liquidation 案例数值上只需要搜索一个内生对象：

- payout 边界 `\bar w`。

左边界已经固定为 `w=0` 且 `p(0)=l`。右边界则由 super-contact 条件决定：

$$
p''(\bar w) = 0.
$$

在数值实现里，这变成：

- 搜索 `s_max = \bar w`，
- 检查 `grid.d2v[-1]`，
- 当右尾曲率逼近零时停止。

这正是脚本使用一维 `boundary_search()` 加 `bisection` 的原因：

- 只有一个未知 target，
- 搜索区间在经济上很好设定，
- 根条件是标量问题，bisection 很稳。

## 仓库里的边界逻辑到底分几层

这个案例的边界信息可以分成三层：

1. 左边界：
   `Boundary.compute_v_left(...) = l`

2. 右边界 value：
   脚本使用与 BCW payout region 相容的闭式边界值，并内含 `p'(\bar w)=1`

3. 右边界 optimality target：
   `super_contact_residual(grid) = grid.d2v[-1]`

这三层必须区分开。FinHJB 里：

- 边界值负责告诉求解器“网格边缘的 value 是什么”；
- 边界 target 负责告诉外层搜索“边界本身应该往哪边移动”。

## Figure 2：如何按经济含义读图

![BCW liquidation main figure](./assets/bcw2011-liquidation-main.svg)

### Panel A：`p(w)`

价值资本比从 liquidation value `l=0.9` 出发，始终高于 liquidation line `l+w`，并在 `\bar w \approx 0.22` 附近平滑接入 payout boundary。

这对应 BCW 的核心结论之一：即使无法再融资，公司也不会在现金还大于零时提前清算。

### Panel B：`p'(w)`

当 `w \to 0` 时，边际现金价值迅速爆炸。因为在这个案例里，每一单位额外现金都能显著推迟被迫清算。

### Panel C：`i(w)`

在低现金区域，投资转成负值。用 BCW 的语言，这就是公司通过 asset sales 远离 liquidation boundary。

### Panel D：`i'(w)`

投资随现金上升，但不是线性的。这个对象比 `i(w)` 更直接地告诉你“投资-现金敏感度”。

## 稳定的量级检查

健康运行通常应当看到：

- `\bar w \approx 0.22`，
- `p'(0) \approx 30`，
- `i(\bar w) \approx 10.5%`，
- `w=0` 附近投资显著为负，
- `p''(\bar w)` 数值上接近零。

在解释更细的图形差异之前，先看这些量级是否站住。

## 代码检查模式

```python
from src.example.BCW2011Liquidation import run_case

bundle = run_case(number=1000)
result = bundle["results"]["baseline"]

print(result["summary"])
print(result["grid"].df.head())
print(result["grid"].df.tail())
```

这个案例最值得先看的量是：

- `result["summary"]["payout_boundary"]`，
- `result["summary"]["dv_at_zero"]`，
- `result["grid"].d2v[-1]`，
- `result["grid"].policy["investment"]`。

## 如何把这个模式迁移到自己的模型

如果你的模型仍然具有下面这些结构，就优先从这个案例起步：

- 一个降维后状态变量，
- 一个控制变量，
- 固定左边界，
- 右端一个内生 payout boundary。

只有当你的模型真的需要以下结构时，才应跳到后面的案例：

- 发行与 value matching，
- 多控制变量，
- 或按区域切换 residual。

## 下一步

- 继续看 [BCW2011 Refinancing 逐步讲解](./bcw2011-refinancing-walkthrough.md)。
- 当你想从“求解器对象”的角度读 `grid`、`summary` 和边界诊断时，再配合 [结果与诊断](./results-and-diagnostics.md) 一起看。
