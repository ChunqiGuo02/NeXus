---
description: access_state 约束策略 — 不同级别的文献允许不同的下游用法
globs: ["**/*.md", "**/*.tex", "**/*.json"]
---

# Access State Policy

## 七级状态及其下游约束

| access_state | 含义 | publishable | 允许的下游用法 |
|---|---|---|---|
| `oa_fulltext` | 公开合法全文 | ✅ true | 全文解析、引用、证据抽取、精确引用 |
| `repository_fulltext` | 仓库版本（CORE/Europe PMC）| ✅ true | 全文解析，标记来源版本 |
| `shadow_fulltext` | 影子图书馆获取 | ❌ false | 仅用于探索性推理和检索指引，**不得进入终稿引用** |
| `user_supplied_pdf` | 用户上传 | ✅ true | 全文解析，需 citation verified |
| `abstract_only` | 仅有摘要 | ❌ false | 仅可做初筛和弱信号，不可精确引用 |
| `metadata_only` | 仅标题/作者/年份 | ❌ false | 仅可做索引和候选项列表 |
| `unavailable` | 无法获取 | ❌ false | **禁止**参与强结论和精确引用 |

## 强制约束

1. `unavailable` 状态的文献**绝不允许**进入 evidence_graph 的强证据链
2. `abstract_only` 的文献只能作为"存在此方向的研究"的弱信号，不可用于支撑具体结论
3. 🚨 **Shadow 证据隔离**：`shadow_fulltext` 的文献可用于探索性阅读、推理和发现相关工作，但 **不得作为 paper-writing 阶段的可投稿证据来源**。如果某条关键 claim 仅有 shadow 来源支撑，必须寻找合法替代来源或降级为弱引用
4. 每篇文献在 corpus_ledger.json 中必须标注 `access_state` 和 `publishable`，不得留空
5. 保留 shadow 获取能力（不删除 Sci-Hub/LibGen 路径），但默认作为"非可投稿证据"处理
