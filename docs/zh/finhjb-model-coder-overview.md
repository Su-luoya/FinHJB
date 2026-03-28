# Model Coder 总览

这一页是 `finhjb-model-coder` 路径的入口页。

如果你想先判断这个 Skill 是否适合你的任务，而不是马上准备全部方程和环境细节，就先读这一页。

## 这个 Skill 适合什么

`finhjb-model-coder` 是仓库里的 Codex Skill，用于把连续时间金融模型翻译成可执行的一维 FinHJB 代码。

它的目标输入不是已有 Python 实现，而是：

- 文字说明
- LaTeX
- HJB 方程
- 一阶条件
- 论文摘录

## 这个 Skill 会做什么

它默认会：

- 判断模型是否适合当前一维 FinHJB 接口
- 确认目标 Python 环境能否导入 `finhjb`
- 只追问那些会改变代码生成结果的关键问题
- 显式选择差分格式和边界搜索方法
- 生成可运行的 FinHJB 代码
- 在交付前跑一次测试修复闭环

## 什么时候该用它

当你想要“理论到代码”的翻译流程，而不想手写第一版 FinHJB 实现时，就应该用它。

典型请求包括：

- “把这套 HJB 和 FOC 系统映射成 `Parameter`、`Boundary`、`PolicyDict`、`Policy`、`Model`。”
- “先判断这篇论文模型能不能放进一维 FinHJB。”
- “生成 baseline 实现并在交付前先测试。”

## 什么时候不该把它当主路径

下面这些情况更适合先走别的路径：

- 你已经有干净的 Python 实现，主要只需要查 API
- 你的模型明显需要多个连续状态变量
- 你更想先通过 BCW 示例理解包本身

这些情况应该先走 package 路径或 BCW 路径。

## 下一步

- [输入材料与环境就绪](./finhjb-model-coder-inputs-and-readiness.md)
- [输出与验证](./finhjb-model-coder-output-and-validation.md)
- [完整整合页](./finhjb-model-coder.md)
