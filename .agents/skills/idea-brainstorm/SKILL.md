---
name: idea-brainstorm
description: 基于 Evidence Graph + Knowledge Graph 进行学术 idea 构思与评估。双速阅读策略（JIT 深读核心论文）。当用户说"帮我想 idea"、"brainstorm"、"研究方向"、"有什么可以做的"时触发。
---

# idea-brainstorm

基于已有证据和知识图谱，系统性地构思研究 idea。

## 前置条件

- `evidence_graph.json` 中至少有 10 条 claims（来自 literature-survey）
- 如果 `knowledge_graph.json` 有数据，优先利用

## 执行流程

### Step 1: 缺口分析（Gap Analysis）

扫描 evidence_graph 和 knowledge_graph，识别以下 5 类缺口：

| 缺口类型 | 检测方法 | 示例 |
|----------|---------|------|
| **方法缺口** | KG 中 method A 用于 domain X 但未用于 domain Y | "Attention 用于 NLP 但未用于城市规划" |
| **矛盾缺口** | evidence_graph 中相互矛盾的 claims | "论文 A 说 X 有效，论文 B 说 X 无效" |
| **规模缺口** | result claims 仅在小规模验证 | "仅在 CIFAR-10 验证，未在 ImageNet 测试" |
| **时序缺口** | 方法提出超过 N 年但无后续改进 | "2019 提出以来无人改进" |
| **跨域缺口** | KG 中两个不相关领域有相似 pattern | "气候模型和金融时序都用 LSTM" |

### Step 2: Idea 生成

对每个识别到的缺口，生成 1-3 个 candidate ideas。每个 idea 包含：

```json
{
  "id": "idea-001",
  "title": "简明标题",
  "description": "一段话描述核心创新点",
  "gap_type": "方法缺口",
  "source_claims": ["claim-001", "claim-015"],
  "expected_contribution": "学术/工程/理论层面的预期贡献",
  "nearest_prior_art": ["paper-id-1", "paper-id-2"],
  "feasibility": "high | medium | low",
  "risk_notes": "潜在风险和挑战"
}
```

### Step 3: 双速阅读（JIT Deep Read）

对每个 idea 的 `nearest_prior_art`：
1. 检查是否已有 claim-extractor 的详细 claims
2. 如果没有，触发 deep-dive Skill 对核心 1-3 篇做精读
3. 精读后重新评估 idea 的可行性

### Step 4: Idea Approval 卡点

将所有 candidate ideas 以表格形式展示给用户：

| # | Title | Gap Type | Feasibility | Risk |
|---|-------|----------|-------------|------|
| 1 | ... | 方法缺口 | High | ... |

用户选择感兴趣的 idea → 写入 `hypothesis_board.json`

## 触发 Novelty Check

用户选定 idea 后，自动触发 `novelty-checker` Skill 进行深度新颖性评估。

## 文件更新

| 文件 | 更新内容 |
|------|---------|
| `hypothesis_board.json` | 写入选定的 idea |
| `evidence_graph.json` | JIT 精读产生的新 claims |
| `project_state.json` | phase → "ideation" |
