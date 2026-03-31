# FinHJB

[简体中文 README](./README.zh-CN.md) | [Documentation](https://su-luoya.github.io/FinHJB/) | [中文文档](https://su-luoya.github.io/FinHJB/zh/)

FinHJB is a JAX-based Python library for solving one-dimensional Hamilton-Jacobi-Bellman (HJB) equations. The repository also contains four BCW benchmark cases and a repository-only Codex skill, `finhjb-model-coder`, for turning continuous-time finance models, LaTeX notes, and paper excerpts into runnable FinHJB code.

## Install

```bash
uv add finhjb
```

```bash
pip install finhjb
```

Installation defaults to CPU. If you want GPU support, install the appropriate JAX backend separately.

## What Lives In This Repository

- the published `finhjb` package interface in [`src/finhjb`](./src/finhjb/)
- four BCW benchmark scripts in [`src/example`](./src/example/)
- the repository-only skill [`finhjb-model-coder`](./skills/finhjb-model-coder/SKILL.md)
- bilingual documentation in [`docs/en`](./docs/en/index.md) and [`docs/zh`](./docs/zh/index.md)

The repository supports three practical workflows.

### 1. Direct package use

If the model is already specified and you want to work straight from the API, start with:

- [Installation and Environment](./docs/en/installation-and-environment.md)
- [Library Quickstart](./docs/en/quickstart-library.md)
- [Modeling Guide](./docs/en/modeling-guide.md)
- [Solver Guide](./docs/en/solver-guide.md)
- [Results and Diagnostics](./docs/en/results-and-diagnostics.md)
- [API Reference](./docs/en/api-reference.md)

### 2. BCW reproduction and adaptation

If you want a paper-aligned benchmark before changing the economics, work from the repository checkout and run the examples from the repository root. The baseline entry point is:

```bash
uv run python src/example/BCW2011Liquidation.py
```

Read in this order:

- [Getting Started](./docs/en/getting-started.md)
- [BCW2011 Case Study](./docs/en/bcw2011-case-study.md)
- [BCW2011 Liquidation Walkthrough](./docs/en/bcw2011-liquidation-walkthrough.md)
- [BCW2011 Refinancing Walkthrough](./docs/en/bcw2011-refinancing-walkthrough.md)
- [BCW2011 Hedging Walkthrough](./docs/en/bcw2011-hedging-walkthrough.md)
- [BCW2011 Credit Line Walkthrough](./docs/en/bcw2011-credit-line-walkthrough.md)
- [Adapting BCW to Your Model](./docs/en/adapting-bcw-to-your-model.md)

### 3. Theory to code with `finhjb-model-coder`

If Codex is reading equations rather than existing Python code, confirm that the target Python environment can actually run `finhjb` before asking for runnable delivery.

Start with:

- [FinHJB Model Coder](./docs/en/finhjb-model-coder.md)
- [Model Coder Overview](./docs/en/finhjb-model-coder-overview.md)
- [Inputs and Readiness](./docs/en/finhjb-model-coder-inputs-and-readiness.md)
- [Output and Validation](./docs/en/finhjb-model-coder-output-and-validation.md)

The `finhjb-model-coder` workflow expects Codex to:

- decide whether the model fits the current one-dimensional FinHJB interface
- confirm that the target Python environment can actually run `finhjb`
- choose the derivative scheme and boundary-search method explicitly
- stop when calibration values, derivations, or plotting requirements are still missing
- split the deliverable into solve, data, and plotting files when sensitivity analysis and figures are both requested
- generate code, run a post-generation test loop, and repair failures before delivery

## Repository Notes

- The published `finhjb` package is the right choice for downstream projects.
- The BCW example scripts in `src/example/` are repository files. They are not included in the published wheel.
- The repository BCW path now includes Case I liquidation, Case II refinancing, Case IV hedging, and Case V credit line examples.
- The BCW scripts are maintained for repository-root execution with imports from `src.example...`.
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

- [Docs Portal](./docs/index.md)
- [Installation and Environment](./docs/en/installation-and-environment.md)
- [Getting Started](./docs/en/getting-started.md)
- [FinHJB Model Coder](./docs/en/finhjb-model-coder.md)
- [BCW2011 Case Study](./docs/en/bcw2011-case-study.md)
- [Adapting BCW to Your Model](./docs/en/adapting-bcw-to-your-model.md)
