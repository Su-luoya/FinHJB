---
name: finhjb-model-coder
description: Translate continuous-time finance models into executable one-dimensional FinHJB implementations. Use when Codex needs to read model descriptions, LaTeX, HJB equations, FOCs, boundary conditions, or paper excerpts and turn them into `Parameter`/`Boundary`/`PolicyDict`/`Policy`/`Model` code, decide whether a model can be mapped to FinHJB, or ask the scholar for the missing details required to generate runnable code.
---

# FinHJB Model Coder

## Overview

Translate a scholar's model materials into runnable FinHJB code.

Work in a spec-first loop: extract the model, identify blocking gaps, confirm only the high-impact details, then generate code and validation guidance.

## Decision Rule

- Read `references/model-spec-schema.md` first to build the working model specification.
- Read `references/clarification-checklist.md` before asking questions or making assumptions.
- Read `references/math-to-finhjb-mapping.md` when mapping mathematics into FinHJB interfaces.
- Read `references/template-selection.md` before choosing a template in `assets/templates/`.
- Read `references/output-contract.md` before drafting the final deliverables.
- Read `references/validation-checklist.md` before emitting validation advice.
- Read `references/unsupported-models.md` as soon as the model looks multi-state, path-dependent, impulse-driven, equilibrium-closed, or otherwise outside current FinHJB scope.

## Workflow

1. Normalize the input into a structured model specification. Accept prose, LaTeX, paper excerpts, or mixed notes.
2. Detect whether the model is implementable in current FinHJB. FinHJB here is one-dimensional; do not fake multidimensional support.
3. Ask concise blocking questions when the state variable, control set, HJB terms, boundary conditions, FOC logic, or solver workflow are missing or ambiguous enough to change code generation.
4. Choose the closest template from `assets/templates/`.
5. Generate three deliverables together: a specification summary, an executable Python file, and a validation checklist.
6. Keep the code faithful to the theorized model. Name intermediate terms by economic meaning and add brief comments mapping key equations to code.
7. If the model is out of scope, stop code generation and explain the smallest workable simplification or the package extension required.

## Generation Rules

- Generate a single runnable Python file unless the user explicitly asks for a larger project layout.
- Use the fixed FinHJB backbone: `Parameter`, `Boundary`, `PolicyDict`, `Policy`, `Model`, and a solver entry block.
- Prefer `@explicit_policy` when a stable closed-form update exists; use `@implicit_policy` when the control is naturally defined through a residual or FOC.
- Choose `solve()` for fixed boundaries, `boundary_search()` for residual-based boundary targets, and `boundary_update()` when a solved grid directly implies new boundaries.
- If the input comes from a paper fragment and formulas are incomplete or image-only, ask the scholar to paste the missing text before committing to code.
- Do not leave silent placeholders in the final code. If a quantity is intentionally unresolved, call it out explicitly in the specification summary and validation list.

## Output

Emit the final answer in three blocks:

1. Structured specification summary
2. Executable FinHJB code
3. Validation checklist

Name the suggested output files as `finhjb_<model-slug>.py` and `finhjb_<model-slug>_spec.md`.
