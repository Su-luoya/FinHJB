# Template Selection

Choose the template that is closest to the model you are implementing, then adapt it instead of writing from scratch.

## Primary Decision Tree

1. Count the number of control variables.
2. Decide whether the boundaries are fixed, found by residual search, or updated from the solved grid.
3. Choose the closest template in `assets/templates/`.

## Template Guide

### `single-control-fixed-boundary.py`

Use when:

- there is one control variable
- all boundaries are fixed or directly computable from parameters and already-known boundary values
- the first runnable version should focus on `solve()`

### `single-control-boundary-search.py`

Use when:

- there is one control variable
- at least one boundary must be found by `boundary_search()`
- the model has smooth-pasting, super-contact, or another residual-based boundary target

### `multi-control-boundary-update.py`

Use when:

- there are multiple controls
- the solved grid directly implies a new boundary via `update_boundary(grid)`
- the model needs an outer loop after the inner solve

Fallback use:

- if there are multiple controls but the boundaries are fixed, start here and remove the `update_boundary()` hook

### `multi-control-boundary-search.py`

Use when:

- there are multiple controls
- one or more boundaries must be chosen by residual search
- the model needs several `BoundaryConditionTarget` entries

## Selection Rules

- Prefer the simpler template when two are plausible.
- Use the closest economic structure, not the closest paper topic.
- Keep the first generated version small and runnable; add extra diagnostics only after the solve logic is coherent.
- Template selection does not decide the derivative scheme. Confirm the diffusion behavior separately.
- Template selection does not lock the boundary-search backend forever. For one or two targets, start from `bisection` when the bracket is credible, then promote to `hybr` or another supported method if the post-generation test loop says the default is not good enough.
