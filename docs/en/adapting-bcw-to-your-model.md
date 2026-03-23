# Adapting BCW To Your Model

This page answers the practical question:

"I can reproduce BCW. How do I turn it into my own model without breaking everything at once?"

The guiding principle is simple:

- copy the BCW structure aggressively,
- change the economics gradually,
- re-validate after every small step.

## Read This After

- [Getting Started](./getting-started.md)
- [BCW2011 Liquidation Walkthrough](./bcw2011-liquidation-walkthrough.md)
- [BCW2011 Hedging Walkthrough](./bcw2011-hedging-walkthrough.md)
- [Modeling Guide](./modeling-guide.md)

## Choose The Right Starting Template

| Your model resembles... | Best starting file |
|---|---|
| one state variable, one control, endogenous right boundary | `src/example/BCW2011Liquidation.py` |
| one state variable, multiple controls, refinancing or boundary updates | `src/example/BCW2011Hedging.py` |

If you are unsure, start from liquidation. It is easier to debug one control than two.

## What You Can Usually Reuse Almost Verbatim

The following parts are often reusable with only renaming:

- the overall file structure,
- the `Parameter` / `Boundary` / `PolicyDict` / `Policy` / `Model` split,
- the `Solver(...)` construction pattern,
- the diagnostic code that prints `grid.boundary`, `grid.df.head()`, and `grid.df.tail()`,
- save/load patterns for solved outputs.

This is a feature, not a weakness. The whole point of learning BCW first is to inherit a clean one-dimensional HJB workflow.

## What You Must Re-Think Carefully

These are the parts you should not copy blindly:

- the economic parameter list,
- the HJB residual signs and drift terms,
- policy formulas and first-order conditions,
- boundary-value formulas,
- the boundary-search target,
- any refinancing or issuance logic,
- interpretation of policy columns.

If you copy these mechanically, the code may run while solving the wrong model.

## Recommended Migration Order

## Step 1: Duplicate A BCW Script

Create a new working file by copying the closest BCW example.

Do not start from a blank file unless you already know the package internals very well.

## Step 2: Rename The Economic Objects

Rename:

- `Parameter`
- `PolicyDict`
- `Boundary`
- `Policy`
- `Model`

Even if the code is still BCW under the hood, renaming early helps you keep the new model mentally separate.

## Step 3: Replace Parameters First

Edit only the `Parameter` class first.

Success condition:

- the file still imports,
- the solver still constructs,
- any derived parameter logic is clear and local.

Do not touch the residual yet.

## Step 4: Get A Fixed-Boundary Solve Working

Before boundary search, aim for:

```python
state, history = solver.solve()
```

Why this matters:

- it isolates HJB and policy logic from boundary-search logic,
- it tells you whether the base equations are coherent,
- it gives you a clean debugging surface.

First checks:

```python
print(type(state).__name__)
print(state.df.head())
print(state.df.tail())
```

## Step 5: Replace The Policy Logic

Implement your actual controls next.

Decision rule:

- use `@explicit_policy` if you have a direct update,
- use `@implicit_policy` if your control is naturally defined through a residual or FOC.

Validate after this step:

- every required policy key exists,
- each array matches the grid length,
- the resulting policy columns look economically interpretable.

## Step 6: Replace The HJB Residual

Only after the policy is coherent should you rewrite `Model.hjb_residual`.

Good practice:

- keep the residual algebra readable,
- assign intermediate terms meaningful names,
- compare each term against your theoretical equation.

Bad practice:

- writing the whole residual in one dense line and then trying to debug sign errors by inspection.

## Step 7: Re-Introduce Endogenous Boundaries

Once the fixed-boundary solve is stable, choose the right workflow:

- `boundary_search()` if a condition such as `d2v[-1] = 0` determines a boundary,
- `boundary_update()` if the solved grid implies a new boundary directly,
- both, if your model truly needs both stages.

Do not add this layer before the fixed-boundary baseline works.

## Step 8: Add Persistence And Diagnostics

After you trust the solve, add:

- `grid.save(...)`,
- `load_grid(...)`,
- continuation or sensitivity runs if needed,
- plots or custom auxiliary diagnostics.

This is the right time to make analysis convenient, because now you have something worth analyzing.

## A Good Validation Ladder

At each stage, ask only one question:

1. does the file import?
2. does `Solver(...)` construct?
3. does `solve()` return a sensible state?
4. do the value/policy curves have the right shape?
5. do boundary conditions hold?
6. only then: do comparative statics make sense?

That ordering prevents you from trying to interpret economics from a numerically broken object.

## What To Copy From BCW, Specifically

### Usually safe to copy

- the class layout,
- typed `PolicyDict` declarations,
- the pattern `Boundary(p=parameter, s_min=..., s_max=...)`,
- `Solver(..., number=..., config=...)`,
- result inspection snippets.

### Must be rewritten

- parameter values and meanings,
- boundary formulas,
- FOC logic,
- HJB drift/diffusion terms,
- boundary targets,
- economic interpretation text.

## Common Migration Mistakes

### Changing everything at once

If you simultaneously change:

- parameters,
- boundaries,
- controls,
- residual,
- search target,

then a failure gives you no clue where to look.

### Starting with sensitivity analysis

Continuation is valuable, but it is a multiplier on top of a base solve. If the base solve is wrong, sensitivity analysis only generates more wrong solves.

### Keeping BCW diagnostics but forgetting BCW assumptions changed

Example:

- `d2v[-1]` is central for BCW's payout-side condition,
- but your model might require a different right-boundary condition.

Reuse the diagnostic pattern, not the literal target without thought.

## A Suggested Work Sequence For Researchers

1. reproduce liquidation unchanged,
2. reproduce hedging unchanged if your model has multiple controls or refinancing,
3. fork the closer example,
4. change parameters and names,
5. get `solve()` stable,
6. add your actual boundary logic,
7. write down your own success checks,
8. only then begin comparative statics or paper tables.

## When To Move From Liquidation To Hedging As A Template

Move to the hedging template if your model needs any of the following:

- more than one control,
- an outer boundary-update rule,
- control-dependent state variance,
- financing or issuance conditions tied to an interior threshold.

If not, staying closer to liquidation keeps the code easier to reason about.

## Final Rule Of Thumb

The first successful custom model should be boring.

That means:

- one file,
- clear class boundaries,
- a stable fixed-boundary solve,
- obvious diagnostics,
- only one new economic idea at a time.

That "boring" path is the fastest way to get to a credible research workflow.

## Next Step

- Return to [Modeling Guide](./modeling-guide.md) for interface details.
- Return to [Solver Guide](./solver-guide.md) for workflow decisions.
- Use [Results and Diagnostics](./results-and-diagnostics.md) to create your own success checklist after each change.

