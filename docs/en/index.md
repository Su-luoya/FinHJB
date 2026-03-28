# FinHJB Documentation (English)

This documentation serves three equal workflows:

- use FinHJB directly as a Python library
- learn the package through the BCW examples in this repository
- use `finhjb-model-coder` to translate theory into code

If you do not yet have a runnable FinHJB environment, start with [Installation and Environment](./installation-and-environment.md).

## Choose Your Path

### Use FinHJB as a Library

This path is for readers who already know the economics they want to implement and want the shortest path to the package API.

Start here:

- [Installation and Environment](./installation-and-environment.md)
- [Library Quickstart](./quickstart-library.md)

Then read:

- [Modeling Guide](./modeling-guide.md)
- [Solver Guide](./solver-guide.md)
- [Results and Diagnostics](./results-and-diagnostics.md)
- [API Reference](./api-reference.md)

### Learn Through BCW

This path is for readers who want to understand FinHJB through the repository's worked BCW examples before adapting the framework to a new model.

Start here:

- [Getting Started](./getting-started.md)
- [BCW2011 Case Study](./bcw2011-case-study.md)

Then read:

- [BCW2011 Liquidation Walkthrough](./bcw2011-liquidation-walkthrough.md)
- [BCW2011 Hedging Walkthrough](./bcw2011-hedging-walkthrough.md)
- [Adapting BCW To Your Model](./adapting-bcw-to-your-model.md)

### Use `finhjb-model-coder`

This path is for readers who want Codex to work from equations, paper excerpts, or LaTeX instead of starting from an existing Python file.

Start here:

- [FinHJB Model Coder](./finhjb-model-coder.md)
- [Model Coder Overview](./finhjb-model-coder-overview.md)

Then read:

- [Inputs and Readiness](./finhjb-model-coder-inputs-and-readiness.md)
- [Output and Validation](./finhjb-model-coder-output-and-validation.md)

This path assumes a runnable FinHJB environment and asks Codex to make derivative-scheme, boundary-search, and validation decisions explicit.

### Shared Reference

Use the reference pages when you need exact names, diagnostics, or recovery steps.

- [API Reference](./api-reference.md)
- [Troubleshooting](./troubleshooting.md)
- [FAQ](./faq.md)

```{toctree}
:maxdepth: 1
:caption: Shared Setup

installation-and-environment
```

```{toctree}
:maxdepth: 1
:caption: Package Path

quickstart-library
modeling-guide
solver-guide
results-and-diagnostics
```

```{toctree}
:maxdepth: 1
:caption: BCW Path

bcw2011-case-study
bcw2011-liquidation-walkthrough
bcw2011-hedging-walkthrough
adapting-bcw-to-your-model
```

```{toctree}
:maxdepth: 1
:caption: Model Coder Path

finhjb-model-coder-overview
finhjb-model-coder-inputs-and-readiness
finhjb-model-coder-output-and-validation
```

```{toctree}
:maxdepth: 1
:caption: Reference

api-reference
troubleshooting
faq
```

```{toctree}
:hidden:

getting-started
finhjb-model-coder
../zh/index
```
