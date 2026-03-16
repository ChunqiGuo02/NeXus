---
name: omni-orchestrator
description: Nexus 统一入口。意图识别 + 模式路由 + 首次引导 + Autopilot 模式。当用户提出任何学术研究相关请求时触发（调研、找论文、构思 idea、写论文、审稿、做实验等）。
---

# omni-orchestrator

Nexus 的总调度 Skill。负责意图识别、模式路由、首次使用引导和 Autopilot 模式管理。

## 首次使用引导

检查 `~/.nexus/global_config.json` 是否存在：
- **不存在** → 触发引导流程（见下方）
- **存在** → 直接进入意图识别

### 引导流程

```
🔬 Nexus — 首次配置

欢迎！我需要做一次简单配置（1 分钟，仅此一次）。

❶ [必填] 请提供一个邮箱（用于学术 API 访问，不会收到任何邮件）：

❷ [可选] 远程 GPU 服务器：
   — AutoDL 用户：粘贴 SSH 登录指令即可
   — 自建服务器：提供 host + user，需已配置 SSH key 免密登录

❸ [可选] 模型偏好配置（参见 rules/model-routing.md）：
   — 不同阶段使用不同模型可提升质量
   — 默认推荐：Idea→Gemini, 架构→Opus, Debug→Codex, 起草→双模型, 润色→GPT
   — 可自定义，也可稍后在 global_config.json 中修改

❹ [可选] 论文写作环境：
   — 如已有 Overleaf 账号，推荐安装 Overleaf Workshop 插件
   — 详见 paper-writing/overleaf_setup.md

✅ 配置完成后展示所有服务状态。

💡 [可选] Semantic Scholar API Key 申请链接。
```

将配置写入 `~/.nexus/global_config.json`。

## 意图识别 + 路由

| 用户意图关键词 | 路由到 | 模式 |
|--------------|--------|------|
| 调研、综述、找论文、search、survey | `literature-survey` | Survey |
| idea、想法、brainstorm、研究方向 | `idea-brainstorm` | Ideate |
| 精读、细读、分析这篇论文、deep dive | `deep-dive` | Deep Dive |
| 读论文、解析 PDF、arxiv 链接、DOI | `paper-ingestion` | 工具 |
| 检查证据质量、audit evidence | `evidence-auditor` | 工具 |
| 写论文、draft、write、paper | `paper-writing` | Write |
| 做实验、跑代码、build、experiment | `experiment-runner` | Build |
| 审稿、review、打分、评估论文质量 | `multi-reviewer` | Review |
| 修改论文、revise、被拒、resubmit、优化论文、草稿升级 | `revise-paper` workflow | Revise |
| 做PPT、做汇报、academic slides | 提示使用 `frontend-slides` skill | 工具 |
| 总结经验、保存规则、evolution memory | `evolution-memory` | 管理 |
| 追踪、monitor、跟进、新论文 | (Phase 3+) | Monitor |
| 验证引用、check citation | `citation-verifier` | 工具 |
| 查看配置/状态 | 展示当前配置和项目状态 | 管理 |
| **自动完成、全自动、autopilot、auto、vibe research、帮我搞定剩下的** | **设置 autopilot=true，继续当前 pipeline** | **Autopilot** |
| **暂停、停、我来看看、manual** | **设置 autopilot=false，恢复手动控制** | **Manual** |

## Autopilot 模式

### 开启

用户在任意阶段说 "自动完成" / "autopilot" / "vibe research" 时：

1. 将 `project_state.json` 的 `"autopilot"` 设为 `true`
2. 回复用户：

```
✅ Autopilot 已开启。后续卡点将自动通过，每个卡点仍会输出简要 summary。
随时说"暂停"可恢复手动控制。
```

3. 继续执行当前 pipeline，普通卡点自动 approve（**硬卡点仍需用户确认，见安全护栏**）

### 关闭

用户说 "暂停" / "停" / "我来看看" / "manual" 时：

1. 将 `project_state.json` 的 `"autopilot"` 设为 `false`
2. 回复用户：`⏸️ Autopilot 已暂停，恢复手动控制。`

### 安全护栏

即使 Autopilot ON，以下操作**仍需用户确认**：
- **SDP 硬卡点**：Idea 终审、Novelty Risk Gate（`overall_risk: unknown/high`）、架构终审、QG3 实验设计审批、审稿终审（见 sdp-protocol）
- 删除已有文件
- 大规模代码重构
- git commit / push / 发布
- 涉及 API 费用的大批量请求（>50 次）
- Attempt Budget 耗尽时的暂停决策

### 卡点行为

在每个人机卡点（Scope Freeze / Corpus Freeze / Idea Approval / Novelty Risk Gate / Architecture Approval / QG3 / Review Arena）：

1. 读取 `project_state.json` 的 `"autopilot"` 字段
2. **autopilot=true 且非硬卡点**：输出 1-2 行 summary → 自动继续下一步
3. **autopilot=true 且是硬卡点**：输出详情 → 等待用户确认（不可跳过）
4. **autopilot=false**（默认）：展示详情 → 等待用户确认

## 项目管理

每次对话开始时：
1. 检查是否存在进行中的项目（`workspace/*/project_state.json`）
2. 如果有，询问用户"继续之前的项目还是新建？"
3. 如果没有，根据意图创建新项目目录

### 创建新项目

```
workspace/{project_name}/
├── project_state.json    # 初始化，含 "autopilot": false
├── corpus_ledger.json    # {"entries": []}
├── evidence_graph.json   # {"claims": []}
├── knowledge_graph.json  # {"nodes": [], "edges": []}
├── hypothesis_board.json # {"hypotheses": []}
├── raw_pdfs/
├── parsed_mds/
├── artifacts/
└── bib/
```

## S2 Key 后补识别

如果用户在任何时候说以下内容，自动识别并写入配置：
- "我拿到了 Semantic Scholar key"
- "S2 key: xxx"
- "API key: xxx"

## 配置状态查询

用户说"查看配置"或"status"时，展示：
- 全局配置状态（email、S2 key、shadow 开关）
- 当前项目状态（phase、corpus 统计、**autopilot 开关**）
- 各数据源就绪状态
