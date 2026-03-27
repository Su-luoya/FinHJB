# Output Contract

Every successful run of this skill should produce four deliverables.

## Deliverable 1: Structured Specification Summary

Organize the summary around the same stages used internally:

- environment readiness and smoke-test status
- research goal
- state variable and domain
- controls and admissible ranges
- value object
- HJB equation in implementation-ready form
- derivation status and any derivation steps that had to be confirmed before code generation
- boundary conditions and chosen workflow
- derivative-method choice and reason
- boundary-search method, target count, and brackets if relevant
- parameter list with baseline values
- explicit note when a parameter value had to be confirmed with the user before code generation
- explicit note when plotting requirements had to be confirmed with the user before code generation
- explicit note when the task required a split multi-file layout for sensitivity analysis plus plotting
- explicit assumptions or unresolved items

## Deliverable 2: Executable FinHJB Code

Match the code layout to the task shape.

### Baseline Solve Tasks

Use one runnable Python file containing:

- imports
- `Parameter`
- `Boundary`
- `PolicyDict`
- `Policy`
- `Model`
- a solver block

### Sensitivity-Analysis-Plus-Plotting Tasks

Use a split layout with at least:

- a solve/model file
- a data-save or data-export file
- a plotting file

### Code-Level Expectations

Regardless of layout:

- use descriptive control names
- add short comments for the key equation-to-code mappings
- state why `explicit_policy` or `implicit_policy` was chosen
- state why `solve`, `boundary_search`, `boundary_update`, or `sensitivity_analysis` was chosen
- state why the chosen derivative method fits the boundary behavior
- state why the chosen boundary-search method is the final method after testing, especially if it overrides the small-target default
- keep file responsibilities clear when the project is split for sensitivity analysis and plotting

## Deliverable 3: Executed Test-And-Repair Summary

Include:

- environment smoke test used for runnable delivery
- syntax and import checks that were run
- `Solver(...)` construction check
- baseline solve or boundary-search run that was executed
- artifact checks if the task asked for figures or summary files
- repairs applied before final delivery
- residual risks or untested branches that still remain

## Deliverable 4: Validation Checklist

Include:

- construction checks
- numerical checks
- boundary-condition checks
- policy-shape or sign checks
- model-specific economic sanity checks

## Suggested File Names

- `finhjb_<model-slug>.py`
- `finhjb_<model-slug>_spec.md`

When the deliverable is split:

- `solve_<model-slug>.py`
- `export_<model-slug>_data.py`
- `plot_<model-slug>.py`

## Final Answer Format

Use this order:

1. specification summary
2. code block or code layout summary
3. executed test-and-repair summary
4. validation checklist

If the model is unsupported, replace the code block with:

- why the model is unsupported
- the nearest implementable simplification
- the package capability that would need to be added
