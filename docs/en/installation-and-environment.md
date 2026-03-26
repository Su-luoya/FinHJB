# Installation and Environment

Read this page before your first solve.

This page keeps installation intentionally minimal. If you only want to use the published package, install FinHJB with one of these commands:

```bash
uv add finhjb
```

```bash
pip install finhjb
```

Installation defaults to CPU. If you want GPU support, install the appropriate JAX backend separately.

## What This Installs

These commands install the published `finhjb` package for use in your own project.

They do not install the repository source tree, so files such as:

- `src/example/BCW2011Liquidation.py`
- `src/example/BCW2011Hedging.py`

are not part of the PyPI wheel.

## If You Plan To Use `finhjb-model-coder`

The skill itself is installed separately from the Python package, and it assumes there is a runnable FinHJB environment behind the conversation.

Use this checklist:

- if the task depends on repository-only examples or fixtures, work from a repository checkout and prefer the repository's own `uv` environment
- if the task is for your own downstream project, install the published package into that project with `uv add finhjb` or `pip install finhjb`
- before asking the skill for runnable code, confirm a smoke test such as `python -c "import finhjb"` or `uv run python -c "import finhjb"`

If that smoke test fails, the skill should help with installation first instead of pretending the final code has already been tested.

## What To Read Next

- If you want to use the package API directly, continue with [Modeling Guide](./modeling-guide.md), [Solver Guide](./solver-guide.md), and [API Reference](./api-reference.md).
- If you want to use the theory-to-code workflow, read [FinHJB Model Coder Skill](./finhjb-model-coder.md) after the environment is ready.
- If you want to study the repository BCW examples, use the walkthrough pages from a repository checkout and start with [Getting Started](./getting-started.md).
