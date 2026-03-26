# Environment Readiness

Check the execution environment before promising runnable FinHJB code.

## Hard Gate

- If the model is unsupported, stop for scope reasons.
- If the model is supported but `finhjb` is unavailable in the intended Python environment, stop for environment reasons.
- Final executable code delivery is allowed only after a smoke test confirms that `finhjb` imports successfully.

## What To Check

- Are we working inside a FinHJB repository checkout, or only inside a downstream project?
- Is the intended Python environment already known from the repo workflow, `.venv`, `uv`, or the user's command style?
- Can the environment import `finhjb`?
- Does the task rely on repository-only artifacts such as `src/example/...` files that are not shipped in the PyPI wheel?

## Recommended Installation Paths

### Repo-backed environment

Use this path when the task depends on repository examples, local templates, or fixtures.

- Prefer the repository's existing `uv` environment when available.
- If the user is setting up from scratch, guide them toward the repository's documented environment workflow.
- Treat `uv run python -c "import finhjb"` as the minimum smoke test for the repo-backed path.

### Package-only environment

Use this path when the user wants to generate code for their own project without repository-only examples.

- Recommend `uv add finhjb` first.
- If the user prefers `pip`, recommend `pip install finhjb`.
- The minimum smoke test is `python -c "import finhjb"`.

## Communication Rules

- State clearly whether the environment is ready, missing, or ambiguous.
- If the environment is missing, switch into install-assistance mode instead of pretending the final code is runnable.
- Once the smoke test passes, record the environment status in the model spec and continue.
- If the user refuses installation help, you may still provide a non-runnable skeleton only if you label it explicitly as untested and blocked by the missing environment.
