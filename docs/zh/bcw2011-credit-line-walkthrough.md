# BCW2011 Credit Line 逐步讲解

建议在 [BCW2011 Hedging 逐步讲解](./bcw2011-hedging-walkthrough.md) 之后阅读。

这一页是下面这个仓库脚本的“公式到代码”讲解：

- `src/example/BCW2011CreditLine.py`

## 目标

读完以后，你应该能理解：

- 为什么状态空间会从 `[0, \bar w]` 扩展到 `[-c, \bar w]`；
- 为什么 BCW 的现金区和信用区可以放进一次 FinHJB 求解；
- 发行与 payout 条件如何和分段 HJB 并存；
- 为什么 Figure 7 是仓库里最典型的 regime-dependent residual 例子。

## 运行约定

请在仓库根目录执行：

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011CreditLine.py
```

## 相比 Refinancing，结构上变了什么

Refinancing 案例假设公司在现金归零时发行股票。Credit Line 案例在融资顺序里插入了一层：

1. 内部现金，
2. 信用额度，
3. 外部股权融资。

这同时改变了状态域和 HJB。

## 这个案例用到的论文方程

### 现金区

当 `w > 0` 时，边际融资来源仍然是内部现金，因此 value function 继续满足 BCW Eq. (13)：

$$
r p(w) =
\left(i(w) - \delta\right)\left(p(w) - w p'(w)\right)
+ \left((r-\lambda)w + \mu - i(w) - g(i(w))\right)p'(w)
+ \frac{\sigma^2}{2} p''(w).
$$

### 信用区：Eq. (31)

当 `w < 0` 时，边际融资来源变成信用额度，因此携带项发生切换：

$$
r p(w) =
\left(i(w) - \delta\right)\left(p(w) - w p'(w)\right)
+ \left((r+\alpha)w + \mu - i(w) - g(i(w))\right)p'(w)
+ \frac{\sigma^2}{2} p''(w).
$$

这两个区域在结构上唯一的差别就是融资项：

- 现金区是 `(r-\lambda)w`；
- 信用区是 `(r+\alpha)w`。

正是这一个切换，带来了论文里信用额度前后完全不同的流动性管理含义。

### 有信用额度时的发行条件

当公司把额度用满，走到 `w=-c` 时，发行条件变成：

$$
p(-c) = p(m) - \phi - (1+\gamma)(m+c),
$$

$$
p'(m) = 1 + \gamma.
$$

也就是说，信用额度改变了发行触发点和总发行规模，但发行后的 smooth-pasting 逻辑并没有变。

### `w=0` 处的连续与光滑

BCW 在论文里要求 `w=0` 处 value function 连续且光滑。

仓库实现采用的数值做法是：在 `[-c, \bar w]` 上解同一个 value function、同一套导数对象：

- residual 会在 `w` 变号时切换融资项；
- 但 `v`、`dv`、`d2v` 始终是同一个全局网格对象。

因此，`w=0` 处的拼接并不是通过额外加一个显式 boundary target 完成的，而是通过“单一全局对象 + 分段 residual”在数值上实现的。

## 分段问题如何变成 FinHJB 代码

| 经济对象 | FinHJB 对象 | 仓库里的角色 |
|---|---|---|
| 信用额度参数 | `Parameter` | 在 refinancing baseline 上增加 `c` 和 `alpha` |
| 扩展后的状态域 | `Boundary.compute_s_min(...)` | 设置 `s_min = -c` |
| 投资控制 | `PolicyDict` | 仍然只需要 `investment` |
| 投资 FOC | `Policy` | 仍然使用 Eq. (14) |
| 分段 HJB | `credit_line_hjb_residual(...)` + `Model.hjb_residual(...)` | 按区域切换融资项 |
| 发行边界 | `refinancing_boundary_residual(..., extra_raise=c)` | 把 Eq. (19) 调整成在 `w=-c` 触发发行 |

这里最值得学的模式是：

- 状态网格跨越一个 regime boundary；
- value function 仍然是全局统一的；
- residual 在不同区域切换。

## 为什么外层仍然搜索 `v_left` 和 `s_max`

虽然状态域更大了，但外层未知量仍然很熟悉：

- 左边界在 `w=-c` 处的 value，
- 右端 payout boundary `\bar w`。

发行规模仍然通过 `p'(m)=1+\gamma` 从网格中恢复。

所以仓库仍然使用双 target 的 `boundary_search(method="hybr")`，只不过左边发行残差要额外把 `c` 这部分 raise amount 算进去。

## Figure 7：如何读这个对照

![BCW credit line main figure](./assets/bcw2011-credit-line-main.svg)

### Panel A：`p(w)`

有 credit line 时，firm value 上升，payout boundary 左移。这意味着公司不需要再囤那么多 precautionary cash。

### Panel B：`p'(w)`

在 `w=0` 附近，边际现金价值相对无额度基准明显下降，因为“现金归零”不再意味着立刻要去外部融资。

### Panel C：`i(w)`

underinvestment 被大幅缓和。有额度时，`w=0` 附近投资仍然为正，而不是像无额度基准那样变成剧烈的 asset sales。

### Panel D：`i'(w)`

在 cash boundary 附近，投资对现金的敏感度变平了，因为融资 regime 的切换不再像无额度时那样陡峭。

## 稳定的量级检查

健康运行通常表现为：

- `c=20%` 时：`\bar w \approx 0.08`；
- `c=20%` 时：`c+m \approx 0.10`；
- `c=20%` 时：`p'(0) \approx 1.01`；
- 无 credit line 时：`\bar w \approx 0.19`、`p'(0) \approx 1.69`；
- 有 credit line 时：`i(0) > 0`；
- 无 credit line 时：`i(0) < 0`。

这些量就是和 BCW Figure 7 对照时最值得先看的检查点。

## 代码检查模式

```python
from src.example.BCW2011CreditLine import run_case

bundle = run_case(number=1000)
for label, result in bundle["results"].items():
    print(label, result["summary"])
```

这个案例最值得先看的字段是：

- `credit_limit`，
- `equity_raise_amount`，
- `dv_at_zero`，
- `investment_at_zero`，
- `state_min`。

## 如何把这个模式迁移到自己的模型

如果你的模型具有下面这些结构，就优先从这个案例起步：

- 仍是一维状态，但有多个融资 regime；
- 存在负状态的 debt region；
- 同一条网格上 residual 按区域切换；
- 发行发生在另一种融资来源耗尽之后。

这是仓库里最直接的“分段 residual”模板。

## 下一步

- 回到 [结果与诊断](./results-and-diagnostics.md)，直接检查负 `w` 区域上的网格结果。
- 然后再看 [把 BCW 改成你自己的模型](./adapting-bcw-to-your-model.md)，把这种 regime-switching 模式迁移到自己的问题上。
