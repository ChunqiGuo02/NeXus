---
description: 完整研究生命周期流水线：Survey → Ideate → Build → Write → Review。支持 Autopilot 模式。
---

# full-research-pipeline

端到端的研究流水线，从文献调研到论文审稿。支持手动和 Autopilot 两种模式。

> [!IMPORTANT]
> 本 pipeline 由 `pipeline-orchestrator` MCP server 驱动。
> 每个 stage 的进入和退出**必须**通过 `advance_pipeline()` / `complete_stage()` 调用。
> 不要自行判断当前应执行哪个 skill — 以 MCP tool 返回值为准。

## 使用方式

- 手动模式: `/full-research-pipeline "研究主题"`
- Autopilot: `/full-research-pipeline "研究主题"` 然后说 "autopilot"

## 卡点行为规范

在每个人机卡点执行以下逻辑：

```
读取 project_state.json → autopilot 字段
  ├─ autopilot=true 且非硬卡点 → 输出 1-2 行 summary → 自动继续
  ├─ autopilot=true 且是硬卡点 → 展示详情 → 等待用户确认（不可跳过）
  └─ autopilot=false           → 展示详情 → 等待用户输入

硬卡点（5 个，与 sdp-protocol / omni-orchestrator 一致）：
  1. Idea Approval
  2. Novelty Risk Gate（overall_risk: unknown/high）
  3. Architecture Approval
  4. QG3 Experimental Design
  5. Review Arena
```

用户可在任意阶段说 "autopilot" 或 "暂停" 来切换模式。

## 流程

### Stage 1: Survey（文献调研）
- 触发 `literature-survey` Skill
- 🔒 **卡点: Scope Freeze** — 确认搜索范围
- 🔒 **卡点: Corpus Freeze** — 确认论文集
- 产出: corpus_ledger.json（含 access_state + publishable） + evidence_graph.json + survey.md

### Stage 2: Evidence Audit + Frontier Check（QG1）
- 触发 `evidence-auditor` Skill（强制，非建议）
- 触发 Research Frontier Check（QG1）+ Forced Cross-Pollination
- 产出: frontier_analysis.md（含跨领域 SOTA）

### Stage 3: Ideate（构思 Idea）
- 触发 `idea-brainstorm` Skill
- Portfolio Ideation（3-4-3 风险对冲）+ ToT 三层探索 + Elo 锦标赛
- SDP 红队攻击（GPT 5.4）：8+1 维度 + 除水攻击 + Visionary Escalation（QG2）
- 🔒 **卡点: Idea Approval** — 用户选择/确认 idea
- 产出: hypothesis_board.json

### Stage 4: JIT Deep Dive + Novelty Check
- 触发 `deep-dive` Skill 对选定 idea 的 nearest_prior_art 精读 3-5 篇（跳过 idea-brainstorm 阶段已快读过的论文）
- 触发 `novelty-checker` Skill 进行风险评估
- 🔒 **卡点: Novelty Risk Gate** — `overall_risk` 为 `unknown`/`high` 时强制等待用户确认（Autopilot 不可跳过）
- 产出: artifacts/deep_dive_*.md + novelty_risk

### Stage 5: Build（实验）
- 触发 `experiment-runner` Skill
- SDP 架构审查（Opus → GPT 5.4）
- 🔒 **卡点: Architecture Approval**
- 实验设计计划 + Core Novelty Invariant 提取 + Discovery-Oriented Templates（QG3）
- 🔒 **卡点: QG3 Experimental Design Approval**
- Baseline 获取（Tier 1-4）→ 环境配置 → 代码生成 → 训练与调试（Attempt Budget + 3-Strike 熔断）
- 版型感知 QG4 严谨性检查（Type A/B/C 不同通过标准）
- 产出: experiments/ + results/ + experiment_story.md

### Stage 6: Write（写论文）
- 触发 `paper-writing` Skill
- SDP 论文辩论起草（Gemini → Opus → GPT 5.4 润色）
- QG5 出版标准检查（含 Shadow 证据过滤 + 图表标准 + Related Work 深度）
- 产出: artifacts/draft.md + references.bib

### Stage 7: Review（审稿）
- 触发 `multi-reviewer` Skill
- 6 审稿人 SDP + 交叉审核 + 拒稿信预演
- 🔒 **卡点: Review Arena** — 用户决定是否修改
- 产出: artifacts/review_report.json

### Stage 8: Revise（修改）
- 根据 review 反馈，回到 Stage 6 修改
- 轻量重审（最多 2 轮）
- 触发 `evolution-memory` 蒸馏

## 人机卡点总览

```
Stage 1 → [Scope Freeze] → [Corpus Freeze]
Stage 3 → [Idea Approval]
Stage 4 → [Novelty Risk Gate]
Stage 5 → [Architecture Approval] → [QG3 Experimental Design]
Stage 7 → [Review Arena]

Autopilot ON  → 普通卡点自动通过（以上 5 个硬卡点始终等待用户确认）
Autopilot OFF → 所有卡点均等待用户确认
```

## Autopilot 自动停止条件

即使 autopilot=true，以下情况自动暂停并通知用户：
- Review-Revise 循环超过 2 轮
- 分数未提升（连续 2 轮 delta < 0.5）
- 发现 retracted citation（安全红线）
- API 调用异常（连续 3 次失败）
- Core Novelty Invariant 3-Strike 熔断

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
