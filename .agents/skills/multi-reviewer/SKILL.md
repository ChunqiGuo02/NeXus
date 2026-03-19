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

## Step 0.5: Domain-Calibrated Reviewer Generation (v2.1)

**不使用通用 persona，而是根据论文 topic 动态生成领域专家 reviewer。**

1. 从论文提取 top-5 关键词 / topic tags
2. 在目标 venue 近 2 年同 area 的论文中找 **高频 senior author**（发过 3+ 篇）
3. 分析这些人的研究风格和关注点：
   - 偏理论 vs 偏实验？
   - 经常在 review 中关注什么？（从 OpenReview 公开 reviews 推断）
   - 他们的代表作中最看重什么 metric / 方法 / 评估标准？
4. 生成 **6 个 Domain-Calibrated Reviewer Profile**：

| Reviewer | 角色 | 生成方式 |
|----------|------|---------|
| A | 该子领域的 senior researcher | 基于高频 senior author 画像 |
| B | 该领域的方法论专家 | 关注数学严谨性 + 算法正确性 |
| C | 应用方向的 practitioner | 关注实用性 + scalability |
| D | 跨领域 reviewer（非核心 area） | 关注 presentation + accessibility |
| E | junior 但 aggressive reviewer | 寻找每一个细节问题 |
| F | Area Chair 视角 | 关注 novelty + significance + fit |

5. 每个 reviewer 必须生成 **"该 reviewer 会特别关注的 3 个问题"** — 基于他们的领域专长

> 这样做的好处：通用型 reviewer 可能不会想到 "为什么不和 GATv2 比"，但 GNN 领域专家一定会问。

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

## 三层 Anchor 校准 + v4 审稿硬化

### Anchor 1: 历史分数分布（静态）

每个 venue_rubrics/*.md 文件内嵌历史统计，用于校准 raw score。

### Anchor 2: cited_by_percentile（可选）

如有被引数据，使用 OpenAlex 验证。

### Anchor 3: 用户校准（渐进式）

用户对历史 review 标注"偏高/准确/偏低"，系统学习偏好。

### Score Deflation Protocol（v4 新增）

**问题**：LLM 有 sycophancy bias，比真实 reviewer 温和得多。

**规则**：
1. 每个 reviewer **必须**找出至少 1 个 **reject-level weakness**（score ≤ 4 的理由），即使整体觉得论文不错
   - 找不到 → 说明审稿不够深入 → 换更严格的 prompt 重审
2. 每个 reviewer 给 overall score 时，同时给出"为什么不应该 reject"的理由
   - 理由不够强 → score 下调 1 分
3. 6 个 reviewer 的 score 分布必须满足：
   - 至少 1 个 score ≤ 5（模拟最严格的 25% 审稿人）
   - 至少 2 个 score ≤ 6（模拟中等严格度）
   - 全部 score > 6 → ⚠️ 模拟失真，增加 Reviewer-2 Attack

### Reviewer-2 Attack（v4 新增 — 极度苛刻模式）

在 6 个 reviewer 之外，额外触发 1 个 **Reviewer-2**（学术圈的 "Reviewer 2 nightmare"）：

```
你是 Reviewer 2。你以极度严格著称。
你的标准是："除非你让我无话可说，否则 reject。"

规则：
1. 找出至少 1 个 FATAL FLAW（能让 AC 直接 reject 的问题，不是小问题）
2. 这个 flaw 必须具体、可验证（不是 "writing could be improved"）
3. 如果真的找不到 fatal flaw → 解释为什么这篇论文值得 accept
4. 你的标准：50% 的论文应该被 reject
```

Reviewer-2 的输出不影响综合 score，但 fatal flaw 必须被显式处理：
- 能 rebuttal → 论文更强
- 不能 rebuttal → 这就是被拒的真正原因

### Venue-Calibrated Score Distribution（v4 新增）

从 `venue_playbooks/playbooks.json` 加载 venue 历史数据校准评分：

```json
{
  "acceptance_rate": "25%",
  "score_distribution": {
    "mean": 5.2, "std": 1.8,
    "accept_threshold": 6.5,
    "oral_threshold": 8.0
  },
  "typical_weaknesses": [
    "incremental contribution",
    "missing important baselines",
    "overclaiming without sufficient evidence"
  ]
}
```

审稿完成后对比 venue 的 accept_threshold：
- score_mean ≥ accept_threshold → "competitive for this venue"
- threshold - 1 ≤ score_mean < threshold → "borderline"
- score_mean < threshold - 1 → "likely reject — 建议补充实验或 pivot"

### Post-Submission Scoring Bias Calibration（v4 新增）

当 `evolution_memory.json` 中积累 ≥2 次真实投稿反馈后：

1. 计算 score_bias = mean(模拟 score - 真实 score)
2. 后续审稿的所有 score 自动减去 score_bias
3. score_bias > 1.5 → ⚠️ "模拟审稿严重偏乐观"

> 这实现了一个**自校准的审稿系统**——越用越准。

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

## Pipeline Exit (v2: 3-Round Review)

v2 拆分为 3 轮递进审稿：

```
review_round1（本 skill 全流程）→ revise_round1 → review_round2（复审+对抗 reviewer）→ revise_round2 → review_round3_meta（AC 终审）
```

完成 Round 1 后：
1. **必须调用** `pipeline-orchestrator.complete_stage("review_round1")` 验证产出
2. 进入 `revise_round1`（修改）→ 然后自动进入 Round 2 和 Meta-Review
3. Meta-Review reject → 可 rollback 到 `experiment_run` 补实验

---

## Domain Taste 集成

在生成 reviewer persona 前，**必须**读取 `artifacts/domain_taste_profile.json`（由 `domain_calibration` stage 自动生成）。

### Reviewer Persona 生成规则

1. **读取 domain_taste_profile.json**:
   - `structural_norms` → 每个 reviewer 的 must_check 中加入违反项
   - `staircase_diffs` → 校准评分（"elite 100% 有 ablation" → 没有则扣分）
   - `argumentation_patterns` → 设定 reviewer 关注的论证维度
   - `must_have_baselines` → 检查是否缺少必备 baseline
   - `trending_direction` → 评估 timing 和 relevance

2. **每个 reviewer persona 必须包含**:
   - ≥3 条来自 domain_taste 的具体检查项
   - 该维度对应的 elite 统计值作为参照
   - 例: "elite insight_density 平均 0.71，低于 0.5 应扣分"

3. **SDP Handoff 生成**:
   - 切换到 Codex 前，调用 `pipeline-orchestrator.generate_sdp_handoff_file(project_dir, "review", 3)`
   - 自动将 domain_taste_profile 的完整核心内容嵌入 handoff（不能只放摘要）
   - 含: structural_norms 全表、staircase_diffs、trending、must_have_baselines
   - 每个 reviewer persona ~800 字，总 handoff ~5000-8000 字

