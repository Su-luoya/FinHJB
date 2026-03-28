# FinHJB

[简体中文 README](./README.zh-CN.md) | [Documentation](https://su-luoya.github.io/FinHJB/) | [中文文档](https://su-luoya.github.io/FinHJB/zh/)

FinHJB is a Python library for solving one-dimensional Hamilton-Jacobi-Bellman (HJB) equations with JAX.

This repository also ships a Codex skill, `finhjb-model-coder`, for turning continuous-time finance models, LaTeX notes, and paper excerpts into executable one-dimensional FinHJB code.

## Install

```bash
uv add finhjb
```

```bash
pip install finhjb
```

Installation defaults to CPU. If you want GPU support, install the appropriate JAX backend separately.

## Choose Your Path

### 1. Use FinHJB as a Python library

Use this path if you already know the model you want to implement and want to work directly with the package API.

Start here:

- [Installation and Environment](./docs/en/installation-and-environment.md)
- [Library Quickstart](./docs/en/quickstart-library.md)
- [Modeling Guide](./docs/en/modeling-guide.md)
- [Solver Guide](./docs/en/solver-guide.md)
- [API Reference](./docs/en/api-reference.md)

### 2. Learn FinHJB through the BCW examples

Use this path if you want to understand the package by reproducing and adapting the repository's BCW examples.

Start here:

- [Getting Started](./docs/en/getting-started.md)
- [BCW2011 Case Study](./docs/en/bcw2011-case-study.md)
- [Adapting BCW to Your Model](./docs/en/adapting-bcw-to-your-model.md)

### 3. Use `finhjb-model-coder`

Use this path if you want Codex to read equations, paper notes, or LaTeX and turn them into FinHJB code.

Before asking for runnable code, confirm that the target Python environment can actually run `finhjb`.

Start here:

- [FinHJB Model Coder](./docs/en/finhjb-model-coder.md)
- [Model Coder Overview](./docs/en/finhjb-model-coder-overview.md)
- [Inputs and Readiness](./docs/en/finhjb-model-coder-inputs-and-readiness.md)
- [Output and Validation](./docs/en/finhjb-model-coder-output-and-validation.md)

The `finhjb-model-coder` workflow expects Codex to:

- decide whether the model fits the current one-dimensional FinHJB interface
- confirm that the target Python environment can actually run `finhjb`
- confirm the derivative scheme and boundary-search method before code generation
- stop and confirm baseline calibration values when symbols are defined but usable numbers are not
- split the deliverable into solve, data, and plotting files when the task combines sensitivity analysis with plotting
- stop and confirm the missing derivation steps when the mathematics does not yet map directly into FinHJB code
- generate code, run a post-generation test loop, and repair failures before delivery

## Repository Notes

- The published `finhjb` package is the right choice for downstream projects.
- The BCW example scripts in `src/example/` are repository files. They are not included in the published wheel.
- The `finhjb-model-coder` skill also lives in the repository, not in the published wheel.

Install the skill from a repository checkout with:

```bash
python scripts/install_skill.py
```

Useful variants:

```bash
python scripts/install_skill.py --dry-run
python scripts/install_skill.py --dest ~/.codex/skills --force
python scripts/install_skill.py --mode link --force
```

## Documentation Map

- [Docs Portal](./docs/en/index.md)
- [Installation and Environment](./docs/en/installation-and-environment.md)
- [Getting Started](./docs/en/getting-started.md)
- [FinHJB Model Coder](./docs/en/finhjb-model-coder.md)
- [BCW2011 Case Study](./docs/en/bcw2011-case-study.md)
- [Adapting BCW to Your Model](./docs/en/adapting-bcw-to-your-model.md)
