---
name: overleaf-setup
description: TexLive + LaTeX Workshop 本地编译 + Overleaf Workshop 云端同步 完整指南。论文写作阶段自动检测并引导配置。
---

# LaTeX 编译 + Overleaf 集成指南

## 架构总览

```
本地 VS Code
  ├─ LaTeX Workshop 插件（本地编译 + PDF 预览 + SyncTeX 双向跳转）
  ├─ Overleaf Workshop 插件（cookie 登录 → 双向实时同步）
  └─ TexLive（本地 LaTeX 引擎）
         ↕ 实时双向同步
Overleaf 云端
  ├─ 云编译（本地 TexLive 不可用时的 fallback）
  ├─ 导师/合作者协作（实时编辑）
  └─ 版本历史 + 备份
```

## Step 0: 环境自动检测

Agent 在进入 paper-writing Stage 6 时自动检测：

```bash
# 检测 TexLive
pdflatex --version 2>$null
xelatex --version 2>$null
latexmk --version 2>$null

# 检测 VS Code 插件
code --list-extensions | Select-String "James-Yu.latex-workshop"
code --list-extensions | Select-String "iamhyc.overleaf-workshop"
```

根据检测结果提供建议：

| TexLive | LaTeX Workshop | Overleaf Workshop | 建议 |
|:---:|:---:|:---:|------|
| ✅ | ✅ | ✅ | 🎉 完美配置，本地编译 + 云端同步 |
| ✅ | ✅ | ❌ | ⚠️ 缺少云协作。需要协作吗？→ 引导安装 Overleaf Workshop |
| ✅ | ❌ | ❌ | ⚠️ 有 TexLive 但缺 VS Code 插件 → `code --install-extension James-Yu.latex-workshop` |
| ❌ | ❌ | ✅ | ⚠️ 纯云模式。本地无法编译，依赖 Overleaf 服务器 |
| ❌ | ❌ | ❌ | 🔴 无 LaTeX 环境 → 引导安装（见下方） |

## Step 1: TexLive 安装

### Windows

```powershell
# 方案 A: winget（推荐，自动配置 PATH）
winget install texlive

# 方案 B: 手动安装（完整版 ~5GB）
# 从 https://tug.org/texlive/ 下载 install-tl-windows.exe
# 选择 "scheme-full" 获取所有宏包
# 或 "scheme-basic" + 按需安装（节省空间）

# 方案 C: MiKTeX（按需下载宏包，初次安装更小）
winget install MiKTeX.MiKTeX
```

### 验证安装

```powershell
pdflatex --version   # 应显示 TexLive 版本
bibtex --version     # BibTeX
latexmk --version    # 自动化编译工具
```

### 缺少宏包自动安装

```powershell
# TexLive
tlmgr install <package_name>

# MiKTeX（自动模式，遇到缺失宏包自动下载）
initexmf --set-config-value=[MPM]AutoInstall=1
```

## Step 2: LaTeX Workshop 配置

### 安装

```powershell
code --install-extension James-Yu.latex-workshop
```

### 推荐 settings.json 配置

```json
{
  "latex-workshop.latex.autoBuild.run": "onSave",
  "latex-workshop.latex.recipe.default": "latexmk (pdflatex)",
  "latex-workshop.latex.recipes": [
    {
      "name": "latexmk (pdflatex)",
      "tools": ["latexmk-pdf"]
    },
    {
      "name": "latexmk (xelatex)",
      "tools": ["latexmk-xelatex"]
    },
    {
      "name": "pdflatex → bibtex → pdflatex × 2",
      "tools": ["pdflatex", "bibtex", "pdflatex", "pdflatex"]
    }
  ],
  "latex-workshop.latex.tools": [
    {
      "name": "latexmk-pdf",
      "command": "latexmk",
      "args": ["-pdf", "-interaction=nonstopmode", "-synctex=1", "-outdir=%OUTDIR%", "%DOC%"]
    },
    {
      "name": "latexmk-xelatex",
      "command": "latexmk",
      "args": ["-xelatex", "-interaction=nonstopmode", "-synctex=1", "-outdir=%OUTDIR%", "%DOC%"]
    },
    {
      "name": "pdflatex",
      "command": "pdflatex",
      "args": ["-interaction=nonstopmode", "-synctex=1", "%DOC%"]
    },
    {
      "name": "bibtex",
      "command": "bibtex",
      "args": ["%DOCFILE%"]
    }
  ],
  "latex-workshop.view.pdf.viewer": "tab",
  "latex-workshop.synctex.afterBuild.enabled": true,
  "latex-workshop.latex.clean.fileTypes": [
    "*.aux", "*.bbl", "*.blg", "*.idx", "*.ind", "*.lof",
    "*.lot", "*.out", "*.toc", "*.acn", "*.acr", "*.alg",
    "*.glg", "*.glo", "*.gls", "*.fls", "*.log", "*.fdb_latexmk",
    "*.snm", "*.nav", "*.synctex.gz"
  ]
}
```

### 快捷键

| 操作 | 快捷键 |
|------|--------|
| 编译 | `Ctrl+Alt+B` |
| 预览 PDF | `Ctrl+Alt+V` |
| SyncTeX 跳转（源码→PDF） | `Ctrl+Alt+J` |
| SyncTeX 反跳（PDF→源码） | 双击 PDF |
| 清理辅助文件 | `Ctrl+Shift+P` → "LaTeX Workshop: Clean up" |

## Step 3: Overleaf Workshop 配置

### 安装

```powershell
code --install-extension iamhyc.overleaf-workshop
```

### 登录配置

1. 浏览器登录 Overleaf（https://www.overleaf.com）
2. F12 → Network → 筛选 `/project` 请求 → 复制完整 Cookie 头
3. VS Code: `Ctrl+Shift+P` → "Overleaf Workshop: Add New Server" → 输入 `https://www.overleaf.com`
4. "View: Show Overleaf Workshop" → 点击 "Login to Server" → 粘贴 Cookie

> ⚠️ **安全提醒**：Cookie 等价于登录凭证。**禁止**将 cookie 写入任何文件或聊天。仅在 VS Code 插件登录对话框中使用。Cookie 过期后需重新获取。

### 项目绑定

```
方式 A: 从 Overleaf 拉取（已有项目）
  Overleaf Workshop 侧栏 → 右键项目 → "Open Project Locally"
  → 自动克隆到本地，后续修改双向同步

方式 B: 本地推送到 Overleaf（新项目）
  1. 在 Overleaf 网页新建空白项目
  2. VS Code 中 Overleaf Workshop → Open 该项目
  3. 将本地模板文件复制过去 → 自动上传
```

### 冲突处理

```
本地修改 + 云端修改同一文件 → 
  Overleaf Workshop 自动检测冲突
  → 弹窗: "Use Local" / "Use Remote" / "Merge"
  → Agent 默认选择 "Use Local"（本地是 Agent 编辑的版本）
  → 但如果 project_state.json 记录了"导师正在审阅"，选 "Use Remote"
```

## Step 4: Agent 编译行为

### 首次编译

```
1. 检测 TexLive → 在项目根目录执行:
   latexmk -pdf -interaction=nonstopmode -synctex=1 main.tex

2. 如果编译失败:
   a. 解析 main.log 查找错误类型
   b. 缺少宏包 → tlmgr install <package>（或 MiKTeX 自动安装）
   c. 语法错误 → Agent 自动修复 .tex 文件 → 重编译
   d. 最多重试 3 次

3. 编译成功 → 提示用户:
   "📄 论文已编译成功 (X 页)。Ctrl+Alt+V 预览 PDF。"
```

### 增量编译

```
Agent 每次修改 .tex 文件后:
  ├─ LaTeX Workshop 检测到 save → 自动触发 latexmk
  ├─ 编译时间: ~5-15 秒（latexmk 增量编译）
  └─ PDF Tab 自动刷新
```

### 编译错误分类处理

| 错误类型 | 自动处理 | 示例 |
|---------|---------|------|
| 缺少宏包 | `tlmgr install` | `! LaTeX Error: File 'xxx.sty' not found.` |
| 未定义命令 | 添加 `\usepackage` | `! Undefined control sequence.` |
| 引用未定义 | 重编译（bibtex + pdflatex×2） | `LaTeX Warning: Reference 'xxx' undefined` |
| 图片未找到 | 检查路径 + 修正 | `! Package pdftex.def Error` |
| 溢出/underfull | 忽略（警告） | `Underfull \hbox` |
| 致命错误 | 展示给用户 | 超过 3 次重试上限 |

## Step 5: 项目初始化模板

Agent 在 paper-writing Step 5 初始化项目时，生成以下目录结构：

```
paper/
├── main.tex              ← 从 venue_templates.md 获取的模板
├── references.bib        ← 从 bib/verified.json 转换
├── figures/
│   ├── method_overview.pdf
│   ├── results_table1.pdf
│   └── ...
├── sections/             ← 可选：按节拆分（大论文时更易管理）
│   ├── introduction.tex
│   ├── related_work.tex
│   ├── method.tex
│   ├── experiments.tex
│   └── conclusion.tex
├── .latexmkrc            ← latexmk 配置
└── .vscode/
    └── settings.json     ← LaTeX Workshop 配置
```

### .latexmkrc 模板

```perl
$pdf_mode = 1;                # 使用 pdflatex
$pdflatex = 'pdflatex -interaction=nonstopmode -synctex=1 %O %S';
$bibtex_use = 2;              # 需要时运行 bibtex
$clean_ext = 'synctex.gz synctex.gz(busy) run.xml tex.bak bbl bcf fdb_latexmk run tdo %R-blx.bib';
```
