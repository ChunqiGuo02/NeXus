---
name: code-review
description: Review code changes for correctness, regressions, edge cases, style issues, and unnecessary churn. Use when checking diffs, reviewing pull-request-like changes, or doing independent quality review.
---

# Code Review

Review checklist:

1. Correctness: Does the code do what it claims?
2. Regressions: What could break?
3. Edge cases: Are failure conditions handled?
4. Interface risk: Did public or internal contracts change unexpectedly?
5. Test coverage: What is untested?
6. Churn: What can be simplified or removed?

Return:
- critical issues
- medium issues
- minor issues
- suggested next checks