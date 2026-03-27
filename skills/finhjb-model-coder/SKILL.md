---
name: finhjb-model-coder
description: Translate continuous-time finance models into executable one-dimensional FinHJB implementations. Use when Codex needs to read model descriptions, LaTeX, HJB equations, FOCs, boundary conditions, or paper excerpts and turn them into `Parameter`/`Boundary`/`PolicyDict`/`Policy`/`Model` code, decide whether a model can be mapped to FinHJB, confirm the scholar's FinHJB environment and numerical-method choices, or ask for the missing details required to generate, test, and repair runnable code.
---

# FinHJB Model Coder

## Overview

Translate a scholar's model materials into runnable and tested FinHJB code.

Work in a spec-first loop: extract the model, identify blocking gaps, confirm only the high-impact details, generate code, test it, repair failures, then hand back a checked deliverable.

## Decision Rule

- Read `references/environment-readiness.md` as soon as the model looks implementable. Environment readiness is a hard gate before final code delivery.
- Read `references/model-spec-schema.md` first to build the working model specification.
- Read `references/clarification-checklist.md` before asking questions or making assumptions.
- Read `references/numerical-method-selection.md` before locking `derivative_method`, `boundary_search(method=...)`, or any boundary-search fallback.
- Read `references/math-to-finhjb-mapping.md` when mapping mathematics into FinHJB interfaces.
- Read `references/template-selection.md` before choosing a template in `assets/templates/`.
- Read `references/output-contract.md` before drafting the final deliverables.
- Read `references/validation-checklist.md` before emitting validation advice.
- Read `references/unsupported-models.md` as soon as the model looks multi-state, path-dependent, impulse-driven, equilibrium-closed, or otherwise outside current FinHJB scope.

## Workflow

1. Normalize the input into a structured model specification. Accept prose, LaTeX, paper excerpts, or mixed notes.
2. Detect whether the model is implementable in current FinHJB. FinHJB here is one-dimensional; do not fake multidimensional support.
3. Confirm environment readiness before promising runnable code. If `finhjb` is not available in the target Python environment, switch to install-assistance mode and stop before final code delivery.
4. Ask concise blocking questions when the state variable, control set, HJB terms, boundary conditions, parameter values, FOC logic, numerical method, or solver workflow are missing or ambiguous enough to change code generation.
5. Lock the structured spec, including `derivative_method`, `boundary_search_method`, and the reason for each choice.
6. Choose the closest template from `assets/templates/`.
7. Generate code and keep it faithful to the theorized model. Name intermediate terms by economic meaning and add brief comments mapping key equations to code.
8. Run the post-generation test loop:
   - syntax and import checks
   - `Solver(...)` construction
   - at least one baseline solve
   - required plots or summary artifacts when the task asks for them
9. If the generated code fails, repair it and rerun the test loop before handing it back. If the failure is blocked by missing equations, missing environment, or unsupported model structure, stop and explain the blocker explicitly.
10. If the model is out of scope, stop code generation and explain the smallest workable simplification or the package extension required.

## Generation Rules

- Generate a single runnable Python file unless the user explicitly asks for a larger project layout.
- Use the fixed FinHJB backbone: `Parameter`, `Boundary`, `PolicyDict`, `Policy`, `Model`, and a solver entry block.
- Prefer `@explicit_policy` when a stable closed-form update exists; use `@implicit_policy` when the control is naturally defined through a residual or FOC.
- Choose `solve()` for fixed boundaries, `boundary_search()` for residual-based boundary targets, and `boundary_update()` when a solved grid directly implies new boundaries.
- Treat environment readiness as a hard requirement for runnable delivery. Prefer a repo-backed environment for repository examples and `uv add finhjb` or `pip install finhjb` for package-only workflows.
- Treat missing economic parameter values as a hard blocker for runnable delivery unless the user explicitly confirms a baseline calibration, a sensitivity grid, or a placeholder-only scaffold.
- Do not silently default the derivative scheme. Use `central` only when the diffusion term stays materially away from zero at both edges; consider `forward` for left-edge degeneracy and `backward` for right-edge degeneracy.
- If `boundary_search()` has one or two endogenous targets, start from `bisection` when you have credible brackets. For three or more targets, or when the two-target default fails the post-generation test loop, promote the search to `hybr` or another supported multidimensional method and say why.
- If the input comes from a paper fragment and formulas are incomplete or image-only, ask the scholar to paste the missing text before committing to code.
- Do not leave silent placeholders in the final code. If a quantity is intentionally unresolved, call it out explicitly in the specification summary and validation list.
- In generated code, add short comments near `Config(...)` and the solve entrypoint explaining why the derivative scheme and solver workflow were chosen.

## Output

Emit the final answer in four blocks:

1. Structured specification summary
2. Executable FinHJB code
3. Executed test-and-repair summary
4. Validation checklist

Name the suggested output files as `finhjb_<model-slug>.py` and `finhjb_<model-slug>_spec.md`.
