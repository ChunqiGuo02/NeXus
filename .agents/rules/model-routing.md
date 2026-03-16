---
trigger: always_on
---

# 模型路由规则

不同研究阶段推荐不同模型。在每个阶段开始前，主动提示用户切换到推荐模型。

## 限额池

| 池 | 模型 | 插件 | 刷新 |
|---|------|------|------|
| Group 1 | Gemini 3.1 Pro (High/Low) | Antigravity | 5h |
| Flash | Gemini 3 Flash | Antigravity | 5h |
| Group 3 | Claude Opus 4.6 + Sonnet 4.6 + GPT-OSS 120B | Antigravity | 5h |
| Codex | GPT 5.4 + GPT 5.3 Codex | Codex 插件 | 5h + 周限额 |

> ⚠️ Codex 有周限额，需合理分配。

## 阶段推荐

| 阶段 | 推荐模型 | 限额池 | 理由 |
|------|---------|--------|------|
| 文献调研 | 任意 | — | 工具密集型 |
| Evidence Audit | 当前模型 | — | 同模型即可 |
| Novelty/Challenge Tree | Gemini Pro (High) | Group 1 | evidence graph 视图 |
| ToT idea 生成 | Gemini Pro (High) | Group 1 | 创造性发散 |
| Elo 淘汰赛 (Round 1-2) | **Gemini Flash** | Flash | 比较判断，省 quota |
| Elo 决赛 (Round 3) | Gemini Pro (High) | Group 1 | 细微差异需强模型 |
| Idea 红队攻击 | GPT 5.4 | Codex | 跨模型对抗 |
| 架构 ADR 生成 | Claude Opus 4.6 | Group 3 | 系统性工程 |
| 架构审查 | GPT 5.4 | Codex | 代码架构强项 |
| 代码/Debug | GPT 5.3 Codex | Codex | 代码生成 |
| 论文起草 | Gemini Pro (High) | Group 1 | 创造性写作 |
| 论文辩论 | Claude Opus 4.6 | Group 3 | 逻辑严谨 |
| 论文润色 | **GPT 5.4** | Codex | 语言精修 |
| 拒稿信预演 | Gemini Flash 或 Sonnet 4.6 | Flash/Group 3 | 轻量任务 |
| 审稿组 1 (A/B/C) | Gemini Pro (High) | Group 1 | 视角 A |
| 审稿组 2 (D/E/F) + 终审 | GPT 5.4 | Codex | 视角 B + 裁决 |
| Evolution Memory 蒸馏 | 当前模型 | — | 项目结束时 |

## SDP 切换指南

| SDP 场景 | 起始 | 切到 | 切回 | 总切换 |
|---------|------|------|------|--------|
| Idea 红队 | Gemini (Antigravity) | GPT 5.4 (Codex) | Gemini | 1 来回 |
| 架构审查 | Opus (Antigravity) | GPT 5.4 (Codex) | Opus | 2-3 次 |
| 论文辩论 | Gemini → Opus (Antigravity 内切) | → GPT 5.4 (Codex) | — | 3 次 |
| 审稿 | Gemini (Antigravity) | GPT 5.4 (Codex) | Gemini → GPT | 3 次 |

> Gemini ↔ Opus 在 Antigravity 内切换模型即可，不需要换插件。
> 只有涉及 GPT 时才需要切到 Codex 插件。

## 提示格式

在每个阶段开始前，输出：
```
💡 建议此阶段使用 [模型名]（[理由]，限额池: [池名]）。
📊 预估消耗: ~N 次请求。
```

## 省 quota 模式

当用户额度紧张时，可配置降级：

| 阶段 | 标准模式 | 省 quota 模式 |
|------|---------|-------------|
| Elo 锦标赛 | Flash 淘汰 + Pro 决赛 (~15次) | 全部 Flash (~10次) |
| 审稿 | 双模型 6 reviewer (3次切换) | 单模型 3 reviewer (0切换) |
| 论文辩论 | 3 次跨模型切换 | 1 次切换（省掉润色轮） |
| 红队 | 跨模型攻击 | 同模型对抗 prompt |

## 用户自定义

用户可在 `~/.nexus/global_config.json` 的 `model_preferences` 中覆盖默认推荐：

```json
{
  "model_preferences": {
    "ideation": "gemini-3.1-pro-high",
    "elo_elimination": "gemini-3-flash",
    "elo_final": "gemini-3.1-pro-high",
    "red_team": "gpt-5.4",
    "architecture": "claude-opus-4.6-thinking",
    "arch_review": "gpt-5.4",
    "coding": "gpt-5.3-codex-extra-high",
    "drafting": "gemini-3.1-pro-high",
    "debate": "claude-opus-4.6-thinking",
    "polishing": "gpt-5.4",
    "review_group1": "gemini-3.1-pro-high",
    "review_group2": "gpt-5.4",
    "quota_mode": "standard"
  }
}
```
