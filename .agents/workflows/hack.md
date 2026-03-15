---
description: 快速低仪式实现或修复，适合小型局部任务。
---

Execute a fast, low-ceremony implementation or bug fix.

Use Fast mode when the task is small and localized.

Execution protocol:
1. Search narrowly using terminal tools like rg, grep, find, or cat.
2. Read only the files necessary to complete the task.
3. Make the smallest correct change.
4. Run the narrowest relevant verification command autonomously when safe.
5. If verification fails, inspect the error, fix the issue, and retry.
6. Finish with a concise result:
   - files changed
   - verification result
   - residual risk if any

Do not produce a long plan unless the task turns out to be non-trivial. If it becomes non-trivial, say so and switch to a plan-first workflow.