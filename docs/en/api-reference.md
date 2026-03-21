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
