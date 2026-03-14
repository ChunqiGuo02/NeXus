---
description: 引用真实性铁律 — 每条引用必须经过多源交叉核验
globs: ["**/*.md", "**/*.tex", "**/*.json"]
---

# Citation Integrity Rule

## 核心原则

**绝不允许出现未经验证的引用。**

## 强制约束

1. **多源核验**: 每条引用必须经 CrossRef + Semantic Scholar + OpenAlex 至少**两源**确认
2. **撤稿检查**: 写入终稿前必须检查 `is_retracted` 状态，已撤稿论文**禁止引用**
3. **Writer 只读 bib/**: paper-writing Skill 只能从 `bib/` 目录读取验证过的 CSL-JSON/BibTeX，**禁止**自行编造作者、标题、年份、DOI
4. **元数据来源**: 引用的作者/标题/年份/venue 必须来自 `verify_citation` 返回的 `verified_metadata`，不得使用 LLM 记忆
5. **不一致处理**: 若多源元数据存在不一致（`discrepancies` 非空），必须人工确认后才可引用

## 违反后果

违反上述任何一条规则的引用，必须标记为 `[UNVERIFIED]` 并在交付前移除或更正。
