---
name: systematic-debugging
description: Debug bugs with a root-cause-first process. Use when diagnosing failures, flaky tests, runtime errors, incorrect outputs, or regressions.
---

# Systematic Debugging

When debugging:

1. Restate the observed failure precisely.
2. Identify the likely execution path and affected files.
3. Gather direct evidence before editing.
4. Form one primary root-cause hypothesis.
5. Prefer the smallest fix that addresses the root cause.
6. After editing, run the narrowest relevant verification first.
7. If the fix is incomplete, state what remains uncertain.

Output must include:
- symptom
- root cause
- files changed
- verification
- residual risk