---
description: 将复杂任务拆分为可并行的工作流，分配给多个 agent。
---

Use Planning mode.

Break this task into parallelizable or stage-based workstreams with minimal overlap.

Rules:
1. Do not split work if the task is a single tight debugging loop.
2. Use one main implementer unless the task clearly separates by module, file boundary, or phase.
3. Keep review and verification independent from implementation.
4. Avoid assigning multiple implementers to the same file or same call chain at the same time.

Output:
- whether orchestration is warranted
- proposed workstreams
- which agent should do each one
- what artifacts or outputs each agent should produce