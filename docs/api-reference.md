# API Reference

This file summarizes the top-level `finhjb` API exported in `src/finhjb/__init__.py`.

## Core Objects

- `Config`
- `Solver`
- `Grid`
- `Grids`
- `ImmutableBoundary`

## Interfaces

- `AbstractBoundary`
- `BoundaryConditionTarget`
- `AbstractModel`
- `AbstractParameter`
- `AbstractPolicy`
- `AbstractPolicyDict`
- `AbstractValueGuess`

## Decorators

- `explicit_policy(order: int)`
- `implicit_policy(order: int, solver="gauss_newton", ...)`

`implicit_policy` supports solvers:

- `gauss_newton`
- `broyden`
- `lm`
- `newton_raphson`

## Initial Value Guess Implementations

- `LinearInitialValue`
- `QuadraticInitialValue`

## IO Utility

- `load(path)`

Loads one of:

- `Grid`
- `Grids`
- `SensitivityResult`

## Solver Methods

`Solver.solve()`:

- Returns `(PolicyIterationState | EvaluationState, history)`

`Solver.boundary_update()`:

- Returns `(BoundaryUpdateState, history)`

`Solver.boundary_search(method, verbose=False)`:

- Returns `BoundarySearchState`

`Solver.sensitivity_analysis(method, param_name, param_values)`:

- Returns `SensitivityResult`

## Grid Convenience Accessors

Important `Grid` properties:

- `s`, `v`, `dv`, `d2v`
- `s_inter`, `policy_inter`, `number_inter`
- `jump_inter`
- `df` (pandas DataFrame)
- `aux` (model-defined auxiliary output)

Important methods:

- `reset()`
- `update_grid(boundary)`
- `update_with_v_inter(v_inter)`
- `save(path)`

## Result Containers

`Grids`:

- mapping-like container `{parameter_value -> Grid}`
- methods: `get`, `select_grids`, `add`, `save`

`SensitivityResult`:

- fields: `result`, `grids`
- properties/methods: `df`, `save`, `load`
