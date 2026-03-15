---
name: overleaf-setup
description: Overleaf + VS Code + TexLive 集成指南。论文写作阶段自动检测并引导配置。
---

# Overleaf 集成指南

## 推荐配置

```
本地 VS Code
  ├─ Overleaf Workshop 插件（cookie 登录 → 双向实时同步）
  ├─ LaTeX Workshop 插件（本地编译 + PDF 预览 + SyncTeX）
  └─ TexLive / MikTeX（本地 LaTeX 引擎，可选）
         ↕ 实时双向同步
Overleaf 网页端
  ├─ 模板社区（NeurIPS/ICLR/ICML 等会议模板）
  ├─ 协作（导师/合作者在线修改）
  └─ 备份（云端版本历史）
```

## 配置档次

| 方案 | 需要什么 | 本地编译 | 云端编译 | 导师协作 |
|------|---------|:---:|:---:|:---:|
| **最省事** | 只装 Overleaf Workshop | ❌ | ✅ | ✅ |
| **离线可用** | Overleaf Workshop + TexLive + LaTeX Workshop | ✅ | ✅ | ✅ |
| **纯本地** | TexLive + LaTeX Workshop（不连 Overleaf） | ✅ | ❌ | ❌ |

## 首次安装引导

当用户说"写论文"且环境未配置时，输出：

```
📝 检测到你要开始写论文，是否配置 LaTeX 环境？
  ① 已有 Overleaf 账号 → 引导安装插件 + Cookie 登录
  ② 纯本地写（安装 TexLive）
  ③ 先用 Markdown 写，稍后转 LaTeX
```

### Overleaf Workshop 配置步骤

1. VS Code 中安装 `Overleaf Workshop` 扩展（作者 iamhyc）
2. Ctrl+Shift+P → "Overleaf Workshop: Add New Server" → 输入 `https://www.overleaf.com`
3. 浏览器登录 Overleaf → F12 → Network → 筛选 `/project` → 复制 Cookie 头
4. VS Code 中 Ctrl+Shift+P → "View: Show Overleaf Workshop" → 点击 "Login to Server" → 粘贴 Cookie
5. 右键项目 → "Open Project Locally" → 开始编辑

> ⚠️ **安全提醒**：Overleaf 的 session cookie 等价于登录凭证。**请勿将 cookie 粘贴到聊天窗口或任何文件中**，仅在 VS Code 插件的登录对话框中使用。Cookie 过期后需重新获取。

### LaTeX Workshop 配置

1. VS Code 中安装 `LaTeX Workshop` 扩展（作者 James Yu）
2. 安装 TexLive（Windows: `winget install texlive`）或 MikTeX
3. 快捷键：
   - `Ctrl+Alt+B`：编译
   - `Ctrl+Alt+V`：预览 PDF
   - `Ctrl+Alt+J`：SyncTeX（源码↔PDF 跳转）

## 模板下载

Agent 在确认目标会议后，从 Overleaf 模板社区下载对应模板：
- NeurIPS: `neurips_2026`
- ICLR: `iclr2026_conference`
- ICML: `icml2026`
- ACL: `acl2026`
- 其他: 搜索 Overleaf Gallery

## Agent 写作行为

1. 如果 Overleaf 已配置 → 直接编辑 `.tex` 文件，改动实时同步
2. 图表保存到 Overleaf 项目的 `figures/` 目录
3. 引用保存为 `references.bib`
4. 用户可随时在本地或 Overleaf 网页预览编译效果
