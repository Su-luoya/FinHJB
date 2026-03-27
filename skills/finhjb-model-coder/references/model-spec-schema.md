# Model Spec Schema

Use this schema before writing any code.

The goal is to turn free-form mathematical input into a compact working specification that drives questions, method choices, layout decisions, and final code generation.

## Stage 1: Delivery Context

These fields decide whether runnable delivery is even possible yet.

- `environment`
  Whether the target Python environment is ready, how `finhjb` is provided, and what smoke test was used.
- `plot_requirements`
  Whether plots are requested, which quantities should be visualized, output file expectations, and any remaining figure questions that still require user confirmation.
- `project_layout`
  Whether the deliverable should stay single-file or be split into separate solve, data, and plotting files. Sensitivity-analysis-plus-plotting tasks should default to the split layout.

## Stage 2: Economic Model

These fields define what is being solved.

- `research_goal`
  What economic question the model answers and what object is being valued or optimized.
- `state_variable`
  The single continuous state variable, its symbol in the paper, its economic meaning, and its admissible interval.
- `controls`
  Every control variable, its symbol, interpretation, admissible range, and whether it is expected to be explicit or implicit.
- `value_object`
  The value function being solved for and any normalization used in the paper.
- `parameters`
  Parameter names, meanings, baseline calibrations, any missing numeric values that still require user confirmation, and any derived quantities.

## Stage 3: Math-To-Code Mapping

These fields define whether the mathematics is already implementation-ready.

- `hjb_equation`
  The exact HJB residual target, restated in solver-friendly notation.
- `derivation_requirements`
  Any mathematical steps that still need to be derived or confirmed before the model can be mapped into executable FinHJB code.
- `drift_diffusion_jump`
  The law of motion terms entering the HJB and whether a non-zero `jump(...)` hook is needed.
- `boundary_conditions`
  Left and right state boundaries, value matching rules, smooth-pasting or super-contact conditions, and whether the boundaries are fixed or endogenous.
- `policy_logic`
  Closed-form rules, FOCs, complementarity conditions, clipping rules, or regime-switching logic needed to update controls.

## Stage 4: Solve Plan

These fields define how the implementation will run.

- `solver_workflow`
  Choose among `solve`, `boundary_search`, `boundary_update`, and `sensitivity_analysis`.
- `numerical_method`
  The selected finite-difference scheme, boundary-search method if any, the number of boundary targets, and the reason these choices fit the model. This block should include explicit subfields such as `derivative_method`, `derivative_method_reason`, `boundary_search_method`, and `boundary_target_count`.
- `post_generation_tests`
  Which checks were run after code generation, whether they passed, and what repairs were required. This block should include explicit subfields such as `post_generation_tests`, `tests_passed`, and `repairs_applied`.
- `diagnostics`
  Quantities that should be checked after the solve to judge whether the implementation is healthy.

## Blocking Gaps

Treat these as code-generation blockers unless the user explicitly authorizes a simplifying assumption:

- state dimension is unclear
- environment readiness is unclear and the user expects runnable code
- the HJB is incomplete or inconsistent with the stated dynamics
- the model still requires unconfirmed derivation steps before it can be mapped into code
- a boundary condition is missing but the workflow depends on it
- a control variable exists in theory but has no update rule or FOC
- parameter symbols are defined but the runnable version has no confirmed numeric calibration
- the user asked for plots but the actual figure contents or output expectations are unspecified
- the task requests sensitivity analysis plus plotting but the file layout is still ambiguous
- the model clearly needs an outer-loop boundary method but the target condition is unspecified
- the diffusion degeneracy pattern is unclear but the derivative scheme choice would change the code

## Defaultable Items

These may be filled with explicit, labeled defaults if the user does not care:

- baseline numerical values for `Config`
- initial policy guess shape
- grid size for a first pass
- whether to print `grid.boundary`, `grid.df.head()`, and `grid.df.tail()`
- whether to use `MPLBACKEND=Agg` in examples

## Working Spec Template

```markdown
# Model Spec

## Research Goal
- ...

## Environment
- environment ready:
- environment type: repo-backed / installed package / unknown
- smoke test:
- blocking issue:

## State Variable
- paper symbol:
- FinHJB symbol:
- meaning:
- domain:

## Controls
- `control_name`:
  - paper symbol:
  - meaning:
  - admissible range:
  - update type: explicit / implicit

## Value Object
- ...

## HJB Equation
- ...

## Derivation Requirements
- direct mapping status:
- derivations still needed:
- user confirmations received:

## Drift, Diffusion, Jump
- drift:
- diffusion:
- jump:

## Boundary Conditions
- left boundary:
- right boundary:
- endogenous targets:

## Policy Logic
- ...

## Parameters
- `name = value`: meaning
- missing values requiring confirmation:

## Plot Requirements
- plots requested:
- quantities to plot:
- expected layout or figure style:
- output files:
- remaining plot questions:

## Project Layout
- layout type: single-file / split multi-file
- solve file:
- data file:
- plot file:
- layout reason:

## Solver Workflow
- primary workflow:
- reason:

## Numerical Method
- derivative method:
- derivative reason:
- diffusion near left boundary:
- diffusion near right boundary:
- boundary search method:
- boundary target count:
- bisection brackets:
- boundary-search reason:

## Post-Generation Tests
- checks run:
- tests passed:
- repairs applied:
- residual risks:

## Diagnostics
- ...

## Remaining Questions
- ...
```

## Output Rule

Before generating code, restate the specification in clear prose using the same economic vocabulary the user used, then map the paper symbols to FinHJB names. Before final delivery, append the executed test-and-repair summary from the post-generation loop.
