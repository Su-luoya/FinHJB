# Confirmed Model Specification

## Research Goal

Reproduce BCW `Case II: Refinancing` as a one-dimensional FinHJB model and compare the two Figure 3 cases:

- fixed issuance cost `phi = 1%`
- no fixed issuance cost `phi = 0`

## Environment

- target environment: repo-backed FinHJB checkout
- smoke test for runnable delivery: `uv run python -c "import finhjb"`
- reason: the evaluation depends on repository-local examples, fixtures, and the skill-local test bundle rather than only the published wheel

## State Variable

- paper symbol: `w = W/K`
- FinHJB state symbol: `s`
- meaning: cash-capital ratio
- domain: `w >= 0`, with the right endpoint determined endogenously by the payout boundary

## Value Object

- paper object: `P(K, W) = K p(w)`
- solved object in code: `p(w)` represented on the grid as `v`

## Controls

- `investment`
  - paper symbol: `i(w)`
  - meaning: investment-capital ratio
  - update rule: Eq. (14)
  - implementation style: implicit residual update as in the liquidation example

No hedging or margin-account control is part of this case.

## HJB Equation

Use BCW Eq. (13):

`r p(w) = (i(w) - delta) (p(w) - w p'(w)) + ((r - lambda) w + mu - i(w) - g(i(w))) p'(w) + 0.5 sigma^2 p''(w)`

with quadratic adjustment cost `g(i) = theta i^2 / 2`.

## Baseline Policy Logic

Use BCW Eq. (14):

`i(w) = (1/theta) * (p(w)/p'(w) - w - 1)`

## Boundary Logic

### Payout Side

- marginal-value condition: Eq. (16), `p'(w_bar) = 1`
- super-contact condition: Eq. (17), `p''(w_bar) = 0`

### Refinancing Side

- financing boundary: `w = 0`
- value matching after issuance: Eq. (19), `p(0) = p(m) - phi - (1 + gamma) m`
- smooth pasting at the return cash-capital ratio: Eq. (20), `p'(m) = 1 + gamma`

## Numerical Method Choices

- derivative method: `central`
- derivative reason: the diffusion term in Eq. (13) is `0.5 sigma^2 p''(w)` with `sigma > 0`, so the fixture does not face left-edge or right-edge diffusion degeneracy
- boundary target count: `2`
- target-count default: `bisection`
- final search method in the archived fixture: `hybr`
- search-method repair note: the post-generation test loop kept the fixed-cost case stable under the default heuristic, but promoted the final implementation to `hybr` because the `phi = 0` comparison under-shot the paper's payout boundary under the two-target default

## Parameters

Baseline calibration from Table I:

- `r = 0.06`
- `delta = 0.1007`
- `mu = 0.18`
- `sigma = 0.09`
- `theta = 1.5`
- `lambda = 0.01`
- `l = 0.9`
- `gamma = 0.06`

Comparison values:

- `phi = 0.01`
- `phi = 0.0`

## Expected Quantitative Targets

For `phi = 0.01`:

- payout boundary near `0.19`
- return cash-capital ratio `m` near `0.06`
- `p(0) > l`
- `p'(0)` around `1.7`
- investment at the payout boundary near `0.11`

For `phi = 0.0`:

- payout boundary near `0.14`
- return cash-capital ratio near `0.0`

## Deliverables

- `BCWrefinancing.py`
- a Figure 3-style four-panel comparison plot
- runtime summary data written into `artifacts/`
- a post-generation test report written into `artifacts/test_report.json`
