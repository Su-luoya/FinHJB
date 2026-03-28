# FinHJB Model Coder Skill

`finhjb-model-coder` is the repository's Codex skill for turning continuous-time finance models into executable one-dimensional FinHJB code.

This page is now the consolidated hub for the Model Coder path.

If you are entering this path fresh, read these pages in order:

- [Model Coder Overview](./finhjb-model-coder-overview.md)
- [Inputs and Readiness](./finhjb-model-coder-inputs-and-readiness.md)
- [Output and Validation](./finhjb-model-coder-output-and-validation.md)

Keep this page open when you want the full all-in-one reference on scope, readiness, numerical choices, testing, and failure modes.

This page is for researchers who want to start from equations, paper notes, or LaTeX rather than from an existing Python file.

## What The Skill Does

The skill is designed to:

- read prose, LaTeX, HJB equations, FOCs, and paper excerpts
- decide whether the model fits the current one-dimensional FinHJB interface
- confirm that the target Python environment can import `finhjb`
- stop and confirm missing derivations, calibrations, plotting requirements, or layout decisions before code generation
- confirm the derivative scheme and boundary-search method when those choices affect the implementation
- generate runnable FinHJB code
- run a post-generation test loop and repair failures before delivery
- return a structured specification summary, the code, an executed test summary, and a validation checklist

The core output is not a BCW reproduction. The core output is theory-to-code translation.

## Stage 1: Before Code Generation

### Supported Model Shape

The current package and the skill are both built around a one-dimensional state grid.

The best fit is:

- one continuous state variable
- one or more continuous controls
- a scalar value function
- fixed boundaries, residual-based boundary search, or direct boundary updates

The skill will refuse to generate misleading code for models that clearly require:

- multiple continuous state variables
- coupled value functions across regimes
- path dependence that cannot be reduced to one state
- solver infrastructure that FinHJB does not currently provide

When that happens, the skill should explain why the model is out of scope and propose the closest implementable simplification.

### Best Input Bundle

The more of the mathematical structure you provide up front, the better the first generated implementation will be.

Recommended inputs:

- the research question and what the value function represents
- the single state variable and its domain
- the full HJB equation
- the controls and their admissible ranges
- the FOC or explicit policy rule for each control
- left and right boundary conditions
- any smooth-pasting, super-contact, or issuance conditions
- parameter meanings and baseline calibration values

You can provide this as:

- plain text notes
- LaTeX
- copied paper excerpts
- a mixture of the above

If a paper screenshot or PDF image omits key formulas, the skill should ask you to paste the missing text before generating code.

### Hard Blockers The Skill Must Surface

The skill should stop and ask before code generation when:

- the environment cannot yet import `finhjb`
- the document defines parameter symbols but omits usable numeric values
- the mathematics still needs derivation before it maps into implementation-ready formulas
- the user requests figures but has not specified what to plot
- the task combines sensitivity analysis with plotting but the output layout is still unclear

This is the main safety rule of the skill: do not silently fill in missing mathematics or deliverable requirements.

## Stage 2: Mapping, Methods, And Layout

### Environment And Preconditions

This skill treats environment readiness as a hard prerequisite for runnable delivery.

What that means in practice:

- if you are working from a FinHJB repository checkout, the skill should prefer the repository's own Python environment
- if you are working in a downstream project, the skill should prefer an installed package workflow such as `uv add finhjb` or `pip install finhjb`
- if the environment cannot yet import `finhjb`, the skill should switch into install-assistance mode instead of pretending the final code is runnable

The minimum smoke test is:

```bash
python -c "import finhjb"
```

Inside this repository, a more faithful smoke test is:

```bash
uv run python -c "import finhjb"
```

### Derivation Before Code

If the mathematics still needs derivation before it maps into code, the skill should stop and say exactly which derivation steps are still missing.

Typical examples:

- the state normalization is still implicit in the paper
- the HJB has not yet been rewritten into an implementation-ready residual
- the control law still needs to be turned into a closed-form update or an FOC residual
- the paper boundary conditions still need to be rewritten as `Boundary` values or `BoundaryConditionTarget`s

The skill should confirm those derivations with the user before it generates code.

### Choosing The Derivative Scheme

The skill should not silently default `derivative_method="central"` in every model.

Use this rule of thumb:

- choose `central` when the diffusion term stays materially away from zero at both boundaries
- choose `forward` when the diffusion term becomes very small near the left boundary
- choose `backward` when the diffusion term becomes very small near the right boundary
- if the excerpt is too incomplete to tell, the skill should ask before generating code

The skill should explain this choice in both the specification summary and the generated `Config(...)` block.

### Choosing The Boundary Search Method

For endogenous boundaries, the skill should choose the search backend explicitly instead of treating it as an implementation detail.

Default heuristic:

- for 1-2 boundary targets, start with `bisection` when credible `low` / `high` brackets exist
- for 3 or more boundary targets, start with `hybr` or another supported multidimensional root solver

Important exception:

- if the 1-2 target default fails the post-generation test loop, the skill should promote the final implementation to `hybr` or another supported method and explain why

### File Layout For Sensitivity Analysis And Plotting

Do not treat every task as a single-script deliverable.

Recommended rule:

- if the task is only a baseline solve or a compact benchmark reproduction, one file is usually enough
- if the task combines sensitivity analysis with saved outputs and figures, split the project into at least three files:
  - a solve/model file
  - a data-save or data-export file
  - a plotting file

This separation makes reruns, plotting changes, and diagnostics much easier to maintain.

## Stage 3: Generation, Testing, And Delivery

### Interaction Flow

The intended workflow is:

1. You provide the model materials.
2. The skill checks whether the model is in scope for one-dimensional FinHJB.
3. The skill confirms that the target Python environment can run `finhjb`.
4. The skill extracts a structured model specification.
5. The skill asks only the blocking questions that change code generation.
6. The skill confirms the derivative scheme, boundary-search method, and file layout.
7. The skill chooses the closest FinHJB template.
8. The skill generates code.
9. The skill runs a test loop and repairs failures before delivery.
10. The skill returns:
   - a structured model spec
   - executable FinHJB code
   - an executed test-and-repair summary
   - a validation checklist

### Post-Generation Test Loop

Before delivery, the skill should run:

- a syntax and import check
- a `Solver(...)` construction check
- at least one baseline solve
- required figure or summary output checks if the task asked for them

If these checks fail for fixable reasons, the skill should repair the implementation and rerun the checks. Only unresolved external blockers such as missing equations, missing derivations, or a missing environment should stop the loop.

## Example Prompts

```text
Use $finhjb-model-coder to turn this one-state financing model into executable FinHJB code. I will paste the HJB, controls, boundary conditions, and calibration next.
```

```text
Use $finhjb-model-coder to read this paper excerpt and tell me whether it can be implemented in one-dimensional FinHJB. If yes, generate the code skeleton. If not, explain the smallest workable simplification.
```

```text
Use $finhjb-model-coder to map this HJB and FOC system into Parameter, Boundary, PolicyDict, Policy, and Model classes, and give me a validation checklist for the first solve.
```

```text
Use $finhjb-model-coder to read this model, confirm whether my current environment can run FinHJB, list any derivations that still need confirmation, choose the derivative scheme and boundary-search method explicitly, then generate and test the code before handing it back.
```

## Installation And Updates

From a repository checkout, install the skill with:

```bash
python scripts/install_skill.py
```

Useful variants:

```bash
python scripts/install_skill.py --dry-run
python scripts/install_skill.py --dest ~/.codex/skills --force
python scripts/install_skill.py --mode link --force
```

Manual installation is also fine: copy `skills/finhjb-model-coder` into `${CODEX_HOME:-$HOME/.codex}/skills/`.

Installing the skill does not install the `finhjb` runtime into every downstream project automatically. The execution environment still needs a working `finhjb` import.

## Common Failure Modes

### The model really has two states

The right next step is not code generation. The right next step is to decide whether a one-state reduction is acceptable.

### The HJB is present but the boundary conditions are not

The skill should stop and ask for the missing left or right boundary logic before choosing `solve()`, `boundary_search()`, or `boundary_update()`.

### The paper defines parameters but does not give the calibration

The skill should stop and ask which numeric values belong in the first runnable implementation. It should not invent a baseline by borrowing numbers from a different example.

### The mathematics still needs derivation before it maps into code

The skill should stop and list the missing derivation steps. It should confirm those steps with the user before generating code.

### The user asked for figures but did not specify what to plot

The skill should stop and ask which solved quantities, comparisons, or paper-style figures belong in the deliverable. It should not silently invent a plotting layout.

### The task asks for sensitivity analysis and plots, but the code is still organized as one file

The skill should reorganize the deliverable into separate solve, data, and plotting files.

### The paper defines a control but not the update rule

The skill should ask whether the control is intended to be explicit, implicit through an FOC, or pinned down by a regime condition.

### The first generated solve is numerically unstable

That usually means the model needs better initialization, a different derivative scheme, better boundary logic, or a cleaner baseline before sensitivity analysis. The skill should first try to repair the generated code and rerun the solve loop.

## Recommended Reading Order

If you are new to the repository:

1. read this page
2. read [Modeling Guide](./modeling-guide.md)
3. read [Solver Guide](./solver-guide.md)
4. only then use the skill on your own model materials
