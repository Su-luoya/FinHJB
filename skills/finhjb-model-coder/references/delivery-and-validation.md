# Delivery And Validation

Read this file after code or rescue artifacts exist and before the final answer.

Your decision after reading: what must be delivered, what must be reported as already executed, and what the scholar should still validate.

## Ordinary Delivery Contract

Return four parts:

1. structured specification summary
2. executable FinHJB code or code-layout summary
3. executed test-and-repair summary
4. validation checklist

## Rescue-Search Delivery Contract

Return five parts:

1. structured specification summary
2. search runner plus task-adapter layout summary
3. executed search summary
4. recommended parameter sets
5. validation checklist

## Executed Checks

Run and report as many as the task requires:

- environment smoke test
- syntax and import checks
- `Solver(...)` construction
- at least one baseline solve or boundary-search run
- artifact checks for requested figures or summary files
- rescue-search artifact checks when rescue mode is active

If a failure is implementation-fixable, repair and rerun. If it is blocked by missing equations, missing derivation, missing calibration, missing plotting requirements, unsupported scope, or missing environment, stop and surface that blocker.

## Validation Checklist

Include only the checks that matter for the model at hand:

- workflow matches the boundary logic
- controls are initialized and economically interpretable
- value function and derivatives look numerically sane
- boundary-search residuals or boundary-update errors behave credibly
- comparative statics are directionally sensible when sensitivity analysis is used
- rescue-search results respect fixed/search split, hard constraints, soft-preference ranking, and declared numeric fallbacks

Always separate:

- what the skill already executed and repaired
- what the scholar should still validate after delivery
