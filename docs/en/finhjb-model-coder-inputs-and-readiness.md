# Inputs And Readiness

`finhjb-model-coder` can only deliver runnable output when two pieces are in place:

- the model materials you provide
- the execution environment behind the conversation

## Best Input Bundle

The skill works best when you provide:

- the research question and the meaning of the value function
- the single state variable and its domain
- the HJB equation
- the controls and admissible ranges
- the FOCs or explicit policy rules
- the left and right boundary conditions
- any smooth-pasting, super-contact, or issuance conditions
- parameter meanings and baseline numeric values

You can provide these as prose, LaTeX, paper excerpts, or a mixture.

## Supported Model Shape

The current skill is built around one-dimensional FinHJB models.

The best fit is:

- one continuous state variable
- one or more continuous controls
- a scalar value function
- fixed boundaries, boundary search, or direct boundary updates

The skill should stop when the problem clearly requires multiple states, coupled value functions across regimes, or solver infrastructure that FinHJB does not currently provide.

## Hard Blockers Before Code Generation

The skill should stop and ask before code generation when:

- the environment cannot yet import `finhjb`
- parameter symbols are given but usable numeric values are not
- the mathematics still needs derivation before it maps into code
- the task asks for figures but the actual plot contents are unspecified
- the task combines sensitivity analysis with plotting but the output layout is still unclear
- rescue search is requested but the skill still does not know the fixed/search parameter split
- rescue search is requested but the desired “shape” has not been translated into diagnostics

## Environment Readiness

Environment readiness is a hard prerequisite for runnable delivery.

Use this rule:

- repository tasks should prefer the repository checkout and its `uv` environment
- downstream-project tasks should prefer a local project install such as `uv add finhjb` or `pip install finhjb`

Minimum smoke test:

```bash
python -c "import finhjb"
```

Repository smoke test:

```bash
uv run python -c "import finhjb"
```

## Numerical Choices The Skill Must Make Explicit

### Derivative scheme

Do not silently default to `central` in every model.

Use this rule of thumb:

- `central` when diffusion stays materially away from zero at both boundaries
- `forward` when diffusion becomes very small near the left boundary
- `backward` when diffusion becomes very small near the right boundary

### Boundary-search method

Do not treat boundary search as a hidden implementation detail.

Use this heuristic:

- 1-2 boundary targets with credible brackets: start with `bisection`
- 3 or more targets: start with `hybr` or another multidimensional root solver

If the first default fails the test-repair loop, the final implementation should be upgraded explicitly.

## Rescue Search Inputs

If the model is already runnable but the calibration or boundary guesses are not trustworthy, `finhjb-model-coder` can switch into `parameter-search rescue mode`.

The minimum extra inputs are:

- which parameters must stay fixed
- which parameters may move, with a range and scale
- which conditions are hard constraints
- which outcomes are just soft preferences
- which diagnostics should be extracted from each solve
- how large the initial search budget should be

The skill should not search until vague shape requests such as “make the plot smoother” have been turned into explicit diagnostics.

## Related Pages

- [Output and Validation](./finhjb-model-coder-output-and-validation.md)
- [Full consolidated skill page](./finhjb-model-coder.md)
