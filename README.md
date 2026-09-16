# RunbookDrift Gate

RunbookDrift Gate is a narrow GenLayer Intelligent Contract for detecting safety regressions between authenticated versions of an operations runbook.

Every validator independently fetches a baseline and candidate from commit-pinned Raw GitHub locations, recomputes both SHA-256 digests from the fetched bytes and evaluates whether rollback, verification and escalation safeguards remain effective. Deterministic contract logic derives the verdict. Only a `SAFE_REVISION` can become the next baseline generation.

## Why GenLayer

Textual diffs cannot reliably determine whether differently worded procedures preserve the same operational safeguard. GenLayer validators can independently judge semantic equivalence while the contract enforces source integrity, bounded output, verdict precedence, authority, lifecycle and replay resistance.

## Public methods

- `open_lineage`: create generation zero from a commit-pinned baseline.
- `propose_revision`: bind one candidate to the current generation.
- `assess_revision`: fetch, hash and semantically compare both documents.
- `promote_revision`: advance the lineage only after `SAFE_REVISION`.
- `dismiss_revision`: close a finalized non-promoted candidate.
- `cancel_pending`: cancel before assessment.
- `get_lineage`, `get_revision`, `get_counts`: authoritative readback.

## Test

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
```

Current status: contract implementation and 10 direct/static tests pass, including exact fetched-byte hashing and proof that digest mismatch blocks the semantic prompt. Raw fixtures are prepared, but the project is not deployed and no live fetch or StudioNet result is claimed yet. See [SPEC.md](SPEC.md), [fixtures/README.md](fixtures/README.md) and [verification/AUDIT.md](verification/AUDIT.md).
