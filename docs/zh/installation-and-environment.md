# 安装与环境

第一次运行 FinHJB 之前，请先读这一页。

这一页关心的不是“包能不能装上”这么简单，而是“你是否已经进入了一个之后可以稳定复现 BCW、再迁移到自己模型的工作环境”。

## 目标

读完这一页后，你应该能做到：

- 创建一个可用的本地环境；
- 在仓库工作树里成功导入 `finhjb`；
- 避开最常见的 JAX 和 Matplotlib 环境问题；
- 在进入 BCW 教程前先做一轮最小化环境验证。

如果你已经确定环境没问题，可以直接去 [快速开始](./getting-started.md)。如果安装失败，请配合 [排障](./troubleshooting.md) 一起看。

## 推荐基线

当前最稳妥的使用方式如下：

| 项目 | 推荐值 |
|---|---|
| Python | `>=3.10` |
| 环境管理 | `uv` |
| 首次运行后端 | CPU |
| 远程/无图形环境绘图 | `MPLBACKEND=Agg` |
| 本地文档构建 | `uv sync --group docs` |

第一次成功运行时，不建议一开始就为 GPU、notebook 或自定义绘图后端做太多额外配置。先确保最简单的 CPU 环境能稳定工作。

## 第一步：克隆仓库

```bash
git clone https://github.com/Su-luoya/FinHJB.git
cd FinHJB
```

后续所有命令都建议在仓库根目录执行。

## 第二步：安装依赖

### 推荐方式：`uv`

```bash
uv sync
```

如果你还想在本地构建 Sphinx 文档站，再执行：

```bash
uv sync --group docs
```

### 备用方式：editable `pip`

```bash
pip install -e .
```

不过项目文档和 CI 默认都使用 `uv`，如果后续环境行为和文档不一致，优先回到 `uv sync` 路线。

## 第三步：验证 Python 环境

先做一个非常小的导入测试，再去跑完整求解：

```bash
uv run python -c "import finhjb as fjb; print('exports:', len(fjb.__all__), 'first:', fjb.__all__[:5])"
```

你应该能看到类似 `Config`、`AbstractBoundary`、`Solver` 这样的导出名。

然后验证示例模块是否可导入：

```bash
uv run python -c "from src.example.BCW2011Liquidation import Parameter; print(Parameter())"
uv run python -c "from src.example.BCW2011Hedging import Parameter; print(Parameter())"
```

如果这里都过不了，就先不要往 walkthrough 页走，说明环境层还没完成。

## 第四步：根据运行环境配置绘图后端

BCW 示例脚本会导入 Matplotlib。在本地图形桌面环境下，这通常没问题；但在服务器、CI、远程 shell 里，经常需要先设置：

```bash
export MPLBACKEND=Agg
```

然后再执行示例：

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011Liquidation.py
```

这只改变绘图后端，不改变模型、方程和数值结果。

### Windows 说明

如果你不在 POSIX shell 中，环境变量写法会不同。真正关键的是：在脚本导入 `matplotlib.pyplot` 之前，让 Matplotlib 使用 `Agg` 后端。

## 第五步：做一个最小 sanity check

在正式求解 BCW 之前，先用一个很小的脚本确认包和配置类都能正常工作：

```bash
uv run python - <<'PY'
import finhjb as fjb
print("versioned exports:", fjb.__all__)
print("Config example:", fjb.Config())
PY
```

这一步非常值得保留，因为它能帮你区分：

- 现在的问题是“环境没好”，
- 还是“模型/数值逻辑有问题”。

## 第六步：两个很有用的附加检查

### 本地构建文档站

```bash
uv run sphinx-build -b dirhtml docs build/sphinx/dirhtml -c .sphinx -W --keep-going
```

这会同时验证：

- docs 依赖组是否安装完整，
- MyST + autodoc 能否工作，
- 文档构建上下文中的导入是否正常。

### 运行文档契约测试

```bash
uv run pytest -q tests/test_doc_and_api_contracts.py
```

这个测试会检查双语页面集合、README 入口链接以及文档/API 的若干基本约束。

## 平台差异提示

### macOS

通常最顺手的流程就是：

```bash
uv sync
uv run python -c "import finhjb"
```

如果你是 Apple Silicon，第一次成功运行前不要急着改 JAX 后端和设备设置。

### Linux / 远程服务器

最常见的失败并不是 JAX，而是 Matplotlib 后端。因此优先设置：

```bash
export MPLBACKEND=Agg
```

并先在非交互环境中完成第一次求解。

### Windows

项目本身是 Python 写的，但文档里的很多命令使用了类 Unix shell 语法。如果环境变量或 heredoc 语法不方便，可以在 PowerShell 中写等价命令，或者使用 WSL。

## 什么叫“安装成功”

一个真正健康的环境，至少应满足：

1. `uv run python -c "import finhjb"` 成功；
2. `uv run python -c "from src.example.BCW2011Liquidation import Parameter"` 成功；
3. 安装 docs 依赖后，`uv run sphinx-build ...` 成功；
4. 你能运行 BCW liquidation 脚本而不出现导入或绘图后端错误。

仅仅“能导入包”还不够，如果示例脚本跑不通，环境仍然没有完全准备好。

## 常见安装失败模式

| 现象 | 最常见原因 | 第一修复动作 |
|---|---|---|
| `ModuleNotFoundError: No module named 'finhjb'` | 用了系统 Python，而不是项目环境 | 统一改用 `uv run ...` |
| `ModuleNotFoundError: No module named 'jax'` | 当前环境里没装齐依赖 | 重新执行 `uv sync` |
| Matplotlib GUI / display 报错 | 远程或无图形环境 | 先设 `MPLBACKEND=Agg` |
| Sphinx 构建时报缺包 | docs 依赖没装 | 运行 `uv sync --group docs` |
| 示例模块导入失败 | 当前目录不在仓库根目录 | `cd` 到仓库根目录后重试 |

## 安装成功后，下一页该看什么

一旦环境通过验证，就直接进入 [快速开始](./getting-started.md)。

那一页解决的是下一层问题：

“我现在能不能把 BCW 跑出来，而且知道结果是不是正常？”

