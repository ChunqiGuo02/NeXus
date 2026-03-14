---
name: safe-refactor
description: Perform safe, reviewable refactors. Use when restructuring code, moving responsibilities, renaming across modules, or reducing duplication without intended behavior changes.
---

# Safe Refactor

1. Define what must not change.
2. Map affected modules, call sites, and tests.
3. Separate mechanical changes from behavioral changes when possible.
4. Keep diffs reviewable and avoid unrelated cleanup.
5. Run the most relevant checks after each meaningful phase.
6. End with:
   - before/after structure
   - compatibility impact
   - verification evidence