---
description: NeurIPS 评审标准 (Neural Information Processing Systems)
---

# NeurIPS Review Rubric

## 页数限制
- 正文: 9 页 (不含参考文献)
- 附录: 无限制（但审稿人没有义务阅读）

## 评分维度 & 权重

| 维度 | NeurIPS 专属权重 | 评分说明 |
|------|----------------|---------|
| **Novelty** | 25% | 核心考量。方法或视角是否前所未有？不接受纯 incremental |
| **Significance** | 20% | 对领域的潜在影响。能否开辟新方向或解决重要问题？ |
| **Soundness** | 20% | 理论证明是否严谨？实验设计是否 fair？ |
| **Clarity** | 15% | 论文是否 self-contained？notation 是否一致？ |
| **Reproducibility** | 10% | 是否提供代码/伪代码/超参数？NeurIPS 有 Reproducibility Checklist |
| **Related Work** | 5% | 文献覆盖是否完整？ |
| **Ethics** | 5% | Broader Impact Statement 是否充分？ |

## NeurIPS 特有要求

- **Reproducibility Checklist**: 必须填写，审稿人会检查
- **Broader Impact Statement**: 强烈建议，不填会扣分
- **Anonymity**: 双盲审稿，正文不得透露作者信息
- **Supplementary Material**: 在 deadline 后有额外提交窗口

## 评分标准 (1-10)

| 分数 | 含义 |
|------|------|
| 8-10 | Strong Accept — 顶级贡献，引领方向 |
| 6-7 | Weak Accept — 有贡献但有可改进之处 |
| 5 | Borderline — 不确定，需要讨论 |
| 3-4 | Weak Reject — 贡献不足或有重大问题 |
| 1-2 | Strong Reject — 根本性缺陷 |

## 常见 Reject 原因

1. 纯工程优化，无理论/方法创新
2. 实验 baseline 不公平或过时
3. 缺少 ablation study
4. Claims 过强但证据不足
5. 与已有工作的差异不清晰

## 历史分数分布（Anchor 校准用）

| 指标 | 值 |
|------|----|
| Accept 线 | ~6.0 (top 25%) |
| Spotlight | ~7.0 (top 5%) |
| Oral | ~8.0 (top 1%) |
| 分数均值 | 5.2 |
| 标准差 | 1.8 |
| 录取率 | ~25% |
