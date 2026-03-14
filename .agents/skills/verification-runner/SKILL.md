---
name: verification-runner
description: Verify implementation claims using tests, lint, typecheck, build output, and runtime checks. Use when confirming whether a fix or feature actually works.
---

# Verification Runner

1. Start with the narrowest relevant verification command.
2. Expand to broader checks only if needed.
3. Separate:
   - verified
   - unverified
   - failed
4. If a command fails, report whether it appears related to the current change or pre-existing.
5. Finish with:
   - commands run
   - outcomes
   - remaining risks