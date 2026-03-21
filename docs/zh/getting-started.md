# 快速开始

## 1. 安装

```bash
uv sync
```

## 2. 定义四个核心组件

1. `AbstractParameter`：不可变模型参数。
2. `AbstractBoundary`：状态/价值边界。
3. `AbstractPolicy`：策略初始化与更新。
4. `AbstractModel`：HJB 残差及可选边界方法。

## 3. 构造求解器

```python
solver = fjb.Solver(
    boundary=boundary,
    model=model,
    policy_guess=True,
    number=500,  # 必须 >= 4
    config=fjb.Config(pi_method="scan", derivative_method="central"),
)
```

## 4. 开始求解

```python
state, history = solver.solve()
```

`state.df` 可查看 `s`、`v`、`dv`、`d2v` 与策略变量。

## 5. 保存与加载

```python
state.grid.save("solution_grid")
loaded_grid = fjb.load_grid("solution_grid")
```

三种 `load` 的快速选择：

- `fjb.load_grid(path)`：读取单个 `Grid`（对应 `state.grid.save(path)`）
- `fjb.load_grids(path)`：读取 `Grids` 集合（对应 `result.grids.save(path)`）
- `fjb.load_sensitivity_result(path)`：读取完整敏感性结果（对应 `result.save(path)`）

更详细示例见：[API 参考](./api-reference.md) 的“加载函数详解”。

## 6. 下一步：论文案例复现

如果你想通过完整案例快速掌握“建模-求解-解释结果”的全流程，建议继续阅读：

- [BCW2011 案例教程](./bcw2011-case-study.md)
