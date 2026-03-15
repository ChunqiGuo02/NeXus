---
name: multi-reviewer
description: 三层 Anchor + 7 维度 + 4 角色多 Agent 审稿系统。当用户说"审稿"、"review"、"帮我看看这篇论文写得怎么样"时触发。
---

# multi-reviewer

模拟顶会审稿流程的**并行多 Subagent** 审稿系统。

## 核心架构：并行 Subagent Dispatch

**不是串行角色扮演**，而是 4 个独立 subagent 并行执行，互不可见：

```
用户说 "审一下这篇论文，目标 ICLR 2026"
  │
  ▼
multi-reviewer 主进程
  │
  ├─ 1. 加载 venue rubric  →  读取 venue_rubrics/iclr.md
  ├─ 2. 准备 evidence      →  读取 evidence_graph.json 中的相关 claims
  ├─ 3. 搜索 related work   →  调用 search_papers 找 arXiv 近期论文做 grounding
  │
  ▼ 并行 dispatch（使用宿主 agent 的 dispatching-parallel-agents 能力；若宿主不支持则退化为串行审稿）
  ┌────────────────┬────────────────┬────────────────┐
  │  Subagent A    │  Subagent B    │  Subagent C    │
  │  严格型审稿人   │  创新型审稿人   │  读者型审稿人   │
  │                │                │                │
  │ 重点:          │ 重点:          │ 重点:          │
  │ • Soundness    │ • Novelty      │ • Clarity      │
  │ • Reproducib.  │ • Significance │ • Related Work │
  │                │                │                │
  │ 输入:          │ 输入:          │ 输入:          │
  │ • draft.md     │ • draft.md     │ • draft.md     │
  │ • rubric       │ • rubric       │ • rubric       │
  │ • evidence     │ • evidence     │ • evidence     │
  │ • related work │ • related work │ • related work │
  │                │                │                │
  │ 输出:          │ 输出:          │ 输出:          │
  │ review_A.json  │ review_B.json  │ review_C.json  │
  └───────┬────────┴───────┬────────┴───────┬────────┘
          │                │                │
          ▼                ▼                ▼
  ┌─────────────────────────────────────────────────┐
  │  Meta Reviewer（串行，在三份 review 完成后执行）   │
  │                                                 │
  │  输入: review_A + review_B + review_C + rubric   │
  │  职责:                                          │
  │  • 综合三人意见                                  │
  │  • 裁决分歧（如 A 说 reject 但 B 说 accept）     │
  │  • 给出最终分数 + 修改建议                       │
  │  • Anchor 校准                                  │
  └─────────────────────────────────────────────────┘
```

## 多模型审稿

💡 **建议使用不同模型模拟不同审稿人**（参见 `rules/model-routing.md`）：

| 角色 | 推荐模型 | 优势 |
|------|---------|------|
| Reviewer A（严格型） | Claude Opus 4.6 Thinking | 发现逻辑漏洞 |
| Reviewer B（创新型） | Gemini 3.1 Pro (High) | 跨领域联想 |
| Reviewer C（读者型） | GPT 5.4 | 语言细节 |
| Meta Reviewer | 用户默认模型 | 综合裁决 |

- **Antigravity**：通过 subagent dispatch 指定不同模型并行执行
- **Claude Code / Open Code**：串行 + `💡` 提示切换模型

## Subagent Prompt 模板

### Reviewer A — 严格型

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
5. 给出 overall score 和 confidence
6. **必须尝试找至少 1 个 failure case**：如果某假设不成立，结论是否还能成立？
7. **数学结构检查**（见下方清单）

**数学检查清单:**
□ 所有符号首次出现时是否有定义？
□ 公式编号连续？有引用但未出现的公式？
□ 定理/引理是否有证明（正文或附录）？
□ Loss function 值域是否合理（如 ≥ 0）？
□ 矩阵乘法维度是否匹配？
□ 梯度可传播？（无 argmax/hard threshold 阻断？）
□ 时间/空间复杂度是否给出？

**论文内容:**
{draft_content}

**Evidence Graph 中与此论文相关的 claims:**
{evidence_claims}

**近期相关工作（用于 grounding）:**
{related_papers}
```

### Reviewer B — 创新型

```
你是一位重视创新的审稿人。你善于发现论文的亮点，同时也会指出创新性不足之处。

你正在审稿目标会议: {venue}
评审标准见附件 rubric。

**你的重点关注领域:**
- Novelty: 核心方法/视角是否前所未有？与最近的 prior art 差异有多大？
- Significance: 能否开辟新方向或解决重要问题？

**你必须做到:**
1. 按 rubric 中的 7 个维度逐一打分
2. 列出至少 3 个 strengths 和 3 个 weaknesses
3. 每个 weakness 必须引用论文中的具体位置
4. **交叉验证 novelty claim**：对照 novelty-checker 的结果（如有），判断 novelty 是否被高估
5. **推广性分析**：如果这个方法 work，它能推广到哪些其他场景？
6. 给出 overall score 和 confidence

**论文内容:**
{draft_content}

**Evidence Graph + novelty_risk:**
{evidence_claims}

**近期相关工作:**
{related_papers}
```

### Reviewer C — 读者型

```
你是一位从读者角度审稿的审稿人。你要以**非本领域毕业生**的视角阅读。

你正在审稿目标会议: {venue}
评审标准见附件 rubric。

**你的重点关注领域:**
- Clarity: 能否仅凭论文理解方法？每个符号首次出现时是否有定义？
- Related Work: 文献覆盖是否完整？与每类相关工作的差异是否明确？

**你必须做到:**
1. 按 rubric 中的 7 个维度逐一打分
2. 列出至少 3 个 strengths 和 3 个 weaknesses
3. **first-pass 测试**：第一遍阅读时标记每个你不理解的地方
4. **figure caption 检查**：每个图/表的 caption 是否 self-contained？
5. **术语一致性**：同一概念是否在不同段落使用不同名称？
6. 给出 overall score 和 confidence

**论文内容:**
{draft_content}

**Evidence Graph:**
{evidence_claims}

**近期相关工作:**
{related_papers}
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

> 实际权重从 `venue_rubrics/{venue}.md` 加载，不同会议不同。

## 三层 Anchor 校准

### Anchor 1: 历史分数分布（静态）

不依赖 OpenReview API，直接在 venue rubric 中内嵌历史统计数据：

```
校准方法：
  raw_avg=7.0 → "高于历史均值 1σ，预估 top 15%"
  raw_avg=5.0 → "接近历史均值，borderline"
  raw_avg=3.5 → "低于均值 1σ，预估 bottom 30%"
```

> 每个 venue_rubrics/*.md 文件末尾已追加该会议的历史分数分布。

### Anchor 2: cited_by_percentile（可选）
- 如果 evidence_graph 中有被引数据，使用 OpenAlex 验证
- 没有则跳过（不阻塞流程）

### Anchor 3: 用户校准（渐进式）
- 用户对历史 review 标注 "偏高/准确/偏低"
- 系统学习偏好，逐步调整

## 会议 Rubric 文件

```
venue_rubrics/
├── generic.md            # 通用学术标准（未指定 venue 时默认）
│
│ ── AI/ML 会议 ──
├── neurips.md            # NeurIPS: 重 Novelty + Significance
├── iclr.md               # ICLR: 重 Soundness + Clarity
├── icml.md               # ICML: 重理论贡献
├── acl.md                # ACL: 重 Reproducibility + 多语言 (1-5 分制)
├── cvpr.md               # CVPR: 重 Visual Quality
├── aaai.md               # AAAI: 跨领域覆盖
│
│ ── 跨领域期刊 ──
├── nature_science.md     # Nature/Science/Cell: 重 Significance (30%)
├── biology.md            # PNAS/eLife/Cell Reports: 重 Soundness + 生物学重复
├── physics.md            # PRL/PRX/ApJ: 重 Soundness + 误差分析
├── earth_science.md      # GRL/JGR/ERL: 重 Data Quality + 模型验证
└── architecture_urban.md # Landscape/Cities/CEUS: 重 Practical Relevance + 图面质量
```

用户指定目标会议后，加载对应 rubric 调整维度权重和评分标准。

## 输出

```json
{
  "venue": "ICLR 2026",
  "overall_score": 6.2,
  "confidence": 0.75,
  "decision_suggestion": "borderline accept",
  "reviews": [
    {
      "reviewer": "A (严格型)",
      "scores": {"novelty": 6, "soundness": 7, "significance": 5, "clarity": 7, "reproducibility": 6, "related_work": 7, "ethics": 8},
      "overall": 6.3,
      "strengths": ["..."],
      "weaknesses": ["..."],
      "questions": ["..."],
      "requested_experiments": ["..."]
    },
    {"reviewer": "B (创新型)", "...": "..."},
    {"reviewer": "C (读者型)", "...": "..."}
  ],
  "meta_review": {
    "summary": "三位审稿人的共识和分歧总结",
    "consensus_strengths": ["三人都认可的优点"],
    "consensus_weaknesses": ["三人都指出的问题"],
    "disagreements": [{"topic": "...", "A_opinion": "...", "B_opinion": "...", "resolution": "裁决理由"}],
    "final_decision": "borderline accept",
    "must_fix": ["不改就 reject 的问题，按优先级排序"],
    "nice_to_have": ["改了更好的建议"],
    "revision_roadmap": [
      {"priority": 1, "issue": "...", "suggested_fix": "...", "estimated_effort": "1h"},
      {"priority": 2, "issue": "...", "suggested_fix": "...", "estimated_effort": "3h"}
    ]
  },
  "anchor_calibration": {
    "raw_average": 5.8,
    "calibrated_average": 6.2,
    "calibration_method": "openreview_iclr2025_distribution",
    "percentile_in_venue": "top 35%"
  }
}
```

保存到 `artifacts/review_report.json`。

## Review Arena 卡点

展示完整 review 报告后，用户可以：
- ✅ 选择要修改的 weaknesses → 触发 paper-writing 修改
- ❌ 标注某些 weakness 为"不同意" → 反馈给 Anchor 3
- 🔄 要求某个 reviewer 重新审 → 重新 dispatch 单个 subagent
