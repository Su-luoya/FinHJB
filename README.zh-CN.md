# FinHJB

[English README](./README.md) | [📖 文档](https://su-luoya.github.io/FinHJB/zh/) | [📖 English Docs](https://su-luoya.github.io/FinHJB/)

FinHJB 是一个基于 JAX 的一维 Hamilton-Jacobi-Bellman (HJB) 方程求解库。

这个仓库同时提供一个 Codex Skill, `finhjb-model-coder`，用于把连续时间金融模型、LaTeX 推导和论文片段转成可执行的一维 FinHJB 代码。

## 安装

```bash
uv add finhjb
```

```bash
pip install finhjb
```

默认安装为 CPU 版本。如需 GPU 支持，请另外安装对应的 JAX 后端。

## 选择你的路径

### 1. 直接把 FinHJB 当 Python 包使用

如果你已经知道自己要实现什么模型，并且准备直接使用包 API，这条路径最合适。

从这里开始：

- [安装与环境](./docs/zh/installation-and-environment.md)
- [库快速上手](./docs/zh/quickstart-library.md)
- [建模指南](./docs/zh/modeling-guide.md)
- [求解器指南](./docs/zh/solver-guide.md)
- [API 参考](./docs/zh/api-reference.md)

### 2. 通过 BCW 示例学习 FinHJB

如果你希望先复现并理解仓库里的四个 BCW 示例，再改成自己的模型，这条路径最合适。

这条 BCW 路径现在是“公式优先”而不是“结果优先”：

- `快速开始` 负责告诉你怎样运行仓库示例，以及 headline number 大致应落在哪些区间。
- `BCW2011 案例总览` 统一解释齐次性降维和记号映射。
- 四个 walkthrough 才是从 BCW 论文方程走到 `Parameter` / `Boundary` / `PolicyDict` / `Policy` / `Model` 的主桥。
- 正式支持的执行契约是“在仓库根目录运行”，例如 `uv run python src/example/BCW2011Liquidation.py`。

从这里开始：

- [快速开始](./docs/zh/getting-started.md)
- [BCW2011 案例总览](./docs/zh/bcw2011-case-study.md)
- [BCW2011 Liquidation 逐步讲解](./docs/zh/bcw2011-liquidation-walkthrough.md)
- [BCW2011 Refinancing 逐步讲解](./docs/zh/bcw2011-refinancing-walkthrough.md)
- [BCW2011 Hedging 逐步讲解](./docs/zh/bcw2011-hedging-walkthrough.md)
- [BCW2011 Credit Line 逐步讲解](./docs/zh/bcw2011-credit-line-walkthrough.md)
- [把 BCW 改成你自己的模型](./docs/zh/adapting-bcw-to-your-model.md)

### 3. 使用 `finhjb-model-coder`

如果你希望 Codex 直接读取方程、论文笔记或 LaTeX，并把它们转成 FinHJB 代码，这条路径最合适。

在要求生成“可运行代码”之前，先确认目标 Python 环境是否真的能运行 `finhjb`。

从这里开始：

- [FinHJB Model Coder](./docs/zh/finhjb-model-coder.md)
- [Model Coder 总览](./docs/zh/finhjb-model-coder-overview.md)
- [输入材料与环境就绪](./docs/zh/finhjb-model-coder-inputs-and-readiness.md)
- [输出与验证](./docs/zh/finhjb-model-coder-output-and-validation.md)

`finhjb-model-coder` 这条路径默认会要求 Codex：

- 判断模型是否适合当前一维 FinHJB 接口
- 先确认目标 Python 环境是否真的能运行 `finhjb`
- 在代码生成前明确确认差分格式和边界搜索方法
- 如果文档里只有参数符号没有具体数值，先停下来确认 baseline calibration
- 如果任务同时包含敏感性分析和画图，默认拆成求解文件、数据保存文件、绘图文件
- 如果数学表达还不能直接对应到代码、需要先做推导，先停下来确认缺失步骤
- 生成代码后先跑一次 post-generation test loop，再修复失败项并交付

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

- [文档首页](./docs/zh/index.md)
- [安装与环境](./docs/zh/installation-and-environment.md)
- [快速开始](./docs/zh/getting-started.md)
- [FinHJB Model Coder](./docs/zh/finhjb-model-coder.md)
- [BCW2011 案例总览](./docs/zh/bcw2011-case-study.md)
- [把 BCW 改成你自己的模型](./docs/zh/adapting-bcw-to-your-model.md)
