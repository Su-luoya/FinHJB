# Output And Validation

Once the model is in scope and the environment is ready, `finhjb-model-coder` should return something you can inspect and run, not just code that looks plausible.

## Expected Delivery

The intended delivery is not “some code that looks plausible.”

The intended delivery is:

- a structured model summary
- executable FinHJB code or a rescue-search runner bundle
- an executed test or search summary
- a validation checklist for the first solve

## Interaction Flow

A healthy interaction usually looks like this:

1. You provide model materials.
2. The skill checks whether the model fits one-dimensional FinHJB.
3. The skill confirms environment readiness.
4. The skill asks only the blocking questions that change code generation.
5. The skill chooses derivative and boundary-search settings explicitly.
6. If calibration rescue is needed, the skill structures fixed parameters, search parameters, hard constraints, and soft preferences.
7. The skill generates code or a rescue-search bundle.
8. The skill runs a post-generation test loop or search loop.
9. The skill repairs fixable failures before delivery.

## Post-Generation Test Loop

Before delivery, the skill should run:

- a syntax and import check
- a `Solver(...)` construction check
- at least one baseline solve
- required figure or summary checks if the task asked for them

If these checks fail for fixable implementation reasons, the skill should repair the code and rerun the checks.

If rescue mode is active, the output bundle should also contain:

- a machine-readable search-history table
- the best-parameter configuration
- a concise summary of the shrink-and-rerun process
- optional scholar-facing diagnostics or plots for the best candidate

## File Layout Rules

Do not force every task into one script.

Recommended rule:

- compact baseline solve: one file is often enough
- sensitivity analysis plus saved outputs and figures: split into solve, data, and plotting files

That separation makes reruns, diagnostics, and figure changes much easier to manage.

## Common Reasons Delivery Should Stop

The skill should stop instead of pretending success when:

- the environment is still not ready for `finhjb`
- important equations or derivations are still missing
- calibration values are still unspecified
- plot requirements are still ambiguous
- the model is outside one-dimensional FinHJB scope

## Related Pages

- [Full consolidated skill page](./finhjb-model-coder.md)
- [Solver Guide](./solver-guide.md)
- [Troubleshooting](./troubleshooting.md)
