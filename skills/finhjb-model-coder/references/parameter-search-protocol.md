# Parameter Search Protocol

Use this guide when the model is already runnable but the current parameter choice is too unreliable for a single hard-coded solve.

This is a rescue workflow, not a replacement for model clarification. If the environment, derivations, boundary conditions, plotting target, or model scope are still unresolved, stop and fix those first.

## Activation Rule

Activate `parameter-search rescue mode` only when all of these are true:

- the target environment can run `finhjb`
- the model already maps into one-dimensional FinHJB code
- the remaining uncertainty is about economic parameters or boundary guesses
- the user can separate hard constraints from soft preferences

## Required Search Specification

Before writing the runner, structure these fields explicitly:

- `fixed_parameters`
  Parameters that the user requires the search to hold fixed.
- `search_parameters`
  Searchable parameters with `name`, `low`, `high`, `scale`, `fixed`, and `initial_center`.
- `hard_constraints`
  Must-pass checks such as convergence, boundary conditions, monotonicity, threshold ranges, or sign restrictions.
- `soft_preferences`
  Weighted ranking rules such as “closer to a target payout boundary” or “closer to the desired slope.”
- `diagnostics_to_extract`
  Metrics computed from each solved candidate before feasibility filtering and ranking.
- `search_budget`
  Coarse sample count, keep ratio, shrink rounds, max candidates, and optional early stop.
- `fallback_numeric_toggles`
  A small allowed set of solver fallbacks, for example `boundary_search_method` or grid size.

## Translating Vague Preferences Into Diagnostics

Do not search directly on vague language such as:

- “make the plot smoother”
- “make it look more like the paper”
- “I want the result to have the right shape”

Translate those statements into diagnostics first, such as:

- payout boundary in a target interval
- value function monotone increasing
- marginal value monotone decreasing
- control profile close to a target boundary value
- comparative statics moving in the expected direction
- crossing point or threshold close to a benchmark

If the user cannot yet say what metric should stand in for the desired shape, stop and ask before searching.

## Search Strategy

The default rescue strategy is:

1. Run a coarse deterministic sweep over the allowed ranges.
2. Filter candidates by hard constraints.
3. Rank feasible candidates using the weighted soft-preference score.
4. Shrink the search box around the top feasible region.
5. Rerun the coarse sweep on the smaller box.

Default guidance:

- prefer one-dimensional or low-dimensional searches
- keep the search focused on economic parameters and boundary guesses
- do not promote every numeric setting into the search space
- use numeric fallbacks only when the solve fails for numeric reasons

## Output Requirements

The rescue bundle should save:

- a machine-readable search history table
- a best-parameter configuration file
- a search summary with shrink history and fallback usage
- optional plots or diagnostics for the best feasible candidate

The final answer should report:

- what was fixed
- what was searched
- what counted as feasible
- what was only preferred
- which parameter combinations were recommended
