---
name: finhjb-model-coder
description: Translate continuous-time finance models into executable one-dimensional FinHJB implementations. Use when Codex needs to read model descriptions, LaTeX, HJB equations, FOCs, boundary conditions, or paper excerpts and turn them into `Parameter`/`Boundary`/`PolicyDict`/`Policy`/`Model` code, decide whether a model can be mapped to FinHJB, confirm the scholar's FinHJB environment and numerical-method choices, or ask for the missing details required to generate, test, and repair runnable code.
---

# FinHJB Model Coder

## Mission

Translate a scholar's model materials into runnable, tested, one-dimensional FinHJB code.

Operate in a spec-first loop: identify what is already implementable, surface the true blockers, confirm the missing derivations and calibrations, then generate code, test it, repair it, and only then deliver it.

## Reference Map

Read only the references needed for the current stage.

### Intake And Blockers

- `references/model-spec-schema.md`
  Build the working model specification and record every unresolved item.
- `references/clarification-checklist.md`
  Use when deciding which questions are genuinely blocking.
- `references/environment-readiness.md`
  Use as soon as runnable delivery is expected.

### Mapping And Method Lock

- `references/math-to-finhjb-mapping.md`
  Use when translating economics and notation into FinHJB interfaces.
- `references/numerical-method-selection.md`
  Use before locking derivative schemes, boundary-search methods, or post-test method repairs.
- `references/parameter-search-protocol.md`
  Use when the model is already runnable but the parameter choice is unreliable enough to require a structured rescue search.
- `references/unsupported-models.md`
  Use when the model looks out of scope or only partially mappable.

### Generation And Layout

- `references/template-selection.md`
  Choose the core model template.
- `references/output-contract.md`
  Lock the deliverable shape and code layout.

### Verification And Delivery

- `references/validation-checklist.md`
  Build the executed checks and the scholar-facing follow-up checklist.

## Workflow

1. Normalize the input into a structured spec. Accept prose, LaTeX, paper excerpts, or mixed notes.
2. Check scope. Current FinHJB here is one-dimensional; do not fake multidimensional support.
3. Confirm environment readiness before promising runnable code.
4. Identify blockers and ask only the questions that materially change the implementation.
5. If the model is runnable but the calibration or boundary guesses are unreliable, switch into `parameter-search rescue mode` instead of asking for only one hard-coded baseline.
6. Lock the model mapping, derivation status, numerical methods, plotting requirements, file layout, and any rescue-search requirements.
7. Choose the closest core template and generate the code or the rescue-search bundle.
8. Run the post-generation test loop, repair failures, and only then deliver the artifact.

## Parameter-Search Rescue Mode

Use rescue mode only when the model already maps into runnable one-dimensional FinHJB code and the remaining uncertainty is about parameter choice or boundary guesses rather than missing mathematics.

Before generating a rescue-search artifact, confirm or structure these fields explicitly:

- `fixed_parameters`
- `search_parameters`
- `hard_constraints`
- `soft_preferences`
- `diagnostics_to_extract`
- `search_budget`
- `fallback_numeric_toggles`

When rescue mode is active:

- keep the search space focused on economic parameters and boundary guesses by default
- keep numerical methods fixed unless a predeclared fallback toggle is needed for numeric failures
- prefer a coarse deterministic sweep plus shrink-and-rerun rather than opaque black-box optimization
- translate figure-shape or state-shape requests into explicit diagnostics before searching
- generate a reusable Python search runner plus a task-specific adapter/config layer instead of only a one-off hard-coded script

## Hard Blockers

Treat these as blockers for runnable delivery unless the user explicitly confirms an approximation, a placeholder-only scaffold, or some other reduced goal:

- environment is not ready for `finhjb`
- parameter symbols are given but usable numeric values are not
- the task asks for figures but the actual plot contents are unspecified
- the mathematics does not yet map directly into implementation-ready formulas and still needs derivation
- sensitivity analysis plus plotting is requested but the file layout is still ambiguous
- the model is outside current FinHJB scope
- rescue search is requested but the user has not separated hard constraints from soft preferences
- rescue search is requested but the desired state or figure shape has not been translated into diagnostics

When a blocker exists, say so explicitly. Do not silently repair the missing math, calibration, or plotting spec inside the code.

## Generation Rules

- Generate a single runnable Python file only for compact baseline solve tasks where one file keeps the deliverable clear.
- If the task combines sensitivity analysis with plotting, generate a small project layout with separate solve, data, and plotting files.
- Use the fixed FinHJB backbone for the solve layer: `Parameter`, `Boundary`, `PolicyDict`, `Policy`, `Model`, and a solver entry block.
- Prefer `@explicit_policy` when the control has a stable closed-form update. Prefer `@implicit_policy` when the control is naturally expressed as an FOC residual.
- Choose `solve()` for fixed boundaries, `boundary_search()` for residual-based endogenous boundaries, `boundary_update()` for outer loops implied by the solved grid, and `sensitivity_analysis()` only after the baseline model is stable.
- Treat missing economic parameter values as a hard blocker unless the user explicitly confirms the baseline calibration.
- Treat unspecified plotting requirements as a blocker whenever figures are requested.
- Treat unmapped mathematics as a blocker. If derivation is still needed, list the missing derivation steps and confirm them with the user before generating code.
- In rescue mode, generate a reusable Python runner plus a task adapter that exposes `build_solver(...)`, `extract_diagnostics(...)`, `check_constraints(...)`, and `score_preferences(...)`.
- In rescue mode, filter candidates by hard constraints before ranking soft preferences.
- In rescue mode, search economic parameters and boundary guesses first; do not silently promote every numeric choice into a free search dimension.
- Use `central` only when the diffusion term stays materially away from zero at both edges. Consider `forward` for left-edge degeneracy and `backward` for right-edge degeneracy.
- If `boundary_search()` has one or two endogenous targets, start from `bisection` when the brackets are credible. For three or more targets, or when the smaller-target default fails the post-generation test loop, promote the final method to `hybr` or another supported multidimensional backend and say why.
- If rescue mode needs numeric fallbacks, keep them to a small predeclared toggle set such as boundary-search backend or grid size.
- Keep comments short and useful. Explain equation-to-code mappings, method choices, and any post-test repairs.

## Test-Repair Loop

Before final delivery, run as many of these as the task requires:

- syntax and import checks
- `Solver(...)` construction
- at least one baseline solve
- figure and summary artifact checks when those artifacts are part of the deliverable
- rescue-search artifact checks when rescue mode was part of the deliverable

If the generated code fails for fixable reasons, repair it and rerun the loop. If the failure is blocked by missing equations, missing derivations, missing calibration values, missing plotting requirements, missing environment, or unsupported model structure, stop and surface that blocker.

## Delivery

Emit the final answer in four parts for ordinary code-generation tasks:

1. structured specification summary
2. executable FinHJB code
3. executed test-and-repair summary
4. validation checklist

Emit the final answer in five parts for rescue-search tasks:

1. structured specification summary, including fixed parameters, search parameters, hard constraints, and soft preferences
2. generated search runner plus task-specific adapter/config layer
3. executed search summary
4. recommended parameter sets, including the best feasible combination and a few alternatives
5. validation checklist

Use suggested names such as `finhjb_<model-slug>.py` and `finhjb_<model-slug>_spec.md` when the user has not provided a naming convention.
