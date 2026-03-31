# Installation and Environment

The first practical question in FinHJB is not about the HJB itself. It is whether you need the published package or the repository checkout.

Use the published package for downstream projects. Use the repository checkout when you need the BCW examples, the source tree, or `finhjb-model-coder`.

## Choose The Right Install Mode

### Published Package

Choose the published package when you are working in your own project and do not need repository-only materials.

```bash
uv add finhjb
```

```bash
pip install finhjb
```

### Repository Checkout

Choose a repository checkout when you want to:

- run `src/example/BCW2011Liquidation.py`,
- run `src/example/BCW2011Refinancing.py`,
- run `src/example/BCW2011Hedging.py`,
- run `src/example/BCW2011CreditLine.py`,
- inspect or modify the source tree,
- install and develop the `finhjb-model-coder` skill from this repository.

From the repository root:

```bash
uv sync
uv run python -c "import finhjb as fjb; print(fjb.__all__[:5])"
```

If you are on a headless machine or remote server, also set:

```bash
export MPLBACKEND=Agg
```

## Repository-Only Material

The published wheel does not include:

- `src/example/BCW2011Liquidation.py`
- `src/example/BCW2011Refinancing.py`
- `src/example/BCW2011Hedging.py`
- `src/example/BCW2011CreditLine.py`
- `skills/finhjb-model-coder/`

If your task depends on those files, use a repository checkout.

## Before You Ask `finhjb-model-coder` For Runnable Code

The skill and the Python package are separate objects. The skill can only deliver honestly runnable code once the environment is already in working order.

Use this checklist before asking Codex for runnable code:

- if the task depends on repository examples or fixtures, prefer a repository checkout and the repository `uv` environment,
- if the task belongs to a downstream project, install `finhjb` inside that project with `uv add finhjb` or `pip install finhjb`,
- before accepting runnable delivery, confirm a smoke test such as `python -c "import finhjb"` or `uv run python -c "import finhjb"`.

If that smoke test fails, the right next step is environment setup, not code generation.

## Related Pages

- Package path: [Library Quickstart](./quickstart-library.md)
- BCW path: [Getting Started](./getting-started.md)
- Model Coder path: [FinHJB Model Coder](./finhjb-model-coder.md)
