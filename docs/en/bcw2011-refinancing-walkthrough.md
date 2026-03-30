# BCW2011 Refinancing Walkthrough

Read this page after [BCW2011 Liquidation Walkthrough](./bcw2011-liquidation-walkthrough.md).

This page is the formula-first walkthrough for:

- `src/example/BCW2011Refinancing.py`

## Goal

By the end of this page, you should understand:

- why Case II turns the left boundary into a financing problem,
- why the solver must search both `v_left` and `s_max`,
- how the issuance target `m` is recovered numerically,
- how the `phi=1%` and `phi=0` comparison maps to Figure 3.

## Run Contract

Run this example from the repository root:

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011Refinancing.py
```

## What Changes Relative To Liquidation

The internal-financing region is unchanged. The state variable is still the cash-capital ratio `w`, and the interior HJB is still BCW Eq. (13). What changes is the lower boundary.

In liquidation, the lower boundary is exogenous:

$$
p(0) = l.
$$

In refinancing, the lower boundary becomes endogenous because the firm issues equity when it reaches zero cash instead of liquidating.

That change introduces:

- a value-matching equation at the issuance point,
- an optimal issuance-size condition at the post-issuance cash target `m`.

## Paper Equations Used In This Case

### Interior HJB And Investment Rule

The interior still uses BCW Eq. (13) and Eq. (14):

$$
r p(w) =
\left(i(w) - \delta\right)\left(p(w) - w p'(w)\right)
+ \left((r-\lambda)w + \mu - i(w) - g(i(w))\right)p'(w)
+ \frac{\sigma^2}{2} p''(w),
$$

$$
i(w) = \frac{1}{\theta}\left(\frac{p(w)}{p'(w)} - w - 1\right).
$$

### Issuance Value Matching: Eq. (19)

$$
p(0) = p(m) - \phi - (1+\gamma)m.
$$

This says the value just before issuance equals the post-issuance firm value minus fixed and proportional issuance costs.

### Optimal Issuance Size: Eq. (20)

$$
p'(m) = 1 + \gamma.
$$

This is the smooth-pasting condition at the return cash-capital ratio `m`.

### Right Boundary

The right side is still pinned by BCW Eq. (16) and Eq. (17):

$$
p'(\bar w)=1, \qquad p''(\bar w)=0.
$$

## Why There Are Two Boundary Targets

This case has two endogenous unknowns:

- the payout boundary `\bar w`,
- the left boundary value `p(0)`.

The issuance target `m` is not directly searched as a boundary variable. Instead, it is recovered from the solved grid as the point where:

$$
p'(m) = 1 + \gamma.
$$

This gives the repository workflow:

1. guess `v_left = p(0)` and `s_max = \bar w`,
2. solve the HJB on `[0, \bar w]`,
3. read `m` off the solved grid using the derivative condition,
4. evaluate the issuance value-matching residual,
5. update both unknowns until the left issuance condition and right super-contact condition both hold.

That is why the script uses a two-target boundary search with `method="hybr"` instead of `bisection`.

## How Those Equations Become FinHJB Objects

| Economic object | FinHJB object | Repository role |
|---|---|---|
| benchmark parameters plus issuance costs | `Parameter` | stores `phi`, `gamma`, and the baseline operating parameters |
| boundary values | `Boundary` | exposes `v_left` as a searched quantity and `v_right` as the payout-side boundary value |
| investment control | `PolicyDict` | stores `investment` |
| Eq. (14) | `Policy` | implicit update for `investment` |
| Eq. (13) | `Model.hjb_residual` | interior HJB |
| Eq. (19) | `refinancing_boundary_residual(...)` | left-boundary target |
| Eq. (20) | `return_cash_ratio_from_grid(...)` | recovers `m` from the solved derivative profile |

The important FinHJB design point is that `m` is not a separate state variable or separate boundary object. It is an economically meaningful interior point inferred from the solved grid.

## Why `hybr` Is The Right Search Method Here

The script searches two nonlinear targets simultaneously:

- `super_contact_residual(grid)` for the payout boundary,
- `refinancing_boundary_residual(grid)` for the issuance boundary.

This is qualitatively different from liquidation:

- liquidation has one scalar target and a robust bracket,
- refinancing has a coupled system because moving `v_left` changes the whole value function and therefore changes both `m` and the right boundary geometry.

That is why the repository standardizes this case on `hybr`.

## Figure 3: What The Comparison Means

![BCW refinancing main figure](./assets/bcw2011-refinancing-main.svg)

### Panel A: `p(w)`

The key comparison is at the left endpoint:

- with costly issuance, `p(0)` is still above liquidation value,
- with zero fixed issuance cost, the curve lifts further and the financing friction is milder.

This is the numerical version of BCW's condition that refinancing is globally preferred when `p(0) > l`.

### Panel B: `p'(w)`

Fixed issuance costs increase the marginal value of cash in low-cash states because internal liquidity helps the firm avoid paying those fixed costs too often.

### Panel C: `i(w)`

Investment is less distorted than in liquidation, but still below first best when financing is costly.

### Panel D: `i'(w)`

The steepness of `i'(w)` near the left side is a compact way to see how financing frictions transmit into real decisions.

## Stable Quantitative Targets

Healthy runs usually show:

- with `phi=1%`: `\bar w \approx 0.19`, `m \approx 0.06`, `p(0) > l`,
- with `phi=0`: `\bar w \approx 0.14`, `m \approx 0`,
- `p'(m) \approx 1.06` in both scenarios.

These are exactly the targets to compare against Figure 3.

## Code Inspection Pattern

```python
from src.example.BCW2011Refinancing import run_case

bundle = run_case(number=1000)
for label, result in bundle["results"].items():
    print(label, result["summary"])
```

For this case, the most informative summary fields are:

- `return_cash_ratio`,
- `dv_at_m`,
- `p0_above_l`,
- `payout_boundary`.

## How To Adapt This Pattern

Start from this case if your own model needs:

- issuance instead of liquidation,
- a left-boundary value-matching condition,
- an interior target like `m` defined by a derivative condition,
- more than one searched boundary unknown.

This is the right template for many financing models even when the later hedging and credit-line extensions are unnecessary.

## Next Step

- Continue to [BCW2011 Hedging Walkthrough](./bcw2011-hedging-walkthrough.md).
- Revisit [Results and Diagnostics](./results-and-diagnostics.md) if you want to inspect how `m` is inferred from `grid.dv`.
