---
name: paper-writing
description: 基于 Story Skeleton + Evidence Graph 生成学术论文草稿。SDP 双模型辩论起草 + GPT 5.4 润色 + 审后修改循环。当用户说"写论文"、"开始写作"、"draft paper"时触发。
---

# paper-writing

从 idea 到完整论文草稿的系统性写作流程。采用 SDP 双模型辩论起草、GPT 5.4 润色和 Overleaf 集成。

读取 `evolution-memory` 中的 `writing_rules`（如有）。

## 前置条件

- `hypothesis_board.json` 中有经 novelty-checker 评估的 idea
- `evidence_graph.json` 中有充足的 claims
- `bib/verified.json` 中有验证过的引用
- `experiment_story.md`（来自 experiment-runner Step 4.5）— 结果、图表、narrative 建议

## 写作流程

### Step 1: Story Skeleton（写作大纲 + v2.2 说服力层）

在动笔之前，先生成中间表示：

```json
{
  "one_sentence_summary": "用一句话（≤30 词）概括论文的核心贡献。如果写不出来，论文缺焦点。",
  "positioning": "来自 venue_fit_report.md 的定位策略（method/empirical/theory/...）",
  "narrative_arc": "从问题到方案到结果的叙事逻辑",
  "sections": [
    {
      "name": "Introduction",
      "goal": "本节要回答什么问题",
      "key_claims": ["claim-001", "claim-005"],
      "estimated_words": 800,
      "key_figures": ["fig1: 方法概览图"],
      "transition_to_next": "本节结尾如何自然引出 Related Work"
    }
  ],
  "abstract_formula": {
    "problem": "一句话描述问题",
    "gap": "一句话描述现有方法的不足",
    "method": "一句话描述我们的方法",
    "result": "一句话描述主要结果",
    "impact": "一句话描述意义"
  },
  "weakness_preemption": [
    {
      "attack": "审稿人可能说：只在 2 个数据集上做了实验",
      "defense": "Section 4.3 展示了 5 个数据集的结果 + Appendix B 有更多",
      "embed_in_section": "Experiments"
    },
    {
      "attack": "审稿人可能说：方法复杂度太高",
      "defense": "Table 3 展示了与 baseline 相同量级的 FLOPs",
      "embed_in_section": "Experiments"
    }
  ],
  "significance_argument": "解决这个问题对领域的意义是什么？",
  "figure1_spec": "Figure 1 应该展示什么，确保自解释核心 idea"
}
```

#### One-Sentence Summary Test (v2.2)

**强制要求**：在 Story Skeleton 完成后，用一句话（≤30 个英文词）总结论文贡献。

- 这句话必须同时出现在 Abstract 第一句和 Introduction 最后一段
- 如果写不出来 → 论文缺焦点，需要回到 ideation 重新聚焦
- 好例子：*"We show that simple data augmentation closes 80% of the gap between supervised and self-supervised learning on ImageNet."*
- 坏例子：*"We propose a novel framework for improved performance."*

#### Weakness Preemption Plan (v2.2)

**在动笔之前**列出 top-5 审稿人可能的攻击点，并为每个攻击点准备预防性论述：

1. 从 `venue_fit_report.md` 的 "预期审稿问题" 中提取 top-5
2. 为每个攻击点写一句话的预防性回答
3. 标注这个防御应该嵌入论文的哪个 section
4. 写作时自然地融入（不能显得是在辩解）

> 最好的论文让审稿人觉得 "我想质疑的点他都解释了"。

#### Narrative Momentum Requirements (v2.2)

写作时每个 section 的段落之间必须有**因果推进**：

- Introduction 的每一段比前一段更具体（大问题 → 具体 gap → 我们的方案）
- Method 的每个子节由前一个子节暴露的问题驱动
- Experiment 的顺序回答读者在读完 Method 后**自然产生的问题**
- Related Work 的每个子类结尾**必须**写 "与上述方法不同，我们..."

每个 section 的最后一句应该**自然引出**下一个 section 的动机。

#### Figure 1 Quality Gate (v2.2)

Figure 1（方法概览图）是审稿人的第一印象。要求：

1. **自解释**：不读正文即可理解核心 idea
2. **30 秒测试**：新读者看 30 秒能说出 "这个方法做了什么"
3. 包含：输入 → 核心处理 → 输出 的完整流程
4. 标注清晰，字号 ≥ 8pt
5. 如果是对比方法，用 (a) existing vs (b) ours 的并列结构

#### Rebuttal-Ready Appendix (v2.2)

论文写的时候就为 rebuttal 做准备：

1. 对 weakness_preemption 中的每个攻击点，在 Appendix 中预备：
   - 补充实验（更多数据集 / 更多 baseline / 参数敏感性）
   - 更详细的推导或解释
   - Failure case 分析
2. 正文中用 "See Appendix X for details" 引出
3. 当审稿人说 "你没有做 X" → 立刻指向 "Appendix C 已有"

#### Insight Density Check (IDC)（v4 新增）

**写完每个 section 后必须检查 insight 密度**。逐段扫描，每段必须包含 ≥1 个 insight marker：

| Marker 类型 | 识别信号 | 示例 |
|------------|---------|------|
| 📊 **定量分析** | 数字、百分比、趋势 | "reduces error by 23%" |
| 🔍 **因果解释** | because, due to, caused by | "This is because X fails when..." |
| ⚡ **对比/类比** | unlike X, in contrast to | "Unlike GCN, our method preserves..." |
| 💡 **非显然观察** | surprisingly, counter-intuitively | "Surprisingly, removing X improves..." |
| 🧩 **深层联系** | 联系更广泛规律 | "This connects to the broader principle of..." |

**Insight Desert 检测**（连续空洞段落）：

| 位置 | 条件 | 处理 |
|------|------|------|
| Introduction | 连续 ≥2 段无 insight marker | 🔴 必须重写 |
| Method | 连续 ≥2 段无 insight marker | 🔴 必须补充 motivation |
| Experiments | 连续 ≥3 段无 insight marker | 🟡 补充分析后继续 |

**典型 Insight Desert（workshop 级写法）**：
> "Deep learning has achieved remarkable success. Recently, GNNs have become popular. We propose a novel method..."

**修复后（顶会级写法）**：
> "Message-passing GNNs provably cannot distinguish k-WL-indistinguishable graphs (Xu et al., 2019). We observe that 73% of failure cases trace back to this ceiling (Table 1), motivating our approach..."

#### Motivation-First Rule（v4 强制）

Method section 中每个公式/算法/架构组件前**必须有 ≥1 句 motivation** 回答"为什么需要这个"。

- ❌ 错误：`"We define the loss function as: L = ..."`
- ✅ 正确：`"Standard CE ignores hierarchical structure, treating cat→dog the same as cat→car. To inject this structure, we define: L = ..."`

检查方法：对每个 `\begin{equation}` / `\begin{algorithm}`,检查前 2 句是否含 motivation 关键词
（"because", "to address", "motivated by", "to handle", "this enables"）。

#### Experiment Story Arc（v4 强制结构）

Experiment section 必须遵循以下叙事弧线：

| 段落 | 标题模板 | 内容 | 必需 |
|------|---------|------|------|
| §1 | Setup | 数据集 + baseline + 评价指标 + 实现细节 | ✅ |
| §2 | Main Results | 主实验表 + 核心发现 | ✅ |
| §3 | **Why It Works** | Ablation + 组件分析 + 关键设计的 justify | ✅ |
| §4 | **Deep Analysis** | Case study / Error analysis / Visualization | ✅ |
| §5 | **When It Fails** | Failure cases + Limitation 分析 | ✅ |
| §6 | Efficiency | FLOPs / Memory / Training time 对比 | ⚠️ 建议 |
| §7 | Sensitivity | 超参数 / 数据量 / 噪声的 robustness | ⚠️ 建议 |

> ⛔ 没有 "Why It Works" → 审稿人会问方法为什么 work
> ⛔ 没有 "When It Fails" → 审稿人认为你在隐藏弱点
> **Workshop 论文 = 只有 §1+§2；顶会论文 = §1-§5 全覆盖**

### Step 1.5: Exemplar Analysis (v2)

1. Find 3 similar oral/spotlight papers from target venue (last 2 years)
2. Analyze: Intro structure, Method intuition-to-formal ratio, Experiment storyline
3. Save to `artifacts/exemplar_analysis.md`
4. Use as style reference for each section

> Novice mode: MANDATORY. Expert mode: recommended.

### Step 2: SDP 双模型辩论起草

```
📊 预估消耗：Group 1 (Gemini) ~5 次 + Group 3 (Opus) ~3 次 + Codex (GPT 5.4) ~3 次
```

遵循 `sdp-protocol` 通用规则。切换 3 次（→Opus →回 Gemini →GPT 5.4 润色）。

**Round 1 — Model A（Gemini Pro）起草**

输出 `dialogue/draft_a.tex` + `dialogue/draft_a_meta.md`：

```
├── 完整论文草稿 draft_a.tex（按 Story Skeleton 逐节撰写）
├── 写作决策日志（为什么这样组织 story / 选论据）
├── 🔴 自评薄弱环节（最弱 section + 原因）
└── 📌 用户偏好和约束
```

**→ 用户切换到 Opus（Antigravity 内切模型即可）**

**Round 2 — Model B（Opus）评审 + 改写最弱部分**

```
├── 逐 section 深度评审（每节 strengths + weaknesses）
├── 最弱 section 的替代版本（直接给改写稿）
├── Story 层面建议（narrative arc 说服力）
└── 具体语言/逻辑改进建议
```

**→ 用户切回 Gemini**

**Round 3 — Model A（Gemini）整合终稿**

```
├── 合并 best of both（标注哪部分来自哪个模型）
├── 终稿 draft_merged.tex
└── 合并决策日志
```

**→ 用户切换到 Codex 插件（GPT 5.4）**

**Round 4 — GPT 5.4 润色**

```
├── 学术风格精修 + 去 AI 味 + 术语一致性
└── 输出 draft_final.tex
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

**Related Work — 分类对比 + 深度定位**：
```
按方法类型分 2-4 个小节
每个小节结尾必须写：
  "与上述方法不同，我们的方案 [区别点]"
引用只用 bib/verified.json

❗ 必须包含 "vs Closest Works" 深度对比表：
| 方法 | 关键差异 | 我们的优势 |
|------|---------|----------|
| ClosestWork A | 假设 X... | 我们不需要 X |
| ClosestWork B | 只处理 Y... | 我们处理 Y+Z |
```

> 这不是引用堆砌，是方法论级别的对比。审稿人最满意这种写法。

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

### Step 4: 出版标准检查（QG5）

| 检查项 | 标准 |
|--------|------|
| ✅ 每个引用都来自 bib/verified.json | 零编造 |
| ✅ 每个断言都挂载 evidence claim | 有据可查 |
| ✅ 无撤稿论文被引用 | citation-integrity |
| 🚨 **所有终稿引用的 claim 必须来自 `publishable=true` 的来源** | Shadow 隔离 |
| ✅ 图表有完整 caption，self-contained | 可读性 |
| ✅ 图表 DPI ≥ 300，字号 ≥ 8pt，色盲友好 | 专业度 |
| ✅ Notation 统一 | 一致性 |
| ✅ 页数符合目标会议要求 | 合规性 |
| ✅ 无 AI 典型表达残留 | 去 AI 味 |
| ✅ 贡献列表中的 claim 都有实验支撑 | 可验证性 |
| ✅ Related Work 含 vs Closest Works 深度对比 | 定位深度 |
| ✅ Significance argument 明确 | 回答 "so what?" |
| ✅ Limitations section 完整 | 诚实报告 |

**Supplementary Material checklist**（附录应包含）：
- 详细数学推导（如有）
- 完整超参数表
- 额外实验结果（正文放不下的）
- 代码可用性声明

### Step 4.5: Claims-Paper Cross-Validation (v2)

For every assertive statement in draft_final.tex:
1. Match to claim in evidence_graph.json
2. No match = unsupported claim (fix or remove)
3. publishable=false source = shadow source leak
4. Check claim STRENGTH matches evidence STRENGTH (prevent overclaiming)
5. Verify each Contribution bullet has corresponding section/experiment

### Step 4.7: Fresh Eyes Test (v2)

With a NEW LLM context (no prior history), read only Introduction + Abstract:
1. Ask: What problem? Core contribution? Why important?
2. If unclear -> rewrite Introduction
3. Novice mode: MANDATORY.

### Step 5: LaTeX 编译流水线

参见 `overleaf_setup.md` 了解完整环境配置，`venue_templates.md` 了解模板注册表。

#### 5.1 环境检测
```bash
pdflatex --version    # 检查 TexLive
latexmk --version     # 检查自动编译工具
code --list-extensions | grep latex   # 检查 VS Code 插件
```
→ 根据检测结果建议安装缺失组件（见 overleaf_setup.md Step 0）

#### 5.2 模板自动获取
```
读取 project_state.json → target_venue
  ├─ 查 venue_templates.md 注册表 → 命中 → git clone / wget 下载
  ├─ 未命中 → 搜索 Overleaf Gallery → "{venue} {year} template"
  ├─ 仍未找到 → 识别出版商 → 下载通用模板（elsarticle/acmart/IEEEtran）
  └─ 兜底 → article.cls + 提示用户手动提供
```

#### 5.3 项目初始化
```
paper/
├── main.tex              ← 从模板生成
├── references.bib        ← 从 bib/verified.json 转换（仅 publishable=true 来源）
├── figures/              ← 从 artifacts/figures/ 复制
├── sections/             ← 可选，按节拆分
├── .latexmkrc            ← 自动编译配置
└── .vscode/settings.json ← LaTeX Workshop recipe 配置
```

#### 5.4 本地编译
```bash
latexmk -pdf -interaction=nonstopmode -synctex=1 main.tex
```
→ LaTeX Workshop 保存时自动触发 → PDF Tab 实时刷新 → SyncTeX 双向跳转

#### 5.5 编译错误自动修复
```
解析 main.log:
  ├─ 缺少宏包 → tlmgr install <pkg> → 重编译
  ├─ 引用未定义 → bibtex + pdflatex ×2
  ├─ 图片路径错误 → 修正路径 → 重编译
  └─ 致命错误 → 展示给用户（最多 3 次重试）
```

#### 5.6 Overleaf 同步（如已配置）
```
Overleaf Workshop 插件 → 双向实时同步
  ├─ 本地编辑 → 自动上传到 Overleaf
  ├─ 导师在 Overleaf 修改 → 自动拉取到本地
  └─ 冲突 → 默认 Use Local（除非导师正在审阅）
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

### Step 7: 论文修改（审后）

按 `review_report.json` 中的 `revision_roadmap` 逐项修改：

```
├── must_fix 全部修改（不改就 reject）
├── nice_to_have 选择性修改
├── 修改部分用 \blue{} 标注
├── 每处修改旁标注对应的 reviewer 和 issue 编号
└── 输出 draft_revised.tex
```

### Step 8: 轻量重审（确认修改质量）

只审查修改过的部分（非全文重审）：

```
├── 对照 must_fix 清单逐项确认
├── 检查修改是否引入新问题
├── 判定：
│   ├── 所有 must_fix 已解决 → ✅ 完成
│   └── 仍有未解决 → 🔄 再修改一轮（最多 2 轮）
└── 输出最终版 draft_final_revised.tex
```

触发 `evolution-memory` 写作规则蒸馏。

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

## 反直觉规则

1. **先写 Method，最后写 Introduction** — 先确定方法再讲故事
2. **先写你的拒稿信** — 在写 Introduction 前，列出 3 个审稿人可能攻击的弱点
3. **Underclaim in prose, overdeliver in evidence** — 文字谦虚，数据说话
4. **不要追求完美初稿** — 第一版的目的是给辩论提供靶子
5. **Related Work 不是引用堆砌** — 每类方法结尾必须写"我们的区别"

### Step 8.5: Reproducibility Checklist (v2)

Auto-generate venue-format checklist from experiment metadata:
- Seeds, hardware, training time, optimizer, batch size
- Code/data availability statement
- Output: `artifacts/reproducibility_checklist.md`

## Pipeline Exit

完成后执行：
1. 更新 `project_state.json` 的 `current_stage`
2. **必须调用** `pipeline-orchestrator.complete_stage("writing")` 验证产出
3. 根据返回值自动进入下一阶段（`review_round1` 第 1 轮审稿）

---

## Domain Taste 集成

在写作前，**必须**读取以下文件（由 `domain_calibration` stage 自动生成）:
- `artifacts/domain_taste_profile.json` → 写作规则和结构标准
- `artifacts/exemplar_structures.json` → elite 论文的段落结构模板

### 校准规则

1. **结构校准**: 每写完一个 section，对比 exemplar_structures.json:
   - 段落数达到 elite 平均的 80%？
   - 词数达到 elite 平均的 70%？
   - 低于 → 补充内容后才继续下一 section

2. **质量阈值动态加载**: quality_engine 的检查阈值从 domain_taste 读取:
   - insight_density 阈值 = elite 值 × 0.7
   - intro 最少段数 = elite 值 × 0.8
   - 图表最少数 = elite 值 × 0.7

3. **实验深度强制**: domain_taste 中 elite% > 70% 的实验类型为 **MANDATORY**:
   - 例: has_ablation elite%=100 → ablation 必须做
   - 例: has_failure_analysis elite%=62 → 不强制但强烈建议

4. **Baseline 完整性**: 检查论文是否提到了 `must_have_baselines` 中的所有 baseline

