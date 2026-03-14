---
description: CVPR 评审标准 (Computer Vision and Pattern Recognition)
---

# CVPR Review Rubric

## 页数限制
- 正文: 8 页 (不含参考文献)
- 附录: 允许

## 评分维度 & 权重

| 维度 | CVPR 专属权重 | 评分说明 |
|------|-------------|---------|
| **Novelty** | 20% | 方法或问题的新颖性 |
| **Soundness** | 20% | 实验设计和 fair comparison |
| **Significance** | 15% | 对 CV 领域的影响 |
| **Clarity** | 10% | 写作和图表质量 |
| **Reproducibility** | 10% | 代码/数据是否可获取 |
| **Visual Quality** | 15% | CVPR 特色！可视化结果质量 |
| **Related Work** | 5% | CV 领域文献覆盖 |
| **Ethics** | 5% | deepfake、隐私等 |

## CVPR 特有要求

- **可视化结果**: 必须有高质量的视觉对比图
- **定量+定性**: 不能只有数字，需要有可视化分析
- **Failure Cases**: 展示失败案例是加分项
- **Real-world Demo**: 有真实场景演示更受欢迎
- **Supplementary Video**: 鼓励提交补充视频

## 评分标准 (1-10)

| 分数 | 含义 |
|------|------|
| 8-10 | Strong Accept — 视觉效果惊艳 + 方法创新 |
| 6-7 | Weak Accept — 结果好但创新有限或反之 |
| 5 | Borderline |
| 3-4 | Weak Reject |
| 1-2 | Strong Reject |

## 常见 Reject 原因

1. 可视化结果不够好，无法让人信服
2. 只在小数据集测试（如只用 CelebA 不用 FFHQ）
3. 缺少与 SOTA 的 fair comparison
4. 方法复杂但提升微小
5. 缺少 failure case 分析
