<p align="center">
  <h1 align="center">🎵 A.R.I.A.</h1>
  <p align="center">
    <strong>A</strong>cademic <strong>R</strong>esearch <strong>I</strong>ntelligent <strong>A</strong>ssistant
    <br />
    <em>AI-powered full-lifecycle research partner</em>
    <br /><br />
    <strong>Survey → Ideate → Experiment → Write → Review</strong>
  </p>
</p>

---

An **agent skill pack** that turns any LLM coding assistant (Antigravity, Claude Code, etc.) into a full-stack academic research partner — from literature survey to paper writing and peer review simulation.

## ✨ What It Does

```
"帮我调研 attention mechanism 在城市计算中的应用"
        │
        ▼
┌─ Phase 1: Foundation ──────────────────────┐
│  📚 Literature Survey (8 data sources)     │
│  ✅ Citation Verification (multi-source)   │
│  📊 Evidence Extraction → Evidence Graph   │
│  🧠 Knowledge Graph (auto-built)          │
└────────────────────────────────────────────┘
        │
        ▼
┌─ Phase 2: Thinking & Writing ──────────────┐
│  💡 Idea Brainstorm (gap-driven)           │
│  🔍 Novelty Check (prior art scan)        │
│  📝 Paper Draft (story skeleton method)    │
│  👥 Multi-Reviewer (parallel subagents)    │
└────────────────────────────────────────────┘
        │
        ▼
┌─ Phase 3: Experimentation ─────────────────┐
│  🧪 Experiment Runner (code → results)     │
│  📈 Result Analysis → Evidence Graph       │
└────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Clone

```bash
git clone https://github.com/ChunqiGuo02/ARIA.git
cd ARIA
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
      "args": ["/path/to/ARIA/mcp-servers/paper-service/server.py"]
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
claude mcp add paper-service python /path/to/ARIA/mcp-servers/paper-service/server.py

# Open project
cd ARIA
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
ARIA/
├── .agents/
│   ├── skills/                    # 13 Skills (Markdown instructions for LLM)
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
│   │   └── repo-architecture/     # 🏗️ Module boundary enforcement
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

First-run setup creates `~/.aria/global_config.json`:

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

## 📄 License

MIT License — see [LICENSE](LICENSE).

---

<p align="center">
  <em>A.R.I.A. — Your research, amplified.</em>
</p>
