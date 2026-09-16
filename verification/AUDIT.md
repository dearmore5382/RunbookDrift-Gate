# Local adversarial audit

This file reports direct-contract verification, not StudioNet execution.

| Area | Case | Expected | Result |
|---|---|---|---|
| Locator | branch instead of 40-char commit | reject | PASS |
| Locator | path traversal | reject | PASS |
| Authority | outsider proposes/cancels | `CURATOR_ONLY` | PASS |
| Lifecycle | second pending candidate | reject | PASS |
| Lifecycle | cancel twice | reject | PASS |
| Happy | all safeguards preserved | `SAFE_REVISION` | PASS |
| Lineage | safe promotion updates baseline and generation | generation +1 | PASS |
| Replay | assess again after final assessment | reject | PASS |
| Failure | rollback removed | `SAFETY_REGRESSION` | PASS |
| Failure | verification removed | `SAFETY_REGRESSION` | PASS |
| Failure | escalation removed | `SAFETY_REGRESSION` | PASS |
| Failure | hazardous target expanded | `SCOPE_EXPANSION` | PASS |
| Failure | semantic uncertainty | `UNCLEAR` | PASS |
| Integrity | fetched digest mismatch | `INTEGRITY_FAILURE`, not promotable | PASS |
| Integrity | digest mismatch before semantic prompt | model is never called | PASS |
| Integrity | exact fetched bytes | recomputed hashes persisted canonically | PASS |
| Availability | fetch/model unavailable | retry, no mutation | PASS |

Before submission, live evidence must additionally prove exact deployed-source parity, real validator fetching of commit-pinned Raw GitHub fixtures, one safe promotion, integrity mismatch handling, one semantic failure and replay rejection on the same deployed address.

## Superseded deployment finding

Deployment `0x0A1c0bE98F74fe09FDe3B8a3Afd07Ee2cAdD412C` exactly matched source hash `cf30a4d86c4dec3f434958b4c132b40eab51ad49ea4b2d563c3cbf55ea587fe0`. Its first assessment finalized with majority agreement on `ASSESSMENT_RETRYABLE`. Receipt inspection and the pinned runtime SDK established the cause: the previous source accessed `response.status_code`; runtime `v0.3.0-rc7` exposes `Response.status`. No positive verdict or promotion occurred.

The source now uses `response.status`, explicitly rejects a missing body, and has a direct regression test. Because deployed source is immutable, live testing must resume only after redeploying the corrected source. This superseded address is retained solely as truthful diagnostic evidence.
