---
name: repo-architecture
description: Apply project-specific architecture and module boundaries. Use when tasks span multiple modules, introduce new files, refactor existing flows, or require understanding where code should live in this repository.
---

# Repo Architecture

Before making non-trivial changes:

1. Read `references/architecture.md`.
2. Follow the documented module boundaries and ownership rules.
3. Place code where the architecture says it belongs.
4. Do not introduce cross-layer shortcuts unless explicitly requested.
5. If the request conflicts with the documented architecture, say so clearly and propose the smallest compliant path.