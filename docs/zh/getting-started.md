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
