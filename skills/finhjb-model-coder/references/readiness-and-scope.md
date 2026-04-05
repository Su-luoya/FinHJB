# Readiness And Scope

Read this file before promising runnable delivery.

Your decision after reading: runnable now, blocked for environment reasons, or blocked for scope reasons.

## Hard Gate

Stop for scope reasons when the model clearly requires:

- two or more continuous state variables
- path dependence that cannot be reduced to one state
- multiple coupled value functions across regimes
- intervention or equilibrium machinery outside current FinHJB interfaces
- free-boundary structure that cannot be represented with current `Boundary` and boundary-search interfaces

Stop for environment reasons when:

- the intended Python environment cannot import `finhjb`
- the task depends on repo-only examples or fixtures but the user is not working in a repo-backed environment

Final executable delivery is allowed only after a smoke test confirms that `finhjb` imports successfully.

## Environment Routing

- Repo-backed task:
  Use this when the task depends on repository examples, local templates, fixtures, or source-only artifacts.
  Minimum smoke test: `uv run python -c "import finhjb"`.
- Package-only task:
  Use this when the user wants code for their own project without repo-only assets.
  Recommend `uv add finhjb` first, or `pip install finhjb` if needed.
  Minimum smoke test: `python -c "import finhjb"`.

## Communication Rule

- If scope is broken, say the model is out of current one-dimensional FinHJB scope and name the exact blocker.
- If environment is broken, switch into install-assistance mode instead of pretending the code is runnable.
- If the user refuses environment setup, you may provide a clearly labeled non-runnable skeleton only if that reduced goal is explicit.
