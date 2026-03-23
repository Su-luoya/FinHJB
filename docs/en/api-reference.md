# API Reference

This page is the reference companion to the tutorial pages.

Use the tutorials first if you are still learning the workflow:

| If you want to... | Read this first |
|---|---|
| install and run the first example | [Installation and Environment](./installation-and-environment.md) |
| reproduce the BCW baseline examples | [Getting Started](./getting-started.md) |
| understand returned objects and diagnostics | [Results and Diagnostics](./results-and-diagnostics.md) |
| adapt BCW to your own model | [Adapting BCW to Your Model](./adapting-bcw-to-your-model.md) |
| understand workflow choice | [Solver Guide](./solver-guide.md) |

Come back here when you want exact exported names, method members, and loader behavior.

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

## API By Task

| Task | Objects you will touch first |
|---|---|
| define a model | `AbstractParameter`, `AbstractBoundary`, `AbstractPolicy`, `AbstractModel` |
| run one fixed-boundary solve | `Solver`, `Config` |
| search for an endogenous boundary | `BoundaryConditionTarget`, `Solver.boundary_search()` |
| inspect a solved object | `Grid`, `Grid.df`, `Grid.aux` |
| store and reload results | `Grid.save`, `load_grid`, `Grids.save`, `load_grids`, `load_sensitivity_result` |

## Loading Functions In Detail

The three `load_*` functions differ by what you want to restore: a single solved grid, a grid collection, or a full sensitivity result.

| Function | Restored type | Matching save call | Typical use |
|---|---|---|---|
| `load_grid(path)` | `Grid` | `state.grid.save(path)` | one solved run |
| `load_grids(path)` | `Grids` | `result.grids.save(path)` | many solved grids along parameter values |
| `load_sensitivity_result(path)` | `SensitivityResult` | `result.save(path)` | full continuation output (summary + grids) |

Guaranteed behavior:

- `.pkl` suffix is auto-added,
- type is validated after loading,
- using the wrong loader raises `TypeError`.

### Example: `load_grid`

```python
import finhjb as fjb

state, _ = solver.solve()
state.grid.save("outputs/baseline_grid")

grid = fjb.load_grid("outputs/baseline_grid")
print(type(grid).__name__)
print(grid.df.head())
```

### Example: `load_grids`

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
print(type(grids).__name__)
print(list(grids.values))
```

### Example: `load_sensitivity_result`

```python
import finhjb as fjb

result.save("outputs/sigma_result")
loaded = fjb.load_sensitivity_result("outputs/sigma_result")

print(type(loaded).__name__)
print(loaded.df.head())
```

### Common Loading Mistakes

1. Loading a continuation result with `load_grid`.
2. Forgetting that the loader auto-adds `.pkl`.
3. Loading the full continuation result when you only needed a single grid.

## Solver Methods

- `Solver.solve() -> (PolicyIterationState | EvaluationState, history)`
- `Solver.boundary_update() -> (BoundaryUpdateState, history)`
- `Solver.boundary_search(method, verbose=False) -> BoundarySearchState`
- `Solver.sensitivity_analysis(method, param_name, param_values) -> SensitivityResult`

See [Solver Guide](./solver-guide.md) for when to use each one.

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

For interpretation, go to [Results and Diagnostics](./results-and-diagnostics.md).

## API Details

### Config

```{eval-rst}
.. autoclass:: finhjb.Config
   :members:
   :no-index:
```

### Solver

```{eval-rst}
.. autoclass:: finhjb.Solver
   :members:
   :no-index:
```

### Structures

```{eval-rst}
.. autoclass:: finhjb.Grid
   :members:
   :no-index:

.. autoclass:: finhjb.Grids
   :members:
   :no-index:

.. autoclass:: finhjb.ImmutableBoundary
   :members:
   :no-index:
```

### Interfaces

```{eval-rst}
.. autoclass:: finhjb.AbstractBoundary
   :members:
   :no-index:

.. autoclass:: finhjb.BoundaryConditionTarget
   :members:
   :no-index:

.. autoclass:: finhjb.AbstractModel
   :members:
   :no-index:

.. autoclass:: finhjb.AbstractParameter
   :members:
   :no-index:

.. autoclass:: finhjb.AbstractPolicy
   :members:
   :no-index:

.. autoclass:: finhjb.AbstractPolicyDict
   :members:
   :no-index:

.. autoclass:: finhjb.AbstractValueGuess
   :members:
   :no-index:

.. autoclass:: finhjb.LinearInitialValue
   :members:
   :no-index:

.. autoclass:: finhjb.QuadraticInitialValue
   :members:
   :no-index:
```

### Helpers

```{eval-rst}
.. autofunction:: finhjb.explicit_policy
   :no-index:

.. autofunction:: finhjb.implicit_policy
   :no-index:
```

### Loading Functions

```{eval-rst}
.. autofunction:: finhjb.load_grid
   :no-index:

.. autofunction:: finhjb.load_grids
   :no-index:

.. autofunction:: finhjb.load_sensitivity_result
   :no-index:
```
