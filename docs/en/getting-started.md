# Getting Started

This page is the fastest path from "I cloned the repository" to "I can run a real HJB case and tell whether the result looks reasonable."

If your environment is not ready yet, start with [Installation and Environment](./installation-and-environment.md). If you want the full research context, use [BCW Case Study](./bcw2011-case-study.md) as your map.

Important scope note:

- if you installed `finhjb` from PyPI or via `uv add`, you can use the library API immediately,
- but the BCW scripts in `src/example/BCW2011Liquidation.py` and `src/example/BCW2011Hedging.py` are repository files,
- so the rest of this page assumes you are working from a repository checkout.

## Goal

By the end of this page, you should be able to:

- install the project and import `finhjb`,
- run the BCW liquidation example,
- run the BCW hedging example,
- check a few stable numerical diagnostics instead of guessing whether the run worked.

## Before You Start

From the repository root, make sure the package and its dependencies are available:

```bash
uv sync
uv run python -c "import finhjb; print(finhjb.__all__[:5])"
```

If you are on a headless machine or remote server, use:

```bash
export MPLBACKEND=Agg
```

That avoids Matplotlib GUI errors while keeping all numerical outputs unchanged.

If you are using only the published package and do not have the repository checkout, skip the BCW script commands below and go directly to:

- [Modeling Guide](./modeling-guide.md)
- [Solver Guide](./solver-guide.md)
- [API Reference](./api-reference.md)

## Step 1: Run the BCW Liquidation Example

The liquidation case is the best first run because it contains the essential ingredients:

- one state variable,
- one main policy variable,
- one right-boundary search problem,
- a very clear success criterion at the payout boundary.

Run:

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011Liquidation.py
```

What this script does:

1. builds BCW baseline parameters,
2. constructs a `Boundary`, `Policy`, and `Model`,
3. runs `solver.boundary_search(method="bisection")`,
4. prints the final state and grid diagnostics.

### What Success Looks Like

With the current repository configuration, a healthy run has the following features:

| Check | What you should expect |
|---|---|
| Left boundary value | `grid.v[0]` is exactly or extremely close to `0.9` |
| Right boundary slope | `grid.dv[-1]` is extremely close to `1.0` |
| Right boundary curvature | `grid.d2v[-1]` is near `0` |
| State upper bound | solved `s_max` lands around `0.22` rather than staying at the initial guess |
| Investment policy | very negative at low cash, then rises and turns positive near the right boundary |

One representative run in this repository produced:

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

Interpretation:

- the right boundary search succeeded because `d2v_right` is essentially zero,
- `dv[-1]` approaching `1` is consistent with the payout-side contact condition,
- the strongly negative low-cash investment reflects tight financing conditions.

## Step 2: Run the BCW Hedging Example

Once the liquidation example is stable, move to the hedging extension:

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011Hedging.py
```

This case adds:

- a second control `psi`,
- the margin-account share `kappa`,
- a refinancing condition for `v_left` that is encoded in the boundary-search targets,
- an additional `update_boundary(grid)` helper that demonstrates a boundary-update-compatible rule,
- the three-region hedge policy structure discussed in BCW.

### What Success Looks Like

For the current repository setup, a healthy hedging run has these characteristics:

| Check | What you should expect |
|---|---|
| Left boundary value | `v_left` is above the liquidation value because refinancing is now active |
| Right boundary curvature | `grid.d2v[-1]` is again very close to `0` |
| Hedge range | `psi` stays between `-pi` and `0` |
| Low-cash region | `psi` is pinned close to `-5.0` (`-pi`) |
| High-cash region | `psi` moves toward `0.0` |
| Investment policy | still negative in distressed states, positive near the right boundary |

One representative run produced:

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

The key sanity check is not one exact number. The robust pattern is:

- `psi` is fully binding in low-cash states,
- the hedge relaxes as cash rises,
- `d2v[-1]` still closes to zero.

For this specific implementation, you can also compare against BCW-style benchmark magnitudes:

- `w_-` is about `0.067`,
- `w_+` is about `0.115`,
- the payout boundary `w_bar` is about `0.1385`,
- `psi` stays in `[-5, 0]`.

## Step 3: Read the Output Instead of Just Running It

After either example finishes, the most useful object is the solved grid:

```python
grid = final_state.grid
print(grid.df.head())
print(grid.df.tail())
```

Focus on:

- `s`: the cash-capital ratio grid,
- `v`: value-capital ratio,
- `dv`: marginal value of cash,
- `d2v`: curvature and boundary contact diagnostics,
- policy columns such as `investment` and `psi`.

If you only look at one number, inspect:

```python
print(grid.d2v[-1])
```

That number tells you whether the right-boundary search is doing its job.

## Step 4: Save a Solved Object

The save/load API is useful once you have a good run and want to avoid re-solving immediately.

```python
state.grid.save("outputs/liquidation_grid")
loaded = fjb.load_grid("outputs/liquidation_grid")
print(loaded.df.head())
```

Quick chooser:

- `load_grid(path)`: one solved grid,
- `load_grids(path)`: multiple grids from continuation,
- `load_sensitivity_result(path)`: summary table plus all saved grids.

## Common First-Run Problems

### The script fails before solving

Go to [Troubleshooting](./troubleshooting.md) and check:

- environment install,
- JAX import issues,
- headless Matplotlib configuration.

### The script runs, but the right boundary looks wrong

Check:

```python
print(grid.dv[-1], grid.d2v[-1])
```

If `grid.d2v[-1]` is not near zero, review:

- [BCW Liquidation Walkthrough](./bcw2011-liquidation-walkthrough.md)
- [Results and Diagnostics](./results-and-diagnostics.md)
- [Solver Guide](./solver-guide.md)

### The policy values surprise you

That is common the first time. In BCW, negative investment in low-cash states is not automatically a bug. Read the interpretation sections in the walkthrough pages before changing the code.

## Where To Go Next

- Read [BCW Case Study](./bcw2011-case-study.md) for the full learning path.
- Read [BCW Liquidation Walkthrough](./bcw2011-liquidation-walkthrough.md) for equation-to-code details.
- Read [BCW Hedging Walkthrough](./bcw2011-hedging-walkthrough.md) for `psi`, `kappa`, and the three hedge regions.
- Read [Adapting BCW to Your Model](./adapting-bcw-to-your-model.md) once you can already reproduce the baseline examples.
