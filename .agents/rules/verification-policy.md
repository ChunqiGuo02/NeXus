---
trigger: always_on
---

- Every code change must end with verification evidence.
- Prefer this order when possible:
  1. targeted tests
  2. typecheck or lint
  3. build or runtime smoke check
- If full verification is not possible, explicitly state:
  - verified
  - not verified
  - residual risk