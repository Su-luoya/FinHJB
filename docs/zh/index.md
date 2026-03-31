# FinHJB 手册

FinHJB 是一个基于 JAX 的一维 HJB 求解库。这套手册面向两类读者：一类已经有模型、需要尽快把方程落到代码；另一类希望先借助一套完整 benchmark，把经济对象、代码对象和数值诊断对应起来。

阅读方式大致分成三条：

- 如果模型已经写清楚，直接走 package 路径；
- 如果想先拿一篇论文 benchmark 当模板，走 BCW 路径；
- 如果手里还是论文、LaTeX 或研究笔记，而不是 Python 代码，走 `finhjb-model-coder` 路径。

如果环境还不能稳定运行，请先看 [安装与环境](./installation-and-environment.md)。BCW 示例和 `finhjb-model-coder` 都属于仓库材料，不包含在发布版 wheel 中。

## 起点怎么选

### 直接使用 Package

当你已经知道模型设定，只需要对象结构、求解流程和结果诊断时，优先走这条路。

- [安装与环境](./installation-and-environment.md)
- [库快速上手](./quickstart-library.md)
- [建模指南](./modeling-guide.md)
- [求解器指南](./solver-guide.md)
- [结果与诊断](./results-and-diagnostics.md)

### 通过 BCW 复现与迁移

当你需要一套带内生边界、能和论文图对应的工作 benchmark，再逐步改成自己的模型时，优先走这条路。

- [快速开始](./getting-started.md)
- [BCW2011 案例总览](./bcw2011-case-study.md)
- [BCW2011 Liquidation 逐步讲解](./bcw2011-liquidation-walkthrough.md)
- [BCW2011 Refinancing 逐步讲解](./bcw2011-refinancing-walkthrough.md)
- [BCW2011 Hedging 逐步讲解](./bcw2011-hedging-walkthrough.md)
- [BCW2011 Credit Line 逐步讲解](./bcw2011-credit-line-walkthrough.md)
- [把 BCW 改成你自己的模型](./adapting-bcw-to-your-model.md)

### 用 `finhjb-model-coder` 做 Theory-to-Code

当输入仍然是 HJB、FOC、LaTeX 或论文摘录，而不是已有实现时，走这条路。第一个实际问题始终是：目标 Python 环境能不能真的运行 `finhjb`。

- [FinHJB Model Coder](./finhjb-model-coder.md)
- [Model Coder 总览](./finhjb-model-coder-overview.md)
- [输入材料与环境就绪](./finhjb-model-coder-inputs-and-readiness.md)
- [输出与验证](./finhjb-model-coder-output-and-validation.md)

```{toctree}
:maxdepth: 1
:caption: 共享起点

installation-and-environment
```

```{toctree}
:maxdepth: 1
:caption: BCW 复现与迁移

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
:caption: 直接使用 Package

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
:caption: 参考

api-reference
troubleshooting
faq
```
