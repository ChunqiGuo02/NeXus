---
description: 
---

Resolve a bug using an evidence-driven loop.

Use Planning mode when the task is non-trivial or the root cause is not yet clear.

1. Restate the bug in one sentence.
2. Identify the likely files and code paths.
3. Gather direct evidence by reproducing or inspecting the failing path.
4. Form a concise root-cause hypothesis.
5. Make the smallest correct fix.
6. Run the narrowest relevant verification first.
7. If verification fails, revise the hypothesis instead of stacking patches.
8. Finish with:
   - root cause
   - files changed
   - why the fix is correct
   - verification evidence
   - remaining risk