---
name: idea-brainstorm
description: 基于 Evidence Graph + Knowledge Graph 进行学术 idea 构思与评估。双阶段流程：Phase 1 用 ToT 思维树系统性探索，Phase 2 用 SDP 跨模型红队攻击。当用户说"帮我想 idea"、"brainstorm"、"研究方向"、"有什么可以做的"时触发。
---

# idea-brainstorm

基于已有证据和知识图谱，系统性地构思研究 idea。采用 ToT 探索广度 + SDP 评估深度双层保障。

> 参考：Yao et al., "Tree of Thoughts: Deliberate Problem Solving with Large Language Models"

## 前置条件

- `evidence_graph.json` 中至少有 10 条 claims（来自 literature-survey）
- 如果 `knowledge_graph.json` 有数据，优先利用
- 建议先运行 `evidence-auditor` 确保证据质量
- 读取 `evolution-memory` 中的 `idea_rules`（如有）

## 执行流程

### Step 0: Research Frontier Check（QG1）

在做 gap analysis 之前，先确保我们对**研究前沿**有准确理解：

1. 从 evidence_graph 中筛选**近 6 个月**的高影响力论文（高被引 / 高关注）
2. 识别 **emerging trends**（近期出现的新方法、新范式、新数据集）
3. 🌀 **Forced Cross-Pollination（强制跨界授粉）**：
   - 强制搜索并提取 3-5 篇与当前领域**看似毫不相关但具备底层启发性**的跨领域 SOTA（例如：做城市热岛效应时，强制引入因果推断、流体力学或图神经网络的顶级论文）。
   - 目的：打破本领域的信息茧房，为范式转换提供外部弹药。
4. 检查是否有**预印本**（arXiv 近 3 个月）可能和我们的方向重叠
5. 输出 `frontier_analysis.md`：
   - 领域当前 SOTA 是什么？
   - 近 6 个月最重要的 3-5 篇论文改变了什么？
   - 领域正在往哪个方向发展？
   - ⚠️ 有哪些近期预印本可能和我们撞车？

> 目的：防止基于过时理解产出 idea，导致"别人 3 个月前已经做了"。

### Step 1: 缺口分析 + 研究图谱生成

#### 1.1 Gap Analysis

扫描 evidence_graph 和 knowledge_graph（结合 Step 0 的 frontier analysis），识别以下 5 类缺口：

| 缺口类型 | 检测方法 | 示例 |
|----------|---------|------|
| **方法缺口** | KG 中 method A 用于 domain X 但未用于 domain Y | "Attention 用于 NLP 但未用于城市规划" |
| **矛盾缺口** | evidence_graph 中相互矛盾的 claims | "论文 A 说 X 有效，论文 B 说 X 无效" |
| **规模缺口** | result claims 仅在小规模验证 | "仅在 CIFAR-10 验证，未在 ImageNet 测试" |
| **时序缺口** | 方法提出超过 N 年但无后续改进 | "2019 提出以来无人改进" |
| **跨域缺口** | KG 中两个不相关领域有相似 pattern | "气候模型和金融时序都用 LSTM" |

#### 1.2 Novelty Tree 视图（从 evidence_graph 生成）

从 evidence graph 构建方法演进时间线：

```
Root: [研究主题]
├── 2020: Method A（paper_001）→ 改进了 X
│   ├── 2021: Method A+ (paper_005) → 加了 Y
│   └── 2022: Method A-lite (paper_012) → 轻量化
├── 2021: Method B（paper_008）→ 新范式
│   └── 2023: [Gap] 无后续改进
└── 2023: Method C（paper_020）→ 当前 SOTA
```

#### 1.3 Challenge-Insight Tree 视图（从 knowledge_graph 生成）

从 knowledge graph 构建问题层次：

```
Challenge: [核心挑战]
├── Sub-challenge 1
│   ├── Insight: 论文 X 发现...
│   ├── Insight: 论文 Y 发现...
│   └── [Gap]: 尚无人从 Z 角度研究
├── Sub-challenge 2
│   └── Insight: ...
└── Sub-challenge 3 [未被充分研究]
```

这两棵树作为 Step 2 ToT 的输入，提供研究全景视角。

### Step 2: ToT 思维树探索（Phase 1 — 同模型 Gemini Pro）

```
📊 预估消耗：Group 1 (Gemini Pro) ~5 次 + Flash 池 ~10 次
```

#### 2.1 思维分解 (Thought Decomposition)

将"从 gap 到 idea"分解为 3 层：
- **L1 研究方向**：哪个 gap 值得做？（从 Step 1 的 gap 列表中选）
- **L2 方法路线**：用什么方法填这个 gap？
- **L3 具体 idea**：方法 + 领域 + 创新点的完整方案

#### 2.2 思维生成 (Thought Generation)

使用 Independent Sampling（Gemini Pro），强制使用**"构思风险对冲"（Portfolio Ideation）**策略，按风险和收益分配 3 个梯队的 idea：

- **Tier 1: Safe & Solid (30% 比例)**
  - 基于 Gap-filling（如 A方法+B应用），强调可行性和工程落地。要求数学推导严密，保证能中会议保底。
- **Tier 2: Ambitious (40% 比例)**
  - 基于 Forced Cross-Pollination。将不相关领域的前沿技术以非平凡（non-trivial）的方式引入本领域。
- **Tier 3: Paradigm Shift (30% 比例)**
  - 终极突破视角：包含 *第一性原理回归*、*矛盾大一统*、*荒谬假设打破*。风险极高，但一旦成功可冲击顶刊/Best Paper。

生成规格：
- 结合你的计算和领域限制，生成 ~18-30 个横跨 3 个 Tier 的 candidate ideas。

每个 L3 idea 输出结构化 JSON：

```json
{
  "id": "idea-001",
  "title": "简明标题",
  "tier": "Tier1_Safe | Tier2_Ambitious | Tier3_ParadigmShift",
  "description": "一段话描述核心创新点",
  "gap_type": "方法缺口等",
  "thought_path": "L1: [方向] → L2: [路线] → L3: [方案]",
  "theoretical_grounding": "支撑这个 idea 最核心的一个数学定理/物理定律/核心公式是什么？（防止纯空想）",
  "falsification_condition": "什么样的明确实验结果可以证明这个 idea 是彻底错误的？（可证伪性）",
  "compute_feasibility": "能否在现有的 N 张 GPU 上在 3 天内完成验证？如果不能，如何下采样？",
  "contribution_type": "new_method | new_formulation | new_benchmark",
  "expected_delta": "vs current SOTA 的预期提升幅度和依据",
  "significance_argument": "谁受益？解决了什么实际问题？为什么现在做？"
}
```

#### 2.3 Elo 锦标赛排名（替代 beam search）

**淘汰赛 Round 1-2**（Gemini Flash — 省 quota）：
- 30 candidates × Swiss-system pairing
- 每次对比 4 维度：novelty / feasibility / relevance / impact
- 批量对比（一次请求对比 3-5 对）
- 淘汰至 top-8

**决赛 Round 3**（Gemini Pro — 保质量）：
- top-8 互比，差异细微，需要强模型
- 最终输出 Elo 排名 top-5

#### 2.4 输出 ToT 存活列表

输出到 `dialogue/tot_survivors.md`：
- 5 个经过 Elo 排名存活的高质量 ideas
- 每个 idea 的完整推理路径（L1→L2→L3）和 Elo 分数
- 被淘汰的 ideas 列表（供红队参考是否有错误淘汰）

### Step 3: SDP 跨模型红队攻击（Phase 2）

```
📊 预估消耗：Codex 池 (GPT 5.4) ~5 次
```

遵循 `sdp-protocol` SKILL 的通用规则。

#### Round 1 — 蓝队（Gemini）打包

输出 `dialogue/ideas_v1.md`（SDP handoff 格式）：

```markdown
# SDP Handoff: Idea Red Team
> 📋 操作：打开 Codex 插件 → 新建对话 → 粘贴本文件

## 5 个 ToT 存活 Ideas
[每个 idea 的 JSON + 推理路径 + Elo 分数]

## 核心假设（显式列出）
[每个 idea 的关键假设]

## 被淘汰的 ideas 摘要
[供红队检查是否有误淘汰]

## 🔴 我认为最可能的风险点
[Generator 主动暴露弱点]

## ❓ 我不确定的点
[开放问题]

## 📌 用户偏好和约束
[从对话中提取的用户偏好]
```

#### → 用户切换到 Codex 插件（GPT 5.4）

#### Round 2 — 红队（GPT 5.4）攻击

读取 `ideas_v1.md`，输出 `dialogue/red_team_report.md`：

对每个 idea 做 **8+1 维度攻击**（QG2 Significance Bar）：
- **假设攻击**：核心假设的反例/反证
- **Baseline 攻击**：有没有更简单的方法达到类似效果？
- **实验攻击**：最可能的失败模式是什么？
- **规模攻击**：能否 scale？换更大数据集还成立吗？
- **Story 攻击**：contribution 够不够一篇论文？
- **增量性检测**：预期提升 `expected_delta` 够大吗？0.5% 的提升不值得做
- **贡献类型审查**：`contribution_type` 是否足够有分量？纯 application 需要有深度 insight
- 🚫 **除水攻击 (Bullshit Detection)**：该想法是否在"吹牛逼"？它是否违反了已知的数学、物理约束或算力极其不现实？`theoretical_grounding` 是否只是胡乱拼凑名词？如果能轻易找到反例，直接 Kill。
- **剪枝审查**：检查 ToT 是否错误淘汰了有价值的 idea

🚀 **必答题：Visionary Escalation（远景拔高攻击）**
- 对于活下来的 Tier 1/Tier 2 idea，红队必须提供拔高方案："怎么将它的雄心（Ambition）放大 10 倍，使之具备拿 Best Paper 的潜质？"

每个 idea 判定：
- survive ✅ — 贡献类型清晰 + 预期增量显著 + 可行
- wounded 🟡 — 需要加强某方面
- killed ❌ — incremental / 不可行 / 已有类似工作
- **magnitude_warning ⚠️** — 预期增量太小，建议放弃或 pivot 到更大的贡献

#### → 用户切回 Antigravity（Gemini）

#### Round 3 — 蓝队（Gemini）回应 + 修订

输出 `dialogue/ideas_v2.md`：
- 逐点 rebuttal（反驳/接受红队意见 + 理由）
- survive ✅ → 保留
- wounded 🟡 → 修订加强（吸收红队建议）
- killed ❌ → 放弃或 pivot
- 被红队建议复活的已淘汰 idea → 重新评估
- 最终 ideas 列表（含战损率）

### Step 4: 双速阅读（JIT Quick Read，仅用于红队前加固）

对最终 ideas 的 `nearest_prior_art`：
1. 检查是否已有 claim-extractor 的详细 claims
2. 如果没有，做快速摘要级阅读（不触发 deep-dive Skill）
3. 快读后重新评估 idea 可行性

> 注意：正式精读在 pipeline Stage 4（Idea Approval 之后）执行，此处仅为快速校验。

### Step 5: Idea Approval 卡点 ⛔

> **Autopilot 硬卡点** — 必须用户确认

将最终 ideas 以表格展示给用户：

| # | Title | Gap Type | Elo Rank | 红队判定 | Feasibility |
|---|-------|----------|----------|---------|-------------|
| 1 | ... | 方法缺口 | #1 | ✅ survive | High |

用户选择感兴趣的 idea → 写入 `hypothesis_board.json`

## 触发后续

- 选定 idea 后 → 自动触发 `novelty-checker`
- 全流程完成后 → 触发 `evolution-memory` IDE 蒸馏

## 文件更新

| 文件 | 更新内容 |
|------|---------| 
| `hypothesis_board.json` | 写入选定的 idea |
| `evidence_graph.json` | Quick Read 校验发现的补充 claims（如有） |
| `project_state.json` | phase → "ideation" |
| `dialogue/tot_survivors.md` | ToT 存活列表 |
| `dialogue/ideas_v1.md` | 蓝队 handoff |
| `dialogue/red_team_report.md` | 红队报告 |
| `dialogue/ideas_v2.md` | 修订后 ideas |

## 反直觉规则

1. **数量优先于质量** — 先生成 30 个再筛选，不要精挑细选 3 个
2. **被 kill 的 idea 不一定是坏 idea** — 可能只是当前条件不成熟，记入 evolution-memory
3. **最好的 idea 往往不是排名第一的** — Elo 排名是参考，用户直觉同样重要
4. **跨域缺口比方法缺口更有潜力** — 但也更难验证，需要更仔细的可行性评估
5. **不要过度防御** — 红队的 suggestion 可以拒绝，但 blocking issue 必须正面回应
