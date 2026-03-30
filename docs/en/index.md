# FinHJB Documentation (English)

This documentation serves three equal workflows:

- use FinHJB directly as a Python library,
- learn the package through the repository BCW examples,
- use `finhjb-model-coder` to translate theory into code.

If you do not yet have a runnable FinHJB environment, start with [Installation and Environment](./installation-and-environment.md).

## Choose Your Path

### Use FinHJB As A Library

Start here:

- [Installation and Environment](./installation-and-environment.md)
- [Library Quickstart](./quickstart-library.md)

Then continue with:

- [Modeling Guide](./modeling-guide.md)
- [Solver Guide](./solver-guide.md)
- [Results and Diagnostics](./results-and-diagnostics.md)
- [API Reference](./api-reference.md)

### Learn Through BCW

Start here:

- [Getting Started](./getting-started.md)
- [BCW2011 Case Study](./bcw2011-case-study.md)

Then continue with:

- [BCW2011 Liquidation Walkthrough](./bcw2011-liquidation-walkthrough.md)
- [BCW2011 Refinancing Walkthrough](./bcw2011-refinancing-walkthrough.md)
- [BCW2011 Hedging Walkthrough](./bcw2011-hedging-walkthrough.md)
- [BCW2011 Credit Line Walkthrough](./bcw2011-credit-line-walkthrough.md)
- [Adapting BCW To Your Model](./adapting-bcw-to-your-model.md)

The BCW path is now organized in two layers:

- `Getting Started` and `Case Study` tell you what to run and how the path is structured,
- the four walkthroughs provide the derivation-level bridge from BCW equations to FinHJB code.

### Use `finhjb-model-coder`

Start here:

- [FinHJB Model Coder](./finhjb-model-coder.md)
- [Model Coder Overview](./finhjb-model-coder-overview.md)
- [Inputs and Readiness](./finhjb-model-coder-inputs-and-readiness.md)
- [Output and Validation](./finhjb-model-coder-output-and-validation.md)

### Shared Reference

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
bcw2011-refinancing-walkthrough
bcw2011-hedging-walkthrough
bcw2011-credit-line-walkthrough
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
