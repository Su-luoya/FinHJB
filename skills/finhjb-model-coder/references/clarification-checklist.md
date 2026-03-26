# Clarification Checklist

Ask questions only when the answer will materially change the generated FinHJB implementation.

## Ask Before Coding

- What is the single continuous state variable and what interval should the grid cover?
- Which objects are controls, and are they chosen continuously inside the HJB?
- What are the exact left and right boundary conditions for the value function?
- Is any boundary endogenous and therefore solved with `boundary_search()` or `boundary_update()`?
- What is the control update rule: closed form, FOC residual, clipping rule, or regime-by-regime logic?
- Does the HJB contain a non-zero jump term that needs `Model.jump(...)`?
- Which parameters and calibration values should be hard-coded into the first executable version?
- What counts as a successful solve in economic or numerical terms?

## Ask When The Input Is A Paper Excerpt

- Confirm every equation that is only referenced by number rather than written out.
- Ask for pasted text when the excerpt omits the boundary conditions.
- Ask for pasted text when the FOC, Kuhn-Tucker condition, or regime split is only shown in an image.
- Ask the user whether they want the first runnable implementation to stay close to the paper notation or to adopt more descriptive variable names.

## Safe Defaults

If the model is otherwise fully specified, you may propose and label these defaults:

- `Config(derivative_method="central", pi_method="scan", pi_max_iter=50, pi_tol=1e-6)`
- `number=500` for a first-pass solve
- `policy_guess=True` when the user gives a meaningful initialization
- `LinearInitialValue` unless the boundary geometry clearly calls for `QuadraticInitialValue`

## Do Not Silently Assume

- a second state variable can be collapsed into a parameter
- an endogenous boundary target is `d2v[-1] = 0` just because BCW uses it
- a multi-control problem can be reduced to one control without economic consequences
- an implicit FOC can be safely rewritten as an explicit update without algebra

## Question Style

- Ask only the blocking questions first.
- Prefer short, concrete questions tied to code consequences.
- If you can recommend a default, state it explicitly so the user can confirm or override it.
