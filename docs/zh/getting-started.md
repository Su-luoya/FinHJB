# 快速开始

这一页现在专门表示 BCW 路径下的仓库快速上手。

如果你的问题是“我已经 clone 了仓库，怎么跑 BCW 示例，并判断结果大致正常”，就从这里开始。

如果你要走纯 package 路径，请改读 [库快速上手](./quickstart-library.md)。

## 目标

读完这一页后，你应该能做到：

- 确认仓库环境可用
- 跑通 BCW liquidation 示例
- 跑通 BCW hedging 示例
- 不用逐行研究全部输出，也能抓住主要成功信号

## 第一步：准备仓库环境

在仓库根目录执行：

```bash
uv sync
uv run python -c "import finhjb as fjb; print(fjb.__all__[:5])"
```

如果你在没有图形界面的环境中运行，再加上：

```bash
export MPLBACKEND=Agg
```

## 第二步：运行 BCW Liquidation 示例

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011Liquidation.py
```

按当前仓库配置，健康的运行通常表现为：

- `v_left` 大约在 `0.9`
- 解出的 `s_max` 大约在 `0.22`
- `dv[-1]` 接近 `1`
- `d2v[-1]` 接近 `0`
- 投资在低现金区域很负，在右边界附近转为正值

## 第三步：运行 BCW Hedging 示例

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011Hedging.py
```

按当前仓库配置，健康的运行通常表现为：

- `v_left` 高于纯 liquidation 的值
- 解出的 `s_max` 大约在 `0.14`
- `psi` 落在 `[-5, 0]`
- `d2v[-1]` 依然接近 `0`
- 对冲策略呈现“绑定区 -> 内部区 -> 零对冲区”的三分区结构

## 第四步：带着目的读输出

跑完之后，先看这几个对象：

```python
print(final_state.grid.boundary)
print(final_state.grid.df.head())
print(final_state.grid.df.tail())
print(final_state.grid.d2v[-1])
```

对 BCW 路径来说，这是从“脚本能跑”走到“我知道解了什么”的最短路径。

## 下一步去哪里

- [BCW2011 案例总览](./bcw2011-case-study.md)：完整学习地图
- [BCW2011 Liquidation 逐步讲解](./bcw2011-liquidation-walkthrough.md)：逐段解释代码和方程映射
- [BCW2011 Hedging 逐步讲解](./bcw2011-hedging-walkthrough.md)：第二控制变量和再融资逻辑
- [把 BCW 改成你自己的模型](./adapting-bcw-to-your-model.md)：当基准案例稳定以后再进入
