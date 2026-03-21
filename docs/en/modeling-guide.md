# Modeling Guide

## Parameter (`AbstractParameter`)

Declare immutable model parameters as class attributes.

```python
class Parameter(fjb.AbstractParameter):
    r: float = 0.03
    sigma: float = 0.15
```

Override `update(boundary)` if you need to refresh derived values from boundary updates.

## Boundary (`AbstractBoundary`)

You can mix:

- directly provided values (`s_min=...`, `s_max=...`),
- computed values via `compute_<boundary_name>` methods.

Dependencies are inferred from method signatures.

Rules:

- do not provide both explicit value and compute method for the same boundary,
- circular dependencies raise an error,
- `s_min < s_max` is validated.

## Policy (`AbstractPolicy`)

1. Implement `initialize(grid, p)` to return all policy keys.
2. Use `@explicit_policy(order=...)` for closed-form updates.
3. Use `@implicit_policy(...)` for root-finding updates.

Supported implicit solvers:

- `gauss_newton`
- `broyden`
- `lm`
- `newton_raphson`

## Model (`AbstractModel`)

Required:

- `hjb_residual(v, dv, d2v, s, policy, jump, boundary, p)`

Optional:

- `jump(...)`
- `boundary_condition()`
- `update_boundary(grid)`
- `auxiliary(grid)`

If you plan to call `solver.boundary_update()`, `update_boundary(grid)` must be implemented.
