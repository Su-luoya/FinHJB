# FinHJB Model Coder Skill

`finhjb-model-coder` 是这个仓库提供的 Codex Skill，用来把连续时间金融模型转成可执行的一维 FinHJB 代码。

这一页面向的读者，是想从方程、论文笔记或 LaTeX 出发，而不是先从已有 Python 文件出发的研究者。

## 这个 Skill 做什么

这个 Skill 的设计目标是：

- 读取文字说明、LaTeX、HJB 方程、FOC 和论文摘录
- 判断模型是否适合当前一维 FinHJB 接口
- 当边界条件、控制变量或校准细节缺失时主动追问
- 生成可运行的 FinHJB 模型文件
- 同步整理一份实现导向的模型规格摘要
- 给出一份验证清单，帮助你判断第一次求解是否可信

它的核心产出不是“复现 BCW”，而是“把理论模型翻译成代码”。

## 支持的模型形态

当前包和这个 Skill 都建立在一维状态网格上。

最适合的模型是：

- 一个连续状态变量
- 一个或多个连续控制变量
- 一个标量价值函数
- 固定边界、残差驱动的边界搜索，或直接由解更新边界

如果模型明显需要下面这些能力，Skill 应该拒绝生成会误导人的代码：

- 多个连续状态变量
- 不同 regime 下耦合的多个价值函数
- 不能压缩成一个状态的路径依赖
- 当前 FinHJB 还没有提供的求解器基础设施

这种情况下，Skill 应该解释为什么超出范围，并给出最接近的可实现简化版本。

## 最推荐的输入格式

你越完整地提供数学结构，第一次生成的实现就越可靠。

最推荐的输入包括：

- 研究问题，以及价值函数代表什么对象
- 唯一的状态变量及其定义域
- 完整的 HJB 方程
- 控制变量及其可行范围
- 每个控制变量的 FOC 或显式策略规则
- 左右边界条件
- smooth pasting、super-contact 或发行条件
- 参数含义与基准校准值

这些材料可以来自：

- 纯文字笔记
- LaTeX
- 从论文复制出来的段落
- 以上几种的混合

如果你提供的是截图或 PDF 图片，而关键公式没有可靠文字版，Skill 应该先要求你补充粘贴公式，再继续生成代码。

## 交互流程

这个 Skill 的目标工作流是：

1. 你先提供模型材料。
2. Skill 提炼出一份结构化模型规格。
3. Skill 只追问那些会改变代码生成结果的关键问题。
4. Skill 选择最接近的 FinHJB 模板。
5. Skill 输出：
   - 结构化模型规格
   - 可执行的 FinHJB 代码
   - 验证清单

这个“先规格、后落码”的步骤很重要。连续时间模型最容易出错的地方，往往就是边界、控制变量或标准化方式被默认假设了。

## 示例 Prompt

```text
Use $finhjb-model-coder to turn this one-state financing model into executable FinHJB code. I will paste the HJB, controls, boundary conditions, and calibration next.
```

```text
Use $finhjb-model-coder to read this paper excerpt and tell me whether it can be implemented in one-dimensional FinHJB. If yes, generate the code skeleton. If not, explain the smallest workable simplification.
```

```text
Use $finhjb-model-coder to map this HJB and FOC system into Parameter, Boundary, PolicyDict, Policy, and Model classes, and give me a validation checklist for the first solve.
```

## 安装与更新

从仓库源码安装这个 Skill：

```bash
python scripts/install_skill.py
```

常用变体：

```bash
python scripts/install_skill.py --dry-run
python scripts/install_skill.py --dest ~/.codex/skills --force
python scripts/install_skill.py --mode link --force
```

手动安装也完全可以：把 `skills/finhjb-model-coder` 复制到 `${CODEX_HOME:-$HOME/.codex}/skills/` 即可。

## 常见失败模式

### 模型其实有两个状态变量

这时正确的下一步不是马上生成代码，而是先判断能否接受一维化近似。

### HJB 有了，但边界条件没有

Skill 应该先停下来追问缺失的左右边界逻辑，再决定使用 `solve()`、`boundary_search()` 还是 `boundary_update()`。

### 论文定义了控制变量，但没有给出更新规则

Skill 应该追问这个控制变量究竟是显式更新、通过 FOC 隐式求解，还是由某个分区条件决定。

### 第一次生成的代码数值上不稳定

这通常说明模型还需要更好的初始化、更清楚的边界逻辑，或者更干净的 baseline，然后才适合做 sensitivity analysis。请结合验证清单，再回到这些文档：

- [建模指南](./modeling-guide.md)
- [求解器指南](./solver-guide.md)
- [把 BCW 改成你自己的模型](./adapting-bcw-to-your-model.md)

## 推荐阅读顺序

如果你刚开始接触这个仓库，建议按这个顺序：

1. 先读这一页
2. 再读 [建模指南](./modeling-guide.md)
3. 再读 [求解器指南](./solver-guide.md)
4. 然后再把 Skill 用到你自己的模型材料上
