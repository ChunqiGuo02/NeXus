---
name: feishu-notify
description: 飞书/Lark 通知集成。在 pipeline 关键节点向飞书群推送富文本卡片，支持 Push（单向通知）和 Interactive（双向审批）两种模式。当用户配置了飞书通知时自动触发。
---

# feishu-notify

## 概述

在研究 pipeline 的关键节点向飞书/Lark 推送通知卡片。
- **Push 模式**：单向推送状态卡片（实验完成、审稿分数、pipeline 进度）
- **Interactive 模式**：通过 OpenClaw 飞书插件实现双向审批（卡点等待用户在飞书上确认）

未配置飞书时，所有通知行为自动跳过，零副作用。

## 配置

在 `~/.nexus/global_config.json` 中添加：

### Push 模式（推荐，5 分钟配置）

```json
{
  "feishu": {
    "mode": "push",
    "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_ID"
  }
}
```

### Interactive 模式（需 OpenClaw 飞书插件）

```json
{
  "feishu": {
    "mode": "interactive",
    "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_ID"
  }
}
```

## 通知时机

以下节点触发通知：

| 事件 | 卡片标题 | 模式 |
|------|---------|------|
| Survey 完成 | 📚 Survey Done: {n} papers found | Push |
| Scope Freeze 等待 | 🔒 Scope Freeze: confirm search scope | Interactive |
| Corpus Freeze 等待 | 🔒 Corpus Freeze: confirm paper set | Interactive |
| Idea 生成完毕 | 💡 {n} Ideas Generated | Push |
| Idea Approval 等待 | 🔒 Idea Approval: select idea | Interactive |
| Novelty Check 完成 | 🔍 Novelty Check: risk={level} | Push |
| 实验完成 | 🧪 Experiment Done: {metric} | Push |
| 论文草稿完成 | 📝 Draft Ready: {sections} sections | Push |
| Review 完成 | 👥 Review Score: {score}/10 | Push |
| Review Arena 等待 | 🔒 Review Arena: revise or accept? | Interactive |
| Pipeline 完成 | ✅ Pipeline Complete | Push |
| 安全暂停 | ⚠️ Auto-paused: {reason} | Push |
| 错误 | ❌ Error: {message} | Push |

## 发送通知的方法

### Push 模式

Agent 在对应节点执行 shell 命令发送 webhook：

```bash
curl -s -X POST "WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "msg_type": "interactive",
    "card": {
      "header": {
        "title": {"tag": "plain_text", "content": "📚 Nexus: Survey Done"},
        "template": "blue"
      },
      "elements": [{
        "tag": "markdown",
        "content": "**Project:** {project_name}\n**Papers found:** {count}\n**Top sources:** S2, arXiv, CrossRef"
      }]
    }
  }'
```

### Interactive 模式

OpenClaw 飞书插件原生处理双向消息：

1. 发送带按钮的卡片（[通过] [调整] [暂停]）
2. 用户在飞书上点击或回复，OpenClaw 直接将指令传回 agent
3. 超时（5 分钟）则按 autopilot 设置决定：autopilot=true → 自动通过，autopilot=false → 暂停等待

## 卡片颜色

| 颜色 | 用途 | template 值 |
|------|------|-------------|
| 🔵 蓝色 | 信息/进度 | `blue` |
| 🟢 绿色 | 成功/完成 | `green` |
| 🔴 红色 | 错误/暂停 | `red` |
| 🟠 橙色 | 等待决策 | `orange` |

## 判断逻辑

```
读取 ~/.nexus/global_config.json → feishu 字段
  ├─ 不存在 → 跳过通知，正常执行
  ├─ mode="push" → 发送 webhook 卡片，不等待
  └─ mode="interactive" → 通过 OpenClaw 发送卡片 + 等待用户响应
```

## 飞书配置

### Push 模式（5 分钟）

1. 打开飞书群 → 群设置 → 机器人 → 添加机器人 → 自定义机器人
2. 起名（如 "Nexus Research Bot"）
3. 安全设置：添加关键词 `Nexus`
4. 复制 Webhook URL 到 `global_config.json`

### Interactive 模式（10-15 分钟）

1. 安装 [OpenClaw 飞书官方插件](https://openclaw.ai)
2. 创建飞书应用，开启 Bot 能力
3. 配置权限：`im:message`, `im:message:send_as_bot`
4. 启用事件订阅：`im.message.receive_v1`
5. 在 OpenClaw 中关联飞书应用凭证
