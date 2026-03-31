# FinHJB

[English README](./README.md) | [📖 文档](https://su-luoya.github.io/FinHJB/zh/) | [📖 English Docs](https://su-luoya.github.io/FinHJB/)

FinHJB 是一个基于 JAX 的一维 Hamilton-Jacobi-Bellman (HJB) 方程求解库。这个仓库同时维护四个 BCW benchmark 示例，以及一个仓库专用的 Codex Skill `finhjb-model-coder`，用于把连续时间金融模型、LaTeX 推导和论文片段转成可运行的 FinHJB 代码。

## 安装

```bash
uv add finhjb
```

```bash
pip install finhjb
```

默认安装为 CPU 版本。如需 GPU 支持，请另外安装对应的 JAX 后端。

## 仓库里有什么

- 发布版 `finhjb` 包接口，位于 [`src/finhjb`](./src/finhjb/)
- 四个 BCW benchmark 脚本，位于 [`src/example`](./src/example/)
- 仓库专用 Skill [`finhjb-model-coder`](./skills/finhjb-model-coder/SKILL.md)
- 双语文档 [`docs/en`](./docs/en/index.md) 与 [`docs/zh`](./docs/zh/index.md)

这个仓库主要服务三类工作流。

### 1. 直接使用 package

如果模型设定已经清楚，只需要对象结构、求解流程和结果诊断，优先看：

- [安装与环境](./docs/zh/installation-and-environment.md)
- [库快速上手](./docs/zh/quickstart-library.md)
- [建模指南](./docs/zh/modeling-guide.md)
- [求解器指南](./docs/zh/solver-guide.md)
- [结果与诊断](./docs/zh/results-and-diagnostics.md)
- [API 参考](./docs/zh/api-reference.md)

### 2. 通过 BCW 复现再迁移

如果你想先拿一套和论文图对应的 benchmark，再逐步改成自己的模型，应该在仓库根目录运行示例。最基础的入口是：

```bash
uv run python src/example/BCW2011Liquidation.py
```

建议阅读顺序：

- [快速开始](./docs/zh/getting-started.md)
- [BCW2011 案例总览](./docs/zh/bcw2011-case-study.md)
- [BCW2011 Liquidation 逐步讲解](./docs/zh/bcw2011-liquidation-walkthrough.md)
- [BCW2011 Refinancing 逐步讲解](./docs/zh/bcw2011-refinancing-walkthrough.md)
- [BCW2011 Hedging 逐步讲解](./docs/zh/bcw2011-hedging-walkthrough.md)
- [BCW2011 Credit Line 逐步讲解](./docs/zh/bcw2011-credit-line-walkthrough.md)
- [把 BCW 改成你自己的模型](./docs/zh/adapting-bcw-to-your-model.md)

### 3. 用 `finhjb-model-coder` 做 theory-to-code

如果 Codex 读的是方程、LaTeX 或论文摘录，而不是现成 Python 代码，那么在要求生成“可运行代码”之前，先确认目标 Python 环境是否真的能运行 `finhjb`。

从这里开始：

- [FinHJB Model Coder](./docs/zh/finhjb-model-coder.md)
- [Model Coder 总览](./docs/zh/finhjb-model-coder-overview.md)
- [输入材料与环境就绪](./docs/zh/finhjb-model-coder-inputs-and-readiness.md)
- [输出与验证](./docs/zh/finhjb-model-coder-output-and-validation.md)

`finhjb-model-coder` 这条路径默认要求 Codex：

- 判断模型是否适合当前一维 FinHJB 接口
- 先确认目标 Python 环境是否真的能运行 `finhjb`
- 明确给出差分格式和边界搜索方法
- 当校准值、推导步骤或作图要求缺失时先停下来确认
- 当任务同时包含敏感性分析和图时，把交付拆成求解、数据和绘图文件
- 生成代码后运行 post-generation test loop，再修复失败项并交付

## 仓库说明

- 发布到 PyPI 的 `finhjb` 包适合下游项目直接依赖。
- `src/example/` 里的 BCW 示例脚本是仓库文件，不包含在发布版 wheel 中。
- 仓库内 BCW 路径现在覆盖了 Case I liquidation、Case II refinancing、Case IV hedging 和 Case V credit line。
- BCW 脚本按“仓库根目录运行 + `src.example...` 绝对导入”的约定维护。
- `finhjb-model-coder` 这个 Skill 也只存在于仓库里，不包含在发布版 wheel 中。

从仓库源码安装这个 Skill：

```bash
python scripts/install_skill.py
```

常用变体：

```bash
python scripts/install_skill.py --dry-run
python scripts/install_skill.py --dest ~/.codex/skills --force
python scripts/install_skill.py --mode link --force
```

## 文档入口

- [文档首页](./docs/index.md)
- [安装与环境](./docs/zh/installation-and-environment.md)
- [快速开始](./docs/zh/getting-started.md)
- [FinHJB Model Coder](./docs/zh/finhjb-model-coder.md)
- [BCW2011 案例总览](./docs/zh/bcw2011-case-study.md)
- [把 BCW 改成你自己的模型](./docs/zh/adapting-bcw-to-your-model.md)
