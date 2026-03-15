---
name: paper-writing
description: 基于 Story Skeleton + Evidence Graph 生成学术论文草稿。支持多会议模板。双模型辩论起草 + GPT 润色。当用户说"写论文"、"开始写作"、"draft paper"时触发。
---

# paper-writing

从 idea 到完整论文草稿的系统性写作流程。支持双模型辩论起草和 Overleaf 集成。

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

### Step 2: 双模型辩论起草

💡 **建议此阶段使用双模型起草**（参见 `rules/model-routing.md`）

**完整并行路径**（Antigravity 支持 subagent dispatch 时）：

```
Round 1 — 并行起草（subagent dispatch）
  ├─ Subagent-Gemini (Gemini 3.1 Pro High)
  │   → 按 Story Skeleton 逐节撰写 draft_gemini.tex
  └─ Subagent-Opus (Claude Opus 4.6 Thinking)
      → 按 Story Skeleton 逐节撰写 draft_opus.tex

Round 2 — 互相预评审
  ├─ Gemini 读 draft_opus.tex → 给出逐节评审
  └─ Opus 读 draft_gemini.tex → 给出逐节评审

Round 3 — 互相 Rebuttal + 修订
  ├─ Gemini 吸收 Opus 的合理建议修改自己的稿件
  └─ Opus 吸收 Gemini 的合理建议修改自己的稿件

Round 4 — 合并共识稿
  ├─ 共识部分 → 直接采用
  ├─ 分歧部分 → 选择论证更强的版本
  └─ 输出 draft_merged.tex

Round 5 — GPT 润色（切换到 GPT 5.4）
  → 学术风格精修 + 去 AI 味 + 术语一致性
  → 输出 draft_final.tex
```

> 自动停止：如果 Round 2 分歧 < 3 处 minor issues，跳过 Round 3 直接合并。

**降级串行路径**（Claude Code / Open Code）：

```
1. 💡 "请使用 Gemini 3.1 Pro (High) 起草第一版" → draft_a.tex
2. 💡 "请切换到 Claude Opus 4.6 起草第二版" → draft_b.tex
3. 💡 "请切换回 Gemini，对 draft_b 评审"
4. 💡 "请切换到 Opus，对 draft_a 评审"
5. 当前模型合并共识稿
6. 💡 "请切换到 GPT 5.4 润色" → draft_final.tex
```

### Section-Level 写作范式

每个 section 按以下结构化模式撰写：

**Introduction — 倒三角**：
```
¶1 大背景（领域重要性，1-2 句，避免 "In recent years..."）
¶2 具体问题（research question, 带引文）
¶3 现有方法 + gap（"However, existing methods suffer from..."）
¶4 我们的方案（一句话核心 idea + 1-2 句 how it works）
¶5 贡献列表（3-4 个具体可验证的 bullet）
¶6 [可选] 论文结构概述
```

**Related Work — 分类对比**：
```
按方法类型分 2-4 个小节
每个小节结尾必须写：
  "与上述方法不同，我们的方案 [区别点]"
引用只用 bib/verified.json
```

**Method — 形式化 + 直觉交替**：
```
1. Problem Formulation（数学定义 + notation table）
2. Overview（图引用 + 一段话概述整体方法）
3. 核心模块：直觉（为什么需要）→ 方程 → 技术细节
4. 训练目标 / 推理流程
```

**Experiments — 讲故事**：
```
1. Setup（数据集统计表 + 实现细节 + 硬件 + baseline 选择理由）
2. Main Results（"X 指标达到 Z，优于次优 N%"）
3. Ablation（每次只变一个组件，表格格式）
4. Analysis（case study + 可视化 + failure case）
5. Limitations
```

### 学科适配

| 学科 | 写作框架来源 | 重点 |
|------|------------|------|
| AI/ML | 参考 [awesome-ai-research-writing](https://github.com/Leey21/awesome-ai-research-writing) 的 prompt 集和 skills | Novelty + Reproducibility |
| Urban/Landscape/Architecture | brainstorm 阶段阅读的顶刊（如 L&UP, Cities, Nature Cities）提取写作框架 | Practical Relevance + 图面质量 |
| Geoscience | 同上，从 GRL/JGR/ERL 提取 | Data Quality + 模型验证 |
| 通用 | 上述通用 section-level 范式 | 平衡 |

> 非 AI/ML 学科的写作风格应在 deep-dive 阶段从该领域顶刊论文中总结，作为 writing_style_guide 存入 `artifacts/`。

### Step 2.5: 图表生成

**方法/架构图**（参考 [PaperBanana](https://github.com/dwzhu-pku/PaperBanana) 理念）：
```
1. 从 evidence_graph 和 deep-dive 笔记中找参考图风格
2. 用文字描述图的内容和布局
3. 用 Python (matplotlib/tikz) 或 SVG 生成
4. Critic 自检：是否 self-contained、标注是否完整
5. 迭代修改直到满意
```

**实验结果图**（从 experiment-runner 的 results/ 读取数据）：

| 图表类型 | 工具 | 输出 |
|---------|------|------|
| 训练曲线（loss/metric vs epoch） | matplotlib | PDF |
| 消融热力图 | seaborn | PDF |
| t-SNE/UMAP 可视化 | sklearn + matplotlib | PDF |
| 注意力可视化 | 从 checkpoint 提取 | PDF |

**论文表格**（LaTeX 三线表）：

```latex
\begin{table}[t]
\centering
\caption{Comparison with state-of-the-art methods on X dataset.}
\begin{tabular}{lcccc}
\toprule
Method & Metric A & Metric B & Metric C \\
\midrule
Baseline 1 & 75.2 & 82.1 & 68.5 \\
Baseline 2 & 76.8 & 83.4 & 70.2 \\
\textbf{Ours} & \textbf{79.1} & \textbf{85.7} & \textbf{73.8} \\
\bottomrule
\end{tabular}
\end{table}
```

所有图表保存到 `artifacts/figures/`。如果 Overleaf 已配置，直接保存到 Overleaf 项目的 `figures/` 目录。

### Step 3: 去 AI 味

参考 [awesome-ai-research-writing](https://github.com/Leey21/awesome-ai-research-writing) 的 de-AI prompts：

**🚫 必须删除的 AI 典型表达**：

| 原文 | 替换为 |
|------|-------|
| "In recent years" / "In the era of" | 直接切入问题 |
| "plays a crucial role" | 具体说明为什么重要 |
| "groundbreaking" / "revolutionary" | 用数据说话 |
| "It is worth noting that" | 直接写 |
| "delves into" / "shed light on" | 用具体动词 |
| "First, ... Second, ... Third, ..." 连续 | 用逻辑连接词 |
| "a myriad of" / "a plethora of" | 用 "many" 或具体数字 |

**✅ 推荐的学术表达**：
- Hedging: "We observe that..." / "Results suggest..." / "This may indicate..."
- Quantitative: "improves by 3.2% (p<0.05)" 而非 "significantly improves"
- Contrast: "Unlike [X], our approach..." / "While [X] assumes..., we..."

### Step 4: 自检清单

| 检查项 | 标准 |
|--------|------|
| ✅ 每个引用都来自 bib/verified.json | 零编造 |
| ✅ 每个断言都挂载 evidence claim | 有据可查 |
| ✅ 无撤稿论文被引用 | citation-integrity |
| ✅ 图表有完整 caption，self-contained | 可读性 |
| ✅ Notation 统一 | 一致性 |
| ✅ 页数符合目标会议要求 | 合规性 |
| ✅ 无 AI 典型表达残留 | 去 AI 味 |
| ✅ 贡献列表中的 claim 都有实验支撑 | 可验证性 |

### Step 5: LaTeX 输出

参见 `overleaf_setup.md` 了解 Overleaf 集成细节。

```
1. 根据目标会议选择 LaTeX 模板
2. 将 draft 转换为 LaTeX（或直接以 LaTeX 书写）
3. 生成 main.tex + references.bib + figures/
4. 本地有 TexLive → 自动编译
5. 有 Overleaf → 实时同步
6. 都没有 → 提示用户选择方案
```

### Step 6: Rebuttal 支持

在 multi-reviewer 给出 review 后，可触发 rebuttal 撰写：

```
输入: review_report.json + draft_final.tex
输出: rebuttal.tex

策略：
1. 按 severity 排序（must-fix 优先）
2. 每个回复：致谢 → 具体回应 → 修改位置（\blue{新增内容}）
3. 有数据支撑 → 联动 experiment-runner 做补充实验
4. 统计字数限制（ICLR 有限制）
```

## 会议适配

| 会议 | 页数限制 | 重点 |
|------|---------|------|
| NeurIPS | 9+引用 | novelty + significance |
| ICLR | 无硬限 | soundness + clarity |
| ICML | 8+引用 | theoretical contribution |
| ACL | 8+引用 | relevance + reproducibility |
| CVPR | 8+引用 | visual results + comparison |
| AAAI | 7+引用 | technical innovation |

## 输出

- `artifacts/draft_final.tex`：论文终稿（LaTeX）
- `artifacts/story_skeleton.json`：写作大纲
- `artifacts/figures/`：所有图表
- `artifacts/references.bib`：参考文献
- 更新 `project_state.json` phase → "writing"
