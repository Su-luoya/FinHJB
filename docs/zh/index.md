# FinHJB 文档（中文）

这套文档同时服务三条同等重要的路径：

- 直接把 FinHJB 当 Python 包使用；
- 通过仓库里的 BCW 示例理解 FinHJB；
- 使用 `finhjb-model-coder` 把理论模型翻译成代码。

如果你还没有一个可运行环境，请先从 [安装与环境](./installation-and-environment.md) 开始。

## 选择你的路径

### 直接使用 FinHJB 这个库

从这里开始：

- [安装与环境](./installation-and-environment.md)
- [库快速上手](./quickstart-library.md)

然后继续：

- [建模指南](./modeling-guide.md)
- [求解器指南](./solver-guide.md)
- [结果与诊断](./results-and-diagnostics.md)
- [API 参考](./api-reference.md)

### 通过 BCW 学习

从这里开始：

- [快速开始](./getting-started.md)
- [BCW2011 案例总览](./bcw2011-case-study.md)

然后继续：

- [BCW2011 Liquidation 逐步讲解](./bcw2011-liquidation-walkthrough.md)
- [BCW2011 Refinancing 逐步讲解](./bcw2011-refinancing-walkthrough.md)
- [BCW2011 Hedging 逐步讲解](./bcw2011-hedging-walkthrough.md)
- [BCW2011 Credit Line 逐步讲解](./bcw2011-credit-line-walkthrough.md)
- [把 BCW 改成你自己的模型](./adapting-bcw-to-your-model.md)

BCW 路径现在分成两层：

- `快速开始` 与 `案例总览` 负责告诉你运行路径和整体结构；
- 四个 walkthrough 负责把 BCW 论文方程逐步映射到 FinHJB 代码。

### 使用 `finhjb-model-coder`

从这里开始：

- [FinHJB Model Coder](./finhjb-model-coder.md)
- [Model Coder 总览](./finhjb-model-coder-overview.md)
- [输入材料与环境就绪](./finhjb-model-coder-inputs-and-readiness.md)
- [输出与验证](./finhjb-model-coder-output-and-validation.md)

### 共享参考区

- [API 参考](./api-reference.md)
- [排障](./troubleshooting.md)
- [FAQ](./faq.md)

```{toctree}
:maxdepth: 1
:caption: 共享起点

installation-and-environment
```

```{toctree}
:maxdepth: 1
:caption: Package 路径

quickstart-library
modeling-guide
solver-guide
results-and-diagnostics
```

```{toctree}
:maxdepth: 1
:caption: BCW 路径

bcw2011-case-study
bcw2011-liquidation-walkthrough
bcw2011-refinancing-walkthrough
bcw2011-hedging-walkthrough
bcw2011-credit-line-walkthrough
adapting-bcw-to-your-model
```

```{toctree}
:maxdepth: 1
:caption: Model Coder 路径

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

```{toctree}
:hidden:

getting-started
finhjb-model-coder
```
