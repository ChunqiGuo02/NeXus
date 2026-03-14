---
trigger: always_on
---

- Use Python with `pip` / `pyproject.toml` for dependency management.
- Use `pytest` for testing, `ruff` for linting, and `mypy` for type checking as the primary verification commands unless a closer command exists.
- MCP servers live under `mcp-servers/` and use FastMCP.
- Skills live under `.agents/skills/` and follow the standard SKILL.md format.
- Workflows live under `.agents/workflows/`.
- New tests should follow the existing project convention for placement and naming.