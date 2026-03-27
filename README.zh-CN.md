# FinHJB

[English README](./README.md) | [📖 文档](https://su-luoya.github.io/FinHJB/zh/) | [📖 English Docs](https://su-luoya.github.io/FinHJB/)

FinHJB 是一个基于 JAX 的一维 Hamilton-Jacobi-Bellman (HJB) 方程求解库。

这个仓库同时提供一个 Codex Skill, `finhjb-model-coder`，用于把连续时间金融模型、LaTeX 推导和论文片段转成可执行的一维 FinHJB 代码。

## 主要特性

- **策略迭代求解**: 支持使用策略迭代求解 HJB 方程，可选 Anderson 加速
- **边界方法**: 边界更新和边界搜索，以获取最优边界条件
- **敏感性分析**: 参数延拓，分析参数变化对解的影响
- **灵活的导数方法**: 支持中心差分、向前差分和向后差分
- **GPU 支持**: 基于 JAX 构建，可无缝使用 CPU/GPU，并支持自动微分
- **类型安全**: 完整的类型注解，参数和策略类提供鲁棒的模型构建
- **结果保存与加载**: 支持保存和加载解、网格和敏感性分析结果
- **`finhjb-model-coder` Skill**: 把理论模型、HJB、FOC 和边界条件转成 FinHJB 模型文件，并附带验证建议

## 安装

使用 `uv` 安装：

```bash
uv add finhjb
```

或使用 `pip`：

```bash
pip install finhjb
```

**注意**: 默认安装为 CPU 版本。如需 GPU 支持，请单独安装相应 CUDA/Metal 后端的 JAX。

如果你的目标是在自己的项目里直接使用发布到 PyPI 的 `finhjb` 包，那么 `uv add` 或 `pip install` 就是正确路径。

如果你的目标是逐行复现 BCW 教程脚本，请使用仓库源码。`src/example/BCW2011Liquidation.py` 和 `src/example/BCW2011Hedging.py` 这些示例脚本并不包含在发布到 PyPI 的 wheel 中。

`finhjb-model-coder` 这个 Skill 也只存在于仓库里，不包含在 PyPI wheel 中。

## FinHJB 的两种使用方式

### 1. 直接使用 Python 包

当你已经清楚自己要写什么模型，并且打算亲自维护实现代码时，直接使用 `finhjb` 包最合适。

### 2. 使用 `finhjb-model-coder` Skill

当你希望 Codex 帮你做这些事时，使用这个 Skill：

- 读取连续时间金融模型的文字说明、LaTeX 或论文摘录
- 判断模型是否能够映射到当前一维 FinHJB 接口
- 先确认目标 Python 环境是否真的能运行 `finhjb`
- 在生成前确认有限差分格式和边界搜索方法
- 主动追问会影响代码生成的关键细节，例如边界、控制变量和校准参数
- 如果文档里只有参数符号没有具体数值，先停下来和你确认 baseline calibration
- 如果用户要求画图但没有说清楚具体画什么，先停下来确认图形需求
- 生成可运行的 FinHJB 模型文件，并在交付前先测试、修复，再返回结构化规格摘要和验证建议

最推荐你提供的材料包括：

- 研究问题与唯一的状态变量
- HJB 方程
- 控制变量及其 FOC 或显式策略规则
- 边界条件、value matching 或 smooth pasting 条件
- 参数定义与基准校准值

在它把代码当成“可运行交付物”之前，这个 Skill 现在还会默认确认：

- 你已经有一个可运行的 FinHJB 环境，来源可以是当前仓库源码环境，也可以是已安装好的 `finhjb` 包
- 如果边界附近扩散项会退化，差分格式已经明确
- 如果模型有内生边界，边界搜索方法已经明确

如果环境缺失，Skill 应该先停下来辅助安装，并要求一个最小 smoke test，例如 `python -c "import finhjb"` 或 `uv run python -c "import finhjb"`。

从仓库源码安装这个 Skill：

```bash
python scripts/install_skill.py
```

预览安装路径，或覆盖已存在的安装：

```bash
python scripts/install_skill.py --dry-run
python scripts/install_skill.py --dest ~/.codex/skills --force
```

如果你希望开发时保持仓库与已安装 Skill 同步，可以使用符号链接模式：

```bash
python scripts/install_skill.py --mode link --force
```

如果你更喜欢手动安装，把 `skills/finhjb-model-coder` 复制到 `${CODEX_HOME:-$HOME/.codex}/skills/` 即可。

这个 Skill 自己也依赖一个已经准备好的运行环境：

- 对仓库示例、BCW 复现和 skill 测试，优先使用仓库自己的 `uv` 环境
- 对下游项目，使用 `uv add finhjb` 或 `pip install finhjb`
- 代码生成后，Skill 默认还会跑一次 solve-loop 检查，再把产物当成正式交付

## 文档入口

如果你是从已发布的包开始使用，建议先看仓库中的这些文档入口：

- [总览](./docs/zh/index.md)
- [安装与环境](./docs/zh/installation-and-environment.md)
- [建模指南](./docs/zh/modeling-guide.md)
- [求解器指南](./docs/zh/solver-guide.md)
- [API 参考](./docs/zh/api-reference.md)

如果你想使用“理论到代码”的 Skill 工作流，请先看：

- [FinHJB Model Coder Skill](./docs/zh/finhjb-model-coder.md)

如果你正在使用仓库源码并想复现 BCW 示例，请从这里开始：

- [快速开始](./docs/zh/getting-started.md)
- [BCW2011 案例总览](./docs/zh/bcw2011-case-study.md)
- [把 BCW 改成你自己的模型](./docs/zh/adapting-bcw-to-your-model.md)
