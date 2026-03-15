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
flowchart TD
    classDef entry fill:#0f172a,color:#ffffff,stroke:#0f172a,stroke-width:1px,rx:10,ry:10
    classDef step fill:#eff6ff,stroke:#2563eb,stroke-width:1.5px,rx:8,ry:8,color:#0f172a
    classDef note fill:#fff7ed,stroke:#f59e0b,stroke-width:1.5px,rx:8,ry:8,color:#9a3412

    U(["User Query"]):::entry

    subgraph P1["📚 Discovery"]
        direction LR
        S["Literature Survey"]:::step --> V["Citation Verify"]:::step --> E["Extract Evidence"]:::step --> K["Build Knowledge Graph"]:::step
    end

    subgraph P2["💡 Ideation & Drafting"]
        direction LR
        B["Brainstorm Ideas"]:::step --> N["Novelty Check"]:::step --> D["Write Draft"]:::step --> M["Multi-Reviewer"]:::step
    end

    subgraph P3["🧪 Validation"]
        direction LR
        R["Run Experiment"]:::step --> A["Analyze Results"]:::step
    end

    U --> S
    K --> B
    M --> R
    A -. "Revise Draft" .-> D

    K -.-> N1[["Scope Freeze"]]:::note
    M -.-> N2[["Review Score"]]:::note
    A -.-> N3[["Done Notification"]]:::note
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
│   ├── skills/                    # 14 Skills (Markdown instructions for LLM)
│   │   ├── omni-orchestrator/     # 🎯 Unified entry point + intent routing
│   │   ├── literature-survey/     # 📚 End-to-end survey pipeline
│   │   ├── citation-verifier/     # ✅ Multi-source citation verification
│   │   ├── claim-extractor/       # 📊 Evidence card extraction
│   │   ├── pattern-promoter/      # 🧠 Auto-build Knowledge Graph
│   │   ├── pdf-to-markdown/       # 📄 PDF parsing (marker-pdf)
│   │   ├── idea-brainstorm/       # 💡 Gap-driven idea generation
│   │   ├── novelty-checker/       # 🔍 Prior art risk assessment
│   │   ├── deep-dive/             # 🔬 In-depth paper analysis
│   │   ├── paper-writing/         # 📝 Draft generation (story skeleton)
│   │   ├── multi-reviewer/        # 👥 Parallel subagent peer review
│   │   │   └── venue_rubrics/     # 13 conference/journal rubrics
│   │   ├── experiment-runner/     # 🧪 Experiment lifecycle management
│   │   ├── repo-architecture/     # 🏗️ Module boundary enforcement
│   │   └── feishu-notify/         # 📱 Feishu/Lark push & interactive notifications
│   │
│   ├── rules/                     # 3 Rules (always-on constraints)
│   │   ├── citation-integrity.md  # All citations must be verified
│   │   ├── evidence-discipline.md # All claims need evidence cards
│   │   └── access-state-policy.md # Paper access level policies
│   │
│   └── workflows/                 # 2 Workflows (orchestration)
│       ├── full-research-pipeline.md  # Complete lifecycle
│       └── quick-survey.md            # Rapid survey (1-3 min)
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

13 review rubrics covering AI/ML conferences and cross-domain journals:

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

### 📱 Feishu/Lark Notifications (Optional)

Get mobile push notifications at key pipeline stages. Add to `~/.nexus/global_config.json`:

```json
{
  "feishu": {
    "mode": "push",
    "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_ID"
  }
}
```

- **Push mode**: One-way status cards (survey done, review scored, errors)
- **Interactive mode**: Two-way approval via OpenClaw Feishu plugin
- Zero impact when unconfigured

## 📄 License

MIT License — see [LICENSE](LICENSE).

---

<p align="center">
  <em>Nexus — First to the KEY!</em>
</p>
