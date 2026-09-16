# StudioNet live results

Contract: [`0x3021150FEf7AD2aaD6394805BB0D2cDc20853e13`](https://explorer-studio.genlayer.com/address/0x3021150FEf7AD2aaD6394805BB0D2cDc20853e13)

Deployed source SHA-256: `86c21e9c17e1033fa2b927a23fdccfcc48908269b83dc402191ff962dacbea19` (exact repository parity verified).

Executed on 2026-09-16 with two distinct StudioNet wallets. All 18 planned transactions reached `FINALIZED` with `MAJORITY_AGREE`; signed writes were never automatically retried. The public machine-readable journal is [`live-0x3021150fef7ad2aad6394805bb0d2cdc20853e13.json`](live-0x3021150fef7ad2aad6394805bb0d2cdc20853e13.json).

| Step | Expected and observed result | Transaction |
|---|---|---|
| Reject non-pinned baseline commit | `INVALID_BASELINE_LOCATOR` | [0x7b83…0448](https://explorer-studio.genlayer.com/tx/0x7b838839149d9303d35d5ae069c479b6b8cf65a08f50f64581330b8029d10448) |
| Open safe-revision lineage | ID `0` | [0x22cc…61d5](https://explorer-studio.genlayer.com/tx/0x22cc38d130e0a9a585c6fe8185a6c68e358a45accb35f3c412f7a33d2da261d5) |
| Reject outsider proposal | `CURATOR_ONLY` | [0xc1e2…8e9e](https://explorer-studio.genlayer.com/tx/0xc1e2cd47cb79052724b2b6ac99b1c48428e33d4562657990ab3a95b35e4c8e9e) |
| Propose authenticated safe revision | ID `0` | [0xa1e4…7544](https://explorer-studio.genlayer.com/tx/0xa1e4b068c4000c96a311f52a7b958d02c190ef7b2c25966c10d6e12b910a7544) |
| Reject second pending revision | `REVISION_NOT_PROPOSABLE` | [0xeb03…6f79](https://explorer-studio.genlayer.com/tx/0xeb037432117336659079d90999d87f6f9f2ba8b32c8ecee7154a1767eed16f79) |
| Fetch, hash and assess safe revision | `SAFE_REVISION` | [0xdfa4…7b57](https://explorer-studio.genlayer.com/tx/0xdfa4f7daf40acd825905fcfb19fb3c01c43b32555afafe9457cdbc6037fe7b57) |
| Promote safe revision | `BASELINE_PROMOTED` | [0x2a5b…a12e](https://explorer-studio.genlayer.com/tx/0x2a5b605a15f179baaadfc524bdda54434ca66e0bc182d4deb69d66712b58a12e) |
| Reject promotion replay | `REVISION_NOT_PROMOTABLE` | [0x1b69…3564](https://explorer-studio.genlayer.com/tx/0x1b6971f77b6c59a1ebf2fd9ac7ef449aedc5f8b29cde592173edbc946ac73564) |
| Open rollback-removal control lineage | ID `1` | [0xdfa6…2d93](https://explorer-studio.genlayer.com/tx/0xdfa6de7a8c65e08397a484d1f2245521f4f09cffa3df4574d401c38d6b142d93) |
| Propose rollback-removing revision | ID `1` | [0x2deb…fa29](https://explorer-studio.genlayer.com/tx/0x2deb412fce4e4b697ac2da67b513dc98a6a3a33aeecb02593b02a27a9d19fa29) |
| Detect semantic safety regression | `SAFETY_REGRESSION` | [0x01fe…79f6](https://explorer-studio.genlayer.com/tx/0x01fecaac8b13dc28ea2caed432d311a87476e9050e7dd98ddb62bb979b8d79f6) |
| Reject unsafe promotion | `REVISION_NOT_PROMOTABLE` | [0x54ea…3274](https://explorer-studio.genlayer.com/tx/0x54eaf606e5e434c266ffbf2ef09623fbc563db2cd6c33d3bd45783729d683274) |
| Dismiss unsafe revision | `REVISION_DISMISSED` | [0xb029…7243](https://explorer-studio.genlayer.com/tx/0xb02924c1e44005261f220fa953eba3f4242ff5e7e0ac0b544c2234b6f9d47243) |
| Open digest-mismatch control lineage | ID `2` | [0x8f5e…5785](https://explorer-studio.genlayer.com/tx/0x8f5e41bfacb31b55b157515cfc7e6947f16d4c247520c5c53310e6f044ca5785) |
| Propose revision with false digest | ID `2` | [0x47e8…db7c](https://explorer-studio.genlayer.com/tx/0x47e80d9dac338035b03d6c8de653833ba43cf5f00a70bb587da4feb12e12db7c) |
| Recompute digest and detect mismatch | `INTEGRITY_FAILURE` | [0x0e63…7e94](https://explorer-studio.genlayer.com/tx/0x0e633380de3958616d06074d0d3c115797fcbf5a9e378ea0206a2696dcef7e94) |
| Reject integrity-failing promotion | `REVISION_NOT_PROMOTABLE` | [0xde84…fa9c](https://explorer-studio.genlayer.com/tx/0xde8423dc411fe8de227a6af1710d470decc5920b0c2135330e5c7d887f31fa9c) |
| Dismiss integrity-failing revision | `REVISION_DISMISSED` | [0x6244…b701](https://explorer-studio.genlayer.com/tx/0x6244ff1edf26e92208b51ad4502c47e470c06e47d19b5a6531c2c421adb9b701) |

Final authoritative readback:

- counts: three lineages and three revisions;
- safe revision: exact baseline and candidate digests persisted, verdict `SAFE_REVISION`, status `PROMOTED`, baseline generation advanced to `1`;
- rollback-removing revision: validators observed rollback and verification as not preserved, verdict `SAFETY_REGRESSION`, status `DISMISSED`;
- false-digest revision: fetched candidate digest differed from the committed all-zero digest, verdict `INTEGRITY_FAILURE`, status `DISMISSED`;
- all three lineages ended with `pending_revision_plus_one = 0`.

This proves the on-chain workflow, exact fetched-byte digest binding and validator-derived safety outcomes for the pinned fixtures. It does not prove that an arbitrary runbook is operationally correct or that every future validator cohort will classify ambiguous language identically; uncertain or unavailable assessments fail closed and cannot be promoted.
