# Installation and Environment

This page is for all three documentation paths.

Read it when you need to answer one practical question first: what exactly should be installed for the workflow you want?

## Choose The Right Install Mode

### Published Package

Use the published package when you are working in your own downstream project and do not need the repository-only examples.

```bash
uv add finhjb
```

```bash
pip install finhjb
```

Installation defaults to CPU. If you want GPU support, install the appropriate JAX backend separately.

### Repository Checkout

Use a repository checkout when you want to:

- run `src/example/BCW2011Liquidation.py`
- run `src/example/BCW2011Hedging.py`
- inspect or modify the source tree
- install and develop the `finhjb-model-coder` skill from this repository

From the repository root:

```bash
uv sync
uv run python -c "import finhjb as fjb; print(fjb.__all__[:5])"
```

If you are on a headless machine or remote server, set:

```bash
export MPLBACKEND=Agg
```

## What The Package Install Does Not Include

The published wheel does not include repository-only files such as:

- `src/example/BCW2011Liquidation.py`
- `src/example/BCW2011Hedging.py`
- `skills/finhjb-model-coder/`

If your task depends on those files, use a repository checkout.

## If You Plan To Use `finhjb-model-coder`

The skill and the Python package are separate pieces.

Use this checklist before asking Codex for runnable code:

- if the task depends on repository examples or fixtures, prefer a repository checkout and the repository's own `uv` environment
- if the task belongs to a downstream project, install `finhjb` inside that project with `uv add finhjb` or `pip install finhjb`
- before accepting runnable delivery, confirm a smoke test such as `python -c "import finhjb"` or `uv run python -c "import finhjb"`

If that smoke test fails, the right next step is environment setup, not code generation.

## What To Read Next

- Package path: [Library Quickstart](./quickstart-library.md)
- BCW path: [Getting Started](./getting-started.md)
- Model Coder path: [FinHJB Model Coder](./finhjb-model-coder.md) or [Inputs and Readiness](./finhjb-model-coder-inputs-and-readiness.md)
