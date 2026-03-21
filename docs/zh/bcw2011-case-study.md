# BCW2011 案例教程（公式-代码逐项映射版）

本页面向“要复现论文、也要看懂代码”的用户。

对应脚本：

- `src/example/BCW2011Liquidation.py`（Case I: Liquidation）
- `src/example/BCW2011Hedging.py`（Case II 扩展: Dynamic Hedging）

唯一公式真源：

- `src/example/A_unified_theory_of_tobin's_q,_corporate_investment,_financing,_and_risk_management.md`

本页所有公式编号、记号解释均与该文件一致。

## 1. 先跑通，再对照

在仓库根目录运行：

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011Liquidation.py
MPLBACKEND=Agg uv run python src/example/BCW2011Hedging.py
```

说明：

- `MPLBACKEND=Agg` 适用于无 GUI 环境。
- 两个脚本都会执行 `boundary_search(method="bisection")` 并输出 `final_state`、`grid`。

## 2. 记号桥接总表（论文 -> 代码）

| 论文记号 | 经济含义 | 代码对象 | 在代码中的表达 |
|---|---|---|---|
| `w = W/K` | 现金-资本比（状态变量） | `s` | `grid.s` |
| `p(w)` | 价值-资本比 | `v` | `grid.v` |
| `p'(w)` | 现金边际价值 | `dv` | `grid.dv` |
| `p''(w)` | 价值函数曲率 | `d2v` | `grid.d2v` |
| `i(w)` | 投资-资本比 | `investment` | `grid.policy["investment"]` |
| `g(i)=theta*i^2/2` | 二次调整成本 | 调整成本项 | `0.5 * p.theta * inv**2` |
| `psi(w)` | 期货对冲仓位 | `psi` | `grid.policy["psi"]` |
| `kappa(w)` | 保证金账户现金占比 | `kappa` | `jnp.minimum(jnp.abs(psi)/p.pi, 1.0)` |

---

## 3. Case I（Liquidation）逐公式对照

### 3.1 Eq.(7): first-best 投资初值

论文：

```math
i^{FB}=r+\delta-\sqrt{(r+\delta)^2-\frac{2(\mu-(r+\delta))}{\theta}}
```

代码映射：`Policy.initialize` 里直接实现该表达式，用作初始策略。

```python
inv_first_best = (
    p.r + p.delta
    - ((p.r + p.delta) ** 2 - 2 * (p.mu - (p.r + p.delta)) / p.theta) ** 0.5
)
```

基准参数下（`r=0.06, delta=0.1007, mu=0.18, theta=1.5`）：

- `i_FB ≈ 0.15115`（年化约 15.1%）

这与论文定量部分一致，可作为你检查初始化是否正确的第一锚点。

### 3.2 Eq.(13): HJB ODE 拆成四项后如何落在代码里

论文（内部融资区 ODE）：

```math
r p(w)= (i-\delta)(p-wp') + ((r-\lambda)w+\mu-i-g(i))p' + \frac{\sigma^2}{2}p''
```

代码在 `Model.hjb_residual` 中写成“左边减右边后的残差 = 0”形式：

```python
capital_drift = (inv - p.delta) * (v - s * dv)
discount = -p.r * v
cash_drift = ((p.r - p.lambda_) * s + p.mu - inv - 0.5 * p.theta * inv**2) * dv
diffusion = 0.5 * p.sigma**2 * d2v
residual = capital_drift + discount + cash_drift + diffusion
```

逐项映射：

| Eq.(13) 中的项 | 代码表达 | 经济含义 |
|---|---|---|
| `(i-\delta)(p-wp')` | `(inv - p.delta) * (v - s * dv)` | 资本净积累对企业价值的贡献 |
| `((r-\lambda)w+\mu-i-g(i))p'` | `((p.r - p.lambda_) * s + p.mu - inv - 0.5 * p.theta * inv**2) * dv` | 现金漂移乘以现金边际价值 |
| `(\sigma^2/2)p''` | `0.5 * p.sigma**2 * d2v` | 现金风险（扩散）对价值的影响 |
| `-r p(w)` | `-p.r * v` | 贴现项 |

### 3.3 Eq.(14): 投资 FOC 在代码里为何写成“隐式残差”

论文：

```math
i(w)=\frac{1}{\theta}\left(\frac{p(w)}{p'(w)}-w-1\right)
```

代码在 `cal_investment_without_explicit` 里写为：

```python
(1 / p.theta) * (v / dv - s - 1) - investment
```

这不是改了公式，而是把 `i^*(w) - i = 0` 交给 `implicit_policy(solver="lm")` 求根。

优点：

- 可以与更复杂 FOC 统一成同一个隐式求解框架；
- 数值上便于做稳定迭代和未来扩展。

### 3.4 边界条件：Eq.(18), Eq.(16), Eq.(17)

在脚本里对应关系如下：

| 论文条件 | 代码实现 | 说明 |
|---|---|---|
| Eq.(18) `p(0)=l` | `Boundary.compute_v_left -> return p.l` | 清算边界 |
| Eq.(17) `p''(w̄)=0` | `s_max_condition -> grid.d2v[-1]` | 右端 super-contact 数值目标 |
| Eq.(16) `p'(w̄)=1` | 通过右端闭式值构造与整体解共同满足 | 当前脚本主搜索目标是 Eq.(17)，Eq.(16) 通过边界结构与 ODE 联立实现 |

### 3.5 你应该如何判读输出

最少看 3 个检查点：

1. `grid.v[0]` 是否接近 `l=0.9`。
2. `grid.d2v[-1]` 是否足够接近 0（如 `1e-6` 量级）。
3. `investment` 在低 `w` 区域是否明显下降（融资紧约束下的防御性行为）。

---

## 4. Case II（Hedging）逐公式对照

### 4.1 Eq.(26): 现金动态新增了什么

在基准现金动态里，新增两块：

1. 保证金账户流动成本：`-epsilon * kappa * W dt`
2. 期货头寸收益扩散项：`+ psi * sigma_m * W dB`

在代码中，对应进入 HJB 的方式是：

- 漂移项进入 `cash_flow_drift`；
- 风险项进入 `total_variance`。

### 4.2 Eq.(28): 对冲版 HJB 在代码中的精确分解

论文：

```math
rP = (I-\delta K)P_K + ((r-\lambda)W + \mu K - I - G(I,K) - \epsilon\kappa W)P_W
+ \frac{1}{2}(\sigma^2K^2 + \psi^2\sigma_m^2W^2 + 2\rho\sigma\sigma_m\psi WK)P_{WW}
```

代码拆成 4 段：

```python
drift_K = (inv - p.delta) * (v - s * dv)
drift_W = cash_flow_drift * dv
total_variance = (
    p.sigma**2
    + (psi**2) * (p.sigma_m**2) * (s**2)
    + 2 * p.rho * p.sigma * p.sigma_m * psi * s
)
diffusion = 0.5 * total_variance * d2v
discount = -p.r * v
```

逐项映射：

| Eq.(28) 项 | 代码项 | 含义 |
|---|---|---|
| `-\epsilon\kappa W` | `- p.epsilon * kappa * s`（在 `cash_flow_drift`） | 保证金账户额外持有成本 |
| `\sigma^2K^2` | `p.sigma**2` | 企业基本波动 |
| `\psi^2\sigma_m^2W^2` | `(psi**2) * (p.sigma_m**2) * (s**2)` | 对冲头寸带来的额外方差 |
| `2\rho\sigma\sigma_m\psi WK` | `2 * p.rho * p.sigma * p.sigma_m * psi * s` | 业务风险与市场风险协方差 |

### 4.3 Eq.(29): 保证金约束如何落地

论文：

```math
\kappa = \min\{|\psi|/\pi, 1\}
```

代码：

```python
kappa = jnp.minimum(jnp.abs(psi) / p.pi, 1.0)
```

解释：

- 当 `|psi|/pi < 1`，保证金账户只需占用部分现金（interior）。
- 当 `|psi|/pi >= 1`，`kappa=1`，所有现金都被保证金占用（约束绑定）。

### 4.4 Eq.(30): interior hedge FOC 的“每一项”在代码里在哪里

论文：

```math
\psi^*(w)=\frac{1}{w}\left(-\frac{\rho\sigma}{\sigma_m}-\frac{\epsilon}{\pi}\frac{p'(w)}{p''(w)}\frac{1}{\sigma_m^2}\right)
```

代码：

```python
psi_interior = (
    1 / s * (
        (-p.rho * p.sigma / p.sigma_m)
        - ((p.epsilon * dv) / (p.pi * d2v * p.sigma_m**2))
    )
)
```

逐项对照：

| Eq.(30) 子项 | 代码表达 |
|---|---|
| `1/w` | `1 / s` |
| `-(rho*sigma/sigma_m)` | `(-p.rho * p.sigma / p.sigma_m)` |
| `-(epsilon/pi)*(p'/p'')*(1/sigma_m^2)` | `- ((p.epsilon * dv) / (p.pi * d2v * p.sigma_m**2))` |

经济直觉：

- 第一项是“无摩擦基准对冲动机”；
- 第二项是“保证金成本修正项”；
- 当修正项把整体仓位推向 0 时，会进入零对冲区。

### 4.5 `w_-` 与 `w_+` 是怎么在代码里实现的

论文中三分区：

1. `w <= w_-`：最大对冲区，`psi=-pi`
2. `w_- < w < w_+`：interior，使用 Eq.(30)
3. `w >= w_+`：零对冲区，`psi=0`

代码对应：

```python
psi_clipped = jnp.maximum(psi_interior, -p.pi)
marginal_benefit = p.rho * p.sigma / p.sigma_m
marginal_cost = jnp.abs((p.epsilon * dv) / (p.pi * d2v * p.sigma_m**2))
should_hedge = marginal_cost < marginal_benefit
new_psi = jnp.where(should_hedge, psi_clipped, 0.0)
```

解释：

- `psi_clipped` 实现 `w_-` 左侧上限（不能比 `-pi` 更小）。
- `should_hedge` 决定是否越过 `w_+` 进入零对冲。

### 4.6 两个可直接核对的数值锚点

基准参数（`rho=0.8, sigma=0.09, sigma_m=0.2`）下：

1. 无摩擦对冲核心项 `-(rho*sigma/sigma_m) = -0.36`。
2. first-best 投资初值 `i_FB ≈ 0.15115`。

如果这两个数你在脚本里算不出来，优先检查参数是否被改动。

---

## 5. 参数实验模板（带公式方向）

在 `BCW2011Hedging.py` 修改参数后重跑，建议只改一个参数：

1. `epsilon: 0.005 -> 0.010`
- Eq.(30) 中保证金修正项权重上升，`psi` 更靠近 0，零对冲区扩大。
2. `pi: 5.0 -> 3.0`
- `psi=-pi` 的上限更紧，低现金状态更容易“顶格受限”。
3. `rho: 0.8 -> 0.3`
- 无摩擦对冲动机项 `-(rho*sigma/sigma_m)` 绝对值下降，整体对冲需求减弱。

---

## 6. 收敛与异常排查（按优先级）

1. `boundary_search` 不收敛
- 先调整 `BoundaryConditionTarget(low/high)` bracket；
- 再增加 `bs_max_iter`，最后再放宽 `bs_tol`。
2. `d2v[-1]` 不接近 0
- 提高 `number`（如 `1000 -> 2000`）；
- 优先使用 `derivative_method="central"`。
3. `psi` 在左端点异常抖动
- 检查极小 `s` 区域的 `dv/d2v` 数值稳定性；
- 先确认中高 `w` 区域形状正确，再回头调边界。

