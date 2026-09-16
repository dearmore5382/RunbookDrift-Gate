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
