---
name: sdp-protocol
description: Structured Dialogue Protocol — 跨模型深度协作的通用规则、handoff 模板和安全护栏。当需要跨模型审查、辩论或对抗时触发。
---

# Structured Dialogue Protocol (SDP)

借鉴学术同行评审的跨模型协作协议。每轮通信达到评审级深度，而非简单信息传递。

## When to Use

- 需要不同模型审查同一产出（idea / 架构 / 论文）
- 需要对抗性评估（红队 / 拒稿信预演）
- 任何 Generator → Reviewer → Rebuttal 的流程

## 核心规则

### 1. Generator 必须暴露弱点
每个 Generator 输出必须包含：
- 🔴 **我认为最可能的风险点**（主动暴露，不藏着）
- ❓ **我不确定的点**（开放问题，向 Reviewer 求教）
- 🔍 **请重点审查**（最可能有问题的部分）

### 2. Reviewer 必须逐点回应
- 对 Generator 提出的每个 🔴/❓/🔍 **必须给出明确回应**
- 区分 `blocking issue`（必须改）和 `suggestion`（可以不改）
- Generator 的 Rebuttal 可以**拒绝 suggestion**（标注理由即可）

### 3. Handoff 文件是完整上下文
- 新模型**必须在新对话中**读取 handoff 文件执行任务
- 不要在已有的代码调试或其他对话中执行 SDP 任务
- 每个 handoff 明确标注"本步骤仅需读取此文件 + [指定背景文件]"

### 4. Autopilot 安全护栏
以下 **5 个硬卡点**不允许 autopilot 自动通过，必须回到用户确认：
1. **Idea 终审**：红队攻击后的最终 ideas 列表
2. **Novelty Risk Gate**：`overall_risk` 为 `unknown` 或 `high` 时强制暂停
3. **架构终审**：ADR 审查修订后的最终架构
4. **QG3 实验设计审批**：实验设计计划（含版型选择）
5. **审稿终审**：6 审稿人交叉审核后的最终判定

其他所有步骤可以 autopilot（但留审计日志）。

## 三层降级策略

| 优先级 | 方式 | 条件 |
|--------|------|------|
| 1 | **MCP API 调用** | 用户配置了 API key |
| 2 | **SDP 文件交接**（手动切换） | 默认方式 |
| 3 | **同模型对抗 prompt** | 只有一个模型可用时 |

## SDP 执行模式（v3）

Pipeline 首次 SDP 时询问用户偏好，记入 `project_state.json` 的 `sdp_mode`。后续所有 SDP 阶段统一使用该模式。

| 模式 | 条件 | 切换次数 | 质量 |
|------|------|---------|------|
| **Full SDP** | 用户愿意手动切换 | 3-4 次/stage | ★★★★★ |
| **Lite SDP** | 用户嫌切换麻烦 | 1 次/stage | ★★★★☆ |
| **Same-Model Adversarial** | 只有 1 个模型可用 | 0 次 | ★★★☆☆ |

### Full SDP（默认）

完整的 Generator → Reviewer → Rebuttal → 终审 流程。参见各 SKILL 的具体 Round 描述。

### Lite SDP

仅保留**最关键的 1 次跨模型交互**：

| 阶段 | Lite 保留的交互 | 跳过的交互 |
|------|----------------|----------|
| Idea 红队 | GPT 红队攻击（Round 2） | 蓝队 rebuttal（Round 3 由同模型完成） |
| 架构审查 | GPT 审查（Round 2） | 终审（由同模型完成修订） |
| 论文写作 | GPT 润色（Round 4） | Opus 评审（Round 2 由同模型完成） |
| 审稿 | GPT 交叉审核（Round 2） | Round 3/4（综合由同模型完成） |

每个阶段的 Lite 模式 handoff 模板追加 `[LITE MODE]` 标记，提醒目标模型需在单次交互中完成审查 + 建议。

### Same-Model Adversarial

完全不切换，用**对抗 prompt** 模拟跨模型效果：

```
现在请你切换到「严格审稿人」角色。忘记你之前帮我写的所有内容。
你的目标是找出尽可能多的问题。假设你是一个想 reject 这篇论文的 reviewer。
不要对我客气。不要说「不错但可以改进」——直接指出致命缺陷。
至少列出 5 个 blocking issues。
```

> ⚠️ Same-Model 模式下，审稿和红队的有效性会降低（约 60-70% 的 Full SDP 质量）。
> 建议仅在额度紧张或用户明确要求时使用。

## Handoff 文件模板

所有 handoff 文件统一存放 `workspace/{project}/dialogue/`。

### 通用 Header

```markdown
# SDP Handoff: [任务名]
> 📋 **操作指引**：
> 1. 打开 [目标插件] → **新建对话**（不要在已有对话中执行）
> 2. 将本文件内容粘贴给 [目标模型]
> 3. [目标模型] 完成后，将输出保存到 `dialogue/[output_filename].md`
> 4. 切回 [原插件]，告诉 Agent "审查完成"

## 背景上下文
[仅包含本步骤需要的最小上下文]

## 任务
[具体的 Reviewer/Generator 指令]

## 输入文件
- 本文件
- [其他必需文件路径]（⚠️ 除列出的文件外，不要读取其他 dialogue/ 文件）
```

### Quota 预估模板

每个 skill 启动 SDP 前显示：

```
📊 本阶段预估消耗：
  - [模型A] 请求: ~N 次（限额池: [池名]）
  - [模型B] 请求: ~M 次（限额池: [池名]）
  
⚠️ 额度紧张时可选：
  ├── [降级选项1]
  └── [降级选项2]
```

## 上下文污染防护

1. 每个 handoff 文件自包含——不依赖对话历史
2. Generator 在 handoff 中增加 `📌 用户偏好和约束` section——显式记录所有不成文约束
3. 被剪掉/killed 的内容标注排除原因——防止后续模型重复讨论
4. 每阶段完成后归档旧 handoff：`dialogue/archive/`
