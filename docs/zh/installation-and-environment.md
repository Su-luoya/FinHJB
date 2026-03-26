# 安装与环境

第一次运行 FinHJB 之前，请先读这一页。

这一页故意保持极简。如果你只是想使用已经发布的包，那么安装命令只需要二选一：

```bash
uv add finhjb
```

```bash
pip install finhjb
```

默认安装是 CPU 版本。如果你需要 GPU 支持，请另外安装对应的 JAX 后端。

## 这些命令会安装什么

上面的命令安装的是发布到 PyPI 的 `finhjb` 包，适合你在自己的项目里直接使用。

它们不会安装仓库源码树，所以像下面这些文件：

- `src/example/BCW2011Liquidation.py`
- `src/example/BCW2011Hedging.py`

并不包含在 PyPI wheel 里。

## 如果你打算使用 `finhjb-model-coder`

这个 Skill 的安装与 Python 包安装是两件事，而且 Skill 默认假设对话背后有一个真的可以运行 FinHJB 的环境。

建议按这个清单确认：

- 如果任务依赖仓库内的示例或测试夹具，请使用仓库源码 checkout，并优先用仓库自己的 `uv` 环境
- 如果任务是你自己项目里的模型，请把发布版 `finhjb` 安装到那个项目里，可以用 `uv add finhjb` 或 `pip install finhjb`
- 在要求 Skill 生成“可运行代码”之前，先确认一个 smoke test，例如 `python -c "import finhjb"` 或 `uv run python -c "import finhjb"`

如果这个 smoke test 失败，Skill 应该先帮助安装，而不是假装最终代码已经经过测试。

## 下一步看什么

- 如果你想直接使用包 API，接下来读 [建模指南](./modeling-guide.md)、[求解器指南](./solver-guide.md) 和 [API 参考](./api-reference.md)。
- 如果你想用“理论到代码”的工作流，请在环境确认好之后继续读 [FinHJB Model Coder Skill](./finhjb-model-coder.md)。
- 如果你想学习仓库里的 BCW 示例，请在源码 checkout 环境下阅读 walkthrough 页面，并从 [快速开始](./getting-started.md) 开始。
