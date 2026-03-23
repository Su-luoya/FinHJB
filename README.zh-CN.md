# FinHJB

[English README](./README.md) | [📖 文档](https://su-luoya.github.io/FinHJB/zh/) | [📖 English Docs](https://su-luoya.github.io/FinHJB/)

FinHJB 是一个基于 JAX 的一维 Hamilton-Jacobi-Bellman (HJB) 方程求解库。

## 主要特性

- **策略迭代求解**: 支持使用策略迭代求解 HJB 方程，可选 Anderson 加速
- **边界方法**: 边界更新和边界搜索，以获取最优边界条件
- **敏感性分析**: 参数延拓，分析参数变化对解的影响
- **灵活的导数方法**: 支持中心差分、向前差分和向后差分
- **GPU 支持**: 基于 JAX 构建，可无缝使用 CPU/GPU，并支持自动微分
- **类型安全**: 完整的类型注解，参数和策略类提供鲁棒的模型构建
- **结果保存与加载**: 支持保存和加载解、网格和敏感性分析结果

## 安装

使用 `uv` 安装：

```bash
uv add finhjb
```

或使用 `pip`：

```bash
pip install finhjb
```

**注意**: 默认安装为 CPU 版本。如需 GPU 支持，请单独安装相应 CUDA/Metal 后端的 JAX。
