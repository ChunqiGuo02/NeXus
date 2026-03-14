---
name: citation-verifier
description: 多源交叉核验引用真实性 + 撤稿检查。验证 DOI/论文是否真实存在、元数据是否一致、是否已被撤稿。当需要验证引用、检查论文真伪、或在写作前确认参考文献时触发。
---

# citation-verifier

对论文引用进行多源交叉核验，确保引用真实性。

## 执行步骤

1. **调用 MCP 工具验证**
   使用 `paper-service` MCP 的 `verify_citation` tool：
   ```
   verify_citation(doi="10.1234/xxx")
   ```

2. **解读结果**

   | status | 含义 | 后续操作 |
   |--------|------|---------|
   | `verified` | 至少两源确认 | ✅ 安全引用 |
   | `unverified` | 无法确认 | ⚠️ 标记为 `[UNVERIFIED]`，寻找替代引用 |
   | `retracted` | 已撤稿 | ❌ **禁止引用**，提示用户 |

3. **写入验证结果**
   更新 `corpus_ledger.json` 中对应条目的：
   - `citation_verified`: true/false
   - `verification_sources`: ["crossref", "openalex", ...]
   - `is_retracted`: true/false
   - `retraction_checked_at`: ISO 时间戳

4. **导出 verified bib**
   将验证通过的引用写入 `bib/verified.json`（CSL-JSON 格式），供 paper-writing Skill 使用

## 批量验证

对 `corpus_ledger.json` 中所有未验证的条目执行批量验证：
```
for entry in corpus_ledger where citation_verified == null:
    result = verify_citation(doi=entry.doi)
    update entry with result
```

## 遵守规则

严格遵守 `rules/citation-integrity.md` 中的所有约束。
