# Getting Started

This page is the repository quickstart for the BCW path.

Use it if your question is: “I cloned the repository. How do I run the four BCW examples and tell whether the outputs look healthy?”

If you want the package-only path, read [Library Quickstart](./quickstart-library.md) instead.

## Goal

By the end of this page, you should be able to:

- confirm the repository environment works,
- run all four BCW example scripts,
- recognize the main success patterns without reading every printed line.

This page is intentionally execution-first. For derivations, boundary logic, and equation-to-code mapping, move from here into the four BCW walkthroughs.

## Step 1: Prepare The Repository Environment

From the repository root:

```bash
uv sync
uv run python -c "import finhjb as fjb; print(fjb.__all__[:5])"
```

If you are on a headless machine, also set:

```bash
export MPLBACKEND=Agg
```

The BCW scripts are documented as repository-root examples. The supported usage pattern is:

```bash
uv run python src/example/BCW2011Liquidation.py
```

not local-directory execution from inside `src/example/`.

## Step 2: Run Case I

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011Liquidation.py
```

Healthy runs usually show `w_bar ≈ 0.22`, `p'(0) ≈ 30`, and a strongly negative investment policy at very low cash.

## Step 3: Run Case II

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011Refinancing.py
```

Healthy runs usually show:

- with `phi=1%`: `w_bar ≈ 0.19`, `m ≈ 0.06`,
- with `phi=0`: `w_bar ≈ 0.14`, `m ≈ 0`.

## Step 4: Run Case IV

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011Hedging.py
```

Healthy runs usually show `w_- ≈ 0.07`, `w_+ ≈ 0.11`, `w_bar ≈ 0.14`, and `psi in [-5, 0]` for the costly-margin case.

## Step 5: Run Case V

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011CreditLine.py
```

Healthy runs usually show `w_bar ≈ 0.08`, `c+m ≈ 0.10`, and `p'(0)` near `1.01` when the credit line is active.

## Step 6: Read The Result Intentionally

After a run, check these first:

```python
print(bundle["artifact_paths"])
print(bundle["results"])
```

If you want the solved grid for one scenario:

```python
result = bundle["results"]["fixed-cost"]
print(result["summary"])
print(result["grid"].df.head())
print(result["grid"].df.tail())
```

## Where To Go Next

- [BCW2011 Case Study](./bcw2011-case-study.md)
- [BCW2011 Liquidation Walkthrough](./bcw2011-liquidation-walkthrough.md)
- [BCW2011 Refinancing Walkthrough](./bcw2011-refinancing-walkthrough.md)
- [BCW2011 Hedging Walkthrough](./bcw2011-hedging-walkthrough.md)
- [BCW2011 Credit Line Walkthrough](./bcw2011-credit-line-walkthrough.md)

Use the walkthroughs when you want the full bridge from paper equations to `Parameter` / `Boundary` / `PolicyDict` / `Policy` / `Model`.
