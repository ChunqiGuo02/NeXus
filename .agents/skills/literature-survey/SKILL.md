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
  └─ 无法获取 → 标记 access_state，触发 Manual Fetch 卡点
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

## 文件更新

| 文件 | 更新内容 |
|------|---------|
| `project_state.json` | scope、phase、stats |
| `corpus_ledger.json` | 所有搜索到的论文（含 access_state）|
| `evidence_graph.json` | 提取的 claims |
| `bib/verified.json` | 验证过的引用 |
| `artifacts/survey.md` | 生成的综述 |
