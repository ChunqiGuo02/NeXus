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
