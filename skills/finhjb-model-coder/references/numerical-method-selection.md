# Numerical Method Selection

Use this guide before locking `Config(derivative_method=...)` or `Solver.boundary_search(method=...)`.

## Derivative Scheme

Choose the finite-difference scheme from the diffusion behavior near the state boundaries.

- Use `central` when the diffusion term stays materially positive at both edges of the state grid.
- Use `forward` when the diffusion term becomes very small near the left boundary, so the left edge should avoid leaning on symmetric differences.
- Use `backward` when the diffusion term becomes very small near the right boundary.
- If both edges are degenerate, or the paper excerpt is too incomplete to tell, ask a blocking question instead of silently defaulting.

Always record:

- the selected `derivative_method`
- why that method matches the boundary behavior
- whether the choice is a paper-grounded conclusion or a fallback assumption

## Boundary Search Method

Choose the default search method from the number of endogenous boundary targets and the quality of the available brackets.

- If `boundary_search()` has one or two targets and you have credible `low` and `high` brackets, start with `bisection`.
- If `boundary_search()` has three or more targets, default to `hybr` or another supported multidimensional root solver.
- If the one- or two-target default fails the post-generation test loop, or if the bracket is not credible, explicitly upgrade the final implementation to `hybr` or another supported fallback and say why.

Always record:

- `boundary_target_count`
- the selected `boundary_search_method`
- bracket values when `bisection` is used
- why the final method differs from the target-count default, if it does

## Post-Generation Repair Rule

Method choice is not finished when the code block is written.

- Run the generated code.
- If the chosen derivative scheme creates boundary artifacts, revisit the scheme.
- If the chosen boundary search method fails to solve or misses the expected benchmark badly, revise the method or brackets and rerun.
- Report the final method and any repair made during testing.
