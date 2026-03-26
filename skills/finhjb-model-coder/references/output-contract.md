# Output Contract

Every successful run of this skill should produce three deliverables.

## Deliverable 1: Structured Specification Summary

Include:

- research goal
- state variable and domain
- controls and admissible ranges
- value object
- HJB equation in implementation-ready form
- boundary conditions and chosen workflow
- parameter list with baseline values
- explicit assumptions or unresolved items

## Deliverable 2: Executable FinHJB Code

The code must contain:

- imports
- `Parameter`
- `Boundary`
- `PolicyDict`
- `Policy`
- `Model`
- a runnable solver block

The code should also:

- use descriptive control names
- add short comments for the key equation-to-code mappings
- state why `explicit_policy` or `implicit_policy` was chosen
- state why `solve`, `boundary_search`, or `boundary_update` was chosen

## Deliverable 3: Validation Checklist

Include:

- construction checks
- numerical checks
- boundary-condition checks
- policy-shape or sign checks
- model-specific economic sanity checks

## Suggested File Names

- `finhjb_<model-slug>.py`
- `finhjb_<model-slug>_spec.md`

## Final Answer Format

Use this order:

1. specification summary
2. code block
3. validation checklist

If the model is unsupported, replace the code block with:

- why the model is unsupported
- the nearest implementable simplification
- the package capability that would need to be added
