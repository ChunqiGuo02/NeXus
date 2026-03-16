---
name: evidence-auditor
description: 对 evidence_graph.json 中的 claims 进行抽样审计，验证准确性。在 idea 构思前自动触发，或用户说"检查证据质量"时触发。
---

# Evidence Auditor

对 evidence graph 中的 claims 进行随机抽样审计，回溯原文验证准确性，确保 idea 生成建立在可靠的证据基础上。

## When to Use

- Idea 构思前自动触发（作为 idea-brainstorm 的前置步骤）
- 用户说"检查证据质量" / "audit evidence"
- 新增大量文献后

## Workflow

### Step 1: 抽样策略

从 `workspace/{project}/evidence_graph.json` 中按影响力抽样：

1. **高优先级**：被多个 idea/gap 引用的 claims（高扇出节点）
2. **中优先级**：支撑关键 gap 的 claims
3. **低优先级**：随机抽样

抽样数量：min(总 claims 的 20%, 15 条)

### Step 2: 回溯验证

对每条抽中的 claim：

1. 找到原始来源：`parsed_mds/{paper_id}.md` 中的对应段落
2. 对比 claim 与原文：
   - 数字是否准确？
   - 结论是否被过度简化或歪曲？
   - 因果关系是否正确？
   - 条件和限定词是否保留？

### Step 3: 输出审计报告

输出到 `workspace/{project}/evidence_audit.md`：

```markdown
# Evidence Audit Report
Date: [日期]
Sample Size: [N] / [总数]

## 审计结果

| Claim ID | Claim 摘要 | 来源论文 | 判定 | 说明 |
|----------|-----------|---------|------|------|
| c_001 | "Method X improves Y by 15%" | paper_123 | ✅ verified | 原文匹配 |
| c_002 | "Dataset Z has 10K samples" | paper_456 | ⚠️ imprecise | 原文说"约10K"，实际 9.8K |
| c_003 | "Approach A outperforms all..." | paper_789 | ❌ inaccurate | 原文有限定条件"在X场景下" |

## 统计
- ✅ Verified: N (X%)
- ⚠️ Imprecise: N (X%)
- ❌ Inaccurate: N (X%)

## 建议修正
[对 inaccurate claims 的具体修正建议]
```

### Step 4: 处理结果

- ✅ verified → 无需操作
- ⚠️ imprecise → 建议修正措辞，标记到 evidence_graph
- ❌ inaccurate → **必须修正或删除**，受影响的 gap/idea 需重新评估

## 反直觉规则

1. **抽检比全检更有效** — 全检容易走马观花，抽检能深入每条 claim
2. **高引用 claim 更可能出错** — 被反复引用时容易变形，优先抽检
3. **"大家都引用"不等于"大家都对"** — 经典误引比你想象的多
