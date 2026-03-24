# FinHJB

[简体中文 README](./README.zh-CN.md) | [📖 Documentation](https://su-luoya.github.io/FinHJB/) | [📖 中文文档](https://su-luoya.github.io/FinHJB/zh/)

FinHJB is a Python library for solving one-dimensional Hamilton-Jacobi-Bellman (HJB) equations with JAX.

## Features

- **Policy Iteration**: Solve HJB equations using policy iteration with optional Anderson acceleration
- **Boundary Methods**: Boundary update and boundary search for optimal boundary conditions
- **Sensitivity Analysis**: Parameter continuation for sensitivity analysis across parameter ranges
- **Flexible Derivatives**: Support for central, forward, and backward finite difference schemes
- **GPU Ready**: Built on JAX for seamless CPU/GPU computation with automatic differentiation
- **Type-Safe Interfaces**: Fully typed parameter and policy classes for robust model construction
- **Serialization**: Save and load solutions, grids, and sensitivity results

## Installation

Install with `uv`:

```bash
uv add finhjb
```

Or with `pip`:

```bash
pip install finhjb
```

**Note**: Installation defaults to CPU. For GPU support, please install JAX separately with the appropriate CUDA/Metal backend.

Installing with `uv add` or `pip install` is the right path if you want to use the published `finhjb` package in your own project.

The BCW walkthrough scripts live in the repository at `src/example/BCW2011Liquidation.py` and `src/example/BCW2011Hedging.py`. They are not included in the published PyPI wheel, so reproducing those examples requires a repository checkout.

## Documentation Paths

If you are starting from the published package, begin with these local documentation entrypoints in the repository:

- [Overview](./docs/en/index.md)
- [Installation and Environment](./docs/en/installation-and-environment.md)
- [Modeling Guide](./docs/en/modeling-guide.md)
- [Solver Guide](./docs/en/solver-guide.md)
- [API Reference](./docs/en/api-reference.md)

If you are working from the repository and want to reproduce the BCW examples, start with:

- [Getting Started](./docs/en/getting-started.md)
- [BCW2011 Case Study](./docs/en/bcw2011-case-study.md)
- [Adapting BCW to Your Model](./docs/en/adapting-bcw-to-your-model.md)
