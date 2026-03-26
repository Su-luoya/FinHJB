# Math To FinHJB Mapping

Use this file to translate the scholar's notation into the FinHJB interfaces.

## Core Mapping

| Mathematical object | FinHJB location | Notes |
|---|---|---|
| model parameters | `Parameter` | Store calibrated constants and derived quantities here. |
| state domain | `Boundary` | `s_min` and `s_max` are the numerical domain endpoints. |
| value boundary values | `Boundary` | `v_left` and `v_right` come from fixed formulas or endogenous rules. |
| control set | `PolicyDict` and `Policy` | Put every control array in `PolicyDict`; update them in `Policy`. |
| HJB residual | `Model.hjb_residual(...)` | Return the interior-point residual driven to zero by the solver. |
| non-local jump term | `Model.jump(...)` | Override only when the model genuinely has a non-zero jump operator. |
| residual-based endogenous boundary | `Model.boundary_condition()` | Use `BoundaryConditionTarget` entries. |
| direct boundary update implied by the solved grid | `Model.update_boundary(grid)` | Use for outer loops of the form solve -> update boundary -> solve. |
| custom diagnostics | `Model.auxiliary(grid)` | Return a small dictionary of derived results. |

## Naming Rules

- Preserve the scholar's economic meaning even when renaming symbols.
- Map the paper's state variable into FinHJB's `s`.
- Map the paper's value function into `v`.
- Use descriptive control names in `PolicyDict` instead of generic names such as `control1`.

## Policy Update Choice

Use `@explicit_policy` when:

- the control has a stable closed-form expression
- clipping or region stitching can be written directly on arrays
- the code will be clearer as an explicit update

Use `@implicit_policy` when:

- the control is naturally written as an FOC residual
- a nonlinear root solver is required pointwise
- the residual form is cleaner than an algebraically manipulated explicit formula

## Solver Workflow Choice

- Use `solve()` when all boundaries are fixed or directly computable.
- Use `boundary_search()` when a solved grid must satisfy one or more residual conditions, such as smooth pasting or super-contact.
- Use `boundary_update()` when the solved grid directly implies revised boundary values.
- Use `sensitivity_analysis()` only after the baseline model solves cleanly.

## One-Dimensional Constraint

Current FinHJB is organized around a single state grid.

If the model has:

- two or more state variables
- path dependence that cannot be folded into one state
- regime switching that requires coupled value functions

then stop and consult `unsupported-models.md` before generating code.
