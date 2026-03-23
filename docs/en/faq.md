# FAQ

This page collects short answers to questions that come up repeatedly when people first use FinHJB through the BCW examples.

## Should I start from the API reference?

Usually no.

If you are new to the project, start with:

1. [Installation and Environment](./installation-and-environment.md)
2. [Getting Started](./getting-started.md)
3. [BCW2011 Case Study](./bcw2011-case-study.md)

Then return to [API Reference](./api-reference.md) when you need exact names or method signatures.

## Why does the documentation focus so much on BCW?

Because BCW gives you:

- a fully worked one-dimensional HJB example,
- endogenous boundary search,
- interpretable policies,
- a natural extension from one control to multiple controls.

It is a better teaching path than starting from abstract interfaces alone.

## Why must I implement `initialize(grid, p)` in the policy class?

Because the solver needs a complete policy container before iteration can begin.

Even if you later choose `policy_guess=False`, the solver still needs to know:

- which policy keys exist,
- what shapes those arrays should have.

## When should I use `@explicit_policy`?

Use it when the policy update can be written directly and stably in code.

Typical case:

- you have a closed-form update formula.

## When should I use `@implicit_policy`?

Use it when the natural mathematical object is a residual or root problem.

Typical case:

- the policy is defined by a first-order condition that is easier to state as `FOC(...) = 0`.

## Why does `policy_guess` matter so much?

Because it changes the starting point of the iteration.

- good initial guesses can speed convergence,
- poor initial guesses can slow or distort it.

This is why the BCW examples spend effort constructing reasonable initial policies.

## When should I call `solve()`?

Call `solve()` when the boundaries are already fixed and you want the cleanest possible base solve.

This should usually be your first workflow when adapting a new model.

## When should I call `boundary_update()`?

Call it only when your model implements `update_boundary(grid)` and the solved grid directly implies a boundary revision.

If your model does not implement that method, `boundary_update()` correctly raises `NotImplementedError`.

## When should I call `boundary_search()`?

Call it when one or more boundaries must be chosen so that a numerical condition holds.

BCW liquidation is the canonical example:

- search over `s_max`,
- evaluate `d2v[-1]`,
- stop when the right-boundary contact condition is satisfied.

## Why is `d2v[-1]` so important in the BCW examples?

Because the payout-side super-contact condition is encoded numerically through the right-tail curvature.

In the BCW scripts, a near-zero `d2v[-1]` is one of the strongest success signals.

## Why can investment be negative at low cash?

Because financing frictions are severe in distressed states. In the BCW setup, negative low-cash investment is economically meaningful, not automatically a coding bug.

## Why is `psi` between `-5` and `0` in the hedging example?

Because `pi = 5` in the benchmark calibration and the code clips the hedge policy to the interval implied by the BCW hedging constraints.

Interpretation:

- `-5` means maximum hedge demand,
- `0` means no hedge.

## How many grid points should I use?

Start with something moderate and stable, then increase only after the model is behaving sensibly.

The BCW example scripts use `number=1000` for high-resolution runs, but the right choice for your workflow depends on:

- curvature,
- stiffness,
- runtime budget,
- how sharp your policy regions are.

## Why not start with sensitivity analysis?

Because continuation is built on repeated solves. If the base solve is wrong, sensitivity analysis just produces many wrong solves.

## Why does `grid.aux` sometimes fail?

Because `auxiliary(grid)` is optional. If your model does not implement it, `grid.aux` raises `NotImplementedError`.

## What is the safest first custom project?

Fork the liquidation example and change only:

1. parameter names and values,
2. the policy formula,
3. the HJB residual,

while keeping the class structure and diagnostic workflow intact.

## How do I know whether my result is "close enough"?

Use ranges and qualitative shapes, not exact single numbers.

For BCW, good questions are:

- is `v` increasing in `s`?
- is `dv[-1]` near the expected right-boundary slope?
- is `d2v[-1]` near zero?
- do the policies have the expected left-tail and right-tail behavior?

## Where should I go after the FAQ?

- [Results and Diagnostics](./results-and-diagnostics.md) for interpretation
- [Modeling Guide](./modeling-guide.md) for interfaces
- [Solver Guide](./solver-guide.md) for workflow choice
- [Adapting BCW to Your Model](./adapting-bcw-to-your-model.md) for migration steps

