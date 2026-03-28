# Getting Started

This page now means repository quickstart for the BCW track.

Read this page if your question is: “I cloned the repository. How do I run the BCW examples and tell whether the outputs look healthy?”

If you want the package-only path, read [Library Quickstart](./quickstart-library.md) instead.

## Goal

By the end of this page, you should be able to:

- confirm the repository environment works
- run the BCW liquidation example
- run the BCW hedging example
- recognize the main numerical success patterns without reading every line of output

## Step 1: Prepare The Repository Environment

From the repository root:

```bash
uv sync
uv run python -c "import finhjb as fjb; print(fjb.__all__[:5])"
```

If you are on a headless machine, also use:

```bash
export MPLBACKEND=Agg
```

## Step 2: Run The BCW Liquidation Example

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011Liquidation.py
```

Healthy runs in this repository usually show:

- `v_left` around `0.9`
- solved `s_max` around `0.22`
- `dv[-1]` close to `1`
- `d2v[-1]` close to `0`
- investment strongly negative at low cash and positive near the right boundary

## Step 3: Run The BCW Hedging Example

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011Hedging.py
```

Healthy runs in this repository usually show:

- `v_left` above the pure liquidation value
- solved `s_max` around `0.14`
- `psi` staying in `[-5, 0]`
- `d2v[-1]` again close to `0`
- a three-region hedge pattern: binding, interior, then zero hedge

## Step 4: Read The Result Intentionally

After a run, check these first:

```python
print(final_state.grid.boundary)
print(final_state.grid.df.head())
print(final_state.grid.df.tail())
print(final_state.grid.d2v[-1])
```

For the BCW path, that is the shortest route from “it ran” to “I know what happened.”

## Where To Go Next

- [BCW2011 Case Study](./bcw2011-case-study.md) for the full learning map
- [BCW2011 Liquidation Walkthrough](./bcw2011-liquidation-walkthrough.md) for line-by-line interpretation
- [BCW2011 Hedging Walkthrough](./bcw2011-hedging-walkthrough.md) for the second control and refinancing logic
- [Adapting BCW To Your Model](./adapting-bcw-to-your-model.md) once the baseline is stable
