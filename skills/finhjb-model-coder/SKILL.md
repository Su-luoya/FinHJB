---
name: finhjb-model-coder
description: Translate continuous-time finance models into executable one-dimensional FinHJB implementations. Use when Codex needs to read model descriptions, LaTeX, HJB equations, FOCs, boundary conditions, or paper excerpts and turn them into `Parameter`/`Boundary`/`PolicyDict`/`Policy`/`Model` code, decide whether a model can be mapped to FinHJB, confirm the scholar's FinHJB environment and numerical-method choices, or ask for the missing details required to generate, test, and repair runnable code.
---

# FinHJB Model Coder

## Mission

Translate a scholar's model materials into runnable, tested, one-dimensional FinHJB code.

Work spec-first: route scope and readiness first, resolve only the real blockers, then generate, run, repair, and deliver.

## Use This Skill When

Use this skill when the user wants to:

- turn prose, LaTeX, HJB equations, FOCs, or paper excerpts into FinHJB code
- decide whether a model fits current one-dimensional FinHJB scope
- confirm runnable environment, numerical choices, or file layout before coding
- recover from unreliable calibration through `parameter-search rescue mode`

## Fast Routing

1. Build the working spec with `references/model-spec-schema.md`.
2. Check scope and environment with `references/readiness-and-scope.md`.
3. If scope, environment, derivation, calibration, or plotting is still blocked, stop and ask only the questions justified by `references/clarification-checklist.md`.
4. If the math already maps into code, lock interfaces with `references/math-to-finhjb-mapping.md`.
5. Lock derivative method, boundary-search backend, template, and layout with `references/implementation-decision-rules.md`.
6. If the model is runnable but parameter choice is unreliable, switch to `parameter-search rescue mode` and follow `references/parameter-search-protocol.md`.
7. Before delivery, use `references/delivery-and-validation.md` to format outputs and executed checks.

## Stage Protocol

- Stage 1: Spec
  Read `references/model-spec-schema.md` and restate the model in a compact executable spec.
- Stage 2: Readiness
  Read `references/readiness-and-scope.md` and decide one thing only: runnable now, blocked, or out of scope.
- Stage 3: Clarification
  Read `references/clarification-checklist.md` and ask only questions that change code, search, or layout.
- Stage 4: Mapping
  Read `references/math-to-finhjb-mapping.md` and map the economics into `Parameter`, `Boundary`, `PolicyDict`, `Policy`, and `Model`.
- Stage 5: Implementation Decisions
  Read `references/implementation-decision-rules.md` and lock derivative scheme, boundary-search method, template, and project layout.
- Stage 6: Rescue Search
  If calibration is the only remaining problem, read `references/parameter-search-protocol.md` and generate a reusable runner plus task adapter. Keep hard constraints before soft preferences.
- Stage 7: Delivery
  Read `references/delivery-and-validation.md` and return the executed artifacts, not just plausible code.

## Output Rule

For ordinary generation tasks, deliver:

1. structured specification summary
2. executable FinHJB code
3. executed test-and-repair summary
4. validation checklist

For rescue-search tasks, deliver:

1. structured specification summary
2. generated search runner plus task-specific adapter/config layer
3. executed search summary
4. recommended parameter sets
5. validation checklist
