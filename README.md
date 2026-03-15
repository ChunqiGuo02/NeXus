<div align="center">
  <h1>
    <img src="assets/nexus_logo.gif" width="96" alt="Nexus Logo" align="center" style="vertical-align: middle;">
    &nbsp;&nbsp;Nexus : &nbsp;<small style="color: #666;">the Next-gen Unified Sub-researcher</small>
  </h1>
</div>
<p align="center">
  <em>Accelerating discovery from idea to publication</em>
  <br /><br />
  <strong>Idea → Survey → Brainstorm → Experiment → Write → Review</strong>
  <br /><br />
  <a href="https://github.com/ChunqiGuo02/Nexus/stargazers"><img src="https://img.shields.io/github/stars/ChunqiGuo02/Nexus?style=flat-square&color=blue" alt="Stars"></a>
  <a href="https://github.com/ChunqiGuo02/Nexus/network/members"><img src="https://img.shields.io/github/forks/ChunqiGuo02/Nexus?style=flat-square&color=blue" alt="Forks"></a>
  <a href="https://github.com/ChunqiGuo02/Nexus/issues"><img src="https://img.shields.io/github/issues/ChunqiGuo02/Nexus?style=flat-square&color=blue" alt="Issues"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square" alt="License"></a>
</p>

---

An **agent skill pack** that turns any LLM coding assistant (Antigravity, Claude Code, etc.) into a full-stack academic research partner — from idea generation to paper writing and peer review simulation.

## ✨ What It Does

```mermaid
flowchart LR
    classDef entry fill:#0f172a,color:#ffffff,stroke:none,rx:10,ry:10,font-weight:bold
    classDef step fill:#eff6ff,stroke:#2563eb,stroke-width:1.5px,rx:8,ry:8,color:#1d4ed8,font-weight:600
    
    style Discovery fill:#f8fafc,stroke:#cbd5e1,stroke-width:1.5px,stroke-dasharray: 5 5,rx:12,ry:12
    style Ideation fill:#f8fafc,stroke:#cbd5e1,stroke-width:1.5px,stroke-dasharray: 5 5,rx:12,ry:12
    style Validation fill:#f8fafc,stroke:#cbd5e1,stroke-width:1.5px,stroke-dasharray: 5 5,rx:12,ry:12

    U(["👨‍💻 User Query"]):::entry

    subgraph Discovery ["📚 Phase 1: Discovery"]
        direction TB
        S["Literature Survey"]:::step 
        V["Citation Verify"]:::step 
        E["Extract Evidence"]:::step 
        K["Knowledge Graph"]:::step
        S --> V --> E --> K
    end

    subgraph Ideation ["💡 Phase 2: Ideation & Draft"]
        direction TB
        B["Brainstorm Ideas"]:::step 
        N["Novelty Check"]:::step 
        D["Write Draft"]:::step 
        M["Multi-Reviewer"]:::step
        B --> N --> D --> M
    end

    subgraph Validation ["🧪 Phase 3: Validation"]
        direction TB
        R["Run Experiment"]:::step 
        A["Analyze Results"]:::step 
        R --> A
    end

    U --> Discovery
    Discovery --> Ideation
    Ideation --> Validation

    %% Auto-revision loops

    M -. "Revise" .-> D
    A -. "Update Draft" .-> D
```

## 🚀 Quick Start

### 1. Clone

```bash
git clone https://github.com/ChunqiGuo02/Nexus.git
cd Nexus
```

### 2. Install MCP Server

```bash
cd mcp-servers/paper-service
pip install -e .
cd ../..
```

### 3. Configure Your Agent

<details>
<summary><strong>Antigravity</strong></summary>

Add to your MCP config (`mcp_config.json` or via settings):

```json
{
  "mcpServers": {
    "paper-service": {
      "command": "python",
      "args": ["/path/to/Nexus/mcp-servers/paper-service/server.py"]
    }
  }
}
```

Then open Antigravity **in the project directory**. Skills, Rules, and Workflows are auto-discovered from `.agents/`.

</details>

<details>
<summary><strong>Claude Code</strong></summary>

```bash
# Add MCP server
claude mcp add paper-service python /path/to/Nexus/mcp-servers/paper-service/server.py

# Open project
cd Nexus
claude
```

Claude Code reads `CLAUDE.md` at project root to discover capabilities.

</details>

<details>
<summary><strong>Other LLM Agents</strong></summary>

1. Copy `.agents/skills/`, `.agents/rules/`, `.agents/workflows/` to your agent's skill directory
2. Configure the MCP server for your framework
3. The skills are plain Markdown — any agent that reads Markdown instructions can use them

</details>

### 4. Start Researching

```
你: 帮我调研 graph neural networks for urban computing
你: 帮我想几个 research idea
你: 审一下这篇论文，目标 NeurIPS 2026
你: 写论文草稿
```

## 📦 Project Structure

```
Nexus/
├── .agents/
│   ├── skills/                    # 18 Skills (Markdown instructions for LLM)
│   │   ├── omni-orchestrator/     # 🎯 Unified entry point + intent routing
│   │   ├── literature-survey/     # 📚 End-to-end survey pipeline
│   │   ├── citation-verifier/     # ✅ Multi-source citation verification
│   │   ├── claim-extractor/       # 📊 Evidence card extraction
│   │   ├── pattern-promoter/      # 🧠 Auto-build Knowledge Graph
│   │   ├── pdf-to-markdown/       # 📄 PDF parsing (marker-pdf)
│   │   ├── idea-brainstorm/       # 💡 Gap-driven idea generation
│   │   ├── novelty-checker/       # 🔍 Prior art risk assessment
│   │   ├── deep-dive/             # 🔬 In-depth paper analysis
│   │   ├── paper-writing/         # 📝 Dual-model debate drafting + Overleaf
│   │   │   └── overleaf_setup.md  # LaTeX/Overleaf integration guide
│   │   ├── multi-reviewer/        # 👥 Multi-model parallel peer review
│   │   │   └── venue_rubrics/     # 12 conference/journal rubrics
│   │   ├── experiment-runner/     # 🧪 Experiment + SSH remote + AutoDL
│   │   ├── repo-architecture/     # 🏗️ Module boundary enforcement
│   │   ├── code-review/           # 🔎 Code review for correctness
│   │   ├── safe-refactor/         # 🔧 Safe, reviewable refactors
│   │   ├── systematic-debugging/  # 🐛 Root-cause-first debugging
│   │   ├── test-author/           # 🧪 Test writing (repo-style)
│   │   └── verification-runner/   # ✅ Verify implementation claims
│   │
│   ├── rules/                     # 7 Rules (always-on constraints)
│   │   ├── citation-integrity.md  # All citations must be verified
│   │   ├── evidence-discipline.md # All claims need evidence cards
│   │   ├── access-state-policy.md # Paper access level policies
│   │   ├── engineering-baseline.md # Small diffs, follow conventions
│   │   ├── repo-conventions.md    # Python/pytest/ruff/mypy standards
│   │   ├── verification-policy.md # Every change needs verification evidence
│   │   └── model-routing.md       # Multi-model stage recommendation
│   │
│   └── workflows/                 # 7 Workflows (orchestration)
│       ├── full-research-pipeline.md  # Complete research lifecycle
│       ├── quick-survey.md            # Rapid survey (1-3 min)
│       ├── bugfix-safe.md             # Evidence-driven bug fixing
│       ├── hack.md                    # Fast, low-ceremony implementation
│       ├── orchestrate-task.md        # Multi-workstream task planning
│       ├── review-changes.md          # Code change review
│       └── verify-result.md           # Result verification
│
├── mcp-servers/
│   └── paper-service/             # MCP Server (Python/FastMCP)
│       ├── server.py              # Entry point
│       ├── shared.py              # Connection pool + retry + cache
│       ├── sources/               # 8 data source integrations
│       │   ├── semantic_scholar.py
│       │   ├── arxiv_source.py
│       │   ├── crossref.py
│       │   ├── openalex.py
│       │   ├── unpaywall.py
│       │   ├── core_api.py
│       │   ├── europe_pmc.py
│       │   └── shadow_library.py  # Sci-Hub/LibGen (configurable)
│       └── tools/                 # 5 MCP tools
│           ├── search_papers.py   # Multi-source concurrent search
│           ├── fetch_paper.py     # 5-tier waterfall fetching
│           ├── verify_citation.py # Cross-validation + retraction check
│           ├── get_citations.py   # Citation graph
│           └── download_pdf.py    # Secure PDF download
│
├── CLAUDE.md                      # Claude Code entry point
└── README.md                      # This file
```

## 🔧 MCP Server: paper-service

### Data Sources

| Source | Coverage | Rate Limit |
|--------|----------|------------|
| Semantic Scholar | 200M+ papers, all fields | 100/5min (free), 100/s (key) |
| arXiv | CS/Physics/Math/Bio/Econ | No limit |
| CrossRef | 150M+ DOIs, all fields | 50/s (polite pool) |
| OpenAlex | 250M+ works, all fields | Generous |
| Unpaywall | OA link resolution | Requires email |
| CORE | OA repository | API key optional |
| Europe PMC | Biomedical | No limit |
| Sci-Hub/LibGen | Shadow libraries | Configurable, off by default |

### MCP Tools

| Tool | Description |
|------|-------------|
| `search_papers` | Multi-source concurrent search with dedup |
| `fetch_paper` | 5-tier waterfall: arXiv → OA → Shadow → Manual → Abstract |
| `verify_citation` | Multi-source cross-validation + retraction check |
| `get_citations` | Reference/citation graph via Semantic Scholar |
| `download_pdf` | Secure download with path traversal protection |

## 👥 Multi-Reviewer: Venue Rubrics

12 review rubrics covering AI/ML conferences and cross-domain journals:

| Category | Venues | Key Focus |
|----------|--------|-----------|
| **AI/ML** | NeurIPS, ICLR, ICML, ACL, CVPR, AAAI | Novelty, Soundness, Reproducibility |
| **Top Journals** | Nature, Science, Cell | Significance 30%, Broad Impact |
| **Biology** | PNAS, eLife, Cell Reports | Biological replicates, Statistics |
| **Physics** | PRL, PRX, ApJ | Error analysis, Dimensional consistency |
| **Earth Science** | GRL, JGR, ERL | Data quality, Model validation |
| **Architecture/Urban** | Nature Cities, Landscape & Urban Planning, Cities | Practical relevance, Visual quality |
| **Generic** | Any venue | Balanced default weights |

## ⚙️ Configuration

First-run setup creates `~/.nexus/global_config.json`:

```json
{
  "email": "your@email.com",
  "semantic_scholar_key": null,
  "shadow_library_enabled": false,
  "shadow_tls_mode": "strict_then_fallback",
  "search_sources": ["semantic_scholar", "arxiv", "crossref", "openalex"]
}
```

- **email**: Required for Unpaywall and CrossRef polite pool
- **semantic_scholar_key**: [Free API key](https://www.semanticscholar.org/product/api#api-key) to avoid rate limits
- **shadow_library_enabled**: Enable Sci-Hub/LibGen (user responsibility)

## 🔄 Workflows

### Full Research Pipeline (`/full-research-pipeline`)
```
Survey → Scope Freeze → Corpus Freeze → Evidence Extraction →
Idea Brainstorm → Idea Approval → Novelty Check → Review Arena →
Paper Writing → Multi-Review → Revision
```

### Quick Survey (`/quick-survey`)
```
Multi-source Search → Smart Filter (citations + recency + novelty) →
20-30 papers → Brief overview (3-5 minutes)
```

### 🤖 Autopilot Mode

Say **"autopilot"**, **"自动完成"**, or **"vibe research"** at any stage:

```
你: 帮我调研 urban computing
AI: [Survey 完成，等待 Scope Freeze...]
你: autopilot
AI: ✅ Autopilot ON. 后续卡点自动通过，随时说"暂停"恢复手动。
    [自动继续 → Corpus Freeze → Ideate → Novelty Check → Write → Review...]
```

- All checkpoints auto-approve with brief summaries
- Safety guardrails: file deletion, git ops, bulk API calls still require confirmation
- Auto-stops after 2 review-revise rounds or if scores plateau



## 🔒 Privacy & Security

> [!IMPORTANT]
> Nexus 是纯本地的 agent skill pack，**不收集任何数据**。但使用过程中会与外部服务交互，请注意以下事项。

**数据流透明度**：

| 数据 | 发送到哪里 | 目的 |
|------|----------|------|
| 论文搜索查询 | Semantic Scholar, arXiv, OpenAlex, CrossRef | 文献检索 |
| 邮箱（可选） | Unpaywall API `mailto` 参数 | 提高 API 配额 |
| 论文草稿/idea | 你使用的 LLM 提供商（OpenAI, Anthropic, Google 等） | 写作/审稿 |
| SSH 连接信息 | 存储在本地 `~/.nexus/global_config.json` | 远程实验 |

**凭据安全**：
- `global_config.json` 以**明文**存储 API Key 和 SSH 信息，已加入 `.gitignore`
- Overleaf Cookie 等价于登录凭证，**请勿粘贴到聊天窗口**，仅在 VS Code 插件中使用
- 未发表的研究 idea（`hypothesis_board.json`）和论文草稿会发送到 LLM API，请确认你的 LLM 提供商数据政策

**Shadow Library**：
- Sci-Hub / LibGen 访问功能**默认关闭**（`shadow_library_enabled: false`）
- 在部分地区使用可能涉及法律风险，请自行评估合规性后再开启

## 📄 License

MIT License — see [LICENSE](LICENSE).

---

<p align="center">
  <em>Nexus — First to the KEY!</em>
</p>
