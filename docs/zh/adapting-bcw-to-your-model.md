# 把 BCW 改成你自己的模型

这一页是 BCW 路径通向“第一个自定义模型”的桥接页。

建议在 [BCW Liquidation 逐步讲解](./bcw2011-liquidation-walkthrough.md)、[BCW Refinancing 逐步讲解](./bcw2011-refinancing-walkthrough.md)、[BCW Hedging 逐步讲解](./bcw2011-hedging-walkthrough.md)、[BCW Credit Line 逐步讲解](./bcw2011-credit-line-walkthrough.md) 和 [建模指南](./modeling-guide.md) 之后阅读。

如果你根本不打算把 BCW 当模板，而是直接从自己的问题开始建模，请改看 [库快速上手](./quickstart-library.md)。

这一页回答的是一个非常实际的问题：

“我已经能复现 BCW 了。接下来怎样把它改造成我自己的模型，而且不要一次改崩全部东西？”

核心原则很简单：

- 结构尽量大胆复用 BCW，
- 经济设定逐步改，
- 每改一步都重新验证。

四个 BCW walkthrough 应该被当成“理论到代码”的底稿来读。这一页默认你已经理解论文方程是怎样落到 `Parameter` / `Boundary` / `PolicyDict` / `Policy` / `Model` 上的。

## 建议在什么之后阅读

- [快速开始](./getting-started.md)
- [BCW Liquidation 逐步讲解](./bcw2011-liquidation-walkthrough.md)
- [BCW Refinancing 逐步讲解](./bcw2011-refinancing-walkthrough.md)
- [BCW Hedging 逐步讲解](./bcw2011-hedging-walkthrough.md)
- [BCW Credit Line 逐步讲解](./bcw2011-credit-line-walkthrough.md)
- [建模指南](./modeling-guide.md)

## 先选对模板

| 你的模型更像…… | 最适合起步的模板 |
|---|---|
| 一维状态、一个控制、左端 liquidation、右端内生 payout 边界 | `src/example/BCW2011Liquidation.py` |
| 一维状态、一个控制、带股权发行或内部现金目标 `m` | `src/example/BCW2011Refinancing.py` |
| 一维状态、两个控制、对冲需求或控制影响方差 | `src/example/BCW2011Hedging.py` |
| 一维状态跨越债务区和现金区，或状态域需要穿过零点 | `src/example/BCW2011CreditLine.py` |

如果拿不准，先从 liquidation 开始。一个控制总比两个控制更容易调，而且它给了你最干净的 payout-side 边界基线。

另外，在你开始改写之前，先保持这套执行约定不变：从仓库根目录运行，并继续使用 `from src.example.bcw2011 import ...` 这一类绝对导入。不要再把相对导入或“切进 `src/example/` 本地直跑”的假设带回来。

## 哪些部分通常可以原样复用

下面这些结构，很多时候可以几乎照搬：

- 整个文件的组织方式；
- `Parameter` / `Boundary` / `PolicyDict` / `Policy` / `Model` 的分工；
- `Solver(...)` 的构造模式；
- 打印 `grid.boundary`、`grid.df.head()`、`grid.df.tail()` 的诊断代码；
- 保存和重载结果的写法。

这并不是“偷懒”，恰恰是 BCW 主线存在的价值：让你先继承一个稳定的一维 HJB 工作流。

## 哪些部分绝不能盲抄

以下内容必须重新思考，而不能机械复制：

- 经济参数列表；
- HJB 残差中的符号和漂移项；
- 控制变量的 FOC 或显式策略；
- 边界值公式；
- 边界搜索目标；
- 再融资或发行逻辑；
- 结果的经济解释。

如果这些部分不重写，你的代码可能“能跑”，但解的其实不是你的模型。

## 推荐迁移顺序

## 第一步：复制最接近的 BCW 脚本

先复制最像你目标问题的 BCW 文件，不要从空白文件开始。

除非你已经非常熟悉 FinHJB 内部接口，否则从零写会让你同时处理太多不确定性。

## 第二步：先改名字

尽早把这些类改成你自己的语义命名：

- `Parameter`
- `PolicyDict`
- `Boundary`
- `Policy`
- `Model`

即便底层逻辑暂时还是 BCW，先把概念边界划清楚，会让你后续不容易混淆。

## 第三步：先只改参数

第一轮只改 `Parameter` 类。

这一阶段的成功标准是：

- 文件还能导入；
- `Solver(...)` 还能构造；
- 派生参数逻辑是清晰、局部且可解释的。

先不要动残差。

## 第四步：先让固定边界求解稳定

在引入边界搜索之前，先争取让下面这个最简单工作流跑通：

```python
state, history = solver.solve()
```

为什么这一步很关键：

- 它把 HJB 主体和边界搜索分开了；
- 它能先告诉你方程和策略是否自洽；
- 调试面最干净。

第一批检查建议是：

```python
print(type(state).__name__)
print(state.df.head())
print(state.df.tail())
```

## 第五步：再替换策略逻辑

接着实现你真正需要的控制变量。

一个实用决策规则：

- 有稳定闭式更新，用 `@explicit_policy`；
- 更自然地写成残差或 FOC，就用 `@implicit_policy`。

这一阶段要确认：

- 所有策略键都存在；
- 每个数组长度和网格一致；
- 求出来的策略列至少能被经济学解释。

## 第六步：再替换 HJB 残差

只有当策略层已经清楚之后，再改 `Model.hjb_residual`。

好的做法：

- 把残差拆成有含义的中间项；
- 每一项都能对应回你的理论方程；
- 用变量名表达经济含义。

不好的做法：

- 把整个残差塞成一行，再靠肉眼找符号错。

## 第七步：最后再引入内生边界

当固定边界求解已经稳定后，再决定用哪种边界工作流：

- 如果边界通过一个数值条件来确定，用 `boundary_search()`；
- 如果当前解可以直接推出新的边界，用 `boundary_update()`；
- 只有当模型确实需要时，才把两者都加进来。

不要在固定边界都还没稳定时，就先加这一层复杂度。

## 第八步：最后补上保存和诊断

当你已经相信这个解可信之后，再加入：

- `grid.save(...)`
- `load_grid(...)`
- continuation / sensitivity
- 图形或自定义辅助诊断

这时再做分析工具建设，效率最高，因为你已经有一个值得分析的对象。

## 一条很稳的验证阶梯

每一步只回答一个问题：

1. 文件能导入吗？
2. `Solver(...)` 能构造吗？
3. `solve()` 能返回一个像样的 state 吗？
4. 价值函数和策略形状合理吗？
5. 边界条件满足了吗？
6. 最后才问 comparative statics 是否合理。

这个顺序能避免你对一个数值上本来就坏掉的对象做经济解释。

## 具体说，哪些 BCW 部分可以抄，哪些必须改

### 通常可以直接复用的

- 类的分层结构；
- `PolicyDict` 的类型声明方式；
- `Boundary(p=parameter, s_min=..., s_max=...)` 的组织模式；
- `Solver(..., number=..., config=...)` 的写法；
- 打印和保存结果的诊断套路。

### 必须重写的

- 参数值和参数含义；
- 边界公式；
- FOC 逻辑；
- HJB 漂移和扩散项；
- 边界目标函数；
- 结果的经济解释。

## 迁移时最常见的错误

### 一次把所有东西都改了

如果你同时改：

- 参数，
- 边界，
- 控制变量，
- 残差，
- 搜索目标，

那么一旦失败，你几乎无法定位到底是哪一层出了问题。

### 还没跑稳 baseline 就开始做 sensitivity analysis

continuation 很有价值，但它只是把基础求解放大很多次。如果 base solve 本身是错的，sensitivity 只会生成更多错误解。

### 还用 BCW 的诊断规则，但 BCW 的边界条件早就不适用了

例如：

- `d2v[-1]` 对 BCW 的 payout-side 条件非常关键；
- 但你的模型右边界条件可能根本不是这一条。

你可以复用“诊断的习惯”，不能无脑复用“诊断的对象”。

## 给研究者的推荐工作流

1. 先一字不改地复现 liquidation；
2. 再一字不改地复现最接近你的高级 BCW 案例：发行边界用 refinancing，双控制用 hedging，分段状态域用 credit line；
3. 复制更接近你的那个示例；
4. 先改参数和命名；
5. 先让 `solve()` 稳定；
6. 再加你的边界逻辑；
7. 为自己的模型写一套成功检查点；
8. 最后才做 comparative statics、图表和论文数值结果。

## 什么时候该从 liquidation 切到别的模板

当你的模型需要下面这些结构时，更适合切到 refinancing：

- 左边界有发行 value matching；
- 存在内部现金目标 `m`；
- 需要围绕发行点做 smooth pasting。

当你的模型需要下面这些结构时，更适合切到 hedging：

- 多于一个控制变量；
- 方差项本身受控制变量影响；
- 对冲需求带有成本或约束。

当你的模型需要下面这些结构时，更适合切到 credit line：

- 债务区和现金区的 HJB 不一样；
- 状态域需要 `s_min < 0`；
- 同一条网格上要拼接分段 residual。

如果都没有，尽量留在 liquidation 这条更简单的主线，会更容易调试。

## 最后一条经验法则

第一个成功的自定义模型，最好是“朴素的”。

所谓朴素，意思是：

- 一个文件先跑通；
- 类职责清晰；
- 固定边界先稳定；
- 诊断项简单直接；
- 每次只引入一个新的经济想法。

这条“看上去不花哨”的路径，往往反而是最快进入可信研究工作流的方式。

## 下一步

- 回 [建模指南](./modeling-guide.md) 查看接口职责细节。
- 回 [求解器指南](./solver-guide.md) 决定工作流。
- 用 [结果与诊断](./results-and-diagnostics.md) 给你的模型建立自己的成功检查表。
