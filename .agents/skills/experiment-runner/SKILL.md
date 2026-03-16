---
name: experiment-runner
description: 管理实验代码的搭建、运行、结果分析。含 AI 架构审查（SDP）和 Attempt Budget 防 rabbit hole。当用户说"做实验"、"跑代码"、"build project"、"experiment"时触发。
---

# experiment-runner

管理从项目搭建到结果分析的完整实验流程。含架构 SDP 审查和 attempt budget 机制。

## 执行流程

### Step 1: 项目初始化（领域适配）

根据 `hypothesis_board.json` 中的 domain 信息选择项目模板：

**AI/ML 项目**：

```
experiments/{experiment_name}/
├── src/
│   ├── model.py          # 模型定义
│   ├── data.py           # 数据加载
│   ├── train.py          # 训练循环
│   ├── evaluate.py       # 评估脚本
│   └── utils.py          # 工具函数
├── configs/
│   └── default.yaml      # 超参数配置
├── scripts/
│   ├── run_train.sh      # 训练启动脚本
│   └── run_eval.sh       # 评估启动脚本
├── data/                 # 数据集（自动下载）
├── results/              # 实验结果
├── checkpoints/          # 模型检查点
├── attempt_log.json      # 尝试日志
└── README.md             # 实验说明
```

读取 `evolution-memory` 中的 `experiment_rules`（如有）。

### Step 1.5: 数据集自动准备

从 `hypothesis_board.json` + `configs/default.yaml` 识别所需数据集，自动匹配下载方式：

| 来源 | 适用场景 | 下载方式 |
|------|---------|---------| 
| torchvision | CIFAR, MNIST, ImageNet 等 | `torchvision.datasets` |
| HuggingFace Hub | NLP / 多模态数据集 | `datasets.load_dataset()` |
| Papers with Code | 查询任务 SOTA 数据集 + benchmark | 获取下载链接 + 评估指标 |
| Kaggle | 竞赛数据集 | `kaggle API`（需 `kaggle.json`） |
| 自定义 URL | 论文中标注的链接 | `wget` / `curl` |
| deep-dive 笔记 | 论文专属数据来源 | 从笔记中提取链接 |

下载位置根据计算环境决定：
- **本地执行** → `experiments/{name}/data/`
- **远程执行** → 直接在服务器侧下载（避免本地中转）

同时自动生成数据加载代码。

**交叉领域支持**（如 AI 方法 → 城市问题）：

```json
// hypothesis_board.json
{
  "domain": {
    "problem": "urban",
    "method": "ai_ml",
    "cross_type": "method_transfer"
  }
}
```

基于 domain 组合加载：
- **数据源**：从问题领域加载（城市数据、遥感影像等）
- **代码模板**：从方法领域加载（model.py / train.py）
- **评估指标**：双标准（ML 指标 + 领域指标）
- **Baseline**：双来源（领域传统方法 + AI 同类方法）

### Step 1.6: Baseline 获取（从 idea claims 反推）

从 `hypothesis_board.json` 的 idea claims 自动推导应该比谁：

```
输入：
  ├─ idea 的 nearest_prior_art → 我们声称改进了什么？
  ├─ evidence_graph 中同数据集+同指标的 result claims
  └─ knowledge_graph 中同 method category 的论文

输出 baseline_plan.md：
  ├─ 必选 baselines（3-5 个，从 idea claims 直接推导）
  ├─ 推荐 baselines（2-3 个，SOTA + 经典方法）
  └─ 每个 baseline 的获取方案：
      Tier 1: 有官方 repo + 预训练权重 → 直接用
      Tier 2: 有官方 repo 但需适配 → fork + 修改
      Tier 3: 无代码 → 按论文描述复现（标注 "our impl."）
      Tier 4: 只需数字 → 从论文原文引用（标注 "as reported in"）
```

用户确认 baseline 清单后继续。

### Step 1.7: 环境自动配置

**本地**：
```
conda create -n {project} python=3.x
pip install -r requirements.txt
检测 GPU → 安装对应 CUDA 版本的 PyTorch
```

**远程（AutoDL/自建服务器）**：
```
1. SSH 连接验证
2. 检测服务器 GPU 型号 + CUDA 版本
3. 自动创建 conda env + 安装依赖
4. 同步代码（rsync）
5. 验证环境（跑 sanity check）
```

### Step 1.8: 计算环境自动推荐

根据实验配置自动估算工作量，主动推荐是否使用远程服务器：

| 级别 | 条件 | 推荐 |
|------|------|------|
| 🟢 轻量 | CPU 可跑, <30min | 建议本地运行 |
| 🟡 中等 | 需 GPU, 30min-4h | ⚠️ 建议在 GPU 服务器运行 |
| 🔴 重度 | 多卡/大模型, >4h | 🚨 强烈建议远程服务器 |

远程配置支持 AutoDL（一键配置）和自建服务器。配置保存到 `project_state.json` 的 `compute_target` 字段。

### Step 1.9: AI 架构审查（SDP）

```
📊 预估消耗：Group 3 (Opus) ~3 次 + Codex 池 (GPT 5.4) ~3 次
```

在代码编写前，通过 SDP 进行架构审查。遵循 `sdp-protocol` 通用规则。

#### Round 1 — Generator（Claude Opus）输出 ADR

输出 `dialogue/adr_v1.md`，Architecture Decision Record：

```markdown
# SDP Handoff: Architecture Review
> 📋 操作：打开 Codex 插件 → 新建对话 → 粘贴本文件

## Requirements Analysis
[从 hypothesis 推导需求]

## Design Space Exploration
[备选方案 + trade-off 矩阵]

## Decision Rationale
[每个选择的理由]

## Architecture Spec
[模块/数据流/接口/目录结构]

## Assumptions & Risks
[前提假设和风险]

## 🔴 我的不确定点（3-5 个）
[最不确定的设计选择]

## 🔍 请重点审查
[最可能有问题的部分]

## ❓ 开放问题（向 Reviewer 提问）
[希望 Reviewer 回答的问题]
```

#### → 用户切换到 Codex 插件（GPT 5.4）

#### Round 2 — Reviewer（GPT 5.4）双重审查

一个 handoff 内完成两种审查：

**Part A: Process Audit（审推理过程）**

| 审查项 | 具体问题 |
|--------|---------|
| 需求完整性 | requirements 是否覆盖了 hypothesis 的所有方面？ |
| 方案遗漏 | design space 是否遗漏了重要备选方案？ |
| 推理逻辑 | rationale 是否有逻辑跳跃或循环论证？ |
| 隐含假设 | 是否有未声明的重要假设？ |

**Part B: Architecture Critique（审架构）**

| 审查项 | 具体问题 |
|--------|---------|
| 模块化 | 关注点分离合理？有无上帝模块？ |
| 数据流 | 输入到输出流转清晰？无循环依赖？ |
| 可复现性 | 符合可复现性规则？ |
| 可扩展性 | 加 ablation/换数据集的改动量可控？ |
| 反模式 | 硬编码路径、全局状态等？ |

输出 `dialogue/arch_review.md`：逐点评分 + 回答 Generator 问题 + 替代方案 + pass/revise/reject

#### → 用户切回 Antigravity（Opus）

#### Round 3 — Generator（Opus）修订

输出 `dialogue/adr_v2.md`：逐点 rebuttal + 回答 Reviewer 问题 + 修订后 ADR v2 + 变更日志

#### Round 4（仅当有 blocking issues）— 终审

→ 再切一次 GPT 确认 blocking issues 已解决

#### → Architecture Approval 卡点 ⛔

展示最终 ADR + AI 审查中修复的主要问题，用户确认后进入实验设计。

**切换次数：2-3 次**，修订循环最多 2 轮。

### Step 2.0: 实验设计计划（QG3 + Discovery-Oriented Experiments）⛔

> **写代码前必须先做实验设计，用户审批后才开始编码。** 
> *终极防平庸机制：避免所有论文都变成统一的"SOTA Beater"跑分模板。*

输出 `experimental_design.md`，首先明确**实验版型（Experiment Template）**：

| 版型 | 目标 | 核心实验类型 | 成功标志 |
|------|------|-------------|----------|
| **Type A: SOTA Beater** | 提出新方法，刷新现有 Benchmark | 主结果对比、Ablation | 定量指标压制现有 SOTA |
| **Type B: Phenomenon Discoverer** | 发现/系统性验证一个未知的宇宙规律（如 Scaling Laws） | 变量控制实验、跨尺度验证 | 规律的普适性验证，无需打擂台 |
| **Type C: Theoretic Explainer** | 解释为什么某个流行方案注定失败/起效 | 构造极端 case、数学等价性实验 | 成功用最小范例复现理论预言 |

基于选定的版型规划实验：

```markdown
# 实验设计计划

## 0. 核心创新不可降级声明 (Core Novelty Invariant)
[明确列出为了保持非平庸，即使代码跑不通也**绝对不能妥协**的 1-2 个核心技术点。如："必须使用非欧几何空间，严禁退化为欧式空间"]

## 1. Hypothesis → Experiment 映射
| Contribution Claim | 验证实验 | 对应图/表 |
|-------|---------|--------|
| "我们的方法在 X 上优于 Y" | 主结果对比实验 | Table 1 |
| "组件 A 是必要的" | 消融实验 | Table 2 |
| "方法在大规模数据上也有效" | 规模实验 | Table 3 |

## 2. 必需数据集清单
| 数据集 | 用途 | 获取方式 | 状态 |
|--------|------|---------|------|
| Dataset A | 主实验 | HuggingFace | ✅ 已下载 |
| Dataset B | 泛化测试 | 官网 URL | ❌ 未下载 |

## 3. 必需 Baseline 清单
[从 baseline_plan.md 引入]

## 4. 统计分析计划
- 使用固定种子列表 `SEEDS = [13, 42, 123]` 独立运行 ≥ 3 次，报告 mean ± std
- 统计检验：paired t-test / Wilcoxon signed-rank
- 多重比较修正：Holm-Bonferroni（当比较组数 ≥ 3 时强制）
- 显著性阈值：p < 0.05，同时报告效应量 (Effect Size: Cohen's d 或 Cliff's delta)

## 5. 公平对比协议
- 所有方法使用相同硬件、相同数据划分、相同预处理
- Baseline 超参：优先用原论文报告的超参，否则同等调参预算
- 明确记录每种方法的计算资源消耗

## 6. 负面结果预案（版型感知）
- **Type A (SOTA)**：如果提升 < 1% → 重新评估 idea 可行性
- **Type B (发现型)**：如果规律无法跨场景复现 → 重新评估实验设计
- **Type C (理论型)**：如果反例构造失败率 > 50% → 重新检查理论推导
- 通用：如果某个数据集上表现不好 → 分析原因并在论文中讨论
- 通用：如果方法完全不 work → pivot 或终止
```

用户审批 experimental_design.md 后才开始写代码。

### Step 2: 代码生成编排

根据审查通过的 ADR + experimental_design.md，按顺序生成代码：

```
2.1 生成顺序：data.py → model.py → train.py → evaluate.py
2.2 每个文件生成后立即做 unit-level sanity check
2.3 baseline 代码获取（Tier 1-4）+ 适配
2.4 全部生成后做 integration sanity check（小数据集跑 1 个 epoch）
```

- 如果项目中存在 `rules/coding-style.md`，遵循其编码规范
- 保证可复现性：固定随机种子、记录环境

### Step 3: 训练与调试（含 Attempt Budget）

#### 动态 Budget 设定

根据实验复杂度（从 Step 1.8 推断）设定 budget：

| 复杂度 | 初始实现 | 调参 | 提出方法 | 消融 |
|--------|---------|------|---------|------|
| 🟢 轻量 | ≤10 | ≤8 | ≤8 | ≤10 |
| 🟡 中等 | ≤20 | ≤12 | ≤12 | ≤15 |
| 🔴 重度 | ≤30 | ≤20 | ≤20 | ≤20 |

#### 4 阶段实验执行

**Stage 1: 初始实现**
- Baseline 复现 + 基本功能跑通
- 小数据 sanity check

**Stage 2: 超参调优**
- 从 configs/default.yaml 开始
- 系统性搜索（grid/random/bayesian）

**Stage 3: 提出方法**
- 实现论文核心创新
- A/B 对比 baseline

**Stage 4: 消融实验**
- 每行去除一个组件
- 证明每个 component 的贡献

#### Checkpoint 评估（每 5 次尝试自动触发）与核心创新熔断（3-Strike Rule）

```
判定当前 Bug 类型：
  1. 🚨 本 Bug 是否直接由《Core Novelty Invariant》引起？（例如：自定义核心公式 NaN，非欧空间投影失败）
     ├── 是 → 触发【专属 3 次微预算】(3-Strike Invariant Circuit Breaker)
     │   ├── 第一次：结合原始论文公式核对代码实现
     │   ├── 第二次：对 Invariant 进行最最小限度的边界松弛/截断保护
     │   └── 第三次修不好：💥 熔断！(触发下述强干预行为)
     └── 否 → 适用常规 Attempt Budget。继续问问题 2。

  2. 常规 Bug 或参数调优：和上次 checkpoint 相比有实质性进展吗？（Y/N）
  3. 如果 N：原因是 bug、方向问题、还是环境问题？

行为矩阵：
  ├── 💥 Invariant 3-Strike 熔断 → 强制暂停并呼叫用户 (notify_user)。输出 `Invariant_Crisis_Report.md`，包含 3 个选项供人类决策：
  │   - 选项A：人类接管修 Bug（提供思路代码）
  │   - 选项B：Pivot 彻底推翻当前 Idea（回退到 idea-brainstorm）
  │   - 选项C：授权降级（放弃核心创新，做成保底增量工作）
  ├── 常规有进展 → 继续
  ├── 常规无进展 + bug → 具体定位，不再盲改
  ├── 常规无进展 + 方向问题 → 回退到上一个工作版本，切换策略
  ├── 常规无进展 + 环境问题 → 解决环境再试
  └── 常规 budget 耗尽 → 强制暂停 + 人工卡点
```

#### 结构化 Attempt Log

每次尝试记录到 `attempt_log.json`：

```json
{
  "attempt_id": 5,
  "stage": "initial_implementation",
  "change": "改了什么",
  "result": "什么结果",
  "diagnosis": "成功/失败原因",
  "next_action": "下一步计划"
}
```

**本地执行**：小数据 sanity check → 逐步扩大规模

**远程执行**（`compute_target == "remote"` 时）：

```
启动：
  agent → rsync 同步代码
  agent → ssh "cd /project && tmux new -d -s train 'python train.py'"

监控（用户说"看看实验跑得怎么样"）：
  agent → ssh "tmux capture-pane -t train -p | tail -30"
  → 解析 loss / epoch / error 信息
  → 异常检测：包含 Error / CUDA OOM / 进程不存在

完成（用户说"实验跑完了"）：
  agent → ssh "cat results/metrics.json" → 读取指标
  agent → rsync results/ 本地 → 拉取完整结果
  agent → 继续 Step 4

异常（用户说"实验报错了"）：
  agent → ssh 读 tmux 输出 → 分析 error
  → attempt budget 内自动修复 + 重启
  → 或报告"需要你手动操作"
```

### Step 4: 结果分析与图表生成

**出图标准**（QG5 的一部分）：
- DPI ≥ 300
- 字号 ≥ 8pt
- 色盲友好配色（使用 seaborn 的 colorblind palette）
- 导出格式：PDF（矢量图）

- **对比表格**（LaTeX 三线表）：自动加粗最佳值 + 报告 mean±std
- **训练曲线**（matplotlib PDF）：双 y 轴 loss + metric
- **消融表**：LaTeX tabular 格式
- **可视化**（按需）：t-SNE/UMAP、Attention heatmap、Case study
- **图表标题自动生成**：self-contained caption
- **统计检验**：主结果必须报告 p-value 或置信区间

### Step 4.5: Experiment Story Bridge

自动生成 `experiment_story.md`，作为 paper-writing 的输入：

```markdown
# Experiment Story

## 📊 Main Results
支撑 hypothesis 的核心数据：
- vs 最强 baseline 提升 X%（统计显著，p=Y）
- 在 N 个数据集上一致胜出

## 🔬 Ablation
每个组件的贡献：
- 去掉组件 A → 性能下降 X%
- 去掉组件 B → 性能下降 Y%

## 💡 Surprising Findings
出乎意料的发现 + 假设解释

## ⚠️ Where We Don't Win
方法在哪些场景下表现不好 + 原因分析（禁止 cherry-pick）

## 📈 所有图表清单
| 图表 | 支撑的 Claim | Caption 初稿 |
|------|-------------|--------|

## 📝 Contribution-Evidence 映射
| Contribution Claim | 支撑证据（表/图） | 状态 |
|-------|---------|------|
| "我们的方法比 SOTA 好" | Table 1 + Figure 2 | ✅ |
| "组件 A 是必要的" | Table 2 | ✅ |
| [缺失] | 无 | ❌ 需要补实验 |

## 💬 建议的 Paper Narrative
基于结果推荐的 story 线
```

### Step 4.8: 实验严谨性检查 + 新颖性复查（QG4，版型感知）⛔

> **必须全部通过才能进入论文写作阶段。**

**通用检查项（所有版型必须通过）：**

| 检查项 | 标准 | 状态 |
|--------|------|------|
| 数据集数量 | ≥ 2 个数据集（ML）或 ≥ 2 个场景（非 ML） | ☐ |
| 多种子运行 | 使用 `SEEDS=[13,42,123]` 独立运行 ≥ 3 次，报告 mean ± std | ☐ |
| 统计检验 | p-value + 效应量 (Cohen's d) + 多重比较修正 (Holm-Bonferroni) | ☐ |
| 公平对比 | 同硬件、同数据划分、同预处理 | ☐ |
| 消融覆盖 | 每个新组件都有消融支撑 | ☐ |
| 全部结果报告 | 含负面结果 + failure analysis（禁止 cherry-pick） | ☐ |
| Contribution 映射 | 每个 claim → 对应表/图 | ☐ |

**版型感知 Novelty Delta Check（按 Type 分支）：**

| 版型 | 通过条件 | 失败处理 |
|------|---------|----------|
| **Type A (SOTA Beater)** | vs best baseline 提升 ≥ 1% 且统计显著 (p<0.05) | 重评 idea 或继续调试 |
| **Type B (Phenomenon Discoverer)** | 发现的规律在 ≥ 3 个尺度/场景下复现一致 | 重评实验设计，增加验证尺度 |
| **Type C (Theoretic Explainer)** | 反例构造成功率 ≥ 80% 且理论预言与实验一致 | 重评理论推导 |

> ⚠️ 不同版型使用不同的通过标准。Type B/C **不需要** SOTA 增益阈值，否则会被误杀。

### Step 5: 结果写回

- `evidence_graph.json`（新 `result` claims）
- `artifacts/experiment_report.md`
- `project_state.json` → phase: "experimenting"
- 触发 `evolution-memory` ESE/IVE 蒸馏

## 可复现性规则

| 要求 | 实现方式 |
|------|---------| 
| 随机种子固定 | 使用固定种子列表 `SEEDS = [13, 42, 123]`，每次运行使用不同种子，禁止全局单一 seed |
| 环境记录 | `pip freeze > requirements.txt` |
| 配置记录 | 每次运行保存 config snapshot（含当次使用的 seed） |
| 检查点保存 | 每 N epoch 保存 checkpoint |
| 结果版本化 | results/{timestamp}/ |

## 反直觉规则

1. **先复现 baseline，不要急着上自己的方法** — 提前发现数据/环境坑
2. **每次只改一个变量** — 改多了出错无法定位根因
3. **失败的尝试也是数据** — 记入 attempt_log，喂给 evolution-memory
4. **Budget 限制不是惩罚** — 它防止你在错误方向上浪费时间
5. **初始实现阶段不是浪费时间** — 它是最重要的阶段，跑通=成功一半
