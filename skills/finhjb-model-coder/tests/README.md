# BCW Case II Skill Evaluation

This folder stores an interactive forward-test for `finhjb-model-coder`.

The goal is to evaluate whether the skill behaves like a real model-coding assistant when given the BCW paper as the only theory source for `Case II: Refinancing`.

## What This Bundle Contains

- `case_ii_refinancing_prompt.md`
  The exact user prompt and source-paper path.
- `case_ii_refinancing_live_transcript.md`
  A cleaned record of the real interaction used to confirm the model before coding.
- `case_ii_refinancing_scripted_protocol.md`
  A reusable interaction script for future reruns.
- `case_ii_refinancing_confirmed_spec.md`
  The model specification confirmed from the paper and the interaction.
- `BCWrefinancing.py`
  The generated FinHJB implementation artifact.
- `artifacts/`
  Runtime outputs such as the Figure 3-style comparison plot and optional summaries.

## How To Re-Run Manually

From the repository root:

```bash
MPLBACKEND=Agg uv run python skills/finhjb-model-coder/tests/BCWrefinancing.py
```

This writes runtime artifacts into `skills/finhjb-model-coder/tests/artifacts/`.

## Acceptance Focus

This is not only a smoke test.

The fixture is intended to verify that the skill:

- identifies the BCW refinancing case correctly
- asks only the genuinely blocking confirmation questions
- generates a refinancing-only one-control model rather than the hedging extension
- reproduces the qualitative Figure 3 comparison for `phi = 1%` and `phi = 0`
