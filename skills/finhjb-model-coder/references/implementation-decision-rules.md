# Implementation Decision Rules

Read this file after the math is mappable and before writing the final implementation.

Your decision after reading: derivative scheme, boundary-search backend, template, and project layout.

## Derivative Scheme

- Use `central` when diffusion stays materially positive at both edges.
- Use `forward` when the left edge is effectively degenerate.
- Use `backward` when the right edge is effectively degenerate.
- If both edges are degenerate, or the excerpt is too incomplete to tell, ask a blocking question.

Always record:

- selected `derivative_method`
- why it matches the boundary behavior
- whether it is paper-grounded or a fallback assumption

## Boundary Search Method

- If `boundary_search()` has one or two targets and credible brackets, start with `bisection`.
- If it has three or more targets, start with `hybr` or another supported multidimensional backend.
- If the smaller-target default fails the executed test loop, explicitly promote the final method and say why.

Always record:

- `boundary_target_count`
- selected `boundary_search_method`
- brackets when `bisection` is used
- why the final method differs from the target-count default, if it does

## Template Choice

- `single-control-fixed-boundary.py`
  One control and fixed or directly computable boundaries.
- `single-control-boundary-search.py`
  One control and residual-based endogenous boundary search.
- `multi-control-boundary-update.py`
  Multiple controls and an outer solve-update loop.
- `multi-control-boundary-search.py`
  Multiple controls and residual-based endogenous boundaries.
- `parameter-search-task.py`
  Use around the solve-layer template when rescue mode is active.

Prefer the simplest template that matches the economics.

## Project Layout

- Compact baseline solve: one runnable Python file is enough.
- Sensitivity analysis plus saved outputs or figures: split into solve, export, and plot files.
- Rescue mode: keep the generic search runner separate from the task adapter/config layer.

## Post-Generation Repair Rule

Decision lock is not final until the code runs.

- If derivative choice creates boundary artifacts, revisit it.
- If boundary-search choice misses the intended benchmark badly, revise method or brackets and rerun.
- If template choice made the output unreadable, simplify the layout without changing the solve logic.
