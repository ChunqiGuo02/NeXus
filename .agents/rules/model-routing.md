---
trigger: always_on
---

# 模型路由规则

不同研究阶段推荐不同模型。在每个阶段开始前，主动提示用户切换到推荐模型。

## 阶段推荐

| 阶段 | 推荐模型 | 理由 | 建议设置 |
|------|---------|------|---------|
| 文献调研 | 任意 | 以工具调用为主，模型差异不大 | — |
| Idea 构思 | Gemini 3.1 Pro (High) | 创造性推理、多角度发散 | thinking: high |
| 架构设计/搭建 | Claude Opus 4.6 Thinking | 长上下文、系统性工程 | planning: ON |
| 代码/Debug | GPT-5.3-codex Extra High | 代码理解+生成 | planning: ON |
| 论文起草 | **双模型辩论** | Gemini + Opus 各起草一版 → 互评 → 共识 → GPT 润色 | — |
| 论文润色 | GPT 5.4 | 语言精细度、学术风格 | — |
| 审稿 | **混合多模型** | 不同模型模拟不同审稿人 | — |

## 论文起草：双模型辩论流程

见 `paper-writing/SKILL.md` Step 2。两条路径：
- **Antigravity**：subagent 并行 dispatch 指定不同模型，全自动
- **Claude Code / Open Code**：串行 + `💡` 提示切换模型，半自动

## 审稿多模型

| 角色 | 推荐模型 | 优势 |
|------|---------|------|
| Reviewer A（严格型） | Claude Opus 4.6 Thinking | 发现逻辑漏洞 |
| Reviewer B（创新型） | Gemini 3.1 Pro (High) | 跨领域联想 |
| Reviewer C（读者型） | GPT 5.4 | 语言细节 |
| Meta Reviewer | 用户默认模型 | 综合裁决 |

## 提示格式

在每个阶段开始前，输出一行提示：
```
💡 建议此阶段使用 [模型名]（[理由]）。如需帮助切换，请告诉我。
```

## 用户自定义

用户可在 `~/.nexus/global_config.json` 的 `model_preferences` 中覆盖默认推荐：

```json
{
  "model_preferences": {
    "ideation": "gemini-3.1-pro-high",
    "architecture": "claude-opus-4.6-thinking",
    "coding": "gpt-5.3-codex-extra-high",
    "drafting_a": "gemini-3.1-pro-high",
    "drafting_b": "claude-opus-4.6-thinking",
    "polishing": "gpt-5.4",
    "review_strict": "claude-opus-4.6-thinking",
    "review_creative": "gemini-3.1-pro-high",
    "review_reader": "gpt-5.4"
  }
}
```

首次引导时提醒用户配置。
