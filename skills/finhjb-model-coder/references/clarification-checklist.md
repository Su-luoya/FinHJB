# Clarification Checklist

Ask questions only when the answer will materially change the generated FinHJB implementation.

## Ask Before Coding

- Which Python environment should be treated as the execution target, and can it already import `finhjb`?
- What is the single continuous state variable and what interval should the grid cover?
- Which objects are controls, and are they chosen continuously inside the HJB?
- What are the exact left and right boundary conditions for the value function?
- Is any boundary endogenous and therefore solved with `boundary_search()` or `boundary_update()`?
- Does the diffusion term stay away from zero at both edges, or does one boundary require `forward` or `backward` differences?
- If `boundary_search()` is needed, how many boundary targets are being solved for, and do we have credible brackets for `bisection`?
- What is the control update rule: closed form, FOC residual, clipping rule, or regime-by-regime logic?
- Does the HJB contain a non-zero jump term that needs `Model.jump(...)`?
- Which parameters and calibration values should be hard-coded into the first executable version?
- If the document names parameters but does not give usable numeric values, which baseline calibration should the runnable version use?
- What counts as a successful solve in economic or numerical terms?

## Ask When The Input Is A Paper Excerpt

- Confirm every equation that is only referenced by number rather than written out.
- Ask for pasted text when the excerpt omits the boundary conditions.
- Ask for the calibration table or pasted parameter values when the excerpt defines symbols but omits their numeric values.
- Ask for pasted text when the FOC, Kuhn-Tucker condition, or regime split is only shown in an image.
- Ask the user whether they want the first runnable implementation to stay close to the paper notation or to adopt more descriptive variable names.

## Safe Defaults

If the model is otherwise fully specified, you may propose and label these defaults:

- `Config(derivative_method="central", pi_method="scan", pi_max_iter=50, pi_tol=1e-6)` only when the diffusion term is not edge-degenerate
- `number=500` for a first-pass solve
- `policy_guess=True` when the user gives a meaningful initialization
- `LinearInitialValue` unless the boundary geometry clearly calls for `QuadraticInitialValue`
- `boundary_search(method="bisection")` for one or two targets with credible brackets
- `boundary_search(method="hybr")` for three or more targets, or when the smaller-target default fails the post-generation test loop

## Do Not Silently Assume

- a second state variable can be collapsed into a parameter
- an economic parameter can be assigned a paper-like number just because a nearby example used it
- an endogenous boundary target is `d2v[-1] = 0` just because BCW uses it
- a multi-control problem can be reduced to one control without economic consequences
- an implicit FOC can be safely rewritten as an explicit update without algebra
- the user's environment is ready just because the repository contains FinHJB source code
- `central` is always acceptable near a degenerate diffusion boundary
- `bisection` should remain the final method after testing if the generated solve clearly fails under it

## Question Style

- Ask only the blocking questions first.
- Prefer short, concrete questions tied to code consequences.
- If you can recommend a default, state it explicitly so the user can confirm or override it.
- If parameter names are present but the numeric calibration is missing, ask before code generation instead of inventing a baseline.
- After code generation, do not stop at "here is the code." Run the test loop, and only ask follow-up questions if the failure is caused by missing model information rather than a fixable implementation issue.
