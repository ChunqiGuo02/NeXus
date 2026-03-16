---
name: claim-extractor
description: 从论文 Markdown 中提取结构化证据卡片（claim + exact_quote + source），构建 Evidence Graph。当需要分析论文内容、提取关键发现、或为写作准备证据时触发。
---

# claim-extractor

从解析后的论文 Markdown 中提取结构化的证据卡片，写入 evidence_graph.json。

## 输入

- 一篇已解析的 Markdown 文件（来自 `parsed_mds/`）
- 对应的 `corpus_ledger.json` 条目（获取 paper_id）

## 输出

更新 `evidence_graph.json`，新增一组 claims。

## 提取规范

对于每篇论文，提取以下类型的 claims：

### claim_type（断言类型）

| 类型 | 示例 |
|------|------|
| `result` | "Multi-head attention 在 ImageNet 上超过 CNN baseline 2.3%" |
| `method` | "我们使用了 scaled dot-product attention 机制" |
| `limitation` | "该方法在小数据集上表现不佳" |
| `hypothesis` | "我们假设 attention 可以完全替代卷积" |
| `observation` | "训练过程中发现 attention heads 存在冗余" |

### 每条 claim 的必填字段

```json
{
  "id": "claim-{自增编号}",
  "paper_id": "{corpus_ledger 中的 id}",
  "section": "论文章节 (如 3.2 Method)",
  "page": null,
  "exact_quote": "原文精确引用（英文或中文）",
  "claim_text": "用中文简明概括此 claim",
  "claim_type": "result | method | limitation | hypothesis | observation",
  "evidence_type": "support | oppose | limitation | neutral",
  "access_state": "从 corpus_ledger 继承的 access_state",
  "publishable": "从 corpus_ledger 继承的 publishable 布尔值",
  "verified": true,
  "extracted_at": "ISO 时间戳"
}
```

## 执行步骤

1. **读取 Markdown 文件**
2. **按章节扫描**，提取每个章节中的关键断言
3. **对每个断言**：
   - 找到原文精确引用（exact_quote）
   - 判断 claim_type 和 evidence_type
   - 生成 claim_text（中文简明概括）
4. **追加写入** `evidence_graph.json` 的 claims 数组
5. **更新** `project_state.json` 的 stats.claims_count

## 质量要求

- 每篇论文通常提取 5-20 条 claims
- exact_quote 必须是**原文照抄**，不得意译
- 避免提取过于泛泛的陈述（如"深度学习很重要"）
- 优先提取有数据支撑的 result 和明确的 limitation

## 遵守规则

严格遵守 `rules/evidence-discipline.md`。
