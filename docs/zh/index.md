# FinHJB 文档（中文）

最推荐的学习顺序不是“先把所有 API 都看完”，而是把文档当成一条研究工作流来走：

1. 先把环境搭好，
2. 再稳定复现 BCW 基准案例，
3. 学会判断结果是不是合理，
4. 最后再把 BCW 模板改造成你自己的模型。

如果你打算使用 `finhjb-model-coder`，顺序也一样：先确认可运行环境，再让 Skill 锁定差分格式和边界搜索方法，最后再接收它测试过的代码产物。

```{toctree}
:maxdepth: 1
:caption: 起步

installation-and-environment
getting-started
troubleshooting
```

```{toctree}
:maxdepth: 1
:caption: BCW 逐步教程

bcw2011-case-study
bcw2011-liquidation-walkthrough
bcw2011-hedging-walkthrough
results-and-diagnostics
```

```{toctree}
:maxdepth: 1
:caption: 改成你自己的模型

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
:caption: 参考

api-reference
faq
```
