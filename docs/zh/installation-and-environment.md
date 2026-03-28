# 安装与环境

这一页服务三条文档路径的共同前置问题：你的目标工作流到底需要安装什么。

## 先选安装模式

### 发布版 Python 包

如果你在自己的项目里使用 FinHJB，而且不依赖仓库里的示例脚本，这就是正确路径。

```bash
uv add finhjb
```

```bash
pip install finhjb
```

默认安装为 CPU 版本。如需 GPU 支持，请另外安装对应的 JAX 后端。

### 仓库源码 checkout

如果你要做下面这些事，就应该使用仓库源码：

- 运行 `src/example/BCW2011Liquidation.py`
- 运行 `src/example/BCW2011Hedging.py`
- 阅读或修改源码
- 从当前仓库安装并开发 `finhjb-model-coder` skill

在仓库根目录执行：

```bash
uv sync
uv run python -c "import finhjb as fjb; print(fjb.__all__[:5])"
```

如果你在服务器或没有图形界面的环境里运行，再加上：

```bash
export MPLBACKEND=Agg
```

## 发布版包不会带上什么

发布到 PyPI 的 wheel 不包含这些仓库内文件：

- `src/example/BCW2011Liquidation.py`
- `src/example/BCW2011Hedging.py`
- `skills/finhjb-model-coder/`

如果你的任务依赖这些文件，就不要只装发布版包。

## 如果你打算使用 `finhjb-model-coder`

Skill 和 Python 包是两件不同的东西。

在要求 Codex 交付“可运行代码”之前，先按下面的清单确认：

- 如果任务依赖仓库示例或测试夹具，优先使用仓库源码和仓库自己的 `uv` 环境
- 如果任务属于你自己的下游项目，请在那个项目里安装 `finhjb`，用 `uv add finhjb` 或 `pip install finhjb`
- 在正式交付前，先跑一个 smoke test，例如 `python -c "import finhjb"` 或 `uv run python -c "import finhjb"`

如果 smoke test 失败，正确的下一步是先解决环境，而不是继续生成代码。

## 下一步看什么

- Package 路径：[库快速上手](./quickstart-library.md)
- BCW 路径：[快速开始](./getting-started.md)
- Model Coder 路径：[FinHJB Model Coder](./finhjb-model-coder.md) 或 [输入材料与环境就绪](./finhjb-model-coder-inputs-and-readiness.md)
