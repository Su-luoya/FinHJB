# Scripted Interaction Protocol

Use this protocol to rerun the BCW refinancing interaction test in the future.

## Goal

Check whether `finhjb-model-coder` behaves like an interactive model-coding assistant instead of skipping straight to code.

## Inputs

- source paper:
  `src/example/A_unified_theory_of_tobin's_q,_corporate_investment,_financing,_and_risk_management.md`
- target task:
  BCW `Case II: Refinancing`

## Expected Skill Behavior

### Preflight Before Asking

Skill should first confirm the execution context without asking unnecessary questions:

- the target is inside the FinHJB repository
- the intended environment is repo-backed rather than PyPI-only
- runnable delivery still requires a smoke test such as `uv run python -c "import finhjb"`

### Question 1

Skill should confirm the model identity:

> I read the paper and identify the target as BCW `Case II: Refinancing`, not the hedging extension. Is that the intended case?

Expected user answer:

> Yes.

### Question 2

Skill should confirm the evaluation style:

> Should this be treated as an interaction-quality test, with the clarification process archived alongside the final artifact?

Expected user answer:

> Yes.

### Question 3

Skill should confirm the comparison scope:

> Should the final implementation reproduce the Figure 3 comparison for both `phi = 1%` and `phi = 0`?

Expected user answer:

> Yes.

### After The Questions

The skill should then say, in substance:

- the model is one-dimensional
- the repository provides the intended FinHJB environment path for this evaluation
- the paper already supplies the key equations and benchmark calibration
- `central` is the derivative-method default because the diffusion term stays away from zero at the boundaries in this fixture
- the target-count heuristic would start from `bisection`, but the final method may be promoted to `hybr` if the post-generation solve loop rejects the smaller-target default
- no further blocking questions are needed
- code generation can begin

### After Code Generation

The skill should execute a solve loop before archiving the artifact:

- import the generated file in the repo-backed environment
- construct the solver
- solve both Figure 3 cases
- write the figure and summary artifacts
- if the initial boundary-search choice fails materially, repair the implementation and rerun

## Failure Modes

Treat the interaction as failed if the skill:

- confuses refinancing with the hedging extension
- ignores environment readiness for runnable delivery
- asks for equations that are already present in the paper
- introduces a second state variable
- silently defaults the derivative scheme or boundary-search method without explaining them
- ignores the `phi = 0` comparison
- begins coding before confirming the intended deliverable shape
- skips the post-generation test loop
