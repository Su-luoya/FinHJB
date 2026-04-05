# 输出与验证

当模型在范围内、环境也就绪以后，`finhjb-model-coder` 的交付物应该是可检查、可运行、可复核的，而不是“看起来像代码”的文本。

## 预期交付物

正确的交付目标不是“看起来像样的代码”，而是：

- 一份结构化模型摘要
- 可执行的 FinHJB 代码或 rescue-search runner bundle
- 一份已执行测试或搜索摘要
- 一份第一次求解的验证清单

## 典型交互流程

健康的交互通常是这样：

1. 你先提供模型材料。
2. Skill 判断模型是否属于一维 FinHJB 范围。
3. Skill 确认环境是否就绪。
4. Skill 只追问那些会改变代码生成结果的关键问题。
5. Skill 显式确认差分格式和边界搜索设置。
6. 如果需要校准救援，Skill 先结构化 fixed parameters、search parameters、hard constraints 和 soft preferences。
7. Skill 生成代码或 rescue-search bundle。
8. Skill 运行 post-generation test loop 或搜索闭环。
9. Skill 先修复可修复的失败项，再正式交付。

## 生成后的测试修复闭环

正式交付前，Skill 应至少运行：

- 语法与导入检查
- `Solver(...)` 构造检查
- 至少一次 baseline solve
- 如果任务要求图或摘要文件，再检查这些产物是否真的生成

如果这些检查因为实现问题而失败，Skill 应先修复代码并重跑。

如果启用了 rescue mode，输出 bundle 还应该包含：

- 一张机器可读的搜索历史表
- 最优参数配置
- 一份缩圈重搜过程摘要
- 可选的最佳候选图形或诊断输出

## 文件结构规则

不要把所有任务都塞进一个脚本。

建议规则：

- 紧凑的 baseline solve：单文件通常足够
- 敏感性分析 + 结果保存 + 图形输出：拆成求解、数据、绘图三个文件

这样更容易重跑、诊断和改图。

## 哪些情况应该中止交付

下面这些情况出现时，Skill 应该停下来，而不是假装已经成功：

- `finhjb` 环境还没准备好
- 关键方程或推导仍然缺失
- 校准值还没明确
- 画图要求仍然含糊
- 模型超出一维 FinHJB 范围

## 相关页面

- [完整整合页](./finhjb-model-coder.md)
- [求解器指南](./solver-guide.md)
- [排障](./troubleshooting.md)
