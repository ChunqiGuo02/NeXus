---
description: 被拒/草稿论文优化流水线：诊断 → 决策（修补 or 重做）→ 执行 → 复审。复用 full-research-pipeline 的全部质量门。
---

# revise-paper

将被拒论文、草稿或预印本升级为顶会/顶刊水准。支持两条路线：修补（核心 idea 可救）和重做（需要 pivot）。

## 使用方式

```
/revise-paper "论文路径或主题"
```

用户可提供以下任意组合：
- 📄 原论文（PDF / TeX / Markdown）— **必须**
- 💬 审稿意见（OpenReview / 邮件截图 / 文本粘贴）— 可选
- 📝 修改想法（markdown 笔记 / 与 Gemini/GPT 的对话记录）— 可选
- 🎯 目标会议/期刊 — 可选（不提供则对标原投稿 venue）

## 卡点行为

与 `full-research-pipeline` 一致：三分支 Autopilot（见 full-research-pipeline.md 卡点行为规范）。

硬卡点（Autopilot 不可跳过）：
1. **救治决策**（方案 A 修补 / 方案 B 重做）
2. 如走重做路线 → 继承 full-research-pipeline 的全部 5 个硬卡点

## 流程

### Stage R0: 输入解析

```
输入文件处理：
  ├─ PDF → pdf-to-markdown → 全文 Markdown
  ├─ TeX → 直接解析
  ├─ 审稿意见 → 结构化提取（每条 weakness 编号 + 严重级别）
  └─ 修改想法(markdown/对话记录) → 提取关键建议列表
```

将原论文喂给 `claim-extractor`，提取原文全部 claims → 写入 `evidence_graph.json`。
将原论文的 references 导入 `corpus_ledger.json`（标注 `access_state`）。

### Stage R1: 论文诊断

#### R1.1 模拟审稿

触发 `multi-reviewer`（6 审稿人 SDP + 交叉审核），对原文做完整审稿。

输出 `artifacts/diagnosis_review.json`：
- 6 份独立 review（7 维度评分 + strengths + weaknesses）
- 综合评分 + 最关键弱点 top-5

#### R1.2 审稿意见交叉验证（如用户提供了真实审稿意见）

```
对比 Agent 诊断 vs 真实审稿意见：
  ├─ 共识弱点 → 标记为 must_fix（双方都指出 = 铁定存在）
  ├─ Agent 独有发现 → 标记为 likely_fix（审稿人没注意到的隐患）
  ├─ 审稿人独有意见 → 标记为 reviewer_specific（可能是审稿人偏好）
  └─ 矛盾点 → 标记为 disputed（需要用户判断）
```

#### R1.3 竞争格局更新

- 触发 `novelty-checker`：检查从被拒到现在，是否有新的竞争论文出现
- 触发 Research Frontier Check：近期前沿是否有变化
- 输出：`artifacts/competitive_update.md`

> ⚠️ 如果发现有几乎一样的新论文已发表（`overall_risk: high`），直接标记为"核心 idea 已被抢占"。

#### R1.4 差距分析报告

综合以上所有信息，生成 `artifacts/gap_analysis.md`：

```markdown
# 差距分析报告

## 原文评分
| 维度 | 当前分 | 目标分（目标 venue 中位线）| 差距 |
|------|--------|------------------------|------|
| Novelty | 5/10 | 7/10 | -2 |
| Soundness | 6/10 | 8/10 | -2 |
| ... | ... | ... | ... |

## 关键弱点分类
| 弱点 | 来源 | 可修复性 | 预估工作量 |
|------|------|---------|-----------|
| Baseline 过时 | 审稿人 + Agent 共识 | ✅ 简单补实验 | 1-2 天 |
| 核心方法缺乏理论支撑 | Agent 独有发现 | ⚠️ 需要重写 Method | 3-5 天 |
| Idea 与 [新论文X] 高度重叠 | novelty-checker | ❌ 不可修复 | N/A |

## 救治方案建议
├─ 方案 A: 修补（如果所有弱点都可修复）
│   预估工作量: X 天
│   预估最终评分: X/10
├─ 方案 B: 重做（如果核心 idea 有不可修复缺陷）
│   保留: 数据集/代码/文献基础
│   重做: idea + 实验 + 写作
└─ Agent 推荐: [A 或 B]
```

### 🔒 Stage R2: 救治决策（硬卡点）

> **Autopilot 不可跳过**。用户必须确认走修补还是重做。

展示 `gap_analysis.md`，用户选择：
- **方案 A: 修补** → 进入 Stage RA
- **方案 B: 重做** → 进入 Stage RB
- **放弃** → 终止

---

## 方案 A: 修补路线

### Stage RA1: 修改计划

基于 gap_analysis 生成 `revision_plan.md`：

```markdown
# 修改计划

## 修改项（按优先级排序）
| # | 弱点 | 修改方案 | 涉及章节 | 对应 QG |
|---|------|---------|---------|--------|
| 1 | Baseline 过时 | 补 3 个 2024 SOTA baseline | Experiments | QG4 |
| 2 | 缺消融实验 | 加 3 组消融 | Experiments | QG4 |
| 3 | Related Work 太浅 | 补 vs Closest Works 对比表 | Related Work | QG5 |
| 4 | Introduction story 弱 | SDP 辩论重写 | Introduction | QG5 |

## 用户提供的修改想法整合
[如果用户提供了想法/对话记录，在此说明如何采纳]

## Core Novelty Invariant（从原文提取）
[原文的核心创新点，修改过程中不可降级]
```

用户确认 revision_plan 后开始修改。

### Stage RA2: 执行修改

```
按 revision_plan 逐项执行：
  ├─ 需要补实验 → 触发 experiment-runner（走完整 QG3/QG4）
  ├─ 需要补文献 → 触发 literature-survey（增量 + novelty-checker 复查）
  ├─ 需要改写 → 触发 paper-writing（SDP 辩论 + 去 AI 味）
  └─ 每项修改用 \blue{} 标注
```

### Stage RA3: 终稿质量门

**全部 QG 检查，不打折扣**：
- QG4 版型感知严谨性检查（含新增实验）
- QG5 出版标准 14 项检查
- 新旧内容一致性检查（修改是否引入新矛盾）

### Stage RA4: 复审

触发 `multi-reviewer` 对修改后的论文做完整审稿：
- 对比修改前后评分变化
- 确认所有 must_fix 已解决
- 如果评分仍低于目标 venue 中位线 → 建议继续修改或转方案 B

### 🔒 最终确认（硬卡点）
展示修改前后对比 + 新的 review 评分，用户决定是否投稿。

---

## 方案 B: 重做路线

### Stage RB1: 资产继承

从原论文继承有价值的部分：

```
保留：
  ├─ corpus_ledger.json（已有的文献基础）
  ├─ evidence_graph.json（已提取的 claims）
  ├─ 实验代码（如果可复用）
  ├─ 数据集（已下载的）
  └─ 对原 idea 失败原因的分析（喂给 idea-brainstorm 避免重蹈覆辙）

不保留：
  ├─ 原 hypothesis_board.json（需要新 idea）
  ├─ 原论文草稿（需要重写）
  └─ 原实验结果（需要重做）
```

### Stage RB2+: 从 full-research-pipeline Stage 2 开始

跳过 Stage 1（文献已有），从 **Stage 2 Evidence Audit** 开始执行完整流水线：

```
Stage 2: Evidence Audit + Frontier Check（QG1）  ← 从这里开始
Stage 3: Ideate（含对原 idea 失败原因的约束）
Stage 4: JIT Deep Dive + Novelty Check
Stage 5: Build
Stage 6: Write
Stage 7: Review
Stage 8: Revise
```

**特殊约束**：在 idea-brainstorm Stage 3 中，额外注入：
- 原 idea 失败原因 → 作为 negative constraint（避免踩同样的坑）
- 用户的修改想法 → 作为 seed idea（如果有的话）
- 原审稿意见 → 作为评估 checklist

---

## 质量保证

| 保障 | 修补路线 | 重做路线 |
|------|---------|---------|
| novelty-checker 查新 | ✅ 重新跑 | ✅ |
| Core Novelty Invariant | ✅ 从原文提取 | ✅ 新生成 |
| QG3 实验设计 | ✅ 补实验必过 | ✅ |
| QG4 版型感知检查 | ✅ | ✅ |
| QG5 出版标准 | ✅ | ✅ |
| 6 审稿人复审 | ✅ 含前后对比 | ✅ |
| publishable 全链路 | ✅ | ✅ |

## 文件更新

| 文件 | 更新内容 |
|------|---------|
| `project_state.json` | `mode: "revise"`, `revise_source`, `revision_plan_path` |
| `artifacts/gap_analysis.md` | 差距分析报告 |
| `artifacts/diagnosis_review.json` | 诊断审稿结果 |
| `artifacts/competitive_update.md` | 竞争格局更新 |
| `revision_plan.md` | 修改计划（方案 A） |
