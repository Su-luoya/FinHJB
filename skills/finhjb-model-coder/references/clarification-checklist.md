# Clarification Checklist

Read this file only after the spec exists and before code or search generation.

Your decision after reading: which missing facts materially change implementation, and which defaults are safe to state explicitly.

## Ask Only When The Answer Changes The Build

- Which Python environment is the execution target, and can it already import `finhjb`?
- What is the single continuous state variable and its interval?
- Which objects are controls, and how are they updated: closed form, FOC residual, clipping, or regime logic?
- Does the current material already map directly into code, or are derivations still missing?
- What are the exact left and right boundary conditions?
- Is any boundary endogenous and solved by `boundary_search()` or `boundary_update()`?
- Does diffusion degenerate near either edge strongly enough to change the derivative scheme?
- If `boundary_search()` is needed, how many targets exist, and are credible brackets available?
- Which numeric parameter values belong in the first runnable version?
- If figures are requested, what exactly should be plotted?
- If the task mixes sensitivity analysis with plotting, should the deliverable be split into solve, export, and plot files?
- If rescue mode is needed, which parameters are fixed, which may move, and what counts as a successful result?

## Rescue-Mode Questions

Ask these only when the model is already runnable and calibration is the only blocker:

- Confirm the fixed/search parameter split explicitly.
- Which parameters must stay fixed?
- For each searchable parameter, what are `low`, `high`, `scale`, and `initial_center`?
- Which conditions are hard constraints?
- Which outcomes are soft preferences with weights or target closeness?
- Which diagnostics should stand in for statements like “smooth,” “paper-like,” or “right shape”? If the user gives natural-language preferences, translate them into metrics before searching.
- What search budget is acceptable for the first pass?
- Which numeric fallbacks are allowed if the solve fails for numeric reasons?

## Safe Defaults

State these as defaults, not facts, when the user does not care:

- `Config(derivative_method="central", pi_method="scan", pi_max_iter=50, pi_tol=1e-6)` only when diffusion is not edge-degenerate
- `number=500` for a first solve
- `policy_guess=True` when a meaningful initialization exists
- `boundary_search(method="bisection")` for one or two targets with credible brackets
- `boundary_search(method="hybr")` for three or more targets, or when the smaller-target default fails after testing
- `search_budget = {coarse_samples: 5, shrink_rounds: 1, keep_ratio: 0.4}` for a first rescue-search pass

## Do Not Silently Assume

- missing calibration values
- missing figure definitions
- missing derivation steps
- unsupported extra state variables
- vague shape preferences without diagnostics
- every numeric setting should become part of the search space
- a boundary-search default should remain final if executed tests say otherwise
