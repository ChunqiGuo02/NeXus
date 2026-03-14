<p align="center">
  <img src="assets/nexus_logo.gif" width="80" alt="Nexus Logo" style="vertical-align: middle;">
  &nbsp;&nbsp;
  <strong style="font-size: 2em;">Nexus</strong>
  <br />
  <strong>The Autonomous AI Co-Scientist</strong>
  <br />
  <em>Accelerating discovery from literature to publication</em>
  <br /><br />
  <strong>Survey → Ideate → Experiment → Write → Review</strong>
  <br /><br />
  <a href="https://github.com/ChunqiGuo02/Nexus/stargazers"><img src="https://img.shields.io/github/stars/ChunqiGuo02/Nexus?style=flat-square&color=blue" alt="Stars"></a>
  <a href="https://github.com/ChunqiGuo02/Nexus/network/members"><img src="https://img.shields.io/github/forks/ChunqiGuo02/Nexus?style=flat-square&color=blue" alt="Forks"></a>
  <a href="https://github.com/ChunqiGuo02/Nexus/issues"><img src="https://img.shields.io/github/issues/ChunqiGuo02/Nexus?style=flat-square&color=blue" alt="Issues"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square" alt="License"></a>
</p>

---

An **agent skill pack** that turns any LLM coding assistant (Antigravity, Claude Code, etc.) into a full-stack academic research partner — from literature survey to paper writing and peer review simulation.

## ✨ What It Does

```mermaid
flowchart TD
    Query(["💬 '帮我调研 attention mechanism 在城市计算中的应用'"])

    subgraph P1 ["Phase 1: Foundation"]
        direction TB
        S["📚 Literature Survey (8 data sources)"]
        V["✅ Citation Verification (multi-source)"]
        E["📊 Evidence Extraction → Evidence Graph"]
        K["🧠 Knowledge Graph (auto-built)"]
        S --> V
        V --> E
        E --> K
    end

    subgraph P2 ["Phase 2: Thinking & Writing"]
        direction TB
        B["💡 Idea Brainstorm (gap-driven)"]
        N["🔍 Novelty Check (prior art scan)"]
        D["📝 Paper Draft (story skeleton method)"]
        M["👥 Multi-Reviewer (parallel subagents)"]
        B --> N
        N --> D
        D --> M
    end

    subgraph P3 ["Phase 3: Experimentation"]
        direction TB
        R["🧪 Experiment Runner (code → results)"]
        A["📈 Result Analysis → Evidence Graph"]
        R --> A
    end

    Query --> P1
    P1 --> P2
    P2 --> P3
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
Search → Top 10 by citations → Brief overview (1-3 minutes)
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
  <em>Nexus — Your research, amplified.</em>
</p>
