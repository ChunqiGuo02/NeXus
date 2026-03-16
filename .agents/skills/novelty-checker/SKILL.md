---
name: novelty-checker
description: 对研究 idea 进行新颖性风险评估，识别最近的 prior art 和碰撞风险。当用户选定 idea 后自动触发，或用户说"检查新颖性"、"有没有人做过"时手动触发。
---

# novelty-checker

对选定的研究 idea 进行系统性新颖性风险评估。

## 输入

- `hypothesis_board.json` 中的某个 idea
- 或用户直接描述的研究想法

## 评估框架

不做二元"新/不新"判断，而是给出风险评估报告：

### 1. Prior Art 搜索

使用 `search_papers` 工具进行多轮搜索：
1. **直接搜索**: idea 的核心关键词
2. **组合搜索**: 方法 + 应用领域
3. **反向搜索**: idea 试图解决的问题的关键词
4. **引用链搜索**: nearest prior art 的引用/被引

### 2. 碰撞风险分析

| 风险等级 | 含义 | 判定条件 |
|----------|------|---------|
| 🔴 **High** | 已有高度相似的工作 | 搜到核心方法+领域完全重合的论文 |
| 🟡 **Medium** | 有部分重叠 | 方法相同但领域不同，或领域相同但方法不同 |
| 🟢 **Low** | 搜索空间未被覆盖 | 无直接匹配，最近的 prior art 也有显著差异 |
| ⚠️ **Unknown** | 覆盖不足，无法判断 | `total_papers_scanned` 低于阈值，**禁止进入 Build 阶段** |

> ⛔ **硬门槛**：当 `total_papers_scanned < 50`（AI/ML）或 `< 30`（其他领域）时，强制返回 `overall_risk: "unknown"`，禁止自动通过。必须补充搜索范围后重新评估。

### 3. 差异化分析

对于每个找到的 prior art，明确列出：
- 与 idea 的**相同点**
- 与 idea 的**不同点**
- idea 相对的**增量贡献**

### 4. 输出报告

```json
{
  "idea_id": "idea-001",
  "overall_risk": "medium",
  "nearest_prior_art": [
    {
      "paper_id": "xxx",
      "title": "...",
      "similarity": 0.7,
      "overlap": "方法层面高度相似",
      "differentiation": "应用领域不同，且我们加入了 X 改进"
    }
  ],
  "uncovered_space": "描述 idea 中尚无人探索的具体方面",
  "recommendation": "proceed_with_differentiation | pivot | abandon",
  "suggested_pivots": ["如果需要调整，建议的方向"],
  "search_queries_used": ["搜索过的关键词列表"],
  "total_papers_scanned": 120
}
```

### 5. Novelty Risk 硬卡点 ⛔

> **Autopilot 下也不可自动跳过。**

将报告展示给用户，用户可以：
- ✅ **继续**: 接受风险，进入架构审查和实验阶段
- 🔄 **调整**: 根据 suggested_pivots 修改 idea
- ❌ **放弃**: 返回 idea-brainstorm 重新构思

**自动阻断条件**（基于输出 JSON 的 `overall_risk` 字段）：
- `overall_risk: "unknown"`（覆盖不足）→ 禁止继续，必须补充搜索
- `overall_risk: "high"`（撞车）→ 强制展示报告，即使 Autopilot 也必须等待用户确认

## 文件更新

更新 `hypothesis_board.json` 中对应 idea 的 `novelty_risk` 对象（即上方输出报告的完整 JSON，其中 `overall_risk` 字段为硬卡点依据）。
