---
name: test-author
description: Write or update tests that match the repository's existing style. Use when adding regression tests, feature tests, unit tests, or filling verification gaps after code changes.
---

# Test Author

When writing tests:

1. Inspect existing tests near the touched code first.
2. Match the project's current framework, naming, fixtures, and assertion style.
3. Prefer targeted regression tests over broad noisy tests.
4. Cover:
   - happy path
   - edge cases
   - failure path if relevant
5. Keep tests deterministic.
6. If behavior is ambiguous, call it out instead of guessing.

Output must include:
- test files added or changed
- behaviors covered
- behaviors still unverified