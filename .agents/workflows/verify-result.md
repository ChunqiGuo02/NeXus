---
description: 验证实现声明是否真实：跑测试、lint、构建、运行时检查。
---

Verify the claimed result only.

Do not redesign the implementation unless verification reveals a real defect.

Check:
1. targeted tests
2. lint/typecheck
3. build output
4. runtime behavior if applicable
5. whether the claimed fix is actually supported by evidence

Return:
- verified claims
- unverified claims
- residual risks