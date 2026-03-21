# API Reference

## Top-Level Exports (`finhjb`)

### Core

- `Config`
- `Solver`
- `Grid`
- `Grids`
- `ImmutableBoundary`

### Interfaces

- `AbstractBoundary`
- `BoundaryConditionTarget`
- `AbstractModel`
- `AbstractParameter`
- `AbstractPolicy`
- `AbstractPolicyDict`
- `AbstractValueGuess`

### Helpers

- `explicit_policy(order: int)`
- `implicit_policy(...)`
- `LinearInitialValue`
- `QuadraticInitialValue`

### Loading

- `load_grid(path)`
- `load_grids(path)`
- `load_sensitivity_result(path)`

## Loading Functions In Detail

The three `load_*` functions differ by what you want to restore: a single solved grid, a grid collection, or a full sensitivity result.

| Function | Restored type | Matching save call | Typical use |
|---|---|---|---|
| `load_grid(path)` | `Grid` | `state.grid.save(path)` | one solved run |
| `load_grids(path)` | `Grids` | `result.grids.save(path)` | many solved grids along parameter values |
| `load_sensitivity_result(path)` | `SensitivityResult` | `result.save(path)` | full continuation output (summary + grids) |

Behavior guaranteed by implementation:

- `.pkl` suffix is auto-added (`Path(path).with_suffix(".pkl")`).
- Type is validated; using the wrong loader raises `TypeError`.

### 1) `load_grid`: restore one `Grid`

```python
import finhjb as fjb

state, _ = solver.solve()
state.grid.save("outputs/baseline_grid")  # actual file: outputs/baseline_grid.pkl

grid = fjb.load_grid("outputs/baseline_grid")
print(type(grid).__name__)  # Grid
print(grid.df.head())
```

### 2) `load_grids`: restore `Grids` (a parameter-path grid set)

```python
import finhjb as fjb
import jax.numpy as jnp

result = solver.sensitivity_analysis(
    method="hybr",
    param_name="sigma",
    param_values=jnp.array([0.09, 0.10, 0.11]),
)
result.grids.save("outputs/sigma_grids")

grids = fjb.load_grids("outputs/sigma_grids")
print(type(grids).__name__)  # Grids
print(list(grids.values))    # stored parameter values
g010 = grids.get(0.10)
print(g010.df.head())
```

### 3) `load_sensitivity_result`: restore full `SensitivityResult`

```python
import finhjb as fjb

result.save("outputs/sigma_result")
loaded = fjb.load_sensitivity_result("outputs/sigma_result")

print(type(loaded).__name__)  # SensitivityResult
print(loaded.df.head())       # continuation summary table
print(loaded.grids.get(0.10).df.head())  # full grid at one parameter value
```

### Common Mistakes

1. Reading `result.save(...)` output with `load_grid`: type mismatch (`Grid` expected, `SensitivityResult` loaded).
2. Using inconsistent file naming: including `.pkl` is fine, but omitting it is cleaner since loaders auto-append.
3. Over-loading data: if you only need one run, prefer `load_grid`; if you only need continuation summary, use `load_sensitivity_result(...).df`.

## Solver Methods

- `Solver.solve() -> (PolicyIterationState | EvaluationState, history)`
- `Solver.boundary_update() -> (BoundaryUpdateState, history)`
- `Solver.boundary_search(method, verbose=False) -> BoundarySearchState`
- `Solver.sensitivity_analysis(method, param_name, param_values) -> SensitivityResult`

## Grid Convenience

`Grid` properties:

- `s`, `v`, `dv`, `d2v`
- `s_inter`, `policy_inter`, `number_inter`, `jump_inter`
- `df`, `aux`

`Grid` methods:

- `reset()`
- `update_grid(boundary)`
- `update_with_v_inter(v_inter)`
- `save(path)`

`Grids` methods:

- `get`, `select_grids`, `add`, `merge`, `save`
