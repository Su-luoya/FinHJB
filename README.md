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
