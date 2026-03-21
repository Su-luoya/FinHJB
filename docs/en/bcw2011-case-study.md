# BCW2011 Case Study (Equation-to-Code Mapping)

This page is for users who want both:

- paper-level reproduction, and
- code-level understanding.

Covered scripts:

- `src/example/BCW2011Liquidation.py` (Case I: Liquidation)
- `src/example/BCW2011Hedging.py` (Case II extension: Dynamic Hedging)

Single equation source:

- `src/example/A_unified_theory_of_tobin's_q,_corporate_investment,_financing,_and_risk_management.md`

All equation numbers and notation here follow that file.

## 1. Run First, Then Map

From repository root:

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011Liquidation.py
MPLBACKEND=Agg uv run python src/example/BCW2011Hedging.py
```

Notes:

- `MPLBACKEND=Agg` is useful in headless environments.
- Both scripts run `boundary_search(method="bisection")` and print `final_state` and `grid` diagnostics.

## 2. Notation Bridge (Paper -> Code)

| Paper symbol | Meaning | Code object | Code expression |
|---|---|---|---|
| `w = W/K` | cash-capital ratio (state variable) | `s` | `grid.s` |
| `p(w)` | value-capital ratio | `v` | `grid.v` |
| `p'(w)` | marginal value of cash | `dv` | `grid.dv` |
| `p''(w)` | curvature of value function | `d2v` | `grid.d2v` |
| `i(w)` | investment-capital ratio | `investment` | `grid.policy["investment"]` |
| `g(i)=theta*i^2/2` | quadratic adjustment cost | adjustment-cost term | `0.5 * p.theta * inv**2` |
| `psi(w)` | hedge position | `psi` | `grid.policy["psi"]` |
| `kappa(w)` | fraction of cash in margin account | `kappa` | `jnp.minimum(jnp.abs(psi)/p.pi, 1.0)` |

---

## 3. Case I (Liquidation): Equation-by-Equation Mapping

### 3.1 Eq.(7): first-best investment initializer

Paper:

```math
i^{FB}=r+\delta-\sqrt{(r+\delta)^2-\frac{2(\mu-(r+\delta))}{\theta}}
```

Code mapping: directly implemented in `Policy.initialize` as policy initializer.

```python
inv_first_best = (
    p.r + p.delta
    - ((p.r + p.delta) ** 2 - 2 * (p.mu - (p.r + p.delta)) / p.theta) ** 0.5
)
```

Under baseline parameters (`r=0.06, delta=0.1007, mu=0.18, theta=1.5`):

- `i_FB ≈ 0.15115` (about 15.1% annualized)

This is a useful first sanity anchor.

### 3.2 Eq.(13): HJB ODE split into code terms

Paper (internal-financing region):

```math
r p(w)= (i-\delta)(p-wp') + ((r-\lambda)w+\mu-i-g(i))p' + \frac{\sigma^2}{2}p''
```

Code in `Model.hjb_residual` uses residual form (`LHS - RHS = 0`):

```python
capital_drift = (inv - p.delta) * (v - s * dv)
discount = -p.r * v
cash_drift = ((p.r - p.lambda_) * s + p.mu - inv - 0.5 * p.theta * inv**2) * dv
diffusion = 0.5 * p.sigma**2 * d2v
residual = capital_drift + discount + cash_drift + diffusion
```

Term-by-term mapping:

| Eq.(13) term | Code expression | Interpretation |
|---|---|---|
| `(i-\delta)(p-wp')` | `(inv - p.delta) * (v - s * dv)` | net capital accumulation channel |
| `((r-\lambda)w+\mu-i-g(i))p'` | `((p.r - p.lambda_) * s + p.mu - inv - 0.5 * p.theta * inv**2) * dv` | cash drift weighted by marginal cash value |
| `(\sigma^2/2)p''` | `0.5 * p.sigma**2 * d2v` | diffusion (risk) channel |
| `-r p(w)` | `-p.r * v` | discount channel |

### 3.3 Eq.(14): why the investment FOC is coded as an implicit residual

Paper:

```math
i(w)=\frac{1}{\theta}\left(\frac{p(w)}{p'(w)}-w-1\right)
```

Code in `cal_investment_without_explicit`:

```python
(1 / p.theta) * (v / dv - s - 1) - investment
```

This is the same condition written as `i*(w) - i = 0`, solved by
`implicit_policy(solver="lm")`.

Why this form:

- keeps a unified root-finding interface for simple and complex FOCs;
- improves extensibility and numerical control.

### 3.4 Boundary conditions: Eq.(18), Eq.(16), Eq.(17)

| Paper condition | Code implementation | Notes |
|---|---|---|
| Eq.(18) `p(0)=l` | `Boundary.compute_v_left -> return p.l` | liquidation boundary |
| Eq.(17) `p''(w̄)=0` | `s_max_condition -> grid.d2v[-1]` | super-contact numerical target |
| Eq.(16) `p'(w̄)=1` | enforced jointly through right-boundary construction + ODE solution | script uses Eq.(17) as the primary boundary-search target |

### 3.5 Minimal output checks

1. `grid.v[0]` is near `l=0.9`.
2. `grid.d2v[-1]` is near zero (for example around `1e-6`).
3. `investment` drops strongly in low-`w` states (precautionary behavior).

---

## 4. Case II (Hedging): Equation-by-Equation Mapping

### 4.1 Eq.(26): what is newly added in cash dynamics

Relative to the baseline cash dynamics, two additions matter:

1. margin-account flow cost: `-epsilon * kappa * W dt`
2. futures-related diffusion exposure: `+ psi * sigma_m * W dB`

In code:

- drift part enters `cash_flow_drift`;
- risk part enters `total_variance`.

### 4.2 Eq.(28): hedging HJB decomposition in code

Paper:

```math
rP = (I-\delta K)P_K + ((r-\lambda)W + \mu K - I - G(I,K) - \epsilon\kappa W)P_W
+ \frac{1}{2}(\sigma^2K^2 + \psi^2\sigma_m^2W^2 + 2\rho\sigma\sigma_m\psi WK)P_{WW}
```

Code split:

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

Term-by-term mapping:

| Eq.(28) term | Code term | Meaning |
|---|---|---|
| `-\epsilon\kappa W` | `- p.epsilon * kappa * s` (inside `cash_flow_drift`) | extra margin-account carry cost |
| `\sigma^2K^2` | `p.sigma**2` | baseline business risk |
| `\psi^2\sigma_m^2W^2` | `(psi**2) * (p.sigma_m**2) * (s**2)` | variance from hedge position |
| `2\rho\sigma\sigma_m\psi WK` | `2 * p.rho * p.sigma * p.sigma_m * psi * s` | covariance between firm and market shocks |

### 4.3 Eq.(29): margin-account rule in code

Paper:

```math
\kappa = \min\{|\psi|/\pi, 1\}
```

Code:

```python
kappa = jnp.minimum(jnp.abs(psi) / p.pi, 1.0)
```

Interpretation:

- if `|psi|/pi < 1`, margin account uses part of cash (interior);
- if `|psi|/pi >= 1`, `kappa=1`, all cash is tied to margin (binding).

### 4.4 Eq.(30): interior hedge FOC mapped term-by-term

Paper:

```math
\psi^*(w)=\frac{1}{w}\left(-\frac{\rho\sigma}{\sigma_m}-\frac{\epsilon}{\pi}\frac{p'(w)}{p''(w)}\frac{1}{\sigma_m^2}\right)
```

Code:

```python
psi_interior = (
    1 / s * (
        (-p.rho * p.sigma / p.sigma_m)
        - ((p.epsilon * dv) / (p.pi * d2v * p.sigma_m**2))
    )
)
```

Subterm mapping:

| Eq.(30) subterm | Code expression |
|---|---|
| `1/w` | `1 / s` |
| `-(rho*sigma/sigma_m)` | `(-p.rho * p.sigma / p.sigma_m)` |
| `-(epsilon/pi)*(p'/p'')*(1/sigma_m^2)` | `- ((p.epsilon * dv) / (p.pi * d2v * p.sigma_m**2))` |

Economic intuition:

- first term is the frictionless hedging motive;
- second term is the margin-cost correction;
- when correction dominates, optimal hedge moves toward zero.

### 4.5 How `w_-` and `w_+` are implemented

Paper's three regions:

1. `w <= w_-`: maximum-hedging region, `psi=-pi`
2. `w_- < w < w_+`: interior region, Eq.(30)
3. `w >= w_+`: zero-hedging region, `psi=0`

Code:

```python
psi_clipped = jnp.maximum(psi_interior, -p.pi)
marginal_benefit = p.rho * p.sigma / p.sigma_m
marginal_cost = jnp.abs((p.epsilon * dv) / (p.pi * d2v * p.sigma_m**2))
should_hedge = marginal_cost < marginal_benefit
new_psi = jnp.where(should_hedge, psi_clipped, 0.0)
```

Interpretation:

- `psi_clipped` enforces the low-cash cap (`w_-` side);
- `should_hedge` switches to zero-hedging beyond `w_+`.

### 4.6 Two numeric anchors you can verify immediately

With baseline parameters (`rho=0.8, sigma=0.09, sigma_m=0.2`):

1. frictionless hedge core term `-(rho*sigma/sigma_m) = -0.36`
2. first-best investment initializer `i_FB ≈ 0.15115`

If either number is off, check parameter overrides first.

---

## 5. Parameter Experiment Template (with equation-level direction)

In `BCW2011Hedging.py`, change one parameter at a time:

1. `epsilon: 0.005 -> 0.010`
- Eq.(30) margin correction becomes stronger, so `psi` moves toward 0 and no-hedge region expands.
2. `pi: 5.0 -> 3.0`
- cap `psi=-pi` becomes tighter; low-cash states become more likely to be constraint-bound.
3. `rho: 0.8 -> 0.3`
- frictionless motive `-(rho*sigma/sigma_m)` weakens in magnitude, reducing hedge demand.

---

## 6. Convergence and Diagnostics (priority order)

1. `boundary_search` fails to converge
- first adjust `BoundaryConditionTarget(low/high)` brackets;
- then increase `bs_max_iter`, and only then loosen `bs_tol`.
2. `d2v[-1]` not close to zero
- increase grid size `number` (for example `1000 -> 2000`);
- prefer `derivative_method="central"`.
3. unstable `psi` near left endpoint
- inspect `dv/d2v` stability in very small-`s` region;
- validate medium/high-`w` shape first, then refine boundary-side settings.

