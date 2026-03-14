---
description: access_state 约束策略 — 不同级别的文献允许不同的下游用法
globs: ["**/*.md", "**/*.tex", "**/*.json"]
---

# Access State Policy

## 七级状态及其下游约束

| access_state | 含义 | 允许的下游用法 |
|---|---|---|
| `oa_fulltext` | 公开合法全文 | ✅ 全文解析、引用、证据抽取、精确引用 |
| `repository_fulltext` | 仓库版本（CORE/Europe PMC）| ✅ 全文解析，标记来源版本 |
| `shadow_fulltext` | 影子图书馆获取 | ✅ 全文解析、证据抽取；引用格式必须基于 CrossRef/OpenAlex 验证的元数据 |
| `user_supplied_pdf` | 用户上传 | ✅ 全文解析，保留来源记录 |
| `abstract_only` | 仅有摘要 | ⚠️ 仅可做初筛和弱证据总结，不可精确引用 |
| `metadata_only` | 仅标题/作者/年份 | ⚠️ 仅可做索引和候选项列表 |
| `unavailable` | 无法获取 | ❌ **禁止**参与强结论和精确引用 |

## 强制约束

1. `unavailable` 状态的文献**绝不允许**进入 evidence_graph 的强证据链
2. `abstract_only` 的文献只能作为"存在此方向的研究"的弱信号，不可用于支撑具体结论
3. `shadow_fulltext` 的文献可用于证据抽取，但 Writer 引用时**必须**使用经 CrossRef/OpenAlex 验证过的元数据
4. 每篇文献在 corpus_ledger.json 中必须标注 `access_state`，不得留空
