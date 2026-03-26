# FinHJB Model Coder Skill

`finhjb-model-coder` is the repository's Codex skill for turning continuous-time finance models into executable one-dimensional FinHJB code.

This page is for researchers who want to start from equations, paper notes, or LaTeX rather than from an existing Python file.

## What The Skill Does

The skill is designed to:

- read prose, LaTeX, HJB equations, FOCs, and paper excerpts
- decide whether the model fits the current one-dimensional FinHJB interface
- ask follow-up questions when boundary conditions, controls, or calibration details are missing
- generate a runnable FinHJB model file
- summarize the model specification in implementation-ready language
- propose a validation checklist so you can judge whether the first solve is credible

The core output is not a BCW reproduction. The core output is theory-to-code translation.

## Supported Model Shape

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

## Best Input Format

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

## Interaction Flow

The intended workflow is:

1. You provide the model materials.
2. The skill extracts a structured model specification.
3. The skill asks only the blocking questions that change code generation.
4. The skill chooses the closest FinHJB template.
5. The skill returns:
   - a structured model spec
   - executable FinHJB code
   - a validation checklist

This spec-first step is important. In continuous-time models, the biggest implementation mistakes usually come from silent assumptions about boundaries, controls, or normalization.

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

## Common Failure Modes

### The model really has two states

In that case, the right next step is not code generation. The right next step is to decide whether a one-state reduction is acceptable.

### The HJB is present but the boundary conditions are not

The skill should stop and ask for the missing left or right boundary logic before choosing `solve()`, `boundary_search()`, or `boundary_update()`.

### The paper defines a control but not the update rule

The skill should ask whether the control is intended to be explicit, implicit through an FOC, or pinned down by a regime condition.

### The first generated solve is numerically unstable

That usually means the model needs better initialization, better boundary logic, or a cleaner baseline before sensitivity analysis. Use the validation checklist and then return to:

- [Modeling Guide](./modeling-guide.md)
- [Solver Guide](./solver-guide.md)
- [Adapting BCW To Your Model](./adapting-bcw-to-your-model.md)

## Recommended Reading Order

If you are new to the repository:

1. read this page
2. read [Modeling Guide](./modeling-guide.md)
3. read [Solver Guide](./solver-guide.md)
4. only then use the skill on your own model materials
