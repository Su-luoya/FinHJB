# FinHJB Documentation (English)

FinHJB is easiest to learn if you treat the documentation as a guided research workflow:

1. get the environment working,
2. reproduce the BCW baseline examples,
3. learn how to read the solver outputs, and
4. then adapt the BCW structure to your own model.

If you want to use `finhjb-model-coder`, keep the same order: first confirm a runnable FinHJB environment, then let the skill lock the derivative scheme and boundary-search method, and only then trust the tested code it generates.

```{toctree}
:maxdepth: 1
:caption: Start Here

installation-and-environment
getting-started
troubleshooting
```

```{toctree}
:maxdepth: 1
:caption: BCW Walkthrough

bcw2011-case-study
bcw2011-liquidation-walkthrough
bcw2011-hedging-walkthrough
results-and-diagnostics
```

```{toctree}
:maxdepth: 1
:caption: Adapt Your Model

modeling-guide
adapting-bcw-to-your-model
solver-guide
```

```{toctree}
:maxdepth: 1
:caption: Codex Skill

finhjb-model-coder
```

```{toctree}
:maxdepth: 1
:caption: Reference

api-reference
faq
```

```{toctree}
:hidden:

../zh/index
```
