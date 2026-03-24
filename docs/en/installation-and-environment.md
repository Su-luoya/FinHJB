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

## What To Read Next

- If you want to use the package API directly, continue with [Modeling Guide](./modeling-guide.md), [Solver Guide](./solver-guide.md), and [API Reference](./api-reference.md).
- If you want to study the repository BCW examples, use the walkthrough pages from a repository checkout and start with [Getting Started](./getting-started.md).
