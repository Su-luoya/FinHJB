# Getting Started

Use this page as an operational checklist for the four BCW repository examples, after the environment is ready and before you start reading the derivation-heavy walkthroughs.

The objective is simple: run the four scripts from the repository root and compare the output to a small set of headline magnitudes.

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

Use `w_bar ≈ 0.22`, `p'(0) ≈ 30`, and strongly negative investment at very low cash as the first-pass checks.

## Step 3: Run Case II

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011Refinancing.py
```

Use these magnitudes as the first checks:

- with `phi=1%`: `w_bar ≈ 0.19`, `m ≈ 0.06`,
- with `phi=0`: `w_bar ≈ 0.14`, `m ≈ 0`.

## Step 4: Run Case IV

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011Hedging.py
```

For the costly-margin line, use `w_- ≈ 0.07`, `w_+ ≈ 0.11`, `w_bar ≈ 0.14`, and `psi in [-5, 0]` as the first checks.

## Step 5: Run Case V

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011CreditLine.py
```

Use `w_bar ≈ 0.08`, `c+m ≈ 0.10`, and `p'(0)` near `1.01` when the credit line is active as the first checks.

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

## Related Pages

- [BCW2011 Case Study](./bcw2011-case-study.md)
- [BCW2011 Liquidation Walkthrough](./bcw2011-liquidation-walkthrough.md)
- [BCW2011 Refinancing Walkthrough](./bcw2011-refinancing-walkthrough.md)
- [BCW2011 Hedging Walkthrough](./bcw2011-hedging-walkthrough.md)
- [BCW2011 Credit Line Walkthrough](./bcw2011-credit-line-walkthrough.md)

Use the walkthroughs when you want the full bridge from paper equations to `Parameter` / `Boundary` / `PolicyDict` / `Policy` / `Model`.
