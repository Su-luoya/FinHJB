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

## 下一步看什么

- 如果你想直接使用包 API，接下来读 [建模指南](./modeling-guide.md)、[求解器指南](./solver-guide.md) 和 [API 参考](./api-reference.md)。
- 如果你想学习仓库里的 BCW 示例，请在源码 checkout 环境下阅读 walkthrough 页面，并从 [快速开始](./getting-started.md) 开始。
