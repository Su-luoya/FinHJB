# FinHJB

[简体中文 README](./README.zh-CN.md) | [📖 Documentation](https://su-luoya.github.io/FinHJB/) | [📖 中文文档](https://su-luoya.github.io/FinHJB/zh/)

FinHJB is a Python library for solving one-dimensional Hamilton-Jacobi-Bellman (HJB) equations with JAX.

This repository also ships a Codex skill, `finhjb-model-coder`, for turning continuous-time finance models, LaTeX notes, and paper excerpts into executable one-dimensional FinHJB code.

## Features

- **Policy Iteration**: Solve HJB equations using policy iteration with optional Anderson acceleration
- **Boundary Methods**: Boundary update and boundary search for optimal boundary conditions
- **Sensitivity Analysis**: Parameter continuation for sensitivity analysis across parameter ranges
- **Flexible Derivatives**: Support for central, forward, and backward finite difference schemes
- **GPU Ready**: Built on JAX for seamless CPU/GPU computation with automatic differentiation
- **Type-Safe Interfaces**: Fully typed parameter and policy classes for robust model construction
- **Serialization**: Save and load solutions, grids, and sensitivity results
- **`finhjb-model-coder` Skill**: Turn theory, HJB equations, FOCs, and boundary conditions into FinHJB model files plus validation guidance

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

The `finhjb-model-coder` skill also lives in the repository, not in the published PyPI wheel.

## Two Ways To Use FinHJB

### 1. Use The Python Package Directly

Use the package directly when you already know the model structure you want to implement and want to write or maintain the code yourself.

### 2. Use The `finhjb-model-coder` Skill

Use the skill when you want Codex to:

- read a continuous-time finance model from prose, LaTeX, or paper excerpts
- decide whether the model fits the current one-dimensional FinHJB interface
- confirm that the target Python environment can actually run `finhjb`
- confirm the finite-difference scheme and boundary-search method before code generation
- ask for the missing boundary, control, or calibration details that materially affect the code
- stop and confirm baseline parameter values when the source document defines symbols but not usable numbers
- ask which quantities to plot when the user wants figures but has not specified the target plot
- split the deliverable into solve, data, and plotting files when the task combines sensitivity analysis with plotting
- stop and confirm the missing derivation steps when the math does not yet map directly into FinHJB code
- generate a runnable FinHJB model file, test it, repair failures, and return a structured spec summary plus validation guidance

The best input bundle includes:

- the research question and the single state variable
- the HJB equation
- controls and their FOCs or explicit policy rules
- boundary conditions, value matching, or smooth-pasting conditions
- parameter definitions and baseline calibration values

Before it hands back "runnable code," the skill now expects:

- a runnable FinHJB environment, either from this repository checkout or from an installed `finhjb` package
- an explicit derivative-scheme choice when boundary diffusion degeneracy matters
- an explicit boundary-search choice when endogenous boundaries are present

If the environment is missing, the skill should pause code delivery and help the user get to a simple smoke test such as `python -c "import finhjb"` or `uv run python -c "import finhjb"`.

Install the skill from a repository checkout:

```bash
python scripts/install_skill.py
```

Preview the resolved install target or replace an existing installation:

```bash
python scripts/install_skill.py --dry-run
python scripts/install_skill.py --dest ~/.codex/skills --force
```

If you prefer a live symlink while developing the skill:

```bash
python scripts/install_skill.py --mode link --force
```

If you prefer manual installation, copy `skills/finhjb-model-coder` into `${CODEX_HOME:-$HOME/.codex}/skills/`.

The skill also assumes the execution environment is ready:

- for repository examples, prefer the repository's own `uv` environment
- for downstream projects, install the published package with `uv add finhjb` or `pip install finhjb`
- after code generation, expect the skill to run a solve-loop check before it treats the artifact as delivered

## Documentation Paths

If you are starting from the published package, begin with these local documentation entrypoints in the repository:

- [Overview](./docs/en/index.md)
- [Installation and Environment](./docs/en/installation-and-environment.md)
- [Modeling Guide](./docs/en/modeling-guide.md)
- [Solver Guide](./docs/en/solver-guide.md)
- [API Reference](./docs/en/api-reference.md)

If you want to use the model-to-code workflow, start with:

- [FinHJB Model Coder Skill](./docs/en/finhjb-model-coder.md)

If you are working from the repository and want to reproduce the BCW examples, start with:

- [Getting Started](./docs/en/getting-started.md)
- [BCW2011 Case Study](./docs/en/bcw2011-case-study.md)
- [Adapting BCW to Your Model](./docs/en/adapting-bcw-to-your-model.md)
