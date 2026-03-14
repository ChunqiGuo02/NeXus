---
name: pdf-to-markdown
description: 将任意学术 PDF 转换为结构化 Markdown，支持表格、公式、图注。用于非 arXiv 论文的解析（arXiv 论文请优先使用 alphaxiv-paper-lookup）。当用户说"帮我读/解析/分析这篇论文"且论文不在 arXiv 上时触发。
---

# pdf-to-markdown

将学术 PDF 转换为结构化 Markdown，保留论文的组织结构。

## 前置条件

需要安装 `marker-pdf` 包：
```bash
pip install marker-pdf
```

## 使用方式

### 输入
- PDF 文件路径（绝对路径或相对于 workspace 的路径）

### 输出
- 结构化 Markdown 文件，保存到 `parsed_mds/{filename}.md`

## 执行步骤

1. **检查 marker 是否安装**
   ```bash
   python -c "import marker; print('marker ready')"
   ```
   未安装则执行 `pip install marker-pdf`

2. **调用 marker 解析 PDF**
   ```bash
   marker_single "{pdf_path}" --output_dir "{project_dir}/parsed_mds/"
   ```

3. **验证输出**
   - 检查生成的 Markdown 文件是否存在
   - 检查文件大小是否合理（>1KB）
   - 如果解析失败，回退到 PyMuPDF 轻量方案：
     ```python
     import pymupdf
     doc = pymupdf.open(pdf_path)
     text = "\n\n".join(page.get_text() for page in doc)
     ```

4. **返回路径**
   - 告知用户 Markdown 已保存到什么位置
   - 如果有明显解析问题（如公式乱码），建议用 nougat 重新解析

## 与 alphaxiv-paper-lookup 的关系

```
论文需要解析
  ├─ 有 arXiv ID → alphaxiv-paper-lookup（秒级，预处理好的 Markdown）
  └─ 无 arXiv ID → pdf-to-markdown（marker 本地解析，几十秒）
      └─ marker 失败 → PyMuPDF 文本提取（兜底）
```

## 注意事项

- marker 消耗较多内存，建议单文件处理
- 解析含大量数学公式的论文，考虑使用 `nougat`（`pip install nougat-ocr`）
- 解析后的 Markdown 可直接供 `claim-extractor` Skill 使用
