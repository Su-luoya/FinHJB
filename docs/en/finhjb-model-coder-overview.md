# Model Coder Overview

This page is the front door for the `finhjb-model-coder` path.

Read it if you want to know whether the skill is the right tool before you prepare equations or environment details.

## What The Skill Is For

`finhjb-model-coder` is the repository's Codex skill for turning continuous-time finance models into executable one-dimensional FinHJB code.

The intended input is not an existing Python implementation. The intended input is:

- prose notes
- LaTeX
- HJB equations
- first-order conditions
- paper excerpts

## What The Skill Does

The skill is designed to:

- decide whether the model fits the current one-dimensional FinHJB interface
- confirm that the target Python environment can import `finhjb`
- ask only the blocking clarification questions that change code generation
- choose the derivative scheme and boundary-search method explicitly
- generate runnable FinHJB code
- run a test-repair loop before delivery

## When To Use It

Use the skill when you want theory-to-code translation and you do not want to hand-write the first FinHJB implementation yourself.

Typical requests:

- “Read this HJB and map it into `Parameter`, `Boundary`, `PolicyDict`, `Policy`, and `Model`.”
- “Tell me whether this paper's model fits one-dimensional FinHJB.”
- “Generate and test the baseline implementation before handing it back.”

## When Not To Use It

Do not use the skill as the primary path when:

- you already have a clean Python implementation and mainly need API lookup
- your model clearly needs multiple continuous state variables
- you want to learn the package by reading the BCW examples first

In those cases, start with the package path or the BCW path instead.

## Read Next

- [Inputs and Readiness](./finhjb-model-coder-inputs-and-readiness.md)
- [Output and Validation](./finhjb-model-coder-output-and-validation.md)
- [Full consolidated skill page](./finhjb-model-coder.md)
