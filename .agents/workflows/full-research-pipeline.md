---
description: 完整研究生命周期流水线：Survey → Ideate → Build → Write → Review
---

# full-research-pipeline

端到端的研究流水线，从文献调研到论文审稿。

## 使用方式

用户输入: `/full-research-pipeline "研究主题"`

## 流程

### Stage 1: Survey（文献调研）
- 触发 `literature-survey` Skill
- 等待 Scope Freeze 和 Corpus Freeze 卡点
- 产出: corpus_ledger.json + evidence_graph.json + survey.md

### Stage 2: Ideate（构思 Idea）
- 触发 `idea-brainstorm` Skill
- 基于 evidence_graph 进行缺口分析
- 等待 Idea Approval 卡点
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
- 等待 Review Arena 卡点
- 产出: artifacts/review_report.json

### Stage 7: Revise（修改）
- 根据 review 反馈，回到 Stage 5 修改
- 重复 Stage 5-6 直到用户满意

## 人机卡点总览

```
Stage 1 → [Scope Freeze] → [Corpus Freeze] → [Manual Fetch]
Stage 2 → [Idea Approval]
Stage 6 → [Review Arena]
```

## 状态追踪

所有状态记录在 `project_state.json` 中，支持断点续跑。
