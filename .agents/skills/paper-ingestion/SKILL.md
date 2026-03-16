---
name: paper-ingestion
description: 统一的论文获取和解析入口。自动识别来源（arxiv/DOI/PDF/标题），选择最优获取方式，输出标准化 Markdown。
---

# Paper Ingestion

统一的论文获取和解析入口。无论论文来源，输出统一格式的结构化 Markdown。

## When to Use

- 用户分享论文 URL、DOI、PDF 文件或论文标题
- literature-survey 批量获取论文时
- 任何需要读取和理解论文内容的场景

## 来源识别

自动解析用户输入，识别论文来源：

| 输入模式 | 识别为 | 示例 |
|---------|--------|------|
| `arxiv.org/abs/XXXX.XXXXX` | arxiv | `https://arxiv.org/abs/2401.12345` |
| `alphaxiv.org/overview/XXXX.XXXXX` | arxiv | `https://alphaxiv.org/overview/2401.12345` |
| `XXXX.XXXXX` 或 `XXXX.XXXXXvN` | arxiv ID | `2401.12345v2` |
| `10.XXXX/...` | DOI | `10.1145/1234567.1234568` |
| `aclanthology.org/...` | ACL | `https://aclanthology.org/2024.acl-long.1/` |
| `*.pdf` 文件路径 | 本地 PDF | `~/papers/example.pdf` |
| PDF URL | 远程 PDF | `https://example.com/paper.pdf` |
| 其他文本 | 标题搜索 | `"Attention Is All You Need"` |

## 三层获取策略

### Tier 1: 结构化 API（最快最准）

#### arxiv 论文 → AlphaXiv API

```bash
# Step 1: 获取 AI 生成的结构化概览（推荐，足够大多数场景）
curl -s "https://alphaxiv.org/overview/{PAPER_ID}.md"

# Step 2: 如需更多细节（公式、表格），获取全文
curl -s "https://alphaxiv.org/abs/{PAPER_ID}.md"
```

- 无需认证，公共端点
- 返回的是 AI 优化的 Markdown，比 PDF 解析质量高
- 404 = 该论文尚未被 AlphaXiv 处理

#### DOI → Semantic Scholar API

```bash
# 获取元数据和摘要
curl -s "https://api.semanticscholar.org/graph/v1/paper/DOI:{DOI}?fields=title,authors,year,abstract,venue,citationCount,references"
```

- 覆盖绝大多数有 DOI 的论文
- 可获取引用关系（用于 evidence graph）

#### ACL Anthology

```bash
# ACL 论文通常同时在 arxiv 上，优先走 arxiv 路径
# 否则下载 PDF 走 Tier 2
```

### Tier 2: PDF 解析（通用）

当 Tier 1 不可用时：

1. **下载 PDF**（如果是 URL）
2. **解析**：优先使用 GROBID（结构化解析，保留章节/图表/公式），fallback 到基础文本提取
3. **结构化**：将解析结果组织为标准格式

### Tier 3: 网页抓取（最后手段）

- arXiv HTML 版本（新论文支持）→ 直接抓取 Markdown
- Google Scholar → 获取元数据
- 论文官网 → 抓取可用信息

## 输出统一格式

无论来源，最终输出到 `parsed_mds/{paper_id}.md`：

```markdown
---
title: "Paper Title"
authors: ["Author A", "Author B"]
year: 2025
venue: "NeurIPS 2025"
doi: "10.xxxx/xxxxx"
arxiv_id: "2401.12345"
source_tier: 1  # 标记用了哪层获取
---

# Paper Title

## Abstract
[摘要全文]

## 1. Introduction
[章节内容]

## 2. Method
[章节内容，数学公式保留 LaTeX: $\mathcal{L} = ...$]

## 3. Experiments
[章节内容]

## 4. Conclusion
[章节内容]

## Figures & Tables
[图表描述，标注 Figure/Table 编号]
```

## 错误处理

| 场景 | 处理 |
|------|------|
| AlphaXiv 404 | Fall through 到 Tier 2（PDF） |
| PDF 下载失败 | 提示用户手动上传 PDF |
| Semantic Scholar 无结果 | 尝试 Google Scholar 搜索 |
| 所有 Tier 失败 | 提示用户提供更多信息（完整标题/URL/PDF） |

## 反直觉规则

1. **不要上来就解析 PDF** — AlphaXiv 的结构化概览比你自己解析的 PDF 质量高得多
2. **元数据和全文一样重要** — venue、引用数等元数据对 evidence graph 至关重要
3. **一篇论文只解析一次** — 检查 `parsed_mds/` 是否已有，避免重复工作
