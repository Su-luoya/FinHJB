# Getting Started

## 1. Install

```bash
uv sync
```

## 2. Define Four Core Components

1. `AbstractParameter`: immutable model parameters.
2. `AbstractBoundary`: state/value boundaries.
3. `AbstractPolicy`: policy initialization and update logic.
4. `AbstractModel`: HJB residual and optional boundary helpers.

## 3. Build Solver

```python
solver = fjb.Solver(
    boundary=boundary,
    model=model,
    policy_guess=True,
    number=500,  # must be >= 4
    config=fjb.Config(pi_method="scan", derivative_method="central"),
)
```

## 4. Solve

```python
state, history = solver.solve()
```

`state.df` provides tabular values (`s`, `v`, `dv`, `d2v`, policies).

## 5. Save and Reload

```python
state.grid.save("solution_grid")
loaded_grid = fjb.load_grid("solution_grid")
```

Quick chooser for the three `load` functions:

- `fjb.load_grid(path)`: load one `Grid` (paired with `state.grid.save(path)`)
- `fjb.load_grids(path)`: load a `Grids` collection (paired with `result.grids.save(path)`)
- `fjb.load_sensitivity_result(path)`: load full continuation output (paired with `result.save(path)`)

For full examples, see “Loading Functions In Detail” in [API Reference](./api-reference.md).

## 6. Next Step: Paper-Based Case Reproduction

If you want a full walkthrough from model setup to result interpretation, continue with:

- [BCW2011 Case Study](./bcw2011-case-study.md)
