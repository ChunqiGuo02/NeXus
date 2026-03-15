---
description: 完整研究生命周期流水线：Survey → Ideate → Build → Write → Review。支持 Autopilot 模式。
---

# full-research-pipeline

端到端的研究流水线，从文献调研到论文审稿。支持手动和 Autopilot 两种模式。

## 使用方式

- 手动模式: `/full-research-pipeline "研究主题"`
- Autopilot: `/full-research-pipeline "研究主题"` 然后说 "autopilot"

## 卡点行为规范

在每个人机卡点执行以下逻辑：

```
读取 project_state.json → autopilot 字段
  ├─ autopilot=true  → 输出 1-2 行 summary → 自动继续
  └─ autopilot=false → 展示详情 → 等待用户输入
```

用户可在任意阶段说 "autopilot" 或 "暂停" 来切换模式。

## 流程

### Stage 1: Survey（文献调研）
- 触发 `literature-survey` Skill
- 🔒 **卡点: Scope Freeze** — 确认搜索范围
- 🔒 **卡点: Corpus Freeze** — 确认论文集
- 产出: corpus_ledger.json + evidence_graph.json + survey.md

### Stage 2: Ideate（构思 Idea）
- 触发 `idea-brainstorm` Skill
- 基于 evidence_graph 进行缺口分析
- 🔒 **卡点: Idea Approval** — 用户选择/确认 idea
- 自动触发 `novelty-checker`
- 产出: hypothesis_board.json（含 novelty_risk）

### Stage 3: Deep Dive（精读关键论文）
- 触发 `deep-dive` Skill
- 对 idea 的 nearest_prior_art 精读 3-5 篇
- 产出: artifacts/deep_dive_*.md

### Stage 4: Build（实验）
- 触发 `experiment-runner` Skill
- 搭建项目 → 训练 → 分析结果
- 产出: experiments/ + results/

### Stage 5: Write（写论文）
- 触发 `paper-writing` Skill
- Story Skeleton → 逐节撰写 → 去 AI 味
- 产出: artifacts/draft.md

### Stage 6: Review（审稿）
- 触发 `multi-reviewer` Skill
- 4 角色审稿 + Anchor 校准
- 🔒 **卡点: Review Arena** — 用户决定是否修改
- 产出: artifacts/review_report.json

### Stage 7: Revise（修改）
- 根据 review 反馈，回到 Stage 5 修改
- 重复 Stage 5-6 直到用户满意（或 autopilot 下达到 2 轮自动停止）

## 人机卡点总览

```
Stage 1 → [Scope Freeze] → [Corpus Freeze]
Stage 2 → [Idea Approval]
Stage 6 → [Review Arena]

Autopilot ON  → 自动通过，输出 summary
Autopilot OFF → 等待用户确认
```

## Autopilot 自动停止条件

即使 autopilot=true，以下情况自动暂停并通知用户：
- Review-Revise 循环超过 2 轮
- 分数未提升（连续 2 轮 delta < 0.5）
- 发现 retracted citation（安全红线）
- API 调用异常（连续 3 次失败）

## 状态追踪

所有状态记录在 `project_state.json` 中，支持断点续跑。

```json
{
  "project_name": "...",
  "current_stage": "survey",
  "autopilot": false,
  "checkpoints_passed": [],
  "created_at": "...",
  "updated_at": "..."
}
```
