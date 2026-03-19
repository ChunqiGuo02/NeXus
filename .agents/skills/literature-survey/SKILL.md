---
name: literature-survey
description: 端到端文献综述流程：搜索→Scope Freeze→Corpus Freeze→下载→解析→证据提取→综述生成。当用户说"帮我调研/综述 XXX"、"帮我找 XXX 相关的论文"时触发。
---

# literature-survey

完整的文献综述流水线，包含人机交互卡点。

## 流程

```
用户提出 topic
  │
  ▼ Scope Freeze 卡点
  确认关键词、时间范围、排除项
  │
  ▼ Step 1: 搜索
  调用 search_papers(query, year_range, max_results=50)
  │
  ▼ Corpus Freeze 卡点
  展示去重后的文献矩阵（标题/年份/引用数/是否OA）
  用户确认后才开始下载
  │
  ▼ Step 2: 获取
  对每篇论文调用 fetch_paper(doi_or_arxiv_id)
  │
  ├─ arXiv → alphaxiv-paper-lookup 获取 Markdown
  ├─ 非 arXiv + 有 PDF → pdf-to-markdown 解析
  └─ 无法获取 → 标记 access_state + publishable，触发 Manual Fetch 卡点
  │
  ▼ Step 3: 验证引用
  对每篇论文调用 citation-verifier Skill
  │
  ▼ Step 4: 提取证据
  对每篇已解析的 Markdown 调用 claim-extractor Skill
  │
  ▼ Step 5: 生成综述
  基于 evidence_graph.json 生成结构化综述
  │
  ▼ Step 6: 更新 KG
  触发 pattern-promoter Skill（如果 claims 够多）
```

## Scope Freeze 卡点

在搜索之前，先与用户确认：
- **关键词**: 搜索用的核心词和扩展词
- **时间范围**: 如 "2020-2026"
- **语言**: en / zh / both
- **排除项**: 不想包含的主题或方向
- **预计规模**: 搜索数量（20/50/100）

将确认结果写入 `project_state.json` 的 scope 字段。

## Corpus Freeze 卡点

搜索完成后，展示文献矩阵：

| # | 标题 | 年份 | 引用 | OA | 来源 |
|---|------|------|------|----|----|
| 1 | Attention Is All You Need | 2017 | 95000 | ✅ | S2+arXiv |
| 2 | ... | ... | ... | ... | ... |

用户可以：
- 删除不需要的论文
- 手动添加 DOI/arXiv ID
- 确认后开始下载

## 综述输出格式

```markdown
# {topic} 文献综述

## 1. 研究背景
(基于 evidence_graph 中的 claims)

## 2. 主要方法
(按 method 类型的 claims 组织)

## 3. 关键发现
(按 result 类型的 claims 组织)

## 4. 现有局限
(按 limitation 类型的 claims 组织)

## 5. 未来方向
(基于 gaps 分析)

## 参考文献
(仅包含 bib/ 中验证过的引用)
```

## 搜索策略深度指导（v3）

### 关键词构造

1. **核心词 + 扩展词矩阵**：
   - 核心词：直接描述研究主题（如 "graph neural network"）
   - 方法同义词：替代叫法（如 "message passing network"）
   - 应用同义词：不同表述（如 "node classification" vs "semi-supervised learning on graphs"）
   - 跨语言：中英文分别搜索（中文学术搜索用 CNKI/万方）

2. **组合搜索模式**：
   | 搜索轮次 | 模式 | 示例 |
   |---------|------|------|
   | Round 1 | 核心方法 + 核心任务 | "contrastive learning" + "graph" |
   | Round 2 | 核心方法 + 应用领域 | "contrastive learning" + "urban computing" |
   | Round 3 | 问题描述（不含方法） | "label-efficient node classification" |
   | Round 4 | 反向搜索：领域 + "survey" OR "review" | "graph learning survey 2024" |

3. **Snowball 搜索**（引用链扩展）：
   - 对 top-5 高引论文，检查其 References 和 Cited By
   - 重点关注近 1 年的被引论文（可能是 emerging work）

### 文献质量评估标准

对每篇搜索到的论文，按以下权重评估是否纳入 corpus：

| 维度 | 权重 | 评估方法 |
|------|------|---------|
| **时效性** | 30% | 发表年份距今 ≤2 年优先；经典方法不受限 |
| **影响力** | 25% | 被引数的 percentile（同年份同领域内归一化） |
| **相关性** | 30% | 与研究主题的直接匹配度（abstract 匹配评分） |
| **方法论** | 15% | 是否提出可复现的方法 / 是否有开源代码 |

> 阈值：综合评分 < 0.4 的论文建议在 Corpus Freeze 时标记排除。

### Survey 输出质量门（v3）

`artifacts/survey.md` 生成后必须通过以下检查：

| 检查项 | 标准 | 状态 |
|--------|------|------|
| **What 问题** | survey 清晰回答了"这个领域在研究什么？" | ☐ |
| **How 方法** | survey 按方法类型（≥3 类）组织了已有工作 | ☐ |
| **Gap 缺口** | survey 明确指出 ≥2 个未解决的 gap | ☐ |
| **时间线** | survey 包含方法演进的时间线或里程碑 | ☐ |
| **定量覆盖** | survey 引用的论文 ≥ corpus 的 60% | ☐ |
| **去重验证** | 无重复引用同一论文的不同表述 | ☐ |

> 未通过 → 补充后重新生成，不允许直接进入 evidence_audit。

## 文件更新

| 文件 | 更新内容 |
|------|---------|
| `project_state.json` | scope、phase、stats |
| `corpus_ledger.json` | 所有搜索到的论文（含 access_state + publishable）|
| `evidence_graph.json` | 提取的 claims |
| `bib/verified.json` | 验证过的引用 |
| `artifacts/survey.md` | 生成的综述 |

## Pipeline Exit

完成后执行：
1. 更新 `project_state.json` 的 `current_stage`
2. **必须调用** `pipeline-orchestrator.complete_stage("survey_fetch")` 验证产出
3. 根据返回值自动进入下一阶段（evidence_audit）
