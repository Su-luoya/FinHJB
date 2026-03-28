# FinHJB Model Coder Skill

`finhjb-model-coder` 是这个仓库提供的 Codex Skill，用来把连续时间金融模型转成可执行的一维 FinHJB 代码。

这一页现在是 Model Coder 路径的整合入口页。

如果你是第一次走这条路径，建议按下面顺序阅读：

- [Model Coder 总览](./finhjb-model-coder-overview.md)
- [输入材料与环境就绪](./finhjb-model-coder-inputs-and-readiness.md)
- [输出与验证](./finhjb-model-coder-output-and-validation.md)

如果你需要一页里看完范围、环境、数值方法、测试闭环和常见失败模式，就继续把这一整页读完。

这一页面向的是希望从方程、论文笔记或 LaTeX 出发，而不是先从已有 Python 文件出发的研究者。

## 这个 Skill 做什么

这个 Skill 的设计目标是：

- 读取文字说明、LaTeX、HJB 方程、FOC 和论文摘录
- 判断模型是否适合当前一维 FinHJB 接口
- 确认目标 Python 环境能否导入 `finhjb`
- 在生成代码前，停下来确认缺失的推导、校准、画图要求或文件结构决策
- 在这些选择会影响实现时，明确确认差分格式和边界搜索方法
- 生成可运行的 FinHJB 代码
- 在交付前运行生成后的测试修复闭环，并先修复失败项
- 返回结构化规格摘要、代码、已执行测试摘要和验证清单

它的核心产出不是复现 BCW，而是把理论模型翻译成代码。

## 第一阶段：生成代码前

### 支持的模型形态

当前包和这个 Skill 都建立在一维状态网格上。

最适合的模型是：

- 一个连续状态变量
- 一个或多个连续控制变量
- 一个标量价值函数
- 固定边界、残差驱动的边界搜索，或直接由求解结果更新边界

如果模型明显需要下面这些能力，Skill 应该拒绝生成会误导人的代码：

- 多个连续状态变量
- 不同 regime 下耦合的多个价值函数
- 不能压缩成一个状态的路径依赖
- 当前 FinHJB 还没有提供的求解器基础设施

这时 Skill 应该说明为什么超出范围，并给出最接近的可实现简化版本。

### 最推荐的输入材料

你越完整地提供数学结构，第一次生成的实现通常就越可靠。

推荐输入包括：

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

如果你提供的是截图或 PDF 图片，而关键公式没有可靠文字版，Skill 应先要求你补充可复制的公式文本，再继续生成代码。

### Skill 必须显式拦下的硬阻塞

在生成代码前，遇到下面这些情况时 Skill 应该先停下来确认：

- 当前环境还不能导入 `finhjb`
- 文档定义了参数，但没有给出数值校准
- 数学表达还不能直接对应到代码，需要先做推导
- 用户要求画图但没有说明具体画什么
- 任务同时包含敏感性分析和画图，但交付物的文件结构还不清楚

这也是这个 Skill 最核心的安全规则：不要静默补全缺失的数学步骤或交付要求。

## 第二阶段：映射、数值方法与文件结构

### 运行环境与前置条件

这个 Skill 把环境就绪视为“可运行交付”的硬前提。

具体来说：

- 如果你在 FinHJB 仓库源码里工作，Skill 应优先使用仓库自己的 Python 环境
- 如果你在自己的下游项目里工作，Skill 应优先走 `uv add finhjb` 或 `pip install finhjb`
- 如果当前环境还不能导入 `finhjb`，Skill 应先切到安装辅助模式，而不是把最终代码说成已经可运行

最小 smoke test 可以是：

```bash
python -c "import finhjb"
```

在这个仓库里，更贴近实际的是：

```bash
uv run python -c "import finhjb"
```

### 数学表达还不能直接对应到代码，需要先做推导

如果模型在数学层面还没有完全映射到实现层，Skill 应该先停下来，明确说出还缺哪些推导步骤。

常见情况包括：

- 论文里的状态归一化还没有完全展开
- HJB 还没有改写成可直接实现的 residual
- 控制律还没有改写成闭式更新或 FOC residual
- 论文中的边界条件还没有改写成 `Boundary` 数值或 `BoundaryConditionTarget`

这些推导步骤需要先和用户确认，再进入代码生成。

### 差分格式如何选

这个 Skill 不应该对所有模型都静默默认 `derivative_method="central"`。

更稳妥的经验法则是：

- 如果扩散项在左右边界都不接近 0，优先 `central`
- 如果扩散项在左边界附近接近 0，优先 `forward`
- 如果扩散项在右边界附近接近 0，优先 `backward`
- 如果材料不足以判断，Skill 应先追问，而不是直接默认

这个选择应同时写进规格摘要和生成代码里的 `Config(...)` 附近注释。

### 边界搜索方法如何选

对内生边界来说，搜索方法不应被当成隐藏实现细节。

默认启发式是：

- 如果只有 1-2 个边界条件目标，而且 bracket 可信，先用 `bisection`
- 如果边界条件目标达到 3 个及以上，先用 `hybr` 或其他支持的多维根求解方法

重要例外：

- 如果 1-2 个目标的默认二分法在生成后的测试修复闭环里表现不好，Skill 应把最终实现升级到 `hybr` 或其他支持的方法，并明确解释原因

### 敏感性分析加作图时的文件结构

不要把所有任务都当成单脚本交付。

建议规则是：

- 如果任务只是 baseline solve 或一个紧凑的 benchmark 复现，单文件通常够用
- 如果任务同时包含敏感性分析、结果保存和画图，至少拆成三个文件：
  - 求解/模型文件
  - 数据保存或数据导出文件
  - 绘图文件

这样拆分能让重跑求解、修改图形和检查诊断都更清楚。

## 第三阶段：生成、测试与交付

### 交互流程

这个 Skill 的目标工作流是：

1. 你先提供模型材料。
2. Skill 先判断模型是否属于一维 FinHJB 可处理范围。
3. Skill 确认目标 Python 环境是否能运行 `finhjb`。
4. Skill 提炼出一份结构化模型规格。
5. Skill 只追问那些会改变代码生成结果的关键问题。
6. Skill 明确确认差分格式、边界搜索方法和文件结构。
7. Skill 选择最接近的 FinHJB 模板。
8. Skill 生成代码。
9. Skill 运行测试修复闭环，并在必要时先修复再交付。
10. Skill 输出：
   - 结构化模型规格
   - 可执行的 FinHJB 代码
   - 已执行测试与修复摘要
   - 验证清单

### 生成后的测试修复闭环

正式交付前，这个 Skill 应至少运行：

- 语法与导入检查
- `Solver(...)` 构造检查
- 至少一次基准求解
- 如果任务要求图或摘要文件，还要检查这些产物是否真的生成

如果这些检查因为可修复的实现问题而失败，Skill 应先修复并重跑。只有缺少公式、缺少推导、环境未就绪或模型本身超范围这类外部阻塞，才应该中止闭环。

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

```text
Use $finhjb-model-coder to read this model, confirm whether my current environment can run FinHJB, list any derivations that still need confirmation, choose the derivative scheme and boundary-search method explicitly, then generate and test the code before handing it back.
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

安装这个 Skill 本身，并不会自动把每个下游项目的 `finhjb` 运行环境都装好。执行环境仍然需要能成功导入 `finhjb`。

## 常见失败模式

### 模型其实有两个状态变量

这时正确的下一步不是马上生成代码，而是先判断能否接受一维化近似。

### HJB 有了，但边界条件没有

Skill 应该先停下来追问缺失的左右边界逻辑，再决定使用 `solve()`、`boundary_search()` 还是 `boundary_update()`。

### 文档定义了参数，但没有给出数值校准

Skill 应该先停下来问清楚第一版可运行实现到底要用哪些数值，而不是从别的案例里猜一个 baseline。

### 数学表达还不能直接对应到代码，需要先做推导

Skill 应该先明确指出还缺哪些推导步骤，例如状态归一化、实现用的 HJB residual、FOC 重写、边界条件改写等，并和用户确认后再生成代码，而不是默默做完推导直接交付。

### 用户要求画图但没有说明具体画什么

Skill 应该先停下来确认交付物里到底要画哪些求解结果、比较静态或论文风格图，而不是因为论文里常见某几张图就直接默认一套绘图布局。

### 任务要求敏感性分析和画图，但代码还写成一个文件

Skill 应该把交付物重构成分开的求解文件、数据文件和绘图文件。

### 论文定义了控制变量，但没有给出更新规则

Skill 应该追问这个控制变量究竟是显式更新、通过 FOC 隐式求解，还是由某个分区条件决定。

### 第一次生成的求解数值上不稳定

这通常说明模型还需要更好的初始化、更合适的差分格式、更清楚的边界逻辑，或者更干净的 baseline，然后才适合做 sensitivity analysis。Skill 应该先尝试修复生成代码并重跑 solve loop。

## 推荐阅读顺序

如果你刚开始接触这个仓库，建议按这个顺序：

1. 先读这一页
2. 再读 [建模指南](./modeling-guide.md)
3. 再读 [求解器指南](./solver-guide.md)
4. 然后再把 Skill 用到你自己的模型材料上
