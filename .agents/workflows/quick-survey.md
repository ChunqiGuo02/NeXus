---
description: 快速文献调研流程：搜索 → 过滤 → 生成简要综述
---

# quick-survey

快速文献调研，当用户只需要快速了解某个话题的现状时使用。

## 使用方式

用户输入: `/quick-survey "关键词"`

## 与 literature-survey 的区别

| 维度 | quick-survey | literature-survey |
|------|-------------|-------------------|
| 耗时 | 1-3 分钟 | 10-30 分钟 |
| 规模 | 10-20 篇 | 40-100 篇 |
| 深度 | 标题 + 摘要 | 全文解析 + 证据提取 |
| 卡点 | 无 | Scope / Corpus Freeze |
| 输出 | 简要综述 | 完整综述 + evidence_graph |

## 流程

// turbo-all

1. 调用 `search_papers(query, max_results=20, sort_by="citation_count")`
2. 按引用数排序，取 Top 10
3. 读取每篇论文的标题 + 摘要
4. 生成 1-2 页的简要综述，包含：
   - 领域概览（2-3 段）
   - 主要方法分类
   - 关键论文列表（带引用数）
   - 建议深入阅读的 3 篇
5. 输出到 `artifacts/quick_survey_{topic}.md`
