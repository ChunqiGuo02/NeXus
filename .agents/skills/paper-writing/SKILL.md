---
name: paper-writing
description: 基于 Story Skeleton + Evidence Graph 生成学术论文草稿。支持多会议模板。当用户说"写论文"、"开始写作"、"draft paper"时触发。
---

# paper-writing

从 idea 到完整论文草稿的系统性写作流程。

## 前置条件

- `hypothesis_board.json` 中有经 novelty-checker 评估的 idea
- `evidence_graph.json` 中有充足的 claims
- `bib/verified.json` 中有验证过的引用

## 写作流程

### Step 1: Story Skeleton（写作大纲）

在动笔之前，先生成中间表示：

```json
{
  "narrative_arc": "从问题到方案到结果的叙事逻辑",
  "sections": [
    {
      "name": "Introduction",
      "goal": "本节要回答什么问题",
      "key_claims": ["claim-001", "claim-005"],
      "estimated_words": 800,
      "key_figures": ["fig1: 方法概览图"]
    },
    {
      "name": "Related Work",
      "goal": "定位本工作在领域中的位置",
      "key_claims": ["claim-010", "claim-012"],
      "categories": ["方法类别 A", "方法类别 B"],
      "estimated_words": 600
    }
  ],
  "abstract_formula": {
    "problem": "一句话描述问题",
    "gap": "一句话描述现有方法的不足",
    "method": "一句话描述我们的方法",
    "result": "一句话描述主要结果",
    "impact": "一句话描述意义"
  }
}
```

### Step 2: 逐节撰写

按 Story Skeleton 中的顺序，逐节生成 LaTeX/Markdown 内容。

**核心规则（参见 rules/evidence-discipline.md）：**
- 每个事实性句子必须挂载 evidence_graph 中的 claim
- 引用只能从 `bib/verified.json` 读取
- 不允许 LLM 凭记忆编造任何引用信息

### Step 3: 去 AI 味

对生成的草稿进行去 AI 化处理：
1. **删除**：inflated language ("groundbreaking", "revolutionary")
2. **删除**：空洞总结 ("In conclusion, it is clear that...")
3. **替换**：被动语态过度使用 → 适当使用主动语态
4. **增加**：具体数字和细节
5. **调整**：段落节奏，避免机械式 "First... Second... Third..."

### Step 4: 自检清单

| 检查项 | 标准 |
|--------|------|
| ✅ 每个引用都来自 bib/verified.json | 零编造 |
| ✅ 每个断言都挂载 evidence claim | 有据可查 |
| ✅ 无撤稿论文被引用 | citation-integrity |
| ✅ 图表有完整 caption | 可读性 |
| ✅ Notation 统一 | 一致性 |
| ✅ 页数符合目标会议要求 | 合规性 |

## 会议适配

根据目标会议调整格式和重点：

| 会议 | 页数限制 | 重点 |
|------|---------|------|
| NeurIPS | 9+引用 | novelty + significance |
| ICLR | 无硬限 | soundness + clarity |
| ICML | 8+引用 | theoretical contribution |
| ACL | 8+引用 | relevance + reproducibility |
| CVPR | 8+引用 | visual results + comparison |
| AAAI | 7+引用 | technical innovation |

## 输出

- `artifacts/draft.md`：论文草稿（Markdown）
- `artifacts/story_skeleton.json`：写作大纲
- 更新 `project_state.json` phase → "writing"
