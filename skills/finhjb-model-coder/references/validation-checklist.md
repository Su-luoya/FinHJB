# Validation Checklist

Use this checklist to keep generated code numerically honest.

## Universal Checks

- the execution environment is identified and `finhjb` imports successfully
- the file imports without syntax errors
- `Solver(...)` constructs successfully
- every control declared in `PolicyDict` is initialized in `Policy.initialize`
- each control array matches the grid length
- the chosen workflow matches the boundary logic in the model
- the economic parameter values in the runnable script match the confirmed calibration
- the selected derivative scheme is consistent with the diffusion behavior near the boundaries

## Fixed-Boundary Checks

- `solve()` returns a state and history without crashing
- `state.df` contains sensible `v`, `dv`, `d2v`, and control columns
- the HJB residual is small enough for a first-pass solve
- the control profile is economically interpretable over the state grid

## Boundary-Search Checks

- the chosen search backend is justified by the number of targets and the bracket quality
- the chosen `BoundaryConditionTarget` is economically justified
- the bracket for `bisection` is credible if that method is used
- the post-solve boundary residual is close to zero
- `grid.boundary` differs meaningfully from the initial guess when it should
- if a one- or two-target default was promoted from `bisection` to `hybr`, the repair note explains why

## Boundary-Update Checks

- `update_boundary(grid)` returns both the proposed update and the update error
- the outer loop actually moves the targeted boundary values
- the update error declines or stabilizes in a credible way

## Sensitivity Checks

- run `sensitivity_analysis()` only after the baseline model is stable
- inspect `result.df` for convergence and boundary errors
- confirm the comparative statics have the expected economic direction

## Scholar-Facing Validation Notes

Always include at least one model-specific economic sanity check such as:

- expected sign of the control near the left boundary
- expected monotonicity of the value function
- expected limiting behavior near payout, liquidation, or issuance thresholds

If a quantity is especially important to the paper, call it out explicitly instead of giving only generic solver checks.

## Delivery Notes

Separate these two things in the final answer:

- what the skill already executed and repaired before delivery
- what the scholar should still validate after delivery
