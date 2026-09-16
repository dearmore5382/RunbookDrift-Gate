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

Deployment `0x08AAF4102cA7E1b70F214A605E05A3aA38aFC437` then verified the corrected web path. Its assessment equivalence output contained the exact committed baseline and candidate SHA-256 values, proving successful validator fetch and digest recomputation. The semantic result was retryable because StudioNet returned model JSON as a string and that source revision required a dictionary. Current source accepts a bounded JSON string through `json.loads`, retains an exact five-key schema, rejects extra keys, and has direct regression tests for both cases. The address is superseded; no positive state or promotion occurred.

Deployment `0xf902855724f6a9Fe63D77A672C53180921b320d0` confirmed fetch, both exact digests and LLM token consumption, but again finalized retryable because cross-provider formatting failed the JSON schema boundary. The current design removes JSON formatting from the semantic interface. Models must return exactly five positional tokens separated by `|`; code maps positions to the five named fields and rejects wrong counts, invalid values, prose-only output and privileged verdict injection. The address is superseded and produced no positive state or promotion.

The current undeployed source additionally rejects a valid token line when it is wrapped in prose or code fences. Its direct suite runs the public happy path through mocked Raw GitHub responses and the real nondeterministic leader/validator callback, verifies exact digests in the persisted observation, and promotes only the agreed `SAFE_REVISION`. Full public failure tests cover digest substitution and consequential validator disagreement. The complete 17-test suite passed twice consecutively, and all five commit-pinned public fixture URLs independently returned HTTP 200 with matching SHA-256 values. Current source SHA-256: `86c21e9c17e1033fa2b927a23fdccfcc48908269b83dc402191ff962dacbea19`.
