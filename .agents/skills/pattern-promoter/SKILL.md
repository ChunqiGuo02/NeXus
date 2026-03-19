---
name: pattern-promoter
description: 从 Evidence Graph 中自动识别高频 claim，提升为 Knowledge Graph 节点。实现渐进式 KG 构建，零冷启动。当 evidence_graph.json 中 claims 达到阈值时自动触发，或用户要求构建领域知识图谱时触发。
---

# pattern-promoter

扫描 evidence_graph.json，将高频出现的 claim 模式提升为 knowledge_graph.json 中的 Pattern/Method/Idea 节点。

## 触发条件

- evidence_graph.json 中新增 claims ≥ 10 条
- 用户明确要求"构建/更新知识图谱"

## 执行步骤

1. **读取** `evidence_graph.json` 全部 claims
2. **聚类分析**：
   - 按 claim_text 语义相似度聚类
   - 统计每个聚类的出现频率（跨多少篇论文）
3. **提升规则**：
   - 频率 ≥ 3（至少 3 篇论文提到）→ 提升为 KG 节点
   - 类型映射：
     - `method` claims → KG `method` 节点
     - `result` + `observation` claims → KG `finding` 节点
     - 多篇论文共同使用的方法组合 → KG `pattern` 节点
4. **构建边**：
   - 比较同一论文中的多个 methods → `builds_on` 边
   - 不同论文中解决同一问题的不同方法 → `alternative_to` 边
   - 后续论文改进前期方法 → `improves_upon` 边
5. **写入** `knowledge_graph.json`
   - 不覆盖已有节点，只追加或更新 frequency
   - 记录 `source_claims` 列表便于溯源

## 输出格式

```json
{
  "nodes": [{
    "id": "pattern-001",
    "type": "method",
    "label": "Multi-Head Self-Attention",
    "description": "并行多头注意力机制",
    "source_claims": ["claim-001", "claim-015", "claim-042"],
    "frequency": 12,
    "promoted_at": "2026-03-14T19:00:00Z"
  }],
  "edges": [{
    "source": "pattern-001",
    "target": "pattern-003",
    "relation": "improves_upon"
  }]
}
```

## 与 Idea2Paper 的区别

Idea2Paper 需要预构建 KG（ICLR/NeurIPS 数据集），冷启动成本高。
本 Skill 从用户自己的 Evidence Graph 中自然生长 KG，**零冷启动、自动覆盖用户研究的领域**。

## Pipeline 集成

此 skill 在 `survey_fetch` 阶段末尾自动触发（当 claims 数达到阈值时）。
不独立占用 pipeline stage，不需要调用 `complete_stage()`。
