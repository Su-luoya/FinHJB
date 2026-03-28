# FinHJB 文档（中文）

这套文档同时服务三条同等重要的路径：

- 直接把 FinHJB 当 Python 包使用
- 通过仓库里的 BCW 示例理解 FinHJB
- 使用 `finhjb-model-coder` 把理论模型翻译成代码

如果你还没有一个可运行环境，请先从 [安装与环境](./installation-and-environment.md) 开始。

## 选择你的路径

### 直接使用 FinHJB 这个库

这条路径适合已经知道自己要实现什么经济模型、希望最短路径进入包 API 的读者。

从这里开始：

- [安装与环境](./installation-and-environment.md)
- [库快速上手](./quickstart-library.md)

然后继续：

- [建模指南](./modeling-guide.md)
- [求解器指南](./solver-guide.md)
- [结果与诊断](./results-and-diagnostics.md)
- [API 参考](./api-reference.md)

### 通过 BCW 学习

这条路径适合想先通过仓库里的 BCW 案例掌握 FinHJB，再改成自己模型的读者。

从这里开始：

- [快速开始](./getting-started.md)
- [BCW2011 案例总览](./bcw2011-case-study.md)

然后继续：

- [BCW2011 Liquidation 逐步讲解](./bcw2011-liquidation-walkthrough.md)
- [BCW2011 Hedging 逐步讲解](./bcw2011-hedging-walkthrough.md)
- [把 BCW 改成你自己的模型](./adapting-bcw-to-your-model.md)

### 使用 `finhjb-model-coder`

这条路径适合希望让 Codex 从方程、论文摘录或 LaTeX 出发，而不是从已有 Python 文件出发的读者。

从这里开始：

- [FinHJB Model Coder](./finhjb-model-coder.md)
- [Model Coder 总览](./finhjb-model-coder-overview.md)

然后继续：

- [输入材料与环境就绪](./finhjb-model-coder-inputs-and-readiness.md)
- [输出与验证](./finhjb-model-coder-output-and-validation.md)

这条路径默认要求背后有一个真的可运行环境，并要求 Codex 把差分格式、边界搜索和验证步骤讲清楚。

### 共享参考区

当你需要精确名字、诊断方法或故障恢复建议时，回到这些页：

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
bcw2011-hedging-walkthrough
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
