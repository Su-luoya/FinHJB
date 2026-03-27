# Math To FinHJB Mapping

Use this file to translate the scholar's notation into the FinHJB interfaces.

If the mathematics cannot yet be translated directly, stop and turn the remaining work into explicit derivation questions instead of silently doing the derivation in code.

## Core Mapping Table

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

## Derivation Gate

Do not move from math to code until each of these is either directly given or explicitly confirmed with the user:

- the state normalization used by the implementation
- the exact residual form of the HJB
- the control update formula or FOC residual written in implementation-ready form
- the mapping from paper boundary conditions into `Boundary` values or `BoundaryConditionTarget`s
- any derived quantities that must be computed before the solver can run

If one of these still requires derivation:

1. say that the current material does not yet map directly into code
2. list the missing derivation steps explicitly
3. ask the user to confirm those derivations or provide the missing intermediate formulas
4. only then generate code

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

## Stop Conditions

Current FinHJB is organized around a single state grid.

If the model has:

- two or more state variables
- path dependence that cannot be folded into one state
- regime switching that requires coupled value functions

then stop and consult `unsupported-models.md` before generating code.
