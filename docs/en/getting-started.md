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
