---
description: 证据纪律 — 无证据挂载的断言不得写入终稿
globs: ["**/*.md", "**/*.tex", "**/*.json"]
---

# Evidence Discipline Rule

## 核心原则

**终稿中的每一个事实性断言，都必须有 evidence_graph.json 中的 claim 作为支撑。**

## 强制约束

1. **证据挂载**: 写入终稿的每个事实性句子（非常识）必须关联至少一条 `evidence_graph.json` 中的 claim
2. **精确引用**: claim 必须包含 `exact_quote`（原文精确引用），不得使用 LLM 意译替代
3. **来源溯源**: 每条 claim 必须标注 `paper_id`（对应 corpus_ledger 中的条目）和 `section`
4. **无证据标红**: 如果一个断言找不到对应的 evidence claim，必须标记为 `[NEEDS_EVIDENCE]` 并在交付前补充或删除
5. **证据类型标注**: 每条 claim 必须标注 `claim_type`（result/method/limitation/hypothesis/observation）和 `evidence_type`（support/oppose/limitation/neutral）
6. 🚨 **可投稿来源约束**: 终稿中引用的每条 claim 必须来自 `publishable=true` 的来源（即 `oa_fulltext`、`repository_fulltext` 或 `user_supplied_pdf`）。`shadow_fulltext`、`abstract_only`、`metadata_only` 来源的 claim **不得**作为终稿证据

## 适用范围

此规则适用于 paper-writing Skill 的所有输出，包括综述、论文草稿、Related Work 等。不适用于 brainstorm 阶段的探索性讨论。
