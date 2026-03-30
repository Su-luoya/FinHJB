# 快速开始

这一页是 BCW 路径下的仓库快速上手。

如果你的问题是“我已经 clone 了仓库，怎么把四个 BCW 示例都跑通，并快速判断结果是否正常”，就从这里开始。

如果你要走纯 package 路径，请改读 [库快速上手](./quickstart-library.md)。

## 目标

读完以后，你应该能做到：

- 确认仓库环境可用；
- 跑通四个 BCW 示例脚本；
- 不需要逐行研究全部输出，也能抓住主要成功信号。

这一页故意只强调“怎么运行”和“怎么看 headline number”。如果你要看公式推导、边界逻辑和 equation-to-code mapping，请从这里继续读四个 BCW walkthrough。

## 第一步：准备仓库环境

在仓库根目录执行：

```bash
uv sync
uv run python -c "import finhjb as fjb; print(fjb.__all__[:5])"
```

如果你在无图形界面的环境里运行，再加上：

```bash
export MPLBACKEND=Agg
```

这套 BCW 脚本的正式使用方式，是在仓库根目录执行：

```bash
uv run python src/example/BCW2011Liquidation.py
```

而不是切到 `src/example/` 里本地直跑。

## 第二步：运行 Case I

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011Liquidation.py
```

健康运行通常表现为 `w_bar ≈ 0.22`、`p'(0) ≈ 30`，以及低现金区域投资显著为负。

## 第三步：运行 Case II

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011Refinancing.py
```

健康运行通常表现为：

- `phi=1%` 时 `w_bar ≈ 0.19`、`m ≈ 0.06`；
- `phi=0` 时 `w_bar ≈ 0.14`、`m ≈ 0`。

## 第四步：运行 Case IV

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011Hedging.py
```

对 costly-margin 那条线，健康运行通常表现为 `w_- ≈ 0.07`、`w_+ ≈ 0.11`、`w_bar ≈ 0.14`，且 `psi` 落在 `[-5, 0]`。

## 第五步：运行 Case V

```bash
MPLBACKEND=Agg uv run python src/example/BCW2011CreditLine.py
```

健康运行通常表现为 `w_bar ≈ 0.08`、`c+m ≈ 0.10`，以及有 credit line 时 `p'(0)` 大约在 `1.01`。

## 第六步：带着目的读结果

跑完以后，先看：

```python
print(bundle["artifact_paths"])
print(bundle["results"])
```

如果你想直接看某个场景的求解结果：

```python
result = bundle["results"]["fixed-cost"]
print(result["summary"])
print(result["grid"].df.head())
print(result["grid"].df.tail())
```

## 下一步去哪里

- [BCW2011 案例总览](./bcw2011-case-study.md)
- [BCW2011 Liquidation 逐步讲解](./bcw2011-liquidation-walkthrough.md)
- [BCW2011 Refinancing 逐步讲解](./bcw2011-refinancing-walkthrough.md)
- [BCW2011 Hedging 逐步讲解](./bcw2011-hedging-walkthrough.md)
- [BCW2011 Credit Line 逐步讲解](./bcw2011-credit-line-walkthrough.md)

如果你想从论文公式一路追到 `Parameter` / `Boundary` / `PolicyDict` / `Policy` / `Model`，应该从这些 walkthrough 继续往下读。
