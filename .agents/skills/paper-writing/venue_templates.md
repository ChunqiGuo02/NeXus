---
name: venue-templates
description: 会议/期刊 LaTeX 模板注册表。paper-writing Step 5 查表自动获取模板。
---

# Venue LaTeX 模板注册表

> Agent 在确认 `target_venue` 后查此表，自动下载模板。

## AI/ML 顶会

| Venue | 模板来源 | 获取命令 | 模板主文件 | 页数 |
|-------|---------|---------|-----------|------|
| **NeurIPS** | [官方 GitHub](https://github.com/neurips-authors/neurips2025) | `git clone https://github.com/neurips-authors/neurips2025.git` | `neurips_2025.tex` | 9+引用 |
| **ICLR** | [Overleaf](https://www.overleaf.com/latex/templates/iclr-2025/PKzgypxzqGQR) | Overleaf Gallery → "ICLR 2025" | `iclr2025_conference.tex` | 无硬限 |
| **ICML** | [官方 GitHub](https://github.com/icml-authors/icml2025) | `git clone https://github.com/icml-authors/icml2025.git` | `icml2025.tex` | 8+引用 |
| **AAAI** | [官方页面](https://aaai.org/authorkit/) | 下载 Author Kit zip | `aaai25.tex` | 7+引用+附录 |
| **CVPR** | [官方 GitHub](https://github.com/cvpr-org/author-kit) | `git clone https://github.com/cvpr-org/author-kit.git` | `cvpr.tex` | 8+引用 |
| **ICCV** | 同 CVPR 模板 | 同上 | `iccv.tex` | 8+引用 |
| **ECCV** | [Springer LNCS](https://www.springer.com/gp/computer-science/lncs/conference-proceedings-guidelines) | 下载 LNCS LaTeX2e zip | `llncs.tex` | 14 页 |
| **ACL/EMNLP/NAACL** | [ACL Rolling Review](https://github.com/acl-org/acl-style-files) | `git clone https://github.com/acl-org/acl-style-files.git` | `acl_latex.tex` | 8+引用 |
| **KDD** | [ACM sigconf](https://www.acm.org/publications/proceedings-template) | `wget acmart-primary.zip` | `sample-sigconf.tex` | 9 页 |
| **WWW** | ACM sigconf | 同上 | `sample-sigconf.tex` | 12 页 |
| **SIGIR** | ACM sigconf | 同上 | `sample-sigconf.tex` | 长文 12/短文 4 |

## 城市 / 地理 / 遥感 顶刊

| Venue | 模板来源 | 获取方式 | 格式 |
|-------|---------|---------|------|
| **Landscape and Urban Planning** | [Elsevier LaTeX](https://www.elsevier.com/researcher/author/policies-and-guidelines/latex-instructions) | 下载 elsarticle 模板 | `elsarticle-template.tex` |
| **Cities** | Elsevier LaTeX | 同上 | `elsarticle-template.tex` |
| **Nature Cities** | [Springer Nature](https://www.springernature.com/gp/authors/campaigns/latex-author-support) | 下载 sn-article 模板 | `sn-article.tex` |
| **Remote Sensing of Environment** | Elsevier LaTeX | 下载 elsarticle | `elsarticle-template.tex` |
| **ISPRS J.** | Elsevier LaTeX | 下载 elsarticle | `elsarticle-template.tex` |
| **GRL / JGR** | [AGU LaTeX](https://www.agu.org/publish-with-agu/publish/author-resources/latex-templates) | 下载 AGU LaTeX 模板 | `agutexSI2019.tex` |
| **ERL** | [IOP Publishing](https://publishingsupport.iopscience.iop.org/questions/latex-template/) | 下载 ioplatexguidelines | `ioplatexguidelines.tex` |

## 通用出版商模板

| 出版商 | 适用范围 | 获取方式 |
|--------|---------|---------|
| **Elsevier (elsarticle)** | 大部分 Elsevier 期刊 | `pip install elsarticle` 或 [GitHub](https://github.com/elsevier-journals/elsarticle) |
| **Springer (svjour3)** | 大部分 Springer 期刊 | [Springer LaTeX](https://www.springer.com/gp/livingreviews/latex-templates) |
| **IEEE (IEEEtran)** | IEEE 会议/期刊 | `texlive` 自带或 [CTAN](https://ctan.org/pkg/ieeetran) |
| **ACM (acmart)** | ACM 会议/期刊 | `texlive` 自带或 [GitHub](https://github.com/borisveytsman/acmart) |

## 模板获取策略（Agent 自动执行）

```
输入: target_venue（从 project_state.json 读取）

Step 1: 查 venue_templates.md 注册表
  ├─ 命中 → 按"获取命令"下载
  └─ 未命中 → Step 2

Step 2: 搜索 Overleaf Gallery
  ├─ 搜索: "{venue_name} {year} template"
  ├─ 找到 → 提示用户在 Overleaf 新建项目再通过 Workshop 同步
  └─ 未找到 → Step 3

Step 3: 搜索出版商通用模板
  ├─ 识别出版商（Elsevier/Springer/IEEE/ACM）
  ├─ 下载对应通用模板
  └─ 未识别 → 使用 article.cls 默认模板 + 提示用户手动提供

Step 4: 初始化项目结构
  ├─ 解压/clone 模板到 experiments/{project}/paper/
  ├─ 重命名主文件为 main.tex
  ├─ 创建 figures/ 和 references.bib
  └─ 写入 project_state.json: template_source + template_path
```

## 年份更新规则

> 模板 URL 可能因年份变化。Agent 在下载前应：
> 1. 先尝试当前注册表中的 URL
> 2. 如果 404，尝试替换年份（如 `neurips2025` → `neurips2026`）
> 3. 如果仍失败，搜索 Overleaf Gallery 作为 fallback
> 4. 更新 venue_templates.md 中的 URL
