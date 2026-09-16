# RunbookDrift Gate specification

## Proof obligation

Establish whether one exact candidate runbook preserves the operational safeguards of one exact baseline runbook under a sealed safety policy. Both documents must be fetched independently from canonical Raw GitHub paths pinned to a 40-character commit SHA, and both byte digests must match their on-chain commitments before semantic judgment.

The contract does not prove that the runbook was executed, that a real system is safe, that repository content is factually correct, or that a GitHub identity has external organizational authority.

## Distinct architecture

The contract maintains a versioned lineage rather than a bilateral agreement, escrow or append-only notice registry:

```text
open lineage with baseline generation 0
  -> propose exactly one candidate for current generation
  -> independently fetch and authenticate baseline + candidate
  -> assess semantic safeguard drift
  -> safe: promote candidate to generation N+1
     unsafe/unclear/integrity failure: dismiss candidate
     unavailable: retry without state mutation
```

Promotion changes the future comparison root. Historical revision observations remain immutable.

## Source and digest boundary

Callers cannot provide arbitrary URLs. The contract accepts validated GitHub owner, repository, exact commit and relative path components, then constructs:

`https://raw.githubusercontent.com/{owner}/{repository}/{commit}/{path}`

It rejects branch names, traversal components and malformed digests. Every validator fetches both byte sequences, enforces status/size bounds and computes SHA-256 locally. A mismatch prevents semantic classification and yields `INTEGRITY_FAILURE`.

## Consensus fields

- `rollback_preserved`
- `verification_preserved`
- `escalation_preserved`
- `dangerous_scope_expanded`
- `operational_meaning_changed`

Each is `YES`, `NO` or `UNCLEAR`. Validators compare the authenticated hashes, source status and all five consequential fields. Free-form reasoning is neither returned nor stored.

## Deterministic verdict precedence

1. unavailable source/model -> retry with no mutation;
2. digest mismatch/invalid UTF-8 -> `INTEGRITY_FAILURE`;
3. missing or weakened rollback, verification or escalation -> `SAFETY_REGRESSION`;
4. broader dangerous scope -> `SCOPE_EXPANSION`;
5. any uncertainty -> `UNCLEAR`;
6. otherwise -> `SAFE_REVISION`.

Only `SAFE_REVISION` is promotable.
