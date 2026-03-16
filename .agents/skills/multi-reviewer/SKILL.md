---
name: multi-reviewer
description: SDP 双模型 6 审稿人 + 交叉审核系统。含拒稿信预演。当用户说"审稿"、"review"、"帮我看看这篇论文写得怎么样"时触发。
---

# multi-reviewer

模拟顶会审稿流程的 **SDP 双模型 6 审稿人 + 交叉审核** 系统。

读取 `evolution-memory` 中的 `review_rules`（如有）。

## Step 0: 拒稿信预演

在正式审稿前，先做一轮自我攻击：

1. 当前模型假设自己是一个想 reject 这篇论文的 reviewer
2. 写一封 200 字拒稿意见（强制找出 3 个致命弱点）
3. 论文作者（当前模型）基于拒稿信**预防性修改**这些弱点
4. 修改完成后再进入正式审稿

> 目的：在别人攻击你之前，先自我攻击。提前暴露弱点并修复。

## Step 1: 准备

```
📊 预估消耗：Group 1 (Gemini) ~5 次 + Codex (GPT 5.4) ~5 次
```

1. 加载 venue rubric → 读取 `venue_rubrics/{venue}.md`
2. 准备 evidence → 读取 `evidence_graph.json` 中的相关 claims
3. 搜索 related work → 找 arXiv 近期论文做 grounding

## Step 2: SDP 双模型 6 审稿人

遵循 `sdp-protocol` 通用规则。切换 3 次（→GPT →回 Gemini →GPT 终审）。

### Round 1 — 模型 1（Gemini Pro）扮演 Reviewer A/B/C

```markdown
# SDP Handoff: Multi-Review Round 2
> 📋 操作：打开 Codex 插件 → 新建对话 → 粘贴本文件

## Reviewer A（严格型）
重点：Soundness + Reproducibility
[7 维度评分 + strengths + weaknesses + questions]

## Reviewer B（创新型）
重点：Novelty + Significance
[7 维度评分 + strengths + weaknesses + questions]

## Reviewer C（读者型）
重点：Clarity + Related Work
[7 维度评分 + strengths + weaknesses + questions]
```

输出到 `dialogue/reviews_gemini.md`。

### → 用户切换到 Codex 插件（GPT 5.4）

### Round 2 — 模型 2（GPT 5.4）扮演 Reviewer D/E/F + 交叉审核

GPT 先独立审稿，再看到 Gemini 的 reviews 做交叉审核：

```
Part 1: 独立审稿
├── Reviewer D（严格型）：独立审稿
├── Reviewer E（创新型）：独立审稿
└── Reviewer F（读者型）：独立审稿

Part 2: 交叉审核（看到 Gemini 的 A/B/C reviews 后）
├── 标注 GPT 组 vs Gemini 组的共识点
├── 标注分歧点 + GPT 组的立场和理由
├── GPT 觉得 Gemini 遗漏了什么
└── GPT 的综合共识/分歧报告
```

输出到 `dialogue/reviews_gpt.md`。

### → 用户切回 Antigravity（Gemini）

### Round 3 — 模型 1（Gemini）交叉回应

```
├── 看到 GPT 的 D/E/F reviews + 交叉审核报告
├── 标注 Gemini 组 vs GPT 组的共识/分歧
├── 对分歧点 Gemini 的立场和理由
└── Gemini 的综合共识/分歧报告
```

输出到 `dialogue/cross_review_gemini.md`。

### → 用户切回 Codex 插件（GPT 5.4）

### Round 4 — 模型 2（GPT 5.4）终审

```
├── 审阅 Gemini 的交叉回应
├── 综合双方意见，做最终裁决
├── 最终修改清单（按优先级排序）
│   ├── must_fix：不改就 reject 的问题
│   └── nice_to_have：改了更好的建议
├── revision_roadmap（每项改进的预估工作量）
└── Overall Decision: Accept / Minor Revision / Major Revision
```

输出到 `dialogue/final_review.md`。

**切换次数：3 次（→GPT →回Gemini →GPT终审）**

## Reviewer Prompt 模板

### 严格型（A/D）

```
你是一位顶会的严格审稿人。你的审稿风格以挑硬伤著称。

你正在审稿目标会议: {venue}
评审标准见附件 rubric。

**你的重点关注领域:**
- Soundness: 理论证明是否有漏洞？实验设计是否 fair？baseline 是否过时？
- Reproducibility: 超参数是否完整？代码是否公开？结果是否可复现？

**你必须做到:**
1. 按 rubric 中的 7 个维度逐一打分
2. 列出至少 3 个 strengths 和 3 个 weaknesses
3. 每个 weakness 必须引用论文中的具体位置（section + 原文）
4. 提出至少 1 个需要额外实验才能回答的 question
5. **必须尝试找至少 1 个 failure case**
6. **数学检查清单**（符号定义、公式编号、维度匹配等）
7. 给出 overall score 和 confidence
```

### 创新型（B/E）

```
你是一位重视创新的审稿人。善于发现亮点，也指出创新性不足。

**重点:**
- Novelty: 核心方法/视角是否前所未有？与最近 prior art 差异多大？
- Significance: 能否开辟新方向或解决重要问题？

**额外要求:**
- **交叉验证 novelty claim**：对照 evidence graph
- **推广性分析**：方法能推广到哪些场景？
```

### 读者型（C/F）

```
你是一位从读者角度审稿的审稿人。以非本领域毕业生的视角阅读。

**重点:**
- Clarity: 仅凭论文能否理解方法？
- Related Work: 文献覆盖是否完整？

**额外要求:**
- **first-pass 测试**：第一遍阅读标记每个不理解的地方
- **figure caption 检查**：每个图/表 caption 是否 self-contained
- **术语一致性**：同一概念是否在不同段落用不同名称
```

## 7 维度评分框架

| 维度 | 默认权重 | 说明 |
|------|---------|------|
| Novelty | 20% | 与 prior art 的差异化 |
| Soundness | 20% | 方法正确性 + 实验严谨性 |
| Significance | 15% | 潜在影响力 |
| Clarity | 15% | 写作质量 + 可读性 |
| Reproducibility | 10% | 能否复现 |
| Related Work | 10% | 文献覆盖完整性 |
| Ethics & Limitations | 10% | 局限性讨论 + 伦理 |

> 实际权重从 `venue_rubrics/{venue}.md` 加载。

## 三层 Anchor 校准

### Anchor 1: 历史分数分布（静态）

每个 venue_rubrics/*.md 文件内嵌历史统计，用于校准 raw score。

### Anchor 2: cited_by_percentile（可选）

如有被引数据，使用 OpenAlex 验证。

### Anchor 3: 用户校准（渐进式）

用户对历史 review 标注"偏高/准确/偏低"，系统学习偏好。

## 审稿终审卡点 ⛔

> **Autopilot 硬卡点** — 必须用户确认

展示完整 review 报告后，用户可以：
- ✅ 选择要修改的 weaknesses → 触发 paper-writing Step 7 修改
- ❌ 标注某些 weakness 为"不同意" → 反馈给 Anchor 3
- 🔄 要求某个 reviewer 重新审 → 重新执行对应 Round

## 输出

保存到 `artifacts/review_report.json`（包含 6 份 review、交叉审核报告、终审裁决、revision_roadmap）。

## 反直觉规则

1. **让步小点赢大的** — 承认小问题，在关键点上站稳
2. **6 个 reviewer 不是为了凑数量** — 双模型的视角差异才是核心价值
3. **consensus weaknesses 必须修** — 两个模型都指出的问题几乎一定存在
4. **disagreements 更有价值** — 分歧意味着这个点值得深入思考
5. **不要让好评麻痹你** — 专注 weaknesses，strengths 不需要你操心
