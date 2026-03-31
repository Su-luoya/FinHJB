# FinHJB Manual

FinHJB is a JAX-based library for one-dimensional HJB problems. This manual is written for readers who want to move between three objects without losing track of the economics: equations, code, and numerical diagnostics.

Use the site in one of three ways:

- start from the package API if your model is already specified and you want a direct implementation path;
- start from BCW if you want a worked benchmark before adapting the structure to your own problem;
- start from `finhjb-model-coder` if your input is still a paper, LaTeX, or research note rather than Python code.

If the environment is not yet runnable, begin with [Installation and Environment](./installation-and-environment.md). The BCW examples and `finhjb-model-coder` are repository materials rather than part of the published wheel.

## Starting Points

### Direct Package Use

Choose this path when you already know the model you want to solve and mainly need the FinHJB object model, solver workflow, and result inspection.

- [Installation and Environment](./installation-and-environment.md)
- [Library Quickstart](./quickstart-library.md)
- [Modeling Guide](./modeling-guide.md)
- [Solver Guide](./solver-guide.md)
- [Results and Diagnostics](./results-and-diagnostics.md)

### BCW Reproduction And Adaptation

Choose this path when you want a paper-aligned benchmark with endogenous boundaries before changing the economics.

- [Getting Started](./getting-started.md)
- [BCW2011 Case Study](./bcw2011-case-study.md)
- [BCW2011 Liquidation Walkthrough](./bcw2011-liquidation-walkthrough.md)
- [BCW2011 Refinancing Walkthrough](./bcw2011-refinancing-walkthrough.md)
- [BCW2011 Hedging Walkthrough](./bcw2011-hedging-walkthrough.md)
- [BCW2011 Credit Line Walkthrough](./bcw2011-credit-line-walkthrough.md)
- [Adapting BCW To Your Model](./adapting-bcw-to-your-model.md)

### Theory To Code With `finhjb-model-coder`

Choose this path when the input is an HJB, a set of FOCs, or notes from a paper draft. The first operational question is always whether the target Python environment can actually run `finhjb`.

- [FinHJB Model Coder](./finhjb-model-coder.md)
- [Model Coder Overview](./finhjb-model-coder-overview.md)
- [Inputs and Readiness](./finhjb-model-coder-inputs-and-readiness.md)
- [Output and Validation](./finhjb-model-coder-output-and-validation.md)

```{toctree}
:maxdepth: 1
:caption: Shared Setup

installation-and-environment
```

```{toctree}
:maxdepth: 1
:caption: BCW Reproduction And Adaptation

getting-started
bcw2011-case-study
bcw2011-liquidation-walkthrough
bcw2011-refinancing-walkthrough
bcw2011-hedging-walkthrough
bcw2011-credit-line-walkthrough
adapting-bcw-to-your-model
```

```{toctree}
:maxdepth: 1
:caption: Direct Package Use

quickstart-library
modeling-guide
solver-guide
results-and-diagnostics
```

```{toctree}
:maxdepth: 1
:caption: Model Coder

finhjb-model-coder
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
